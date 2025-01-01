import cv2
import numpy as np
import os
import logging
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Dict
from statistics import mean, stdev
import shutil
import pyautogui
import gc
from PIL import Image

# Set up directory structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
DEBUG_DIR = os.path.join(TEMP_DIR, "debug_output")
LOG_DIR = os.path.join(TEMP_DIR, "logs")

# Create necessary directories
for directory in [TEMP_DIR, DEBUG_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'template_matching.log')),
        logging.StreamHandler()
    ]
)

@dataclass
class MatchQuality:
    structural_similarity: float  # SSIM score
    pixel_difference: float      # Mean absolute difference
    edge_similarity: float       # Edge detection similarity
    histogram_similarity: float  # Color histogram similarity

@dataclass
class Match:
    """Represents a match found in the screen image."""
    x: int                     # Top-left x coordinate
    y: int                     # Top-left y coordinate
    width: int                 # Width of match region
    height: int                # Height of match region
    confidence: float          # Match confidence score
    method: str               # Template matching method used
    scale: float              # Scale factor used
    quality: MatchQuality     # Quality metrics for the match
    consensus_count: int = 1  # Number of matches in consensus group
    match_region: np.ndarray = None  # The actual matched region
    
    @property
    def center_x(self) -> int:
        """Calculate center x coordinate."""
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        """Calculate center y coordinate."""
        return self.y + self.height // 2

class ImageMatcher:
    def __init__(self, threshold=0.1):
        self.threshold = threshold
        self.screen_image = None
        self.target_image = None
        self.screen_gray = None
        self.target_gray = None
        self.debug_dir = DEBUG_DIR
        
        # Cache for preprocessed images
        self._preprocessed_cache = {}
        
        # Reduced scales for better performance
        self.scales = [0.95, 1.0, 1.05]
        
        # Most effective matching methods
        self.methods = [
            (cv2.TM_CCOEFF_NORMED, "TM_CCOEFF_NORMED"),
            (cv2.TM_CCORR_NORMED, "TM_CCORR_NORMED")
        ]
        
        # Quality thresholds
        self.quality_thresholds = {
            'confidence': threshold,
            'structural_similarity': 0.1,
            'edge_similarity': 0.1,
            'pixel_difference': 0.1,
            'histogram_similarity': 0.1,
            'consensus_count': 1
        }
        
        # Initialize CLAHE for preprocessing
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

    def capture_screen(self):
        """Capture the current screen."""
        # Capture the screen
        screen = pyautogui.screenshot()
        # Convert to numpy array and BGR format
        screen_image = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        # Convert to grayscale
        screen_gray = cv2.cvtColor(screen_image, cv2.COLOR_BGR2GRAY)
        # Preprocess grayscale image
        screen_gray = self.preprocess_image(screen_gray)
        return screen_image, screen_gray

    def process_screen(self, screen_array: np.ndarray):
        """Optimized screen processing."""
        try:
            logging.debug("Starting screen processing")
            self.screen_image = screen_array
            logging.debug(f"Screen image shape: {self.screen_image.shape}")
            
            # Convert to grayscale efficiently
            if len(screen_array.shape) == 3:
                logging.debug("Converting color image to grayscale")
                self.screen_gray = cv2.cvtColor(screen_array, cv2.COLOR_RGB2GRAY)
            else:
                logging.debug("Image already in grayscale")
                self.screen_gray = screen_array
                
            logging.debug(f"Grayscale image shape: {self.screen_gray.shape}")
            logging.debug("Applying preprocessing...")
            self.screen_gray = self.preprocess_image(self.screen_gray)
            logging.debug("Screen processing complete")
        except Exception as e:
            logging.error(f"Error processing screen: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            raise

    def load_target(self, target_path: str):
        """Load target image to search for."""
        try:
            # Load target image using PIL to match raw screenshot format
            target_img = Image.open(target_path)
            target_img = target_img.convert('RGB')  # Ensure RGB format
            self.target = np.array(target_img)
            
            # Log target image details
            logging.info(f"Loaded target image {target_path}: {self.target.shape}")
            self.target_height, self.target_width = self.target.shape[:2]
            logging.info(f"Target dimensions: {self.target_width}x{self.target_height}")
            
            # Save normalized version for debugging
            debug_path = os.path.join(os.path.dirname(target_path), "target-norm.png")
            Image.fromarray(self.target).save(debug_path)
            logging.info(f"Saved normalized target image: {debug_path}")
            
            return True
        except Exception as e:
            logging.error(f"Error loading target image: {str(e)}")
            return False
            
    def find_matches(self, screen):
        """Find all matches in the screen image."""
        if self.target is None:
            logging.error("Target image not loaded")
            return []
            
        try:
            # Ensure screen is in correct format
            if isinstance(screen, Image.Image):
                screen = np.array(screen)
            
            # Convert both images to BGR for OpenCV
            if len(screen.shape) == 3 and screen.shape[2] == 3:
                screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            else:
                screen_bgr = screen
                
            target_bgr = cv2.cvtColor(self.target, cv2.COLOR_RGB2BGR)
                
            # Log shapes for debugging
            logging.info(f"Screen shape: {screen_bgr.shape}, Target shape: {target_bgr.shape}")
            logging.info(f"Screen dtype: {screen_bgr.dtype}, Target dtype: {target_bgr.dtype}")
            
            # Perform template matching
            result = cv2.matchTemplate(screen_bgr, target_bgr, cv2.TM_CCOEFF_NORMED)
            
            # Get all matches above minimum threshold
            locations = np.where(result >= 0.001)  # Very low threshold to see all potential matches
            matches = []
            
            for pt in zip(*locations[::-1]):
                x, y = pt
                confidence = result[y, x]
                
                # Extract regions for quality calculation
                screen_region = screen_bgr[y:y+target_bgr.shape[0], x:x+target_bgr.shape[1]]
                if screen_region.shape != target_bgr.shape:
                    continue
                    
                # Calculate match quality
                quality = self.calculate_match_quality(screen_region, target_bgr)
                
                # Create match object with correct parameters
                match = Match(
                    x=x,
                    y=y,
                    width=self.target_width,
                    height=self.target_height,
                    confidence=confidence,
                    method="TM_CCOEFF_NORMED",
                    scale=1.0,
                    quality=quality
                )
                matches.append(match)
                
            logging.info(f"Found {len(matches)} potential matches with confidence >= 0.001")
            if matches:
                best_match = max(matches, key=lambda m: m.confidence)
                logging.info(f"Best match confidence: {best_match.confidence:.4f}")
                worst_match = min(matches, key=lambda m: m.confidence)
                logging.info(f"Worst match confidence: {worst_match.confidence:.4f}")
            
            return matches
            
        except Exception as e:
            logging.error(f"Error finding matches: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return []

    def visualize_matches(self, matches: List[Match], output_path: str):
        """Create a debug image showing all matches with confidence scores."""
        # Create a copy of the screen image
        vis_image = self.screen_image.copy()
        
        # Sort matches by confidence for better visualization
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # Draw matches
        for idx, match in enumerate(matches):
            # Draw red dot at match center
            cv2.circle(vis_image, (match.center_x, match.center_y), 5, (0, 0, 255), -1)
            
            # Draw confidence score above the dot
            conf_text = f"#{idx+1} Conf: {match.confidence:.2f}"
            cv2.putText(vis_image, conf_text, 
                       (match.center_x - 40, match.center_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Draw quality metrics below the dot
            quality_text = f"SSIM: {match.quality.structural_similarity:.2f}"
            cv2.putText(vis_image, quality_text,
                       (match.center_x - 40, match.center_y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Draw rectangle around match region
            cv2.rectangle(vis_image, 
                         (match.x, match.y),
                         (match.x + match.width, match.y + match.height),
                         (0, 255, 0), 2)

        # Save the visualization
        cv2.imwrite(output_path, vis_image)

    def extract_match_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Extract the region of the screen image corresponding to a match."""
        try:
            # Ensure coordinates are within image bounds
            y1 = max(0, y)
            y2 = min(self.screen_image.shape[0], y + height)
            x1 = max(0, x)
            x2 = min(self.screen_image.shape[1], x + width)
            
            return self.screen_image[y1:y2, x1:x2].copy()
        except Exception as e:
            logging.warning(f"Error extracting match region: {str(e)}")
            return np.zeros((height, width, 3), dtype=np.uint8)

    def calculate_match_quality(self, region: np.ndarray, target: np.ndarray) -> MatchQuality:
        """Calculate quality metrics for a potential match."""
        try:
            # Quick size check
            if region is None or target is None:
                return MatchQuality(0.0, 0.0, 0.0, 0.0)
                
            # Convert to grayscale efficiently (assuming BGR input)
            region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
            
            # Calculate structural similarity first (fastest)
            ssim = cv2.matchTemplate(region_gray, target_gray, cv2.TM_CCOEFF_NORMED)[0][0]
            
            # Early exit if SSIM is too low
            if ssim < 0.1:
                return MatchQuality(
                    structural_similarity=float(ssim),
                    pixel_difference=0.0,
                    edge_similarity=0.0,
                    histogram_similarity=0.0
                )
            
            # Calculate other metrics only if SSIM is promising
            region_edges = cv2.Canny(region_gray, 100, 200)
            target_edges = cv2.Canny(target_gray, 100, 200)
            
            edge_overlap = np.sum(np.logical_and(region_edges > 0, target_edges > 0))
            edge_total = np.sum(np.logical_or(region_edges > 0, target_edges > 0))
            edge_sim = edge_overlap / (edge_total + 1e-6)
            
            # Calculate histogram similarity
            region_hist = cv2.calcHist([region_gray], [0], None, [256], [0, 256])
            target_hist = cv2.calcHist([target_gray], [0], None, [256], [0, 256])
            cv2.normalize(region_hist, region_hist)
            cv2.normalize(target_hist, target_hist)
            hist_sim = cv2.compareHist(region_hist, target_hist, cv2.HISTCMP_CORREL)
            
            # Calculate pixel difference
            pixel_diff = 1 - np.mean(np.abs(region_gray - target_gray)) / 255
            
            return MatchQuality(
                structural_similarity=float(ssim),
                pixel_difference=float(pixel_diff),
                edge_similarity=float(edge_sim),
                histogram_similarity=float(max(0, hist_sim))
            )
            
        except Exception as e:
            logging.warning(f"Error calculating match quality: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return MatchQuality(0.0, 0.0, 0.0, 0.0)

    def _find_consensus_matches(self, matches: List[Match], distance_threshold=20) -> List[Match]:
        """Optimized consensus finding."""
        if not matches:
            return []
            
        try:
            # Convert to numpy arrays for vectorized operations
            centers = np.array([(m.center_x, m.center_y) for m in matches])
            
            # Calculate pairwise distances
            distances = np.sqrt(((centers[:, np.newaxis] - centers) ** 2).sum(axis=2))
            
            # Find groups efficiently
            groups = []
            used = set()
            
            for i in range(len(matches)):
                if i in used:
                    continue
                    
                # Find all matches within threshold distance
                group_indices = np.where(distances[i] < distance_threshold)[0]
                if len(group_indices) >= 2:  # Require at least 2 matches
                    groups.append([matches[j] for j in group_indices])
                    used.update(group_indices)
            
            # Create consensus matches
            consensus_matches = []
            for group in groups:
                try:
                    # Calculate quality score vectorized
                    scores = np.array([
                        m.quality.structural_similarity * 0.35 +
                        m.quality.edge_similarity * 0.25 +
                        m.confidence * 0.25 +
                        m.quality.histogram_similarity * 0.15
                        for m in group
                    ])
                    
                    best_idx = np.argmax(scores)
                    best_match = group[best_idx]
                    
                    # Average coordinates
                    avg_x = int(np.mean([m.x for m in group]))
                    avg_y = int(np.mean([m.y for m in group]))
                    avg_scale = np.mean([m.scale for m in group])
                    
                    consensus_match = Match(
                        x=avg_x,
                        y=avg_y,
                        width=best_match.width,
                        height=best_match.height,
                        confidence=best_match.confidence,
                        method=best_match.method,
                        scale=avg_scale,
                        quality=best_match.quality,
                        consensus_count=len(group),
                        match_region=best_match.match_region
                    )
                    consensus_matches.append(consensus_match)
                except Exception as e:
                    logging.warning(f"Error creating consensus match: {str(e)}")
                    continue
            
            return sorted(consensus_matches, key=lambda m: m.confidence, reverse=True)
            
        except Exception as e:
            logging.error(f"Error finding consensus matches: {str(e)}")
            return []

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Optimized image preprocessing with caching."""
        # Check cache first
        cache_key = hash(image.tobytes())
        if cache_key in self._preprocessed_cache:
            return self._preprocessed_cache[cache_key]
            
        try:
            # Apply adaptive histogram equalization
            equalized = self.clahe.apply(image)
            
            # Apply Gaussian blur to reduce noise
            processed = cv2.GaussianBlur(equalized, (3,3), 0)
            
            # Cache result
            if len(self._preprocessed_cache) > 10:  # Limit cache size
                self._preprocessed_cache.clear()
            self._preprocessed_cache[cache_key] = processed
            
            return processed
        except Exception as e:
            logging.warning(f"Error preprocessing image: {str(e)}")
            return image

def test_matcher():
    matcher = ImageMatcher(threshold=0.1)
    
    # Get all field images
    image_dir = os.path.join(BASE_DIR, "images")
    target_path = os.path.join(image_dir, "target.png")
    field_images = [f for f in os.listdir(image_dir) if f.startswith("field") and f.endswith(".png")]
    
    total_start_time = time.time()
    match_results = []
    
    for field_image in field_images:
        field_path = os.path.join(image_dir, field_image)
        logging.info(f"\nProcessing {field_image}")
        
        try:
            # Load images and find matches
            matcher.load_images(field_path, target_path)
            matches = matcher.find_matches()
            
            # Create annotated image with red dot
            try:
                matcher.create_annotated_image(matches, field_path)
                logging.info(f"Successfully created annotated image for {field_image}")
            except Exception as e:
                logging.error(f"Error creating annotated image for {field_image}: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
            
            # Save visualization
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(matcher.debug_dir, f"matches_{field_image}_{timestamp}.png")
                matcher.visualize_matches(matches, output_path)
                logging.info(f"Successfully created visualization for {field_image}")
            except Exception as e:
                logging.error(f"Error creating visualization for {field_image}: {str(e)}")
                import traceback
                logging.error(traceback.format_exc())
            
            # Store results for summary
            match_results.append({
                'image': field_image,
                'matches': matches,
                'count': len(matches)
            })
            
            # Log detailed match information
            logging.info(f"\nDetailed Match Analysis for {field_image}:")
            for idx, match in enumerate(matches, 1):
                logging.info(f"\nMatch {idx}:")
                logging.info(f"Center Point: ({match.center_x}, {match.center_y})")
                logging.info(f"Bounding Box: ({match.x}, {match.y}, {match.x + match.width}, {match.y + match.height})")
                logging.info(f"Quality Metrics:")
                logging.info(f"- Confidence: {match.confidence:.3f}")
                logging.info(f"- Structural Similarity: {match.quality.structural_similarity:.3f}")
                logging.info(f"- Edge Similarity: {match.quality.edge_similarity:.3f}")
                logging.info(f"- Pixel Difference: {match.quality.pixel_difference:.3f}")
                logging.info(f"- Histogram Similarity: {match.quality.histogram_similarity:.3f}")
                logging.info(f"Method: {match.method} at scale {match.scale:.2f}")
                logging.info(f"Consensus Count: {match.consensus_count}")
        except Exception as e:
            logging.error(f"Error processing {field_image}: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            continue
    
    # Print summary
    total_time = time.time() - total_start_time
    logging.info("\n=== Summary ===")
    logging.info(f"Total images processed: {len(field_images)}")
    logging.info(f"Total processing time: {total_time:.3f} seconds")
    logging.info(f"Average time per image: {total_time/len(field_images):.3f} seconds")
    logging.info("\nMatches per image:")
    for result in match_results:
        logging.info(f"- {result['image']}: {result['count']} matches")

if __name__ == "__main__":
    test_matcher() 