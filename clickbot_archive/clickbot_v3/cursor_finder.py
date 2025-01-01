import mss
import numpy as np
from PIL import Image
import pyautogui
import time
from datetime import datetime

class CursorFinder:
    def __init__(self):
        self.sct = mss.mss()
        self.cursor_monitor = None
        # Speed up mouse movement
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0
        pyautogui.PAUSE = 0
        
    def log(self, message):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
        
    def find_cursor_window(self):
        """Find monitor with Cursor window"""
        try:
            # Skip first monitor (represents all monitors combined)
            for i, monitor in enumerate(self.sct.monitors[1:], 1):
                # Capture full monitor
                screenshot = self.sct.grab(monitor)
                img_array = np.array(screenshot)
                
                # Convert BGRA to RGB
                img_array = img_array[:, :, [2,1,0]]
                
                # Look for dark theme UI colors (background should be dark)
                dark_mask = np.all(img_array <= [30, 30, 30], axis=2)
                dark_pixel_ratio = np.sum(dark_mask) / (monitor['width'] * monitor['height'])
                
                # If more than 50% dark pixels, likely the Cursor window
                if dark_pixel_ratio > 0.5:
                    self.log(f"Found Cursor window at ({monitor['left']}, {monitor['top']}) - Size: {monitor['width']}x{monitor['height']}")
                    self.cursor_monitor = monitor
                    return monitor
                    
            return None
            
        except Exception as e:
            self.log(f"Error scanning monitors: {str(e)}")
            return None
            
    def click_cursor_dropdown(self):
        """Click Cursor dropdown in top left"""
        if not self.cursor_monitor:
            return False
            
        try:
            # Top left corner of window
            x = self.cursor_monitor['left'] + 50  # Offset for Cursor dropdown
            y = self.cursor_monitor['top'] + 20   # Offset from top
            
            # Store current mouse position
            original_x, original_y = pyautogui.position()
            
            # Move and click
            pyautogui.moveTo(x, y, duration=0)
            pyautogui.click(x, y)
            self.log(f"Clicked Cursor dropdown at ({x}, {y})")
            
            # Restore position
            pyautogui.moveTo(original_x, original_y, duration=0)
            return True
            
        except Exception as e:
            self.log(f"Error clicking Cursor dropdown: {str(e)}")
            return False
            
    def find_composer_region(self):
        """Find composer title (pink underline) in top right"""
        if not self.cursor_monitor:
            return None
            
        try:
            # Calculate absolute coordinates for top right portion
            monitor_right = self.cursor_monitor['left'] + self.cursor_monitor['width']
            composer_width = int(self.cursor_monitor['width'] * 0.3)
            composer_region = {
                'left': monitor_right - composer_width,  # Start from right edge
                'top': self.cursor_monitor['top'],
                'width': composer_width,
                'height': 40  # Only top 40 pixels
            }
            
            self.log(f"Scanning for composer line in region: {composer_region['width']}x{composer_region['height']} at ({composer_region['left']}, {composer_region['top']})")
            
            screenshot = self.sct.grab(composer_region)
            img_array = np.array(screenshot)
            
            # Convert BGRA to RGB
            img_array = img_array[:, :, [2,1,0]]
            
            # Look for exact pink color (251, 120, 198) with small tolerance for anti-aliasing
            pink_mask = np.all((
                (img_array[:, :, 0] >= 245) & (img_array[:, :, 0] <= 255) &  # R: 251 ±6
                (img_array[:, :, 1] >= 115) & (img_array[:, :, 1] <= 125) &  # G: 120 ±5
                (img_array[:, :, 2] >= 193) & (img_array[:, :, 2] <= 203)    # B: 198 ±5
            ), axis=0)
            
            pink_count = np.sum(pink_mask)
            self.log(f"Found {pink_count} pixels matching exact pink color")
            
            if pink_count == 0:
                self.log("No matching pink pixels found")
                return None
            
            # Find connected components
            from scipy import ndimage
            labeled_array, num_features = ndimage.label(pink_mask)
            self.log(f"Found {num_features} pink components")
            
            # Look for horizontal line components
            for i in range(1, num_features + 1):
                component_mask = labeled_array == i
                y_coords, x_coords = np.where(component_mask)
                if len(y_coords) == 0:
                    continue
                    
                # Get component dimensions
                width = np.max(x_coords) - np.min(x_coords)
                height = np.max(y_coords) - np.min(y_coords)
                
                self.log(f"Component {i}: {width}x{height} pixels")
                
                # Look for components that are:
                # - At least 10 pixels wide
                # - 1-2 pixels high (allowing for some anti-aliasing)
                if width >= 10 and height <= 2:
                    center_x = int(np.mean(x_coords))
                    center_y = int(np.mean(y_coords))
                    screen_x = composer_region['left'] + center_x
                    screen_y = composer_region['top'] + center_y
                    self.log(f"Found pink line: {width}x{height} at ({screen_x}, {screen_y})")
                    return (screen_x, screen_y)
            
            self.log("No suitable pink line found")
            return None
            
        except Exception as e:
            self.log(f"Error finding composer: {str(e)}")
            return None
            
    def find_accept_button(self):
        """Find Accept button (white text on light gray) on right side"""
        if not self.cursor_monitor:
            return None
            
        try:
            # Focus on right side of window
            right_region = {
                'left': self.cursor_monitor['left'] + int(self.cursor_monitor['width'] * 0.8),
                'top': self.cursor_monitor['top'],
                'width': int(self.cursor_monitor['width'] * 0.2),
                'height': self.cursor_monitor['height']
            }
            
            screenshot = self.sct.grab(right_region)
            img_array = np.array(screenshot)
            
            # Convert BGRA to RGB
            img_array = img_array[:, :, [2,1,0]]
            
            # Look for light gray background
            gray_mask = np.all((img_array >= [220, 220, 220]) & (img_array <= [240, 240, 240]), axis=2)
            
            # Find connected components
            from scipy import ndimage
            labeled_array, num_features = ndimage.label(gray_mask)
            
            # Look for button-sized regions
            for i in range(1, num_features + 1):
                component_mask = labeled_array == i
                y_coords, x_coords = np.where(component_mask)
                if len(y_coords) == 0:
                    continue
                    
                width = np.max(x_coords) - np.min(x_coords)
                height = np.max(y_coords) - np.min(y_coords)
                
                # Check if component has button-like properties
                if (50 < width < 200 and 20 < height < 50):
                    center_x = int(np.mean(x_coords))
                    center_y = int(np.mean(y_coords))
                    screen_x = right_region['left'] + center_x
                    screen_y = right_region['top'] + center_y
                    self.log(f"Found Accept button at ({screen_x}, {screen_y})")
                    return (screen_x, screen_y)
            
            return None
            
        except Exception as e:
            self.log(f"Error finding Accept button: {str(e)}")
            return None

def main():
    finder = CursorFinder()
    
    # Find Cursor window
    if not finder.find_cursor_window():
        return
        
    # Click Cursor dropdown
    finder.click_cursor_dropdown()
    time.sleep(0.5)  # Wait for dropdown
    
    # Find composer region
    composer_pos = finder.find_composer_region()
    if not composer_pos:
        finder.log("Could not find composer region")
        return
        
    # Start monitoring for Accept button
    while True:
        accept_pos = finder.find_accept_button()
        if accept_pos:
            # Store current mouse position
            original_x, original_y = pyautogui.position()
            
            # Click Accept button
            pyautogui.moveTo(accept_pos[0], accept_pos[1], duration=0)
            pyautogui.click()
            finder.log("Clicked Accept button")
            
            # Restore mouse position
            pyautogui.moveTo(original_x, original_y, duration=0)
            time.sleep(1)  # Wait before next scan
            
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped") 