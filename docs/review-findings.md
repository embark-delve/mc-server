> **Baseline review (df94b16).** Subsequent repairs are tracked in [implementation status](implementation-status.md); use the [current README](../README.md) for commands.

# Codebase findings

Date: 2026-09-27. Baseline: `df94b16`. Source line numbers below refer to that baseline. **Reproduced** means exercised locally without a live Minecraft server. **Static** means established by reading the implementation; external/runtime behavior still needs an integration test. Priorities are defined in [the overview](laptop-readiness.md).

## F01 — P0: Restore can destroy the world and move unrelated directories

**Reproduced.** `src/utils/file_manager.py:159–200`; caller `src/implementations/docker_server.py:477–499`.

Restore unpacks directly into `base_dir`, enumerates every directory there, chooses the first directory as the restore source, deletes `target_dir`, and moves that arbitrary source into its place. When the first directory is `data`, it deletes the directory it is about to move. When it is another directory, such as `backups`, `plugins`, `src`, or `.git`, it can move unrelated content instead. Enumeration order is not a valid archive format.

A reproduction with only disposable `data/world.txt` and a valid ZIP returned `False` and left the world file missing. Failure is reported only after deletion. The caller also ignores the return value of `stop()` and does not independently verify a stopped server before extraction.

**Required fix:** refuse restoration unless stop is verified; validate the archive and expected layout in a fresh staging directory; restrict members to the intended profile roots; reject unsafe paths, links, unexpected roots, oversized expansions, and corrupt files; preserve the existing data as rollback; switch directories only after validation; revert on failure. Add per-profile locking. Never enumerate arbitrary repository directories to find the restored world. This is a confirmed destructive logic bug; the review does **not** claim a proven generic ZIP traversal exploit in Python's extraction library.

**Acceptance:** exact backup/restore round trip; corrupt or unexpected archives leave original data unchanged; an unrelated directory stays untouched; failed stop prevents extraction; interrupted replacement has a documented recovery path.

## F02 — P0: Committed configuration makes the quick start fail

**Reproduced.** `config.yml:11–18`, `src/utils/config.py:64–74`, `src/minecraft_server_manager.py:58–86`.

The sample uses `server.type: PAPER` to mean Minecraft flavor. `Config` puts it into both deployment type and flavor. The manager accepts only `docker` or `aws`, so even `python minecraft-server.py status` raises `ValueError: Unsupported server type: paper`. Supplying `--type docker` bypasses this one issue but exposes F03.

**Required fix:** define separate validated fields for backend and flavor, migrate the example, reject invalid combinations, and put initialization inside the CLI error boundary. Fail on malformed or mistyped configuration instead of logging and silently continuing with defaults. Validate positive timeouts, ports, memory sizes, directories, versions, and flavor-specific settings. Preserve the documented precedence: defaults < file < environment < explicitly supplied CLI values.

## F03 — P0: Default monitoring crashes construction and opens a listener too early

**Reproduced with the HTTP server mocked.** `src/core/base_server.py:90–98`, `src/implementations/docker_server.py:103–111`, `src/utils/monitoring.py:95–111,205–267`.

The base class creates a monitor and the Docker subclass creates another. Both register identical gauges in Prometheus's global registry, causing `DuplicateTimeseries` on the second initialization. This happens before normal server actions and is independent of Docker availability. An additional instance in the same process has the same problem.

Construction starts the first metrics HTTP server with no explicit bind address. That makes even status/backup construction attempt to expose a metrics listener. The sandbox blocked the socket in the test suite, but the duplicate registration was separately reproduced with socket startup mocked, so the central failure is not a sandbox artifact.

**Required fix:** initialize once, make monitoring opt-in, avoid network side effects in constructors, and use an explicit loopback binding and managed collector registry/lifecycle. Ensure multiple profiles do not compete for port 9100 or duplicate metrics. Turning monitoring off in YAML currently cannot work around this through the primary CLI because of F04.

## F04 — P0: Important settings are accepted but ignored or overwritten

**Static plus focused reproductions.** `minecraft-server.py:101–135`, `src/utils/config.py:50–209`, `src/core/base_server.py:59–76`, `src/implementations/docker_server.py:615–664`.

The CLI passes only backend, version, flavor, and two idle settings to the manager. It drops memory, base directory, and monitoring/export settings. `--memory 4G` is parsed, but the base class still uses `2G`. The README's `MinecraftServerManager(memory="4G")` raises `TypeError` because the Docker constructor accepts no memory argument.

`RCON_PASSWORD` from `.env.example` is not read by `Config` or used by the Compose template. Sample container name, ports, difficulty, mode, backup retention/schedule, plugin restart policy, and path subdirectories are not wired through. Non-default `data_dir_name` changes the manager's path but Compose still mounts `./data`; backup can therefore target different data from the running server.

Argparse's absent boolean flags arrive as `False`: `from_args` then turns auto-shutdown back on and resets debug to false, overriding file/environment choices. This was reproduced. `server.type: docker` without `flavor` also incorrectly assigns `docker` as the flavor through the legacy fallback.

**Required fix:** one typed configuration model passed to the backend; explicit missing-value handling for boolean CLI flags; schema validation and unknown-key errors; normalized profile paths; a redacted effective-configuration command. Test generated Compose values and runtime arguments, not just individual config getters. Document unsupported fields instead of accepting inert knobs.

## F05 — P0: Network and credential defaults need a local safety boundary

**Static.** `src/implementations/docker_server.py:624–648`, `.env.example`, `config.yml`.

The game mapping `25565:25565` has no host IP. Docker publishes such mappings on all host interfaces, subject to host networking and firewall conditions. That is wider than laptop-only use; it does not by itself establish internet reachability. [Docker port publishing](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/).

The RCON password is hard-coded to `minecraft`; changing `.env` gives a false sense of protection because it is ignored. **RCON port 25575 is not published by the generated Compose file**, so this is not a finding of directly internet-exposed RCON. It remains an administrative interface reachable within applicable container networks. `ENFORCE_SECURE_PROFILE` is explicitly disabled. This does not mean account authentication is disabled: the code does not explicitly set `ONLINE_MODE=false`.

**Required fix:** default to `127.0.0.1:HOST_PORT:25565`; require explicit LAN mode; set `ONLINE_MODE=true`, enable the allowlist for private play, and default secure profiles on unless a documented compatibility need requires otherwise. Use a per-profile random secret stored in a protected ignored file, with `RCON_PASSWORD_FILE`; keep RCON unpublished. Redact secrets in diagnostics, backups shared with others, and generated configuration displays. [Image server-property and RCON options](https://docker-minecraft-server.readthedocs.io/en/latest/configuration/server-properties/).

A malicious plugin runs code with the container's access to mounted world/config files. Bind only profile-specific directories, do not mount the Docker socket into the game container, and keep host credentials outside its mounts. Trusted private players and a local bind reduce exposure but do not make downloaded plugins trustworthy.

## F06 — P0: Backup creation is not a reliable recovery contract

**Static.** `src/implementations/docker_server.py:438–475`, `src/utils/file_manager.py:59–156`, `src/utils/config.py:80–83`.

The live backup path prints a warning and broadcasts a message, but does not flush/freeze saves or stop the server. It zips only `data_dir`, excluding the separate plugin source, configuration source, and resolved deployment settings. Some plugin files may have been copied into `/data` by the image, but the complete source state is not guaranteed. Retention exists as an isolated utility and is never invoked by Docker backup; the advertised cron schedule is not implemented. Second-resolution archive names can collide. Archive creation is not an atomic publish operation.

**Required fix:** initially support stopped-server backups only, with confirmed shutdown and exclusive profile access. Include the complete necessary state and a manifest of Minecraft build, image digest, and plugin hashes. Write to a temporary archive, verify it, then rename. Add unique names, free-space checks, and retention applied only after a successful backup. A later live-backup workflow must coordinate `save-off`, `save-all flush`, and `save-on` in `finally`, and account for plugins' own stores. Prove recovery in a separate profile and keep a second copy outside the laptop for important worlds.

## F07 — P0: Server lifecycle reports the wrong state

**Static.** `src/implementations/docker_server.py:117–137,187–281,309–341`, `src/utils/command_executor.py:24–73`, `src/commands/server_commands.py:18–143`.

Startup treats presence in `docker ps` as success, not Minecraft readiness or container health; image download, initialization, or a restart loop can be mistaken for a ready game. Stop issues RCON `stop`, sleeps five seconds, then runs Compose down without a configured save grace period. `is_running()` converts Docker failures into false, so a missing or inaccessible daemon can be presented as an already stopped server. Stopped/crashed containers skip cleanup. The `unless-stopped` policy also needs testing when the JVM exits after an RCON stop.

Commands have no subprocess timeout. The executor defaults to `check=True`, while callers often expect to inspect nonzero return codes; some error paths are therefore unreachable. CLI handlers print failure on false results but normally return success to the OS. Constructor failures occur outside the exception handler.

**Required fix:** distinguish absent, stopped, starting, healthy, unhealthy, paused, and Docker-unavailable states; use the image's Minecraft health check with a configurable startup deadline; wait for verified shutdown with an adequate configurable grace period; propagate useful errors and nonzero exit codes. Validate profile identity using Compose project/service labels before operating on containers. [Image health checking](https://docker-minecraft-server.readthedocs.io/en/latest/misc/healthcheck/).

## F08 — P0: Version drift and missing laptop resource limits

**Static; current compatibility checked upstream.** `src/implementations/docker_server.py:37,46,622–637,659`, `config.yml:18`.

The default API pairs Minecraft `latest` with `java21`; the sample instead fixes Minecraft at 1.20.4. These are inconsistent policies. Current Paper 26.1+ needs Java 25. Pin a compatible server release/build and image release/digest, and keep separate profiles for older modpacks. Floating server versions can also upgrade persistent world formats unexpectedly. [Paper Java requirements](https://docs.papermc.io/paper/getting-started/), [image version selection](https://docker-minecraft-server.readthedocs.io/en/latest/versions/java/).

`MEMORY` sets Java heap behavior, not a hard Docker memory limit. The generated service has no CPU/memory cap or Docker log rotation. This can exhaust laptop resources alongside the game client and Docker VM. Select an actual RAM budget after checking the machine; provide container memory headroom beyond the heap, CPU limits, lower view/simulation distances, and rotating logs. Avoid combining hand-selected JVM options with automatic flag sets without testing the resulting command. Do not benchmark or recommend a player capacity from the unverified host specifications.

## F09 — P1: Idle management does not survive the normal CLI lifecycle

**Static.** `src/utils/auto_shutdown.py:68–193`, `src/implementations/docker_server.py:144–178,280–283,325–326,650–652`.

The Python monitor is a daemon thread and dies when the `start` CLI exits. It does not periodically query the server; player lists are refreshed on status calls, with empty-list updates missing in several branches. In a long-running API process the timer can expire despite players being present. On expiry, the callback calls `DockerServer.stop()`, which calls `stop_monitoring()` and tries to join the current thread; that raises instead of completing shutdown. Threshold updates do not consistently update the container configuration.

The generated `ENABLE_AUTOPAUSE` separately enables an image-level pause mechanism. Pause is not shutdown and does not mean memory or Docker VM resources have been released. Choose one explicit behavior: manual stop for the initial release, image-native pause for faster return, or image-native auto-stop for releasing server resources. Image auto-stop and autopause are incompatible, and auto-stop needs a restart policy that does not immediately restart the container. [Auto-pause](https://docker-minecraft-server.readthedocs.io/en/latest/misc/autopause-autostop/autopause/), [auto-stop](https://docker-minecraft-server.readthedocs.io/en/latest/misc/autopause-autostop/autostop/).

## F10 — P1: Advertised mod management is unfinished and unsafe to enable

**Reproduced.** `src/utils/mod_manager.py:185–254,284–402,439–492`.

Every provider lookup is mocked. Installation writes `Mock mod file content` and reports success. Stored metadata uses `file` and `installed_date`, while uninstall expects `filename` and listing expects `installed_at`; a successful mock install cannot be uninstalled through the public method. Updates remove the old version before obtaining a replacement. Forge/Fabric content is routed through the plugins directory, not a loader-specific mods workflow. The compatibility table rejects Modrinth for Paper and treats repositories as if they were loaders.

Filenames/identifiers and cached uninstall paths are not constrained to the plugin directory; untrusted input can select paths outside it. This is a local/API input validation issue, not a demonstrated remote game-client exploit.

**Required fix:** explicitly mark downloads unsupported or disable the feature first. For initial play, permit reviewed manual plugins for a single flavor. Later use maintained image integrations or real provider APIs; validate server-side support, game version, loader, dependencies, and hashes; bound network requests; install atomically; preserve the previous version until validation succeeds; constrain all file paths; use one metadata schema. Never treat a checksum as proof that a plugin is benign.

## F11 — P1: Multiple-server support and persistent identity are missing

**Static with custom-directory mismatch reproduced.** `src/minecraft_server_manager.py:51–68`, `src/implementations/docker_server.py:32–36,104–110,117–137,615–664`, `src/utils/monitoring.py:450–463`.

One hard-coded host port, default container name, repository-local storage, and implicit Compose project prevent safe multi-instance use. A matching unrelated container name is sufficient for `is_running()`. Monitoring hard-codes `minecraft-server`. Each start rewrites `docker-compose.yml`, erasing manual security/configuration edits. CLI version overrides are not persisted, so a later start can regenerate different settings.

**Required fix:** a profile ID mapping to a persisted configuration, independent data/backups, unique Compose project, host port, and metrics labels. Use explicit Compose file/project arguments and Docker labels, avoid fixed container names where possible, and serialize lifecycle operations per profile. Reject path/port conflicts before startup. Backups and restores must retain profile/version provenance. Running two servers must not stop, modify, or back up each other.

## F12 — P1: Packaging, dependencies, and CI are not a working maintenance baseline

**Wheel contents verified; checks executed.** `pyproject.toml:17,36–44,70–74`, `requirements*.txt`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `Makefile`.

- Entry point `src.minecraft_manager:main` names a nonexistent module. `packages = ["src"]` produces a wheel containing only `src/__init__.py` and `src/minecraft_server_manager.py`, omitting all backend/util/command subpackages. The standalone entry script is not packaged.
- Package metadata omits required imports such as PyYAML, python-dotenv, and rich; the requirements file differs, includes development tools, repeats entries, and adds the obsolete pathlib backport. AWS dependencies are eagerly imported even for local use.
- Lower bounds without a lock resolve differently over time and allow old vulnerable releases. This review's freshly resolved environment is not evidence about packages you installed last year. See [audit limits](review-validation.md).
- Python 3.8/3.9 remain advertised and tested despite end-of-life. Current mypy rejects the configured Python 3.8 target. CI and pre-commit use differing tool generations and dependency sets.
- Executed tests: 12 failed, 28 passed, one expected failure. The CLI tests patch original modules rather than the imported names used by the CLI; monitoring tests share registry side effects. Production code has special `MagicMock` branches instead of enforcing subprocess contracts.
- No automated archive recovery tests or isolated real Docker smoke test protects the central data path. The committed coverage XML is historical, not current proof of readiness.
- Terraform validation runs in `terraform/aws`, which has nested modules/environments but no root `.tf` files; `fmt` is nonrecursive and allowed to fail. Root Terraform files are empty. Validate actual environment/module roots on PRs if retained.
- CI uses aging action tags and `checkov-action@master`; add minimal job permissions and pin reviewed action revisions. Container publication needs explicit package-write permission if not supplied by repository defaults. Do not assume it currently succeeds.
- `docs-build` changes into `docs` while using a relative `.venv` tool path; no MkDocs config is supplied. Pre-commit references absent Terraform config files. `make run-aws` passes CLI flags the parser does not accept. README refers to a missing LICENSE file.

**Required fix:** one installable CLI module and discovered packages; one authoritative dependency specification with optional cloud/dev extras; a reproducible dependency lock and updates; a current supported Python matrix; passing unit tests, lint and types; a wheel-install smoke test from outside the checkout; dependency/container/secret scans. Upgrade tools deliberately rather than merely chasing all formatting warnings first.

## F13 — P1/P2: Metrics are not yet useful operational evidence

**Static plus size-parser reproduction.** `src/utils/monitoring.py:119–202,311–350,440–561`, `src/implementations/docker_server.py:start`.

Docker startup never calls `monitor.start()`. Collected names such as `container_cpu_percent` do not match registered gauge keys such as `cpu_usage`; player/TPS/heap gauges are not populated by an implemented collector. The size parser returns **2 bytes for `2GiB`**, because slicing uses the length of the converted float string rather than the original numeric token. Host metrics reflect the manager host, not necessarily the game container or Docker VM. AWS collection is a placeholder. The manager/status keys also disagree about version and uptime.

**Required fix:** initially provide accurate on-demand status and Docker resource use without an HTTP exporter. If persistent metrics are desired, run a separate supported collector, distinguish host/container/game measurements, and test units, names, freshness, profile identity, and lifecycle.

## F14 — P1 before cloud use, P2 for laptop scope: Other deployment paths need quarantine

**Static, no cloud resources created.** `src/implementations/aws_server.py`, `terraform/aws/`, `kubernetes/`, `docker/`, `Dockerfile`.

AWS interpolates console text directly into `AWS-RunShellScript` (`aws_server.py:428`) and interpolates mod IDs into `sudo rm -f` (`:740`). Shell metacharacters can escape the intended Minecraft command/path when caller-provided input reaches these methods. Quote/validate remote arguments and prefer a narrowly scoped remote operation. This is not the same as the Docker backend, which uses subprocess argument lists with shell disabled.

AWS also passes an unsupported `aws_region` argument to `ServerMonitor`, assumes a systemd Minecraft service and host `rcon-cli`, while Terraform provisions Docker Compose, and claims instance creation it does not implement. Stop does not stop the EC2 instance, so it is not cloud cost shutdown. Restore submits asynchronous extraction without checking success and appears to nest an archive's `data/` under the target `data/`. Terraform omits an SSM instance profile/agent setup contract and defaults SSH ingress to the entire internet; resolve these before cloud use.

Kubernetes embeds the same fixed RCON secret and EULA acceptance, uses a floating image, a provider-specific storage class, and no game readiness probes. It is not connected to a Python Kubernetes implementation despite the architecture diagram.

The manager Dockerfile copies the full build context, has no `.dockerignore`, runs as root, lacks the Docker CLI/Compose it invokes, and declares volumes that do not match its default `/app` data paths. Local `.env` files or worlds can enter a local build context/image; `.gitignore` does not protect Docker builds. Do not publish a locally built image until a `.dockerignore` and packaging contract are in place. Running the manager on the host is simpler for this laptop scope.

The older shell manager uses a different data root and the legacy `docker-compose` binary, expects an absent Compose file, and has a restore menu that never appends to its backup array. `set -e` can bypass its advertised restore rollback. Its smoke script exits on the first `((SUCCESS++))` or `((FAILURE++))` when the old value is zero. Consolidate on one supported CLI; deprecate these alternate paths rather than maintaining contradictory instructions.

## F15 — P1: Documentation promises exceed implementation

**Static.** `README.md`, `docs/architecture.md`, `docs/server-configuration.md`, `docs/mods-and-plugins.md`, `examples/advanced_server_management.py`.

The architecture says the manager uses the factory, but it constructs backends directly. It depicts an absent Kubernetes implementation. The README advertises mock mods and unusable memory arguments; configuration docs describe ignored fields; editing Compose by hand is advised even though the next manager start overwrites it. Several guides use incompatible schemas or outdated version examples.

Rewrite around one executable local quick start. Distinguish implemented, experimental, and planned capabilities. Document Java Edition, explicit EULA acceptance, backup recovery, local/LAN access, version pinning, macOS sleep, data ownership, and every supported flag. Generate command reference from the CLI where practical. EULA should be a conscious setup choice, not unconditionally emitted as `TRUE` by code.

## Useful foundations to retain

The image-based runtime avoids maintaining a custom Java launcher; persistent `/data` binding is already present. Configuration uses `yaml.safe_load`. Docker commands normally use argument lists rather than a shell. Interfaces and the small command registry provide useful seams for tests. Keep these parts, simplify construction and configuration, and prioritize correct data handling over a broad architectural rewrite.
