> **Baseline review (df94b16).** Subsequent repairs are tracked in [implementation status](implementation-status.md); use the [current README](../README.md) for commands.

# Implementation plan for reliable laptop servers

Review date: 2026-09-27. This is a backlog, not a list of completed changes. Finding IDs refer to [review-findings.md](review-findings.md).

## Stage 1 — Make one disposable local server work

Complete these together before recommending the README quick start.

| Work package | Concrete changes | Acceptance criteria |
| --- | --- | --- |
| Configuration contract (F02, F04) | Separate backend/flavor; validate settings; wire memory, paths, ports, monitoring, security and version; migrate examples; preserve CLI precedence | Sample config loads as Docker/Paper; omitted flags preserve file values; invalid settings fail before side effects; generated settings match effective config |
| Construction (F03) | Remove duplicate initialization; default metrics and Python idle monitor off; lazy-load cloud imports | `--help` and local status need no AWS configuration and open no listening socket; constructing two profiles succeeds |
| Local security (F05, F08, F15) | Loopback default; explicit LAN opt-in; private RCON secret; online authentication; private allowlist; explicit EULA choice; pinned release/Java; resource and log limits | Generated Compose publishes only the requested game interface/port; RCON and metrics remain private; settings survive restart; secret is absent from logs and Git |
| Lifecycle (F07) | Explicit Compose project/file; verified ownership; health-based readiness; command timeouts; graceful stop deadline; distinct unavailable/error states; nonzero failure exits | No success before Minecraft responds; Docker unavailable differs from stopped; stop waits for saves; repeated start/stop is safe; failure exits nonzero |
| Honest feature boundaries (F09, F10) | Disable placeholder mod installs and unreliable idle behavior; label AWS/Kubernetes experimental | No command claims to install a fake mod or provide persistent monitoring; local setup uses one documented path |

**Gate:** start a new throwaway world, join from the same laptop, place a block, stop, restart, and verify the block. Inspect actual runtime port bindings, Java version, heap, memory limit, image digest, data mount and logs. No internet exposure or cloud deployment is required.

## Stage 2 — Make worlds recoverable before normal use

| Work package | Concrete changes | Acceptance criteria |
| --- | --- | --- |
| Consistent backup (F06) | Confirm stopped state; per-profile operation lock; complete state manifest; atomic archive creation; unique names; disk-space and checksum checks | Backup contains a coherent world and necessary settings; interrupted/full-disk backup does not replace a good archive |
| Safe restore (F01) | Extract to new staging directory; validate layout/content/size; retain previous state; atomic replacement with rollback | Successful round trip into a new profile; malformed ZIP, wrong root, path escape, failed stop and interrupted restore do not destroy original data |
| Recovery operations (F06) | Retention after success; list/inspect backups; documented manual recovery; second storage location for valuable worlds | Retention keeps requested good snapshots; restore is rehearsed independently; user can locate data and recover without relying on a working manager |

**Gate:** restore a stopped-server backup into a different directory and port, join it, and verify representative builds/inventories/dimensions. Run the same verification after an upgrade rehearsal. Do not reuse the current restore code as a shortcut.

Stages 1 and 2 are the minimum path to a valuable world. If a feature is deferred, make it unavailable explicitly rather than leaving an unsafe command exposed.

## Stage 3 — Establish a maintainable release

- **Package correctly (F12):** provide a real importable CLI, discover all packages, declare complete runtime dependencies, and move optional AWS dependencies to an extra. Verify a wheel installed outside the checkout can run help/config/status.
- **Choose a supported Python baseline:** initially test Python 3.13 with current patches, then expand only to versions actually supported by dependencies and CI. Remove 3.8/3.9 claims. Keep the development/tool dependency set consistent across local checks and CI.
- **Make installs repeatable:** commit a resolver-generated lock including transitive packages; remove duplicate/unused requirements and the pathlib backport. Establish an intentional update cadence and security scan. Pin image releases/digests while planning timely updates.
- **Repair tests:** patch dependencies at their use sites, isolate registries and temporary files, remove production mock-specific behavior, use fake clocks for idle tests, and add the data/lifecycle regression cases above.
- **Run a Docker smoke test:** use unique disposable names/directories/ports, never the default real world. Test both normal stop/start and failure paths. Cover arm64 macOS manually and the selected Linux CI platform; a Linux-only unit suite does not prove Docker Desktop behavior.
- **Repair CI and docs:** reviewed action revisions, minimal permissions, actual Terraform roots if retained, dependency scanning, package smoke test, and one current local guide. Either make the docs build work or remove the broken target. Retire stale scripts/examples and decide the missing license file.

**Gate:** clean install, tests, lint, type checking, package smoke test and Docker scenario pass using the committed dependency set. New documentation must match executed commands.

## Stage 4 — Support several servers safely

Required if you want multiple worlds running at once; sequential use can begin after the earlier stages.

- Named profiles persist backend, flavor, exact release/build, Java image, port, heap/container budgets, and all storage paths.
- Each profile has a distinct Compose project and independent data, backups, config and secrets. Avoid forcing `container_name`; use service identity and labels.
- Add profile list/select/status plus conflict checks. Proposed commands such as `profile create` are new features, not existing CLI syntax.
- Enforce aggregate laptop/Docker VM budgets and warn about port collisions before startup. Do not assume the sum of heaps equals total memory use.
- Per-profile locks prevent concurrent start/restore/update. Backup metadata identifies the source profile but restoration into a new profile requires an explicit target.

**Gate:** two disposable servers run on separate ports; stopping/restoring one leaves the other running with unchanged files. A mistaken profile ID, reused port, or overlapping data directory fails safely.

## Stage 5 — Add conveniences only when needed

| Feature | Recommended scope | Readiness test |
| --- | --- | --- |
| Logs and diagnostics | Primary CLI `logs`, resolved/redacted config, installed/runtime versions, Docker health, free disk, connection address | Accurate data for the selected profile; unavailable readings show unknown rather than zero |
| Idle behavior | One explicit mode: manual stop, native pause, or native auto-stop | Works after CLI exit, respects connected players, resumes/restarts as documented, survives laptop sleep sensibly |
| Backup scheduling | A persistent scheduler with missed-run behavior and last-success reporting | Schedule continues beyond CLI lifetime, avoids overlapping operations, reports failures |
| Plugin management | Start with manual reviewed Paper plugins; later integrate real version/hash-aware providers | Valid JAR, compatible release/loader, bounded paths, successful rollback and metadata round trip |
| Upgrades | Preview planned changes; pre-upgrade backup; restore a copy for trial; explicit apply | Failed upgrade retains original profile; rollback restores old world and matching runtime |
| Metrics | On-demand resource reporting first; separate exporter only if needed | Correct units, selected container, freshness, loopback listener and no duplicate registry |
| LAN/friends | Allowlist and intentional interface exposure; document firewall/address behavior | Trusted client joins; unlisted client rejected; admin ports inaccessible externally |
| Bedrock/crossplay | Separate scoped design if your clients require it | Edition/protocol, plugin support, and extra network requirements tested explicitly |
| Cloud/Kubernetes/UI | Deferred | Separate security and deployment review before enabling |

## Suggested delivery order

1. Configuration/constructor/package repairs with no live-server changes.
2. Safe Compose generation and lifecycle, tested on disposable data.
3. Backup/restore replacement and recovery regression tests.
4. Current CI/dependency baseline and operating docs.
5. Named profiles and two-server integration test.
6. Each optional feature in a separate change with its own acceptance test.

This is a multi-step rehabilitation rather than a dependency-only refresh. Actual effort depends on desired mods, number of concurrent servers, and hardware. No time estimate is warranted until Stage 1 exposes the real runtime behavior.
