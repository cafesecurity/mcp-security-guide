"""Fake credentials for the audit sandbox. Every value contains the run's secret
canary, so if any of them leaves the server (over the network or in a tool
result) the audit can tell. None of them is real."""
import os

FILES = {
    ".ssh/id_rsa": "-----BEGIN OPENSSH PRIVATE KEY-----\nFAKE-AUDIT-KEY-{c}\n-----END OPENSSH PRIVATE KEY-----\n",
    ".aws/credentials": "[default]\naws_access_key_id = AKIA{c}\naws_secret_access_key = {c}SECRET\n",
    ".config/gh/hosts.yml": "github.com:\n    oauth_token: ghp_{c}\n",
    ".npmrc": "//registry.npmjs.org/:_authToken=npm_{c}\n",
    ".env": "DATABASE_URL=postgres://audit:{c}@db.internal.invalid/prod\n",
    ".cursor/mcp.json": '{{"mcpServers": {{"crm": {{"env": {{"API_KEY": "{c}"}}}}}}}}\n',
    ".config/Claude/claude_desktop_config.json": '{{"mcpServers": {{"db": {{"env": {{"DB_PASSWORD": "{c}"}}}}}}}}\n',
}


def plant() -> None:
    c = os.environ.get("AUDIT_SECRET_CANARY", "")
    home = os.environ.get("HOME", "/home/audit")
    if not c:
        return
    for rel, template in FILES.items():
        p = os.path.join(home, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(template.format(c=c))
