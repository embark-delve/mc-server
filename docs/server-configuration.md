# Minecraft Server Configuration Guide

This document provides a comprehensive reference for configuring your Minecraft server using the Minecraft Server Manager. Whether you're running a simple vanilla server or a complex modded setup, this guide will help you understand all available configuration options.

## Configuration Methods

You can configure your Minecraft server in several ways:

1. **Command-line Arguments**: Directly when launching the server

   ```bash
   python minecraft-server.py --memory 4G --version 1.20.1 start
   ```

2. **Environment Variables**: Set in the `.env` file or in the Docker Compose file

   ```
   MINECRAFT_VERSION=1.20.1
   MEMORY=4G
   ```

3. **Docker Compose File**: Modify `docker-compose.yml` directly

   ```yaml
   environment:
     VERSION: "1.20.1"
     MEMORY: "4G"
   ```

4. **Server Configuration API**: Through code
   ```python
   manager.update_server_configuration(
       memory="4G",
       minecraft_version="1.20.1"
   )
   ```

## Core Server Settings

### Basic Server Configuration

| Parameter     | Description               | Default            | Example                              |
| ------------- | ------------------------- | ------------------ | ------------------------------------ |
| `VERSION`     | Minecraft server version  | `latest`           | `1.20.1`                             |
| `TYPE`        | Server flavor             | `PAPER`            | `VANILLA`, `SPIGOT`, `FORGE`         |
| `MEMORY`      | Memory allocation         | `2G`               | `4G`, `8G`                           |
| `MOTD`        | Server message of the day | `Minecraft Server` | `Welcome to my server!`              |
| `DIFFICULTY`  | Game difficulty           | `normal`           | `peaceful`, `easy`, `normal`, `hard` |
| `MODE`        | Game mode                 | `survival`         | `creative`, `adventure`, `spectator` |
| `HARDCORE`    | Enable hardcore mode      | `false`            | `true`                               |
| `PVP`         | Enable player vs. player  | `true`             | `false`                              |
| `ONLINE_MODE` | Verify player identity    | `true`             | `false`                              |
| `MAX_PLAYERS` | Maximum player limit      | `20`               | `100`                                |

### World Settings

| Parameter             | Description                   | Default   | Example                            |
| --------------------- | ----------------------------- | --------- | ---------------------------------- |
| `LEVEL`               | World name                    | `world`   | `myworld`                          |
| `LEVEL_TYPE`          | World generation type         | `default` | `flat`, `amplified`, `largebiomes` |
| `SEED`                | World generation seed         | Random    | `12345`                            |
| `GENERATE_STRUCTURES` | Generate structures           | `true`    | `false`                            |
| `SPAWN_PROTECTION`    | Protected blocks around spawn | `16`      | `0` (disabled)                     |
| `VIEW_DISTANCE`       | Chunk view distance           | `10`      | `16`                               |
| `SIMULATION_DISTANCE` | Entity simulation distance    | `10`      | `8`                                |
| `SPAWN_ANIMALS`       | Enable animal spawning        | `true`    | `false`                            |
| `SPAWN_MONSTERS`      | Enable monster spawning       | `true`    | `false`                            |
| `SPAWN_NPCS`          | Enable NPC spawning           | `true`    | `false`                            |

### Performance Settings

| Parameter             | Description                   | Default          | Example                                 |
| --------------------- | ----------------------------- | ---------------- | --------------------------------------- |
| `USE_AIKAR_FLAGS`     | Use optimized JVM flags       | `true`           | `false`                                 |
| `JVM_XX_OPTS`         | Custom JVM flags              | See below        | `-XX:+UseG1GC -XX:MaxGCPauseMillis=200` |
| `NETWORK_COMPRESSION` | Network compression threshold | `256`            | `512`                                   |
| `MAX_TICK_TIME`       | Max milliseconds per tick     | `60000`          | `-1` (disabled)                         |
| `MAX_MEMORY`          | Maximum memory allocation     | Same as `MEMORY` | `4G`                                    |
| `INIT_MEMORY`         | Initial memory allocation     | Same as `MEMORY` | `2G`                                    |

Default JVM flags when `USE_AIKAR_FLAGS` is true:

```
-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1
```

### Security Settings

| Parameter           | Description           | Default     | Example           |
| ------------------- | --------------------- | ----------- | ----------------- |
| `OPS`               | Server operators      | None        | `user1,user2`     |
| `WHITELIST`         | Whitelisted players   | None        | `player1,player2` |
| `ENFORCE_WHITELIST` | Enforce whitelist     | `false`     | `true`            |
| `ENABLE_RCON`       | Enable remote console | `true`      | `false`           |
| `RCON_PASSWORD`     | RCON password         | `minecraft` | `your_password`   |
| `RCON_PORT`         | RCON port             | `25575`     | `25580`           |
| `ENABLE_QUERY`      | Enable server query   | `false`     | `true`            |
| `QUERY_PORT`        | Query port            | `25565`     | `25566`           |

### Auto-Shutdown Configuration

| Parameter               | Description                           | Default    | Example    |
| ----------------------- | ------------------------------------- | ---------- | ---------- |
| `ENABLE_AUTOPAUSE`      | Enable auto-shutdown                  | `true`     | `false`    |
| `AUTOPAUSE_TIMEOUT_EST` | Minutes of inactivity before shutdown | `120` (2h) | `240` (4h) |

## Server Type Specific Settings

### Paper/Spigot Settings

| Parameter                      | Description                | Default      | Example                                                                                              |
| ------------------------------ | -------------------------- | ------------ | ---------------------------------------------------------------------------------------------------- |
| `PAPER_DOWNLOAD_URL`           | Custom Paper download URL  | Official URL | `https://papermc.io/api/v2/projects/paper/versions/1.18.2/builds/388/downloads/paper-1.18.2-388.jar` |
| `SPIGOT_DOWNLOAD_URL`          | Custom Spigot download URL | Official URL | URL to custom build                                                                                  |
| `PAPER_DISABLE_UPDATE_SCANNER` | Disable update scanning    | `false`      | `true`                                                                                               |
| `ENABLE_ROLLING_LOGS`          | Enable log rotation        | `true`       | `false`                                                                                              |
| `USE_LARGE_PAGES`              | Use large pages for memory | `false`      | `true`                                                                                               |

### Forge Settings

| Parameter                | Description                | Default      | Example                 |
| ------------------------ | -------------------------- | ------------ | ----------------------- |
| `FORGE_VERSION`          | Forge version              | Latest       | `36.2.39`               |
| `FORGE_INSTALLER_URL`    | Custom Forge installer URL | Official URL | URL to custom installer |
| `FORGE_INSTALLER_SHASUM` | SHA sum for installer      | None         | SHA256 hash             |

### Fabric Settings

| Parameter                  | Description                 | Default      | Example                 |
| -------------------------- | --------------------------- | ------------ | ----------------------- |
| `FABRIC_VERSION`           | Fabric loader version       | Latest       | `0.14.19`               |
| `FABRIC_INSTALLER_URL`     | Custom Fabric installer URL | Official URL | URL to custom installer |
| `FABRIC_INSTALLER_VERSION` | Fabric installer version    | Latest       | `0.11.2`                |

## Advanced Server Properties

Below are some advanced `server.properties` settings that can be fine-tuned:

```properties
# Network settings
network-compression-threshold=256
prevent-proxy-connections=false
use-native-transport=true

# Game mechanics
allow-flight=false
allow-nether=true
enable-command-block=false
force-gamemode=false
function-permission-level=2
generate-structures=true
max-build-height=256
max-world-size=29999984
spawn-animals=true
spawn-monsters=true
spawn-npcs=true

# Resource usage
max-tick-time=60000
entity-broadcast-range-percentage=100
simulation-distance=10
view-distance=10
entity-activation-range-animals=32
entity-activation-range-monsters=32
entity-activation-range-misc=16
```

## Example Configurations

### Vanilla Survival Server

```yaml
environment:
  TYPE: "VANILLA"
  VERSION: "1.20.1"
  MEMORY: "2G"
  DIFFICULTY: "normal"
  MODE: "survival"
  MOTD: "Vanilla Survival Server"
  PVP: "true"
  VIEW_DISTANCE: "10"
  MAX_PLAYERS: "20"
```

### High-Performance Paper Server

```yaml
environment:
  TYPE: "PAPER"
  VERSION: "1.20.1"
  MEMORY: "8G"
  INIT_MEMORY: "2G"
  USE_AIKAR_FLAGS: "true"
  VIEW_DISTANCE: "12"
  SIMULATION_DISTANCE: "8"
  NETWORK_COMPRESSION_THRESHOLD: "512"
  MAX_TICK_TIME: "-1"
  MOTD: "High Performance Paper Server"
```

### Family-Friendly Creative Server

```yaml
environment:
  TYPE: "PAPER"
  VERSION: "1.20.1"
  MEMORY: "4G"
  MODE: "creative"
  DIFFICULTY: "peaceful"
  PVP: "false"
  SPAWN_MONSTERS: "false"
  MOTD: "Creative Building Server"
  WHITELIST: "player1,player2,player3"
  ENFORCE_WHITELIST: "true"
  OPS: "admin1,admin2"
```

### Modded Forge Server

```yaml
environment:
  TYPE: "FORGE"
  VERSION: "1.18.2"
  FORGE_VERSION: "40.2.0"
  MEMORY: "6G"
  MAX_MEMORY: "8G"
  MOTD: "Modded Forge Server"
  MAX_PLAYERS: "10"
  VIEW_DISTANCE: "8"
```

## Troubleshooting Common Configuration Issues

### Out of Memory Errors

If your server crashes with "out of memory" errors:

1. Increase the memory allocation:

   ```yaml
   MEMORY: "4G"
   ```

2. Enable Aikar's flags for better memory management:

   ```yaml
   USE_AIKAR_FLAGS: "true"
   ```

3. Reduce view distance and simulation distance:
   ```yaml
   VIEW_DISTANCE: "8"
   SIMULATION_DISTANCE: "6"
   ```

### Performance Issues

If your server is experiencing lag:

1. Update Java version (for newer Minecraft versions):

   ```yaml
   image: itzg/minecraft-server:java21
   ```

2. Reduce redstone complexity with Paper settings:

   ```yaml
   # Add to data/config/paper-world-defaults.yml
   redstone-implementation: alternate
   ```

3. Install performance-enhancing mods/plugins:
   ```bash
   python minecraft-server.py console install-mod lithium
   ```

## Further Resources

- [Official Minecraft Wiki - Server.properties](https://minecraft.wiki/w/Server.properties)
- [Paper Documentation](https://docs.papermc.io/)
- [Spigot Configuration Guide](https://www.spigotmc.org/wiki/spigot-configuration/)
- [Forge Documentation](https://docs.minecraftforge.net/)
- [Fabric Documentation](https://fabricmc.net/wiki/)
