# Installed Forge 1.20.1 mods

Installed 2026-09-27 on the live Forge 47.4.23 / Java 25 profile. These files were selected from publisher metadata explicitly listing **Forge** and **Minecraft 1.20.1**, downloaded over HTTPS, and checked against publisher SHA-512 hashes before the local SHA-256-verified installer copied them. All installed mods are enabled.

| Mod | Version | File |
| --- | --- | --- |
| [Easy NPC](https://modrinth.com/mod/easy-npc/version/KWOV0VKY) | `7.12.1` | `easy_npc_bundle-forge-1.20.1-7.12.1.jar` |
| [Easy NPC: Config UI](https://modrinth.com/mod/easy-npc-config-ui/version/swcRILIX) | `7.12.1` | `easy_npc_config_ui-forge-1.20.1-7.12.1.jar` |
| [Easy NPC: Core](https://modrinth.com/mod/easy-npc-core/version/b2koOKsW) | `7.12.1` | `easy_npc-forge-1.20.1-7.12.1.jar` |
| [Farmer's Delight](https://modrinth.com/mod/farmers-delight/version/SiIpcZzM) | `1.20.1-1.3.4` | `FarmersDelight-1.20.1-1.3.4.jar` |
| [Carry On](https://modrinth.com/mod/carry-on/version/edGQD16r) | `2.1.2.7` | `carryon-forge-1.20.1-2.1.2.7.jar` |
| [Sophisticated Backpacks](https://modrinth.com/mod/sophisticated-backpacks/version/u2NNJgIW) | `1.20.1-3.26.4.2172` | `sophisticatedbackpacks-1.20.1-3.26.4.2172.jar` |
| [Sophisticated Core](https://modrinth.com/mod/sophisticated-core/version/7LbBi96J) | `1.20.1-1.5.2.2346` | `sophisticatedcore-1.20.1-1.5.2.2346.jar` |
| [Chipped](https://modrinth.com/mod/chipped/version/pi3f4er3) | `3.0.7` | `chipped-forge-1.20.1-3.0.7.jar` |
| [Resourceful Lib](https://modrinth.com/mod/resourceful-lib/version/OhsHaCcW) | `2.1.29` | `resourcefullib-forge-1.20.1-2.1.29.jar` |
| [MiguelEconomy](https://modrinth.com/mod/migueleconomy/version/YWgCwGim) | `1.1.4` | `migueleconomy-1.1.4.jar` |
| [MiguelEconomy X EasyNPC](https://modrinth.com/mod/migueleconomy-x-easynpc/version/4IUPLF0v) | `0.1.0-1.20.1` | `migueleconomy_easynpc-0.1.0-1.20.1.jar` |
| [Waystones](https://modrinth.com/mod/waystones/version/Y0IgdaoP) | `14.1.21+forge-1.20.1` | `waystones-forge-1.20.1-14.1.21.jar` |
| [Balm](https://modrinth.com/mod/balm/version/dDN38ae7) | `7.3.44+forge-1.20.1` | `balm-forge-1.20.1-7.3.44.jar` |

## Dependencies and validation

- Easy NPC requires its matching Core and Config UI modules; all three use 7.12.1.
- Chipped requires Resourceful Lib on the server. Its Athena dependency is declared CLIENT-only in mods.toml and was deliberately not installed on the dedicated server.
- Waystones requires Balm; Sophisticated Backpacks requires Sophisticated Core.
- A stopped-world backup was created before installation. The initial modded startup reached healthy status and passed the live authentication/allowlist/port checks.
- Sophisticated Core emitted config-watcher parsing errors during initial default-file generation. The resulting file parses as valid TOML. A second clean restart reached healthy status with zero ERROR/FATAL/config-parsing entries and passed live security verification again.
- This is the requested missing-mod subset plus dependencies, not the complete earlier wishlist. Exact client files were not supplied; clients should match this version list before joining. Healthy startup does not prove NPC/economy gameplay or a matching Forge handshake.

## Admin login investigation

The existing `owner` admin record is present. No password was read, logged or reset. Server logs showed no web exception. Invalid credentials produced the expected rejection in the live browser. Successful password login and an authenticated dashboard were verified in a disposable browser profile, and the opt-in real HTTP CLI/login test passed. The real dashboard was reopened using the existing private local owner link, restoring management access without changing the password. The reported live-account password failure has not yet been reproduced; the exact error is still needed. If the password is unknown, reset locally with `uv run minecraft-server admin owner` (15–128 characters), then reload http://127.0.0.1:8765/ and sign in as `owner`.
