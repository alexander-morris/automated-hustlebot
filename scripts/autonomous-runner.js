const { exec, spawn } = require('child_process');
const chokidar = require('chokidar');
const path = require('path');
const fs = require('fs-extra');
const axios = require('axios');

class AutonomousRunner {
  constructor() {
    this.clientProcess = null;
    this.serverProcess = null;
    this.clickerProcess = null;
    this.setupLogs();

    process.on('exit', () => {
      if (this.clickerProcess) {
        this.clickerProcess.kill();
      }
    });
  }

  setupLogs() {
    const logsDir = path.join(__dirname, '../logs');
    fs.ensureDirSync(logsDir);
    this.logStream = fs.createWriteStream(
      path.join(logsDir, 'autonomous-runner.log'),
      { flags: 'a' }
    );
  }

  log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    this.logStream.write(logMessage);
    console.log(logMessage);
  }

  async startClickerService() {
    // Create logs directory if it doesn't exist
    fs.ensureDirSync(path.join(__dirname, '../clicker-service/logs'));
    
    // Start the Python clicker service with full path
    this.clickerProcess = spawn('python', ['app.py'], {
      cwd: path.join(process.cwd(), 'clicker-service'),
      stdio: 'pipe',
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    this.clickerProcess.stdout.pipe(process.stdout);
    this.clickerProcess.stderr.pipe(process.stderr);

    // Wait for service to start
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Test the service
    try {
      await axios.post('http://localhost:3333/click/accept');
      this.log('Clicker service started successfully');
    } catch (error) {
      this.log('Clicker service failed to start: ' + error.message);
      throw error;
    }
  }

  async acceptChanges() {
    try {
      await axios.post('http://localhost:3333/click/accept');
      this.log('Triggered accept click');
    } catch (error) {
      this.log(`Error triggering click: ${error.message}`);
    }
  }

  watchForChanges() {
    const watcher = chokidar.watch([
      'client/src/**/*',
      'server/src/**/*'
    ], {
      ignored: [
        /(^|[\/\\])\../,
        '**/node_modules/**',
        '**/dist/**',
        '**/build/**',
        '**/logs/**'
      ],
      persistent: true
    });

    watcher.on('change', async (filepath) => {
      this.log(`File changed: ${filepath}`);
      await this.acceptChanges();
    });
  }

  async restartClient() {
    this.log('Restarting client...');
    if (this.clientProcess) {
      this.clientProcess.kill();
    }

    this.clientProcess = spawn('npm', ['start'], {
      cwd: path.join(__dirname, '../client'),
      stdio: 'pipe'
    });

    this.clientProcess.stdout.pipe(process.stdout);
    this.clientProcess.stderr.pipe(process.stderr);
  }

  async restartServer() {
    this.log('Restarting server...');
    if (this.serverProcess) {
      this.serverProcess.kill();
    }

    this.serverProcess = spawn('npm', ['start'], {
      cwd: path.join(__dirname, '../server'),
      stdio: 'pipe'
    });

    this.serverProcess.stdout.pipe(process.stdout);
    this.serverProcess.stderr.pipe(process.stderr);
  }

  async findAndKillExistingProcesses() {
    const processes = await findProcess('name', 'node');
    for (const proc of processes) {
      if (proc.name.includes('node')) {
        try {
          process.kill(proc.pid);
          this.log(`Killed existing process: ${proc.pid}`);
        } catch (err) {
          this.log(`Failed to kill process ${proc.pid}: ${err.message}`);
        }
      }
    }
  }

  async start() {
    try {
      this.log('Starting autonomous runner...');
      
      // Start the clicker service first
      await this.startClickerService();
      
      // Kill any existing processes
      await this.findAndKillExistingProcesses();
      
      // Start watching for changes
      this.watchForChanges();
      
      // Start applications
      await this.restartClient();
      await this.restartServer();
      
      this.log('Autonomous runner started successfully');
    } catch (error) {
      this.log(`Error starting autonomous runner: ${error.message}`);
      throw error;
    }
  }
}

// Add these dependencies to package.json
const requiredDeps = {
  "ws": "^8.13.0",
  "find-process": "^1.4.7"
};

// Update package.json
const packageJson = require('../package.json');
packageJson.devDependencies = {
  ...packageJson.devDependencies,
  ...requiredDeps
};
fs.writeFileSync(
  path.join(__dirname, '../package.json'),
  JSON.stringify(packageJson, null, 2)
);

// Start the autonomous runner
const runner = new AutonomousRunner();
runner.start().catch(error => {
  console.error('Failed to start autonomous runner:', error);
  process.exit(1);
}); 