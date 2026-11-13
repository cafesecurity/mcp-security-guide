// HTTP wiring: protected resource metadata, bearer authentication, rate limit,
// and a stateless MCP handler (spec 2026-07-28: no sessions; one server per request).
// Guide: guide/03-build.md ("6. Validate every token", "7. Localhost is not a wall",
//        "8. Check that headers match the body"); guide/06-deploy-operate.md.

import type { Express } from "express";
import { createMcpHandler, getOAuthProtectedResourceMetadataUrl, type OAuthTokenVerifier } from "@modelcontextprotocol/server";
import { createMcpExpressApp, mcpAuthMetadataRouter, requireBearerAuth } from "@modelcontextprotocol/express";
import { toNodeHandler } from "@modelcontextprotocol/node";
import type { DocStore } from "./corpus.js";
import type { LogSink } from "./log.js";
import { perUserRateLimit } from "./ratelimit.js";
import { buildServer } from "./tools.js";

export const SCOPE_READ = "docs.read";

export interface AppOptions {
  /** This server's canonical URI, e.g. https://trevor.example.com/mcp. Also the token audience. */
  resourceUrl: URL;
  /** The authorisation server's issuer identifier. */
  issuer: string;
  /** Authorisation server metadata (RFC 8414), advertised to clients. */
  authorizationEndpoint: string;
  tokenEndpoint: string;
  verifier: OAuthTokenVerifier;
  store: DocStore;
  log: LogSink;
  /**
   * Interface to bind to. Defaults to 127.0.0.1, which also turns on the SDK's
   * Host and Origin validation against DNS rebinding.
   */
  host?: string;
  /** Required when host is not a loopback address: the hostnames clients use. */
  allowedHosts?: string[];
  rateLimit?: { limit: number; windowMs: number };
}

const LOOPBACK = new Set(["127.0.0.1", "localhost", "::1"]);

export function createApp(opts: AppOptions): Express {
  const host = opts.host ?? "127.0.0.1";
  if (!LOOPBACK.has(host) && !opts.allowedHosts?.length) {
    // Fail closed: binding beyond loopback without a Host allow-list disables rebinding protection.
    throw new Error(`host ${host} needs allowedHosts`);
  }

  const app = createMcpExpressApp({
    host,
    ...(opts.allowedHosts ? { allowedHosts: opts.allowedHosts, allowedOrigins: opts.allowedHosts } : {}),
    jsonLimit: "64kb",
  });
  app.disable("x-powered-by");

  // RFC 9728 protected resource metadata, so clients can find the authorisation server.
  app.use(
    mcpAuthMetadataRouter({
      resourceServerUrl: opts.resourceUrl,
      scopesSupported: [SCOPE_READ], // the minimal set; nothing else exists here
      resourceName: "Ask Trevor (example)",
      oauthMetadata: {
        issuer: opts.issuer,
        authorization_endpoint: opts.authorizationEndpoint,
        token_endpoint: opts.tokenEndpoint,
        response_types_supported: ["code"],
        grant_types_supported: ["authorization_code", "refresh_token"],
        code_challenge_methods_supported: ["S256"],
        authorization_response_iss_parameter_supported: true,
      },
    }),
  );

  const resourceMetadataUrl = getOAuthProtectedResourceMetadataUrl(opts.resourceUrl);
  const handler = createMcpHandler((ctx) => buildServer(ctx.authInfo, { store: opts.store, log: opts.log }), {
    legacy: "reject", // 2026-07-28 only: no sessions, no 2025-era handshake
  });
  const serve = toNodeHandler(handler);

  app.post(
    opts.resourceUrl.pathname,
    // Token in the Authorization header only; signature, issuer, audience, expiry and scope checked.
    requireBearerAuth({
      verifier: opts.verifier,
      requiredScopes: [SCOPE_READ],
      resourceMetadataUrl,
      expectedResource: opts.resourceUrl,
    }),
    perUserRateLimit(opts.rateLimit ?? { limit: 60, windowMs: 60_000 }),
    (req, res) => serve(req, res, req.body),
  );

  // No GET stream and no sessions in 2026-07-28.
  app.all(opts.resourceUrl.pathname, (_req, res) => {
    res.status(405).set("Allow", "POST").end();
  });

  return app;
}
