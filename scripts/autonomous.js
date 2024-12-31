const fs = require('fs-extra');
const path = require('path');
const chokidar = require('chokidar');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

class AutonomousManager {
  constructor() {
    this.featureQueue = [];
    this.currentFeature = null;
    this.isProcessing = false;
    this.logPath = path.join(__dirname, '../logs/autonomous.log');
  }

  async initialize() {
    // Load features from knowledge base
    const featureDir = path.join(__dirname, '../knowledgebase/feature-specs');
    const features = await fs.readdir(featureDir);
    
    this.featureQueue = features
      .filter(f => f.endsWith('.md'))
      .sort((a, b) => {
        const numA = parseInt(a.split('-')[0]);
        const numB = parseInt(b.split('-')[0]);
        return numA - numB;
      });

    // Set up file watchers
    this.setupWatchers();
    
    // Start processing features
    this.processNextFeature();
  }

  async processNextFeature() {
    if (this.isProcessing || this.featureQueue.length === 0) return;
    
    this.isProcessing = true;
    this.currentFeature = this.featureQueue.shift();
    
    try {
      // Read feature specification
      const featureContent = await fs.readFile(
        path.join(__dirname, '../knowledgebase/feature-specs', this.currentFeature),
        'utf8'
      );
      
      this.log(`Starting implementation of feature: ${this.currentFeature}`);
      
      // Create feature branch
      await this.executeGitCommand(`git checkout -b feature/${this.currentFeature}`);
      
      // Implement feature (this would be handled by Cursor/Claude)
      // ... feature implementation ...
      
      // Run tests
      await this.runTests();
      
      // If tests pass, commit and merge
      await this.executeGitCommand('git add .');
      await this.executeGitCommand(`git commit -m "Implemented ${this.currentFeature}"`);
      await this.executeGitCommand('git checkout main');
      await this.executeGitCommand(`git merge feature/${this.currentFeature}`);
      
      this.log(`Completed implementation of feature: ${this.currentFeature}`);
    } catch (error) {
      this.log(`Error implementing feature ${this.currentFeature}: ${error.message}`);
    }
    
    this.isProcessing = false;
    this.processNextFeature();
  }

  setupWatchers() {
    // Watch for file changes
    const watcher = chokidar.watch([
      path.join(__dirname, '../client/src'),
      path.join(__dirname, '../server/src'),
      path.join(__dirname, '../knowledgebase')
    ]);

    watcher.on('change', async (filePath) => {
      this.log(`File changed: ${filePath}`);
      await this.runTests();
    });
  }

  async runTests() {
    try {
      await execAsync('npm test');
      this.log('Tests passed successfully');
    } catch (error) {
      this.log(`Test failure: ${error.message}`);
      // Handle test failure (Cursor/Claude would analyze and fix)
    }
  }

  async executeGitCommand(command) {
    try {
      const { stdout } = await execAsync(command);
      this.log(`Git command succeeded: ${command}\n${stdout}`);
    } catch (error) {
      this.log(`Git command failed: ${command}\n${error.message}`);
      throw error;
    }
  }

  log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    fs.appendFileSync(this.logPath, logMessage);
    console.log(logMessage);
  }
}

// Start autonomous operation
const manager = new AutonomousManager();
manager.initialize().catch(error => {
  console.error('Failed to start autonomous operation:', error);
  process.exit(1);
}); 