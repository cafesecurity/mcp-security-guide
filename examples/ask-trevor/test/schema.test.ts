// Injection through arguments, from guide/04-test.md: the schema refuses bad input.
import { beforeAll, describe, expect, it } from "vitest";
import { mcp, setup } from "./helpers.js";

let ctx: Awaited<ReturnType<typeof setup>>;
let token: string;

beforeAll(async () => {
  ctx = await setup();
  token = await ctx.issuer.token({ tenant: "trevor-co", groups: ["all-staff"] });
});

async function rejected(name: string, args: Record<string, unknown>) {
  const res = await mcp(ctx.app, token, "tools/call", { name, arguments: args });
  // Either a JSON-RPC error or a tool error result; never a successful call.
  const failed = res.status >= 400 || res.body.error !== undefined || res.body.result?.isError === true;
  expect(failed, JSON.stringify(res.body)).toBe(true);
  expect(ctx.logs.filter((l) => l.outcome === "ok" && l.tool === name && JSON.stringify(l.arguments).includes("UNIQUE"))).toEqual([]);
}

describe("strict input schemas", () => {
  it("rejects an over-long query", () => rejected("search_docs", { query: `UNIQUE${"x".repeat(300)}` }));
  it("rejects an empty query", () => rejected("search_docs", { query: "" }));
  it("rejects a limit above 25", () => rejected("search_docs", { query: "UNIQUE", limit: 1000 }));
  it("rejects a non-integer limit", () => rejected("search_docs", { query: "UNIQUE", limit: 2.5 }));
  it("rejects the wrong type", () => rejected("search_docs", { query: ["UNIQUE"] }));
  it("rejects unknown properties", () => rejected("search_docs", { query: "UNIQUE", tenant: "other-co" }));
  it("rejects path traversal in a document ID", () => rejected("get_doc", { id: "../../etc/passwd" }));
  it("rejects shell metacharacters in a document ID", () => rejected("get_doc", { id: "doc-x;rm -rf /" }));
  it("rejects a caller trying to pick their own user", () => rejected("get_doc", { id: "doc-board-minutes", sub: "dana" }));
});
