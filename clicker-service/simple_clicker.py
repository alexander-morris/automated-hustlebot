#!/usr/bin/env python3
import pyautogui
import time
import logging
import os
from PIL import Image, ImageGrab
import random
from collections import Counter
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('clicker.log'),
        logging.StreamHandler()
    ]
)

class SimpleClicker:
    def __init__(self):
        """Initialize the clicker with default values."""
        self.cursor_bg_color = (32, 33, 36)  # RGB values for Cursor background
        self.cursor_bg_hex = '#202124'  # Hex value for Cursor background
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Set up safe zones
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        self.running = True
        
        # Accept button color range (blue)
        self.button_color_range = {
            'r': (40, 70),    # Red range
            'g': (120, 150),  # Green range
            'b': (240, 255)   # Blue range
        }
        
        # Maximum runtime in seconds
        self.max_runtime = 30
        
        # Get information about all monitors
        self.monitors = self.get_monitor_info()
        logging.info(f"Detected {len(self.monitors)} monitors: {self.monitors}")
        
        # Calculate expected points to check
        total_points = sum(
            ((m['width'] // 10) * (m['height'] // 10))
            for m in self.monitors
        )
        logging.info(f"Will check approximately {total_points} points across all monitors")

    def get_monitor_info(self):
        """Get information about all connected monitors"""
        try:
            from AppKit import NSScreen
            monitors = []
            
            for screen in NSScreen.screens():
                frame = screen.frame()
                monitors.append({
                    'left': int(frame.origin.x),
                    'top': int(frame.origin.y),
                    'width': int(frame.size.width),
                    'height': int(frame.size.height)
                })
                logging.info(f"Found monitor: {monitors[-1]}")
                
            if not monitors:
                # Fallback to single monitor
                size = pyautogui.size()
                monitors = [{'left': 0, 'top': 0, 'width': size[0], 'height': size[1]}]
                logging.info("Falling back to single monitor mode")
                
            return monitors
        except Exception as e:
            logging.error(f"Error getting monitor info: {e}")
            # Fallback to single monitor
            size = pyautogui.size()
            return [{'left': 0, 'top': 0, 'width': size[0], 'height': size[1]}]

    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color code"""
        if len(rgb) >= 3:
            return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
        return '#000000'

    def analyze_color_distribution(self, screen, monitor):
        """Analyze the color distribution in a region of the screen"""
        colors = Counter()
        sample_count = 0
        
        # Sample a grid of points
        for x in range(monitor['left'], monitor['left'] + monitor['width'], 50):
            for y in range(monitor['top'], monitor['top'] + monitor['height'], 50):
                try:
                    pixel = screen.getpixel((x, y))
                    hex_color = self.rgb_to_hex(pixel)
                    colors[hex_color] += 1
                    sample_count += 1
                except Exception as e:
                    logging.debug(f"Error sampling pixel at ({x}, {y}): {e}")
        
        # Log the most common colors
        logging.info(f"Color distribution for monitor (sampled {sample_count} points):")
        for color, count in colors.most_common(10):
            percentage = (count / sample_count) * 100
            logging.info(f"  {color}: {count} pixels ({percentage:.1f}%)")
        
        return colors

    def find_cursor_window(self):
        """Find the Cursor window by looking for its distinctive background color"""
        logging.info(f"Attempting to find Cursor window (looking for background color {self.cursor_bg_hex})...")
        try:
            # Use ImageGrab instead of pyautogui.screenshot()
            screen = ImageGrab.grab()
            logging.info(f"Captured screenshot: {screen.size}")
            
            # Save a debug screenshot
            debug_filename = 'debug_screenshot.png'
            screen.save(debug_filename)
            logging.info(f"Saved debug screenshot to {debug_filename}")
            
            for monitor_idx, monitor in enumerate(self.monitors):
                logging.info(f"Scanning monitor {monitor_idx + 1}: {monitor}")
                
                # Analyze color distribution for this monitor
                color_dist = self.analyze_color_distribution(screen, monitor)
                
                # Calculate sampling points for this monitor
                sample_points = self.generate_sample_points(monitor)
                logging.info(f"Generated {len(sample_points)} sample points for monitor {monitor_idx + 1}")
                
                potential_regions = []
                samples_checked = 0
                
                for x, y in sample_points:
                    samples_checked += 1
                    if samples_checked % 100 == 0:
                        logging.debug(f"Checked {samples_checked}/{len(sample_points)} points on monitor {monitor_idx + 1}")
                    
                    try:
                        pixel = screen.getpixel((x, y))
                        hex_color = self.rgb_to_hex(pixel)
                        
                        # Log every 50th sample with more detail
                        if samples_checked % 50 == 0:
                            logging.debug(f"Sampling at ({x}, {y}): RGB{pixel[:3]} / {hex_color}")
                            # Also check surrounding pixels
                            surrounding = []
                            for dx, dy in [(-5,0), (5,0), (0,-5), (0,5)]:
                                try:
                                    px = screen.getpixel((x+dx, y+dy))
                                    surrounding.append(self.rgb_to_hex(px))
                                except:
                                    pass
                            logging.debug(f"Surrounding colors: {surrounding}")
                        
                        # Check if pixel matches Cursor background color (with some tolerance)
                        if self.is_cursor_bg_color(pixel):
                            logging.info(f"Found matching background color at ({x}, {y}): RGB{pixel[:3]} / {hex_color}")
                            # Found a potential region, verify it's large enough
                            region = self.verify_cursor_region(screen, x, y)
                            if region:
                                logging.info(f"Found potential Cursor window region: {region}")
                                potential_regions.append(region)
                    except Exception as e:
                        logging.debug(f"Error checking pixel at ({x}, {y}): {e}")
                        continue
                
                if potential_regions:
                    # Use the largest region found (most likely to be the main window)
                    self.cursor_region = max(potential_regions, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
                    x1, y1, x2, y2 = self.cursor_region
                    logging.info(f"Selected Cursor window region on monitor {monitor_idx + 1}: ({x1}, {y1}) to ({x2}, {y2}), size: {x2-x1}x{y2-y1}")
                    return True
                
                logging.warning(f"No Cursor window found on monitor {monitor_idx + 1} after checking {samples_checked} points")
            
            return False
            
        except Exception as e:
            logging.error(f"Error finding Cursor window: {str(e)}")
            return False

    def generate_sample_points(self, monitor):
        """Generate a list of points to sample on the monitor"""
        points = []
        width = monitor['width']
        height = monitor['height']
        
        # Calculate grid size based on screen dimensions
        step_x = max(10, width // 100)  # At most 100 points horizontally
        step_y = max(10, height // 100)  # At most 100 points vertically
        
        logging.info(f"Sampling every {step_x}x{step_y} pixels")
        
        # Sample in a grid pattern
        for x in range(0, width, step_x):
            for y in range(0, height, step_y):
                # Convert to screen coordinates
                screen_x = monitor['left'] + x
                screen_y = monitor['top'] + y
                
                # Add some random offset to avoid grid-like sampling
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                final_x = screen_x + offset_x
                final_y = screen_y + offset_y
                
                # Validate coordinates are within screen bounds
                if (0 <= final_x < monitor['left'] + width and 
                    0 <= final_y < monitor['top'] + height):
                    points.append((final_x, final_y))
        
        # Shuffle points to distribute sampling across the screen
        random.shuffle(points)
        return points

    def validate_coordinates(self, x, y, monitor):
        """Validate that coordinates are within reasonable bounds"""
        if x < 0 or y < 0:
            logging.error(f"Invalid negative coordinates: ({x}, {y})")
            return False
        
        if x > 5000 or y > 5000:  # Reasonable maximum screen dimensions
            logging.error(f"Coordinates exceed reasonable bounds: ({x}, {y})")
            return False
            
        if not (monitor['left'] <= x < monitor['left'] + monitor['width'] and
                monitor['top'] <= y < monitor['top'] + monitor['height']):
            logging.error(f"Coordinates ({x}, {y}) outside monitor bounds: {monitor}")
            return False
            
        return True

    def is_cursor_bg_color(self, pixel):
        """Check if a pixel matches the Cursor background color."""
        # Handle RGBA pixels by taking only RGB values
        r, g, b = pixel[:3]  # Take first 3 values for RGB
        target_r, target_g, target_b = self.cursor_bg_color
        
        # Check if RGB values match within tolerance
        matches = (
            abs(r - target_r) <= self.color_tolerance and
            abs(g - target_g) <= self.color_tolerance and
            abs(b - target_b) <= self.color_tolerance
        )
        
        if matches:
            self.logger.debug(f"Color match: RGB({r},{g},{b}) matches target RGB({target_r}, {target_g}, {target_b}) within tolerance {self.color_tolerance}")
        
        return matches

    def verify_cursor_region(self, screen, start_x, start_y):
        """Verify and measure a potential Cursor window region"""
        try:
            width, height = screen.size
            
            # Find right edge
            right_x = start_x
            while right_x < width and self.is_cursor_bg_color(screen.getpixel((right_x, start_y))):
                right_x += 20
            
            # Find bottom edge
            bottom_y = start_y
            while bottom_y < height and self.is_cursor_bg_color(screen.getpixel((start_x, bottom_y))):
                bottom_y += 20
            
            region_width = right_x - start_x
            region_height = bottom_y - start_y
            
            # Verify minimum size (100x100 pixels)
            if region_width > 100 and region_height > 100:
                logging.info(f"Verified region at ({start_x}, {start_y}): {region_width}x{region_height} pixels")
                return (start_x, start_y, right_x, bottom_y)
            
            logging.debug(f"Region at ({start_x}, {start_y}) too small: {region_width}x{region_height} pixels")
            return None
            
        except Exception as e:
            logging.error(f"Error verifying region: {str(e)}")
            return None

    def is_accept_button_color(self, pixel):
        """Check if a pixel matches the Accept button color ranges"""
        r, g, b = pixel
        matches = (self.button_color_range['r'][0] <= r <= self.button_color_range['r'][1] and
                  self.button_color_range['g'][0] <= g <= self.button_color_range['g'][1] and
                  self.button_color_range['b'][0] <= b <= self.button_color_range['b'][1])
        if matches:
            logging.debug(f"Found button color: RGB{pixel} / {self.rgb_to_hex(pixel)}")
        return matches

    def watch_and_click(self):
        logging.info("Starting Simple Clicker")
        print("First, trying to locate Cursor window...")
        
        start_time = time.time()
        error_count = 0
        max_errors = 10  # Stop after 10 errors
        
        try:
            while self.running:
                # Check timeout
                if time.time() - start_time > self.max_runtime:
                    logging.warning(f"Exceeded maximum runtime of {self.max_runtime} seconds")
                    return False
                
                if error_count >= max_errors:
                    logging.error(f"Stopped after encountering {error_count} errors")
                    return False
                
                if not hasattr(self, 'cursor_region'):
                    if not self.find_cursor_window():
                        error_count += 1
                        logging.warning("Could not find Cursor window, retrying...")
                        time.sleep(1)
                        continue
                
                # Take a screenshot of just the Cursor window region
                screen = pyautogui.screenshot(region=self.cursor_region)
                region_x, region_y, region_right, region_bottom = self.cursor_region
                width = region_right - region_x
                height = region_bottom - region_y
                
                logging.debug(f"Scanning Cursor window region {width}x{height} at ({region_x}, {region_y})")
                
                # Look for the Accept button
                for x in range(0, width, 5):  # Smaller steps for more precision
                    for y in range(0, height, 5):
                        pixel = screen.getpixel((x, y))
                        if self.is_accept_button_color(pixel):
                            hex_color = self.rgb_to_hex(pixel)
                            logging.info(f"Found potential button pixel at ({region_x + x}, {region_y + y}): RGB{pixel} / {hex_color}")
                            if self.verify_button_area(screen, x, y):
                                # Convert coordinates relative to screen
                                screen_x = region_x + x
                                screen_y = region_y + y
                                logging.info(f"Verified button at ({screen_x}, {screen_y})")
                                
                                # Save current mouse position
                                current_x, current_y = pyautogui.position()
                                
                                # Click the button
                                pyautogui.click(screen_x, screen_y)
                                logging.info(f"Clicked at ({screen_x}, {screen_y})")
                                
                                # Restore mouse position
                                pyautogui.moveTo(current_x, current_y)
                                time.sleep(1)
                                return
                
                time.sleep(0.1)  # Short sleep between scans
                
        except KeyboardInterrupt:
            logging.info("Stopping clicker")
            self.running = False
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return False

    def verify_button_area(self, screen, x, y):
        """Verify this is actually a button by checking surrounding pixels"""
        try:
            for dx in [-5, 0, 5]:
                for dy in [-2, 0, 2]:
                    check_x = x + dx
                    check_y = y + dy
                    if 0 <= check_x < screen.width and 0 <= check_y < screen.height:
                        pixel = screen.getpixel((check_x, check_y))
                        hex_color = self.rgb_to_hex(pixel)
                        logging.debug(f"Checking button area at ({check_x}, {check_y}): RGB{pixel} / {hex_color}")
                        if not self.is_accept_button_color(pixel):
                            return False
            return True
        except Exception as e:
            logging.error(f"Error verifying button area: {e}")
            return False

if __name__ == "__main__":
    clicker = SimpleClicker()
    success = clicker.watch_and_click()
    if not success:
        sys.exit(1)  # Exit with error code if unsuccessful 