# ClickBot v2

A Python-based automation tool that automatically clicks the accept button when the cursor is in the composer area.

## Setup

1. Install the required dependencies:
```bash
pip3 install -r requirements.txt
```

## Usage

1. First, run the calibration script to set up the button and composer area positions:
```bash
python3 calibrate.py
```

2. Follow the calibration instructions:
   - Move your cursor to the accept button and press Enter to capture its position
   - Move your cursor to the top-left corner of the composer area and press Enter
   - Move your cursor to the bottom-right corner of the composer area and press Enter

3. Run the ClickBot:
```bash
python3 clicker.py
```

The ClickBot will show a small status window in the bottom-right corner while it's running. When your cursor enters the calibrated composer area, it will automatically click the accept button.

Press Ctrl+C to stop the ClickBot.

## Files

- `calibrate.py`: Tool for setting up button and composer area positions
- `clicker.py`: Main ClickBot script that handles the automation
- `config.json`: Configuration file storing the calibrated positions
- `requirements.txt`: List of Python package dependencies 