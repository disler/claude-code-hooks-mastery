#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import { config } from 'dotenv';

config();

interface InputData {
    session_id: string;
    source: string;
}

async function logSessionStart(inputData: InputData): Promise<void> {
    /**Log session start event to logs directory.*/
    // Ensure logs directory exists
    const logDir = path.resolve('logs');
    await fs.mkdir(logDir, { recursive: true });
    const logFile = path.join(logDir, 'session_start.json');
    
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

async function getGitStatus(): Promise<[string | null, number | null]> {
    /**Get current git status information.*/
    try {
        // Get current branch
        const branchResult = await new Promise<{stdout: string, returncode: number}>((resolve) => {
            const proc = spawn('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { timeout: 5000 });
            let stdout = '';
            proc.stdout?.on('data', (data) => stdout += data.toString());
            proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
            proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
        });
        
        const currentBranch = branchResult.returncode === 0 ? branchResult.stdout.trim() : "unknown";
        
        // Get uncommitted changes count
        const statusResult = await new Promise<{stdout: string, returncode: number}>((resolve) => {
            const proc = spawn('git', ['status', '--porcelain'], { timeout: 5000 });
            let stdout = '';
            proc.stdout?.on('data', (data) => stdout += data.toString());
            proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
            proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
        });
        
        let uncommittedCount = 0;
        if (statusResult.returncode === 0) {
            const changes = statusResult.stdout.trim() ? statusResult.stdout.trim().split('\n') : [];
            uncommittedCount = changes.length;
        }
        
        return [currentBranch, uncommittedCount];
    } catch (error) {
        return [null, null];
    }
}

async function getRecentIssues(): Promise<string | null> {
    /**Get recent GitHub issues if gh CLI is available.*/
    try {
        // Check if gh is available
        const ghCheck = await new Promise<number>((resolve) => {
            const proc = spawn(process.platform === 'win32' ? 'where' : 'which', ['gh']);
            proc.on('close', (code) => resolve(code || 0));
            proc.on('error', () => resolve(1));
        });
        
        if (ghCheck !== 0) {
            return null;
        }
        
        // Get recent open issues
        const result = await new Promise<{stdout: string, returncode: number}>((resolve) => {
            const proc = spawn('gh', ['issue', 'list', '--limit', '5', '--state', 'open'], { timeout: 10000 });
            let stdout = '';
            proc.stdout?.on('data', (data) => stdout += data.toString());
            proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
            proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
        });
        
        if (result.returncode === 0 && result.stdout.trim()) {
            return result.stdout.trim();
        }
    } catch (error) {
        // Silently fail
    }
    return null;
}

async function loadDevelopmentContext(source: string): Promise<string> {
    /**Load relevant development context based on session source.*/
    const contextParts: string[] = [];
    
    // Add timestamp
    contextParts.push(`Session started at: ${new Date().toLocaleString()}`);
    contextParts.push(`Session source: ${source}`);
    
    // Add git information
    const [branch, changes] = await getGitStatus();
    if (branch) {
        contextParts.push(`Git branch: ${branch}`);
        if (changes && changes > 0) {
            contextParts.push(`Uncommitted changes: ${changes} files`);
        }
    }
    
    // Load project-specific context files if they exist
    const contextFiles = [
        ".claude/CONTEXT.md",
        ".claude/TODO.md",
        "TODO.md",
        ".github/ISSUE_TEMPLATE.md"
    ];
    
    for (const filePath of contextFiles) {
        try {
            const content = await fs.readFile(filePath, 'utf8');
            if (content.trim()) {
                contextParts.push(`\n--- Content from ${filePath} ---`);
                contextParts.push(content.trim().substring(0, 1000));  // Limit to first 1000 chars
            }
        } catch (error) {
            // File doesn't exist or can't be read, skip
        }
    }
    
    // Add recent issues if available
    const issues = await getRecentIssues();
    if (issues) {
        contextParts.push("\n--- Recent GitHub Issues ---");
        contextParts.push(issues);
    }
    
    return contextParts.join("\n");
}

async function main(): Promise<void> {
    try {
        // Parse command line arguments
        const args = process.argv.slice(2);
        const loadContext = args.includes('--load-context');
        const announce = args.includes('--announce');
        
        // Read JSON input from stdin
        let stdinData = '';
        if (process.stdin.isTTY) {
            // If no stdin, use default
            stdinData = JSON.stringify({ session_id: 'test', source: 'startup' });
        } else {
            // Read from stdin
            process.stdin.setEncoding('utf8');
            for await (const chunk of process.stdin) {
                stdinData += chunk;
            }
        }
        
        const inputData: InputData = JSON.parse(stdinData);
        
        // Extract fields
        const sessionId = inputData.session_id || 'unknown';
        const source = inputData.source || 'unknown';  // "startup", "resume", or "clear"
        
        // Log the session start event
        await logSessionStart(inputData);
        
        // Load development context if requested
        if (loadContext) {
            const context = await loadDevelopmentContext(source);
            if (context) {
                // Using JSON output to add context
                const output = {
                    hookSpecificOutput: {
                        hookEventName: "SessionStart",
                        additionalContext: context
                    }
                };
                console.log(JSON.stringify(output));
                process.exit(0);
            }
        }
        
        // Announce session start if requested
        if (announce) {
            try {
                // Try to use TTS to announce session start
                const scriptDir = path.dirname(process.argv[1]);
                const ttsScript = path.join(scriptDir, "utils", "tts", "pyttsx3_tts.ts");
                
                try {
                    await fs.access(ttsScript);
                    
                    const messages = {
                        "startup": "Claude Code session started",
                        "resume": "Resuming previous session",
                        "clear": "Starting fresh session"
                    } as const;
                    
                    const message = messages[source as keyof typeof messages] || "Session started";
                    
                    const proc = spawn("node", [ttsScript, message], { timeout: 5000 });
                    await new Promise((resolve) => {
                        proc.on('close', resolve);
                        proc.on('error', resolve);
                    });
                } catch (error) {
                    // TTS script doesn't exist or failed, silently continue
                }
            } catch (error) {
                // Silently fail
            }
        }
        
        // Success
        process.exit(0);
        
    } catch (error) {
        // Handle any errors gracefully
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => process.exit(0));
}