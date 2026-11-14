# Sources

*As of 13 November 2026.*

Every factual claim in this guide, where it was checked and when. If you find a claim that is not here, or a source that no longer says what we say it does, please [open a correction](../.github/ISSUE_TEMPLATE/correction.md).

**Status values.** *Verified* means the primary source was opened and says what the guide says. *Verified (press)* means reliable secondary reporting was used because the primary source was unavailable. *Guide's own* means it is this guide's analysis or example, not a fact about the world.

## Protocol and specification

| # | Claim | Status | Checked | Source |
| --- | --- | --- | --- | --- |
| P1 | MCP launched in November 2024 and was donated to the Agentic AI Foundation, a Linux Foundation fund, in December 2025 | Verified | Nov 2026 | [MCP blog](https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/) |
| P2 | The 2026-07-28 specification is stateless and has no protocol sessions | Verified | 13 Nov 2026 | [Security Best Practices, State Handle Hijacking](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) |
| P3 | Authorisation is optional; HTTP implementations SHOULD follow it; STDIO implementations SHOULD NOT and take credentials from the environment | Verified | 13 Nov 2026 | [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) |
| P4 | Every row of the spec checklist, sections 1 to 4 and 9 | Verified against the page text | 13 Nov 2026 | [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization); [Security Considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations) |
| P5 | Every row of the spec checklist, sections 5 to 8, and the common scope mistakes | Verified against the page text | 13 Nov 2026 | [Security Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) |
| P6 | Dynamic Client Registration is deprecated in favour of Client ID Metadata Documents | Verified | 13 Nov 2026 | [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) |
| P7 | RFC 8707 resource indicators bind tokens to an audience only when the AS supports them | Verified | 13 Nov 2026 | [Security Considerations](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/security-considerations); [RFC 8707](https://datatracker.ietf.org/doc/html/rfc8707) |
| P8 | PKCE alone does not stop mix-up attacks; the `iss` check does, if honest servers emit `iss` | Verified | 13 Nov 2026 | [Security Best Practices, Mix-Up Attacks](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices) |
| P9 | Every row of the spec checklist, section 10 (Origin validation, localhost binding, header and body must match) | Verified against the page text | 13 Nov 2026 | [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) |
| P10 | Official SDKs: several shipped with DNS-rebinding protection off for local servers and have since fixed it | Verified | 9 Nov 2026 | [Python PYSEC-2026-1617](https://osv.dev/vulnerability/PYSEC-2026-1617); [TypeScript GHSA-w48q-cv73-mx4w](https://github.com/modelcontextprotocol/typescript-sdk/security/advisories/GHSA-w48q-cv73-mx4w); [Go CVE-2026-34742](https://api.osv.dev/v1/vulns/CVE-2026-34742) |
| P11 | The TypeScript SDK's `createMcpExpressApp` binds to 127.0.0.1 by default and adds Host and Origin validation for loopback binds; `createMcpHandler` checks headers against the body | Verified in the SDK's type definitions and by the example's tests | 13 Nov 2026 | `@modelcontextprotocol/express` 2.0.2, `@modelcontextprotocol/server` 2.4.0; [example tests](../examples/ask-trevor/test/transport.test.ts) |
| P12 | Tool annotations are hints, untrusted unless the server is trusted | Verified | Nov 2026 | [Spec: Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) |
| P13 | URL mode elicitation sends the user to a page on the server's own site for interactions that must not pass through the client; the spec names payments among its uses | Verified | 9 Nov 2026 | Spec: Elicitation (2026-07-28) |
| P14 | The official MCP Registry uses reverse-DNS names verified by GitHub, DNS or HTTP, checks package ownership (`mcpName`), lists hosted servers under `remotes`, and doesn't review code | Verified | 9 Nov 2026 | [MCP Registry](https://modelcontextprotocol.io/registry/about) |
| P15 | npm trusted publishing needs `id-token: write` and adds provenance automatically | Verified | 9 Nov 2026 | [npm docs: trusted publishers](https://docs.npmjs.com/trusted-publishers) |

## Models and tests

| # | Claim | Status | Checked | Source |
| --- | --- | --- | --- | --- |
| M1 | The lethal trifecta: private data, untrusted content, external communication (Simon Willison, June 2025) | Verified | Nov 2026 | [Simon Willison](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) |
| M2 | Agents Rule of Two wording, Meta, 31 October 2025; supplements rather than replaces least privilege | Verified | Nov 2026 | [Meta AI](https://ai.meta.com/blog/practical-ai-agent-security/) |
| M3 | Feed, Behaviour, Impact model | Guide's own | — | — |
| M4 | The eight server categories and their usual letters | Guide's own | — | — |
| M5 | The Ask Trevor example and its identity models | Guide's own (hypothetical) | — | [examples/ask-trevor](../examples/ask-trevor/) |

## Frameworks

| # | Claim | Status | Checked | Source |
| --- | --- | --- | --- | --- |
| F1 | OWASP MCP Top 10 IDs and titles; 2025 list in beta | Verified | Nov 2026 | [OWASP](https://owasp.org/www-project-mcp-top-10/) |
| F2 | OWASP Top 10 for Agentic Applications published 9 December 2025 | Verified | 13 Nov 2026 | [OWASP GenAI Security Project](https://genai.owasp.org/) |
| F3 | ASI01 Agent Goal Hijack; ASI02 Tool Misuse | Verified (press) | 13 Nov 2026 | Titles are in OWASP's PDF; checked against several consistent summaries |
| F4 | OWASP Top 10 for LLM Applications 2026 edition published 4 August 2026; LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure | Verified (press) | 13 Nov 2026 | OWASP's project page could not be opened from our tools; checked against consistent search results |
| F5 | MITRE ATLAS technique, mitigation and case study IDs and names; no MCP-named technique | Verified | 13 Nov 2026 | [ATLAS data 5.6.0](https://github.com/mitre-atlas/atlas-data) |
| F6 | MAESTRO: CSA, February 2025, seven layers, six steps; tool misuse in layer 7, toolkits in layer 3 | Verified | Nov 2026 | [CSA](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro) |
| F7 | MAESTRO version 2 released June 2026 for open peer review | Verified | 13 Nov 2026 | [CSA MAESTRO v2](https://cloudsecurityalliance.org/artifacts/maestro-v2) |
| F8 | NIST's SP 800-53 overlay project (COSAiS) was renamed COSIS on 20 October 2026; agent overlays are planned but no draft is published | Verified | 13 Nov 2026 | [NIST CSRC](https://csrc.nist.gov/Projects/cosais) |
| F9 | NSA MCP guidance published 20 May 2026 | Verified | Nov 2026 | [NSA](https://www.nsa.gov/Press-Room/Press-Releases-Statements/Press-Release-View/Article/4496698/) |
| F10 | CoSAI MCP Security approved 8 January 2026 | Verified (title page) | Nov 2026 | [CoSAI](https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf) |

## Cases

| # | Claim | Status | Checked | Source |
| --- | --- | --- | --- | --- |
| C1 | OX Security STDIO findings; Anthropic's "expected behaviour" response; 9 of 11 registries | Verified (press) | Nov 2026 | [VentureBeat](https://venturebeat.com/security/mcp-stdio-flaw-200000-ai-agent-servers-exposed-ox-security-audit); [CSA research note](https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-rce-design-vulnerability-20260423-csa/) |
| C2 | Obsidian Security OAuth takeover; Square named; fixed late September 2025 | Verified | Nov 2026 | [Obsidian Security](https://www.obsidiansecurity.com/blog/when-mcp-meets-oauth-common-pitfalls-leading-to-one-click-account-takeover) |
| C3 | Claude Code CVE-2025-59536 (CVSS 8.7) and CVE-2026-21852 (CVSS v4.0 5.3) | Verified | Nov 2026 | [Check Point](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/); [GitHub advisory](https://github.com/anthropics/claude-code/security/advisories/GHSA-jh7p-qr78-84p7) |
| C4 | postmark-mcp: version 1.0.16, BCC to attacker, about 1,643 downloads, copied from the official server | Verified | Nov 2026 | [The Hacker News](https://thehackernews.com/2025/09/first-malicious-mcp-server-found.html); [Koi Security](https://www.koi.security/blog/postmark-mcp-npm-malicious-backdoor-email-theft); [ReversingLabs](https://www.reversinglabs.com/blog/postmark-mcp-attack-takeaways) |
| C5 | mcp-remote CVE-2025-6514, CVSS 9.6, full command execution on Windows | Verified | Nov 2026 | [JFrog](https://jfrog.com/blog/2025-6514-critical-mcp-remote-rce-vulnerability/) |
| C6 | Supabase MCP demonstration on a test project | Verified | Nov 2026 | [General Analysis](https://generalanalysis.com/blog/supabase-mcp-blog) |
| C7 | MCP Inspector CVE-2025-49596, CVSS 9.4, fixed in 0.14.1 | Verified | Nov 2026 | [Oligo](https://www.oligo.security/blog/critical-rce-vulnerability-in-anthropic-mcp-inspector-cve-2025-49596); [Tenable](https://www.tenable.com/blog/how-tenable-research-discovered-a-critical-remote-code-execution-vulnerability-on-anthropic) |
| C8 | Asana: launched 1 May, found 4 June, about 1,000 customers, back 17 June 2025 | Verified | Nov 2026 | [BleepingComputer](https://www.bleepingcomputer.com/news/security/asana-warns-mcp-ai-feature-exposed-customer-data-to-other-orgs/) |
| C9 | Jira Service Management "Living Off AI" was a proof of concept by Cato Networks, June 2025 | Verified | 13 Nov 2026 | [Cato Networks](https://www.catonetworks.com/blog/cato-ctrl-poc-attack-targeting-atlassians-mcp/); ATLAS AML.CS0039 |
| C10 | GitHub toxic agent flow, 26 May 2025 | Verified | Nov 2026 | [Invariant Labs](https://invariantlabs.ai/blog/mcp-github-vulnerability) |
| C11 | Tool poisoning, rug pull and WhatsApp demonstration, April 2025 | Verified | Nov 2026 | [Invariant Labs](https://invariantlabs.ai/blog/whatsapp-mcp-exploited) |
| C12 | EchoLeak (CVE-2025-32711) did not involve MCP; Replit's database wipe did not involve MCP | Verified | Nov 2026 | [Simon Willison on EchoLeak](https://simonwillison.net/2025/Jun/11/echoleak/); [Fast Company on Replit](https://www.fastcompany.com/91372483/replit-ceo-what-really-happened-when-ai-agent-wiped-jason-lemkins-database-exclusive) |
| C13 | The 9,403-server study measured cryptographic misuse: over half of the misuses found were in developer-tool and data-science servers | Verified (abstract) | 13 Nov 2026 | [arXiv 2512.03775](https://arxiv.org/abs/2512.03775) |
| C14 | WorkOS, October 2026: an autonomous testing agent escaped a researcher's test environment and reached an internal sales tool; four gaps (internet-reachable API, predictable development credential accepted in production, no rate limit, five days to detection); access cut on 30 October; WorkOS now tests itself with the same agent | Verified | 12 Nov 2026 | [WorkOS update, 6 Nov 2026](https://workos.com/security/bulletins/update-for-october-30th-2026-data-security-incident) |
| C15 | Shai-Hulud (September 2025) stole npm tokens and republished poisoned versions of victims' packages; npm classic tokens revoked 9 December 2025; trusted publishing launched July 2025 | Verified | 10 Nov 2026 | [GitHub changelog](https://github.blog/changelog/2025-12-09-npm-classic-tokens-revoked-session-based-auth-and-cli-token-management-now-available/) |
| C16 | TanStack, May 2026: malicious versions published through the project's trusted publisher; no npm tokens stolen; a short-lived OIDC token was extracted from the release runner | Verified | 10 Nov 2026 | [TanStack postmortem](https://tanstack.com/blog/npm-supply-chain-compromise-postmortem) |
| C17 | OX Security: 9 of 11 MCP marketplaces accepted a proof-of-concept malicious server (April 2026) | OX's own claim, attributed | 10 Nov 2026 | [VentureBeat](https://venturebeat.com/security/mcp-stdio-flaw-200000-ai-agent-servers-exposed-ox-security-audit) |
| C18 | UpGuard found misspelled MCP server names in real developers' configuration files | Verified | 10 Nov 2026 | [UpGuard](https://www.upguard.com/blog/typosquatting-in-the-mcp-ecosystem) |
| C19 | Package hallucination: in a USENIX Security 2025 study (Spracklen and others) of 576,000 samples from 16 models, 19.7% of recommended packages didn't exist; many invented names recurred on repeated prompts | Verified (secondary) | 13 Nov 2026 | [CSA research note](https://labs.cloudsecurityalliance.org/research/csa-research-note-slopsquatting-ai-supply-chain-20260419-csa/) summarising the paper |
| C20 | The UK NCSC says AI-driven attack activity has so far tended to generate noticeable security alerts | Verified | 12 Nov 2026 | [NCSC blog](https://www.ncsc.gov.uk/blogs/why-cyber-defenders-need-to-be-ready-for-frontier-ai) |

## Controls for organisations

| # | Claim | Status | Checked | Source |
| --- | --- | --- | --- | --- |
| O1 | Microsoft Zero Trust guidance on unsanctioned local agents, and an Intune policy to block them | Verified | Nov 2026 | [DEV-151](https://microsoft.github.io/zerotrustassessment/docs/workshop-guidance/devices/DEV_151); [AI-177](https://microsoft.github.io/zerotrustassessment/docs/workshop-guidance/AI/AI_177) |
| O2 | Microsoft 365 user consent settings and admin consent workflow | Verified | Nov 2026 | [Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/admin/misc/user-consent) |
| O3 | Google Workspace API controls for third-party app access | Verified | Nov 2026 | [Google Workspace Admin Help](https://knowledge.workspace.google.com/admin/apps/control-which-third-party-and-internal-apps-access-google-workspace-data) |
| O4 | GitHub Copilot enterprise MCP allow-lists fail closed (August 2026) | Verified | Nov 2026 | [GitHub changelog](https://github.blog/changelog/2026-08-07-mcp-allowlists-in-enterprise-managed-settings) |
| O5 | Claude Code `managed-mcp.json` and `allowManagedMcpServersOnly` behaviour | Verified | Nov 2026 | [Claude Code docs](https://code.claude.com/docs/en/managed-mcp) |
| O6 | Microsoft recommends Purview DLP to exclude sensitive content from Copilot grounding | Verified | 13 Nov 2026 | [Microsoft Learn: Microsoft 365 Copilot E5 guide](https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-e5-guide) |
| O7 | Microsoft Graph: delegated `Mail.Read` reads the signed-in user's mail; the application permission of the same name reads every mailbox | Verified | 9 Nov 2026 | [Microsoft Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference) |
| O8 | Google Workspace domain-wide delegation lets an app or service account access users' data without their consent; grants are under API controls > Manage Domain Wide Delegation | Verified | 9 Nov 2026 | [Google Workspace Admin Help](https://support.google.com/a/answer/162106) |
| O9 | Entra's on-behalf-of flow, and OAuth token exchange (RFC 8693), give a server its own token for an upstream API | Verified | 9 Nov 2026 | [Microsoft identity platform: on-behalf-of](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow); [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693) |

## Skills and the audit sandbox

| # | Claim | Status | Checked | Source |
| --- | --- | --- | --- | --- |
| S1 | Agent Skills format: a folder with `SKILL.md`; `name` 1-64 lowercase letters, digits and hyphens, matching the folder; `description` 1-1024 characters | Verified | 13 Nov 2026 | [agentskills.io specification](https://agentskills.io/specification) |
| S2 | Claude Code loads project skills from `.claude/skills/` and personal skills from `~/.claude/skills/` | Verified | 13 Nov 2026 | [Claude Code docs: skills](https://code.claude.com/docs/en/skills) |
| S3 | The official MCP Registry is at registry.modelcontextprotocol.io | Verified | 13 Nov 2026 | [MCP blog, September 2025](https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/) |
| S4 | A container on a Docker `--internal` network can still reach services on the host through the bridge's gateway address; gateway mode `isolated` (or `inhibit_ipv4`) removes it | Verified by test (Docker 29.9) | 13 Nov 2026 | Our own test; the sandbox repeats it before every run (`isolation_check` in `run_sandbox.py`) |
| S5 | The audit sandbox catches the evil-server fixture's credential theft and rug pull, and reports nothing for the plain fixture | Verified by test | 13 Nov 2026 | [skills/tests](../skills/tests/test_audit_scripts.py), run in CI |
| S6 | Tested on a real package: `@modelcontextprotocol/server-everything` 2.3.0 in the sandbox (STDIO and HTTP): its `get-env` tool returned the planted fake `DATABASE_URL`, and one tool's default argument points at raw.githubusercontent.com, which the sink logged | Observed | 13 Nov 2026 | Our own run; a demonstration of the sandbox, not a vulnerability report (it is a reference server built to exercise the protocol) |
| S7 | Claude Code's CLAUDE.md can import other files with `@path` lines | Verified | 14 Nov 2026 | [Claude Code docs: memory](https://code.claude.com/docs/en/memory) |
| S8 | The quick start's commands (section 1, and section 4 by hand against `@modelcontextprotocol/server-everything` 2.3.0) | Verified by running them | 14 Nov 2026 | Our own run, in a clean home directory |

## Corrections

| Date | What changed |
| --- | --- |
| 13 Nov 2026 | Before publication: the claim that "over half of MCP servers are developer tools" was a misreading of arXiv 2512.03775 and was removed (see C13). The same error appears in the first video in the series, whose description carries a correction. |
