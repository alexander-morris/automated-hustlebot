import os
import time
import pyautogui
from PIL import Image
from logging_config import setup_logging, log_error_with_context, save_debug_image
from image_matcher import ImageMatcher

class ErrorRecoveryHandler:
    def __init__(self, debug=False):
        self.logger = setup_logging('error_recovery', debug)
        self.debug = debug
        self.matcher = ImageMatcher(debug)
        self.error_indicators = ['error-icon.png', 'note-text.png']
        self.recovery_target = 'agent-buttons-footer.png'
        
        # Load reference images
        self.images_dir = os.path.join(os.path.dirname(__file__), 'images')
        self.error_images = self._load_error_images()
        self.recovery_image = self._load_recovery_image()

    def _load_error_images(self):
        """Load error indicator images."""
        images = {}
        for img_name in self.error_indicators:
            path = os.path.join(self.images_dir, img_name)
            if os.path.exists(path):
                images[img_name] = Image.open(path)
            else:
                self.logger.warning(f"Error indicator image not found: {img_name}")
        return images

    def _load_recovery_image(self):
        """Load recovery target image."""
        path = os.path.join(self.images_dir, self.recovery_target)
        if os.path.exists(path):
            return Image.open(path)
        self.logger.warning(f"Recovery target image not found: {self.recovery_target}")
        return None

    def check_for_errors(self, screen):
        """Check if any error indicators are present on screen."""
        try:
            for name, image in self.error_images.items():
                match = self.matcher.find_template(screen, image, threshold=0.8)
                if match:
                    self.logger.info(f"Error indicator detected: {name} with confidence {match['confidence']:.4f}")
                    if self.debug:
                        annotated = screen.copy()
                        self.matcher.draw_match(annotated, match)
                        save_debug_image(annotated, f'error_detected_{name}', 'debug_output')
                    return True, name
            return False, None
        except Exception as e:
            log_error_with_context(self.logger, e, "Error checking for error indicators")
            return False, None

    def perform_recovery(self, screen):
        """Execute the error recovery sequence."""
        try:
            self.logger.info("Starting error recovery sequence")
            
            # Find recovery target (agent buttons footer)
            if not self.recovery_image:
                raise RuntimeError("Recovery target image not loaded")
            
            match = self.matcher.find_template(screen, self.recovery_image)
            if not match:
                self.logger.error("Could not find recovery target")
                return False

            # Calculate click position (30px above target)
            click_x = match['x']
            click_y = match['y'] - 30

            if self.debug:
                annotated = screen.copy()
                self.matcher.draw_match(annotated, match)
                # Draw click target
                from PIL import ImageDraw
                draw = ImageDraw.Draw(annotated)
                draw.ellipse([click_x-2, click_y-2, click_x+2, click_y+2], fill='blue')
                save_debug_image(annotated, 'recovery_click_target', 'debug_output')

            # Perform recovery actions
            self.logger.info(f"Clicking at position ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            
            time.sleep(0.5)  # Wait for click to register
            
            self.logger.info("Typing 'continue'")
            pyautogui.write('continue')
            
            time.sleep(0.2)  # Wait for typing to complete
            
            self.logger.info("Pressing Enter")
            pyautogui.press('enter')
            
            self.logger.info("Recovery sequence completed")
            return True

        except Exception as e:
            log_error_with_context(self.logger, e, "Error during recovery sequence")
            return False

    def handle_error_case(self, screen):
        """Main error handling flow."""
        try:
            has_error, error_type = self.check_for_errors(screen)
            if has_error:
                self.logger.info(f"Detected error case: {error_type}")
                if self.perform_recovery(screen):
                    self.logger.info("Error recovery successful")
                    return True
                else:
                    self.logger.error("Error recovery failed")
                    return False
            return True
        except Exception as e:
            log_error_with_context(self.logger, e, "Error in error handling flow")
            return False 