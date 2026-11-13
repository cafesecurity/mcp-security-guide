// Transport tests from guide/04-test.md: Origin and Host checks against DNS
// rebinding, header and body consistency, and no session endpoints.
import request from "supertest";
import { beforeAll, describe, expect, it } from "vitest";
import { createApp } from "../src/server.js";
import { mcp, setup } from "./helpers.js";
import { jwtVerifier } from "../src/auth.js";
import { memoryStore } from "../src/corpus.js";

let ctx: Awaited<ReturnType<typeof setup>>;
let token: string;

beforeAll(async () => {
  ctx = await setup();
  token = await ctx.issuer.token({ tenant: "trevor-co", groups: ["all-staff"] });
});

describe("transport", () => {
  it("rejects a request from a foreign web page (Origin) with 403", async () => {
    const res = await mcp(ctx.app, token, "tools/list", {}, { Origin: "https://evil.example" });
    expect(res.status).toBe(403);
  });

  it("accepts a localhost Origin", async () => {
    const res = await mcp(ctx.app, token, "tools/list", {}, { Origin: "http://localhost:6274" });
    expect(res.status).toBe(200);
  });

  it("rejects a rebinding attempt (foreign Host header) with 403", async () => {
    const res = await mcp(ctx.app, token, "tools/list", {}, { Host: "evil.example:3333" });
    expect(res.status).toBe(403);
  });

  it("rejects a request whose Mcp-Name header doesn't match the tool in the body", async () => {
    const res = await mcp(
      ctx.app, token, "tools/call",
      { name: "search_docs", arguments: { query: "holiday" } },
      { "Mcp-Name": "get_doc" },
    );
    expect(res.status).toBe(400);
    expect(res.body.error?.code).toBe(-32020);
  });

  it("rejects a request whose Mcp-Method header doesn't match the body", async () => {
    const res = await mcp(ctx.app, token, "tools/list", {}, { "Mcp-Method": "resources/list" });
    expect(res.status).toBe(400);
    expect(res.body.error?.code).toBe(-32020);
  });

  it("has no GET stream or DELETE session endpoint", async () => {
    expect((await request(ctx.app).get("/mcp").set("Authorization", `Bearer ${token}`)).status).toBe(405);
    expect((await request(ctx.app).delete("/mcp").set("Authorization", `Bearer ${token}`)).status).toBe(405);
  });

  it("refuses to bind beyond loopback without a Host allow-list", () => {
    expect(() =>
      createApp({
        resourceUrl: new URL("https://trevor.example.com/mcp"),
        issuer: "https://login.example.com",
        authorizationEndpoint: "https://login.example.com/authorize",
        tokenEndpoint: "https://login.example.com/token",
        verifier: jwtVerifier({ issuer: "x", audience: "y", keys: ctx.issuer.keys }),
        store: memoryStore([]),
        log: () => {},
        host: "0.0.0.0",
      }),
    ).toThrow(/allowedHosts/);
  });
});
