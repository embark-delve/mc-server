> Historical baseline launch record (before LAN forwarding, mod installation and the UI reorganization). For current state use [implementation status](implementation-status.md), [installed mods](installed-mods.md), and [UI review](web-ui-review.md). Counts and addresses below describe that earlier run.

# Launch and MVP verification — 2026-09-27

## Authorized configuration

The user explicitly accepted the Minecraft EULA and supplied these Java identities:

- MineBuilder006 — game administrator/operator
- MountFuji42 — game administrator/operator
- Nebulic_ — allowed player

The website retains one administrator; players do not need website accounts. The private world lives at `/Users/shamil/MinecraftServers/forge`. Game networking is still laptop-only, `127.0.0.1:25565`.

## Completed live checks

Docker Desktop 4.92.0 / Engine 29.8.0 installed successfully. System-wide binary linking required a password, so installation used `--no-binaries`; the manager finds Docker's bundled macOS CLI automatically. Minecraft runs in Docker; the manager remains a local Python process.

The real base Forge 47.4.23 / Minecraft 1.20.1 / Java 25 world started healthy. Live inspection confirmed online-mode authentication, whitelist enforcement, exactly the three approved players, both requested operators, loopback game binding, and no published RCON/management ports. RCON confirmed zero players before the test stop.

Clean CLI stop and backup passed. A separate backup triggered through the actual web UI confirmation dialog passed too. The real world was stopped during the disposable restore rehearsal because Docker has about 8 GiB of memory.

The disposable Docker integration test passed in 169.29 seconds: startup, live security checks, persistent scoreboard write, clean stop, backup, restore into a different profile, startup, live security checks, and retrieval of the original scoreboard value. Its containers were removed by scoped test cleanup. The first attempt failed an unreliable chat-output assertion; that output is retained separately, and the final test asserts explicit write/read results.

The real-world start was exercised through the browser. Final status/security snapshots are in `implementation-evidence/live-status.json` and `live-security.json`; the browser preview is at http://127.0.0.1:8765/.

## Mod-management MVP

Each installed server mod has an enable/disable switch in World care; installs start enabled. Changes require a stopped, cleanly exited server and authenticated confirmation. Disabled JARs move atomically to `data/disabled-mods`, remain in world backups, and can be re-enabled. CLI equivalents are `mods-enable FILE.jar` and `mods-disable FILE.jar`. Conflicting files and path traversal are rejected; files are not deleted by toggles.

The latest default automated run passed 105 tests, with opt-in HTTP/game tests skipped in that default run. The real Docker integration ran separately and passed. Mod state round trips, file hashes, default enablement, conflicts, authentication and running-server refusal are tested. Ruff, formatting, mypy, JavaScript syntax and package builds pass.

## Still pending

The full requested modpack is not installed: exact compatible files/dependencies and a matching client pack still need validation. Mod switches do not resolve dependencies automatically, and client-only rendering mods/shaders/resource packs are not server mods.

A real allowed-account client join and rejection of a different non-allowlisted authenticated client have not been performed. Configuration checks do not replace those admission tests. Sign in through the normal Minecraft launcher; do not share Microsoft passwords or session tokens. Other devices cannot join while the default loopback-only binding is retained; a deliberate LAN setup is a separate step.
