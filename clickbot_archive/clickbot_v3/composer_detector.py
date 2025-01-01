"""
Composer detection module for finding the composer area in Cursor
"""
import cv2
import numpy as np
from PIL import Image
import pytesseract
import time

class ComposerDetector:
    def __init__(self):
        # Region where composer was last found
        self.last_composer_region = None
        
    def find_composer(self, screenshot):
        """
        Find the composer area in a screenshot
        Returns: (x, y, w, h) of composer area or None if not found
        """
        try:
            # Convert to numpy array
            img_array = np.array(screenshot)
            
            # Try both light and dark text detection
            text_regions = self._find_text_regions(img_array)
            
            # Look for composer-related text
            composer_keywords = ['composer', 'write', 'message', 'type']
            
            for region, text in text_regions:
                if any(keyword in text.lower() for keyword in composer_keywords):
                    print(f"Found composer area with text: {text}")
                    self.last_composer_region = region
                    return region
            
            print("Composer area not found")
            return None
            
        except Exception as e:
            print(f"Error finding composer: {str(e)}")
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
                
                # Skip if too small
                if w < 50 or h < 20:
                    continue
                
                # Extract region and get text
                region_img = Image.fromarray(result[y:y+h, x:x+w])
                text = pytesseract.image_to_string(region_img).strip()
                
                if text:
                    results.append(((x, y, w, h), text))
        
        return results
    
    def get_composer_region(self):
        """Get the last found composer region"""
        return self.last_composer_region 