# UserPromptSubmit Hook Documentation

The UserPromptSubmit hook is a powerful lifecycle event in Claude Code that fires immediately when a user submits a prompt, before Claude processes it. This hook provides the ability to log, validate, modify, or even block user prompts based on custom criteria.

## Overview

**Hook Name:** `UserPromptSubmit`  
**Fires:** Immediately when a user submits a prompt to Claude Code  
**Can Block:** Yes (exit code 2 with stderr message)  
**Primary Use Cases:** Prompt logging, validation, security filtering, context injection  

## JSON Payload Structure

The UserPromptSubmit hook receives the following JSON payload via stdin:

```json
{
  "hook_event_type": "UserPromptSubmit",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "prompt": "The user's submitted prompt text",
  "timestamp": "2024-01-20T15:30:45.123Z",
  "context": {
    "working_directory": "/path/to/project",
    "git_status": "clean",
    "platform": "darwin"
  }
}
```

### Payload Fields

- **hook_event_type**: Always "UserPromptSubmit" for this hook
- **session_id**: Unique identifier for the Claude Code session
- **prompt**: The exact text the user submitted
- **timestamp**: ISO 8601 timestamp of when the prompt was submitted
- **context**: Additional context about the environment

## Hook Capabilities

### 1. Logging and Auditing

The most basic use case is logging all user prompts for auditing purposes:

```typescript
// Log user prompt to session directory
const logDir = ensureSessionLogDir(sessionId);
const logFile = path.join(logDir, 'user_prompt_submit.json');

// Append to existing log
logData.push(inputData);
fs.writeFileSync(logFile, JSON.stringify(logData, null, 2));
```

### 2. Prompt Validation and Blocking

The hook can validate prompts and block them if they violate policies:

```typescript
function validatePrompt(prompt: (message?: string, _default?: string) => (string | null)): {
    isValid: boolean;
    reason?: string
} {
    // Validate the user prompt for security or policy violations
    const blockedPatterns = [
        ['sudo rm -rf /', 'Dangerous command detected'],
        ['delete all', 'Overly broad deletion request'],
        ['api_key', 'Potential secret exposure risk']
    ];
    
    const promptLower = new toString()prompt;
    
    for (const [pattern, reason] of blockedPatterns) {
        if (promptLower.includes(pattern.toLowerCase())) {
            return { isValid: false, reason };
        }
    }
    
    return { isValid: true };
}

// In main():
const { isValid, reason } = validatePrompt(prompt);
if (!isValid) {
    console.error(`Prompt blocked: ${reason}`);
}
}

}



    
```

### 3. Context Injection

The hook can print additional context that gets prepended to the user's prompt:

```typescript
// Add context information that will be included in the prompt
console.log(`Project: ${projectName}`);
console.log(`Current branch: ${gitBranch}`);
console.log(`Time: ${new Date().toISOString()}`);
```

### 4. Prompt Modification

While the hook cannot directly modify the prompt text, it can provide additional context that effectively changes what Claude sees:

```typescript
// Example: Add coding standards reminder
if (prompt.toLowerCase().includes("write code")) {
    console.log("Remember: Follow TypeScript best practices and include proper type annotations");
}
```

## Exit Codes and Flow Control

The UserPromptSubmit hook follows standard Claude Code hook exit code conventions:

| Exit Code | Behavior | Use Case |
|-----------|----------|----------|
| 0 | Success | Prompt is processed normally, stdout content is added as context |
| 2 | Block | Prompt is blocked, stderr message shown to user |
| Other | Non-blocking Error | Error shown to user, prompt still processed |

## Advanced JSON Output Control

Beyond simple exit codes, UserPromptSubmit can return structured JSON:

```json
{
  "decision": "block" | "approve" | undefined,
  "reason": "Explanation for the decision",
  "context": "Additional context to prepend to prompt",
  "suppressOutput": true | false
}
```

- **decision: "block"** - Prevents prompt processing, shows reason to user
- **decision: "approve"** - Explicitly allows prompt (useful for allowlisting)
- **context** - Text to prepend to the user's prompt
- **suppressOutput** - Hide stdout from being added to prompt

## Implementation Examples

### Example 1: Basic Logging

```typescript
#!/usr/bin/env npx ts-node

import * as fs from 'fs';
import * as path from 'path';

// Read input
const input = fs.readFileSync(0, 'utf-8');
const inputData = JSON.parse(input);
const sessionId = inputData.session_id || 'unknown';
const prompt = inputData.prompt || '';

// Log to file
const logDir = path.join('logs', sessionId);
fs.mkdirSync(logDir, { recursive: true });
const logFile = path.join(logDir, 'user_prompts.json');

// Append prompt
let prompts: any[] = [];
if (fs.existsSync(logFile)) {
    const content = fs.readFileSync(logFile, 'utf-8');
    prompts = JSON.parse(content);
}

prompts.push({
    timestamp: inputData.timestamp,
    prompt: prompt
});

fs.writeFileSync(logFile, JSON.stringify(prompts, null, 2));
process.exit(0);
```

### Example 2: Security Validation

```typescript
#!/usr/bin/env npx ts-node

import * as fs from 'fs';

// Security patterns to block
const DANGEROUS_PATTERNS = [
    [/rm\s+-rf\s+\//, 'Dangerous system deletion command'],
    [/curl.*\|\s*sh/, 'Unsafe remote script execution'],
    [/eval\s*\(/, 'Unsafe code evaluation'],
    [/export\s+.*KEY/, 'Potential credential exposure'],
] as const;

const input = fs.readFileSync(0, 'utf-8');
const inputData = JSON.parse(input);
const prompt = inputData.prompt || '';

// Check for dangerous patterns
for (const [pattern, reason] of DANGEROUS_PATTERNS) {
    if (pattern.test(prompt)) {
        console.error(`Security Policy Violation: ${reason}`);
        process.exit(2); // Block the prompt
    }
}

process.exit(0);
```

### Example 3: Context Enhancement

```typescript
#!/usr/bin/env npx ts-node

import * as fs from 'fs';
import * as dotenv from 'dotenv';

dotenv.config();

const input = fs.readFileSync(0, 'utf-8');
const inputData = JSON.parse(input);
const prompt = inputData.prompt || '';

// Add project context for coding requests
const codingKeywords = ['code', 'implement', 'function', 'class'];
if (codingKeywords.some(keyword => prompt.toLowerCase().includes(keyword))) {
    const projectName = process.env.PROJECT_NAME || 'Unknown Project';
    const codingStandards = process.env.CODING_STANDARDS || 'Follow best practices';
    
    console.log(`Project: ${projectName}`);
    console.log(`Standards: ${codingStandards}`);
    console.log(`Generated at: ${new Date().toISOString()}`);
    console.log("---"); // Separator
}

process.exit(0);
```

### Example 4: Intelligent Prompt Analysis

```typescript
#!/usr/bin/env npx ts-node

import * as fs from 'fs';
import * as dotenv from 'dotenv';
import Anthropic from '@anthropic-ai/sdk';

dotenv.config();

async function analyzePromptIntent(prompt: string) {
    // Use LLM to analyze prompt intent and risks
    const client = new Anthropic({
        apiKey: process.env.ANTHROPIC_API_KEY
    });
    
    const analysisPrompt = `Analyze this user prompt for potential risks or policy violations:
    
    Prompt: "${prompt}"
    
    Respond with JSON containing:
    - risk_level: "low", "medium", or "high"
    - concerns: list of specific concerns
    - recommendation: "allow", "block", or "warn"
    `;
    
    const response = await client.messages.create({
        model: "claude-3-5-haiku-20241022",
        max_tokens: 200,
        messages: [{ role: "user", content: analysisPrompt }]
    });
    
    return JSON.parse(response.content[0].text);
}

const input = fs.readFileSync(0, 'utf-8');
const inputData = JSON.parse(input);
const prompt = inputData.prompt || '';

// Analyze prompt
analyzePromptIntent(prompt).then(analysis => {
    if (analysis.recommendation === 'block') {
        console.error(`Blocked: ${analysis.concerns.join(', ')}`);
        process.exit(2);
    } else if (analysis.recommendation === 'warn') {
        // Add warning as context
        console.log(`⚠️  Caution: ${analysis.concerns.join(', ')}`);
        console.log("Please ensure you understand the implications.");
        console.log("---");
    }
    
    process.exit(0);
});
```

## Configuration Options

The UserPromptSubmit hook in this codebase supports several command-line flags:

- **--validate**: Enable prompt validation against security patterns
- **--log-only**: Only log prompts without any validation or blocking
- **--summarize**: Generate AI summaries of prompts (when integrated with observability)

Example configuration in `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "npx ts-node .claude/hooks/user_prompt_submit.ts --log-only"
          },
          {
            "type": "command",
            "command": "npx ts-node .claude/hooks/send_event.ts --source-app my-app --event-type UserPromptSubmit --summarize"
          }
        ]
      }
    ]
  }
}
```

## Best Practices

1. **Fast Execution**: Keep processing minimal as this runs on every prompt
2. **Clear Messages**: When blocking, provide clear reasons to the user
3. **Fail Open**: On errors, exit with code 0 to avoid blocking legitimate work
4. **Privacy**: Be mindful of logging sensitive information
5. **Context Relevance**: Only add context that's relevant to the prompt

## Integration with Other Hooks

UserPromptSubmit often works in conjunction with other hooks:

- **PreToolUse**: UserPromptSubmit can set context that influences tool blocking
- **Stop**: Can verify that requested tasks in the prompt were completed
- **Notification**: Can trigger custom notifications based on prompt content

## Security Considerations

1. **Input Sanitization**: Always validate and sanitize prompt content
2. **Log Rotation**: Implement log rotation to prevent unbounded growth
3. **Sensitive Data**: Consider redacting sensitive information in logs
4. **Rate Limiting**: Consider implementing rate limiting for repeated prompts

## Troubleshooting

Common issues and solutions:

1. **Hook Not Firing**: Ensure the hook is properly configured in settings.json
2. **Blocking Not Working**: Verify you're using exit code 2 with stderr
3. **Context Not Added**: Ensure you're printing to stdout, not stderr
4. **JSON Errors**: Always handle JSON parsing errors gracefully

## Summary

The UserPromptSubmit hook provides a powerful interception point for:
- Logging all user interactions
- Enforcing security policies
- Adding contextual information
- Preventing dangerous operations
- Analyzing prompt patterns

When combined with other Claude Code hooks, it forms a comprehensive system for controlling and monitoring AI assistant behavior.