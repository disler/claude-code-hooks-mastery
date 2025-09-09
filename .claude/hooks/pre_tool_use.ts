#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';

interface InputData {
    tool_name: string;
    tool_input: Record<string, any>;
}

function isDangerousRmCommand(command: string): boolean {
    /**
     * Comprehensive detection of dangerous rm commands.
     * Matches various forms of rm -rf and similar destructive patterns.
     */
    // Normalize command by removing extra spaces and converting to lowercase
    const normalized = command.toLowerCase().replace(/\s+/g, ' ');
    
    // Pattern 1: Standard rm -rf variations
    const patterns = [
        /\brm\s+.*-[a-z]*r[a-z]*f/,  // rm -rf, rm -fr, rm -Rf, etc.
        /\brm\s+.*-[a-z]*f[a-z]*r/,  // rm -fr variations
        /\brm\s+--recursive\s+--force/,  // rm --recursive --force
        /\brm\s+--force\s+--recursive/,  // rm --force --recursive
        /\brm\s+-r\s+.*-f/,  // rm -r ... -f
        /\brm\s+-f\s+.*-r/,  // rm -f ... -r
    ];
    
    // Check for dangerous patterns
    for (const pattern of patterns) {
        if (pattern.test(normalized)) {
            return true;
        }
    }
    
    // Pattern 2: Check for rm with recursive flag targeting dangerous paths
    const dangerousPaths = [
        /\//,           // Root directory
        /\/\*/,         // Root with wildcard
        /~/,            // Home directory
        /~\//,          // Home directory path
        /\$HOME/,       // Home environment variable
        /\.\./,         // Parent directory references
        /\*/,           // Wildcards in general rm -rf context
        /\./,           // Current directory
        /\.\s*$/,       // Current directory at end of command
    ];
    
    if (/\brm\s+.*-[a-z]*r/.test(normalized)) {  // If rm has recursive flag
        for (const pathPattern of dangerousPaths) {
            if (pathPattern.test(normalized)) {
                return true;
            }
        }
    }
    
    return false;
}

function isEnvFileAccess(toolName: string, toolInput: Record<string, any>): boolean {
    /**
     * Check if any tool is trying to access .env files containing sensitive data.
     */
    if (['Read', 'Edit', 'MultiEdit', 'Write', 'Bash'].includes(toolName)) {
        // Check file paths for file-based tools
        if (['Read', 'Edit', 'MultiEdit', 'Write'].includes(toolName)) {
            const filePath = toolInput.file_path || '';
            if (filePath.includes('.env') && !filePath.endsWith('.env.sample')) {
                return true;
            }
        }
        
        // Check bash commands for .env file access
        else if (toolName === 'Bash') {
            const command = toolInput.command || '';
            // Pattern to detect .env file access (but allow .env.sample)
            const envPatterns = [
                /\b\.env\b(?!\.sample)/,  // .env but not .env.sample
                /cat\s+.*\.env\b(?!\.sample)/,  // cat .env
                /echo\s+.*>\s*\.env\b(?!\.sample)/,  // echo > .env
                /touch\s+.*\.env\b(?!\.sample)/,  // touch .env
                /cp\s+.*\.env\b(?!\.sample)/,  // cp .env
                /mv\s+.*\.env\b(?!\.sample)/,  // mv .env
            ];
            
            for (const pattern of envPatterns) {
                if (pattern.test(command)) {
                    return true;
                }
            }
        }
    }
    
    return false;
}

async function main(): Promise<void> {
    try {
        // Read JSON input from stdin
        let stdinData = '';
        if (process.stdin.isTTY) {
            // If no stdin, use default for testing
            stdinData = JSON.stringify({ tool_name: 'test', tool_input: {} });
        } else {
            // Read from stdin
            process.stdin.setEncoding('utf8');
            for await (const chunk of process.stdin) {
                stdinData += chunk;
            }
        }
        
        const inputData: InputData = JSON.parse(stdinData);
        
        const toolName = inputData.tool_name || '';
        const toolInput = inputData.tool_input || {};
        
        // Check for .env file access (blocks access to sensitive environment files)
        if (isEnvFileAccess(toolName, toolInput)) {
            console.error("BLOCKED: Access to .env files containing sensitive data is prohibited");
            console.error("Use .env.sample for template files instead");
            process.exit(2);  // Exit code 2 blocks tool call and shows error to Claude
        }
        
        // Check for dangerous rm -rf commands
        if (toolName === 'Bash') {
            const command = toolInput.command || '';
            
            // Block rm -rf commands with comprehensive pattern matching
            if (isDangerousRmCommand(command)) {
                console.error("BLOCKED: Dangerous rm command detected and prevented");
                process.exit(2);  // Exit code 2 blocks tool call and shows error to Claude
            }
        }
        
        // Ensure log directory exists
        const logDir = path.resolve('logs');
        await fs.mkdir(logDir, { recursive: true });
        const logPath = path.join(logDir, 'pre_tool_use.json');
        
        // Read existing log data or initialize empty list
        let logData: any[] = [];
        try {
            const data = await fs.readFile(logPath, 'utf8');
            logData = JSON.parse(data);
        } catch (error) {
            logData = [];
        }
        
        // Append new data
        logData.push(inputData);
        
        // Write back to file with formatting
        await fs.writeFile(logPath, JSON.stringify(logData, null, 2));
        
        process.exit(0);
        
    } catch (error) {
        // Handle any errors gracefully
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => process.exit(0));
}