#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';

async function main(): Promise<void> {
    try {
        // Read JSON input from stdin
        let stdinData = '';
        if (process.stdin.isTTY) {
            stdinData = JSON.stringify({ action: 'compact', reason: 'test' });
        } else {
            process.stdin.setEncoding('utf8');
            for await (const chunk of process.stdin) {
                stdinData += chunk;
            }
        }
        
        const inputData = JSON.parse(stdinData);
        
        // Ensure log directory exists
        const logDir = path.resolve('logs');
        await fs.mkdir(logDir, { recursive: true });
        const logPath = path.join(logDir, 'pre_compact.json');
        
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
        
        process.exit(0);
        
    } catch (error) {
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => process.exit(0));
}