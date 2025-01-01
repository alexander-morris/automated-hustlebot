"""
Monitor detection module for finding Cursor instances
"""
import mss
import numpy as np
import cv2
from PIL import Image
import pytesseract
import time

class CursorMonitor:
    def __init__(self):
        self.sct = mss.mss()
        self.last_cursor_monitor = None
        
    def find_cursor_window(self):
        """
        Scan all monitors for a Cursor window.
        Returns: Monitor dict if found, None if not found
        """
        print("\nScanning monitors for Cursor window...")
        
        # Skip first monitor (represents all monitors combined)
        for i, monitor in enumerate(self.sct.monitors[1:], 1):
            print(f"\nChecking monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            # Capture top portion of monitor where title would be
            title_region = {
                'left': monitor['left'],
                'top': monitor['top'],
                'width': monitor['width'],
                'height': 100  # Just capture top portion
            }
            
            screenshot = self.sct.grab(title_region)
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Save debug image
            debug_path = f'debug_monitor_{i}_title.png'
            img.save(debug_path)
            print(f"Saved debug image: {debug_path}")
            
            # Try both light and dark text detection
            text = self._detect_text(img)
            print(f"Found text: {text}")
            
            if any('cursor' in t.lower() for t in text):
                print(f"Found Cursor on monitor {i}!")
                self.last_cursor_monitor = monitor
                return monitor
        
        print("No Cursor window found on any monitor")
        return None
    
    def _detect_text(self, img):
        """Detect both light and dark text in image"""
        results = []
        img_array = np.array(img)
        
        # Light text on dark background
        light_mask = np.all((img_array >= [200, 200, 200]), axis=2)
        light_result = np.zeros_like(img_array)
        light_result[light_mask] = [255, 255, 255]
        
        # Dark text on light background
        dark_mask = np.all((img_array <= [50, 50, 50]), axis=2)
        dark_result = np.zeros_like(img_array)
        dark_result[dark_mask] = [255, 255, 255]
        
        # Try OCR on both
        for result in [light_result, dark_result]:
            result_pil = Image.fromarray(result)
            text = pytesseract.image_to_string(result_pil).strip().split('\n')
            results.extend([t for t in text if t.strip()])
        
        return results
    
    def get_cursor_region(self):
        """
        Get the region of the last found Cursor window
        Returns: Region dict or None if not found
        """
        if not self.last_cursor_monitor:
            return None
            
        # Return full monitor region for now
        return self.last_cursor_monitor 