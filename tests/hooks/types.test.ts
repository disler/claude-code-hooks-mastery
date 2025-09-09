import {
  isNotificationData,
  isUserPromptSubmitData,
  isToolUseData,
  isValidationResult,
  HookError,
  ValidationError,
  TTSError
} from '../../.claude/hooks/types';

describe('Type Guards', () => {
  describe('isNotificationData', () => {
    it('should return true for valid notification data', () => {
      const data = {
        message: 'Test message',
        type: 'info',
        session_id: 'test-session'
      };
      expect(isNotificationData(data)).toBe(true);
    });

    it('should return false for invalid notification data', () => {
      const invalidData = [
        { message: 'Test', type: 'invalid' },
        { type: 'info' },
        { message: 123, type: 'info' },
        null,
        undefined
      ];
      
      invalidData.forEach(data => {
        expect(isNotificationData(data)).toBe(false);
      });
    });
  });

  describe('isUserPromptSubmitData', () => {
    it('should return true for valid prompt data', () => {
      const data = {
        session_id: 'test-session',
        prompt: 'Test prompt'
      };
      expect(isUserPromptSubmitData(data)).toBe(true);
    });

    it('should return false for invalid prompt data', () => {
      expect(isUserPromptSubmitData({ session_id: 'test' })).toBe(false);
      expect(isUserPromptSubmitData({ prompt: 'test' })).toBe(false);
      expect(isUserPromptSubmitData(null)).toBe(false);
    });
  });

  describe('isToolUseData', () => {
    it('should return true for valid tool use data', () => {
      const data = {
        session_id: 'test-session',
        tool_name: 'TestTool',
        parameters: { key: 'value' }
      };
      expect(isToolUseData(data)).toBe(true);
    });

    it('should return true even without parameters', () => {
      const data = {
        session_id: 'test-session',
        tool_name: 'TestTool'
      };
      expect(isToolUseData(data)).toBe(true);
    });
  });

  describe('isValidationResult', () => {
    it('should return true for valid validation results', () => {
      expect(isValidationResult({ isValid: true })).toBe(true);
      expect(isValidationResult({ isValid: false, reason: 'Error' })).toBe(true);
      expect(isValidationResult({ 
        isValid: true, 
        suggestions: ['Fix this', 'Try that'] 
      })).toBe(true);
    });

    it('should return false for invalid validation results', () => {
      expect(isValidationResult({ isValid: 'true' })).toBe(false);
      expect(isValidationResult({ reason: 'Error' })).toBe(false);
      expect(isValidationResult(null)).toBe(false);
    });
  });
});

describe('Error Classes', () => {
  describe('HookError', () => {
    it('should create HookError with correct properties', () => {
      const error = new HookError('Test error', 'TEST_CODE', { detail: 'value' });
      expect(error.message).toBe('Test error');
      expect(error.code).toBe('TEST_CODE');
      expect(error.details).toEqual({ detail: 'value' });
      expect(error.name).toBe('HookError');
    });
  });

  describe('ValidationError', () => {
    it('should create ValidationError with correct code', () => {
      const error = new ValidationError('Validation failed', { field: 'test' });
      expect(error.message).toBe('Validation failed');
      expect(error.code).toBe('VALIDATION_ERROR');
      expect(error.details).toEqual({ field: 'test' });
      expect(error.name).toBe('ValidationError');
    });
  });

  describe('TTSError', () => {
    it('should create TTSError with correct code', () => {
      const error = new TTSError('TTS failed');
      expect(error.message).toBe('TTS failed');
      expect(error.code).toBe('TTS_ERROR');
      expect(error.name).toBe('TTSError');
    });
  });
});