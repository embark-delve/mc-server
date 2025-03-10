#!/bin/bash

# Test script for Docker-based Minecraft server

set -e

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
SERVER_SCRIPT="${SCRIPT_DIR}/minecraft-server.sh"
CONTAINER_NAME="minecraft-server"
SUCCESS=0
FAILURE=0

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

run_test() {
    local test_name="$1"
    local command="$2"
    
    echo -e "${YELLOW}Running test: ${test_name}${NC}"
    
    if eval "$command"; then
        echo -e "${GREEN}✓ Test passed: ${test_name}${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}✗ Test failed: ${test_name}${NC}"
        ((FAILURE++))
    fi
    
    echo
}

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}    Minecraft Server Docker Testing Suite     ${NC}"
echo -e "${BLUE}==============================================${NC}"
echo ""

# Basic setup tests
echo -e "${YELLOW}=== Basic Setup Tests ===${NC}"

# Test docker availability
run_test "Docker Available" "docker --version > /dev/null 2>&1"

# Test docker-compose availability
run_test "Docker Compose Available" "docker-compose --version > /dev/null 2>&1"

# Test script exists and is executable
run_test "Server Script Exists" "[ -f \"${SERVER_SCRIPT}\" ]"
run_test "Server Script Is Executable" "[ -x \"${SERVER_SCRIPT}\" ]"

# Test required directories
run_test "Data Directory Exists" "[ -d \"${SCRIPT_DIR}/data\" ] || mkdir -p \"${SCRIPT_DIR}/data\""
run_test "Plugins Directory Exists" "[ -d \"${SCRIPT_DIR}/plugins\" ] || mkdir -p \"${SCRIPT_DIR}/plugins\""
run_test "Config Directory Exists" "[ -d \"${SCRIPT_DIR}/config\" ] || mkdir -p \"${SCRIPT_DIR}/config\""
run_test "Backups Directory Exists" "[ -d \"${SCRIPT_DIR}/backups\" ] || mkdir -p \"${SCRIPT_DIR}/backups\""

# Test docker-compose.yml
run_test "Docker Compose File Exists" "[ -f \"${SCRIPT_DIR}/docker-compose.yml\" ]"
run_test "Docker Compose File Contains Minecraft" "grep -q 'minecraft' \"${SCRIPT_DIR}/docker-compose.yml\""

# Server functionality tests
echo -e "${YELLOW}=== Server Functionality Tests ===${NC}"

# Test server start
run_test "Server Start" "${SERVER_SCRIPT} start"

# Test server is running
run_test "Server Running" "docker ps --format '{{.Names}}' | grep -q \"^${CONTAINER_NAME}$\""

# Test server status
run_test "Server Status" "${SERVER_SCRIPT} status | grep -q 'ONLINE'"

# Allow some time for the server to initialize
echo -e "${YELLOW}Waiting for server to initialize (this may take a minute)...${NC}"
sleep 45

# Test server connectivity (requires netcat)
run_test "Server Connectivity" "nc -z localhost 25565 || nc -G 5 localhost 25565"

# Test server logs
run_test "Server Logs" "${SERVER_SCRIPT} logs --tail=10 | grep -q 'minecraft'"

# Test sending a command to the server (if RCON is enabled)
run_test "Server Command" "${SERVER_SCRIPT} cmd \"help\" | grep -q 'commands\|help'"

# Test backup functionality
echo -e "${YELLOW}=== Backup Functionality Tests ===${NC}"

# Test backup creation
run_test "Backup Creation" "${SERVER_SCRIPT} backup"
run_test "Backup File Exists" "ls -1 \"${SCRIPT_DIR}/backups\" | grep -q 'minecraft_backup_'"

# Test plugin directory mounting
echo -e "${YELLOW}=== Plugin Functionality Tests ===${NC}"

# Test plugin management (listing only)
run_test "Plugin Management" "${SERVER_SCRIPT} plugins | grep -q 'Plugin Management'"

# Cleanup tests
echo -e "${YELLOW}=== Cleanup Tests ===${NC}"

# Test server stop
run_test "Server Stop" "${SERVER_SCRIPT} stop"

# Verify server is stopped
run_test "Server Stopped" "! docker ps --format '{{.Names}}' | grep -q \"^${CONTAINER_NAME}$\""

# Print test results summary
echo -e "${YELLOW}===== Test Results =====${NC}"
echo -e "${GREEN}Passed: ${SUCCESS}${NC}"
echo -e "${RED}Failed: ${FAILURE}${NC}"

# Calculate percentage
TOTAL=$((SUCCESS + FAILURE))
if [ $TOTAL -gt 0 ]; then
    PERCENT=$((SUCCESS * 100 / TOTAL))
    echo -e "Success rate: ${GREEN}${PERCENT}%${NC}"
fi

if [ "$FAILURE" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! Check the output above for details.${NC}"
    exit 1
fi 