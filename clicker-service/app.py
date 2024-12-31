#!/usr/bin/env python3
from flask import Flask, jsonify
import pyautogui
import logging
import time
from logging.handlers import RotatingFileHandler
import json
import os

# Important: Set pyautogui to fail-safe mode
pyautogui.FAILSAFE = True
# Add small pause between actions
pyautogui.PAUSE = 0.5

app = Flask(__name__)

# Configure logging with more detail
if not os.path.exists('logs'):
    os.makedirs('logs')

handler = RotatingFileHandler('logs/clicker.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s: %(message)s\n'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

def get_screen_info():
    """Get screen information for debugging"""
    screen_size = pyautogui.size()
    mouse_pos = pyautogui.position()
    return f"Screen size: {screen_size}, Current mouse: {mouse_pos}"

@app.route('/click/accept', methods=['POST'])
def click_accept():
    try:
        # Log current state
        app.logger.debug(f"Pre-click state: {get_screen_info()}")
        
        # Get coordinates from config
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
            coords = config['accept_button']
        
        app.logger.info(f"Moving to coordinates: {coords}")
        
        # Move mouse with safety checks
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(coords['x'], coords['y'], duration=0.2)
        time.sleep(0.1)  # Small pause
        
        # Click and verify
        pyautogui.click()
        time.sleep(0.1)  # Small pause
        
        # Move mouse back
        pyautogui.moveTo(current_x, current_y, duration=0.2)
        
        app.logger.debug(f"Post-click state: {get_screen_info()}")
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"Click failed: {str(e)}\n{get_screen_info()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/calibrate', methods=['GET'])
def get_current_pos():
    """Get current mouse position for calibration"""
    x, y = pyautogui.position()
    return jsonify({'x': x, 'y': y})

@app.route('/calibrate/save', methods=['POST'])
def save_current_pos():
    """Save current mouse position as accept button location"""
    try:
        x, y = pyautogui.position()
        config = {'accept_button': {'x': x, 'y': y}}
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f)
        app.logger.info(f"Saved new coordinates: x={x}, y={y}")
        return jsonify({'status': 'success', 'x': x, 'y': y})
    except Exception as e:
        app.logger.error(f"Calibration failed: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.logger.info(f"Starting clicker service\n{get_screen_info()}")
    app.run(port=3333, debug=True) 