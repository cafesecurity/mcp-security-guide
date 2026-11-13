// Tenant and user isolation from guide/04-test.md. Runs on every build.
import { beforeAll, describe, expect, it } from "vitest";
import { callTool, setup } from "./helpers.js";

let ctx: Awaited<ReturnType<typeof setup>>;
let alice: string; // all-staff only
let priya: string; // procurement
let dana: string; // board member, by user
let otherCo: string; // a user in another tenant, in every group

beforeAll(async () => {
  ctx = await setup();
  alice = await ctx.issuer.token({ sub: "alice", tenant: "trevor-co", groups: ["all-staff"] });
  priya = await ctx.issuer.token({ sub: "priya", tenant: "trevor-co", groups: ["all-staff", "procurement"] });
  dana = await ctx.issuer.token({ sub: "dana", tenant: "trevor-co", groups: ["all-staff"] });
  otherCo = await ctx.issuer.token({ sub: "olu", tenant: "other-co", groups: ["all-staff", "legal", "procurement"] });
});

const ids = (data: unknown) => ((data as { results: { id: string }[] }).results ?? []).map((r) => r.id);

describe("isolation", () => {
  it("a document the user may not read looks exactly like one that doesn't exist", async () => {
    const forbidden = await callTool(ctx.app, alice, "get_doc", { id: "doc-board-minutes" });
    const missing = await callTool(ctx.app, alice, "get_doc", { id: "doc-does-not-exist" });
    expect(forbidden.data).toEqual({ error: "not_found" });
    expect(missing.data).toEqual(forbidden.data);
  });

  it("the named user can read a document shared with them by user", async () => {
    const res = await callTool(ctx.app, dana, "get_doc", { id: "doc-board-minutes" });
    expect((res.data as { id: string }).id).toBe("doc-board-minutes");
  });

  it("search never returns documents outside the caller's access list", async () => {
    expect(ids((await callTool(ctx.app, alice, "search_docs", { query: "supplier" })).data)).toEqual([]);
    expect(ids((await callTool(ctx.app, priya, "search_docs", { query: "supplier" })).data)).toEqual([
      "doc-supplier-contract",
      "doc-supplier-quote",
    ]);
  });

  it("another tenant's user never sees this tenant's documents, even with matching groups", async () => {
    const found = ids((await callTool(ctx.app, otherCo, "search_docs", { query: "supplier contract" })).data);
    expect(found).toEqual(["doc-other-tenant"]);
    const direct = await callTool(ctx.app, otherCo, "get_doc", { id: "doc-supplier-contract" });
    expect(direct.data).toEqual({ error: "not_found" });
  });

  it("this tenant's users never see another tenant's documents", async () => {
    const found = ids((await callTool(ctx.app, priya, "search_docs", { query: "another organisation" })).data);
    expect(found).toEqual([]);
    const direct = await callTool(ctx.app, priya, "get_doc", { id: "doc-other-tenant" });
    expect(direct.data).toEqual({ error: "not_found" });
  });

  it("the same query by two users back to back gives each their own results", async () => {
    const a = ids((await callTool(ctx.app, priya, "search_docs", { query: "board" })).data);
    const b = ids((await callTool(ctx.app, dana, "search_docs", { query: "board" })).data);
    expect(a).toEqual([]);
    expect(b).toEqual(["doc-board-minutes"]);
  });
});
