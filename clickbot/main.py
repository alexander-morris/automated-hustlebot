import os
import time
import logging
import pyautogui
import mss
import mss.tools
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from image_matcher import ImageMatcher
from typing import Tuple
import math
import cv2

class ClickBot:
    def __init__(self, threshold=0.7):
        self.matcher = ImageMatcher(threshold=threshold)
        self.last_click_time = 0
        self.click_cooldown = 2.0  # Seconds between clicks
        self.original_mouse_pos = (0, 0)
        self.move_duration = 0.1  # Fast but not instant movement
        self.debug_dir = os.path.join(os.path.dirname(__file__), "debug_output")
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Initialize screen capture
        self.sct = mss.mss()
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Small delay between actions
        
    def save_debug_image(self, screen_img, matches, timestamp):
        """Save debug image with matches highlighted."""
        # Convert to PIL Image if numpy array
        if isinstance(screen_img, np.ndarray):
            screen_img = cv2.cvtColor(screen_img, cv2.COLOR_BGR2RGB)
            debug_img = Image.fromarray(screen_img)
        else:
            debug_img = screen_img
            
        draw = ImageDraw.Draw(debug_img)
        
        # Draw matches
        for idx, match in enumerate(matches):
            # Draw red dot
            dot_radius = 5
            draw.ellipse(
                [
                    match.center_x - dot_radius,
                    match.center_y - dot_radius,
                    match.center_x + dot_radius,
                    match.center_y + dot_radius
                ],
                fill='red'
            )
            
            # Draw confidence text
            text = f"#{idx+1} Conf: {match.confidence:.2f}"
            draw.text(
                (match.center_x, match.center_y - 20),
                text,
                fill='red',
                stroke_width=2,
                stroke_fill='black'
            )
            
            # Draw SSIM score
            ssim_text = f"SSIM: {match.quality.structural_similarity:.2f}"
            draw.text(
                (match.center_x, match.center_y + 20),
                ssim_text,
                fill='red',
                stroke_width=2,
                stroke_fill='black'
            )
        
        # Save debug image
        filename = f"screen_matches_{timestamp}.png"
        debug_path = os.path.join(self.debug_dir, filename)
        debug_img.save(debug_path)
        logging.info(f"Saved debug image: {filename}")
        
    def capture_screen(self):
        """Capture the entire screen."""
        # Capture all monitors
        for monitor in self.sct.monitors[1:]:  # Skip first monitor (combined view)
            try:
                # Capture monitor
                screenshot = self.sct.grab(monitor)
                
                # Convert to numpy array
                img_array = np.array(screenshot)
                
                # Convert BGRA to RGB
                img_array = img_array[:, :, [2,1,0]]
                
                return img_array
                
            except Exception as e:
                logging.error(f"Error capturing monitor: {str(e)}")
                continue
                
        return None
        
    def save_mouse_position(self):
        """Save current mouse position."""
        self.original_mouse_pos = pyautogui.position()
        
    def restore_mouse_position(self):
        """Restore mouse to original position."""
        pyautogui.moveTo(
            self.original_mouse_pos[0],
            self.original_mouse_pos[1],
            duration=self.move_duration/2  # Faster return movement
        )
        
    def smooth_click(self, x: int, y: int) -> bool:
        """Perform a smooth click operation with position restore."""
        try:
            # Check cooldown
            current_time = time.time()
            if current_time - self.last_click_time < self.click_cooldown:
                return False
                
            # Save current mouse position
            self.save_mouse_position()
            
            # Move to target smoothly
            pyautogui.moveTo(x, y, duration=self.move_duration)
            
            # Click and small pause
            pyautogui.click()
            time.sleep(0.1)
            
            # Restore position
            self.restore_mouse_position()
            
            # Update last click time
            self.last_click_time = current_time
            return True
            
        except Exception as e:
            logging.error(f"Error during click operation: {str(e)}")
            # Try to restore mouse position even if click failed
            try:
                self.restore_mouse_position()
            except:
                pass
            return False

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize bot with 70% threshold
    bot = ClickBot(threshold=0.7)
    
    # Load target image
    target_path = os.path.join(os.path.dirname(__file__), "images", "target.png")
    if not os.path.exists(target_path):
        logging.error(f"Target image not found at {target_path}")
        return
    
    bot.matcher.load_target(target_path)
    logging.info("Target image loaded successfully")
    
    try:
        while True:
            # Capture current screen
            screen = bot.capture_screen()
            if screen is None:
                logging.error("Failed to capture screen")
                time.sleep(1)
                continue
                
            # Find matches
            matches = bot.matcher.find_matches(screen)
            
            # Generate timestamp for debug image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if matches:
                logging.info(f"Found {len(matches)} matches:")
                # Sort matches by confidence
                matches.sort(key=lambda m: m.confidence, reverse=True)
                
                # Save debug image with all matches
                bot.save_debug_image(screen, matches, timestamp)
                
                # Process best match
                best_match = matches[0]
                logging.info(f"Best match:")
                logging.info(f"  Position: ({best_match.center_x}, {best_match.center_y})")
                logging.info(f"  Confidence: {best_match.confidence:.2f}")
                logging.info(f"  SSIM: {best_match.quality.structural_similarity:.2f}")
                
                # Attempt click if confidence is high enough (70%)
                if best_match.confidence > 0.7:
                    if bot.smooth_click(best_match.center_x, best_match.center_y):
                        logging.info("Successfully clicked target")
                    else:
                        logging.info("Click skipped (cooldown)")
            else:
                # Save debug image even with no matches
                bot.save_debug_image(screen, [], timestamp)
            
            # Sleep to prevent excessive CPU usage
            time.sleep(0.5)  # Reduced sleep time for better responsiveness
            
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user")
    except Exception as e:
        logging.error(f"Error during monitoring: {str(e)}")

if __name__ == "__main__":
    main() 