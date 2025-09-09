#!/usr/bin/env node

import OpenAI from 'openai';
import { config } from 'dotenv';
import * as process from 'process';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import * as os from 'os';

config();

async function playAudio(audioBuffer: Buffer): Promise<void> {
    // Create temporary file
    const tempFile = path.join(os.tmpdir(), `openai_tts_${Date.now()}.mp3`);
    
    try {
        // Write audio to temporary file
        await fs.writeFile(tempFile, audioBuffer);
        
        // Play audio based on platform
        let command: string;
        let args: string[];
        
        if (process.platform === 'win32') {
            // Windows: use powershell with Add-Type for media player
            command = 'powershell';
            args = ['-c', `(New-Object Media.SoundPlayer "${tempFile}").PlaySync()`];
        } else if (process.platform === 'darwin') {
            // macOS: use afplay
            command = 'afplay';
            args = [tempFile];
        } else {
            // Linux: try common players
            command = 'aplay';
            args = [tempFile];
        }
        
        const player = spawn(command, args, { stdio: 'ignore' });
        
        return new Promise((resolve, reject) => {
            player.on('close', (code) => {
                fs.unlink(tempFile).catch(() => {}); // Clean up, ignore errors
                if (code === 0) {
                    resolve();
                } else {
                    reject(new Error(`Audio player exited with code ${code}`));
                }
            });
            
            player.on('error', (error) => {
                fs.unlink(tempFile).catch(() => {}); // Clean up, ignore errors
                reject(error);
            });
        });
    } catch (error) {
        // Clean up on error
        try {
            await fs.unlink(tempFile);
        } catch {}
        throw error;
    }
}

export async function textToSpeech(text: string): Promise<Buffer | null> {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
        return null;
    }

    try {
        const client = new OpenAI({ apiKey });

        const response = await client.audio.speech.create({
            model: "tts-1",  // OpenAI TTS model
            voice: "nova",
            input: text,
            response_format: "mp3",
        });

        return Buffer.from(await response.arrayBuffer());
    } catch (error) {
        console.error(`Error generating audio: ${error}`);
        return null;
    }
}

async function main() {
    /**
     * OpenAI TTS Script
     *
     * Uses OpenAI's TTS model for high-quality text-to-speech.
     * Accepts optional text prompt as command-line argument.
     *
     * Usage:
     * - node openai_tts.ts                    # Uses default text
     * - node openai_tts.ts "Your custom text" # Uses provided text
     *
     * Features:
     * - OpenAI TTS-1 model
     * - Nova voice (engaging and warm)
     * - MP3 format audio output
     * - Cross-platform audio playback
     */

    // Get API key from environment
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
        console.error("❌ Error: OPENAI_API_KEY not found in environment variables");
        console.error("Please add your OpenAI API key to .env file:");
        console.error("OPENAI_API_KEY=your_api_key_here");
        process.exit(1);
    }

    console.log("🎙️  OpenAI TTS");
    console.log("=" + "=".repeat(20));

    // Get text from command line argument or use default
    const args = process.argv.slice(2);
    const text = args.length > 0
        ? args.join(" ")  // Join all arguments as text
        : "Today is a wonderful day to build something people love!";

    console.log(`🎯 Text: ${text}`);
    console.log("🔊 Generating and playing...");

    try {
        // Generate audio
        const audioBuffer = await textToSpeech(text);

        if (!audioBuffer) {
            throw new Error("Failed to generate audio");
        }

        // Play audio
        await playAudio(audioBuffer);
        console.log("✅ Playback complete!");

    } catch (error) {
        console.error(`❌ Error: ${error}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(console.error);
}