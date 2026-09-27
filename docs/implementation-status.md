# Current implementation status

Updated 2026-09-27. This supersedes the initial implementation snapshot. The baseline review remains in [laptop-readiness.md](laptop-readiness.md); use the [admin guide](admin-guide.md) for current operation.

## Working MVP

- Local Docker server: Minecraft Java Edition 1.20.1, Forge 47.4.23, Java 25. Docker Desktop is installed and the base Forge server has reached healthy status.
- CLI and single-admin local web dashboard support setup, start/stop/restart, status/logs, player access, bans/removal, backups, and individual mod enable/disable. Installed server mods default to enabled; changes require a stopped server.
- Minecraft online authentication and enforced allowlisting remain mandatory. MineBuilder006 and MountFuji42 are configured operators; Nebulic_ is allowed. Website accounts are not required for players.
- Game and dashboard bind to localhost. RCON is private to Docker. Admin passwords are salted scrypt hashes in a private profile file, not plaintext `.env` entries. See [web security](web-ui-security.md).
- Profiles have locks, runtime/image pinning, bounded operations, safe checksummed backups and staged restore with rollback. Cloud deployment and old unattended automation remain disabled.
- Python dependencies use pyproject.toml/uv.lock. Node tooling uses package-lock.json. Commit/push hooks and CI cover formatting, syntax, typing, tests, secret detection, production security scanning and dependency audits. See [development](development.md).

## Validation

The local commit gate passes, including Ruff, mypy, Bandit, ESLint, Prettier and staged Gitleaks. The push gate passes regression tests and both dependency audits. Full-history Gitleaks passes with one exact, documented historical example-password fingerprint excluded; history has not been rewritten.

The default suite passes with two opt-in integration tests skipped. Separate live Docker save/backup/restore and HTTP checks have passed; [launch progress](launch-progress.md) records the live evidence. Restore verification uses a persisted scoreboard value in disposable worlds. Never run a restore test against the real world.

## Remaining launch limits

1. The full requested modpack has not been installed or proven compatible. Resolve exact publisher artifacts/dependencies and validate a matching client; [modpack candidates](modpack-candidates.md) are research, not a tested pack.
2. A real Minecraft client still needs to demonstrate an allowed join and rejection of a non-allowlisted authenticated account.
3. Outside-network access is not configured. The public-IP probe from this laptop timed out and is not an independent external test. See [remote access](remote-access.md) for the recommended private VPN approach.
4. The downloaded container image and third-party mod JARs have not undergone a complete vulnerability audit. Python/npm audits do not cover those components.
5. Set the persistent admin password with `minecraft-server admin owner` if not already configured. Stop/save before laptop sleep and keep independent backups.
