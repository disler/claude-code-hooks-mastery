#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import { config } from 'dotenv';

config();

interface InputData {
    session_id: string;
    stop_hook_active: boolean;
    transcript_path?: string;
}

function getCompletionMessages(): string[] {
    /**Return list of friendly completion messages.*/
    return [
        "Work complete!",
        "All done!",
        "Task finished!",
        "Job complete!",
        "Ready for next task!"
    ];
}

async function getTtsScriptPath(): Promise<string | null> {
    /**
     * Determine which TTS script to use based on available API keys.
     * Priority order: ElevenLabs > OpenAI > pyttsx3
     */
    // Get current script directory and construct utils/tts path
    const scriptDir = path.dirname(process.argv[1]);
    const ttsDir = path.join(scriptDir, "utils", "tts");
    
    // Check for ElevenLabs API key (highest priority)
    if (process.env.ELEVENLABS_API_KEY) {
        const elevenlabsScript = path.join(ttsDir, "elevenlabs_tts.ts");
        try {
            await fs.access(elevenlabsScript);
            return elevenlabsScript;
        } catch {}
    }
    
    // Check for OpenAI API key (second priority)
    if (process.env.OPENAI_API_KEY) {
        const openaiScript = path.join(ttsDir, "openai_tts.ts");
        try {
            await fs.access(openaiScript);
            return openaiScript;
        } catch {}
    }
    
    // Fall back to pyttsx3 (no API key required)
    const pyttsx3Script = path.join(ttsDir, "pyttsx3_tts.ts");
    try {
        await fs.access(pyttsx3Script);
        return pyttsx3Script;
    } catch {}
    
    return null;
}

async function getLlmCompletionMessage(): Promise<string> {
    /**
     * Generate completion message using available LLM services.
     * Priority order: OpenAI > Anthropic > Ollama > fallback to random message
     * 
     * Returns:
     *     Generated or fallback completion message
     */
    // Get current script directory and construct utils/llm path
    const scriptDir = path.dirname(process.argv[1]);
    const llmDir = path.join(scriptDir, "utils", "llm");
    
    // Try OpenAI first (highest priority)
    if (process.env.OPENAI_API_KEY) {
        const oaiScript = path.join(llmDir, "oai.ts");
        try {
            await fs.access(oaiScript);
            
            const result = await new Promise<{stdout: string, returncode: number}>((resolve) => {
                const proc = spawn("node", [oaiScript, "--completion"], { timeout: 10000 });
                let stdout = '';
                proc.stdout?.on('data', (data) => stdout += data.toString());
                proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
                proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
            });
            
            if (result.returncode === 0 && result.stdout.trim()) {
                return result.stdout.trim();
            }
        } catch {}
    }
    
    // Try Anthropic second
    if (process.env.ANTHROPIC_API_KEY) {
        const anthScript = path.join(llmDir, "anth.ts");
        try {
            await fs.access(anthScript);
            
            const result = await new Promise<{stdout: string, returncode: number}>((resolve) => {
                const proc = spawn("node", [anthScript, "--completion"], { timeout: 10000 });
                let stdout = '';
                proc.stdout?.on('data', (data) => stdout += data.toString());
                proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
                proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
            });
            
            if (result.returncode === 0 && result.stdout.trim()) {
                return result.stdout.trim();
            }
        } catch {}
    }
    
    // Try Ollama third (local LLM)
    const ollamaScript = path.join(llmDir, "ollama.ts");
    try {
        await fs.access(ollamaScript);
        
        const result = await new Promise<{stdout: string, returncode: number}>((resolve) => {
            const proc = spawn("node", [ollamaScript, "--completion"], { timeout: 10000 });
            let stdout = '';
            proc.stdout?.on('data', (data) => stdout += data.toString());
            proc.on('close', (code) => resolve({ stdout, returncode: code || 0 }));
            proc.on('error', () => resolve({ stdout: '', returncode: 1 }));
        });
        
        if (result.returncode === 0 && result.stdout.trim()) {
            return result.stdout.trim();
        }
    } catch {}
    
    // Fallback to random predefined message
    const messages = getCompletionMessages();
    return messages[Math.floor(Math.random() * messages.length)];
}

async function announceCompletion(): Promise<void> {
    /**Announce completion using the best available TTS service.*/
    try {
        const ttsScript = await getTtsScriptPath();
        if (!ttsScript) {
            return;  // No TTS scripts available
        }
        
        // Get completion message (LLM-generated or fallback)
        const completionMessage = await getLlmCompletionMessage();
        
        // Call the TTS script with the completion message
        const proc = spawn("node", [ttsScript, completionMessage], { 
            stdio: 'ignore',  // Suppress output
            timeout: 10000   // 10-second timeout
        });
        
        await new Promise<void>((resolve) => {
            proc.on('close', () => resolve());
            proc.on('error', () => resolve()); // Fail silently
            
            // Timeout fallback
            setTimeout(() => {
                proc.kill();
                resolve();
            }, 10000);
        });
        
    } catch (error) {
        // Fail silently for any errors
    }
}

async function main(): Promise<void> {
    try {
        // Parse command line arguments
        const args = process.argv.slice(2);
        const chat = args.includes('--chat');
        const notify = args.includes('--notify');
        
        // Read JSON input from stdin
        let stdinData = '';
        if (process.stdin.isTTY) {
            // If no stdin, use default for testing
            stdinData = JSON.stringify({ session_id: 'test', stop_hook_active: false });
        } else {
            // Read from stdin
            process.stdin.setEncoding('utf8');
            for await (const chunk of process.stdin) {
                stdinData += chunk;
            }
        }
        
        const inputData: InputData = JSON.parse(stdinData);
        
        // Extract required fields
        const sessionId = inputData.session_id || "";
        const stopHookActive = inputData.stop_hook_active || false;
        
        // Ensure log directory exists
        const logDir = path.resolve("logs");
        await fs.mkdir(logDir, { recursive: true });
        const logPath = path.join(logDir, "stop.json");
        
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
        
        // Handle --chat switch
        if (chat && inputData.transcript_path) {
            const transcriptPath = inputData.transcript_path;
            try {
                await fs.access(transcriptPath);
                
                // Read .jsonl file and convert to JSON array
                const chatData: any[] = [];
                const fileContent = await fs.readFile(transcriptPath, 'utf8');
                const lines = fileContent.split('\n');
                
                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (trimmedLine) {
                        try {
                            chatData.push(JSON.parse(trimmedLine));
                        } catch {
                            // Skip invalid lines
                        }
                    }
                }
                
                // Write to logs/chat.json
                const chatFile = path.join(logDir, 'chat.json');
                await fs.writeFile(chatFile, JSON.stringify(chatData, null, 2));
            } catch (error) {
                // Fail silently
            }
        }
        
        // Announce completion via TTS (only if --notify flag is set)
        if (notify) {
            await announceCompletion();
        }
        
        process.exit(0);
        
    } catch (error) {
        // Handle any errors gracefully
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => process.exit(0));
}