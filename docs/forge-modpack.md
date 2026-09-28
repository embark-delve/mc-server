# Forge pack plan

Updated 2026-09-27. Target: **Minecraft Java Edition 1.20.1, Forge 47.4.23, Java 25**. This is a requested-content inventory, **not a resolved or tested modpack lockfile**. No listed third-party JAR has been downloaded or run as part of this change.

## Runtime decision

Minecraft 1.20.1 and Java 25 are different version schemes. Forge's official download page lists **47.4.23 for Minecraft 1.20.1**. The Forge 47.4.9 changelog explicitly added Java 25 runtime support. The repository therefore targets Java 25 as the newest runtime supported by the evidence checked here, with configurable Java 21/17 fallback only if exact mod testing requires it. This does not establish support for a newer Java major or for every mod on Java 25. [Forge downloads](https://files.minecraftforge.net/net/minecraftforge/forge/index_1.20.1.html), [Forge Java 25 change](https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.9/forge-1.20.1-47.4.9-changelog.txt).

Do not upgrade Minecraft independently of this pack. If a mod requires Java 17, first test that finding on a separate disposable profile; preserve the old world and its runtime together. The image digest is locked per profile on the first pull.

## Requested items

“Candidate” below means a proposed role to verify against exact artifact metadata, **not confirmed support or a download instruction**. Exact file IDs, versions, loader flags, dependency ranges and hashes are required for every entry. Content mods commonly also belong in the client pack; a server inventory alone cannot establish client compatibility.

| Requested item | Intended treatment / outstanding verification |
| --- | --- |
| [Let's Do] API | Server/client library candidate; match the legacy Let's Do versions that actually require it |
| [Let's Do] Farm & Charm | Server/client content candidate; resolve exact 1.20.1 Forge release and dependencies |
| [Let's Do] Meadow | Server/client world/content candidate; test against Farm & Charm and legacy Bakery |
| AllTheLeaks | Server optimization candidate; verify the exact Forge file and interaction with other fixes |
| Architectury API | Shared dependency candidate; choose Forge 1.20.1 artifact |
| Athena | Shared dependency candidate; confirm which Chipped release requires it |
| Balm | Shared dependency candidate; match Waystones dependencies |
| Beautify! | Server/client content candidate; exact project/file required |
| Carry On | Server/client gameplay candidate; verify configuration and permissions |
| Chipped | Server/client content candidate; resolve dependencies rather than adding guessed library versions |
| Easy NPC | Candidate NPC implementation; verify whether it is a bundle or separate modules at the selected version |
| Easy NPC: Config UI | Verify supported side and matching Easy NPC version; do not assume a UI module belongs on a dedicated server |
| Easy NPC: Core | Match Easy NPC/Config UI/integration versions; avoid duplicate bundled modules |
| Embeddium | **Client only**, omit from dedicated server; verified upstream |
| Farmer's Delight | Server/client content candidate; choose Forge build |
| FerriteCore (NeoForge) | Select an artifact explicitly compatible with **Forge 1.20.1**; the project offers multiple loaders, so “NeoForge” in the name is insufficient |
| Fulbright (Jack's Fulbright) | Intended client visual enhancement; exact project spelling and side metadata still required |
| GeckoLib | Shared dependency candidate; select required major/version for the actual consuming mods |
| Handcrafted | Server/client content candidate; verify Resourceful Lib requirement |
| Journeyman | **Ambiguous name**; do not substitute JourneyMap without confirmation/export |
| Just Enough Items (JEI) | Client UI candidate; determine whether any chosen integrations need its optional server components |
| Legacy: [Let's Do] Bakery | Preserve the requested **legacy** project/version line, not a similarly named replacement |
| Macaw's Doors | Listed twice with different capitalization; retain one exact artifact |
| Macaw's Fences and Walls | Server/client content candidate |
| Macaw's Furniture | Server/client content candidate |
| Macaw's Roofs | Server/client content candidate |
| Macaw's Trapdoors | Server/client content candidate |
| Macaw's Windows | Server/client content candidate |
| MiguelEconomy | Exact Forge 1.20.1 release required; do not substitute MiguelEconomy MAX |
| MiguelEconomy X EasyNPC | Exact addon, economy and NPC compatibility ranges required |
| ModernFix | Server optimization candidate; test jointly with AllTheLeaks and FerriteCore |
| Oculus | **Client only**, omit from dedicated server; verified upstream |
| Resourceful Lib | Shared dependency candidate; match dependants' exact constraints |
| Sophisticated Backpacks | Server/client content candidate; match Sophisticated Core |
| Sophisticated Core | Shared dependency candidate; exact matching release required |
| Waystones | Server/client gameplay candidate; resolve Balm version |
| Waystones Teleport Pets | Addon candidate; confirm exact Waystones dependency/version |
| WorldEdit | Use the **Forge mod**, not the Paper/Bukkit plugin; review operator permissions |
| “motschen netter leaves” resource pack | Likely Motschen's Better Leaves; confirm exact pack. Client resource pack, not a server JAR |
| Complementary Shaders – Reimagined | Client shader pack; validate with the chosen Oculus/client renderer and this laptop's GPU |

Confirmed side/identity sources: [Embeddium](https://modrinth.com/mod/embeddium), [Oculus](https://modrinth.com/mod/oculus), [FerriteCore](https://modrinth.com/mod/ferrite-core), [MiguelEconomy](https://www.curseforge.com/minecraft/mc-mods/migueleconomy), [MiguelEconomy X EasyNPC](https://www.curseforge.com/minecraft/mc-mods/migueleconomy-x-easynpc). Other rows intentionally remain candidates pending the actual pack export.

## Publisher metadata collected

A concrete [candidate-version table](modpack-candidates.md) and publisher metadata/hashes have now been saved. These narrow the choices but are not a tested dependency lock or a set of installed mods.

## Needed to finish the pack

Provide a CurseForge/Modrinth export, a pack link, or exact project/file links. Display names alone cannot safely choose between Forge, NeoForge, Fabric, different Minecraft versions, legacy forks and client-only modules. An export supplies IDs and file versions, but still requires server-side filtering, dependency resolution and a launch test.

The next pack workflow is:

1. Resolve each selected file to its canonical project, version, loader, game version and server/client metadata. Deduplicate Macaw's Doors and check Easy NPC's packaging.
2. Produce separate server and client inventories, including all transitive dependencies. Record file URL/ID, SHA-256, source, license/redistribution constraints and dependency versions. Do not invent hashes or mirror non-redistributable files.
3. Download from the actual publishers, verify hashes, and install server JARs only into a disposable profile using the supported local installer. It never treats mock bytes as a successful install.
4. Start Forge on Java 25, inspect missing dependencies, side errors, mixin failures and crash reports, and adjust exact versions deliberately. If runtime compatibility forces an older Java, document the evidence.
5. Join with the matched client pack; test new world generation, all dimensions, NPC/economy interactions, backpacks, teleporting pets, WorldEdit privileges, saves, restart and restore. Check heap/CPU under normal gameplay; shader performance is a separate client test.
6. Commit the resolved metadata/lockfile and test record, not private credentials or a bundle of third-party JARs.

Until these steps are complete, the project is **Forge-configured**, not “the entire pack installed and validated.”
