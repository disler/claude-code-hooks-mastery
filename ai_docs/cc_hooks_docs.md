# Get started with Claude Code hooks

> Learn how to customize and extend Claude Code's behavior by registering shell commands

Claude Code hooks are user-defined shell commands that execute at various points
in Claude Code's lifecycle. Hooks provide deterministic control over Claude
Code's behavior, ensuring certain actions always happen rather than relying on
the LLM to choose to run them.

<Tip>
  For reference documentation on hooks, see [Hooks reference](/en/docs/claude-code/hooks).
</Tip>

Example use cases for hooks include:

* **Notifications**: Customize how you get notified when Claude Code is awaiting
  your input or permission to run something.
* **Automatic formatting**: Run `prettier` on .ts files, `gofmt` on .go files,
  etc. after every file edit.
* **Logging**: Track and count all executed commands for compliance or
  debugging.
* **Feedback**: Provide automated feedback when Claude Code produces code that
  does not follow your codebase conventions.
* **Custom permissions**: Block modifications to production files or sensitive
  directories.

By encoding these rules as hooks rather than prompting instructions, you turn
suggestions into app-level code that executes every time it is expected to run.

<Warning>
  You must consider the security implication of hooks as you add them, because hooks run automatically during the agent loop with your current environment's credentials.
  For example, malicious hooks code can exfiltrate your data. Always review your hooks implementation before registering them.

  For full security best practices, see [Security Considerations](/en/docs/claude-code/hooks#security-considerations) in the hooks reference documentation.
</Warning>

## Hook Events Overview

Claude Code provides several hook events that run at different points in the
workflow:

* **PreToolUse**: Runs before tool calls (can block them)
* **PostToolUse**: Runs after tool calls complete
* **UserPromptSubmit**: Runs when the user submits a prompt, before Claude processes it
* **Notification**: Runs when Claude Code sends notifications
* **Stop**: Runs when Claude Code finishes responding
* **Subagent Stop**: Runs when subagent tasks complete
* **PreCompact**: Runs before Claude Code is about to run a compact operation
* **SessionStart**: Runs when Claude Code starts a new session or resumes an existing session

Each event receives different data and can control Claude's behavior in
different ways.

## Quickstart

In this quickstart, you'll add a hook that logs the shell commands that Claude
Code runs.

### Prerequisites

Install `jq` for JSON processing in the command line.

### Step 1: Open hooks configuration

Run the `/hooks` [slash command](/en/docs/claude-code/slash-commands) and select
the `PreToolUse` hook event.

`PreToolUse` hooks run before tool calls and can block them while providing
Claude feedback on what to do differently.

### Step 2: Add a matcher

Select `+ Add new matcher…` to run your hook only on Bash tool calls.

Type `Bash` for the matcher.

<Note>You can use `*` to match all tools.</Note>

### Step 3: Add the hook

Select `+ Add new hook…` and enter this command:

```bash
jq -r '"\(.tool_input.command) - \(.tool_input.description // "No description")"' >> ~/.claude/bash-command-log.txt
```

### Step 4: Save your configuration

For storage location, select `User settings` since you're logging to your home
directory. This hook will then apply to all projects, not just your current
project.

Then press Esc until you return to the REPL. Your hook is now registered!

### Step 5: Verify your hook

Run `/hooks` again or check `~/.claude/settings.json` to see your configuration:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"\\(.tool_input.command) - \\(.tool_input.description // \"No description\")\"' >> ~/.claude/bash-command-log.txt"
          }
        ]
      }
    ]
  }
}
```

### Step 6: Test your hook

Ask Claude to run a simple command like `ls` and check your log file:

```bash
cat ~/.claude/bash-command-log.txt
```

You should see entries like:

```
ls - Lists files and directories
```

## More Examples

<Note>
  For a complete example implementation, see the bash command validator example in our public codebase.
</Note>

### Code Formatting Hook

Automatically format TypeScript files after editing:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -q '\\.ts$'; then npx prettier --write \"$file_path\"; fi; }"
          }
        ]
      }
    ]
  }
}
```

### Markdown Formatting Hook

Automatically fix missing language tags and formatting issues in markdown files:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npx ts-node $CLAUDE_PROJECT_DIR/.claude/hooks/markdown_formatter.ts"
          }
        ]
      }
    ]
  }
}
```

Create `.claude/hooks/markdown_formatter.ts` with this content:

````typescript
#!/usr/bin/env npx ts-node

/**
 * Markdown formatter for Claude Code output.
 * Fixes missing language tags and spacing issues while preserving code content.
 */
import * as fs from 'fs';

function detectLanguage(code: string): string {
    const s = code.trim();
    
    // JSON detection
    if (/^\s*[{\[]/.test(s)) {
        try {
            JSON.parse(s);
            return 'json';
        } catch {
            // Continue to other detections
        }
    }
    
    // TypeScript detection
    if (/^\s*(interface|type|enum)\s+\w+/.test(s) ||
        /:\s*(string|number|boolean|any)\b/.test(s) ||
        /<.*>/.test(s) && /\bfunction\b/.test(s)) {
        return 'typescript';
    }
    
    // JavaScript detection  
    if (/\b(function\s+\w+\s*\(|const\s+\w+\s*=)/.test(s) ||
        /=>|console\.(log|error)/.test(s)) {
        return 'javascript';
    }
    
    // Bash detection
    if (/^#!.*\b(bash|sh)\b/m.test(s) ||
        /\b(if|then|fi|for|in|do|done)\b/.test(s)) {
        return 'bash';
    }
    
    // SQL detection
    if (/\b(SELECT|INSERT|UPDATE|DELETE|CREATE)\s+/i.test(s)) {
        return 'sql';
    }
        
    return 'text';
}

function formatMarkdown(content: string): string {
    // Fix unlabeled code fences
    function addLangToFence(match: string, indent: string, info: string, body: string, closing: string): string {
        if (!info.trim()) {
            const lang = detectLanguage(body);
            return `${indent}\`\`\`${lang}\n${body}${closing}\n`;
        }
        return match;
    }
    
    const fencePattern = /(?:^([ \t]{0,3})```([^\n]*)\n(.*?)(\n\1```)\s*$)/gms;
    content = content.replace(fencePattern, addLangToFence);
    
    // Fix excessive blank lines (only outside code fences)
    content = content.replace(/\n{3,}/g, '\n\n');
    
    return content.trimEnd() + '\n';
}

// Main execution
try {
    const inputData = JSON.parse(await new Promise<string>((resolve, reject) => {
        let data = '';
        process.stdin.on('data', chunk => data += chunk);
        process.stdin.on('end', () => resolve(data));
        process.stdin.on('error', reject);
    }));
    
    const filePath = inputData?.tool_input?.file_path || '';
    
    if (!filePath.endsWith('.md') && !filePath.endsWith('.mdx')) {
        process.exit(0); // Not a markdown file
    }
    
    if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf-8');
        const formatted = formatMarkdown(content);
        
        if (formatted !== content) {
            fs.writeFileSync(filePath, formatted);
            console.log(`✓ Fixed markdown formatting in ${filePath}`);
        }
    }
} catch (error) {
    console.error(`Error formatting markdown: ${error}`, process.stderr);
    process.exit(1);
}
````

Make the script executable:

```bash
chmod +x .claude/hooks/markdown_formatter.ts
```

This hook automatically:

* Detects programming languages in unlabeled code blocks
* Adds appropriate language tags for syntax highlighting
* Fixes excessive blank lines while preserving code content
* Only processes markdown files (`.md`, `.mdx`)

### Custom Notification Hook

Get desktop notifications when Claude needs input:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Awaiting your input'"
          }
        ]
      }
    ]
  }
}
```

### File Protection Hook

Block edits to sensitive files:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "node -e \"const data = JSON.parse(require('fs').readFileSync(0, 'utf8')); const path = data.tool_input?.file_path || ''; process.exit(['.env', 'package-lock.json', '.git/'].some(p => path.includes(p)) ? 2 : 0)\""
          }
        ]
      }
    ]
  }
}
```

## Learn more

* For reference documentation on hooks, see [Hooks reference](/en/docs/claude-code/hooks).
* For comprehensive security best practices and safety guidelines, see [Security Considerations](/en/docs/claude-code/hooks#security-considerations) in the hooks reference documentation.
* For troubleshooting steps and debugging techniques, see [Debugging](/en/docs/claude-code/hooks#debugging) in the hooks reference
  documentation.
