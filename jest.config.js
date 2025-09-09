module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/.claude', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.ts',
    '**/?(*.)+(spec|test).ts'
  ],
  transform: {
    '^.+\\.ts$': ['ts-jest', {
      tsconfig: {
        esModuleInterop: true,
        allowSyntheticDefaultImports: true
      }
    }]
  },
  collectCoverageFrom: [
    '.claude/**/*.ts',
    '!.claude/**/*.d.ts',
    '!.claude/**/__tests__/**',
    '!**/node_modules/**',
    '!**/dist/**'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/.claude/$1',
    '^@hooks/(.*)$': '<rootDir>/.claude/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/.claude/hooks/utils/$1',
    '^@types/(.*)$': '<rootDir>/.claude/hooks/types/$1'
  },
  testTimeout: 10000,
  verbose: true
};