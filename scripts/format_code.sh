#!/bin/bash
#
# Auto-format code based on file extension.
# This script runs after file modifications to ensure consistent formatting.
#

# Read the hook input
HOOK_INPUT=$(cat)

# Extract file path and tool name using jq
FILE_PATH=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // ""')
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // ""')

# Only process file modifications
if [[ ! "$TOOL_NAME" =~ ^(Write|Edit|MultiEdit)$ ]]; then
    exit 0
fi

# Skip if no file path
if [ -z "$FILE_PATH" ] || [ "$FILE_PATH" = "null" ]; then
    exit 0
fi

# Log the formatting attempt
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking format for: $FILE_PATH" >> logs/formatting.log

# Get file extension
EXT="${FILE_PATH##*.}"
BASENAME=$(basename "$FILE_PATH")

# Skip formatting for certain files
case "$BASENAME" in
    .gitignore|.env*|*.md|*.txt|*.log|*.json|*.yml|*.yaml)
        echo "  Skipping format for $BASENAME" >> logs/formatting.log
        exit 0
        ;;
esac

# Format based on extension
case "$EXT" in
    py)
        # Python formatting
        if command -v black &> /dev/null; then
            echo "  Running black on $FILE_PATH" >> logs/formatting.log
            black "$FILE_PATH" 2>> logs/formatting-errors.log || true
        elif command -v autopep8 &> /dev/null; then
            echo "  Running autopep8 on $FILE_PATH" >> logs/formatting.log
            autopep8 --in-place "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        
        # Python import sorting
        if command -v isort &> /dev/null; then
            echo "  Running isort on $FILE_PATH" >> logs/formatting.log
            isort "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    js|jsx|ts|tsx)
        # JavaScript/TypeScript formatting
        if command -v prettier &> /dev/null; then
            echo "  Running prettier on $FILE_PATH" >> logs/formatting.log
            prettier --write "$FILE_PATH" 2>> logs/formatting-errors.log || true
        elif command -v eslint &> /dev/null; then
            echo "  Running eslint --fix on $FILE_PATH" >> logs/formatting.log
            eslint --fix "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    go)
        # Go formatting
        if command -v gofmt &> /dev/null; then
            echo "  Running gofmt on $FILE_PATH" >> logs/formatting.log
            gofmt -w "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        
        if command -v goimports &> /dev/null; then
            echo "  Running goimports on $FILE_PATH" >> logs/formatting.log
            goimports -w "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    rs)
        # Rust formatting
        if command -v rustfmt &> /dev/null; then
            echo "  Running rustfmt on $FILE_PATH" >> logs/formatting.log
            rustfmt "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    sh|bash)
        # Shell script formatting
        if command -v shfmt &> /dev/null; then
            echo "  Running shfmt on $FILE_PATH" >> logs/formatting.log
            shfmt -w "$FILE_PATH" 2>> logs/formatting-errors.log || true
        fi
        ;;
        
    *)
        echo "  No formatter configured for .$EXT files" >> logs/formatting.log
        ;;
esac

# Always exit successfully to not block operations
exit 0