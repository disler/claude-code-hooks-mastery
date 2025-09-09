#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔄 Claude Code Hooks Migration Tool');
console.log('====================================\n');

// Check if Python hooks exist
const pythonHooksDir = path.join(__dirname, '..', '.claude', 'hooks');
const pythonFiles = fs.readdirSync(pythonHooksDir).filter(f => f.endsWith('.py'));

if (pythonFiles.length === 0) {
  console.log('✅ No Python hooks found. Already using TypeScript!');
  process.exit(0);
}

console.log(`Found ${pythonFiles.length} Python hook files to migrate:\n`);
pythonFiles.forEach(file => console.log(`  - ${file}`));

// Backup Python files
const backupDir = path.join(__dirname, '..', '.claude', 'hooks', 'python-backup');
if (!fs.existsSync(backupDir)) {
  fs.mkdirSync(backupDir, { recursive: true });
  console.log(`\n📁 Creating backup directory: ${backupDir}`);
}

console.log('\n📦 Backing up Python files...');
pythonFiles.forEach(file => {
  const src = path.join(pythonHooksDir, file);
  const dest = path.join(backupDir, file);
  fs.copyFileSync(src, dest);
  console.log(`  ✓ Backed up ${file}`);
});

// Check for custom modifications
console.log('\n🔍 Checking for custom modifications...');
const customPatterns = [
  /# CUSTOM:/gi,
  /# TODO:/gi,
  /# MODIFIED:/gi,
  /def custom_/gi
];

const modifiedFiles = [];
pythonFiles.forEach(file => {
  const content = fs.readFileSync(path.join(pythonHooksDir, file), 'utf8');
  const hasCustomCode = customPatterns.some(pattern => pattern.test(content));
  if (hasCustomCode) {
    modifiedFiles.push(file);
  }
});

if (modifiedFiles.length > 0) {
  console.log('\n⚠️  Warning: The following files contain custom modifications:');
  modifiedFiles.forEach(file => console.log(`  - ${file}`));
  console.log('\n  Please review the TypeScript versions and port your custom logic manually.');
}

// Check dependencies
console.log('\n📋 Checking dependencies...');
try {
  const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'package.json'), 'utf8'));
  
  console.log('  Node.js dependencies are configured in package.json');
  console.log('\n  To install dependencies, run: npm install');
  
  // Check for Python-specific environment variables
  const envFile = path.join(__dirname, '..', '.env');
  if (fs.existsSync(envFile)) {
    console.log('\n  ✓ .env file found - environment variables will work with TypeScript');
  }
} catch (error) {
  console.error('  ❌ Error reading package.json');
}

// Build instructions
console.log('\n🛠️  Migration Steps:');
console.log('  1. Install Node.js dependencies:');
console.log('     npm install');
console.log('\n  2. Build TypeScript files:');
console.log('     npm run build:hooks');
console.log('\n  3. Test the hooks:');
console.log('     npm test');
console.log('\n  4. Once verified, remove Python files:');
console.log('     rm .claude/hooks/*.py');

// Configuration migration
console.log('\n⚙️  Configuration Migration:');
console.log('  - Python: Used direct script execution');
console.log('  - TypeScript: Requires compilation or tsx runtime');
console.log('\n  Update your Claude Code settings if needed:');
console.log('  - For compiled JS: Use dist/.claude/hooks/<hook>.js');
console.log('  - For direct TS: Use tsx .claude/hooks/<hook>.ts');

// Breaking changes
console.log('\n⚠️  Breaking Changes:');
console.log('  1. Execution: TypeScript files need compilation or tsx runtime');
console.log('  2. Dependencies: Node.js/npm required instead of Python/pip');
console.log('  3. File paths: May need updating in Claude Code settings');
console.log('  4. Custom code: Manual porting required for modifications');

console.log('\n✅ Migration preparation complete!');
console.log('   Python files backed up to:', backupDir);
console.log('   Follow the steps above to complete migration.\n');