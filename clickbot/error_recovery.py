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
        self.error_threshold = 0.8  # Confidence threshold for error detection
        self.max_retries = 3  # Maximum number of retries for recovery
        
        # Load reference images
        self.images_dir = os.path.join(os.path.dirname(__file__), 'images')
        self.error_images = {}  # Initialize empty, load on demand
        self.recovery_image = None  # Initialize empty, load on demand

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

    def _ensure_images_loaded(self):
        """Ensure all necessary images are loaded."""
        if not self.error_images:
            self.error_images = self._load_error_images()
        if not self.recovery_image:
            self.recovery_image = self._load_recovery_image()

    def perform_recovery(self, screen):
        """Perform the recovery sequence."""
        self.logger.info("Starting error recovery sequence")
        self._ensure_images_loaded()
        
        try:
            if not self.recovery_image:
                self.logger.error("Recovery target image not loaded")
                return False
            
            # Find the recovery target with retries
            target = None
            for attempt in range(self.max_retries):
                target = self.matcher.find_template(
                    screen, 
                    self.recovery_image,
                    threshold=self.error_threshold
                )
                if target:
                    break
                time.sleep(1)  # Wait before retry
            
            if not target:
                self.logger.error("Could not find recovery target")
                return False
            
            # Calculate click position (30 pixels above target)
            click_y = max(0, target['y'] - 30)  # Ensure y doesn't go negative
            
            # Perform the recovery sequence
            self.logger.info(f"Clicking at position ({target['x']}, {click_y})")
            pyautogui.click(target['x'], click_y)
            time.sleep(0.5)  # Wait after click
            
            self.logger.info("Typing 'continue'")
            pyautogui.write('continue')
            time.sleep(0.2)  # Wait after typing
            
            self.logger.info("Pressing Enter")
            pyautogui.press('enter')
            
            self.logger.info("Recovery sequence completed")
            return True
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Error during recovery sequence")
            return False

    def check_for_errors(self, screen):
        """Check if error conditions are met (two error icons or note text)."""
        self._ensure_images_loaded()
        
        try:
            error_icon = self.error_images.get('error-icon.png')
            note_text = self.error_images.get('note-text.png')
            
            if not error_icon:
                self.logger.error("Error icon template not loaded")
                return False, None

            # Find all error icon instances
            error_matches = self.find_all_error_matches(screen, error_icon)
            
            # We need at least two high-confidence error icons
            high_confidence_matches = [m for m in error_matches if m['confidence'] >= self.error_threshold]
            if len(high_confidence_matches) >= 2:
                self.logger.info(f"Found {len(high_confidence_matches)} high-confidence error icons")
                return True, 'multiple_error_icons'

            # Check for note text as additional validation
            if note_text:
                note_match = self.matcher.find_template(
                    screen, 
                    note_text,
                    threshold=self.error_threshold
                )
                if note_match and note_match['confidence'] >= self.error_threshold:
                    self.logger.info(f"Found note text with confidence {note_match['confidence']:.4f}")
                    return True, 'note_text'

            return False, None
        except Exception as e:
            log_error_with_context(self.logger, e, "Error checking for error indicators")
            return False, None

    def find_all_error_matches(self, screen, template):
        """Find all instances of an error indicator in the screen."""
        try:
            matches = []
            result = None
            
            # Use multi-scale template matching to find all instances
            scales = [1.0, 0.9, 1.1]  # Try different scales to handle size variations
            
            for scale in scales:
                # Scale the template
                if scale != 1.0:
                    w = int(template.width * scale)
                    h = int(template.height * scale)
                    scaled_template = template.resize((w, h))
                else:
                    scaled_template = template

                # Find matches at this scale
                result = self.matcher.find_template(screen, scaled_template, threshold=self.error_threshold)
                if result:
                    # Check if this match overlaps with existing matches
                    is_unique = True
                    for existing in matches:
                        # Calculate overlap
                        x_overlap = abs(result['x'] - existing['x']) < template.width
                        y_overlap = abs(result['y'] - existing['y']) < template.height
                        if x_overlap and y_overlap:
                            is_unique = False
                            break
                    
                    if is_unique:
                        matches.append(result)
                        
                        if self.debug:
                            self.logger.debug(f"Found error match at ({result['x']}, {result['y']}) "
                                          f"with confidence {result['confidence']:.4f}")

            return matches
        except Exception as e:
            log_error_with_context(self.logger, e, "Error finding error matches")
            return []

    def handle_error_case(self, screen):
        """Main error handling flow."""
        has_error, error_type = self.check_for_errors(screen)
        if has_error:
            self.logger.info(f"Detected error condition: {error_type}")
            return self.perform_recovery(screen)
        return False 