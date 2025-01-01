"""
Accept button watcher module for finding and clicking accept buttons
"""
import cv2
import numpy as np
from PIL import Image
import pytesseract
import pyautogui
import time

class AcceptWatcher:
    def __init__(self):
        # Coordinates of last found accept button
        self.last_accept_pos = None
        # Time of last click
        self.last_click_time = 0
        # Minimum time between clicks (seconds)
        self.click_cooldown = 2.0
        
    def find_accept_button(self, screenshot, base_x=0, base_y=0):
        """
        Find an accept button in the screenshot
        Returns: (x, y) coordinates relative to base_x,base_y or None if not found
        """
        try:
            # Convert to numpy array
            img_array = np.array(screenshot)
            
            # Try both light and dark text detection
            text_regions = self._find_text_regions(img_array)
            
            # Look for accept-related text
            accept_keywords = ['accept', 'approve', 'confirm', 'yes', 'ok']
            
            for region, text in text_regions:
                if any(keyword in text.lower() for keyword in accept_keywords):
                    x, y, w, h = region
                    # Center of the button
                    center_x = base_x + x + w//2
                    center_y = base_y + y + h//2
                    print(f"Found accept button with text: {text} at ({center_x}, {center_y})")
                    self.last_accept_pos = (center_x, center_y)
                    return (center_x, center_y)
            
            return None
            
        except Exception as e:
            print(f"Error finding accept button: {str(e)}")
            return None
    
    def _find_text_regions(self, img_array):
        """Find regions containing text and return (region, text) pairs"""
        results = []
        
        # Light text on dark background
        light_mask = np.all((img_array >= [200, 200, 200]), axis=2)
        light_result = np.zeros_like(img_array)
        light_result[light_mask] = [255, 255, 255]
        
        # Dark text on light background
        dark_mask = np.all((img_array <= [50, 50, 50]), axis=2)
        dark_result = np.zeros_like(img_array)
        dark_result[dark_mask] = [255, 255, 255]
        
        # Process both light and dark results
        for result in [light_result, dark_result]:
            # Convert to grayscale
            gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
            
            # Find contours
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Process each contour
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Skip if too small or too large for a button
                if w < 40 or h < 20 or w > 200 or h > 100:
                    continue
                
                # Extract region and get text
                region_img = Image.fromarray(result[y:y+h, x:x+w])
                text = pytesseract.image_to_string(region_img).strip()
                
                if text:
                    results.append(((x, y, w, h), text))
        
        return results
    
    def try_click_accept(self):
        """Try to click the last found accept button"""
        if not self.last_accept_pos:
            return False
            
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            print("Waiting for click cooldown...")
            return False
            
        try:
            x, y = self.last_accept_pos
            print(f"Clicking accept button at ({x}, {y})")
            
            # Move to button
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.2)
            
            # Click
            pyautogui.click(x, y)
            self.last_click_time = current_time
            return True
            
        except Exception as e:
            print(f"Error clicking accept button: {str(e)}")
            return False 