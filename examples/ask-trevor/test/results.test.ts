// Hostile content in results, from guide/04-test.md. The supplier quote in the
// sample corpus carries hidden instructions, invisible characters, a terminal
// escape and an image link.
import { beforeAll, describe, expect, it } from "vitest";
import { plainText } from "../src/text.js";
import { callTool, setup } from "./helpers.js";

let ctx: Awaited<ReturnType<typeof setup>>;
let priya: string;

beforeAll(async () => {
  ctx = await setup();
  priya = await ctx.issuer.token({ sub: "priya", tenant: "trevor-co", groups: ["all-staff", "procurement"] });
});

describe("results are data", () => {
  it("tags outsiders' documents as external and staff documents as internal", async () => {
    const res = await callTool(ctx.app, priya, "search_docs", { query: "supplier" });
    const results = (res.data as { results: { id: string; source: string }[] }).results;
    expect(Object.fromEntries(results.map((r) => [r.id, r.source]))).toEqual({
      "doc-supplier-contract": "internal",
      "doc-supplier-quote": "external",
    });
  });

  it("strips hidden instructions, invisible characters, escapes and links from a hostile document", async () => {
    const res = await callTool(ctx.app, priya, "get_doc", { id: "doc-supplier-quote" });
    const text = res.raw.result.content[0].text as string;
    expect(text).not.toMatch(/ignore previous instructions/i);
    expect(text).not.toMatch(/attacker\.example/);
    expect(text).not.toMatch(/https?:/);
    expect(text).not.toMatch(/[​-‏‪-‮⁠-⁩﻿]/);
    expect(text).not.toContain("\\u001b");
    expect((res.data as { body: string }).body).toContain("Our renewal price is £48,000.");
    expect((res.data as { source: string }).source).toBe("external");
  });
});

describe("plainText", () => {
  it.each([
    ["zero-width characters", "a​b‍c﻿", "abc"],
    ["bidirectional overrides", "abc‮dcba", "abcdcba"],
    ["tag characters", "hi\u{e0041}\u{e0042}", "hi"],
    ["terminal escapes", "\u001b[31mred\u001b[0m", "red"],
    ["OSC escapes", "\u001b]0;title\u0007text", "text"],
    ["HTML comments", "a<!-- secret -->b", "ab"],
    ["HTML tags", "<b>bold</b> <img src=x onerror=y>", "bold"],
    ["tag rebuilt by removing an inner comment", "<<!-- -->script>x", "x"],
    ["tag rebuilt twice over", "<<<b>b>script>z", "z"],
    ["unclosed comment", "a<!-- hidden", "a‹!-- hidden"],
    ["unclosed tag", "x<script src=y", "x‹script src=y"],
    ["comparisons are kept", "1 < 2 and x <= y", "1 < 2 and x <= y"],
    ["tag rebuilt from a split opening bracket", "<<b>script>x", "x"],
    ["comment rebuilt by removing an inner comment", "a<!<!-- x -->-- hidden -->b", "ab"],
    ["markdown images", "see ![x](https://e.example/p.png?d=1)", "see [image removed]"],
    ["markdown links keep their text", "read [the terms](https://e.example/t)", "read the terms"],
    ["bare URLs", "go to https://e.example/x now", "go to [link removed] now"],
    ["javascript URLs", "click javascript:alert(1)", "click [link removed]"],
  ])("removes %s", (_label, input, expected) => {
    expect(plainText(input)).toBe(expected);
  });
});
