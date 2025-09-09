#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Make compiled hook files executable
const hooksDir = path.join(__dirname, '..', 'dist', '.claude', 'hooks');

if (fs.existsSync(hooksDir)) {
  const files = fs.readdirSync(hooksDir);
  
  files.forEach(file => {
    if (file.endsWith('.js') && !file.includes('.d.ts')) {
      const filePath = path.join(hooksDir, file);
      
      // Add shebang if not present
      const content = fs.readFileSync(filePath, 'utf8');
      if (!content.startsWith('#!/usr/bin/env node')) {
        fs.writeFileSync(filePath, '#!/usr/bin/env node\n' + content);
      }
      
      // Make executable on Unix-like systems
      if (process.platform !== 'win32') {
        fs.chmodSync(filePath, 0o755);
      }
      
      console.log(`✓ Made executable: ${file}`);
    }
  });
  
  console.log('All hook files are now executable');
} else {
  console.log('Build directory not found. Run "npm run build" first.');
}