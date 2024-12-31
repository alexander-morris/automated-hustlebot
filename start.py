#!/usr/bin/env python3
import subprocess
import sys
import time
import json
import os
import signal
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
import pyautogui

class AutomationController:
    def __init__(self):
        self.composer_process = None
        self.app = QApplication(sys.argv)
        self.status_window = None
        self.config_file = 'clickbot_v2/config.json'
        
    def start_composer(self):
        print("🚀 Starting composer...")
        self.composer_process = subprocess.Popen(
            ["cursor"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(5)  # Give composer time to start
        
    def calibrate_clickbot(self):
        print("\n🎯 Starting ClickBot calibration...")
        print("Please follow the calibration steps:")
        
        # Wait for user to position cursor on accept button
        input("\n1. Move cursor to the ACCEPT button position and press Enter...")
        accept_pos = pyautogui.position()
        print(f"✅ Accept button position saved: ({accept_pos.x}, {accept_pos.y})")
        
        # Wait for user to define composer area
        input("\n2. Move cursor to the TOP-LEFT corner of the composer area and press Enter...")
        top_left = pyautogui.position()
        print(f"✅ Top-left corner saved: ({top_left.x}, {top_left.y})")
        
        input("\n3. Move cursor to the BOTTOM-RIGHT corner of the composer area and press Enter...")
        bottom_right = pyautogui.position()
        print(f"✅ Bottom-right corner saved: ({bottom_right.x}, {bottom_right.y})")
        
        # Save configuration
        config = {
            'accept_button': {'x': accept_pos.x, 'y': accept_pos.y},
            'composer_area': {
                'top_left': {'x': top_left.x, 'y': top_left.y},
                'bottom_right': {'x': bottom_right.x, 'y': bottom_right.y}
            }
        }
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print("\n💾 Configuration saved!")
        
    def show_status_window(self):
        if not self.status_window:
            self.status_window = StatusWindow()
        self.status_window.show()
        
    def start_monitoring(self):
        print("\n👀 Starting accept button monitoring...")
        self.show_status_window()
        
        try:
            while True:
                try:
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                except FileNotFoundError:
                    print("❌ Configuration not found. Starting calibration...")
                    self.calibrate_clickbot()
                    continue
                    
                # Check if cursor is in composer area
                pos = pyautogui.position()
                top_left = config['composer_area']['top_left']
                bottom_right = config['composer_area']['bottom_right']
                
                if (top_left['x'] <= pos.x <= bottom_right['x'] and 
                    min(top_left['y'], bottom_right['y']) <= pos.y <= max(top_left['y'], bottom_right['y'])):
                    # Click accept button
                    accept_pos = config['accept_button']
                    pyautogui.click(accept_pos['x'], accept_pos['y'])
                    print(f"🖱️  Clicked accept button at ({accept_pos['x']}, {accept_pos['y']})")
                    time.sleep(0.5)  # Small delay to prevent rapid clicking
                    
                self.app.processEvents()  # Keep the Qt event loop running
                time.sleep(0.1)  # Short sleep to prevent high CPU usage
                
        except KeyboardInterrupt:
            print("\n👋 Stopping automation...")
            if self.composer_process:
                self.composer_process.terminate()
            if self.status_window:
                self.status_window.close()
            sys.exit(0)

class StatusWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create status label
        self.label = QLabel(self)
        self.label.setStyleSheet("""
            QLabel { 
                color: green; 
                font-size: 14px; 
                background-color: rgba(0, 0, 0, 180); 
                padding: 5px; 
                border-radius: 5px; 
            }
        """)
        self.label.setText("🤖 Automation Active")
        self.label.move(10, 10)
        self.label.adjustSize()
        
        # Set window size
        self.resize(150, 40)
        
        # Position in bottom-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 50, 
                 screen.height() - self.height() - 50)

def main():
    print("🤖 Starting Automation System...")
    controller = AutomationController()
    
    try:
        controller.start_composer()
        if not os.path.exists(controller.config_file):
            controller.calibrate_clickbot()
        controller.start_monitoring()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if controller.composer_process:
            controller.composer_process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main() 