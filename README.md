# HustleBot III

An automated system for continuous operation with integrated click automation.

## Setup

1. Install Python dependencies:
```bash
pip3 install -r clickbot_v2/requirements.txt
```

## Usage

1. Start the automation system:
```bash
python3 start.py
```

This will:
- Start the Cursor composer
- Launch the ClickBot
- Guide you through calibration (if needed)
- Begin monitoring for accept buttons

The system will show a small status window in the bottom-right corner while running. When your cursor enters the calibrated composer area, it will automatically click any accept buttons that appear.

Press Ctrl+C to stop the automation system.

## Components

- `start.py`: Main entry point that coordinates the composer and click automation
- `clickbot_v2/`: Directory containing the click automation system
  - `calibrate.py`: Standalone calibration tool
  - `clicker.py`: Standalone click automation script
  - `config.json`: Configuration file storing calibrated positions
  - `requirements.txt`: Python package dependencies

## Development

The repository is organized into several key areas:
- `knowledgebase/`: Documentation and specifications
- `process-instructions/`: Development and deployment guides
- `server/`: Backend server implementation
- `client/`: Frontend client implementation 

