#!/usr/bin/env python3
import sys
import json
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor
from Quartz import NSEvent, NSSystemDefined

def get_cursor_position():
    pos = NSEvent.mouseLocation()
    return {'x': int(pos.x), 'y': int(NSEvent.mouseLocation().y)}

class CoordinateLabel(QWidget):
    def __init__(self):
        super().__init__()
        # Make it a small floating window that stays on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create the coordinate display label
        self.label = QLabel(self)
        self.label.setStyleSheet("QLabel { color: red; font-size: 18px; background-color: rgba(0, 0, 0, 180); padding: 5px; border-radius: 5px; }")
        self.label.move(10, 10)
        
        # Set initial size
        self.resize(200, 50)
        
        # Timer for updating coordinates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_coordinates)
        self.update_timer.start(100)  # Update every 100ms
        
        # Position the window in the top-left corner
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.x() + 50, screen.y() + 50)
        
    def update_coordinates(self):
        pos = get_cursor_position()
        self.label.setText(f"({pos['x']}, {pos['y']})")
        self.label.adjustSize()

class ClickBotCalibrator:
    def __init__(self):
        self.config = {
            'accept_button': None,
            'composer_area': {
                'top_left': None,
                'bottom_right': None
            }
        }
        self.app = QApplication(sys.argv)
        self.coord_label = None
        
    def wait_for_input(self, prompt):
        print(prompt)
        input("Press Enter when ready to capture position...")
        pos = get_cursor_position()
        print(f"\n🎯 Position locked at: ({pos['x']}, {pos['y']})")
        return pos
        
    def calibrate_accept_button(self):
        print("\nStep 1: Calibrating Accept Button Position")
        print("Move your cursor to the accept button position")
        pos = self.wait_for_input("Position your cursor and press Enter to capture")
        self.config['accept_button'] = {'x': pos['x'], 'y': pos['y']}
        print("✅ Accept button position saved!")
        
    def calibrate_composer_area(self):
        print("\nStep 2: Calibrating Composer Area")
        print("Move your cursor to the TOP-LEFT corner of the composer area")
        top_left = self.wait_for_input("Position your cursor at the top-left corner and press Enter to capture")
        self.config['composer_area']['top_left'] = {'x': top_left['x'], 'y': top_left['y']}
        print("✅ Top-left corner saved!")
        
        print("\nMove your cursor to the BOTTOM-RIGHT corner of the composer area")
        bottom_right = self.wait_for_input("Position your cursor at the bottom-right corner and press Enter to capture")
        self.config['composer_area']['bottom_right'] = {'x': bottom_right['x'], 'y': bottom_right['y']}
        print("✅ Bottom-right corner saved!")
        
        print(f"\nComposer area boundaries:")
        print(f"• Top-left: ({top_left['x']}, {top_left['y']})")
        print(f"• Bottom-right: ({bottom_right['x']}, {bottom_right['y']})")
        
    def show_coordinate_label(self):
        self.coord_label = CoordinateLabel()
        self.coord_label.show()
        
    def hide_coordinate_label(self):
        if self.coord_label:
            self.coord_label.close()
        
    def save_config(self):
        with open('clickbot_v2/config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        print("\n💾 Configuration saved to clickbot_v2/config.json")
        
    def run_calibration(self):
        print("Starting ClickBot Calibration...")
        print("Coordinates will be shown in the top-left corner")
        print("Move your cursor to each position and press Enter to capture")
        
        try:
            self.show_coordinate_label()
            self.calibrate_accept_button()
            self.calibrate_composer_area()
            self.hide_coordinate_label()
            self.save_config()
            print("\n🎉 Calibration completed successfully!")
            
        except KeyboardInterrupt:
            print("\n❌ Calibration cancelled by user")
            self.hide_coordinate_label()
            sys.exit(1)
            
        finally:
            self.app.quit()

if __name__ == "__main__":
    calibrator = ClickBotCalibrator()
    calibrator.run_calibration() 