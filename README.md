# Minecraft Server Manager

A local CLI and single-admin web manager for **Minecraft Java Edition 1.20.1 / Forge 47.4.23**, targeting **Java 25**. It runs the game in Docker and keeps each server's files outside this repository.

The original prototype has been replaced with a smaller supported local path. AWS, Kubernetes, legacy shell management, mock mod downloads, automatic shutdown and persistent metrics are disabled. The web dashboard provides the everyday server controls; advanced restore and JAR installation remain in the CLI.

**Validation status:** code-level safety tests and packaging checks are automated. The installed 13-JAR mod subset starts cleanly in Docker; full wishlist compatibility and actual client admission/rejection still require validation; see [implementation status](docs/implementation-status.md). Do not treat a passing unit suite as proof that the modpack loads.

## Install

Install a current Python 3.13 and [uv](https://docs.astral.sh/uv/getting-started/installation/), plus a working local Docker engine with Compose v2 (for example [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)). Java is supplied by the game image; no host Java installation is needed.

```sh
uv sync --locked
uv run --locked minecraft-server --help
docker version
docker compose version
```

`pyproject.toml` defines dependencies; `uv.lock` pins the resolved set. There is no maintained requirements.txt. Python dependencies, Java, Minecraft, Forge and individual mods have separate version contracts.

## Configure and initialize

The checked-in `config.yml` describes this laptop, including its explicitly enabled LAN bind and player list. For a new installation, change those values first; use `127.0.0.1` and `allow_lan: false` until remote access is intentionally configured.

Edit `config.yml`: add your exact Minecraft username to `server.allowlist`, select a heap/container budget your laptop can support, and optionally set `paths.base_dir` to an empty dedicated directory. Default storage is `~/MinecraftServers/forge`. The initial 4G heap / 6G container values are configurable starting values, not a measured recommendation for your laptop.

```sh
uv run --locked minecraft-server config
uv run --locked minecraft-server render
```

Read the [Minecraft EULA](https://aka.ms/MinecraftEULA). Only if you accept it:

```sh
uv run --locked minecraft-server init --accept-eula
```

Initialization creates private profile directories and a random private RCON secret. It refuses to adopt a nonempty directory. It does not download or start Minecraft. EULA agreement is recorded explicitly in that profile, not inferred from a config file.

## Operate

```sh
uv run --locked minecraft-server start
uv run --locked minecraft-server status
uv run --locked minecraft-server logs --lines 100
uv run --locked minecraft-server console list
uv run --locked minecraft-server stop
uv run --locked minecraft-server backup
uv run --locked minecraft-server backups
```

Connect from the Java Edition client using the configured `server.bind_address:25565` on this laptop/LAN, or the router’s public address for remote players. This laptop configuration explicitly enables a LAN game binding for owner-configured TCP port forwarding. Authentication and allowlisting remain enabled; the dashboard stays localhost-only and RCON is not published. See [remote access](docs/remote-access.md) for validation limits and how to disable forwarding. New configurations default to loopback unless explicitly changed.

The first start downloads the configured image and records its immutable digest in `runtime.json`. Later starts use that digest. Game/Forge/Java/image changes are refused once a world has a runtime lock: test upgrades in a separate profile. Startup succeeds only after Minecraft's health check passes. Stop waits for a clean game exit and refuses to force-kill if saving exceeds the deadline. A failed startup can leave a container running for diagnosis; use logs/status and stop explicitly.

Stop before closing the laptop, quitting Docker Desktop, backing up, restoring, or changing mods. The manager does not keep a background process alive after the CLI exits.

## Mods and client content

See the complete requested list and unresolved choices in [the Forge pack plan](docs/forge-modpack.md). The [installed version manifest](docs/installed-mods.md) records the 13 server JARs already installed and verified. Exact client matching and the remaining wishlist are still pending. Embeddium and Oculus are client-side; resource packs and shaders belong in the client. A NeoForge artifact is not automatically a Forge artifact. Do not install every listed item on the server indiscriminately.

The current supported install path is a reviewed local Forge JAR with an expected SHA-256 from a trusted manifest/source:

```sh
uv run --locked minecraft-server mods-install /absolute/path/mod.jar --sha256 EXPECTED_64_HEX_DIGEST
uv run --locked minecraft-server mods-list
uv run --locked minecraft-server mods-remove exact-filename.jar
```

Installation checks the hash and Forge metadata and refuses known/declared client-only files. It is not a malware scan or proof of dependency/Java compatibility. Never take an untrusted download and treat hashing it yourself as establishing trust. Back up before replacing mods; old filenames are never silently overwritten. All server mods live inside the backed-up `data/mods` directory.

## Backups and recovery

Managed backups require a stopped server. They include all `data/` (worlds, mods, configs, player state), a checksum manifest and runtime/config metadata. Archives are private files and may contain plugin credentials or a generated server.properties RCON password: protect them and do not publish them. Keep an independent copy outside the laptop for valuable worlds.

Restore requires an explicit archive and target-profile confirmation:

```sh
uv run --locked minecraft-server restore /absolute/path/backup.zip --confirm-profile forge
```

Restoration validates and extracts into staging before touching the world. Previous data is retained as `data.rollback`. Verify the restored world before moving that rollback directory to safe storage; another restore refuses to overwrite it. The manager refuses old unmanifested ZIPs: preserve original archives and recover them manually into a new empty directory, never into the checkout or a live server.

For a recovery rehearsal, copy `config.yml` to a separate YAML file, change its profile name, data root and game port, initialize it after EULA acceptance, and restore the backup there. A fresh empty profile may adopt the image digest from a compatible backup. All runtime settings must match; the game port and target directory may differ.

If interrupted after `data` was renamed to `data.rollback`, leave the server stopped, preserve all directories, and restore that rollback to `data` manually. Do not initialize over existing files. The retained directory is intentionally not automatically deleted.

## Multiple servers

Use one YAML file, distinct profile name, independent base directory and host port per server:

```sh
uv run --locked minecraft-server --config profiles/creative.yml start
uv run --locked minecraft-server --config profiles/creative.yml stop
```

Commands derive a Compose project identity from the profile name and data root. They do not target arbitrary containers by a shared default name. Ports must be unique, and the combined heaps/containers must fit your Docker VM and laptop. Per-profile locks prevent concurrent manager operations; do not bypass them by editing live world files or starting the same directory manually.

## Development

```sh
uv sync --locked
make bootstrap   # Local Node, locked tools, pre-commit + pre-push hooks
make check       # Python/frontend lint, types, Bandit and tests
make security    # Python/npm dependency audits and history secret scan
uv build         # Source archive and complete installable wheel
```

Run `make format` before committing. Review dependency updates through `uv lock --upgrade` and re-run all checks. The Dockerfile is an **offline CLI inspection image**; it deliberately does not receive the Docker socket and is not a server-management deployment.

## Documentation

Start with the [admin guide](docs/admin-guide.md), [development checks](docs/development.md), and [outside-network access](docs/remote-access.md).

- [Implementation status and remaining validation](docs/implementation-status.md)
- [Requested Forge modpack](docs/forge-modpack.md)
- [Original review](docs/laptop-readiness.md), [findings](docs/review-findings.md), [validation evidence](docs/review-validation.md)

The original review and older guides are historical. The review's line numbers refer to baseline `df94b16`; this README describes the replacement local implementation.

## Family web dashboard

```sh
uv run --locked minecraft-server web
```

Open the owner bootstrap link printed in your terminal, or configure the single admin with `uv run --locked minecraft-server admin owner` and sign in. The dashboard is laptop-only. Anyone using the admin login can set up the world, add/ban/remove Minecraft players, start/stop/restart, view logs, toggle installed mods, and create backups. There are no player website accounts or grown-up approval gates. Keep the owner link private.

Minecraft still runs in Docker. The CLI/web manager runs on the laptop; the dashboard does not expose or mount a Docker socket. A working Docker engine, your explicit EULA acceptance, an approved username allowlist, and a validated modpack are needed before live play.

After starting the game, inspect its actual access controls:

```sh
uv run --locked minecraft-server security
```

Use **Server**, **Mods**, **Players**, **Backups**, **Logs**, **Join**, and **Settings**. Password changes are in Settings only. See [current UI capabilities](docs/web-ui-review.md), [security boundaries](docs/web-ui-security.md), and the [documentation index](docs/README.md).

See [accounts and invitations](docs/accounts-and-invitations.md) for single-admin setup and Minecraft player controls. Website credentials do not replace Minecraft/Microsoft authentication.
