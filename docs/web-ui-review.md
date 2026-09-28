# Management UI review and changes

## Problems corrected

- Stop and mod inventory existed but were hidden under an ambiguous “World care” section.
- The admin password form was outside the page panels, so even its collapsed heading appeared on every page.
- The dashboard did not offer restart or server logs.
- Join information incorrectly hard-coded localhost after the game was moved to the LAN binding.

## Current navigation

| Page | Available controls |
| --- | --- |
| Server | Health/access status, first-time setup, Start server, Save & stop, Restart |
| Mods | Installed filenames/versions, installed/enabled counts, search, enabled/disabled switches |
| Players | Allow by Minecraft username, ban/unban, remove/restore access |
| Backups | Create stopped-world backup, list recent backups and sizes |
| Logs | Read/refresh the latest 100 Minecraft log lines |
| Join | Minecraft/Forge requirements, configured local/LAN address, copy address, remote-forwarding explanation |
| Settings | Collapsed admin password change/recovery form only |

Stop/restart require explicit confirmation and save through the existing backend. Mod switches are unavailable while running; the page explains why. Backup creation also requires a stopped world. New JAR installation and backup restore remain CLI operations; they are not claimed as web features. The website has no general command console or arbitrary file editor.

## Validation

Browser checks on the live dashboard confirmed that the stop confirmation opens and cancels without stopping the game; all 13 enabled mods appear; searching Waystones filters the list; Settings alone contains the collapsed password form; logs load; and backups are listed with creation disabled while running. Backend tests exercise restart authorization/profile confirmation and invocation, bounded/admin-only log reads, sanitized backend failures, and password recovery/session invalidation. Python typing, Ruff, Bandit, ESLint and Prettier checks pass.

The management service was restarted to load the new endpoints. Minecraft was not stopped during this UI review. Existing web sessions may require a fresh sign-in after a management-service restart; the stored admin password is unchanged.
