const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const fs = require('fs');
const path = require('path');

// Create Express app
const app = express();

// Create logs directory if it doesn't exist
const logDir = path.join(__dirname, '../../logs/server');
fs.existsSync(logDir) || fs.mkdirSync(logDir, { recursive: true });

// Create a write stream for logging
const accessLogStream = fs.createWriteStream(
  path.join(logDir, 'access.log'),
  { flags: 'a' }
);

// Middleware
app.use(cors());
app.use(express.json());
app.use(morgan('combined', { stream: accessLogStream }));

// Basic route
app.get('/api/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Start server
const PORT = process.env.SERVER_PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 