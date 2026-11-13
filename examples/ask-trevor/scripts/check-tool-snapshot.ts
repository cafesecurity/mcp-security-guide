// Compare the live tool definitions with the committed snapshot.
//   npm run snapshot:check    exit 1 if they differ (CI)
//   npm run snapshot:update   rewrite the snapshot (then bump the version and update CHANGELOG.md)
// Guide: guide/07-change.md. Publish the printed hash with each release (guide/05-release.md).
import { readFileSync, writeFileSync } from "node:fs";
import { currentToolDefinitions, serialise, sha256 } from "./tool-definitions.js";

const FILE = new URL("../tool-definitions.snapshot.json", import.meta.url);
const live = serialise(await currentToolDefinitions());

if (process.argv.includes("--update")) {
  writeFileSync(FILE, live);
  console.log(`snapshot updated; sha256 ${sha256(live)}`);
  console.log("Now bump the version in src/tools.ts and package.json, and describe the change in CHANGELOG.md.");
} else {
  const committed = readFileSync(FILE, "utf8");
  if (committed !== live) {
    console.error("Tool definitions differ from tool-definitions.snapshot.json.");
    console.error("Every change to a tool's name, description, schema or annotations needs human review,");
    console.error("a version bump and a CHANGELOG entry. Run `npm run snapshot:update` once approved.");
    process.exit(1);
  }
  console.log(`tool definitions match the snapshot; sha256 ${sha256(live)}`);
}
