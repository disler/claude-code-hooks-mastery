#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';
import { spawn } from 'child_process';

async function main(): Promise<void> {
    try {
        // Read JSON input from stdin
        let stdinData = '';
        if (process.stdin.isTTY) {
            stdinData = JSON.stringify({ active: true, session_id: 'test' });
        } else {
            process.stdin.setEncoding('utf8');
            for await (const chunk of process.stdin) {
                stdinData += chunk;
            }
        }
        
        const inputData = JSON.parse(stdinData);
        
        // Generate advanced v4 status line
        const timestamp = new Date().toLocaleTimeString();
        const sessionId = inputData.session_id?.slice(-6) || 'unknown';
        
        // Try to get git branch and status
        let gitInfo = '';
        try {
            // Get branch name
            const branchResult = await new Promise<string>((resolve) => {
                const proc = spawn('git', ['rev-parse', '--abbrev-ref', 'HEAD']);
                let output = '';
                proc.stdout.on('data', (data) => output += data.toString());
                proc.on('close', () => resolve(output.trim()));
                proc.on('error', () => resolve(''));
            });
            
            if (branchResult) {
                // Get status
                const statusResult = await new Promise<number>((resolve) => {
                    const proc = spawn('git', ['status', '--porcelain']);
                    let lineCount = 0;
                    proc.stdout.on('data', (data) => {
                        lineCount += data.toString().split('\n').filter((line: string) => line.trim()).length;
                    });
                    proc.on('close', () => resolve(lineCount));
                    proc.on('error', () => resolve(0));
                });
                
                const statusIndicator = statusResult > 0 ? `⚠️${statusResult}` : '✓';
                gitInfo = ` → ${branchResult}${statusIndicator}`;
            }
        } catch {}
        
        // Get current directory name
        const currentDir = path.basename(process.cwd());
        
        const statusLine = `🎨 Claude Code v4 [${currentDir}] [${sessionId}]${gitInfo} [${timestamp}]`;
        
        // Output the status line
        console.log(statusLine);
        
        process.exit(0);
        
    } catch (error) {
        console.log('🎨 Claude Code v4');
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => {
        console.log('🎨 Claude Code v4');
        process.exit(0);
    });
}