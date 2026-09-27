# Management MVP

Updated 2026-09-27 to reflect the user's corrected scope.

One server admin, no player website accounts, no website invitations, and no child/adult role split. The admin can be the person setting up the server, including a child using the family laptop. Setup is available directly in both the CLI and web UI; it does not instruct the user to wait for a grown-up.

The local “Block & Bloom” dashboard contains:

- A setup form: Minecraft username, explicit EULA acceptance, safe preselected Forge settings.
- World status, start, graceful stop, stopped-world backup, joining instructions and address copying.
- A Players page: add a Minecraft username to the allowlist, ban, unban, remove, and re-add. No website credentials for players.
- One admin login, with a local owner bootstrap link for first setup and recovery.

The original block-island SVG, local fonts/assets, reduced-motion support, native forms/dialogs, keyboard focus, responsive layout, and plain language provide a welcoming interface without expanding the product into a social/account platform. The UI reports actual setup/health/access-check states rather than invented activity.

MVP launch order: working Docker → explicit EULA acceptance and allowed username → base Forge lifecycle and access verification → approved client/server modpack → real allowed-account join and unapproved-account rejection. The exact modpack is a compatibility deliverable, not a reason to add unrelated management features.

Outside MVP: player website accounts, invitation delivery, role management, public dashboard hosting, multiple-world dashboard, web restore, console/file browser, automatic unreviewed mod downloads. The existing CLI restore remains available with explicit safeguards.

## MVP mod controls

Installed server mods are enabled by default. Each installed JAR has a switch in World care. Changes require a stopped server, authentication and a confirmation. Disabled files move atomically into `data/disabled-mods`, remain in backups and can be re-enabled without redownloading. No live hot-loading or automatic dependency changes: users must keep required dependencies enabled and should back up before removing content mods. Client-only mods, resource packs and shaders do not belong in the server's enabled-mod list.

CLI equivalents: `minecraft-server mods-disable example.jar` and `minecraft-server mods-enable example.jar`.
