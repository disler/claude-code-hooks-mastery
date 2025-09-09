#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import { config } from 'dotenv';

config();

interface InputData {
    session_id: string;
    prompt: string;
}

async function logUserPrompt(sessionId: string, inputData: InputData): Promise<void> {
    /**Log user prompt to logs directory.*/
    // Ensure logs directory exists
    const logDir = path.resolve('logs');
    await fs.mkdir(logDir, { recursive: true });
    const logFile = path.join(logDir, 'user_prompt_submit.json');
    
    // Read existing log data or initialize empty list
    let logData: any[] = [];
    try {
        const data = await fs.readFile(logFile, 'utf8');
        logData = JSON.parse(data);
    } catch (error) {
        // File doesn't exist or invalid JSON, use empty array
        logData = [];
    }
    
    // Append the entire input data
    logData.push(inputData);
    
    // Write back to file with formatting
    await fs.writeFile(logFile, JSON.stringify(logData, null, 2));
}

async function manageSessionData(sessionId: string, prompt: string, nameAgent: boolean = false): Promise<void> {
    /**Manage session data in the new JSON structure.*/
    // Ensure sessions directory exists
    const sessionsDir = path.resolve('.claude', 'data', 'sessions');
    await fs.mkdir(sessionsDir, { recursive: true });
    
    // Load or create session file
    const sessionFile = path.join(sessionsDir, `${sessionId}.json`);
    
    let sessionData: any;
    try {
        const data = await fs.readFile(sessionFile, 'utf8');
        sessionData = JSON.parse(data);
    } catch (error) {
        sessionData = { session_id: sessionId, prompts: [] };
    }
    
    // Add the new prompt
    sessionData.prompts.push(prompt);
    
    // Generate agent name if requested and not already present
    if (nameAgent && !sessionData.agent_name) {
        // Try Ollama first (preferred)
        try {
            const result = await new Promise<{stdout: string, returncode: number}>((resolve) => {
                const proc = spawn("node", [path.resolve(".claude/hooks/utils/llm/ollama.ts"), "--agent-name"], { timeout: 5000 });
                let stdout = '';
                proc.stdout?.on('data', (data) => stdout += data.toString());
                proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
                proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
            });
            
            if (result.returncode === 0 && result.stdout.trim()) {
                const agentName = result.stdout.trim();
                // Check if it's a valid name (not an error message)
                if (agentName.split(/\s+/).length === 1 && /^[a-zA-Z0-9]+$/.test(agentName)) {
                    sessionData.agent_name = agentName;
                } else {
                    throw new Error("Invalid name from Ollama");
                }
            } else {
                throw new Error("Ollama failed");
            }
        } catch (error) {
            // Fall back to Anthropic if Ollama fails
            try {
                const result = await new Promise<{stdout: string, returncode: number}>((resolve) => {
                    const proc = spawn("node", [path.resolve(".claude/hooks/utils/llm/anth.ts"), "--agent-name"], { timeout: 10000 });
                    let stdout = '';
                    proc.stdout?.on('data', (data) => stdout += data.toString());
                    proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
                    proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
                });
                
                if (result.returncode === 0 && result.stdout.trim()) {
                    const agentName = result.stdout.trim();
                    // Validate the name
                    if (agentName.split(/\s+/).length === 1 && /^[a-zA-Z0-9]+$/.test(agentName)) {
                        sessionData.agent_name = agentName;
                    }
                }
            } catch (error) {
                // If both fail, don't block the prompt
            }
        }
    }
    
    // Save the updated session data
    try {
        await fs.writeFile(sessionFile, JSON.stringify(sessionData, null, 2));
    } catch (error) {
        // Silently fail if we can't write the file
    }
}

function validatePrompt(prompt: string): [boolean, string | null] {
    /**
     * Validate the user prompt for security or policy violations.
     * Returns tuple (is_valid, reason).
     */
    // Example validation rules (customize as needed)
    const blockedPatterns: Array<[string, string]> = [
        // Add any patterns you want to block
        // Example: ['rm -rf /', 'Dangerous command detected'],
    ];
    
    const promptLower = prompt.toLowerCase();
    
    for (const [pattern, reason] of blockedPatterns) {
        if (promptLower.includes(pattern.toLowerCase())) {
            return [false, reason];
        }
    }
    
    return [true, null];
}

async function main(): Promise<void> {
    try {
        // Parse command line arguments
        const args = process.argv.slice(2);
        const validate = args.includes('--validate');
        const logOnly = args.includes('--log-only');
        const storeLastPrompt = args.includes('--store-last-prompt');
        const nameAgent = args.includes('--name-agent');
        
        // Read JSON input from stdin
        let stdinData = '';
        if (process.stdin.isTTY) {
            // If no stdin, use default for testing
            stdinData = JSON.stringify({ session_id: 'test', prompt: 'test prompt' });
        } else {
            // Read from stdin
            process.stdin.setEncoding('utf8');
            for await (const chunk of process.stdin) {
                stdinData += chunk;
            }
        }
        
        const inputData: InputData = JSON.parse(stdinData);
        
        // Extract session_id and prompt
        const sessionId = inputData.session_id || 'unknown';
        const prompt = inputData.prompt || '';
        
        // Log the user prompt
        await logUserPrompt(sessionId, inputData);
        
        // Manage session data with JSON structure
        if (storeLastPrompt || nameAgent) {
            await manageSessionData(sessionId, prompt, nameAgent);
        }
        
        // Validate prompt if requested and not in log-only mode
        if (validate && !logOnly) {
            const [isValid, reason] = validatePrompt(prompt);
            if (!isValid) {
                // Exit code 2 blocks the prompt with error message
                console.error(`Prompt blocked: ${reason}`);
                process.exit(2);
            }
        }
        
        // Add context information (optional)
        // You can print additional context that will be added to the prompt
        // Example: console.log(`Current time: ${new Date()}`);
        
        // Success - prompt will be processed
        process.exit(0);
        
    } catch (error) {
        // Handle any errors gracefully
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => process.exit(0));
}