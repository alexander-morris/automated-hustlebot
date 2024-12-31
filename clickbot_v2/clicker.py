#!/usr/bin/env python3
import json
import time
import sys
import pyautogui
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor

class ClickBot:
    def __init__(self):
        self.config = self.load_config()
        self.app = QApplication(sys.argv)
        self.status_window = None
        
    def load_config(self):
        try:
            with open('clickbot_v2/config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Configuration file not found. Please run calibrate.py first.")
            sys.exit(1)
            
    def click_accept_button(self):
        pos = self.config['accept_button']
        pyautogui.click(pos['x'], pos['y'])
        print(f"🖱️  Clicked accept button at ({pos['x']}, {pos['y']})")
        
    def is_cursor_in_composer(self):
        pos = pyautogui.position()
        top_left = self.config['composer_area']['top_left']
        bottom_right = self.config['composer_area']['bottom_right']
        
        return (top_left['x'] <= pos.x <= bottom_right['x'] and 
                min(top_left['y'], bottom_right['y']) <= pos.y <= max(top_left['y'], bottom_right['y']))
                
    def show_status(self):
        if not self.status_window:
            self.status_window = StatusWindow()
        self.status_window.show()
        
    def hide_status(self):
        if self.status_window:
            self.status_window.close()
            
    def run(self):
        print("Starting ClickBot...")
        print("Press Ctrl+C to exit")
        
        try:
            self.show_status()
            while True:
                if self.is_cursor_in_composer():
                    self.click_accept_button()
                time.sleep(0.5)  # Check every 500ms
                
        except KeyboardInterrupt:
            print("\n👋 ClickBot stopped")
            self.hide_status()
            sys.exit(0)
            
        finally:
            self.app.quit()

class StatusWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create status label
        self.label = QLabel(self)
        self.label.setStyleSheet("QLabel { color: green; font-size: 14px; background-color: rgba(0, 0, 0, 180); padding: 5px; border-radius: 5px; }")
        self.label.setText("ClickBot Active")
        self.label.move(10, 10)
        self.label.adjustSize()
        
        # Set window size
        self.resize(150, 40)
        
        # Position in bottom-right corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 50, 
                 screen.height() - self.height() - 50)

if __name__ == "__main__":
    bot = ClickBot()
    bot.run() 