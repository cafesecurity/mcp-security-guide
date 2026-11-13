// Access-token verification for a remote MCP server acting as an OAuth 2.1 resource server.
// Guide: guide/02-design.md, "Which tokens does the server accept?"; guide/03-build.md, "6. Validate every token".

import { jwtVerify, errors as joseErrors, type JWTVerifyGetKey } from "jose";
import { OAuthError, OAuthErrorCode, type AuthInfo, type OAuthTokenVerifier } from "@modelcontextprotocol/server";
import type { Caller } from "./corpus.js";

export interface VerifierOptions {
  /** The authorisation server's issuer identifier, compared exactly. */
  issuer: string;
  /** This server's canonical URI: the only audience we accept. */
  audience: string;
  /** Signing keys, usually createRemoteJWKSet(new URL(jwksUri)). */
  keys: JWTVerifyGetKey;
  /** Accepted signature algorithms. Never "none". */
  algorithms?: string[];
}

/**
 * Verifies a JWT access token: signature, pinned algorithm, issuer, audience,
 * expiry, and the claims this server needs. Anything else is refused with
 * invalid_token, which the SDK turns into a 401 with a WWW-Authenticate challenge.
 *
 * The token is never forwarded anywhere. If this server called an upstream API
 * it would obtain a separate token for it (token exchange or on-behalf-of).
 */
export function jwtVerifier(opts: VerifierOptions): OAuthTokenVerifier {
  const algorithms = opts.algorithms ?? ["RS256", "ES256"];
  return {
    async verifyAccessToken(token: string): Promise<AuthInfo> {
      let payload;
      try {
        ({ payload } = await jwtVerify(token, opts.keys, {
          issuer: opts.issuer,
          audience: opts.audience, // the line people forget
          algorithms,
          requiredClaims: ["exp", "sub", "aud", "iss"],
          clockTolerance: 5,
        }));
      } catch (err) {
        // Don't echo verification details back to the caller.
        const reason = err instanceof joseErrors.JWTExpired ? "token expired" : "invalid token";
        throw new OAuthError(OAuthErrorCode.InvalidToken, reason);
      }

      const tenant = typeof payload.tenant === "string" ? payload.tenant : undefined;
      if (!tenant) throw new OAuthError(OAuthErrorCode.InvalidToken, "invalid token");

      const scopes = typeof payload.scope === "string" ? payload.scope.split(" ").filter(Boolean) : [];
      const groups = Array.isArray(payload.groups) ? payload.groups.filter((g): g is string => typeof g === "string") : [];
      const clientId =
        typeof payload.client_id === "string" ? payload.client_id : typeof payload.azp === "string" ? payload.azp : "unknown";

      return {
        token,
        clientId,
        scopes,
        expiresAt: payload.exp,
        // The audience the token actually carries, so the SDK's expectedResource
        // check is a genuine second check rather than an echo of our setting.
        resource: tokenAudience(payload.aud, opts.audience),
        extra: { sub: payload.sub, tenant, groups, jti: payload.jti },
      };
    },
  };
}

function tokenAudience(aud: string | string[] | undefined, expected: string): URL {
  const values = Array.isArray(aud) ? aud : aud ? [aud] : [];
  const chosen = values.find((v) => v === expected) ?? values[0];
  try {
    return new URL(chosen ?? "");
  } catch {
    throw new OAuthError(OAuthErrorCode.InvalidToken, "invalid token");
  }
}

/** The caller as the tools see it: only what the verified token says. */
export function callerFrom(auth: AuthInfo | undefined): Caller {
  const extra = auth?.extra ?? {};
  const sub = extra.sub;
  const tenant = extra.tenant;
  if (typeof sub !== "string" || typeof tenant !== "string") {
    // Unreachable behind requireBearerAuth; fail closed if it ever happens.
    throw new Error("no verified caller");
  }
  const groups = Array.isArray(extra.groups) ? (extra.groups as string[]) : [];
  return { sub, tenant, groups };
}
