# Troubleshooting Guide

This guide covers common issues you might encounter when using the Minecraft Server Manager and provides solutions to resolve them.

## Server Startup Issues

### Java Version Compatibility

**Problem**: The server fails to start with Java version errors like `UnsupportedClassVersionError`.

**Symptom**: Container keeps restarting, and logs show:

```
Exception in thread "ServerMain" java.lang.UnsupportedClassVersionError: org/bukkit/craftbukkit/Main has been compiled by a more recent version of the Java Runtime
```

**Solution**:

1. Update the Docker image to use Java 21 (required for recent Minecraft versions):

   ```yaml
   # In docker-compose.yml
   image: itzg/minecraft-server:java21
   ```

2. If using an older Minecraft version that doesn't support Java 21, specify the version:

   ```yaml
   # For older Minecraft versions (pre-1.18)
   image: itzg/minecraft-server:java17
   ```

3. Manual fix for docker-compose.yml:

   ```bash
   sed -i 's/java17/java21/g' docker-compose.yml
   ```

4. Restart the server with the updated Java version:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Memory Issues

**Problem**: Server crashes during startup with out-of-memory errors.

**Symptom**: Logs show `java.lang.OutOfMemoryError: Java heap space`.

**Solution**:

1. Increase memory allocation:

   ```bash
   python minecraft-server.py --memory 4G start
   ```

2. Or edit docker-compose.yml:

   ```yaml
   environment:
     MEMORY: "4G"
   ```

3. For very large modpacks, you might need 6-8GB:
   ```bash
   python minecraft-server.py --memory 8G start
   ```

### Port Conflicts

**Problem**: Docker can't start the container because port 25565 is already in use.

**Symptom**: Error message: `Error starting container: port is already allocated`.

**Solution**:

1. Find what's using the port:

   ```bash
   lsof -i :25565
   # or
   netstat -tuln | grep 25565
   ```

2. Stop the process using the port:

   ```bash
   kill <PID>
   ```

3. Or change the port in docker-compose.yml:
   ```yaml
   ports:
     - "25570:25565" # Maps external port 25570 to internal 25565
   ```

## Connection Issues

### Can't Connect to Server

**Problem**: Minecraft client can't connect to the server.

**Symptoms**:

- "Connection timed out" error
- "Connection refused" error

**Solutions**:

1. **Verify server is running**:

   ```bash
   python minecraft-server.py status
   ```

2. **Check connection information**:

   - For local connections, use `localhost` or `127.0.0.1`
   - For LAN connections, use the local IP address shown in status
   - For remote connections, ensure port 25565 is forwarded in your router

3. **Firewall issues**:

   ```bash
   # On Linux
   sudo ufw allow 25565/tcp

   # On Windows (run as administrator)
   netsh advfirewall firewall add rule name="Minecraft Server" dir=in action=allow protocol=TCP localport=25565
   ```

4. **For AWS servers**:
   - Check security group settings to allow TCP port 25565 from your IP or 0.0.0.0/0
   - Verify the instance is in a public subnet with route to internet gateway

### Connection Timeout

**Problem**: Connection times out when trying to connect.

**Solution**:

1. Ensure the server is fully initialized:

   ```bash
   docker logs minecraft-server | tail -n 50
   ```

   Look for "Done! For help, type "help""

2. Check if the server is accessible:

   ```bash
   telnet <server_ip> 25565
   ```

3. Disable online mode for testing:
   ```yaml
   environment:
     ONLINE_MODE: "false"
   ```

## Performance Issues

### Server Lag

**Problem**: Server runs slowly or has high tick times.

**Solutions**:

1. Increase memory allocation:

   ```bash
   python minecraft-server.py --memory 4G start
   ```

2. Optimize Java flags in docker-compose.yml:

   ```yaml
   JVM_XX_OPTS: "-XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC"
   ```

3. Install performance mods:

   ```bash
   python minecraft-server.py console install-mod lithium
   python minecraft-server.py console install-mod starlight
   ```

4. Adjust server settings in server.properties:
   ```properties
   view-distance=8
   simulation-distance=8
   network-compression-threshold=256
   ```

### High CPU Usage

**Problem**: Server uses too much CPU.

**Solution**:

1. Check what entities or chunks might be causing issues:

   ```bash
   python minecraft-server.py console spark tps
   ```

2. Install performance mods like Lithium or Paper if using Vanilla.

3. Limit server resources (Docker):
   ```yaml
   deploy:
     resources:
       limits:
         cpus: "2"
   ```

## Mod/Plugin Issues

### Failed Mod Installation

**Problem**: Mod installation fails.

**Solution**:

1. Ensure the server is running:

   ```bash
   python minecraft-server.py status
   ```

2. Verify mod ID is correct:

   ```bash
   # For Modrinth
   curl -s https://api.modrinth.com/v2/project/lithium | jq .id
   ```

3. Manual installation:
   - Download the mod file
   - Place it in the plugins/ directory
   - Restart the server

### Incompatible Mods

**Problem**: Server crashes after mod installation.

**Solution**:

1. Check logs for specific mod errors:

   ```bash
   docker exec minecraft-server cat /data/logs/latest.log
   ```

2. Start server without mods:

   ```bash
   # Temporarily rename plugins directory
   mv plugins plugins_backup
   ```

3. Add mods one by one to identify the problematic one.

## Backup and Restore Issues

### Backup Creation Failed

**Problem**: Server backup fails to create.

**Solution**:

1. Check disk space:

   ```bash
   df -h
   ```

2. Ensure backup directory permissions:

   ```bash
   chmod -R 777 backups/
   ```

3. Manual backup:
   ```bash
   docker exec minecraft-server mc-backup
   ```

### Restore Failed

**Problem**: Restore operation fails.

**Solution**:

1. Stop the server first:

   ```bash
   python minecraft-server.py stop
   ```

2. Check backup file integrity:

   ```bash
   tar -tvf backups/server_backup.tar.gz
   ```

3. Manual restore:
   ```bash
   rm -rf data/*
   tar -xzf backups/server_backup.tar.gz -C data/
   ```

## Environment-Specific Issues

### Docker Issues

**Problem**: Docker-related errors.

**Solution**:

1. Restart Docker service:

   ```bash
   # Linux
   sudo systemctl restart docker

   # macOS/Windows
   docker desktop restart
   ```

2. Check Docker logs:
   ```bash
   docker system info
   docker events --since 30m
   ```

### AWS Issues

**Problem**: AWS deployment issues.

**Solution**:

1. Check AWS credentials:

   ```bash
   aws sts get-caller-identity
   ```

2. Verify instance status:

   ```bash
   aws ec2 describe-instances --instance-ids <instance-id>
   ```

3. Check CloudWatch logs:
   ```bash
   aws logs get-log-events --log-group-name /minecraft/server --log-stream-name <stream>
   ```

## Diagnostic Commands

### Server Diagnostics

```bash
# Check server status with debug
python minecraft-server.py --debug status

# View detailed logs
docker logs minecraft-server | grep -i error

# Enter server console
python minecraft-server.py console

# Check server properties
docker exec minecraft-server cat /data/server.properties
```

### System Diagnostics

```bash
# Check Docker status
docker stats minecraft-server

# Check server resource usage
top -p $(docker inspect --format {{.State.Pid}} minecraft-server)

# Check open ports
ss -tuln | grep 25565
```

## Getting Additional Help

If you're still experiencing issues after trying these troubleshooting steps, you can get help from:

1. Create an issue in the GitHub repository with:

   - Exact error messages
   - Steps to reproduce
   - Server logs
   - System information

2. Join our Discord server for community support.

3. Check the official documentation for the Minecraft server type you're using:
   - [Paper](https://docs.papermc.io/)
   - [Spigot](https://www.spigotmc.org/wiki/spigot/)
   - [Forge](https://docs.minecraftforge.net/)
