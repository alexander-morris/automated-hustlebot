#!/usr/bin/env python3
import json
import sys
import pyautogui
import os
from PyQt5.QtWidgets import QApplication

def calibrate():
    """Run a quick calibration for the accept button position."""
    print("\n🎯 Quick Accept Button Calibration")
    print("Please follow the instructions:")
    
    # Wait for user to position cursor on accept button
    input("\nMove cursor to where the Accept button appears and press Enter...")
    accept_pos = pyautogui.position()
    print(f"✅ Accept button position saved: ({accept_pos.x}, {accept_pos.y})")
    
    # Save configuration
    config = {
        'accept_button': {'x': accept_pos.x, 'y': accept_pos.y},
        'composer_area': {
            'top_left': {'x': 0, 'y': 0},  # Default values
            'bottom_right': {'x': 0, 'y': 0}
        }
    }
    
    os.makedirs('clickbot_v2', exist_ok=True)
    with open('clickbot_v2/config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("\n💾 Configuration saved!")
    return config

def click_accept():
    try:
        # Initialize Qt application (needed for pyautogui)
        app = QApplication.instance() or QApplication(sys.argv)
        
        try:
            # Try to load configuration
            with open('clickbot_v2/config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print("⚙️  No configuration found. Starting quick calibration...")
            config = calibrate()
            
        # Get accept button position
        pos = config['accept_button']
        
        # Click the button
        pyautogui.click(pos['x'], pos['y'])
        print(f"🖱️  Clicked accept button at ({pos['x']}, {pos['y']})")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(click_accept()) 