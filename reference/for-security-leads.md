# For security leads

*As of 13 November 2026.*

One page for whoever has to approve an MCP server, or decide which ones staff may connect. The rest of the guide is for the people building it.

## What an MCP server changes

A server gives an AI agent three new things: text to read, actions to take and systems to reach. The text matters as much as the code, because the model may obey it. Risk adds up across every server one agent holds, so a harmless server can become dangerous next to another one. See [the model](model.md) for the detail.

## Ten questions to ask before you approve a server

Each question links to the page where the builder should have the answer.

1. **Does it need to be an MCP server?** Would an ordinary API, or a narrower tool, do? ([Decide](../guide/00-decide.md))
2. **Whose identity does it use?** Each user's own delegated access is the safe default. One service account with organisation-wide rights gives every user, and every successful prompt injection, the master key. ([Design](../guide/02-design.md))
3. **Which of the three letters does it light?** [A] reads text outsiders can write, [B] reaches private data or sensitive systems, [C] changes things or sends data out. Ask for the scorecard, for this server and for the agents that will hold it. ([Threat model](../guide/01-threat-model.md))
4. **Which tools change or delete anything, and who approves those calls?** ([Design](../guide/02-design.md))
5. **Does it check that each token was issued for it, and does it refuse to pass tokens on?** Both are requirements of the specification. ([Spec checklist](spec-checklist.md))
6. **How is one customer's or user's data kept from another, and is that tested on every build?** ([Test](../guide/04-test.md))
7. **How is it published, and how would users know a copy is fake?** ([Release](../guide/05-release.md))
8. **What does it log, and can you see who called which tool, with what, and when, without the content itself filling the logs?** ([Deploy and operate](../guide/06-deploy-operate.md))
9. **What happens when a tool's description changes?** It should be treated as a release and re-approved. ([Change](../guide/07-change.md))
10. **How do you switch it off, and revoke its tokens, in under an hour?** ([Incident and retire](../guide/08-incident-retire.md))

For a server someone else wrote, ask for an audit of the exact version you will run. The [`mcp-server-audit`](../skills/mcp-server-audit/SKILL.md) skill produces one, including an optional run in a sandbox with fake credentials, and ends with approve, approve with conditions, or reject.

Red flags: a single shared service account; "it's read-only" with a send or write tool on the list; tokens with wildcard scopes; a local server installed with `latest` instead of a pinned version; no answer to question 10.

## Controlling the agents staff connect

A well-built server can still leak if someone connects it to an unmanaged agent with a shell, community plug-ins and a messaging channel. Microsoft's Zero Trust guidance warns that [unsanctioned local agents](https://microsoft.github.io/zerotrustassessment/docs/workshop-guidance/devices/DEV_151) can read local files, run shell commands and send data outside the organisation's controls.

You have five layers of control:

1. **Identity and consent (the strongest).** If an unapproved agent cannot get a token, it cannot reach the data from any machine. In Google Workspace, restrict third-party access under [API controls](https://knowledge.workspace.google.com/admin/apps/control-which-third-party-and-internal-apps-access-google-workspace-data) and trust only approved client IDs. In Microsoft 365, [restrict user consent](https://learn.microsoft.com/en-us/microsoft-365/admin/misc/user-consent) to third-party apps, use the admin consent workflow and review existing grants. On your own servers, register only approved MCP clients.
2. **The organisation's own agent clients.** [GitHub Copilot](https://github.blog/changelog/2026-08-07-mcp-allowlists-in-enterprise-managed-settings) enforces enterprise MCP allow and deny lists that fail closed. In [Claude Code](https://code.claude.com/docs/en/managed-mcp), a managed `managed-mcp.json` file limits users to the servers it lists; without the `allowManagedMcpServersOnly` setting, a user's own allow-list entries are merged with yours.
3. **Endpoints.** Device management can block unsanctioned local agents by name, process or bundle ID. Microsoft's Shadow AI guidance shows how to [build an Intune policy](https://microsoft.github.io/zerotrustassessment/docs/workshop-guidance/AI/AI_177) for managed Windows devices.
4. **Network and SaaS.** Mark unsanctioned generative AI apps in your cloud access security broker and block them, and add prompt-level data loss prevention in managed browsers. Expect gaps where staff use personal accounts.
5. **A paved road.** Offer a sanctioned agent with approved servers built in, so the safe path is also the easy one. Blocking alone pushes people to workarounds.

The products named are examples. Other vendors offer equivalent controls.

## Running it as a programme

- **Inventory** every MCP server, including those on developers' machines. Scan repositories for MCP configuration files and networks for open servers.
- **Registry**: submit, review, approve, re-review. Every server has an owner. Unregistered servers are blocked.
- **Gateway** for remote servers, with single sign-on, policy, logging and outbound allow-lists.
- **Short-lived credentials** from a vault. No shared service account across agents, and development credentials kept apart from production.
- **Score every production agent** with the [scorecard](model.md#scorecard), and require human approval wherever all three letters are lit.
- **Logs to the SIEM**: identity, tool, parameters and time, with sensitive values masked.
- **Rehearse** an "MCP server compromised" incident, including the kill switch.
- **Track spec versions.** The 2026-07-28 revision removed sessions and changed authorisation, and older servers need migrating.

For audit and risk registers, the [framework crosswalk](frameworks.md) maps all of this to OWASP, MITRE ATLAS, CSA MAESTRO and the NIST AI RMF.

## More

- The video series that goes with this guide is listed in the [README](../README.md#videos).
- For the agents your staff already run, the free [AI Agent Check](https://cafesecurity.github.io/ai-tools/agent-check/) walks through the same questions.
