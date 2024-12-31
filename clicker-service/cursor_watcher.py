#!/usr/bin/env python3
import mss
import numpy as np
import logging
import time
from mss import tools
import pyautogui
import subprocess
import sys
import os
import traceback

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cursor_watcher.log', mode='w'),
        logging.StreamHandler()
    ]
)

# Import button finder with error handling
try:
    from button_finder import ButtonFinder
    logging.info("Successfully imported ButtonFinder")
except ImportError as e:
    logging.error(f"Failed to import ButtonFinder: {str(e)}")
    logging.error(traceback.format_exc())
    sys.exit(1)

class CursorWatcher:
    def __init__(self):
        try:
            self.check_permissions()
            self.sct = mss.mss()
            self.button_finder = ButtonFinder()
            # Dark mode Cursor colors with wider tolerance
            self.colors = {
                'background': [(20, 20, 20), (40, 40, 40)],  # Dark gray background range
                'text': [(180, 180, 180), (220, 220, 220)],  # Light gray text range
                'composer': [(35, 35, 35), (55, 55, 55)]     # Composer background range
            }
            self.window_region = None
            self.composer_region = None
            logging.info("CursorWatcher initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize CursorWatcher: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def check_permissions(self):
        """Check and request screen recording permissions"""
        logging.info("Checking screen recording permissions...")
        
        try:
            # Try to take a test screenshot
            with mss.mss() as sct:
                sct.shot()
        except mss.exception.ScreenShotError:
            logging.warning("Screen recording permission not granted")
            
            # Prompt user to grant permission
            print("\nScreen Recording Permission Required")
            print("1. Open System Preferences > Security & Privacy > Privacy")
            print("2. Select 'Screen Recording' from the left sidebar")
            print("3. Add and enable Python/Terminal in the right panel")
            
            # Open System Preferences directly to the right location
            subprocess.run([
                'open', 
                'x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture'
            ])
            
            input("\nPress Enter after granting permission (you'll need to restart the script)...")
            sys.exit(0)
            
        logging.info("Screen recording permission granted")

    def find_cursor_window(self):
        """Locate the Cursor application window"""
        start_time = time.time()
        timeout = 10
        
        logging.info("Starting Cursor window search with elevated permissions...")
        
        # First try using accessibility APIs if available
        try:
            import Quartz
            logging.info("Using Quartz accessibility API")
            
            # Get screen dimensions
            main_monitor = self.sct.monitors[0]
            screen_width = main_monitor['width']
            screen_height = main_monitor['height']
            logging.info(f"Screen dimensions: {screen_width}x{screen_height}")
            
            # Get all windows
            windows = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID
            )
            
            # Look for Cursor window
            cursor_windows = []
            for window in windows:
                name = window.get(Quartz.kCGWindowName, '')
                owner = window.get(Quartz.kCGWindowOwnerName, '')
                
                if 'Cursor' in owner or 'Cursor' in str(name):
                    bounds = window.get(Quartz.kCGWindowBounds)
                    height = int(bounds['Height'])
                    
                    # Only consider windows that are tall enough to be the main window
                    if height > 100:  # Main window should be taller than title bar
                        cursor_windows.append((bounds, height))
                        logging.info(f"Found potential Cursor window: {bounds}")
            
            if cursor_windows:
                # Use the tallest window (most likely to be the main window)
                bounds, _ = max(cursor_windows, key=lambda x: x[1])
                logging.info(f"Selected main Cursor window: {bounds}")
                
                # Handle negative coordinates by using absolute values
                x = int(bounds['X'])
                y = int(bounds['Y'])
                width = int(bounds['Width'])
                height = int(bounds['Height'])
                
                # Convert negative coordinates to positive screen coordinates
                if x < 0:
                    x = screen_width + x
                if y < 0:
                    y = screen_height + y
                    
                # Adjust for menu bar height (typically 25 pixels on macOS)
                menu_bar_height = 25
                if y < menu_bar_height:
                    y = menu_bar_height
                    height = height - menu_bar_height
                
                # Ensure window is within screen bounds
                x = max(0, min(x, screen_width - width))
                y = max(menu_bar_height, min(y, screen_height - height))
                width = min(width, screen_width - x)
                height = min(height, screen_height - y)
                
                self.window_region = {
                    'top': y,
                    'left': x,
                    'width': width,
                    'height': height
                }
                
                logging.info(f"Adjusted window region: {self.window_region}")
                return True
            else:
                logging.warning("No suitable Cursor windows found via Quartz")
                    
        except ImportError:
            logging.warning("Quartz API not available, falling back to pixel search")
            
        # Fall back to pixel search method
        for monitor_num, monitor in enumerate(self.sct.monitors[1:], 1):
            logging.info(f"Checking monitor {monitor_num}: {monitor}")
            
            try:
                screen = self.sct.grab(monitor)
                img = np.array(screen)
                
                # Save debug screenshot for this monitor
                timestamp = time.strftime("%H%M%S")
                tools.to_png(screen.rgb, screen.size, 
                            output=f'debug_monitor_{monitor_num}_{timestamp}.png')
                
                logging.debug(f"Monitor {monitor_num} size: {img.shape}")
                
                # Look for dark regions (Cursor's dark theme)
                dark_pixels = np.where(
                    (img[:, :, 0] >= 20) & (img[:, :, 0] <= 70) &
                    (img[:, :, 1] >= 20) & (img[:, :, 1] <= 70) &
                    (img[:, :, 2] >= 20) & (img[:, :, 2] <= 70)
                )
                
                if len(dark_pixels[0]) > 0:
                    logging.info(f"Found {len(dark_pixels[0])} dark pixels on monitor {monitor_num}")
                    
                    # Group nearby dark pixels into regions
                    regions = []
                    current_region = []
                    
                    for y, x in zip(dark_pixels[0], dark_pixels[1]):
                        if time.time() - start_time > timeout:
                            logging.warning("Search timeout reached")
                            return False
                            
                        if not current_region:
                            current_region = [(x, y)]
                        elif abs(x - current_region[-1][0]) < 100 and abs(y - current_region[-1][1]) < 100:
                            current_region.append((x, y))
                        else:
                            if len(current_region) > 1000:  # Minimum region size
                                regions.append(current_region)
                            current_region = [(x, y)]
                    
                    if regions:
                        # Find largest contiguous dark region
                        largest_region = max(regions, key=len)
                        x_coords, y_coords = zip(*largest_region)
                        
                        # Calculate window bounds
                        x = min(x_coords) + monitor['left']
                        y = min(y_coords) + monitor['top']
                        width = max(x_coords) - min(x_coords)
                        height = max(y_coords) - min(y_coords)
                        
                        # Adjust for menu bar and screen bounds
                        menu_bar_height = 25
                        if y < menu_bar_height:
                            y = menu_bar_height
                            height = height - menu_bar_height
                            
                        x = max(0, min(x, screen_width - width))
                        y = max(menu_bar_height, min(y, screen_height - height))
                        width = min(width, screen_width - x)
                        height = min(height, screen_height - y)
                        
                        self.window_region = {
                            'top': y,
                            'left': x,
                            'width': width,
                            'height': height
                        }
                        
                        logging.info(f"Found Cursor window on monitor {monitor_num}: {self.window_region}")
                        return True
                    
            except Exception as e:
                logging.error(f"Error processing monitor {monitor_num}: {str(e)}")
                if time.time() - start_time > timeout:
                    break
        
        logging.warning("Could not find Cursor window on any monitor")
        return False
        
    def find_composer_area(self):
        """Locate the composer area within the Cursor window"""
        if not self.window_region:
            if not self.find_cursor_window():
                return False
                
        try:
            # Take a screenshot using mss
            logging.info("Taking screenshot with mss")
            with mss.mss() as sct:
                window = sct.grab(self.window_region)
                img = np.array(window)
                
                # Save debug screenshot
                mss.tools.to_png(window.rgb, window.size, output='debug_composer.png')
                
                # Convert BGRA to RGB if necessary
                if img.shape[2] == 4:
                    img = img[:, :, :3]  # Remove alpha channel
                    logging.info("Converted BGRA to RGB")
                
                logging.info(f"Screenshot shape: {img.shape}")
                
                # Analyze more of the window, not just the bottom
                search_height = min(400, img.shape[0])  # Look at bottom 400px or whole window
                bottom_section = img[-search_height:, :, :]
                
                logging.info(f"Analyzing bottom section of window: shape={bottom_section.shape}")
                
                # Sample multiple points to understand the color range
                sample_points = [
                    (bottom_section.shape[0] // 2, bottom_section.shape[1] // 2),  # Center
                    (bottom_section.shape[0] - 20, bottom_section.shape[1] // 2),  # Near bottom
                    (bottom_section.shape[0] - 20, 20),  # Bottom left
                    (bottom_section.shape[0] - 20, bottom_section.shape[1] - 20)  # Bottom right
                ]
                
                for y, x in sample_points:
                    color = bottom_section[y, x]
                    logging.info(f"Sample color at ({x}, {y}): RGB={color}")
                
                # Look for dark gray areas (composer background)
                dark_matches = np.where(
                    (bottom_section[:, :, 0] >= 20) & (bottom_section[:, :, 0] <= 70) &  # Wider range for R
                    (bottom_section[:, :, 1] >= 20) & (bottom_section[:, :, 1] <= 70) &  # Wider range for G
                    (bottom_section[:, :, 2] >= 20) & (bottom_section[:, :, 2] <= 70)    # Wider range for B
                )
                
                logging.info(f"Found {len(dark_matches[0])} dark colored pixels")
                
                if len(dark_matches[0]) > 0:
                    # Find the largest contiguous region
                    y_coords = dark_matches[0]
                    x_coords = dark_matches[1]
                    
                    # Group nearby points
                    regions = []
                    current_region = []
                    
                    for y, x in zip(y_coords, x_coords):
                        if not current_region:
                            current_region = [(x, y)]
                        elif abs(x - current_region[-1][0]) < 50 and abs(y - current_region[-1][1]) < 50:
                            current_region.append((x, y))
                        else:
                            if len(current_region) > 100:  # Minimum region size
                                regions.append(current_region)
                            current_region = [(x, y)]
                    
                    if current_region and len(current_region) > 100:
                        regions.append(current_region)
                    
                    if regions:
                        # Use the largest region
                        largest_region = max(regions, key=len)
                        x_coords, y_coords = zip(*largest_region)
                        
                        # Calculate region bounds
                        x_min = min(x_coords)
                        x_max = max(x_coords)
                        y_min = self.window_region['height'] - search_height + min(y_coords)
                        y_max = self.window_region['height'] - search_height + max(y_coords)
                        
                        self.composer_region = {
                            'top': y_min + self.window_region['top'],
                            'left': x_min + self.window_region['left'],
                            'width': x_max - x_min,
                            'height': y_max - y_min
                        }
                        
                        logging.info(f"Found composer area using dark region: {self.composer_region}")
                        return True
                
                # If we haven't found the composer area, try looking for a light text area
                light_matches = np.where(
                    (bottom_section[:, :, 0] >= 180) & (bottom_section[:, :, 0] <= 220) &  # Light gray
                    (bottom_section[:, :, 1] >= 180) & (bottom_section[:, :, 1] <= 220) &
                    (bottom_section[:, :, 2] >= 180) & (bottom_section[:, :, 2] <= 220)
                )
                
                logging.info(f"Found {len(light_matches[0])} light colored pixels")
                
                if len(light_matches[0]) > 0:
                    # Use the bottom area where light text was found
                    y_min = self.window_region['height'] - 100  # Bottom 100 pixels
                    y_max = self.window_region['height']
                    x_min = 0
                    x_max = self.window_region['width']
                    
                    self.composer_region = {
                        'top': y_min + self.window_region['top'],
                        'left': x_min + self.window_region['left'],
                        'width': x_max - x_min,
                        'height': y_max - y_min
                    }
                    
                    logging.info(f"Found composer area using light text: {self.composer_region}")
                    return True
                
                # If all else fails, use the bottom portion of the window
                y_min = self.window_region['height'] - 100  # Bottom 100 pixels
                y_max = self.window_region['height']
                x_min = 0
                x_max = self.window_region['width']
                
                self.composer_region = {
                    'top': y_min + self.window_region['top'],
                    'left': x_min + self.window_region['left'],
                    'width': x_max - x_min,
                    'height': y_max - y_min
                }
                
                logging.info(f"Using default bottom area as composer region: {self.composer_region}")
                return True
                
        except Exception as e:
            logging.error(f"Error finding composer area: {str(e)}")
            logging.error(traceback.format_exc())
            return False
        
    def watch_for_messages(self):
        """Monitor for new messages and button locations"""
        if not self.composer_region:
            if not self.find_composer_area():
                return
        
        print("\n=== Watching Cursor Chat ===")
        print("Looking for messages and buttons")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check for accept button
                if self.button_finder.click_button('accept'):
                    logging.info("Clicked accept button")
                    time.sleep(1)  # Wait a bit before looking for more buttons
                
                time.sleep(0.5)  # Reduce CPU usage
                
        except KeyboardInterrupt:
            logging.info("Stopping button watcher")
            
if __name__ == "__main__":
    watcher = CursorWatcher()
    watcher.watch_for_messages() 