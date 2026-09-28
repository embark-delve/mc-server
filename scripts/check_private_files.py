"""Refuse private runtime files even if force-added past .gitignore."""

import re
import sys
from pathlib import PurePosixPath

PATTERNS = re.compile(
    r"(^|/)(\.env($|\.)|\.envrc$|\.clubhouse-|rcon\.secret$|"
    r"runtime\.json$|profile\.json$|\.operation\.lock$|"
    r"node_modules/|\.venv/|\.tools/|\.specstory/|data/|backups/|"
    r"data\.rollback/|secrets/|\.terraform/)"
    r"|\.(pem|key|p12|pfx|keystore|tfstate|tfplan|tfvars)(\.|$)"
)


def main() -> int:
    rejected = []
    for name in sys.argv[1:]:
        path = PurePosixPath(name)
        if path.name.endswith(".example"):
            continue
        if PATTERNS.search(name) or path.name in {
            "config.local.yml",
            "config.private.yml",
        }:
            rejected.append(name)
    if rejected:
        print("Private/runtime files cannot be committed:\n" + "\n".join(rejected))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
