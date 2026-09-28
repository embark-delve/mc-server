"""Use project-local Node, or Node 24 on PATH, without shell interpolation."""

import os
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    local = ROOT / ".tools/node/bin"
    env = dict(os.environ)
    if (local / "node").is_file():
        env["PATH"] = str(local) + os.pathsep + env.get("PATH", "")
    node = shutil.which("node", path=env.get("PATH"))
    npm = shutil.which("npm", path=env.get("PATH"))
    if not node or not npm:
        raise SystemExit("Install Node 24 or run make bootstrap")
    version = subprocess.check_output([node, "--version"], text=True, env=env)  # noqa: S603 # nosec B603
    if not version.startswith("v24."):
        raise SystemExit(
            "Node 24 required; run make bootstrap (your global Node is unchanged)"
        )
    commands = {
        "ci": ["ci", "--ignore-scripts"],
        "lint": ["run", "lint"],
        "format": ["run", "format"],
        "format-check": ["run", "format:check"],
        "audit": ["audit", "--audit-level=low"],
    }
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit("Choose ci, lint, format, format-check or audit")
    return subprocess.call([node, npm, *commands[sys.argv[1]]], cwd=ROOT, env=env)  # noqa: S603 # nosec B603


if __name__ == "__main__":
    raise SystemExit(main())
