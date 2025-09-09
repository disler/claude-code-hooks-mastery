#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';

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
        
        // Generate v3 status line with git info
        const timestamp = new Date().toLocaleTimeString();
        const sessionId = inputData.session_id?.slice(-6) || 'unknown';
        
        // Try to get git branch
        let gitInfo = '';
        try {
            const { spawn } = require('child_process');
            const gitProc = spawn('git', ['rev-parse', '--abbrev-ref', 'HEAD']);
            let gitOutput = '';
            gitProc.stdout.on('data', (data: Buffer) => gitOutput += data.toString());
            await new Promise((resolve) => gitProc.on('close', resolve));
            
            if (gitOutput.trim()) {
                gitInfo = ` → ${gitOutput.trim()}`;
            }
        } catch {}
        
        const statusLine = `⚡ Claude Code v3 [${sessionId}]${gitInfo} [${timestamp}]`;
        
        // Output the status line
        console.log(statusLine);
        
        process.exit(0);
        
    } catch (error) {
        console.log('⚡ Claude Code v3');
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => {
        console.log('⚡ Claude Code v3');
        process.exit(0);
    });
}