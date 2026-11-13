// Fake credentials for the audit sandbox (same set as canaries.py). Every value
// contains the run's secret canary. None of them is real.
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const FILES = {
  ".ssh/id_rsa": (c) => `-----BEGIN OPENSSH PRIVATE KEY-----\nFAKE-AUDIT-KEY-${c}\n-----END OPENSSH PRIVATE KEY-----\n`,
  ".aws/credentials": (c) => `[default]\naws_access_key_id = AKIA${c}\naws_secret_access_key = ${c}SECRET\n`,
  ".config/gh/hosts.yml": (c) => `github.com:\n    oauth_token: ghp_${c}\n`,
  ".npmrc": (c) => `//registry.npmjs.org/:_authToken=npm_${c}\n`,
  ".env": (c) => `DATABASE_URL=postgres://audit:${c}@db.internal.invalid/prod\n`,
  ".cursor/mcp.json": (c) => `{"mcpServers": {"crm": {"env": {"API_KEY": "${c}"}}}}\n`,
  ".config/Claude/claude_desktop_config.json": (c) => `{"mcpServers": {"db": {"env": {"DB_PASSWORD": "${c}"}}}}\n`,
};

export function plant() {
  const c = process.env.AUDIT_SECRET_CANARY;
  const home = process.env.HOME || "/home/audit";
  if (!c) return;
  for (const [rel, make] of Object.entries(FILES)) {
    const p = path.join(home, rel);
    mkdirSync(path.dirname(p), { recursive: true });
    writeFileSync(p, make(c));
  }
}
