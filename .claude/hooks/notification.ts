#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';
import { config } from 'dotenv';
import { NotificationData, NotificationLog, TTSProvider, TTSRequest, HookExitCode } from './types';

config();

async function main(): Promise<void> {
    try {
        // Read JSON input from stdin
        let stdinData = '';
        if (process.stdin.isTTY) {
            stdinData = JSON.stringify({ message: 'test notification', type: 'info' });
        } else {
            process.stdin.setEncoding('utf8');
            for await (const chunk of process.stdin) {
                stdinData += chunk;
            }
        }
        
        const inputData: NotificationData = JSON.parse(stdinData);
        
        // Ensure log directory exists
        const logDir = path.resolve('logs');
        await fs.mkdir(logDir, { recursive: true });
        const logPath = path.join(logDir, 'notification.json');
        
        // Read existing log data or initialize empty list
        let logData: NotificationLog[] = [];
        try {
            const data = await fs.readFile(logPath, 'utf8');
            logData = JSON.parse(data);
        } catch (error) {
            logData = [];
        }
        
        // Create log entry
        const logEntry: NotificationLog = {
            timestamp: new Date().toISOString(),
            session_id: inputData.session_id,
            type: 'notification',
            data: inputData
        };
        
        // Append new data
        logData.push(logEntry);
        
        // Write back to file with formatting
        await fs.writeFile(logPath, JSON.stringify(logData, null, 2));
        
        // Check if TTS is requested via environment or config
        const enableTTS = process.env.ENABLE_NOTIFICATION_TTS === 'true' || 
                         process.argv.includes('--tts');
        
        if (enableTTS && inputData.message) {
            await speakNotification(inputData);
        }
        
        process.exit(0);
        
    } catch (error) {
        process.exit(0);
    }
}

async function speakNotification(data: NotificationData): Promise<void> {
    /**
     * Speak notification using available TTS provider.
     * Tries providers in order: ElevenLabs, OpenAI, pyttsx3
     */
    const message = formatNotificationForSpeech(data);
    
    // Try ElevenLabs first
    if (process.env.ELEVENLABS_API_KEY) {
        try {
            const result = await runTTSCommand(
                path.resolve('.claude/hooks/utils/tts/elevenlabs_tts.ts'),
                message
            );
            if (result.success) return;
        } catch (error) {
            // Fall through to next provider
        }
    }
    
    // Try OpenAI TTS
    if (process.env.OPENAI_API_KEY) {
        try {
            const result = await runTTSCommand(
                path.resolve('.claude/hooks/utils/tts/openai_tts.ts'),
                message
            );
            if (result.success) return;
        } catch (error) {
            // Fall through to next provider
        }
    }
    
    // Try pyttsx3 as fallback (no API key needed)
    try {
        const result = await runTTSCommand(
            path.resolve('.claude/hooks/utils/tts/pyttsx3_tts.ts'),
            message
        );
        if (result.success) return;
    } catch (error) {
        // All providers failed, silently continue
    }
}

function formatNotificationForSpeech(data: NotificationData): string {
    /**
     * Format notification for natural speech output.
     */
    const typePrefix = {
        'info': 'Information',
        'warning': 'Warning',
        'error': 'Error',
        'success': 'Success'
    };
    
    const prefix = typePrefix[data.type] || 'Notification';
    return `${prefix}: ${data.message}`;
}

async function runTTSCommand(
    scriptPath: string,
    text: string
): Promise<{ success: boolean; error?: string }> {
    /**
     * Run TTS script as subprocess.
     */
    return new Promise((resolve) => {
        const proc = spawn('node', [scriptPath, text], {
            stdio: ['ignore', 'pipe', 'pipe'],
            timeout: 10000
        });
        
        let stdout = '';
        let stderr = '';
        
        proc.stdout?.on('data', (data) => stdout += data.toString());
        proc.stderr?.on('data', (data) => stderr += data.toString());
        
        proc.on('close', (code) => {
            resolve({
                success: code === 0,
                error: code !== 0 ? stderr || 'TTS command failed' : undefined
            });
        });
        
        proc.on('error', (error) => {
            resolve({
                success: false,
                error: error.message
            });
        });
    });
}

if (require.main === module) {
    main().catch(() => process.exit(0));
}