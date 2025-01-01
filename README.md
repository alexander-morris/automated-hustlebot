# HustleBot III

Empowering developers to maximize their potential by combining hacking ingenuity, hustle mindset, and AI automation.

## Vision
HustleBot represents the intersection of hacker creativity, hustle culture's drive for efficiency, and AI's transformative power. It's designed for developers who understand that working smarter means leveraging every available tool and automation to stay ahead in today's fast-paced tech landscape.

## Features
- Intelligent screen monitoring and pattern recognition
- Automated response handling with high precision
- Smart window detection across multiple monitors
- Configurable actions with development mode for testing
- Real-time confidence scoring and match visualization

## Philosophy
This project embodies the modern developer's approach to productivity:
- **Hacker Mindset**: Finding creative solutions to automate repetitive tasks
- **Hustle Culture**: Maximizing efficiency to stay ahead of the competition
- **AI Integration**: Leveraging machine learning for smarter automation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/alexander-morris/automated-hustlebot.git
cd automated-hustlebot
```

2. Create and activate a Python virtual environment:
```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

3. Install the required dependencies:
```bash
cd clickbot
pip install -r requirements.txt
```

## Usage

### Development Mode
For testing and development, run the bot with debug output enabled:
```bash
python main.py --debug
```
This will:
- Save annotated screenshots showing match locations
- Log confidence scores for all matches
- Run at a faster scan interval (1 second)
- Not perform actual clicks

### Production Mode
For normal operation:
```bash
# Using the start script
./start_clickbot.sh

# Or directly with Python
python main.py
```

### Stopping the Bot
To stop the bot:
```bash
./stop_clickbot.sh
```

## Configuration
The bot can be configured through environment variables or command-line arguments:
- `--debug`: Enable development mode with visual debugging
- `--interval`: Set the scan interval in seconds (default: 3)
- `--confidence`: Set the minimum confidence threshold (default: 0.8)

## Debugging
Debug outputs are saved in:
- `debug_output/`: Annotated screenshots showing match locations
- `annotated_matches/`: Images showing detected matches with confidence scores
- `template_matching.log`: Detailed matching process logs

## Project Structure
- `clickbot/`: Main bot implementation
  - `main.py`: Core bot logic and monitor detection
  - `image_matcher.py`: Image matching algorithms
  - `requirements.txt`: Python dependencies
  - `start_clickbot.sh`: Startup script
  - `stop_clickbot.sh`: Shutdown script

## Contributing
This project is open to contributions from developers who share our vision of combining technical excellence with productivity optimization.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

