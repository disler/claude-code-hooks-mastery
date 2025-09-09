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
        
        // Generate enhanced status line output
        const timestamp = new Date().toLocaleTimeString();
        const sessionId = inputData.session_id?.slice(-6) || 'unknown';
        const statusLine = `🤖 Claude Code v2 [${sessionId}] [${timestamp}]`;
        
        // Output the status line
        console.log(statusLine);
        
        process.exit(0);
        
    } catch (error) {
        console.log('🤖 Claude Code v2');
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => {
        console.log('🤖 Claude Code v2');
        process.exit(0);
    });
}