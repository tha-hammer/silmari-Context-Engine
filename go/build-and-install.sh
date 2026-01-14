#!/bin/bash
# Wrapper script for building and installing context-engine and loop-runner
# Prompts to remove existing binaries before building and confirms before installing

set -e

BINARIES=("context-engine" "loop-runner")
BUILD_DIR="./build"
USER_BIN_DIR="$HOME/.local/bin"
SYSTEM_BIN_DIR="/usr/local/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to find all locations of a binary
find_binary_locations() {
    local binary=$1
    local locations=()
    
    # Check in build directory
    if [ -f "$BUILD_DIR/$binary" ]; then
        locations+=("$BUILD_DIR/$binary")
    fi
    
    # Check in user bin directory
    if [ -f "$USER_BIN_DIR/$binary" ]; then
        locations+=("$USER_BIN_DIR/$binary")
    fi
    
    # Check in system bin directory
    if [ -f "$SYSTEM_BIN_DIR/$binary" ]; then
        locations+=("$SYSTEM_BIN_DIR/$binary")
    fi
    
    # Print locations (one per line)
    printf '%s\n' "${locations[@]}"
}

# Function to remove binaries and report each deletion
remove_binaries() {
    local deleted_count=0
    
    for binary in "${BINARIES[@]}"; do
        local locations
        mapfile -t locations < <(find_binary_locations "$binary")
        
        if [ ${#locations[@]} -eq 0 ]; then
            continue
        fi
        
        for location in "${locations[@]}"; do
            if [ -f "$location" ]; then
                # Check if we need sudo for system bin directory
                if [[ "$location" == "$SYSTEM_BIN_DIR"* ]] && [ ! -w "$SYSTEM_BIN_DIR" ]; then
                    echo -e "${YELLOW}Deleting:${NC} $binary at $location (requires sudo)"
                    if sudo rm -f "$location"; then
                        echo -e "${GREEN}✓ Deleted:${NC} $binary at $location"
                        deleted_count=$((deleted_count + 1))
                    else
                        echo -e "${RED}✗ Failed to delete:${NC} $binary at $location"
                    fi
                else
                    if rm -f "$location"; then
                        echo -e "${GREEN}✓ Deleted:${NC} $binary at $location"
                        deleted_count=$((deleted_count + 1))
                    else
                        echo -e "${RED}✗ Failed to delete:${NC} $binary at $location"
                    fi
                fi
            fi
        done
    done
    
    # Always return success (0) - we don't care about the count
    return 0
}

# Check for existing binaries
echo "Checking for existing binaries..."
found_any=0
for binary in "${BINARIES[@]}"; do
    locations=()
    mapfile -t locations < <(find_binary_locations "$binary")
    if [ ${#locations[@]} -gt 0 ]; then
        found_any=1
        break
    fi
done

# Prompt for clean install
if [ $found_any -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Found existing binaries:${NC}"
    for binary in "${BINARIES[@]}"; do
        locations=()
        mapfile -t locations < <(find_binary_locations "$binary")
        for location in "${locations[@]}"; do
            echo "  - $binary at $location"
        done
    done
    echo ""
    read -p "Do you want a clean install and delete existing binaries? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo ""
        remove_binaries
        echo ""
    else
        echo "Skipping binary removal..."
        echo ""
    fi
else
    echo "No existing binaries found."
    echo ""
fi

# Build
echo "Building binaries..."
make build

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build completed successfully${NC}"
echo ""

# Prompt for installation to /usr/local/bin
read -p "Do you want to install to /home/maceo/.local/bin/? [Y/n] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    make install-user
    echo ""
    echo -e "${GREEN}✓ Installation completed!${NC}"
else
    echo "Skipping installation."
    echo "You can install later with: make install-user"
fi
