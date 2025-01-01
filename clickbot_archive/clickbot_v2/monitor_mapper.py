#!/usr/bin/env python3
import mss
import numpy as np
from PIL import Image
import pytesseract
import pyautogui
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor
import sys
import time

class CursorTracer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.label = QLabel(self)
        self.label.setStyleSheet("QLabel { color: white; background-color: rgba(0, 0, 0, 150); padding: 5px; border-radius: 5px; }")
        self.resize(200, 30)
        self.show()
        
        # Update position every 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_position)
        self.timer.start(100)
        
    def update_position(self):
        pos = pyautogui.position()
        self.move(pos.x + 20, pos.y + 20)  # Offset from cursor
        self.label.setText(f"Cursor: ({pos.x}, {pos.y})")
        self.label.adjustSize()

class MonitorMapper:
    def __init__(self):
        self.sct = mss.mss()
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.tracer = None
        
    def find_menu_text(self, monitor, save_debug=False):
        """Try to find menu text in the top-left corner of a monitor."""
        # Capture top-left area
        area = {
            "left": monitor["left"],
            "top": monitor["top"],
            "width": 800,  # Wide enough to catch menu items
            "height": 25   # Tall enough for menu bar
        }
        screenshot = self.sct.grab(area)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        
        if save_debug:
            debug_path = f'monitor_{monitor["left"]}_{monitor["top"]}_orig.png'
            img.save(debug_path)
            print(f"💾 Saved original: {debug_path}")
        
        # Process for text detection
        img_array = np.array(img)
        
        # Try both light text on dark and dark text on light
        results = []
        
        # Light text on dark background
        text_mask = np.all((img_array >= [215, 215, 215]), axis=2)
        result = np.zeros_like(img_array)
        result[text_mask] = [255, 255, 255]
        
        if save_debug:
            debug_path = f'monitor_{monitor["left"]}_{monitor["top"]}_light.png'
            Image.fromarray(result).save(debug_path)
            print(f"💾 Saved light text: {debug_path}")
        
        # Scale up for better OCR
        result_pil = Image.fromarray(result)
        result_pil = result_pil.resize((result_pil.width * 2, result_pil.height * 2))
        
        # Try different PSM modes
        for psm in [7, 6]:  # Line and uniform block modes
            text = pytesseract.image_to_string(
                result_pil,
                config=f'--psm {psm}'
            ).strip().lower()
            if text:
                results.append(text)
        
        # Dark text on light background
        text_mask = np.all((img_array <= [40, 40, 40]), axis=2)
        result = np.zeros_like(img_array)
        result[text_mask] = [255, 255, 255]
        
        if save_debug:
            debug_path = f'monitor_{monitor["left"]}_{monitor["top"]}_dark.png'
            Image.fromarray(result).save(debug_path)
            print(f"💾 Saved dark text: {debug_path}")
        
        # Scale up for better OCR
        result_pil = Image.fromarray(result)
        result_pil = result_pil.resize((result_pil.width * 2, result_pil.height * 2))
        
        # Try different PSM modes
        for psm in [7, 6]:  # Line and uniform block modes
            text = pytesseract.image_to_string(
                result_pil,
                config=f'--psm {psm}'
            ).strip().lower()
            if text:
                results.append(text)
        
        return results
    
    def map_monitors(self):
        """Map all monitors and find which one has the Cursor menu."""
        print("\n🖥️  Mapping Monitors...")
        
        # Skip first monitor (represents all monitors combined)
        for i, monitor in enumerate(self.sct.monitors[1:], 1):
            print(f"\nMonitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            texts = self.find_menu_text(monitor, save_debug=True)
            print(f"Found text: {texts}")
            
            # Look for menu-like words
            menu_words = ['file', 'edit', 'view', 'window', 'help', 'cursor']
            for text in texts:
                if any(word in text for word in menu_words):
                    print(f"🎯 Found menu text on Monitor {i}!")
                    print(f"Text: {text}")
                    return monitor
        
        print("❌ Could not find menu bar on any monitor")
        return None
    
    def start_cursor_tracing(self):
        """Start tracing the cursor position."""
        print("\n🖱️  Starting cursor tracer...")
        print("Move your cursor around to see coordinates")
        print("Press Ctrl+C to stop")
        
        self.tracer = CursorTracer()
        
        try:
            self.app.exec_()
        except KeyboardInterrupt:
            print("\n👋 Stopped tracing")
    
    def run(self):
        """Run the monitor mapping process."""
        try:
            cursor_monitor = self.map_monitors()
            if cursor_monitor:
                print("\n✅ Found Cursor menu!")
                print(f"Monitor: {cursor_monitor['width']}x{cursor_monitor['height']} at ({cursor_monitor['left']}, {cursor_monitor['top']})")
                
                print("\nStarting cursor tracer to help with positioning...")
                self.start_cursor_tracing()
            
            return 0
        except KeyboardInterrupt:
            print("\n👋 Stopped mapping")
            return 0
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1

def main():
    mapper = MonitorMapper()
    return mapper.run()

if __name__ == "__main__":
    sys.exit(main()) 