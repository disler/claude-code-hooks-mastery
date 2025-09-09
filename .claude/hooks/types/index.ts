/**
 * Comprehensive type definitions for Claude Code hooks
 */

// Core hook types
export interface HookInputData {
    session_id: string;
    [key: string]: any;
}

export interface UserPromptSubmitData extends HookInputData {
    prompt: string;
}

export interface NotificationData extends HookInputData {
    message: string;
    type: 'info' | 'warning' | 'error' | 'success';
    timestamp?: string;
}

export interface ToolUseData extends HookInputData {
    tool_name: string;
    parameters?: Record<string, any>;
    timestamp?: string;
}

export interface SessionStartData extends HookInputData {
    start_time: string;
    metadata?: Record<string, any>;
}

export interface SessionStopData extends HookInputData {
    end_time: string;
    duration?: number;
    reason?: string;
}

export interface SubagentData extends HookInputData {
    subagent_id: string;
    subagent_type?: string;
    action?: string;
    data?: any;
}

export interface PreCompactData extends HookInputData {
    context_size?: number;
    threshold?: number;
    action?: 'compact' | 'warn' | 'skip';
}

// Session management types
export interface SessionData {
    session_id: string;
    prompts: string[];
    agent_name?: string;
    metadata?: SessionMetadata;
    created_at?: string;
    updated_at?: string;
}

export interface SessionMetadata {
    user?: string;
    project?: string;
    environment?: string;
    [key: string]: any;
}

// Logging types
export interface LogEntry {
    timestamp: string;
    session_id: string;
    type: string;
    data: any;
}

export interface NotificationLog extends LogEntry {
    type: 'notification';
    data: NotificationData;
}

export interface PromptLog extends LogEntry {
    type: 'prompt';
    data: UserPromptSubmitData;
}

// Validation types
export interface ValidationResult {
    isValid: boolean;
    reason?: string;
    suggestions?: string[];
}

export interface ValidationRule {
    pattern: string | RegExp;
    message: string;
    severity?: 'warning' | 'error';
}

// LLM interaction types
export interface LLMRequest {
    prompt: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    system_prompt?: string;
}

export interface LLMResponse {
    text: string;
    model: string;
    usage?: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
    };
    error?: string;
}

// TTS types
export interface TTSRequest {
    text: string;
    voice?: string;
    model?: string;
    speed?: number;
    pitch?: number;
}

export interface TTSResponse {
    audio: Buffer;
    format: 'mp3' | 'wav' | 'ogg';
    duration?: number;
}

export interface TTSProvider {
    textToSpeech(request: TTSRequest): Promise<TTSResponse | null>;
    playAudio(audio: Buffer): Promise<void>;
    isAvailable(): boolean;
}

// Command execution types
export interface CommandResult {
    stdout: string;
    stderr?: string;
    returncode: number;
    duration?: number;
}

export interface HookConfig {
    enabled: boolean;
    validate?: boolean;
    logOnly?: boolean;
    timeout?: number;
    retries?: number;
    [key: string]: any;
}

// Error types
export class HookError extends Error {
    constructor(
        message: string,
        public code: string,
        public details?: any
    ) {
        super(message);
        this.name = 'HookError';
    }
}

export class ValidationError extends HookError {
    constructor(message: string, details?: any) {
        super(message, 'VALIDATION_ERROR', details);
        this.name = 'ValidationError';
    }
}

export class TTSError extends HookError {
    constructor(message: string, details?: any) {
        super(message, 'TTS_ERROR', details);
        this.name = 'TTSError';
    }
}

// Utility types
export type HookExitCode = 0 | 1 | 2;
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface Logger {
    log(level: LogLevel, message: string, data?: any): void;
    debug(message: string, data?: any): void;
    info(message: string, data?: any): void;
    warn(message: string, data?: any): void;
    error(message: string, data?: any): void;
}

// Environment configuration
export interface EnvironmentConfig {
    ANTHROPIC_API_KEY?: string;
    OPENAI_API_KEY?: string;
    ELEVENLABS_API_KEY?: string;
    OLLAMA_HOST?: string;
    LOG_LEVEL?: LogLevel;
    LOG_DIR?: string;
    SESSION_DIR?: string;
    [key: string]: string | undefined;
}

// Hook handler type
export type HookHandler<T extends HookInputData = HookInputData> = (
    data: T,
    config?: HookConfig
) => Promise<HookExitCode>;

// Export type guards
export function isNotificationData(data: any): data is NotificationData {
    return data && 
           typeof data.message === 'string' && 
           ['info', 'warning', 'error', 'success'].includes(data.type);
}

export function isUserPromptSubmitData(data: any): data is UserPromptSubmitData {
    return data && 
           typeof data.session_id === 'string' && 
           typeof data.prompt === 'string';
}

export function isToolUseData(data: any): data is ToolUseData {
    return data && 
           typeof data.session_id === 'string' && 
           typeof data.tool_name === 'string';
}

export function isValidationResult(result: any): result is ValidationResult {
    return result && 
           typeof result.isValid === 'boolean' &&
           (result.reason === undefined || typeof result.reason === 'string');
}