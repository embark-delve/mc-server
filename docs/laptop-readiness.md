> **Baseline review (df94b16).** Subsequent repairs are tracked in [implementation status](implementation-status.md); use the [current README](../README.md) for commands.

# Laptop readiness review

Reviewed **2026-09-27**, against commit **df94b16** (2025-03-10). This assessment describes the existing code; it does not implement the fixes or certify a live server.

## Verdict

**Do not use the current manager with a world you care about yet.** The project is a useful prototype around the `itzg/minecraft-server` image, but the advertised quick start fails before reaching Docker, default monitoring raises an exception, and restore can delete world data. Mod installation writes mock content rather than real JAR files.

The shortest route to reliable laptop use is to finish **one local Docker backend**, with one explicitly selected Minecraft version and safe persistence. Keep AWS and Kubernetes out of the first release. A web dashboard, automatic mod downloads, and Prometheus are optional; dependable startup, shutdown, backups, configuration, and resource limits are not.

## Read the review

- [Findings and evidence](review-findings.md): security, correctness, maintenance, and incomplete features, with source locations and proposed fixes.
- [Prioritized implementation plan](laptop-roadmap.md): ordered work packages and acceptance criteria, including multiple servers.
- [Laptop operating guide](laptop-runbook.md): recommended operating model and validation steps **after the blockers are fixed**.
- [Validation record](review-validation.md): executed checks, results, limitations, and saved logs.

## What must happen first

| Priority | Work | Why it matters |
| --- | --- | --- |
| P0 | Rewrite restore to stage and validate before replacing data | A disposable restore reproduction deleted the world file and returned failure |
| P0 | Separate deployment backend from Minecraft flavor; wire configuration end to end | The committed sample selects unsupported backend `PAPER`; memory and monitoring settings are ignored by the CLI |
| P0 | Remove duplicate monitoring initialization; default optional services off | Default construction raises a duplicate Prometheus metrics exception |
| P0 | Make backup consistency, server readiness, and graceful stop explicit | Running containers are reported as ready; running worlds are zipped without coordinating saves |
| P0 | Use local-only networking, private RCON credentials, explicit authentication settings, and resource budgets | Current game port binds all host interfaces, RCON has a fixed password, and no container resource limits are generated |
| P0 | Select and pin a compatible Minecraft/Paper build and Java image | `latest` with `java21` is no longer a safe pairing |
| P1 | Repair installation, dependency management, tests, and CI | The built wheel omits subpackages and points its command at a nonexistent module |
| P1 | Add named server profiles, ports, and separate storage | Current defaults permit only one predictable instance and can target an unrelated container with the same name |
| P1/P2 | Disable unfinished features, then add them individually | Mock mods and ephemeral monitoring/idle management create misleading promises |

P0 means a gate before trusting valuable worlds; P1 means needed for a maintainable daily-use release or the relevant feature; P2 means optional follow-up. An unused unsafe feature can be explicitly disabled rather than fully implemented for the first release.

## What exists versus what works

| Capability | Assessment |
| --- | --- |
| Java Edition via Docker | Real implementation, blocked by configuration and monitoring defects |
| Start / stop / restart / console | Real Docker commands, but lifecycle and failure reporting need repair |
| Backups | ZIP creation exists; consistency, full coverage, retention wiring, and recovery are incomplete |
| Restore | Unsafe; do not use on real data |
| Memory configuration | Parsed by CLI but not passed through; documented constructor argument also fails |
| Mods/plugins | Mock downloads; install/uninstall metadata disagree |
| Monitoring | Duplicate registrations, no Docker collector startup, inconsistent metric names |
| Idle management | Short-lived Python daemon thread plus a separate container autopause mechanism; not reliable automatic shutdown |
| Multiple local servers | Not a complete supported workflow; names, host ports, storage, and metrics conflict |
| AWS | Partial, inconsistent with Terraform provisioning; not needed locally |
| Kubernetes | Standalone manifest/script, not an implemented Python backend |
| Bedrock Edition | No implemented backend or crossplay setup; assume Java Edition for this plan |

## Current compatibility and laptop assumptions

The inspected machine reports **macOS arm64** and **Python 3.13.0**. Docker was not found on the command search path; that does not prove Docker Desktop is absent from the machine. RAM, free disk budget, desired player count, Minecraft edition, and preferred modpack remain unverified. The plan assumes a small private Java Edition server, initially accessible only from this laptop.

Paper's current documentation lists **Java 25 for 26.1+**, and Java 21 for its 1.20–1.21.11 range. Select the exact server release first; do not mechanically change every old world to a new version. The image project provides arm64 Java 25 and Java 21 variants and versioned image releases. Pin the image release/digest and server build, then test upgrades on a restored copy. [Paper requirements](https://docs.papermc.io/paper/getting-started/), [image Java versions](https://docker-minecraft-server.readthedocs.io/en/latest/versions/java/).

Use a maintained Python version and test it explicitly. Python 3.8 and 3.9 are end-of-life, despite appearing in this project's CI matrix. Python 3.13 is a reasonable initial target; update its patch release before establishing the supported development environment. [Python version status](https://devguide.python.org/versions/).

## Definition of ready

The project is ready for your first valuable world only when a clean installation can start a disposable server, wait for actual Minecraft readiness, accept a client connection, preserve a placed block across stop/start, produce a stopped-server backup, restore that backup into a separate profile, and repeat these steps without accessing another profile's files or ports. Invalid configuration, unavailable Docker, failed shutdown, and corrupt backups must fail clearly without deleting data. See the [roadmap](laptop-roadmap.md) for the full acceptance checklist.
