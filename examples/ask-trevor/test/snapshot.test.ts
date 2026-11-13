// The tool list must match the committed snapshot exactly (guide/04-test.md, guide/07-change.md).
// A failure here is not a test to "fix": it means a tool definition changed and needs review,
// a version bump and a changelog entry before `npm run snapshot:update`.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { currentToolDefinitions, serialise } from "../scripts/tool-definitions.js";

describe("tool definitions", () => {
  it("match tool-definitions.snapshot.json exactly", async () => {
    const committed = readFileSync(new URL("../tool-definitions.snapshot.json", import.meta.url), "utf8");
    expect(serialise(await currentToolDefinitions())).toBe(committed);
  });

  it("are all read-only and never address the model or mention other tools", async () => {
    const tools = (await currentToolDefinitions()) as {
      name: string; description: string; annotations?: { readOnlyHint?: boolean };
    }[];
    for (const t of tools) {
      expect(t.annotations?.readOnlyHint, t.name).toBe(true);
      expect(t.description, t.name).not.toMatch(/\b(you must|always|ignore|assistant|AI|model|instead of)\b/i);
      expect(t.description, t.name).not.toMatch(/[​-‏‪-‮⁠-⁩﻿<>]/);
    }
  });
});
