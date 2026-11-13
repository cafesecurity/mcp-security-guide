// A local test issuer: signs access tokens with a throwaway key so the tests,
// and `npm run dev`, never touch a real identity provider.
// NOT FOR PRODUCTION. Use your own identity provider; see README.md.

import { createLocalJWKSet, exportJWK, generateKeyPair, SignJWT, type JWK } from "jose";

export const TEST_ISSUER = "http://127.0.0.1:9999/test-issuer";
export const TEST_RESOURCE = "http://127.0.0.1:3333/mcp";

export interface TokenClaims {
  sub?: string;
  tenant?: string;
  groups?: string[];
  scope?: string;
  client_id?: string;
  aud?: string;
  iss?: string;
  /** Seconds from now; negative for an expired token. */
  expiresIn?: number;
  jti?: string;
}

export async function createTestIssuer() {
  const { privateKey, publicKey } = await generateKeyPair("RS256");
  const jwk: JWK = { ...(await exportJWK(publicKey)), kid: "test-key", alg: "RS256", use: "sig" };
  const keys = createLocalJWKSet({ keys: [jwk] });

  // A second key the server doesn't trust, for "wrong signer" tests.
  const { privateKey: strangerKey } = await generateKeyPair("RS256");

  async function sign(claims: TokenClaims, key = privateKey, kid = "test-key"): Promise<string> {
    const now = Math.floor(Date.now() / 1000);
    const { aud, iss, expiresIn, sub, ...rest } = claims;
    return new SignJWT({ scope: "docs.read", client_id: "test-client", ...rest })
      .setProtectedHeader({ alg: "RS256", kid })
      .setIssuer(iss ?? TEST_ISSUER)
      .setAudience(aud ?? TEST_RESOURCE)
      .setSubject(sub ?? "alice")
      .setIssuedAt(now)
      .setExpirationTime(now + (expiresIn ?? 300))
      .setJti(claims.jti ?? `jti-${Math.random().toString(36).slice(2)}`)
      .sign(key);
  }

  return {
    keys,
    /** A token from the trusted test issuer. */
    token: (claims: TokenClaims = {}) => sign(claims),
    /** A correctly formed token signed by a key the server does not trust. */
    strangerToken: (claims: TokenClaims = {}) => sign(claims, strangerKey, "test-key"),
  };
}
