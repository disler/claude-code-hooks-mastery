#!/usr/bin/env node

import { config } from 'dotenv';
import * as process from 'process';
import axios from 'axios';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';
import * as os from 'os';

config();

async function playAudio(audioBuffer: Buffer): Promise<void> {
    // Create temporary file
    const tempFile = path.join(os.tmpdir(), `elevenlabs_${Date.now()}.mp3`);
    
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
    const apiKey = process.env.ELEVENLABS_API_KEY;
    if (!apiKey) {
        return null;
    }

    try {
        const response = await axios.post(
            `https://api.elevenlabs.io/v1/text-to-speech/WejK3H1m7MI9CHnIjW9K`,
            {
                text: text,
                model_id: "eleven_turbo_v2_5",
                voice_settings: {
                    stability: 0.5,
                    similarity_boost: 0.5
                }
            },
            {
                headers: {
                    'Accept': 'audio/mpeg',
                    'Content-Type': 'application/json',
                    'xi-api-key': apiKey
                },
                responseType: 'arraybuffer'
            }
        );

        return Buffer.from(response.data);
    } catch (error) {
        console.error(`Error generating audio: ${error}`);
        return null;
    }
}

async function main() {
    /**
     * ElevenLabs Turbo v2.5 TTS Script
     * 
     * Uses ElevenLabs' Turbo v2.5 model for fast, high-quality text-to-speech.
     * Accepts optional text prompt as command-line argument.
     * 
     * Usage:
     * - node elevenlabs_tts.ts                    # Uses default text
     * - node elevenlabs_tts.ts "Your custom text" # Uses provided text
     * 
     * Features:
     * - Fast generation (optimized for real-time use)
     * - High-quality voice synthesis
     * - Stable production model
     * - Cost-effective for high-volume usage
     */
    
    // Get API key from environment
    const apiKey = process.env.ELEVENLABS_API_KEY;
    if (!apiKey) {
        console.error("❌ Error: ELEVENLABS_API_KEY not found in environment variables");
        console.error("Please add your ElevenLabs API key to .env file:");
        console.error("ELEVENLABS_API_KEY=your_api_key_here");
        process.exit(1);
    }
    
    console.log("🎙️  ElevenLabs Turbo v2.5 TTS");
    console.log("=" + "=".repeat(40));
    
    // Get text from command line argument or use default
    const args = process.argv.slice(2);
    const text = args.length > 0 
        ? args.join(" ")  // Join all arguments as text
        : "The first move is what sets everything in motion.";
    
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