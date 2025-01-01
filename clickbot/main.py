import cv2
import numpy as np
from PIL import Image
import os
import logging
import pyautogui
import time
from datetime import datetime
import mss
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def find_cursor_monitor():
    """Find the monitor containing the Cursor application."""
    logging.info("Searching for monitor with Cursor application...")
    
    # Load reference image
    ref_path = os.path.join("images", "cursor-screen-head.png")
    reference_img = cv2.imread(ref_path)
    if reference_img is None:
        logging.error(f"Reference image not found at {ref_path}")
        return None
        
    with mss.mss() as sct:
        # Check each monitor
        for i, monitor in enumerate(sct.monitors[1:], 1):
            logging.info(f"Checking monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
            
            # Capture top portion of monitor
            area = {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": 50  # Only check top 50 pixels
            }
            
            try:
                # Capture and convert to numpy array
                screenshot = sct.grab(area)
                screen_img = np.array(screenshot)
                screen_img = screen_img[:, :, :3]  # Remove alpha channel
                
                # Template matching
                result = cv2.matchTemplate(screen_img, reference_img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                logging.info(f"Monitor {i} match confidence: {max_val:.3f}")
                
                if max_val > 0.8:  # High confidence threshold
                    logging.info(f"Found Cursor application on monitor {i}")
                    return monitor
                    
            except Exception as e:
                logging.warning(f"Error checking monitor {i}: {str(e)}")
                continue
    
    logging.warning("Could not find Cursor application, falling back to primary monitor")
    return sct.monitors[1]

class ClickBot:
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Load target image
        target_path = os.path.join("images", "target.png")
        target = Image.open(target_path)
        target = target.convert('RGB')
        target_np = np.array(target)
        self.target_bgr = cv2.cvtColor(target_np, cv2.COLOR_RGB2BGR)
        
        # Find correct monitor
        self.monitor = find_cursor_monitor()
        if not self.monitor:
            raise RuntimeError("Failed to find Cursor monitor")
            
        logging.info(f"Using monitor: {self.monitor['width']}x{self.monitor['height']} at ({self.monitor['left']}, {self.monitor['top']})")
        
        # Create debug output directory
        os.makedirs("debug_output", exist_ok=True)
        
        # Store target dimensions
        self.target_h, self.target_w = self.target_bgr.shape[:2]
        
    def check_for_target(self):
        """Check for target in the current screen."""
        with mss.mss() as sct:
            # Capture screen
            screenshot = sct.grab(self.monitor)
            screen_np = np.array(screenshot)
            screen_bgr = screen_np[:, :, :3]  # Remove alpha channel
            
            # Perform template matching
            result = cv2.matchTemplate(screen_bgr, self.target_bgr, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= 0.8:  # High confidence match
                x, y = max_loc
                click_x = self.monitor['left'] + x + self.target_w // 2
                click_y = self.monitor['top'] + y + self.target_h // 2
                
                logging.info(f"Found target with {max_val:.2%} confidence at ({click_x}, {click_y})")
                
                if self.dev_mode:
                    response = input("Click target? [y/N] ")
                    if response.lower() != 'y':
                        return
                
                # Save current mouse position
                original_x, original_y = pyautogui.position()
                
                try:
                    # Move to target and click
                    pyautogui.moveTo(click_x, click_y, duration=0.2)
                    time.sleep(0.1)
                    pyautogui.click()
                    time.sleep(0.1)
                    
                    # Return to original position
                    pyautogui.moveTo(original_x, original_y, duration=0.1)
                    logging.info("Click executed successfully")
                    
                except Exception as e:
                    logging.error(f"Error during click operation: {str(e)}")
            
            else:
                logging.debug(f"No high confidence matches found (best: {max_val:.2%})")
    
    def run(self, check_interval=1.0):
        """Run the click bot continuously."""
        logging.info("Starting click bot...")
        last_monitor_check = time.time()
        
        try:
            while True:
                # Check if we need to update monitor selection (every 5 minutes)
                current_time = time.time()
                if current_time - last_monitor_check >= 300:  # 5 minutes
                    self.monitor = find_cursor_monitor()
                    last_monitor_check = current_time
                
                self.check_for_target()
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logging.info("Click bot stopped by user")
        except Exception as e:
            logging.error(f"Click bot error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Cursor Click Bot")
    parser.add_argument("--dev", action="store_true", help="Run in development mode (requires click confirmation)")
    args = parser.parse_args()
    
    try:
        bot = ClickBot(dev_mode=args.dev)
        bot.run()
    except Exception as e:
        logging.error(f"Failed to start click bot: {str(e)}")

if __name__ == "__main__":
    main() 