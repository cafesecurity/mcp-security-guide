#!/usr/bin/env python3
"""Sandbox entrypoint for Python servers: plant canary credentials in the
throwaway home directory, then start the server in place of this process."""
import configparser
import glob
import os
import sys

from canaries import plant  # noqa: E402  (copied next to this file in the image)


def console_script(name: str) -> tuple[str, str]:
    for ep in glob.glob("/srv/pkgs/*.dist-info/entry_points.txt"):
        cp = configparser.ConfigParser()
        cp.read(ep)
        if cp.has_section("console_scripts") and cp.has_option("console_scripts", name):
            mod, _, func = cp.get("console_scripts", name).partition(":")
            return mod.strip(), func.strip()
    sys.exit(f"audit sandbox: console script {name!r} not found")


plant()
mode = os.environ.get("AUDIT_MODE")
args = sys.argv[1:]
if mode == "pypi":
    sys.path.insert(0, "/srv/pkgs")
    os.environ["PYTHONPATH"] = "/srv/pkgs"
    if os.environ.get("AUDIT_MODULE"):
        os.execv(sys.executable, [sys.executable, "-m", os.environ["AUDIT_MODULE"], *args])
    mod, func = console_script(os.environ["AUDIT_CONSOLE_SCRIPT"])
    os.execv(sys.executable, [sys.executable, "-c", f"import sys; sys.argv[0]={os.environ['AUDIT_CONSOLE_SCRIPT']!r}; from {mod} import {func} as f; sys.exit(f())", *args])
elif mode == "local":
    os.chdir("/srv/app")
    os.execv(sys.executable, [sys.executable, os.environ["AUDIT_RUN"], *args])
else:
    sys.exit("audit sandbox: AUDIT_MODE must be pypi or local")
