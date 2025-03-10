# Minecraft Mods and Plugins Guide

This guide explains how to use and manage mods and plugins with the Minecraft Server Manager, including the differences between them, recommended options for different purposes, and installation guides.

## Understanding Mods vs. Plugins

### What are Mods?

**Mods** (modifications) directly change the Minecraft game code to add new features, items, blocks, mechanics, or completely transform gameplay. They typically require:

- A modding platform like Forge or Fabric
- Installation on both the server AND client
- More system resources

**Examples**: Thaumcraft, Create, Twilight Forest, Botania

### What are Plugins?

**Plugins** extend the server functionality without requiring client-side modifications. They:

- Only need to be installed on the server
- Work with vanilla clients (players don't need to install anything)
- Run on server platforms like Bukkit, Spigot, and Paper

**Examples**: WorldEdit, Essentials, GriefPrevention, LuckPerms

## Mod and Plugin Management

The Minecraft Server Manager provides tools to easily install, manage, and update both mods and plugins.

### Using the Command Line Interface

```bash
# List installed mods/plugins
python minecraft-server.py console list-mods

# Install a mod (Fabric/Forge) or plugin (Paper/Spigot)
python minecraft-server.py console install-mod <mod_id> --source <source>

# Uninstall a mod/plugin
python minecraft-server.py console uninstall-mod <mod_id>
```

### Using the Python API

```python
from src.minecraft_server_manager import MinecraftServerManager

manager = MinecraftServerManager(server_type="paper")

# List installed mods/plugins
mods = manager.list_mods()

# Install a mod or plugin
manager.install_mod("worldedit", source="bukkit")

# Uninstall a mod or plugin
manager.uninstall_mod("worldedit")
```

## Recommended Mods and Plugins

### Essential Server Plugins (Paper/Spigot)

| Plugin Name         | Purpose                     | Installation Command                          |
| ------------------- | --------------------------- | --------------------------------------------- |
| **Essentials**      | Core commands and utilities | `install-mod essentials --source bukkit`      |
| **WorldEdit**       | In-game world editing       | `install-mod worldedit --source bukkit`       |
| **LuckPerms**       | Permissions management      | `install-mod luckperms --source bukkit`       |
| **Vault**           | Economy API for plugins     | `install-mod vault --source bukkit`           |
| **CoreProtect**     | Anti-grief and rollback     | `install-mod coreprotect --source bukkit`     |
| **GriefPrevention** | Claim protection            | `install-mod griefprevention --source bukkit` |

### Performance Optimization

#### For Paper/Spigot Servers

| Plugin Name              | Purpose                 | Installation Command                    |
| ------------------------ | ----------------------- | --------------------------------------- |
| **Spark**                | Performance profiling   | `install-mod spark --source bukkit`     |
| **ClearLagg**            | Entity and item cleanup | `install-mod clearlagg --source bukkit` |
| **Fast Async WorldEdit** | Faster world editing    | `install-mod fawe --source bukkit`      |

#### For Fabric Servers

| Mod Name        | Purpose                   | Installation Command                         |
| --------------- | ------------------------- | -------------------------------------------- |
| **Lithium**     | General performance       | `install-mod lithium --source modrinth`      |
| **Starlight**   | Light engine optimization | `install-mod starlight --source modrinth`    |
| **FerriteCore** | Memory usage reduction    | `install-mod ferrite-core --source modrinth` |
| **LazyDFU**     | Faster startup            | `install-mod lazydfu --source modrinth`      |

#### For Forge Servers

| Mod Name            | Purpose               | Installation Command                              |
| ------------------- | --------------------- | ------------------------------------------------- |
| **AI Improvements** | Mob AI optimization   | `install-mod ai-improvements --source curseforge` |
| **Clumps**          | XP orb optimization   | `install-mod clumps --source curseforge`          |
| **FastWorkbench**   | Crafting optimization | `install-mod fastworkbench --source curseforge`   |
| **FerriteCore**     | Memory optimization   | `install-mod ferritecore --source curseforge`     |

### Admin Tools

| Plugin Name       | Purpose                   | Installation Command                          |
| ----------------- | ------------------------- | --------------------------------------------- |
| **Multiverse**    | Multiple world management | `install-mod multiverse-core --source bukkit` |
| **EssentialsX**   | Admin commands            | `install-mod essentialsx --source bukkit`     |
| **Dynmap**        | Live web map              | `install-mod dynmap --source bukkit`          |
| **PermissionsEx** | Permissions management    | `install-mod permissionsex --source bukkit`   |

### Gameplay Enhancements

| Plugin/Mod Name      | Purpose               | Installation Command                              | Type      |
| -------------------- | --------------------- | ------------------------------------------------- | --------- |
| **McMMO**            | RPG skills            | `install-mod mcmmo --source bukkit`               | Plugin    |
| **BetterSleeping**   | Improved sleep        | `install-mod bettersleeping --source bukkit`      | Plugin    |
| **Create**           | Mechanical automation | `install-mod create --source curseforge`          | Forge Mod |
| **Biomes O' Plenty** | Additional biomes     | `install-mod biomes-o-plenty --source curseforge` | Forge Mod |

## Installation Guides

### Installing Bukkit/Spigot Plugins

1. **Automatic Installation (Recommended)**:

   ```bash
   python minecraft-server.py console install-mod worldedit --source bukkit
   ```

2. **Manual Installation**:
   - Download the plugin JAR file from a trusted source
   - Place it in the `plugins/` directory
   - Restart the server

### Installing Forge Mods

1. **Automatic Installation**:

   ```bash
   python minecraft-server.py console install-mod create --source curseforge
   ```

2. **Manual Installation**:
   - Download the mod JAR file from a trusted source
   - Place it in the `mods/` directory
   - Restart the server
   - Ensure players have the same mod installed

### Installing Fabric Mods

1. **Automatic Installation**:

   ```bash
   python minecraft-server.py console install-mod lithium --source modrinth
   ```

2. **Manual Installation**:
   - Download the mod JAR file from a trusted source
   - Place it in the `mods/` directory
   - Restart the server
   - Ensure players have the same mod installed (if required)

## Supported Mod Sources

The Minecraft Server Manager supports multiple sources for mods and plugins:

| Source            | Type    | Command Parameter     |
| ----------------- | ------- | --------------------- |
| **Modrinth**      | Mods    | `--source modrinth`   |
| **CurseForge**    | Mods    | `--source curseforge` |
| **Bukkit/Spigot** | Plugins | `--source bukkit`     |
| **GitHub**        | Both    | `--source github`     |
| **Jenkins**       | Both    | `--source jenkins`    |

## Creating Modpacks

For creating custom modpacks, follow these steps:

1. Install the base server type (Forge or Fabric)

   ```bash
   python minecraft-server.py --type forge --version 1.18.2 start
   ```

2. Install mods one by one:

   ```bash
   python minecraft-server.py console install-mod create --source curseforge
   python minecraft-server.py console install-mod jei --source curseforge
   ```

3. Configure mods as needed in their respective config files

4. Export the modpack for players:
   - Share the list of mods and their versions
   - Consider using a dedicated launcher like CurseForge or MultiMC

## Plugin Configuration

Most plugins create their config files in the `plugins/<plugin_name>/` directory. After installing a plugin:

1. Start the server to generate default config files
2. Stop the server
3. Edit the configuration files as needed
4. Restart the server to apply changes

Example configuration directory structure:

```
plugins/
  ├── Essentials/
  │   ├── config.yml
  │   └── userdata/
  ├── LuckPerms/
  │   ├── config.yml
  │   └── users/
  ├── WorldEdit/
  │   └── config.yml
  ├── Essentials.jar
  ├── LuckPerms.jar
  └── WorldEdit.jar
```

## Common Issues and Solutions

### Mod Compatibility

**Problem**: Mods are incompatible with each other.

**Solution**:

1. Check for specific incompatibilities in mod documentation
2. Try removing mods one by one to identify conflicts
3. Look for compatibility patches or alternatives

### Plugin Conflicts

**Problem**: Plugins are conflicting with each other.

**Solution**:

1. Check for plugins that modify the same functionality
2. Update to the latest versions
3. Check plugin configuration for conflict resolution options

### Client-Side Requirements

**Problem**: Players can't see mod content.

**Solution**:

1. Ensure players have the same mods installed
2. Provide a modpack or installer for players
3. Verify mod versions match between server and client

### Performance Issues

**Problem**: Server lags after installing mods/plugins.

**Solution**:

1. Check server performance with profiling tools
2. Remove resource-intensive mods/plugins
3. Increase server memory allocation
4. Add performance optimization mods

## Updating Mods and Plugins

To update mods and plugins:

```bash
# Update a specific mod/plugin
python minecraft-server.py console update-mod worldedit

# List outdated mods/plugins
python minecraft-server.py console list-mods --outdated
```

Always back up your server before updating mods or plugins, as updates may cause compatibility issues or data changes.

## Further Resources

- [Bukkit Plugin Directory](https://dev.bukkit.org/bukkit-plugins)
- [Spigot Resource Page](https://www.spigotmc.org/resources/)
- [Modrinth](https://modrinth.com/)
- [CurseForge Minecraft Mods](https://www.curseforge.com/minecraft/mc-mods)
- [Fabric Mod Database](https://fabricmc.net/wiki/tutorial:mod_list)
