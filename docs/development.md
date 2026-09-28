# Development and commit checks

Use Python 3.13+, uv, Gitleaks 8.30.1, and the pinned Node 24 version in .node-version. Node is only needed for frontend development checks; the game/dashboard runtime does not need Node.

On macOS install Gitleaks with `brew install gitleaks`, then:

```sh
make bootstrap
make check
make security
uv run --locked pre-commit run --all-files
uv run --locked pre-commit run --all-files --hook-stage pre-push
```

`make bootstrap` syncs uv.lock, installs a project-local Node runtime in ignored `.tools/node`, installs package-lock.json with lifecycle scripts disabled, and installs both pre-commit and pre-push Git hooks. It does not change the user's global Node. CI uses Node 24 from .node-version. Hooks are local entries using locked Python/npm tools rather than floating remote hook revisions. Gitleaks is an external pinned-version prerequisite in CI.

Commit checks: private/runtime filename guard, whitespace/newline/merge conflict checks, YAML/JSON/TOML/Python syntax, private keys, file sizes and case collisions, symlinks, Ruff lint/format, mypy, Bandit, Python lock consistency, ESLint and Prettier, and redacted staged-file Gitleaks.

Push checks: regression tests plus Python and npm dependency vulnerability audits, including developer dependencies. CI repeats checks, scans full history with Gitleaks, validates a clean npm install/uv lock, and builds/installs the wheel outside the checkout. The Docker and real HTTP integration tests are opt-in; normal hooks never start a game server or accept the EULA.

```sh
make format
uv build
MC_WEB_INTEGRATION=1 uv run --locked pytest tests/integration/test_web_live.py
# Only after explicit EULA acceptance, with Docker running and sufficient memory:
MC_INTEGRATION_EULA=accepted MC_TEST_USERNAME=YourJavaName uv run --locked pytest tests/integration/test_docker_lifecycle.py
```

Use disposable profiles for live tests. Docker's memory budget must accommodate each running game. The restore test writes a scoreboard value and verifies it after restoring into another profile. Never test restore against the real world.

## Secret handling

`.gitignore` excludes env variants, private access stores, keys, game data/backups, Terraform state/variable files, generated tools and local transcripts. A hook also refuses private filenames even when force-added. The example env template is allowed and must contain no credentials. Gitleaks scans staged content independently of formatter exclusions.

The history scan identified one retired example RCON default in `terraform/aws/modules/minecraft_server/variables.tf`, commit `bd290837e9bc160590f9d5a1136df98056e5eff0`. Current source removed it and the running server uses a freshly generated secret. `.gitleaksignore` records only that exact historical fingerprint; new occurrences remain detectable. History was not rewritten. Any older deployment that used the example password must replace it. Recorded transcripts were removed from Git tracking but preserved locally; earlier commits still contain historical files.

Bandit suppressions are narrow and reviewed: fixed executable/argv calls without a shell in the command/tool runners. The RCON secret mount is represented as a filesystem path rather than treated as a password literal. Do not globally disable scanner rules to get a commit through.

Use `uv add --dev ...` and npm's exact-version installs to update tools deliberately, then rerun the full gate. Network-dependent audits fail rather than silently claiming a clean result when their databases are unavailable.
