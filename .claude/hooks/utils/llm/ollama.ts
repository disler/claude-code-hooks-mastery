#!/usr/bin/env node

import OpenAI from 'openai';
import { config } from 'dotenv';
import * as process from 'process';

config();

export async function promptLlm(promptText: string): Promise<string | null> {
    /**
     * Base Ollama LLM prompting method using GPT-OSS model.
     *
     * Args:
     *     promptText: The prompt to send to the model
     *
     * Returns:
     *     The model's response text, or null if error
     */
    try {
        // Ollama uses OpenAI-compatible API - exactly as shown in docs
        const client = new OpenAI({
            baseURL: "http://localhost:11434/v1",
            apiKey: "ollama",  // required, but unused
        });

        // Default to 20b model, can override with OLLAMA_MODEL env var
        const model = process.env.OLLAMA_MODEL || "gpt-oss:20b";

        const response = await client.chat.completions.create({
            model: model,
            messages: [{ role: "user", content: promptText }],
            max_tokens: 1000,
        });

        return response.choices[0]?.message?.content?.trim() || null;
    } catch (error) {
        console.error(`Error: ${error}`, error);
        return null;
    }
}

export async function generateCompletionMessage(): Promise<string | null> {
    /**
     * Generate a completion message using Ollama LLM.
     *
     * Returns:
     *     A natural language completion message, or null if error
     */
    const engineerName = process.env.ENGINEER_NAME?.trim() || "";

    let nameInstruction = "";
    let examples = "";

    if (engineerName) {
        nameInstruction = `Sometimes (about 30% of the time) include the engineer's name '${engineerName}' in a natural way.`;
        examples = `Examples of the style: 
- Standard: "Work complete!", "All done!", "Task finished!", "Ready for your next move!"
- Personalized: "${engineerName}, all set!", "Ready for you, ${engineerName}!", "Complete, ${engineerName}!", "${engineerName}, we're done!" `;
    } else {
        examples = `Examples of the style: "Work complete!", "All done!", "Task finished!", "Ready for your next move!" `;
    }

    const prompt = `Generate a short, friendly completion message for when an AI coding assistant finishes a task. 

Requirements:
- Keep it under 10 words
- Make it positive and future focused
- Use natural, conversational language
- Focus on completion/readiness
- Do NOT include quotes, formatting, or explanations
- Return ONLY the completion message text
${nameInstruction}

${examples}

Generate ONE completion message:`;

    let response = await promptLlm(prompt);

    // Clean up response - remove quotes and extra formatting
    if (response) {
        response = response.trim().replace(/^["']|["']$/g, '');
        // Take first line if multiple lines
        response = response.split("\n")[0].trim();
    }

    return response;
}

export async function generateAgentName(): Promise<string> {
    /**
     * Generate a one-word agent name using Ollama.
     *
     * Returns:
     *     A single-word agent name, or fallback name if error
     */

    // Example names to guide generation
    const exampleNames = [
        "Phoenix",
        "Sage",
        "Nova",
        "Echo",
        "Atlas",
        "Cipher",
        "Nexus",
        "Oracle",
        "Quantum",
        "Zenith",
        "Aurora",
        "Vortex",
        "Nebula",
        "Catalyst",
        "Prism",
        "Axiom",
        "Helix",
        "Flux",
        "Synth",
        "Vertex",
    ];

    // Create examples string
    const examplesStr = exampleNames.slice(0, 10).join(", ");  // Use first 10 as examples

    const promptText = `Generate exactly ONE unique agent/assistant name.

Requirements:
- Single word only (no spaces, hyphens, or punctuation)
- Abstract and memorable
- Professional sounding
- Easy to pronounce
- Similar style to these examples: ${examplesStr}

Generate a NEW name (not from the examples). Respond with ONLY the name, nothing else.

Name:`;

    try {
        const response = await promptLlm(promptText);

        if (response) {
            // Extract and clean the name
            let name = response.trim();
            // Ensure it's a single word
            name = name ? name.split(/\s+/)[0] : "Agent";
            // Remove any punctuation
            name = name.replace(/[^a-zA-Z0-9]/g, '');
            // Capitalize first letter
            name = name ? name.charAt(0).toUpperCase() + name.slice(1).toLowerCase() : "Agent";

            // Validate it's not empty and reasonable length
            if (name && name.length >= 3 && name.length <= 20) {
                return name;
            } else {
                throw new Error("Invalid name generated");
            }
        } else {
            throw new Error("No response from Ollama");
        }
    } catch (error) {
        // Return random fallback name
        return exampleNames[Math.floor(Math.random() * exampleNames.length)];
    }
}

// Command line interface for testing
async function main() {
    const args = process.argv.slice(2);

    if (args.length > 0) {
        if (args[0] === "--completion") {
            const message = await generateCompletionMessage();
            if (message) {
                console.log(message);
            } else {
                console.log("Error generating completion message");
            }
        } else if (args[0] === "--agent-name") {
            // Generate agent name (no input needed)
            const name = await generateAgentName();
            console.log(name);
        } else {
            const promptText = args.join(" ");
            const response = await promptLlm(promptText);
            if (response) {
                console.log(response);
            } else {
                console.log("Error calling Ollama API");
            }
        }
    } else {
        console.log("Usage: node ollama.ts 'your prompt here' or node ollama.ts --completion or node ollama.ts --agent-name");
    }
}

if (require.main === module) {
    main().catch(console.error);
}