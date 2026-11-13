import request from "supertest";
import { memoryStore, SAMPLE_DOCS } from "../src/corpus.js";
import { jwtVerifier } from "../src/auth.js";
import type { ToolCallEvent } from "../src/log.js";
import { createApp } from "../src/server.js";
import { createTestIssuer, TEST_ISSUER, TEST_RESOURCE } from "./issuer.js";

export const PROTOCOL = "2026-07-28";

export async function setup(opts: { rateLimit?: { limit: number; windowMs: number } } = {}) {
  const issuer = await createTestIssuer();
  const logs: ToolCallEvent[] = [];
  const app = createApp({
    resourceUrl: new URL(TEST_RESOURCE),
    issuer: TEST_ISSUER,
    authorizationEndpoint: `${TEST_ISSUER}/authorize`,
    tokenEndpoint: `${TEST_ISSUER}/token`,
    verifier: jwtVerifier({ issuer: TEST_ISSUER, audience: TEST_RESOURCE, keys: issuer.keys }),
    store: memoryStore(SAMPLE_DOCS),
    log: (e) => logs.push(e),
    ...(opts.rateLimit ? { rateLimit: opts.rateLimit } : {}),
  });
  return { app, issuer, logs };
}

let nextId = 1;

/** Build a 2026-07-28 JSON-RPC request body with the per-request _meta envelope. */
export function rpcBody(method: string, params: Record<string, unknown> = {}) {
  return {
    jsonrpc: "2.0",
    id: nextId++,
    method,
    params: {
      ...params,
      _meta: {
        "io.modelcontextprotocol/protocolVersion": PROTOCOL,
        "io.modelcontextprotocol/clientInfo": { name: "test-client", version: "1.0.0" },
        "io.modelcontextprotocol/clientCapabilities": {},
      },
    },
  };
}

/** POST an MCP request with the headers the Streamable HTTP transport requires. */
export function mcp(
  app: Parameters<typeof request>[0],
  token: string | undefined,
  method: string,
  params: Record<string, unknown> = {},
  extraHeaders: Record<string, string> = {},
) {
  let req = request(app)
    .post("/mcp")
    .set("Content-Type", "application/json")
    .set("Accept", "application/json, text/event-stream")
    .set("MCP-Protocol-Version", PROTOCOL)
    .set("Mcp-Method", method);
  const name = (params.name ?? params.uri) as string | undefined;
  if (name) req = req.set("Mcp-Name", name);
  if (token) req = req.set("Authorization", `Bearer ${token}`);
  for (const [k, v] of Object.entries(extraHeaders)) req = req.set(k, v);
  return req.send(rpcBody(method, params));
}

/** Call a tool and return the parsed JSON from its text content. */
export async function callTool(app: Parameters<typeof request>[0], token: string, name: string, args: Record<string, unknown>) {
  const res = await mcp(app, token, "tools/call", { name, arguments: args });
  if (res.status !== 200) throw new Error(`HTTP ${res.status}: ${res.text}`);
  const result = res.body.result;
  if (!result) return { error: res.body.error, isError: true, raw: res.body };
  const text = result.content?.[0]?.text ?? "";
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }
  return { data, isError: result.isError === true, raw: res.body };
}
