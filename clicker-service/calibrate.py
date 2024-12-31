#!/usr/bin/env python3
import pyautogui
import json
import time
import os
import sys

def calibrate():
    print("\n=== Cursor Accept Button Calibration ===")
    print("\n1. Move your mouse to the Cursor 'Accept' button position")
    print("2. Keep it there for 5 seconds")
    print("3. Don't move until calibration is complete\n")
    
    for i in range(5, 0, -1):
        sys.stdout.write(f"\rCalibrating in {i} seconds...")
        sys.stdout.flush()
        time.sleep(1)
    
    # Get the current mouse position
    x, y = pyautogui.position()
    print(f"\n\nCaptured position: x={x}, y={y}")
    
    # Save to config
    config = {'accept_button': {'x': x, 'y': y}}
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    print("\nConfiguration saved!")
    print("\nTesting position...")
    
    # Test the position
    current_x, current_y = pyautogui.position()
    pyautogui.moveTo(x, y, duration=0.2)
    time.sleep(0.5)
    pyautogui.moveTo(current_x, current_y, duration=0.2)
    
    print("\nCalibration complete! You can now run the autonomous system.")

if __name__ == "__main__":
    try:
        calibrate()
    except KeyboardInterrupt:
        print("\nCalibration cancelled.")
    except Exception as e:
        print(f"\nError during calibration: {str(e)}") 