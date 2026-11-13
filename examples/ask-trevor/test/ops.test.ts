// Operations tests from guide/04-test.md: rate limits, and logs that record who did what
// without tokens or document content.
import { describe, expect, it } from "vitest";
import { callTool, mcp, setup } from "./helpers.js";

describe("rate limit", () => {
  it("returns 429 with Retry-After once a user exceeds the limit, without affecting other users", async () => {
    const ctx = await setup({ rateLimit: { limit: 3, windowMs: 60_000 } });
    const a = await ctx.issuer.token({ sub: "alice", tenant: "trevor-co", groups: ["all-staff"] });
    const b = await ctx.issuer.token({ sub: "bob", tenant: "trevor-co", groups: ["all-staff"] });
    for (let i = 0; i < 3; i++) expect((await mcp(ctx.app, a, "tools/list")).status).toBe(200);
    const limited = await mcp(ctx.app, a, "tools/list");
    expect(limited.status).toBe(429);
    expect(Number(limited.headers["retry-after"])).toBeGreaterThan(0);
    expect((await mcp(ctx.app, b, "tools/list")).status).toBe(200);
  });
});

describe("logs", () => {
  it("record user, tenant, client, tool, arguments and outcome, but no token or document text", async () => {
    const ctx = await setup();
    const token = await ctx.issuer.token({ sub: "priya", tenant: "trevor-co", groups: ["procurement"], jti: "tok-123" });
    await callTool(ctx.app, token, "get_doc", { id: "doc-supplier-contract" });
    await callTool(ctx.app, token, "get_doc", { id: "doc-board-minutes" });

    expect(ctx.logs).toHaveLength(2);
    expect(ctx.logs[0]).toMatchObject({
      event: "tool_call", user: "priya", tenant: "trevor-co", client: "test-client",
      tool: "get_doc", arguments: { id: "doc-supplier-contract" }, resultCount: 1, outcome: "ok", tokenId: "tok-123",
    });
    expect(ctx.logs[1]).toMatchObject({ arguments: { id: "doc-board-minutes" }, outcome: "not_found", resultCount: 0 });

    const all = JSON.stringify(ctx.logs);
    expect(all).not.toContain(token);
    expect(all).not.toContain(token.split(".")[2]); // not even the signature
    expect(all).not.toContain("60-day notice period"); // no document text
  });
});
