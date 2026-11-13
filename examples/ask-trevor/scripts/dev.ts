// Local development only: runs the server on 127.0.0.1 with the throwaway test
// issuer and prints a short-lived token for each sample user.
// NOT FOR PRODUCTION. Production uses src/main.ts and your own identity provider.
import { jwtVerifier } from "../src/auth.js";
import { memoryStore, SAMPLE_DOCS } from "../src/corpus.js";
import { stderrSink } from "../src/log.js";
import { createApp } from "../src/server.js";
import { createTestIssuer, TEST_ISSUER, TEST_RESOURCE } from "../test/issuer.js";

const issuer = await createTestIssuer();
const app = createApp({
  resourceUrl: new URL(TEST_RESOURCE),
  issuer: TEST_ISSUER,
  authorizationEndpoint: `${TEST_ISSUER}/authorize`,
  tokenEndpoint: `${TEST_ISSUER}/token`,
  verifier: jwtVerifier({ issuer: TEST_ISSUER, audience: TEST_RESOURCE, keys: issuer.keys }),
  store: memoryStore(SAMPLE_DOCS),
  log: stderrSink,
});

const users = {
  alice: ["all-staff"],
  priya: ["all-staff", "procurement"],
  dana: ["all-staff"],
};

app.listen(3333, "127.0.0.1", async () => {
  console.log(`Ask Trevor (example) on ${TEST_RESOURCE}  [development only: test issuer, tokens valid 1 hour]\n`);
  for (const [sub, groups] of Object.entries(users)) {
    console.log(`${sub.padEnd(6)} ${await issuer.token({ sub, tenant: "trevor-co", groups, expiresIn: 3600 })}\n`);
  }
});
