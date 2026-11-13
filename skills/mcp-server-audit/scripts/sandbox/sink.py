#!/usr/bin/env python3
"""Network sink for the audit sandbox.

Runs on the sandbox's internal network as the server's only DNS resolver and as
the address every name resolves to. It answers every DNS query with its own
address, accepts TCP connections on common ports, and logs what arrives as JSON
lines on stdout: DNS names, TLS server names (SNI), HTTP request lines, headers
and bodies, and the first bytes of anything else. Nothing is forwarded anywhere.

Standard library only.
"""
import base64
import json
import os
import socket
import struct
import threading
import time

SINK_IP = os.environ.get("SINK_IP", "0.0.0.0")
TCP_PORTS = [int(p) for p in os.environ.get("SINK_PORTS", "21,22,25,80,443,465,587,993,3306,5432,6379,8000,8080,8443,9200,27017").split(",")]
MAX_BYTES = 65536
lock = threading.Lock()


def log(event: dict) -> None:
    event["time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with lock:
        print(json.dumps(event), flush=True)


# --- DNS ------------------------------------------------------------------------

def parse_qname(data: bytes, offset: int = 12) -> tuple[str, int]:
    labels = []
    while offset < len(data):
        n = data[offset]
        if n == 0:
            return ".".join(labels), offset + 1
        if n & 0xC0:
            return ".".join(labels), offset + 2
        labels.append(data[offset + 1: offset + 1 + n].decode("ascii", "replace"))
        offset += 1 + n
    return ".".join(labels), offset


def dns_answer(query: bytes) -> bytes:
    qname, end = parse_qname(query)
    qtype = struct.unpack(">H", query[end:end + 2])[0] if len(query) >= end + 2 else 1
    header = query[:2] + b"\x81\x80" + b"\x00\x01" + (b"\x00\x01" if qtype == 1 else b"\x00\x00") + b"\x00\x00\x00\x00"
    question = query[12:end + 4]
    if qtype != 1:  # answer only A records; others get an empty NOERROR
        return header + question
    ip = socket.inet_aton(SINK_IP if SINK_IP != "0.0.0.0" else "127.0.0.1")
    answer = b"\xc0\x0c" + struct.pack(">HHIH", 1, 1, 5, 4) + ip
    return header + question + answer


def dns_server() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 53))
    while True:
        data, addr = s.recvfrom(4096)
        try:
            name, end = parse_qname(data)
            qtype = struct.unpack(">H", data[end:end + 2])[0] if len(data) >= end + 2 else 0
            log({"kind": "dns", "from": addr[0], "name": name, "qtype": qtype})
            s.sendto(dns_answer(data), addr)
        except Exception as e:  # noqa: BLE001
            log({"kind": "dns-error", "from": addr[0], "error": str(e)[:200]})


# --- TCP ------------------------------------------------------------------------

def tls_sni(data: bytes) -> str | None:
    try:
        if data[0] != 0x16 or data[5] != 0x01:
            return None
        p = 9 + 2 + 32
        p += 1 + data[p]                                   # session id
        p += 2 + struct.unpack(">H", data[p:p + 2])[0]     # cipher suites
        p += 1 + data[p]                                   # compression
        end = p + 2 + struct.unpack(">H", data[p:p + 2])[0]
        p += 2
        while p + 4 <= end:
            etype, elen = struct.unpack(">HH", data[p:p + 4])
            if etype == 0:
                n = struct.unpack(">H", data[p + 7:p + 9])[0]
                return data[p + 9:p + 9 + n].decode("ascii", "replace")
            p += 4 + elen
    except (IndexError, struct.error):
        return None
    return None


def handle(conn: socket.socket, addr, port: int) -> None:
    conn.settimeout(3)
    data = b""
    try:
        while len(data) < MAX_BYTES:
            chunk = conn.recv(8192)
            if not chunk:
                break
            data += chunk
            if data[:1] != b"\x16" and b"\r\n\r\n" in data:
                head, _, body = data.partition(b"\r\n\r\n")
                length = 0
                for line in head.split(b"\r\n")[1:]:
                    if line.lower().startswith(b"content-length:"):
                        length = int(line.split(b":", 1)[1].strip() or 0)
                if len(body) >= length:
                    break
            if data[:1] == b"\x16" and len(data) > 5:
                break
    except (socket.timeout, OSError, ValueError):
        pass
    event = {"kind": "tcp", "from": addr[0], "port": port, "bytes": len(data), "raw_b64": base64.b64encode(data[:8192]).decode()}
    sni = tls_sni(data) if data else None
    if sni:
        event.update(kind="tls", sni=sni)
    elif data[:16].split(b" ")[0] in (b"GET", b"POST", b"PUT", b"PATCH", b"DELETE", b"HEAD", b"OPTIONS"):
        head, _, body = data.partition(b"\r\n\r\n")
        lines = head.decode("latin-1").split("\r\n")
        event.update(kind="http", request=lines[0][:500],
                     headers={l.split(":", 1)[0]: l.split(":", 1)[1].strip()[:500] for l in lines[1:] if ":" in l},
                     body=body[:8192].decode("utf-8", "replace"))
        try:
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok")
        except OSError:
            pass
    elif data:
        event["text"] = data[:2048].decode("utf-8", "replace")
    log(event)
    conn.close()


def tcp_server(port: int) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", port))
    except OSError as e:
        log({"kind": "sink-error", "port": port, "error": str(e)})
        return
    s.listen(64)
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr, port), daemon=True).start()


if __name__ == "__main__":
    threading.Thread(target=dns_server, daemon=True).start()
    for p in TCP_PORTS:
        threading.Thread(target=tcp_server, args=(p,), daemon=True).start()
    log({"kind": "sink-ready", "ip": SINK_IP, "ports": TCP_PORTS})
    while True:
        time.sleep(3600)
