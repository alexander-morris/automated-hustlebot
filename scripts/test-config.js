const puppeteer = require('puppeteer');
const axios = require('axios');
const path = require('path');
const fs = require('fs-extra');

class TestRunner {
  constructor() {
    this.browser = null;
    this.page = null;
  }

  async setupPuppeteer() {
    this.browser = await puppeteer.launch({
      headless: false,  // Set to true in production
      args: ['--window-size=1920,1080']
    });
    this.page = await this.browser.newPage();
    
    // Capture console logs
    this.page.on('console', msg => {
      const logPath = path.join(__dirname, '../logs/client/console.log');
      fs.appendFileSync(logPath, `${new Date().toISOString()} - ${msg.type()}: ${msg.text()}\n`);
    });

    // Capture network errors
    this.page.on('pageerror', error => {
      const logPath = path.join(__dirname, '../logs/client/errors.log');
      fs.appendFileSync(logPath, `${new Date().toISOString()} - PageError: ${error.message}\n`);
    });
  }

  async runFrontendTests() {
    try {
      await this.page.goto('http://localhost:3000');
      
      // Basic page load test
      const title = await this.page.title();
      
      // Check for React errors in console
      const consoleErrors = [];
      this.page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      // Basic content check
      const content = await this.page.content();
      const hasAppContent = content.includes('Autonomous Development Project');

      return { 
        status: 'completed',
        title,
        consoleErrors,
        hasExpectedContent: hasAppContent
      };
    } catch (error) {
      return { error: error.message };
    }
  }

  async runBackendTests() {
    try {
      // Health check
      const healthCheck = await axios.get('http://localhost:3001/api/health');
      
      // Add more API tests here
      
      return { status: 'passed', results: healthCheck.data };
    } catch (error) {
      return { status: 'failed', error: error.message };
    }
  }
}

module.exports = TestRunner; 