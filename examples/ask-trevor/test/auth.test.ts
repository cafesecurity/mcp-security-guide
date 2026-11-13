// Authorisation tests from guide/04-test.md, "The minimum test list".
import request from "supertest";
import { beforeAll, describe, expect, it } from "vitest";
import { TEST_ISSUER, TEST_RESOURCE } from "./issuer.js";
import { mcp, setup } from "./helpers.js";

let ctx: Awaited<ReturnType<typeof setup>>;
const staff = { tenant: "trevor-co", groups: ["all-staff"] };

beforeAll(async () => {
  ctx = await setup();
});

function expectInvalidToken(res: request.Response) {
  expect(res.status).toBe(401);
  const challenge = res.headers["www-authenticate"] ?? "";
  expect(challenge).toMatch(/^Bearer /);
  expect(challenge).toContain('error="invalid_token"');
  expect(challenge).toContain("resource_metadata=");
}

describe("authorisation", () => {
  it("accepts a valid token for this server", async () => {
    const res = await mcp(ctx.app, await ctx.issuer.token(staff), "tools/list");
    expect(res.status).toBe(200);
    expect(res.body.result.tools).toHaveLength(2);
  });

  it("no token: 401 with a challenge pointing to the protected resource metadata", async () => {
    const res = await mcp(ctx.app, undefined, "tools/list");
    expectInvalidToken(res);
    expect(res.headers["www-authenticate"]).toContain("/.well-known/oauth-protected-resource/mcp");
  });

  it("a token for a different audience, from our own issuer: 401", async () => {
    const token = await ctx.issuer.token({ ...staff, aud: "https://mail.example.com/api" });
    expectInvalidToken(await mcp(ctx.app, token, "tools/list"));
  });

  it("a token from a different issuer: 401", async () => {
    const token = await ctx.issuer.token({ ...staff, iss: "https://evil.example/issuer" });
    expectInvalidToken(await mcp(ctx.app, token, "tools/list"));
  });

  it("a token signed by a key we don't trust: 401", async () => {
    const token = await ctx.issuer.strangerToken(staff);
    expectInvalidToken(await mcp(ctx.app, token, "tools/list"));
  });

  it("an expired token: 401", async () => {
    const token = await ctx.issuer.token({ ...staff, expiresIn: -60 });
    expectInvalidToken(await mcp(ctx.app, token, "tools/list"));
  });

  it("a token without the tenant claim: 401", async () => {
    const token = await ctx.issuer.token({ groups: ["all-staff"] });
    expectInvalidToken(await mcp(ctx.app, token, "tools/list"));
  });

  it("a token without the docs.read scope: 403 insufficient_scope naming the scope", async () => {
    const token = await ctx.issuer.token({ ...staff, scope: "profile" });
    const res = await mcp(ctx.app, token, "tools/list");
    expect(res.status).toBe(403);
    const challenge = res.headers["www-authenticate"] ?? "";
    expect(challenge).toContain('error="insufficient_scope"');
    expect(challenge).toContain('scope="docs.read"');
  });

  it("a token in the query string instead of the header: rejected", async () => {
    const token = await ctx.issuer.token(staff);
    const res = await request(ctx.app)
      .post(`/mcp?access_token=${encodeURIComponent(token)}`)
      .set("Content-Type", "application/json")
      .set("Accept", "application/json, text/event-stream")
      .send({ jsonrpc: "2.0", id: 1, method: "tools/list", params: {} });
    expectInvalidToken(res);
  });

  it("a token with the 'none' algorithm: 401", async () => {
    const enc = (o: object) => Buffer.from(JSON.stringify(o)).toString("base64url");
    const now = Math.floor(Date.now() / 1000);
    const unsigned = `${enc({ alg: "none", typ: "JWT" })}.${enc({
      iss: TEST_ISSUER, aud: TEST_RESOURCE, sub: "alice", tenant: "trevor-co", scope: "docs.read", exp: now + 300,
    })}.`;
    expectInvalidToken(await mcp(ctx.app, unsigned, "tools/list"));
  });
});

describe("protected resource metadata (RFC 9728)", () => {
  it("names this resource, its authorisation server and only the minimal scope", async () => {
    const res = await request(ctx.app).get("/.well-known/oauth-protected-resource/mcp");
    expect(res.status).toBe(200);
    expect(res.body.resource).toBe(TEST_RESOURCE);
    expect(res.body.authorization_servers).toEqual([`${TEST_ISSUER}`]);
    expect(res.body.scopes_supported).toEqual(["docs.read"]);
  });
});
