# Publisher version candidates (not a tested lockfile)

Queried Modrinth's public API on 2026-09-27 with **Minecraft 1.20.1 + Forge** filters. These are the latest stable candidate releases returned for individually matched projects, not a jointly resolved dependency graph. Publisher side metadata is copied as reported and must be checked against exact JAR dependencies. No JARs were downloaded.

The [raw metadata snapshot](review-evidence/2026-09-27/modrinth-candidates.json) contains publisher file URLs, SHA-512/SHA-1 hashes and dependency IDs. Those hashes are not SHA-256 values for the local installer; download verification and an install inventory still need to be performed. Do not automatically install every search result: the snapshot also contains unrelated search hits, retained for auditability.

| Matched project | Candidate version | Modrinth version ID | Reported server side |
| --- | --- | --- | --- |
| [[Let's Do] API](https://modrinth.com/mod/do-api) | `1.2.15` | `uEaTMht9` | required |
| [[Let's Do] Farm & Charm](https://modrinth.com/mod/lets-do-farm-charm) | `1.0.14` | `9fzY3YV6` | required |
| [[Let's Do] Meadow](https://modrinth.com/mod/lets-do-meadow) | `1.3.25` | `phZQOZzG` | required |
| [Architectury API](https://modrinth.com/mod/architectury-api) | `9.2.14+forge` | `1MKTLiiG` | required |
| [Athena](https://modrinth.com/mod/athena-ctm) | `3.1.2` | `DULOQFj7` | unsupported |
| [Balm](https://modrinth.com/mod/balm) | `7.3.44+forge-1.20.1` | `dDN38ae7` | optional |
| [Beautify!](https://modrinth.com/mod/beautify) | `2.0.2` | `v9NnLuyB` | required |
| [Carry On](https://modrinth.com/mod/carry-on) | `2.1.2.7` | `edGQD16r` | required |
| [Chipped](https://modrinth.com/mod/chipped) | `3.0.7` | `pi3f4er3` | required |
| [Easy NPC](https://modrinth.com/mod/easy-npc) | `7.12.1` | `KWOV0VKY` | required |
| [Easy NPC: Config UI](https://modrinth.com/mod/easy-npc-config-ui) | `7.12.1` | `swcRILIX` | required |
| [Easy NPC: Core](https://modrinth.com/mod/easy-npc-core) | `7.12.1` | `b2koOKsW` | required |
| [Embeddium](https://modrinth.com/mod/embeddium) | `0.3.31+mc1.20.1` | `UTbfe5d1` | unsupported |
| [FerriteCore](https://modrinth.com/mod/ferrite-core) | `6.0.1` | `DG5Fn9Sz` | optional |
| [Geckolib](https://modrinth.com/mod/geckolib) | `4.8.4` | `aC5KMoNg` | optional |
| [Handcrafted](https://modrinth.com/mod/handcrafted) | `3.0.6` | `N7wZwOFy` | required |
| [Just Enough Items (JEI)](https://modrinth.com/mod/jei) | `15.56.0.205` | `9jqubC9n` | optional |
| [Legacy: [Let's Do] Bakery](https://modrinth.com/mod/lets-do-bakery) | `1.1.15` | `Jo8EwiDR` | required |
| [Macaw's Doors](https://modrinth.com/mod/macaws-doors) | `1.1.5` | `n8BlIUm3` | required |
| [Macaw's Fences and Walls](https://modrinth.com/mod/macaws-fences-and-walls) | `1.2.1` | `HnyfcyJ9` | required |
| [Macaw's Furniture](https://modrinth.com/mod/macaws-furniture) | `3.4.1` | `mvGf4LNK` | required |
| [Macaw's Roofs](https://modrinth.com/mod/macaws-roofs) | `2.3.2` | `31e80GhE` | required |
| [Macaw's Trapdoors](https://modrinth.com/mod/macaws-trapdoors) | `1.1.5` | `5B4awHaA` | required |
| [Macaw's Windows](https://modrinth.com/mod/macaws-windows) | `2.4.2` | `SSIlzrPf` | required |
| [MiguelEconomy](https://modrinth.com/mod/migueleconomy) | `1.1.4` | `YWgCwGim` | required |
| [MiguelEconomy X EasyNPC](https://modrinth.com/mod/migueleconomy-x-easynpc) | `0.1.0-1.20.1` | `4IUPLF0v` | required |
| [ModernFix](https://modrinth.com/mod/modernfix) | `5.27.83+mc1.20.1` | `jAZ7Ge3d` | optional |
| [Oculus](https://modrinth.com/mod/oculus) | `1.20.1-1.8.0` | `iQ1SwGc3` | unsupported |
| [Resourceful Lib](https://modrinth.com/mod/resourceful-lib) | `2.1.29` | `OhsHaCcW` | required |
| [Sophisticated Backpacks](https://modrinth.com/mod/sophisticated-backpacks) | `1.20.1-3.26.4.2172` | `u2NNJgIW` | required |
| [Sophisticated Core](https://modrinth.com/mod/sophisticated-core) | `1.20.1-1.5.2.2346` | `7LbBi96J` | required |
| [Waystones](https://modrinth.com/mod/waystones) | `14.1.21+forge-1.20.1` | `Y0IgdaoP` | required |
| [Waystones Teleport Pets](https://modrinth.com/mod/waystones-teleport-pets) | `1.2` | `Yh4b40rs` | required |
| [WorldEdit](https://modrinth.com/mod/worldedit) | `7.2.15` | `Wrlqaul6` | required |

AllTheLeaks is available from its [CurseForge publisher](https://www.curseforge.com/minecraft/mc-mods/alltheleaks), which currently lists `alltheleaks-1.1.3+1.20.1-forge.jar`. Farmer's Delight, the exact Jack's Fullbright project, and “Journeyman” still need canonical file selection; the fuzzy search results were not accepted as substitutes. The modpack export will also settle whether to preserve already-used versions instead of these newer candidates.

Athena is marked server-unsupported in project metadata while Chipped declares it as a dependency. Easy NPC has multiple matching modules. These are examples of why project-level side labels or choosing each newest file independently are not sufficient to validate this pack.
