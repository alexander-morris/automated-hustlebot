#!/usr/bin/env python3
import json
import sys
import os
import time
import mss
import numpy as np
from PIL import Image
import pytesseract
from PyQt5.QtWidgets import QApplication
import pyautogui

class AcceptButtonWatcher:
    def __init__(self):
        self.sct = mss.mss()
        # Find the monitor with the Cursor menu bar
        self.monitor = None
        for mon in self.sct.monitors[1:]:  # Skip the "all monitors" monitor
            if self.check_for_cursor_menu(mon):
                self.monitor = mon
                break
        if not self.monitor:
            self.monitor = self.sct.monitors[1]  # Fallback to primary
            
        self.config_file = 'clickbot_v2/config.json'
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.last_status_time = 0
        self.status_interval = 5
        
    def check_for_cursor_menu(self, monitor):
        """Check if this monitor contains the Cursor menu."""
        # Capture top-left area where Cursor menu should be
        area = {
            "left": monitor["left"],
            "top": monitor["top"],
            "width": 200,
            "height": 25
        }
        screenshot = self.sct.grab(area)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        
        # Process for text detection
        img_array = np.array(img)
        text_mask = np.all((img_array >= [215, 215, 215]), axis=2)
        result = np.zeros_like(img_array)
        result[text_mask] = [255, 255, 255]
        result_pil = Image.fromarray(result)
        result_pil = result_pil.resize((result_pil.width * 2, result_pil.height * 2))
        
        # Check for "Cursor" text
        text = pytesseract.image_to_string(result_pil, config='--psm 7').strip().lower()
        return 'cursor' in text
        
    def calibrate(self):
        """Run calibration using Cursor menu as reference."""
        print("\n🎯 Calibration Process")
        print("First, let's verify the Cursor menu location...")
        
        # Capture and verify Cursor menu area
        menu_area = {
            "left": self.monitor["left"],
            "top": self.monitor["top"],
            "width": 200,
            "height": 25
        }
        screenshot = self.sct.grab(menu_area)
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        debug_path = 'cursor_menu_debug.png'
        img.save(debug_path)
        print(f"💾 Saved menu area image: {debug_path}")
        
        # Now get accept button position
        print("\nNow, move cursor to where the Accept/⌘ symbol appears and press Enter...")
        input("Press Enter when ready...")
        pos = pyautogui.position()
        
        # Calculate position relative to monitor
        rel_x = pos.x - self.monitor["left"]
        rel_y = pos.y - self.monitor["top"]
        print(f"✅ Button position saved: ({rel_x}, {rel_y}) relative to monitor")
        
        # Save configuration with relative coordinates
        config = {
            'monitor_offset': {
                'x': self.monitor["left"],
                'y': self.monitor["top"]
            },
            'accept_button': {
                'x': rel_x,
                'y': rel_y
            },
            'button_area': {
                'x': rel_x - 200,
                'y': rel_y - 50,
                'width': 400,
                'height': 100
            }
        }
        
        print(f"\n📏 Scanning area: {config['button_area']['width']}x{config['button_area']['height']} pixels")
        print(f"   centered at ({rel_x}, {rel_y}) relative to monitor at ({self.monitor['left']}, {self.monitor['top']})")
        
        os.makedirs('clickbot_v2', exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print("\n💾 Configuration saved!")
        return config
        
    def preprocess_image(self, screenshot):
        """Preprocess the image for better OCR results."""
        # Convert to PIL Image
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        
        # Convert to numpy array for processing
        img_array = np.array(img)
        
        # Create mask for light text on dark background (inverted)
        text_mask = np.all((img_array >= [215, 215, 215]), axis=2)  # Looking for light text
        
        # Create white text on black background
        result = np.zeros_like(img_array)
        result[text_mask] = [255, 255, 255]
        
        # Scale up for better OCR
        result_pil = Image.fromarray(result)
        result_pil = result_pil.resize((result_pil.width * 2, result_pil.height * 2))
        
        # Save debug image with timestamp
        debug_path = f'debug_text_{int(time.time())}.png'
        result_pil.save(debug_path)
        print(f"💾 Saved debug image: {debug_path}")
        return result_pil
        
    def read_text(self, screenshot):
        """Use OCR to read text from the screenshot."""
        # Preprocess the image
        processed_img = self.preprocess_image(screenshot)
        
        # Use Tesseract with specific config for better results
        custom_config = '--psm 7'  # Single line mode
        text = pytesseract.image_to_string(processed_img, config=custom_config).strip().lower()
        
        # Print all text found, even if empty
        if text:
            print(f"📝 Found text: '{text}'")
        else:
            print("📝 No text detected in this frame")
        return text
        
    def is_accept_button(self, screenshot, text):
        """Check if the text contains 'accept' or '⌘'."""
        has_accept = 'accept' in text or '⌘' in text
        if has_accept:
            print("🎯 Accept button detected!")
        return has_accept
        
    def print_status(self, force=False):
        """Print status update if enough time has passed."""
        current_time = time.time()
        if force or (current_time - self.last_status_time) >= self.status_interval:
            print("👀 Watching for Accept/⌘ buttons... (Press Ctrl+C to stop)")
            self.last_status_time = current_time
        
    def click_position(self, rel_x, rel_y):
        """Click at the given coordinates relative to monitor."""
        abs_x = self.monitor["left"] + rel_x
        abs_y = self.monitor["top"] + rel_y
        pyautogui.click(abs_x, abs_y)
        print(f"🖱️  Clicked at ({abs_x}, {abs_y})")
        
    def watch_and_click(self):
        try:
            # Load or create configuration
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except FileNotFoundError:
                print("⚙️  No configuration found. Starting calibration...")
                config = self.calibrate()
            
            print("\n👀 Starting button watch...")
            print("Will click when 'Accept' or '⌘' is detected")
            print("Press Ctrl+C to stop")
            
            button_area = config['button_area']
            accept_pos = config['accept_button']
            checks = 0
            
            while True:
                # Capture the button area (using monitor-relative coordinates)
                screenshot = self.sct.grab({
                    'left': self.monitor["left"] + button_area['x'],
                    'top': self.monitor["top"] + button_area['y'],
                    'width': button_area['width'],
                    'height': button_area['height']
                })
                
                # Read and check text
                text = self.read_text(screenshot)
                if self.is_accept_button(screenshot, text):
                    print(f"🎯 Found accept button! Text: '{text}'")
                    self.click_position(accept_pos['x'], accept_pos['y'])
                    time.sleep(0.5)  # Wait before checking again
                
                checks += 1
                if checks % 10 == 0:  # Print status every 10 checks
                    self.print_status()
                    
                time.sleep(0.2)  # Check every 200ms
                
        except KeyboardInterrupt:
            print("\n👋 Stopped watching")
            return 0
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1

def main():
    watcher = AcceptButtonWatcher()
    return watcher.watch_and_click()

if __name__ == "__main__":
    sys.exit(main()) 