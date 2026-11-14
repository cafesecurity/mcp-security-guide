"""Tests for bin/mcp-guide: init, status, update and remove are safe to repeat and keep people's edits.

  python3 -m unittest discover -s tests -v
  MCP_GUIDE_AUDIT_TEST=1 also runs `mcp-guide audit local` on the malicious fixture (needs Docker)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "mcp-guide"
FIXTURE = ROOT / "skills" / "tests" / "fixtures" / "evil-server"


def guide(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    env = {**os.environ, "PATH": "/usr/bin:/bin"}  # no `claude` on PATH, so detection depends on the repo only
    r = subprocess.run([sys.executable, str(CLI), *args], cwd=cwd, capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    if check and r.returncode != 0:
        raise AssertionError(f"mcp-guide {' '.join(args)} failed:\n{r.stdout}\n{r.stderr}")
    return r


class SetUp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_for_claude_adds_rules_skills_and_pointers(self):
        (self.repo / "AGENTS.md").write_text("# Ours\n- use pnpm\n")
        guide("init", "--agent", "claude", cwd=self.repo)
        for skill in ("mcp-threat-model", "mcp-security-review", "mcp-release-check", "mcp-server-audit"):
            self.assertTrue((self.repo / ".claude/skills" / skill / "SKILL.md").exists(), skill)
        self.assertFalse(any(p.name == "__pycache__" for p in (self.repo / ".claude/skills").rglob("*")))
        self.assertEqual((self.repo / "MCP-SECURITY-RULES.md").read_text(), (ROOT / "AGENTS.md").read_text())
        agents = (self.repo / "AGENTS.md").read_text()
        self.assertTrue(agents.startswith("# Ours\n- use pnpm\n"), "existing content kept")
        self.assertIn("MCP-SECURITY-RULES.md", agents)
        self.assertIn("@MCP-SECURITY-RULES.md", (self.repo / "CLAUDE.md").read_text())
        self.assertTrue(os.access(self.repo / ".claude/skills/mcp-server-audit/scripts/scan_code.py", os.X_OK))

    def test_detects_other_agents(self):
        guide("init", cwd=self.repo)
        self.assertTrue((self.repo / ".agents/skills/mcp-threat-model/SKILL.md").exists())
        self.assertFalse((self.repo / "CLAUDE.md").exists())
        with tempfile.TemporaryDirectory() as d:
            repo2 = Path(d)
            subprocess.run(["git", "init", "-q", str(repo2)], check=True)
            (repo2 / "CLAUDE.md").write_text("# Ours\n")
            guide("init", cwd=repo2)
            self.assertTrue((repo2 / ".claude/skills/mcp-threat-model/SKILL.md").exists())

    def test_repeating_is_harmless(self):
        guide("init", "--agent", "claude", cwd=self.repo)
        before = (self.repo / "AGENTS.md").read_text(), (self.repo / "CLAUDE.md").read_text()
        guide("init", "--agent", "claude", cwd=self.repo)
        guide("init", "--agent", "claude", "--force", cwd=self.repo)
        guide("update", cwd=self.repo)
        self.assertEqual(before, ((self.repo / "AGENTS.md").read_text(), (self.repo / "CLAUDE.md").read_text()))

    def test_update_keeps_edits_and_status_reports_them(self):
        guide("init", "--agent", "claude", cwd=self.repo)
        skill = self.repo / ".claude/skills/mcp-threat-model/SKILL.md"
        skill.write_text(skill.read_text() + "\nOur house rule.\n")
        self.assertIn("edited by you: .claude/skills/mcp-threat-model/SKILL.md", guide("status", cwd=self.repo).stdout)
        guide("update", cwd=self.repo)
        self.assertIn("Our house rule.", skill.read_text())
        guide("update", "--force", cwd=self.repo)
        self.assertNotIn("Our house rule.", skill.read_text())

    def test_does_not_overwrite_files_it_did_not_install(self):
        (self.repo / "MCP-SECURITY-RULES.md").write_text("our own rules\n")
        guide("init", cwd=self.repo)
        self.assertEqual((self.repo / "MCP-SECURITY-RULES.md").read_text(), "our own rules\n")

    def test_remove_restores_the_repository(self):
        (self.repo / "AGENTS.md").write_text("# Ours\n")
        guide("init", "--agent", "claude", cwd=self.repo)
        guide("remove", cwd=self.repo)
        self.assertEqual((self.repo / "AGENTS.md").read_text(), "# Ours\n")
        self.assertFalse((self.repo / "CLAUDE.md").exists(), "CLAUDE.md only had our pointer")
        self.assertFalse((self.repo / ".claude").exists())
        self.assertFalse((self.repo / "MCP-SECURITY-RULES.md").exists())
        self.assertFalse((self.repo / ".mcp-security-guide.json").exists())

    def test_manifest_records_version_and_hashes(self):
        guide("init", cwd=self.repo)
        m = json.loads((self.repo / ".mcp-security-guide.json").read_text())
        self.assertEqual(m["agent"], "agents")
        self.assertIn("MCP-SECURITY-RULES.md", m["files"])
        self.assertTrue(all(len(h) == 64 for h in m["files"].values()))

    def test_refuses_outside_a_git_repository(self):
        with tempfile.TemporaryDirectory() as d:
            r = guide("init", cwd=Path(d), check=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("not inside a git repository", r.stderr)


class Audit(unittest.TestCase):
    def test_static_audit_of_a_local_directory(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "audit"
            guide("audit", "local", str(FIXTURE), "--no-sandbox", "--out", str(out), cwd=ROOT)
            summary = (out / "SUMMARY.md").read_text()
            self.assertIn("credential-paths", summary)
            self.assertIn("Worst finding: **high**", summary)
            self.assertTrue((out / "REPORT.md").exists())

    def test_sandbox_is_not_run_without_consent(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "audit"
            r = guide("audit", "local", str(FIXTURE), "--language", "python", "--run", "server.py", "--out", str(out), cwd=ROOT)
            self.assertIn("pass --yes to allow", r.stdout)
            self.assertFalse((out / "sandbox").exists())

    @unittest.skipUnless(os.environ.get("MCP_GUIDE_AUDIT_TEST") == "1", "set MCP_GUIDE_AUDIT_TEST=1 to run the sandbox (needs Docker)")
    def test_full_audit_catches_the_malicious_fixture(self):
        extra = []
        for flag, var in (("--python-image", "AUDIT_PYTHON_IMAGE"), ("--node-image", "AUDIT_NODE_IMAGE")):
            if os.environ.get(var):
                extra += [flag, os.environ[var]]
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "audit"
            r = subprocess.run([sys.executable, str(CLI), "audit", "local", str(FIXTURE), "--language", "python", "--run", "server.py",
                                "--out", str(out), "--yes", *(["--", *extra] if extra else [])], capture_output=True, text=True, timeout=900)
            summary = (out / "SUMMARY.md").read_text()
            self.assertIn("Worst finding: **critical**", summary, r.stdout + r.stderr)
            self.assertIn("credentials-exfiltrated", summary)


if __name__ == "__main__":
    unittest.main()
