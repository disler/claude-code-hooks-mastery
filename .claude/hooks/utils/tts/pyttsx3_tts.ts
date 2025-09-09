#!/usr/bin/env node

import { spawn } from 'child_process';
import * as process from 'process';

export async function speak(text: string): Promise<void> {
    return new Promise((resolve, reject) => {
        let command: string;
        let args: string[];

        // Use platform-specific TTS commands
        if (process.platform === 'win32') {
            // Windows: use PowerShell with System.Speech.Synthesis
            command = 'powershell';
            args = [
                '-c',
                `Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Rate = 2; $speak.Volume = 80; $speak.Speak("${text.replace(/"/g, '""')}")`
            ];
        } else if (process.platform === 'darwin') {
            // macOS: use built-in say command
            command = 'say';
            args = ['-r', '180', text]; // Set rate to 180 words per minute
        } else {
            // Linux: try espeak or festival
            command = 'espeak';
            args = ['-s', '180', text]; // Set speed to 180 words per minute
        }

        const tts = spawn(command, args, { stdio: 'pipe' });

        tts.on('close', (code) => {
            if (code === 0) {
                resolve();
            } else {
                reject(new Error(`TTS process exited with code ${code}`));
            }
        });

        tts.on('error', (error) => {
            reject(error);
        });
    });
}

async function main() {
    /**
     * Platform-native TTS Script
     * 
     * Uses platform-specific text-to-speech engines for offline synthesis.
     * Accepts optional text prompt as command-line argument.
     * 
     * Usage:
     * - node pyttsx3_tts.ts                    # Uses default text
     * - node pyttsx3_tts.ts "Your custom text" # Uses provided text
     * 
     * Features:
     * - Offline TTS (no API key required)
     * - Cross-platform compatibility
     * - Configurable voice settings
     * - Immediate audio playback
     */
    
    console.log("🎙️  Platform Native TTS");
    console.log("=" + "=".repeat(15));
    
    // Get text from command line argument or use default
    const args = process.argv.slice(2);
    let text: string;
    
    if (args.length > 0) {
        text = args.join(" ");  // Join all arguments as text
    } else {
        // Default completion messages
        const completionMessages = [
            "Work complete!",
            "All done!",
            "Task finished!",
            "Job complete!",
            "Ready for next task!"
        ];
        text = completionMessages[Math.floor(Math.random() * completionMessages.length)];
    }
    
    console.log(`🎯 Text: ${text}`);
    console.log("🔊 Speaking...");
    
    try {
        await speak(text);
        console.log("✅ Playback complete!");
    } catch (error) {
        console.error(`❌ Error: ${error}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(console.error);
}