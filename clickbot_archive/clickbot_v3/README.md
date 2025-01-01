# Clickbot V3

An automated system for detecting and clicking Accept buttons in the Cursor IDE.

## Components

### Main Files
- `main.py` - The main entry point of the system that orchestrates all components. It initializes the monitor detection, composer detection, and accept button watching functionality.

### Core Components
- `cursor_monitor.py` - Responsible for detecting and tracking the Cursor IDE window across multiple monitors. Uses OCR to identify the Cursor window by its title.

- `cursor_finder.py` - Handles the core functionality of finding specific UI elements within the Cursor window, including the dropdown menu and accept buttons.

- `composer_detector.py` - Specialized module for detecting the composer area in Cursor where code suggestions appear. Uses text detection to identify composer-related UI elements.

- `accept_watcher.py` - Monitors for and detects Accept buttons within the composer area. Handles the button clicking logic and maintains click cooldowns.

### Testing
- `test_submit.py` - Test script for finding and clicking Accept buttons. Useful for testing the button detection and clicking functionality in isolation.

### Dependencies
- `requirements.txt` - Lists all Python package dependencies:
  - mss: For screen capture
  - numpy: For image processing
  - pyautogui: For mouse control
  - Pillow: For image handling
  - scipy: For additional image processing

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main script to start the bot:
```bash
python main.py
```

For testing specific components, you can run:
```bash
python test_submit.py
```

## Features

- Multi-monitor support
- Automatic Cursor window detection
- Precise Accept button detection using color matching and OCR
- Efficient screen region monitoring
- Automatic mouse control with position restoration
- Error handling and logging 