#!/usr/bin/env node

import * as fs from 'fs/promises';
import * as path from 'path';

async function logStatusLine(inputData: any, statusLineOutput: string): Promise<void> {
    // Ensure logs directory exists
    const logDir = path.resolve('logs');
    await fs.mkdir(logDir, { recursive: true });
    const logFile = path.join(logDir, 'status_line.json');
    
    // Read existing log data or initialize empty list
    let logData: any[] = [];
    try {
        const data = await fs.readFile(logFile, 'utf8');
        logData = JSON.parse(data);
    } catch (error) {
        logData = [];
    }
    
    // Create log entry with input data and generated output
    const logEntry = {
        timestamp: new Date().toISOString(),
        input_data: inputData,
        status_line_output: statusLineOutput
    };
    
    // Append the log entry
    logData.push(logEntry);
    
    // Write back to file with formatting
    await fs.writeFile(logFile, JSON.stringify(logData, null, 2));
}

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
        
        // Generate status line output
        const timestamp = new Date().toLocaleTimeString();
        const statusLine = `Claude Code Active [${timestamp}]`;
        
        // Log the status line event
        await logStatusLine(inputData, statusLine);
        
        // Output the status line
        console.log(statusLine);
        
        process.exit(0);
        
    } catch (error) {
        console.log('Claude Code');
        process.exit(0);
    }
}

if (require.main === module) {
    main().catch(() => {
        console.log('Claude Code');
        process.exit(0);
    });
}