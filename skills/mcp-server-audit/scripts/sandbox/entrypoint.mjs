// Sandbox entrypoint for Node servers: plant canary credentials in the throwaway
// home directory, then run the server with this process's stdin and stdout.
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { plant } from "./canaries.mjs";

plant();
const mode = process.env.AUDIT_MODE;
let script;
if (mode === "npm") {
  const pkg = process.env.AUDIT_NPM_PACKAGE;
  const dir = path.join("/srv/node_modules", pkg);
  const manifest = JSON.parse(readFileSync(path.join(dir, "package.json"), "utf8"));
  let bin = manifest.bin;
  if (bin && typeof bin === "object") bin = bin[process.env.AUDIT_BIN || Object.keys(bin)[0]];
  script = path.join(dir, bin || manifest.main || "index.js");
} else if (mode === "local") {
  process.chdir("/srv/app");
  script = path.join("/srv/app", process.env.AUDIT_RUN);
} else {
  console.error("audit sandbox: AUDIT_MODE must be npm or local");
  process.exit(2);
}
const child = spawn(process.execPath, [script, ...process.argv.slice(2)], { stdio: "inherit" });
for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => child.kill(sig));
child.on("exit", (code, signal) => process.exit(code ?? (signal ? 1 : 0)));
