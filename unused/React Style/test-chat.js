#!/usr/bin/env node

/**
 * Test script for JD Copilot Chat Interface
 * This script tests the basic functionality of the chat interface
 */

console.log('🧪 Testing JD Copilot Chat Interface...\n');

// Test 1: Check if all required files exist
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const requiredFiles = [
  'package.json',
  'index.html',
  'main.tsx',
  'App.tsx',
  'components/ChatInterface.tsx',
  'components/ChatInput.tsx',
  'components/MessageBubble.tsx',
  'components/ChatHeader.tsx',
  'components/MascotCharacter.tsx',
  'components/AiThinkingFeedback.tsx',
  'components/ScrollToBottom.tsx',
  'components/ParticleVortex.tsx',
  'components/ui/button.tsx',
  'lib/utils.ts',
  'tailwind.config.js',
  'vite.config.ts',
  'tsconfig.json'
];

console.log('📁 Checking required files...');
let allFilesExist = true;

requiredFiles.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} - MISSING`);
    allFilesExist = false;
  }
});

console.log('');

// Test 2: Check package.json dependencies
if (fs.existsSync('package.json')) {
  console.log('📦 Checking package.json dependencies...');
  try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    const requiredDeps = ['react', 'react-dom', 'motion', 'lucide-react'];
    const requiredDevDeps = ['@vitejs/plugin-react', 'tailwindcss', 'typescript'];
    
    console.log('Core dependencies:');
    requiredDeps.forEach(dep => {
      if (packageJson.dependencies && packageJson.dependencies[dep]) {
        console.log(`✅ ${dep}@${packageJson.dependencies[dep]}`);
      } else {
        console.log(`❌ ${dep} - MISSING`);
        allFilesExist = false;
      }
    });
    
    console.log('\nDev dependencies:');
    requiredDevDeps.forEach(dep => {
      if (packageJson.devDependencies && packageJson.devDependencies[dep]) {
        console.log(`✅ ${dep}@${packageJson.devDependencies[dep]}`);
      } else {
        console.log(`❌ ${dep} - MISSING`);
        allFilesExist = false;
      }
    });
  } catch (error) {
    console.log(`❌ Error reading package.json: ${error.message}`);
    allFilesExist = false;
  }
}

console.log('');

// Test 3: Check TypeScript configuration
if (fs.existsSync('tsconfig.json')) {
  console.log('⚙️ Checking TypeScript configuration...');
  try {
    const tsConfig = JSON.parse(fs.readFileSync('tsconfig.json', 'utf8'));
    
    if (tsConfig.compilerOptions && tsConfig.compilerOptions.jsx === 'react-jsx') {
      console.log('✅ JSX configuration correct');
    } else {
      console.log('❌ JSX configuration incorrect');
      allFilesExist = false;
    }
    
    if (tsConfig.compilerOptions && tsConfig.compilerOptions.strict) {
      console.log('✅ Strict mode enabled');
    } else {
      console.log('❌ Strict mode disabled');
      allFilesExist = false;
    }
  } catch (error) {
    console.log(`❌ Error reading tsconfig.json: ${error.message}`);
    allFilesExist = false;
  }
}

console.log('');

// Test 4: Check Tailwind configuration
if (fs.existsSync('tailwind.config.js')) {
  console.log('🎨 Checking Tailwind configuration...');
  try {
    const tailwindConfig = fs.readFileSync('tailwind.config.js', 'utf8');
    
    if (tailwindConfig.includes('darkMode') && tailwindConfig.includes('content')) {
      console.log('✅ Tailwind configuration looks good');
    } else {
      console.log('❌ Tailwind configuration incomplete');
      allFilesExist = false;
    }
  } catch (error) {
    console.log(`❌ Error reading tailwind.config.js: ${error.message}`);
    allFilesExist = false;
  }
}

console.log('');

// Test 5: Check Vite configuration
if (fs.existsSync('vite.config.ts')) {
  console.log('⚡ Checking Vite configuration...');
  try {
    const viteConfig = fs.readFileSync('vite.config.ts', 'utf8');
    
    if (viteConfig.includes('@vitejs/plugin-react') && viteConfig.includes('port: 3000')) {
      console.log('✅ Vite configuration looks good');
    } else {
      console.log('❌ Vite configuration incomplete');
      allFilesExist = false;
    }
  } catch (error) {
    console.log(`❌ Error reading vite.config.ts: ${error.message}`);
    allFilesExist = false;
  }
}

console.log('');

// Final result
if (allFilesExist) {
  console.log('🎉 All tests passed! The React chat interface is ready to use.');
  console.log('\n🚀 Next steps:');
  console.log('1. Run: npm install');
  console.log('2. Run: npm run dev');
  console.log('3. Open: http://localhost:3000');
  console.log('4. Test the chat interface!');
} else {
  console.log('❌ Some tests failed. Please check the missing files and dependencies.');
  console.log('\n🔧 To fix:');
  console.log('1. Ensure all required files are present');
  console.log('2. Check package.json dependencies');
  console.log('3. Verify configuration files');
}

console.log('\n📚 For more information, see README.md');
