// This script will help verify your Firebase configuration
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env.local') });

const requiredVars = [
  'NEXT_PUBLIC_API_KEY',
  'NEXT_PUBLIC_AUTH_DOMAIN',
  'NEXT_PUBLIC_PROJECT_ID',
  'NEXT_PUBLIC_STORAGE_BUCKET',
  'NEXT_PUBLIC_MESSAGING_SENDER_ID',
  'NEXT_PUBLIC_APP_ID',
  'NEXT_PUBLIC_MEASUREMENT_ID'
];

console.log('\n🔥 Firebase Configuration Checker\n');
console.log('Checking environment variables in .env.local...\n');

let allVarsPresent = true;
const missingVars = [];

requiredVars.forEach(varName => {
  const value = process.env[varName];
  if (!value) {
    console.log(`❌ Missing: ${varName}`);
    missingVars.push(varName);
    allVarsPresent = false;
  } else {
    console.log(`✅ Found: ${varName}`);
  }
});

if (!allVarsPresent) {
  console.log('\n🚨 Missing required environment variables!');
  console.log('Please add the following to your .env.local file:\n');
  
  missingVars.forEach(varName => {
    console.log(`${varName}=your_${varName.replace('NEXT_PUBLIC_', '').toLowerCase()}`);
  });
  
  console.log('\nYou can find these values in your Firebase Console:');
  console.log('1. Go to https://console.firebase.google.com/');
  console.log('2. Select your project');
  console.log('3. Click the gear icon ⚙️ next to "Project Overview"');
  console.log('4. Select "Project settings"');
  console.log('5. Scroll down to "Your apps" section');
  console.log('6. Click on your web app (or create one if needed)');
  console.log('7. Find the firebaseConfig object and copy the values');
} else {
  console.log('\n🎉 All required environment variables are present!');
  console.log('\nTo start the development server, run:');
  console.log('npm run dev');
}

// Also check if .env.local is gitignored
const gitignorePath = path.join(__dirname, '../.gitignore');
if (fs.existsSync(gitignorePath)) {
  const gitignore = fs.readFileSync(gitignorePath, 'utf8');
  if (!gitignore.includes('.env.local')) {
    console.log('\n⚠️  Warning: .env.local is not in .gitignore!');
    console.log('Please add it to prevent committing sensitive data.');
  }
}
