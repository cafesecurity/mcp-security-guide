# Framework crosswalk

*As of 13 November 2026.*

Use the [model](model.md) and the lifecycle pages to find threats, then use these frameworks to name them in audits, risk registers and pull request descriptions. They cover different layers, and none is complete for MCP on its own.

## Status

| Framework | Use it for | Status |
| --- | --- | --- |
| [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) | What the protocol requires | 2026-07-28 (see [spec-checklist.md](spec-checklist.md)) |
| [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/) | Risks in the MCP layer itself | 2025 list, still in beta |
| [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/) | Risks in agents that plan, remember and act | First edition, published 9 December 2025 |
| [OWASP Top 10 for LLM Applications](https://genai.owasp.org/) | Risks in the model layer, such as prompt injection | 2026 edition, published 4 August 2026 |
| [MITRE ATLAS](https://atlas.mitre.org/) | How attackers operate, in ATT&CK-style techniques | Data release 2026.10 checked. Agent-tool techniques, no MCP-named technique |
| [CSA MAESTRO](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro) | Running the threat-modelling exercise, layer by layer | Version 1 (seven layers), February 2025. [Version 2](https://cloudsecurityalliance.org/artifacts/maestro-v2) released June 2026 for open peer review; this guide maps to version 1 |
| NIST AI RMF 1.0 | Running the programme: Govern, Map, Measure, Manage | Voluntary. NIST's [SP 800-53 control overlay project](https://csrc.nist.gov/Projects/cosis) (COSAiS, renamed COSIS on 20 October 2026) lists single-agent and multi-agent overlays as planned; none had been published as a draft |
| [NSA MCP guidance](https://www.nsa.gov/Press-Room/Press-Releases-Statements/Press-Release-View/Article/4496698/) | Baseline design controls for MCP | Published 20 May 2026 |
| [CoSAI MCP Security](https://www.coalitionforsecureai.org/wp-content/uploads/2026/03/model-context-protocol-security-1.pdf) | An industry threat model and secure design patterns for MCP | Approved 8 January 2026 |

## OWASP MCP Top 10 (2025 beta)

| ID | Risk | FBI | Lifecycle page |
| --- | --- | --- | --- |
| MCP01 | Token mismanagement and secret exposure | Impact | [Design](../guide/02-design.md), [Build](../guide/03-build.md), [Deploy and operate](../guide/06-deploy-operate.md) |
| MCP02 | Privilege escalation via scope creep | Impact | [Design](../guide/02-design.md), [Change](../guide/07-change.md) |
| MCP03 | Tool poisoning | Feed | [Build](../guide/03-build.md), [Change](../guide/07-change.md) |
| MCP04 | Software supply chain attacks and dependency tampering | Feed, Impact | [Build](../guide/03-build.md), [Release](../guide/05-release.md) |
| MCP05 | Command injection and execution | Behaviour | [Build](../guide/03-build.md), [Test](../guide/04-test.md) |
| MCP06 | Intent flow subversion | Feed, Behaviour | [Threat model](../guide/01-threat-model.md), [Design](../guide/02-design.md) |
| MCP07 | Insufficient authentication and authorisation | Impact | [Design](../guide/02-design.md), [Build](../guide/03-build.md) |
| MCP08 | Lack of audit and telemetry | All | [Deploy and operate](../guide/06-deploy-operate.md) |
| MCP09 | Shadow MCP servers | All | [Decide](../guide/00-decide.md), [Deploy and operate](../guide/06-deploy-operate.md) |
| MCP10 | Context injection and over-sharing | Feed, Impact | [Design](../guide/02-design.md), [Test](../guide/04-test.md) |

## Other OWASP lists

Only the entries this guide uses are listed, and only those checked against a reliable source.

| ID | Risk | Where it fits |
| --- | --- | --- |
| LLM01 (LLM Top 10, 2026) | Prompt injection | Instructions in tool descriptions and results |
| LLM02 (LLM Top 10, 2026) | Sensitive information disclosure | Results that carry more than the caller should see |
| ASI01 (Agentic Top 10) | Agent goal hijack | An agent steered by what a tool returned |
| ASI02 (Agentic Top 10) | Tool misuse | A legitimate tool used for the wrong end |

## MITRE ATLAS

ATLAS has no technique named for MCP. These agent-tool entries fit most closely. All IDs and names were checked against the ATLAS data release 2026.10 (28 October 2026) on [GitHub](https://github.com/mitre-atlas/atlas-data).

| ID | Name | Lifecycle page |
| --- | --- | --- |
| AML.T0115.002 | Publish Poisoned AI Artifacts: AI Agent Tools | [Release](../guide/05-release.md) |
| AML.T0010.005 | AI Supply Chain Compromise: AI Agent Tool | [Build](../guide/03-build.md), [Change](../guide/07-change.md) |
| AML.T0110 | AI Agent Tool Poisoning | [Build](../guide/03-build.md), [Change](../guide/07-change.md) |
| AML.T0053 | AI Agent Tool Invocation | [Design](../guide/02-design.md) |
| AML.T0086 | Exfiltration via AI Agent Tool Invocation | [Threat model](../guide/01-threat-model.md), [Design](../guide/02-design.md) |
| AML.T0101 | Data Destruction via AI Agent Tool Invocation | [Design](../guide/02-design.md) |
| AML.T0098 | AI Agent Tool Credential Harvesting | [Build](../guide/03-build.md) |
| AML.M0030 | Restrict AI Agent Tool Invocation on Untrusted Data (mitigation) | [Design](../guide/02-design.md) |

ATLAS case studies that involve MCP:

| ID | Title | Type |
| --- | --- | --- |
| AML.CS0039 | Living Off AI: Prompt Injection via Jira Service Management | Exercise (June 2025) |
| AML.CS0045 | Data Exfiltration via an MCP Server used by Cursor | Exercise (June 2025) |
| AML.CS0053 | Poisoned Postmark MCP Server Email Exfiltration | Incident (September 2025) |
| AML.CS0054 | Data Exfiltration via Remote Poisoned MCP Tool | Exercise (April 2025) |

## By stage

The nine stages a connection passes through (see [model.md](model.md#nine-stages)), with the IDs that fit each.

| Stage | FBI | OWASP | ATLAS |
| --- | --- | --- | --- |
| 1. Discover and install | Feed, Impact | MCP04 | AML.T0115.002, AML.T0010.005 |
| 2. Configure and launch | Behaviour, Impact | MCP05, MCP09 | — |
| 3. Authorise | Impact | MCP01, MCP02, MCP07 | AML.T0098 |
| 4. List tools | Feed | MCP03 | AML.T0110 |
| 5. Call | Behaviour, Impact | MCP05 | AML.T0053, AML.T0086, AML.T0101 |
| 6. Result | Feed | MCP06, MCP10 | AML.M0030 |
| 7. Compose | All three | ASI01, ASI02 | AML.T0086 |
| 8. Update | Feed | MCP03, MCP04 | AML.T0110 |
| 9. Operate and retire | All three | MCP08, MCP09 | — |

## CSA MAESTRO

MAESTRO is a method, not a list: it tells you where in the stack to look and how to run the exercise. Use it as the process, with this guide's model and lifecycle pages as the MCP-specific content.

The Cloud Security Alliance published MAESTRO (Multi-Agent Environment, Security, Threat, Risk, and Outcome) in February 2025. It splits an agentic system into seven layers. CSA's article puts tool misuse and integrations in layer 7 and agent toolkits and their dependencies in layer 3. The rest of this mapping is this guide's own.

| MAESTRO layer | What MCP puts there | FBI |
| --- | --- | --- |
| 1. Foundation Models | The model that reads tool descriptions and results, and may follow instructions in them | Feed |
| 2. Data Operations | Resources, retrieved data, and context or memory shared across users and tenants | Feed, Impact |
| 3. Agent Frameworks | MCP SDKs, client and server code, their dependencies, the STDIO launch command | Behaviour |
| 4. Deployment and Infrastructure | Where servers run: local processes, containers, remote HTTP endpoints, network binding | Impact |
| 5. Evaluation and Observability | Tool-call logs, baselines, alerts when definitions change | All three |
| 6. Security and Compliance (cuts across all layers) | OAuth, token audience, consent, policy, registry approval | Impact |
| 7. Agent Ecosystem | Third-party servers, registries, tool misuse, other agents and integrations | All three |

MAESTRO's six steps line up with this guide:

1. **Decompose the system into layers.** Place each server with the table above, then ask the three questions in [model.md](model.md#three-questions-for-every-server).
2. **Model layer-specific threats.** Use [Threat model](../guide/01-threat-model.md).
3. **Identify cross-layer threats.** Use the [composition tests](model.md#composition-count-across-the-agent). A third-party server (layer 7) plus shared private data (layer 2) plus a model that obeys what it reads (layer 1) is the lethal trifecta in MAESTRO's terms.
4. **Assess risk.** Score likelihood and impact, using Impact's breadth, depth and time.
5. **Plan mitigations.** Use the lifecycle checklists and [spec-checklist.md](spec-checklist.md).
6. **Implement and monitor.** [Deploy and operate](../guide/06-deploy-operate.md), and the RMF's Manage function below.

## NIST AI RMF

The RMF's four functions give the programme around this guide:

- **Govern:** an internal registry, an owner for every server, approval rules.
- **Map:** the inventory, the three questions and the scorecard.
- **Measure:** tenant-isolation tests, injection tests, red teaming, tool-call logs.
- **Manage:** the controls on the lifecycle pages, the kill switch, incident response.
