# Minecraft Server Flavors Guide

This guide compares the different Minecraft server implementations (flavors) available through the Minecraft Server Manager. Each server type has its own strengths, weaknesses, and unique features to consider when choosing the right one for your needs.

## Server Types Overview

| Server Type | Performance | Plugin Support | Mod Support | Update Speed | Vanilla Compatibility |
| ----------- | ----------- | -------------- | ----------- | ------------ | --------------------- |
| Vanilla     | ⭐⭐        | ❌             | ❌          | ⭐⭐⭐⭐⭐   | ⭐⭐⭐⭐⭐            |
| Spigot      | ⭐⭐⭐      | ⭐⭐⭐⭐       | ❌          | ⭐⭐⭐⭐     | ⭐⭐⭐⭐              |
| Paper       | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐       | ❌          | ⭐⭐⭐⭐     | ⭐⭐⭐⭐              |
| Forge       | ⭐⭐        | ❌             | ⭐⭐⭐⭐⭐  | ⭐⭐         | ⭐⭐⭐                |
| Fabric      | ⭐⭐⭐⭐    | ❌             | ⭐⭐⭐⭐    | ⭐⭐⭐       | ⭐⭐⭐⭐              |
| Purpur      | ⭐⭐⭐⭐⭐  | ⭐⭐⭐⭐⭐     | ❌          | ⭐⭐⭐       | ⭐⭐⭐                |

## Detailed Comparison

### Vanilla

The official Minecraft server provided by Mojang.

**Pros:**

- 100% compatibility with the vanilla client
- Receives updates immediately when new Minecraft versions release
- Simplest to set up and understand
- Official support from Mojang

**Cons:**

- Limited performance optimizations
- No built-in plugin support
- Few configuration options for advanced users
- Can struggle with many players or complex redstone

**Best for:**

- Small servers with few players (1-5)
- Players who want the exact vanilla experience
- Testing and simple setups
- Temporary servers

**Configuration with Minecraft Server Manager:**

```yaml
TYPE: "VANILLA"
VERSION: "1.20.1"
```

### Spigot

An extended and optimized version of the vanilla server with plugin support.

**Pros:**

- Improved performance over vanilla
- Supports Bukkit plugins (thousands available)
- More configuration options
- Better entity handling and chunk loading

**Cons:**

- Updates take some time after vanilla release
- Some vanilla behaviors might be altered
- Less performant than Paper

**Best for:**

- Small to medium servers (5-20 players)
- Servers needing basic plugins
- Balance between vanilla experience and performance

**Configuration with Minecraft Server Manager:**

```yaml
TYPE: "SPIGOT"
VERSION: "1.20.1"
```

### Paper

A high-performance fork of Spigot with additional optimizations and features.

**Pros:**

- Significantly better performance than Spigot
- Supports all Spigot/Bukkit plugins
- Advanced configuration options
- Excellent for larger servers
- Better multithreading capabilities

**Cons:**

- Further diverges from vanilla behavior in some cases
- Some technical vanilla farms might not work as expected

**Best for:**

- Medium to large servers (20-100+ players)
- Servers requiring maximum performance
- Public community servers
- Servers using many plugins

**Configuration with Minecraft Server Manager:**

```yaml
TYPE: "PAPER"
VERSION: "1.20.1"
```

### Forge

The most popular modding platform allowing for extensive game modifications.

**Pros:**

- Supports thousands of Forge mods
- Allows for total game transformations
- Strong community support
- Stable API for mod developers

**Cons:**

- Performance can be impacted heavily by mods
- Updates to new Minecraft versions take longer
- No native plugin support (though hybrid solutions exist)
- Higher memory and CPU requirements

**Best for:**

- Modded gameplay experiences
- Custom modpacks
- Technical or adventure-focused servers
- Single-player-like multiplayer experiences

**Configuration with Minecraft Server Manager:**

```yaml
TYPE: "FORGE"
VERSION: "1.18.2"
FORGE_VERSION: "40.2.0"
MEMORY: "6G" # Modded servers need more memory
```

### Fabric

A lightweight, modern modding platform with better performance than Forge.

**Pros:**

- Faster updates to new Minecraft versions
- Better performance than Forge with mods installed
- Growing community and mod ecosystem
- More lightweight than Forge

**Cons:**

- Fewer available mods than Forge
- No native plugin support
- Newer platform with fewer community resources
- Incompatible with Forge mods

**Best for:**

- Performance-focused modded servers
- Newer Minecraft versions
- Lightweight mod collections
- Technical Minecraft communities

**Configuration with Minecraft Server Manager:**

```yaml
TYPE: "FABRIC"
VERSION: "1.20.1"
MEMORY: "4G"
```

### Purpur

A fork of Paper with even more features and customization options.

**Pros:**

- All Paper optimizations plus more
- Numerous additional configuration options
- Experimental features not found in other servers
- Support for very large player counts

**Cons:**

- Furthest from vanilla behavior
- Less stable than Paper due to experimental features
- Might break some technical vanilla farms/mechanisms

**Best for:**

- Large public servers
- Servers needing extreme customization
- Communities wanting unique gameplay features
- Minigame servers

**Configuration with Minecraft Server Manager:**

```yaml
TYPE: "PURPUR"
VERSION: "1.20.1"
```

## Special Purpose Servers

### Mohist/Magma/Arclight

Hybrid servers that attempt to combine Forge mod support with Bukkit/Spigot plugin support.

**Pros:**

- Run both mods and plugins simultaneously
- Access to both ecosystems
- Some unique features

**Cons:**

- Stability issues
- Compatibility problems between mods and plugins
- Performance concerns
- Slower updates

**Best for:**

- Experienced server admins
- Specialized server setups needing both mods and plugins
- Testing and development environments

### Velocity/Waterfall/BungeeCord

Proxy servers that allow connecting multiple Minecraft servers together.

**Note:** These are not standalone server types but proxies that run alongside Minecraft servers.

**Pros:**

- Connect multiple servers together
- Better player distribution
- Advanced network features

**Cons:**

- More complex setup
- Additional server requirements
- Extra configuration needed

## Choosing the Right Server Type

### For a Simple Server with Friends

**Recommendation:** Paper

```yaml
TYPE: "PAPER"
VERSION: "1.20.1"
MEMORY: "2G"
```

Paper provides good performance without complex configuration, suitable for most small to medium groups.

### For a High-Performance Public Server

**Recommendation:** Paper or Purpur

```yaml
TYPE: "PAPER"
VERSION: "1.20.1"
MEMORY: "8G"
VIEW_DISTANCE: "8"
SIMULATION_DISTANCE: "6"
USE_AIKAR_FLAGS: "true"
```

### For a Modded Experience

**Recommendation:** Forge or Fabric

```yaml
TYPE: "FORGE"
VERSION: "1.18.2"
FORGE_VERSION: "40.2.0"
MEMORY: "6G"
```

### For Technical Minecraft

**Recommendation:** Paper with careful configuration or Fabric with lithium/phosphor mods

```yaml
TYPE: "PAPER"
VERSION: "1.20.1"
MEMORY: "4G"
```

With these configuration adjustments in `paper.yml`:

```yaml
use-faster-eigencraft-redstone: false
fix-tnt-entity-height: false
```

## Version Support Table

| Server Type | 1.16.5 | 1.17.1 | 1.18.2 | 1.19.4 | 1.20.x |
| ----------- | ------ | ------ | ------ | ------ | ------ |
| Vanilla     | ✅     | ✅     | ✅     | ✅     | ✅     |
| Spigot      | ✅     | ✅     | ✅     | ✅     | ✅     |
| Paper       | ✅     | ✅     | ✅     | ✅     | ✅     |
| Forge       | ✅     | ✅     | ✅     | ✅     | ✅     |
| Fabric      | ✅     | ✅     | ✅     | ✅     | ✅     |
| Purpur      | ✅     | ✅     | ✅     | ✅     | ✅     |

## Migration Between Server Types

### Upgrading from Vanilla to Paper

1. Make a backup of your vanilla server
2. Change the server type in your configuration:
   ```yaml
   TYPE: "PAPER"
   ```
3. Start the server with the Minecraft Server Manager
4. The world data will be automatically migrated

### Migrating from Bukkit/Spigot to Paper

1. Back up your server
2. Change the server type:
   ```yaml
   TYPE: "PAPER"
   ```
3. Start the server
4. All plugins and worlds should work without modification

### Migrating Between Mod Systems (Forge to Fabric)

1. Back up your server
2. This is a more complex migration - mods are not compatible between systems
3. Set up the new server type:
   ```yaml
   TYPE: "FABRIC"
   ```
4. Your world data can be reused, but you'll need to find equivalent mods
5. Consider using a fresh world if heavy modded content was used

## Further Reading

- [Paper Documentation](https://docs.papermc.io/)
- [Spigot Wiki](https://www.spigotmc.org/wiki/spigot/)
- [Forge Documentation](https://docs.minecraftforge.net/)
- [Fabric Wiki](https://fabricmc.net/wiki/start)
- [Purpur Documentation](https://purpurmc.org/docs)
