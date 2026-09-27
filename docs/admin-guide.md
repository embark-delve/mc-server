# Server administration

This is the current supported workflow: Minecraft runs in Docker; the CLI and single-admin web dashboard run on the laptop. Players never need website accounts. The default bind is loopback, so only this laptop can connect. See [remote access](remote-access.md) before allowing other devices.

## Install and start

Install Python 3.13+, uv and Docker Desktop. Start Docker Desktop and wait for its engine. Then:

```sh
uv sync --locked
uv run --locked minecraft-server admin owner
uv run --locked minecraft-server web
```

The admin command prompts privately for a unique 15–128 character password. Open http://127.0.0.1:8765/ and sign in. The CLI also prints a temporary owner link for bootstrap/recovery; protect it like a password. The link expires on manager restart. Login sessions expire after eight hours; logout revokes the current session.

**Do not put an admin password in `.env`.** The admin command stores only a salted scrypt hash in a private mode-0600 `.clubhouse-<profile-path-hash>.json` next to the world profile. Running `admin owner` again replaces the single admin and invalidates previous password-login sessions. Restart the manager to invalidate a copied owner link too. Automation may pass a password using `--password-stdin` from a secret manager; never place a literal password in shell history or an argument.

`.env.example` contains non-secret process settings only. The CLI does not auto-load `.env`, and there is no `ADMIN_PASSWORD` setting. Runtime configuration uses config.yml, explicitly exported supported variables, then CLI flags. Use `--config config.local.yml` for private local overrides (a complete YAML config, not an implicit overlay). Put `--config` before the subcommand consistently when using one.

## First-world setup

The web setup form accepts your exact Java username and explicit EULA acceptance. Anyone authorized to use the single admin login can set up the world; there is no grown-up role gate. The CLI equivalent, only after reading and accepting the Minecraft EULA, is:

```sh
uv run --locked minecraft-server setup --minecraft-name YourJavaName --accept-eula
uv run --locked minecraft-server start
uv run --locked minecraft-server security
```

Minecraft 1.20.1 / Forge 47.4.23 / Java 25 are the selected runtime. A nonempty allowlist is required. The first image pull is pinned by digest in the private profile. The manager will not silently change an existing world's Minecraft/Forge/Java runtime. A game's first startup may take several minutes.

## Daily operations

```sh
uv run --locked minecraft-server status
uv run --locked minecraft-server logs --lines 100
uv run --locked minecraft-server start
uv run --locked minecraft-server stop
uv run --locked minecraft-server restart
uv run --locked minecraft-server security
```

The dashboard provides start, graceful stop, backups, joining instructions, player access, and mod switches. Stop saves and waits for a clean exit instead of force-killing the server. Keep the laptop awake during play. Exiting the dashboard does not stop the Minecraft container; stop the game explicitly before shutting down Docker or the laptop.

`security` inspects actual port mappings, server authentication/whitelist settings, allowed players and operators. It is a configuration check, not a substitute for a real allowed-player login and unapproved-player rejection test. A failure needs investigation before play.

## Players and game administrators

```sh
uv run --locked minecraft-server players add FriendJavaName
uv run --locked minecraft-server players list
uv run --locked minecraft-server players ban FriendJavaName
uv run --locked minecraft-server players unban FriendJavaName
uv run --locked minecraft-server players remove FriendJavaName
```

These are also available under **Players**. Ban/remove disconnect a running player when Docker/RCON works, revoke operator privileges and persist exclusion across restarts. They do not delete builds. If synchronization fails, the command reports failure; stop the game rather than assuming the player was disconnected. An unban does not re-add a removed player; add them again separately.

In config.yml, `server.operators` names the intended game administrators and must be a subset of `server.allowlist`. Game operators and the website admin are different things. Banned/removed names are filtered out before granting operator access. Keep online mode and whitelist enforcement enabled; Minecraft authenticates players using their own Microsoft/Minecraft accounts. Do not share those account passwords.

## Mods

Install only reviewed compatible Forge JARs and their required dependencies while stopped:

```sh
uv run --locked minecraft-server mods-install /absolute/path/example.jar --sha256 VERIFIED_SHA256
uv run --locked minecraft-server mods-list
uv run --locked minecraft-server mods-disable example.jar
uv run --locked minecraft-server mods-enable example.jar
```

Installed server mods default to enabled. World care offers the same switches. Disabled files remain in `data/disabled-mods` and are backed up. Changes while running or after an unclean stop are refused. Back up before changing content mods; disabling a dependency can prevent startup. Client-only rendering mods, shaders and resource packs belong on clients. See [the requested modpack](forge-modpack.md) for unresolved compatibility work. Do not claim the full pack is installed just because Forge is healthy.

## Backup and restore

```sh
uv run --locked minecraft-server stop
uv run --locked minecraft-server backup
uv run --locked minecraft-server backups
uv run --locked minecraft-server restore /absolute/path/backup.zip --confirm-profile forge
```

Backups contain the whole game data directory, including enabled/disabled mods, and a checksum manifest. Treat ZIPs as sensitive: game/plugin settings can contain secrets. Keep an independent off-laptop copy. Also back up the adjacent private `.clubhouse-*.json` access store separately; it holds the admin hash and persistent bans/removals and is deliberately outside game backups. Preserve it when moving a profile.

Restore validates into staging and retains the previous data as `data.rollback`; it refuses to overwrite that rollback. Verify the restored world before archiving/removing the rollback yourself. Rehearse in a distinct disposable profile first; never use the real world for destructive tests.

## Troubleshooting

- Docker unavailable: open Docker Desktop, wait for the engine, then retry. On macOS the manager can use Docker's bundled CLI even without system command links.
- Startup failure: read `logs`; inspect incompatible/missing mod dependencies and memory. Stop cleanly before changes.
- Cannot join: confirm exact Java username, Minecraft/Forge/modpack versions and server health; other devices cannot reach a loopback-only bind.
- Lost admin password: rerun `admin owner`; no Microsoft account recovery is involved.
- CLI/UI conflicts: wait for the existing operation. Do not delete locks or bypass the manager to mutate live data.
