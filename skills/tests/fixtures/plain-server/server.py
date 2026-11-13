#!/usr/bin/env python3
"""TEST FIXTURE: a well-behaved MCP server with one read-only tool and no network use."""
import json
import sys

TOOLS = [{
    "name": "word_count",
    "description": "Counts the words in a piece of text and returns the number.",
    "inputSchema": {"type": "object", "properties": {"text": {"type": "string", "maxLength": 10000}}, "required": ["text"]},
    "annotations": {"readOnlyHint": True, "openWorldHint": False},
}]

for line in sys.stdin:
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        continue
    if "id" not in msg:
        continue
    m = msg.get("method")
    if m == "initialize":
        res = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "word-count", "version": "1.0.0"}}
    elif m == "tools/list":
        res = {"tools": TOOLS}
    elif m == "tools/call":
        res = {"content": [{"type": "text", "text": str(len(msg["params"]["arguments"].get("text", "").split()))}]}
    else:
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "Method not found"}}) + "\n")
        sys.stdout.flush()
        continue
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": res}) + "\n")
    sys.stdout.flush()
