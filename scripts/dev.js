const chokidar = require('chokidar');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs-extra');
const dotenv = require('dotenv');
const TestRunner = require('./test-config');

// Load environment variables
dotenv.config();

// Ensure logs directory exists
fs.ensureDirSync(path.join(__dirname, '../logs/client'));
fs.ensureDirSync(path.join(__dirname, '../logs/server'));
fs.ensureDirSync(path.join(__dirname, '../logs/tests'));

const testRunner = new TestRunner();

class ProcessManager {
  constructor() {
    this.clientProcess = null;
    this.serverProcess = null;
    this.clientLog = fs.createWriteStream(
      path.join(__dirname, '../logs/client/process.log'),
      { flags: 'a' }
    );
    this.serverLog = fs.createWriteStream(
      path.join(__dirname, '../logs/server/process.log'),
      { flags: 'a' }
    );
    this.testLog = fs.createWriteStream(
      path.join(__dirname, '../logs/tests/test.log'),
      { flags: 'a' }
    );
  }

  async runTests(type) {
    try {
      if (type === 'frontend') {
        // Wait for webpack to finish
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        if (!testRunner.browser) {
          await testRunner.setupPuppeteer();
        }
        
        const frontendResults = await testRunner.runFrontendTests();
        this.testLog.write(`\n[${new Date().toISOString()}] Frontend Tests:\n${JSON.stringify(frontendResults, null, 2)}\n`);
        
        // Check for errors and handle the first one
        if (frontendResults.consoleErrors && frontendResults.consoleErrors.length > 0) {
          this.handleError('frontend', frontendResults.consoleErrors[0]);
        }
      }
      
      if (type === 'backend') {
        const backendResults = await testRunner.runBackendTests();
        this.testLog.write(`\n[${new Date().toISOString()}] Backend Tests:\n${JSON.stringify(backendResults, null, 2)}\n`);
        
        if (backendResults.status === 'failed') {
          this.handleError('backend', backendResults.error);
        }
      }
    } catch (error) {
      this.testLog.write(`\n[${new Date().toISOString()}] Test Error: ${error.message}\n`);
      this.handleError('test', error);
    }
  }

  handleError(type, error) {
    const errorLog = fs.createWriteStream(
      path.join(__dirname, '../logs/errors.log'),
      { flags: 'a' }
    );

    errorLog.write(`\n[${new Date().toISOString()}] ${type} Error:\n${JSON.stringify(error, null, 2)}\n`);
    
    // Analyze error and suggest solution
    const solution = this.analyzeProblem(type, error);
    errorLog.write(`Suggested Solution:\n${solution}\n`);
  }

  analyzeProblem(type, error) {
    // Basic error analysis logic
    if (type === 'frontend') {
      if (error.includes('Module not found')) {
        return 'Missing dependency. Check package.json and run npm install';
      }
      if (error.includes('Syntax error')) {
        return 'Code syntax error. Check the indicated file and line number';
      }
    }

    if (type === 'backend') {
      if (error.includes('ECONNREFUSED')) {
        return 'Server not running or wrong port. Check server configuration';
      }
      if (error.includes('MongoDB')) {
        return 'Database connection error. Check MongoDB connection string and ensure database is running';
      }
    }

    return 'Unknown error. Manual investigation required';
  }

  async startClient() {
    if (this.clientProcess) {
      this.clientProcess.kill();
    }

    this.clientLog.write(`\n[${new Date().toISOString()}] Starting client...\n`);
    
    this.clientProcess = spawn('npm', ['start'], {
      cwd: path.join(__dirname, '../client'),
      env: { ...process.env },
      stdio: 'pipe'
    });

    this.clientProcess.stdout.pipe(this.clientLog);
    this.clientProcess.stderr.pipe(this.clientLog);

    this.clientProcess.on('exit', () => {
      this.runTests('frontend');
    });
  }

  async startServer() {
    if (this.serverProcess) {
      this.serverProcess.kill();
    }

    this.serverLog.write(`\n[${new Date().toISOString()}] Starting server...\n`);
    
    this.serverProcess = spawn('npm', ['start'], {
      cwd: path.join(__dirname, '../server'),
      env: { ...process.env },
      stdio: 'pipe'
    });

    this.serverProcess.stdout.pipe(this.serverLog);
    this.serverProcess.stderr.pipe(this.serverLog);

    this.serverProcess.on('exit', () => {
      this.runTests('backend');
    });
  }

  setupWatchers() {
    // Watch client files
    const clientWatcher = chokidar.watch(
      path.join(__dirname, '../client/src'),
      {
        ignored: /(^|[\/\\])\../,
        persistent: true
      }
    );

    clientWatcher.on('change', (path) => {
      this.clientLog.write(`\n[${new Date().toISOString()}] File changed: ${path}\n`);
      this.startClient();
    });

    // Watch server files
    const serverWatcher = chokidar.watch(
      path.join(__dirname, '../server/src'),
      {
        ignored: /(^|[\/\\])\../,
        persistent: true
      }
    );

    serverWatcher.on('change', (path) => {
      this.serverLog.write(`\n[${new Date().toISOString()}] File changed: ${path}\n`);
      this.startServer();
    });
  }

  async start() {
    try {
      await this.startClient();
      await this.startServer();
      this.setupWatchers();
    } catch (error) {
      this.handleError('startup', error);
      throw error; // Re-throw to trigger the catch block in the main execution
    }
  }
}

const manager = new ProcessManager();
manager.start().catch(error => {
  console.error('Failed to start:', error);
  process.exit(1);
}); 