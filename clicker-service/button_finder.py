#!/usr/bin/env python3
import pyautogui
import time
import json
import os
import mss
import numpy as np
import logging
from mss import tools
import traceback
import sys
import shutil
from datetime import datetime, timedelta
import signal
from functools import wraps

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(process)d] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('button_finder.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def with_timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set the signal handler and a timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm
                signal.alarm(0)
            return result
        return wrapper
    return decorator

class ButtonFinder:
    def __init__(self):
        self.composer_region = None
        self.sct = mss.mss()
        self.start_time = time.time()
        self.process_timeout = 300  # 5 minutes
        
        # Create debug directory if it doesn't exist
        self.debug_dir = 'debug_images'
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Clean up old debug files
        self.cleanup_old_debug_files()
        
        # Log process start
        logging.info(f"ButtonFinder initialized - Process ID: {os.getpid()}")
        
        # Schedule periodic status updates
        self.last_status_update = time.time()
        self.status_update_interval = 30  # seconds
        
        # Define color ranges for buttons, including gradient pixels
        self.button_colors = {
            'cancel': {
                'solid': {
                    'r': (240, 255),
                    'g': (240, 255),
                    'b': (235, 245)
                },
                'gradient': {
                    'r': (135, 150),
                    'g': (135, 150),
                    'b': (135, 150)
                }
            }
        }

    def check_process_timeout(self):
        """Check if overall process has exceeded timeout"""
        if time.time() - self.start_time > self.process_timeout:
            logging.error("Process timeout exceeded")
            self.cleanup_and_exit(1)

    def update_status(self):
        """Provide periodic status updates"""
        current_time = time.time()
        if current_time - self.last_status_update >= self.status_update_interval:
            elapsed = current_time - self.start_time
            logging.info(f"Status update - Running for {elapsed:.1f}s - Process ID: {os.getpid()}")
            self.last_status_update = current_time

    def cleanup_and_exit(self, status_code):
        """Clean up resources and exit with status code"""
        try:
            self.sct.close()
            logging.info(f"Cleaning up and exiting with status {status_code}")
            sys.exit(status_code)
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            sys.exit(1)

    @with_timeout(5)  # 5 second timeout for button detection
    def click_button(self, button_type):
        """Find and move cursor to a button of the specified type"""
        try:
            self.check_process_timeout()
            self.update_status()
            
            if not self.composer_region:
                logging.error("Composer region not set")
                return False
            
            # Take screenshot of composer region
            screenshot = self.sct.grab(self.composer_region)
            debug_path = self.save_debug_image(screenshot, f'button_region')
            
            # Log detailed region information
            logging.info(f"Searching region: {self.composer_region}")
            logging.info(f"Screenshot dimensions: {screenshot.width}x{screenshot.height}")
            
            # Convert to numpy array
            img = np.array(screenshot)
            if img.shape[2] == 4:
                img = img[:, :, :3]
                logging.info("Converted BGRA to RGB")
                
            height, width = img.shape[:2]
            logging.info(f"Button region dimensions: {width}x{height}")
            
            # Find text area boundary
            boundary_y = self.find_text_area_boundary(img)
            if boundary_y is None:
                logging.info("No text area boundary found")
                return False
                
            logging.info(f"Found text area boundary at y={boundary_y}")
            
            # Only search below the boundary
            search_region = img[boundary_y:, :, :]
            logging.info(f"Searching region below y={boundary_y} ({search_region.shape[0]} pixels high)")
            
            # Find text clusters
            text_clusters = self.find_text_clusters(search_region)
            
            if not text_clusters:
                logging.info("No text clusters found")
                return False
                
            logging.info(f"Found {len(text_clusters)} potential text clusters")
            
            # Sort clusters by y position (prefer buttons near the bottom)
            text_clusters.sort(key=lambda c: c['y'], reverse=True)
            
            # For now, move to the first cluster found (we'll add OCR later)
            cluster = text_clusters[0]
            
            # Calculate center of the cluster
            center_x = cluster['x'] + cluster['width'] // 2
            center_y = boundary_y + cluster['y'] + cluster['height'] // 2
            
            # Move cursor to the center point
            abs_x = self.composer_region['left'] + center_x
            abs_y = self.composer_region['top'] + center_y
            
            logging.info(f"\nMoving cursor to text cluster at absolute coordinates ({abs_x}, {abs_y})")
            logging.info(f"Cluster stats: light_ratio={cluster['light_ratio']:.2f}, dark_ratio={cluster['dark_ratio']:.2f}")
            
            pyautogui.moveTo(abs_x, abs_y)
            return True
            
        except TimeoutError:
            logging.error(f"Button detection timed out after 5 seconds")
            self.save_debug_image(screenshot, f'timeout_failure')
            return False
        except Exception as e:
            logging.error(f"Error finding {button_type} button: {str(e)}")
            logging.error(traceback.format_exc())
            self.save_debug_image(screenshot, f'error_state')
            return False 

    def cleanup_old_debug_files(self, max_age_hours=24):
        """Remove debug files older than specified hours"""
        try:
            now = datetime.now()
            for filename in os.listdir(self.debug_dir):
                if filename.startswith('debug_'):
                    filepath = os.path.join(self.debug_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if now - file_time > timedelta(hours=max_age_hours):
                        os.remove(filepath)
                        logging.info(f"Removed old debug file: {filename}")
        except Exception as e:
            logging.warning(f"Error cleaning up debug files: {str(e)}")
        
    def save_debug_image(self, img_data, name_suffix):
        """Save a debug image with timestamp"""
        try:
            timestamp = time.strftime("%H%M%S")
            filename = f'debug_{name_suffix}_{timestamp}.png'
            filepath = os.path.join(self.debug_dir, filename)
            mss.tools.to_png(img_data.rgb, img_data.size, output=filepath)
            logging.info(f"Saved debug image: {filename}")
            return filepath
        except Exception as e:
            logging.warning(f"Error saving debug image: {str(e)}")
            return None
        
    def set_composer_region(self, region):
        """Set the composer region to search within"""
        self.composer_region = region
        
    def is_color_in_range(self, pixel, ranges):
        """Check if a pixel's color falls within any of the specified ranges"""
        r, g, b = pixel
        
        # Check solid color range with wider tolerance for anti-aliasing
        solid_match = (ranges['solid']['r'][0] <= r <= ranges['solid']['r'][1] and
                      ranges['solid']['g'][0] <= g <= ranges['solid']['g'][1] and
                      ranges['solid']['b'][0] <= b <= ranges['solid']['b'][1])
                      
        # Check gradient color range
        gradient_match = (ranges['gradient']['r'][0] <= r <= ranges['gradient']['r'][1] and
                         ranges['gradient']['g'][0] <= g <= ranges['gradient']['g'][1] and
                         ranges['gradient']['b'][0] <= b <= ranges['gradient']['b'][1])
                         
        return solid_match or gradient_match

    def find_text_area_boundary(self, img):
        """Find the boundary between text area and button area by looking for color transitions"""
        if img.shape[2] == 4:  # Convert BGRA to RGB if needed
            img = img[:, :, :3]
        
        height = img.shape[0]
        width = img.shape[1]
        
        # Look for the border color (383d54) and background transition
        border_color = np.array([56, 61, 84])  # 383d54 in RGB
        text_bg = np.array([33, 34, 45])       # 21222d in RGB
        button_bg = np.array([40, 43, 54])     # 282b36 in RGB
        
        tolerance = 40  # Increased color matching tolerance
        min_boundary_height = 50  # Minimum pixels from bottom
        
        # Start from 2/3 of the way down
        start_y = height * 2 // 3
        
        # Scan from middle to bottom
        for y in range(start_y, height - min_boundary_height, -1):
            # Sample multiple x positions to avoid being fooled by text
            x_samples = np.linspace(0, width-1, 100, dtype=int)  # More samples
            colors = img[y, x_samples]
            
            # Count matches for each color with higher tolerance
            border_matches = np.sum(np.all(np.abs(colors - border_color) < tolerance, axis=1))
            text_bg_matches = np.sum(np.all(np.abs(colors - text_bg) < tolerance, axis=1))
            button_bg_matches = np.sum(np.all(np.abs(colors - button_bg) < tolerance, axis=1))
            
            # Calculate match percentages
            total_samples = len(x_samples)
            border_percent = border_matches / total_samples
            bg_percent = (text_bg_matches + button_bg_matches) / total_samples
            
            # Log color samples periodically
            if y % 20 == 0:
                sample_colors = colors[::10]  # Log every 10th color
                logging.debug(f"y={y} colors: {sample_colors}")
            
            # More lenient matching
            if border_percent > 0.05 or bg_percent > 0.2:
                logging.info(f"Found boundary at y={y} (border={border_percent:.2f}, bg={bg_percent:.2f})")
                return y
        
        # If no clear boundary found, return 2/3 down
        default_y = start_y
        logging.info(f"No clear boundary found, using default y={default_y}")
        return default_y

    def analyze_text_region(self, region, x, y, width=50, height=20):
        """Analyze a region for text-like patterns of light and dark pixels"""
        if x + width > region.shape[1] or y + height > region.shape[0]:
            return 0, 0  # Out of bounds
        
        # Extract the region
        text_region = region[y:y+height, x:x+width]
        
        # Convert to grayscale for simpler analysis
        gray = np.mean(text_region, axis=2)
        
        # Count light and dark pixels with more lenient thresholds
        light_pixels = np.sum(gray > 160)  # More lenient threshold for light pixels
        dark_pixels = np.sum(gray < 80)    # More lenient threshold for dark pixels
        
        # Calculate ratios
        total_pixels = width * height
        light_ratio = light_pixels / total_pixels
        dark_ratio = dark_pixels / total_pixels
        
        # Log color information for debugging
        if light_ratio > 0.05:  # Log any region with significant light pixels
            avg_color = np.mean(text_region, axis=(0,1))
            logging.debug(f"Region ({x},{y}) - Avg RGB: {avg_color}, Light: {light_ratio:.2f}, Dark: {dark_ratio:.2f}")
        
        return light_ratio, dark_ratio

    def find_text_clusters(self, img):
        """Find clusters of pixels that match text patterns"""
        height, width = img.shape[:2]
        
        # Parameters for text detection - more lenient
        word_width = 60    # Width for "Cancel" text
        word_height = 30   # Height for typical button text
        step_x = 10       # Smaller steps for more precise scanning
        step_y = 5
        
        # Expected ratios for text regions - more lenient
        expected_light_ratio = 0.08   # About 8% light pixels for text
        expected_dark_ratio = 0.5     # About 50% dark pixels for background
        tolerance = 0.25             # More lenient tolerance
        
        text_clusters = []
        
        logging.info(f"Scanning for text clusters (window: {word_width}x{word_height}, step: {step_x}x{step_y})")
        logging.info(f"Target ratios: light={expected_light_ratio:.2f}±{tolerance}, dark={expected_dark_ratio:.2f}±{tolerance}")
        
        # Sample colors from the image for debugging
        sample_points = [(0,0), (width//4,height//2), (width//2,height//2), (3*width//4,height//2), (width-1,height-1)]
        for px, py in sample_points:
            if 0 <= px < width and 0 <= py < height:
                color = img[py,px]
                logging.info(f"Sample color at ({px},{py}): RGB={color}")
        
        # Scan the entire region
        for y in range(0, height - word_height, step_y):
            for x in range(0, width - word_width, step_x):
                light_ratio, dark_ratio = self.analyze_text_region(img, x, y, word_width, word_height)
                
                # Log more frequently for debugging
                if y % 20 == 0 and x % 40 == 0:
                    logging.debug(f"Sample at ({x}, {y}): light={light_ratio:.2f}, dark={dark_ratio:.2f}")
                
                # Check if ratios match expected text patterns
                if (abs(light_ratio - expected_light_ratio) < tolerance and 
                    abs(dark_ratio - expected_dark_ratio) < tolerance):
                    
                    score = 1 - (abs(light_ratio - expected_light_ratio) + 
                                abs(dark_ratio - expected_dark_ratio)) / 2
                    
                    # More lenient score threshold
                    if score > 0.5:  # Even more lenient threshold
                        text_clusters.append({
                            'x': x,
                            'y': y,
                            'width': word_width,
                            'height': word_height,
                            'light_ratio': light_ratio,
                            'dark_ratio': dark_ratio,
                            'score': score
                        })
                        logging.info(f"Found potential text at ({x}, {y}): light={light_ratio:.2f}, dark={dark_ratio:.2f}, score={score:.2f}")
        
        # Sort clusters by score
        text_clusters.sort(key=lambda c: c['score'], reverse=True)
        
        if text_clusters:
            logging.info(f"\nTop 3 clusters by score:")
            for i, cluster in enumerate(text_clusters[:3]):
                logging.info(f"{i+1}. ({cluster['x']}, {cluster['y']}): score={cluster['score']:.3f}, light={cluster['light_ratio']:.2f}")
        
        return text_clusters

    def is_color_match(self, pixel, target_color, tolerance=5):
        """Check if a pixel matches a target color within tolerance"""
        return all(abs(p - t) <= tolerance for p, t in zip(pixel, target_color))

    def find_button(self, screenshot, button_type='cancel'):
        """Find a button in the screenshot"""
        height, width = screenshot.shape[:2]
        
        # Target colors from analysis
        CANCEL_TEXT = (247, 247, 240)  # #f7f7f0 - white text
        ACCEPT_BG = (49, 54, 73)      # #313649 - border color
        
        # Track potential button locations
        button_pixels = []
        
        # Scan for button text
        for y in range(height):
            current_run = 0
            run_start = None
            
            for x in range(width):
                pixel = screenshot[y, x]
                
                if button_type == 'cancel' and self.is_color_match(pixel, CANCEL_TEXT):
                    if current_run == 0:
                        run_start = x
                    current_run += 1
                elif button_type == 'accept' and self.is_color_match(pixel, ACCEPT_BG):
                    if current_run == 0:
                        run_start = x
                    current_run += 1
                else:
                    if current_run >= 3:  # Minimum run length for button text
                        button_pixels.append((run_start + current_run//2, y))
                    current_run = 0
                    run_start = None
            
            # Check end of line
            if current_run >= 3:
                button_pixels.append((run_start + current_run//2, y))
        
        # Group nearby pixels into potential buttons
        buttons = []
        for x, y in button_pixels:
            # Check if this pixel belongs to an existing button
            found_group = False
            for button in buttons:
                center_x, center_y, count = button
                if abs(x - center_x) < 20 and abs(y - center_y) < 10:
                    # Update button center
                    new_count = count + 1
                    new_x = (center_x * count + x) / new_count
                    new_y = (center_y * count + y) / new_count
                    button[0] = new_x
                    button[1] = new_y
                    button[2] = new_count
                    found_group = True
                    break
            
            if not found_group:
                buttons.append([x, y, 1])
        
        # Find button with most matching pixels
        if buttons:
            best_button = max(buttons, key=lambda b: b[2])
            if best_button[2] >= 5:  # Minimum number of matching pixels
                return (int(best_button[0]), int(best_button[1]))
        
        return None 

def main():
    """Main function to initialize and run button finder"""
    try:
        finder = ButtonFinder()
        
        # Get screen size for better positioning
        screen_width, screen_height = pyautogui.size()
        logging.info(f"Screen dimensions: {screen_width}x{screen_height}")
        
        # Account for potential display scaling (2x on Retina displays)
        scale_factor = 1  # Changed to 1 since mss handles scaling
        logging.info(f"Using scale factor: {scale_factor}x")
        
        # Calculate safe region that stays within screen bounds
        region_width = min(400, screen_width // 2)
        region_height = min(200, screen_height // 4)
        
        # Position region in bottom center of screen, ensuring it stays within bounds
        composer_region = {
            'left': max(0, min((screen_width - region_width) // 2, screen_width - region_width)),
            'top': max(0, min(screen_height - region_height - 200, screen_height - region_height)),
            'width': region_width,
            'height': region_height
        }
        
        logging.info(f"Initial composer region: {composer_region}")
        finder.set_composer_region(composer_region)
        logging.info("Starting button detection...")
        
        # Try multiple attempts with different positions
        max_attempts = 5
        for attempt in range(max_attempts):
            logging.info(f"\nAttempt {attempt + 1}/{max_attempts}")
            
            # Take a debug screenshot of full screen
            with mss.mss() as sct:
                # Get the primary monitor
                monitor = sct.monitors[1]
                logging.info(f"Monitor bounds: {monitor}")
                
                # Ensure region stays within monitor bounds
                composer_region['left'] = max(0, min(composer_region['left'], monitor['width'] - composer_region['width']))
                composer_region['top'] = max(0, min(composer_region['top'], monitor['height'] - composer_region['height']))
                
                full_screen = sct.grab(monitor)
                debug_path = finder.save_debug_image(full_screen, f'full_screen_{attempt}')
                logging.info(f"Saved full screen debug image: {debug_path}")
            
            finder.set_composer_region(composer_region)
            success = finder.click_button('cancel')
            
            if success:
                logging.info("Successfully found and moved to cancel button")
                return 0
            
            # Adjust region for next attempt - try different areas
            if attempt == 0:
                composer_region['top'] = max(0, composer_region['top'] - 100)
            elif attempt == 1:
                composer_region['top'] = min(monitor['height'] - region_height, composer_region['top'] + 200)
            elif attempt == 2:
                composer_region['left'] = max(0, composer_region['left'] - 100)
            elif attempt == 3:
                composer_region['left'] = min(monitor['width'] - region_width, composer_region['left'] + 200)
            
            logging.info(f"Adjusted composer region: {composer_region}")
            time.sleep(1)  # Brief pause between attempts
        
        logging.error("Failed to find cancel button after all attempts")
        return 1
            
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        logging.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 