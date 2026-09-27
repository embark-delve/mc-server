# Live validation update

Docker is now installed; EULA acceptance and all three usernames were supplied. Base Forge started, passed the live security check, and completed clean-stop and CLI/browser backups. See [current launch progress](launch-progress.md) for the final restore result. The earlier blockers below are historical.

# MVP validation — 2026-09-27

Final scope: one admin, self-service CLI/web setup, player allowlist/ban/removal, world lifecycle and backups. No player website accounts or invitation system.

## Completed

- Automated suite: 100 passed, 2 skipped in the default run. The real CLI/HTTP test is separately enabled and passes; the actual Docker game test remains blocked.
- Real CLI + Uvicorn HTTP smoke test on a disposable profile: single admin configuration, password login, player add/ban/unban/remove, unauthenticated rejection, hostile Host/Origin rejection, logout/session revocation, and absence of the removed website-user API. This does not start Minecraft or accept the user's EULA.
- Unit tests: explicit EULA/auth required for setup; private password hashing and one-admin replacement; durable player exclusion; revocation before startup for operators; live kick/ban dispatch and failure reporting; fixed allowed HTTP operations; serialized world operations; redacted errors; bounded login requests and attempts.
- Runtime-security tests reject offline mode, missing whitelist enforcement, unexpected published ports, mismatched allowlists and unapproved operators. These simulate Docker responses.
- Ruff, formatting, mypy and JavaScript syntax checks pass. Runtime dependency audit found no known vulnerabilities; evidence is saved in implementation-evidence/web-runtime-audit.json.
- Browser inspection covered desktop/mobile layouts, navigation, world setup state, joining instructions and player-management controls. The current preview reports that the real world has not been initialized.

## Launch blockers and remaining live checks

No Docker executable or Docker Desktop app was found in the standard locations inspected on this laptop. No Minecraft container has been started or verified. Explicit EULA acceptance and an actual allowed Minecraft username remain pending. Exact modpack files also remain unresolved.

Once prerequisites are available, run the disposable integration lifecycle test with MC_INTEGRATION_EULA=accepted and MC_TEST_USERNAME set. It checks health, effective authentication/allowlist/ports, in-world marker creation, stop, backup, restore and marker recovery. Then test the real approved modpack with an allowed Minecraft account and verify rejection of a different non-allowlisted authenticated account. The user signs into their normal launcher; do not collect Microsoft credentials. Check another device cannot connect under default loopback-only bindings.

Configuration inspection and mocked tests do not prove live player admission behavior. The website is locally exercised; the game server must not be described as live-verified yet. Starlette emits a non-failing TestClient httpx deprecation warning; it is not suppressed.
