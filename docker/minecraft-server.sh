#!/bin/bash

# Minecraft Server Docker Manager
# This script helps manage a Docker-based Minecraft server

set -e

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
DATA_DIR="${SCRIPT_DIR}/data"
PLUGINS_DIR="${SCRIPT_DIR}/plugins"
CONFIG_DIR="${SCRIPT_DIR}/config"
BACKUPS_DIR="${SCRIPT_DIR}/backups"
CONTAINER_NAME="minecraft-server"

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Print header
print_header() {
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${BLUE}        Minecraft Server Manager             ${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo ""
}

# Ensure directories exist
mkdir -p "${DATA_DIR}" "${PLUGINS_DIR}" "${CONFIG_DIR}" "${BACKUPS_DIR}"

check_server_running() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        return 0 # Server is running
    else
        return 1 # Server is not running
    fi
}

start_server() {
    print_header
    
    if check_server_running; then
        echo -e "${YELLOW}Server is already running!${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Starting Minecraft server...${NC}"
    cd "${SCRIPT_DIR}" && docker-compose up -d
    
    echo -e "${GREEN}Checking server startup...${NC}"
    # Wait for the server to initialize (checks 10 times with 5-second intervals)
    for i in {1..10}; do
        if docker logs ${CONTAINER_NAME} 2>&1 | grep -q "Done"; then
            echo -e "${GREEN}Server started successfully!${NC}"
            echo -e "Connect to server at: ${PURPLE}localhost:25565${NC}"
            return 0
        fi
        echo -e "${YELLOW}Waiting for server to initialize... ($i/10)${NC}"
        sleep 5
    done
    
    echo -e "${YELLOW}Server is starting but taking longer than expected.${NC}"
    echo -e "${YELLOW}Check logs with: $0 logs${NC}"
}

stop_server() {
    print_header
    
    if ! check_server_running; then
        echo -e "${YELLOW}Server is not running!${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Stopping Minecraft server...${NC}"
    
    # Send stop command to server console first for clean shutdown
    execute_command "stop"
    
    # Wait for server to stop gracefully
    sleep 5
    
    # Force stop if still running
    cd "${SCRIPT_DIR}" && docker-compose down
    echo -e "${GREEN}Server stopped successfully!${NC}"
}

restart_server() {
    print_header
    echo -e "${GREEN}Restarting Minecraft server...${NC}"
    stop_server
    sleep 2
    start_server
}

backup() {
    print_header
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="${BACKUPS_DIR}/minecraft_backup_${timestamp}.tar.gz"
    
    echo -e "${GREEN}Creating backup: ${backup_file}${NC}"
    
    # Create backup directory if it doesn't exist
    mkdir -p "${BACKUPS_DIR}"
    
    # If server is running, warn the players
    if check_server_running; then
        execute_command "say Server backup starting. You may experience lag for a few moments."
    fi
    
    # Create the backup
    tar -czf "${backup_file}" -C "${SCRIPT_DIR}" data plugins config
    
    # Check if backup was successful
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup completed: ${backup_file}${NC}"
        
        # Report backup size
        size=$(du -h "${backup_file}" | cut -f1)
        echo -e "${GREEN}Backup size: ${size}${NC}"
        
        # Notify players
        if check_server_running; then
            execute_command "say Server backup completed successfully!"
        fi
        
        # Clean up old backups (keep last 10)
        NUM_BACKUPS_TO_KEEP=10
        NUM_BACKUPS=$(ls -1 "${BACKUPS_DIR}"/minecraft_backup_*.tar.gz 2>/dev/null | wc -l)
        if [ ${NUM_BACKUPS} -gt ${NUM_BACKUPS_TO_KEEP} ]; then
            echo -e "${YELLOW}Cleaning up old backups (keeping last ${NUM_BACKUPS_TO_KEEP})...${NC}"
            ls -1t "${BACKUPS_DIR}"/minecraft_backup_*.tar.gz | tail -n +$((${NUM_BACKUPS_TO_KEEP}+1)) | xargs rm -f
        fi
    else
        echo -e "${RED}Backup failed!${NC}"
    fi
}

restore_backup() {
    print_header
    
    # Check if server is running
    if check_server_running; then
        echo -e "${RED}Server must be stopped before restoring a backup.${NC}"
        echo -e "${YELLOW}Stop the server first with: $0 stop${NC}"
        return 1
    fi
    
    # List available backups
    echo -e "${GREEN}Available backups:${NC}"
    
    if [ ! -d "${BACKUPS_DIR}" ] || [ -z "$(ls -A ${BACKUPS_DIR})" ]; then
        echo -e "${RED}No backups found in ${BACKUPS_DIR}${NC}"
        return 1
    fi
    
    # List backups with numbers
    local i=1
    local backups=()
    
    while read -r backup; do
        backups+=("$backup")
        local date_part=$(echo "$backup" | sed -E 's/.*minecraft_backup_([0-9]{8}_[0-9]{6}).*/\1/')
        local date_formatted=$(date -d "${date_part:0:8} ${date_part:9:2}:${date_part:11:2}:${date_part:13:2}" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)
        
        if [ $? -ne 0 ]; then
            # MacOS date command is different
            date_formatted=$(date -j -f "%Y%m%d_%H%M%S" "$date_part" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)
            
            if [ $? -ne 0 ]; then
                date_formatted="$date_part"
            fi
        fi
        
        local size=$(du -h "$backup" | cut -f1)
        echo -e "${i}) ${date_formatted} (${size})"
        ((i++))
    done < <(ls -1t "${BACKUPS_DIR}"/minecraft_backup_*.tar.gz)
    
    # Ask user to select a backup
    echo ""
    read -p "Enter the number of the backup to restore (or 'q' to quit): " selection
    
    if [[ $selection == 'q' || $selection == 'Q' ]]; then
        echo -e "${YELLOW}Restore cancelled.${NC}"
        return 0
    fi
    
    if ! [[ $selection =~ ^[0-9]+$ ]] || [ $selection -lt 1 ] || [ $selection -gt ${#backups[@]} ]; then
        echo -e "${RED}Invalid selection.${NC}"
        return 1
    fi
    
    local selected_backup="${backups[$((selection-1))]}"
    
    echo -e "${YELLOW}You are about to restore the following backup: ${selected_backup}${NC}"
    echo -e "${RED}WARNING: This will overwrite all current data!${NC}"
    read -p "Are you sure you want to continue? (y/n): " confirm
    
    if [[ $confirm != 'y' && $confirm != 'Y' ]]; then
        echo -e "${YELLOW}Restore cancelled.${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Restoring backup: ${selected_backup}${NC}"
    
    # Move current data to temp location as a precaution
    echo -e "${YELLOW}Creating temporary backup of current data...${NC}"
    temp_backup="${DATA_DIR}_temp_$(date +%s)"
    mv "${DATA_DIR}" "${temp_backup}"
    mkdir -p "${DATA_DIR}"
    
    # Restore from backup
    echo -e "${GREEN}Extracting backup...${NC}"
    tar -xzf "${selected_backup}" -C "${SCRIPT_DIR}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup restored successfully!${NC}"
        echo -e "${YELLOW}Removing temporary backup...${NC}"
        rm -rf "${temp_backup}"
    else
        echo -e "${RED}Restore failed! Reverting to previous data...${NC}"
        rm -rf "${DATA_DIR}"
        mv "${temp_backup}" "${DATA_DIR}"
    fi
}

status() {
    print_header
    echo -e "${GREEN}Minecraft server status:${NC}"
    
    if ! check_server_running; then
        echo -e "${YELLOW}Server is currently ${RED}OFFLINE${NC}"
        return 0
    fi
    
    echo -e "Server is currently ${GREEN}ONLINE${NC}"
    
    # Show container status
    cd "${SCRIPT_DIR}" && docker-compose ps
    
    # Get more detailed server info if it's running
    echo -e "\n${GREEN}Server Information:${NC}"
    
    # Get server version
    local version=$(docker logs ${CONTAINER_NAME} 2>&1 | grep "Starting minecraft server version" | tail -1 | sed -E 's/.*version (.*)/\1/')
    echo -e "Version: ${BLUE}${version:-Unknown}${NC}"
    
    # Get server uptime
    local container_start_time=$(docker inspect --format='{{.State.StartedAt}}' ${CONTAINER_NAME})
    local uptime=$(docker inspect --format='{{.State.StartedAt}}' ${CONTAINER_NAME} | xargs date -d | xargs -I{} bash -c "echo \$((($(date +%s) - \$(date -d '{}' +%s))) / 60) minutes")
    
    echo -e "Uptime: ${BLUE}${uptime:-Unknown}${NC}"
    
    # Get player count if RCON is enabled
    echo -e "\n${GREEN}Player Info:${NC}"
    local player_list=$(docker exec ${CONTAINER_NAME} rcon-cli "list")
    echo -e "${BLUE}${player_list:-Could not get player list}${NC}"
    
    # Show container resource usage
    echo -e "\n${GREEN}Resource Usage:${NC}"
    docker stats ${CONTAINER_NAME} --no-stream --format "CPU: {{.CPUPerc}}  RAM: {{.MemUsage}}"
}

show_logs() {
    print_header
    echo -e "${GREEN}Showing Minecraft server logs:${NC}"
    cd "${SCRIPT_DIR}" && docker-compose logs "$@"
}

execute_command() {
    if ! check_server_running; then
        echo -e "${RED}Server is not running!${NC}"
        return 1
    fi
    
    local command="$1"
    echo -e "${GREEN}Executing command: ${command}${NC}"
    docker exec ${CONTAINER_NAME} rcon-cli "$command"
}

console() {
    print_header
    
    if ! check_server_running; then
        echo -e "${RED}Server is not running!${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Connecting to Minecraft server console...${NC}"
    echo -e "${YELLOW}Type 'exit' to leave the console${NC}"
    
    # Access console through RCON
    docker exec -it ${CONTAINER_NAME} rcon-cli
}

manage_plugins() {
    print_header
    echo -e "${GREEN}Plugin Management${NC}"
    
    echo -e "1) List installed plugins"
    echo -e "2) Install plugin from URL"
    echo -e "3) Remove plugin"
    echo -e "4) Return to main menu"
    
    read -p "Enter your choice: " choice
    
    case "$choice" in
        1)
            # List plugins
            echo -e "${GREEN}Installed plugins:${NC}"
            if [ -d "${PLUGINS_DIR}" ] && [ "$(ls -A ${PLUGINS_DIR})" ]; then
                ls -1 "${PLUGINS_DIR}" | grep '\.jar$' | sed 's/\.jar$//'
            else
                echo -e "${YELLOW}No plugins installed.${NC}"
            fi
            ;;
        2)
            # Install plugin
            read -p "Enter plugin JAR URL: " plugin_url
            plugin_name=$(basename "$plugin_url")
            
            echo -e "${GREEN}Downloading plugin: ${plugin_name}${NC}"
            if curl -s -L -o "${PLUGINS_DIR}/${plugin_name}" "$plugin_url"; then
                echo -e "${GREEN}Plugin downloaded successfully!${NC}"
                
                if check_server_running; then
                    echo -e "${YELLOW}Note: You may need to restart the server for the plugin to take effect.${NC}"
                    read -p "Restart server now? (y/n): " restart_now
                    if [[ $restart_now == 'y' || $restart_now == 'Y' ]]; then
                        restart_server
                    fi
                fi
            else
                echo -e "${RED}Failed to download plugin.${NC}"
            fi
            ;;
        3)
            # Remove plugin
            echo -e "${GREEN}Installed plugins:${NC}"
            if [ ! -d "${PLUGINS_DIR}" ] || [ -z "$(ls -A ${PLUGINS_DIR})" ]; then
                echo -e "${YELLOW}No plugins installed.${NC}"
                return 0
            fi
            
            # List plugins with numbers
            local i=1
            local plugins=()
            
            while read -r plugin; do
                plugins+=("$plugin")
                echo -e "${i}) ${plugin%.*}"
                ((i++))
            done < <(ls -1 "${PLUGINS_DIR}" | grep '\.jar$')
            
            read -p "Enter the number of the plugin to remove (or 'q' to quit): " selection
            
            if [[ $selection == 'q' || $selection == 'Q' ]]; then
                echo -e "${YELLOW}Removal cancelled.${NC}"
                return 0
            fi
            
            if ! [[ $selection =~ ^[0-9]+$ ]] || [ $selection -lt 1 ] || [ $selection -gt ${#plugins[@]} ]; then
                echo -e "${RED}Invalid selection.${NC}"
                return 1
            fi
            
            rm "${PLUGINS_DIR}/${plugins[$((selection-1))]}"
            echo -e "${GREEN}Plugin removed successfully!${NC}"
            
            if check_server_running; then
                echo -e "${YELLOW}Note: You may need to restart the server for the change to take effect.${NC}"
                read -p "Restart server now? (y/n): " restart_now
                if [[ $restart_now == 'y' || $restart_now == 'Y' ]]; then
                    restart_server
                fi
            fi
            ;;
        4)
            return 0
            ;;
        *)
            echo -e "${RED}Invalid choice.${NC}"
            ;;
    esac
}

show_help() {
    print_header
    echo -e "${GREEN}Minecraft Server Docker Manager${NC}"
    echo -e "${BLUE}Usage: $0 [command]${NC}"
    echo ""
    echo -e "${YELLOW}Server Management Commands:${NC}"
    echo -e "  ${BLUE}start${NC}      Start the Minecraft server"
    echo -e "  ${BLUE}stop${NC}       Stop the Minecraft server"
    echo -e "  ${BLUE}restart${NC}    Restart the Minecraft server"
    echo -e "  ${BLUE}status${NC}     Show server status, uptime, and player count"
    echo -e "  ${BLUE}console${NC}    Connect to the server console (RCON)"
    echo ""
    echo -e "${YELLOW}Data Management Commands:${NC}"
    echo -e "  ${BLUE}backup${NC}     Create a backup of the server data"
    echo -e "  ${BLUE}restore${NC}    Restore from a previous backup"
    echo -e "  ${BLUE}plugins${NC}    Manage server plugins"
    echo ""
    echo -e "${YELLOW}Monitoring Commands:${NC}"
    echo -e "  ${BLUE}logs${NC}       Show server logs (add -f to follow)"
    echo -e "  ${BLUE}cmd \"command\"${NC}   Execute a command on the server console"
    echo ""
    echo -e "${YELLOW}Help Commands:${NC}"
    echo -e "  ${BLUE}help${NC}       Show this help message"
}

# Main script execution
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        status
        ;;
    backup)
        backup
        ;;
    restore)
        restore_backup
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    console)
        console
        ;;
    cmd)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Command required.${NC}"
            echo -e "${YELLOW}Usage: $0 cmd \"command\"${NC}"
            exit 1
        fi
        execute_command "$2"
        ;;
    plugins)
        manage_plugins
        ;;
    help|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac 