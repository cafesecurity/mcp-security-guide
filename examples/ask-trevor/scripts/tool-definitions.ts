// Fetch the tool list exactly as a client sees it, over HTTP, with a test token.
import { createHash } from "node:crypto";
import { mcp, setup } from "../test/helpers.js";

export async function currentToolDefinitions(): Promise<unknown[]> {
  const { app, issuer } = await setup();
  const res = await mcp(app, await issuer.token({ tenant: "trevor-co", groups: ["all-staff"] }), "tools/list");
  if (res.status !== 200) throw new Error(`tools/list failed: HTTP ${res.status}`);
  return res.body.result.tools as unknown[];
}

/** Stable serialisation: what gets committed and hashed. */
export function serialise(tools: unknown[]): string {
  return `${JSON.stringify(tools, null, 2)}\n`;
}

export function sha256(text: string): string {
  return createHash("sha256").update(text).digest("hex");
}
