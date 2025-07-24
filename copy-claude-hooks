#!/bin/bash

# Claude Code Hooks Copy Script
# Copies .claude directory from the hooks mastery project to current or specified directory

set -e  # Exit on any error

# Get the directory where this script is located
SOURCE_CLAUDE_DIR="/Users/vincent.cho/workspace/github.com/disler/claude-code-hooks-mastery/.claude"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    echo "Claude Code Hooks Copy Script"
    echo ""
    echo "Usage:"
    echo "  copy-claude-hooks                    # Copy to current directory"
    echo "  copy-claude-hooks /path/to/project   # Copy to specified directory"
    echo "  copy-claude-hooks --help             # Show this help"
    echo ""
    echo "This script copies the .claude directory from:"
    echo "  $SOURCE_CLAUDE_DIR"
    echo ""
    echo "To the target directory, enabling Claude Code hooks functionality."
}

# Check if help was requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Determine target directory
if [[ $# -eq 0 ]]; then
    TARGET_DIR="$(pwd)"
    print_status "Using current directory: $TARGET_DIR"
elif [[ $# -eq 1 ]]; then
    TARGET_DIR="$1"
    print_status "Using specified directory: $TARGET_DIR"
else
    print_error "Too many arguments. Use --help for usage information."
    exit 1
fi

# Validate source directory exists
if [[ ! -d "$SOURCE_CLAUDE_DIR" ]]; then
    print_error "Source .claude directory not found at: $SOURCE_CLAUDE_DIR"
    print_warning "Please make sure you're running this script from the claude-code-hooks-mastery directory."
    exit 1
fi

# Validate target directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
    print_error "Target directory does not exist: $TARGET_DIR"
    exit 1
fi

# Check if .claude already exists in target
TARGET_CLAUDE_DIR="$TARGET_DIR/.claude"
if [[ -d "$TARGET_CLAUDE_DIR" ]]; then
    print_warning ".claude directory already exists in target."
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Operation cancelled."
        exit 0
    fi
    print_status "Removing existing .claude directory..."
    rm -rf "$TARGET_CLAUDE_DIR"
fi

# Copy .claude directory
print_status "Copying .claude directory..."
cp -r "$SOURCE_CLAUDE_DIR" "$TARGET_CLAUDE_DIR"

# Update settings.json to use absolute paths for the target project
print_status "Updating hook paths to use absolute paths..."
SETTINGS_FILE="$TARGET_CLAUDE_DIR/settings.json"
if [[ -f "$SETTINGS_FILE" ]]; then
    # Use sed to replace relative paths with absolute paths
    sed -i.bak "s|uv run .claude/hooks/|uv run $TARGET_CLAUDE_DIR/hooks/|g" "$SETTINGS_FILE"
    rm -f "$SETTINGS_FILE.bak"  # Remove backup file
    print_status "Updated settings.json with absolute paths"
else
    print_warning "settings.json not found, skipping path updates"
fi

# Create logs directory if it doesn't exist
LOGS_DIR="$TARGET_DIR/logs"
if [[ ! -d "$LOGS_DIR" ]]; then
    print_status "Creating logs directory..."
    mkdir -p "$LOGS_DIR"
fi

# Verify the copy was successful
if [[ -f "$TARGET_CLAUDE_DIR/settings.json" ]]; then
    print_success "Claude hooks successfully copied to: $TARGET_CLAUDE_DIR"
    print_status "Hooks are now active for this project!"

    # Show what was copied
    echo ""
    print_status "Files copied:"
    find "$TARGET_CLAUDE_DIR" -type f | sort | sed 's|^|  |'

    echo ""
    print_status "Next steps:"
    echo "  1. Set up your API keys in $TARGET_DIR/.env (optional)"
    echo "  2. Customize permissions in $TARGET_CLAUDE_DIR/settings.json if needed"
    echo "  3. Run any Claude Code command to see hooks in action!"
    echo ""
    print_status "Note: The hooks use \$CLAUDE_PROJECT_ROOT to resolve paths correctly."
    print_status "Claude Code automatically sets this environment variable."
else
    print_error "Copy operation failed. Please check permissions and try again."
    exit 1
fi