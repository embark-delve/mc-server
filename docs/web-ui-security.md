# Local dashboard and Minecraft access security

Updated 2026-09-27. The final scope is one admin and no player website accounts; see [admin and players](accounts-and-invitations.md).

## What runs where

Minecraft/Forge runs in an `itzg/minecraft-server` Docker container. The Python CLI and the new Starlette/Uvicorn dashboard run on the laptop and use the existing scoped Docker backend. The browser never receives Docker credentials or socket access. The repository's Dockerfile is a CLI inspection image, not a deployment for the web manager. **Minecraft is containerized; the manager runs locally. The base Forge server has now started and passed its live access-configuration check; see launch-progress.md for current evidence.**

Do not mount the Docker socket into a general-purpose web application to make this “all Docker.” Docker control carries extensive host privileges. A future fully containerized control plane needs a separately reviewed broker with a narrow API, authenticated communication, fixed profile mapping, and explicit socket privileges. Merely mounting the socket read-only does not make Docker API operations read-only.

## Game access

The generated Compose configuration forces ONLINE_MODE, ENFORCE_SECURE_PROFILE, ENABLE_WHITELIST and ENFORCE_WHITELIST to true. Initialization/start require a nonempty approved username list. The whitelist is synchronized from configuration. Only the game port is published, on 127.0.0.1 by default; RCON stays unpublished and uses a private random secret file. Public binds require explicit LAN configuration, which remains off.

Minecraft online mode authenticates a player's Minecraft session. The allowlist separately authorizes which authenticated identities can enter. A valid paid account alone is not an invitation. This is not a shared game password, and a web dashboard link does not grant game access. Do not disable online mode for offline launchers, disable the whitelist, give operator privileges to unapproved accounts, forward the port on a router, or expose RCON.

`minecraft-server security` checks a **running** owned container:

- Actual published game address/port matches the approved configuration; no other ports are published.
- Generated server.properties requires online mode, whitelist, whitelist enforcement, and secure profiles.
- The live whitelist names exactly match the configured nonempty list.
- Every operator is also on the approved list, because operators can bypass the whitelist.
- Secrets read during inspection are never included in the result.

The UI uses this check before displaying “Ready to explore.” A failed check is prominently reported; it does not automatically kill a running game or disconnect users. Stop the world and investigate. This check is a snapshot of effective files and port bindings, not an active login challenge, continuous firewall, or proof that a malicious mod cannot bypass authentication. Do not edit these files while running. An actual allowed-account join and non-allowlisted-account rejection remain required acceptance tests.

## Dashboard access

The final MVP has one admin and no player website accounts. See [admin and players](accounts-and-invitations.md) for setup, login, and access-management commands. No age or grown-up role gates setup.

Launch with `uv run --locked minecraft-server web`. The bind address is fixed to 127.0.0.1. The CLI prints a temporary random owner link for initial setup/recovery; normal sign-in uses the single local admin password. Login issues an eight-hour random bearer session. Tokens are kept in per-tab session storage and sent as Authorization headers. The owner token arrives in a URL fragment removed from the address bar, and expires when the manager exits. No Microsoft credentials are requested.

All management API routes authenticate. Login is public, rate-limited and request-size bounded. Mutations require the exact local Origin and POST; lifecycle/player changes use fixed operations, with explicit profile confirmation where appropriate. No permissive CORS is enabled. Host validation resists DNS rebinding. Proxy headers are disabled. Security headers prevent framing, sniffing, caching and referrer leakage; a restrictive CSP allows only local scripts/assets. Dynamic data is inserted as text.

The web setup form requires explicit EULA acceptance and only prepares this configured profile with an approved Minecraft username. Player controls add/ban/unban/remove exact names; they cannot issue arbitrary console commands. No file upload, arbitrary console, restore, config editor or Docker API is exposed. World lifecycle operations serialize, and backend locks prevent overlapping profile mutations. Game access synchronization is verified; failures are reported rather than hidden.

Local HTTP is suitable only for the loopback design. Do not expose it through a public/LAN reverse proxy. Remote access, TLS and device management are outside the MVP. Anyone who can access the owner's OS account, terminal, profile files or Docker daemon is outside the dashboard's isolation boundary.

## Remaining security work before routine play

Install/update Docker Desktop from the vendor, verify a working engine, obtain EULA acceptance and exact usernames, pin/review the full modpack, run live lifecycle and admission tests, scan the selected container image, and rehearse restoration. Keep OS/Docker patched, keep offline backups, avoid untrusted mod JARs, and review pinned image updates deliberately. Unit tests and dependency audits are evidence with limits, not a security certification.

## Primary references

- [Docker daemon attack surface](https://docs.docker.com/engine/security/#docker-daemon-attack-surface)
- [Protect the Docker daemon socket](https://docs.docker.com/engine/security/protect-access/)
- [Docker security announcements](https://docs.docker.com/security/security-announcements/)
- [Minecraft image server properties and RCON secret files](https://docker-minecraft-server.readthedocs.io/en/latest/configuration/server-properties/)
- [Starlette Host middleware](https://www.starlette.io/middleware/)
