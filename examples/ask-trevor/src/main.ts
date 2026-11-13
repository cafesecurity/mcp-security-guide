// Production-style entry point. All configuration comes from the environment;
// there are no defaults for anything security-relevant.
//
//   MCP_RESOURCE_URL   this server's canonical URI, e.g. https://trevor.example.com/mcp
//   OAUTH_ISSUER       your identity provider's issuer identifier
//   OAUTH_JWKS_URL     its signing keys
//   OAUTH_AUTHORIZE_URL, OAUTH_TOKEN_URL   its endpoints, advertised to clients
//   HOST, PORT         bind address (default 127.0.0.1:3333)
//   ALLOWED_HOSTS      comma-separated hostnames; required if HOST is not loopback
//
// This example serves a bundled, made-up corpus. See README.md.

import { createRemoteJWKSet } from "jose";
import { jwtVerifier } from "./auth.js";
import { memoryStore, SAMPLE_DOCS } from "./corpus.js";
import { stderrSink } from "./log.js";
import { createApp } from "./server.js";

function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`missing environment variable ${name}`);
  return v;
}

const resourceUrl = new URL(required("MCP_RESOURCE_URL"));
const issuer = required("OAUTH_ISSUER");
const host = process.env.HOST ?? "127.0.0.1";
const port = Number(process.env.PORT ?? "3333");
const allowedHosts = process.env.ALLOWED_HOSTS?.split(",").map((h) => h.trim()).filter(Boolean);

const app = createApp({
  resourceUrl,
  issuer,
  authorizationEndpoint: required("OAUTH_AUTHORIZE_URL"),
  tokenEndpoint: required("OAUTH_TOKEN_URL"),
  verifier: jwtVerifier({
    issuer,
    audience: resourceUrl.href,
    keys: createRemoteJWKSet(new URL(required("OAUTH_JWKS_URL"))),
  }),
  store: memoryStore(SAMPLE_DOCS),
  log: stderrSink,
  host,
  ...(allowedHosts ? { allowedHosts } : {}),
});

app.listen(port, host, () => {
  process.stderr.write(`ask-trevor-example listening on http://${host}:${port}${resourceUrl.pathname}\n`);
});
