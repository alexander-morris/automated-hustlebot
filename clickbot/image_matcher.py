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
    x: int
    y: int
    width: int
    height: int
    confidence: float
    method: str
    scale: float
    quality: MatchQuality
    consensus_count: int = 1
    match_region: np.ndarray = None
    
    @property
    def center_x(self) -> int:
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        return self.y + self.height // 2

class ImageMatcher:
    def __init__(self, threshold=0.1):  # Lowered threshold to 0.1
        self.threshold = threshold
        self.screen_image = None
        self.target_image = None
        self.screen_gray = None
        self.target_gray = None
        self.debug_dir = DEBUG_DIR
        
        # Updated thresholds with lower values to catch more potential matches
        self.quality_thresholds = {
            'confidence': 0.1,  # Lowered significantly
            'structural_similarity': 0.1,
            'edge_similarity': 0.1,
            'pixel_difference': 0.1,
            'histogram_similarity': 0.1,
            'consensus_count': 1
        }
        
        # Expanded scale range for better detection
        self.scales = [0.9, 0.95, 1.0, 1.05, 1.1]
        
        # Using all matching methods for comprehensive search
        self.methods = [
            (cv2.TM_CCOEFF_NORMED, "TM_CCOEFF_NORMED"),
            (cv2.TM_CCORR_NORMED, "TM_CCORR_NORMED"),
            (cv2.TM_SQDIFF_NORMED, "TM_SQDIFF_NORMED")
        ]

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
        """Process a provided screen array."""
        self.screen_image = screen_array
        # Convert to grayscale
        self.screen_gray = cv2.cvtColor(screen_array, cv2.COLOR_RGB2BGR)
        self.screen_gray = cv2.cvtColor(self.screen_gray, cv2.COLOR_BGR2GRAY)
        # Preprocess grayscale image
        self.screen_gray = self.preprocess_image(self.screen_gray)
        
    def load_target(self, target_path: str):
        """Load and preprocess the target image."""
        self.target_image = cv2.imread(target_path)
        if self.target_image is None:
            raise ValueError(f"Failed to load target image: {target_path}")
        
        logging.info(f"Loaded target image {target_path}: {self.target_image.shape[:2]}")
        
        # Convert to grayscale
        target_gray = cv2.cvtColor(self.target_image, cv2.COLOR_BGR2GRAY)
        # Preprocess grayscale image
        self.target_gray = self.preprocess_image(target_gray)
        return True

    def find_matches(self, screen_array: np.ndarray = None) -> List[Match]:
        """Find all matches of the target image in the screen image."""
        if screen_array is not None:
            self.process_screen(screen_array)
            
        if self.screen_gray is None or self.target_gray is None:
            raise ValueError("Screen and target images must be loaded first")

        all_matches = []
        timestamp = int(time.time())

        for scale in self.scales:
            # Scale target image
            if scale != 1.0:
                width = int(self.target_gray.shape[1] * scale)
                height = int(self.target_gray.shape[0] * scale)
                scaled_target = cv2.resize(self.target_gray, (width, height))
            else:
                scaled_target = self.target_gray

            for method, method_name in self.methods:
                # Apply template matching
                result = cv2.matchTemplate(self.screen_gray, scaled_target, method)
                
                # Handle different method result interpretations
                if method == cv2.TM_SQDIFF_NORMED:
                    result = 1 - result

                # Find all matches above threshold
                locations = np.where(result >= self.threshold)
                
                for pt in zip(*locations[::-1]):  # Switch columns and rows
                    match_region = self.extract_match_region(
                        pt[0], pt[1], 
                        scaled_target.shape[1], 
                        scaled_target.shape[0]
                    )
                    
                    # Calculate match quality
                    quality = self.calculate_match_quality(match_region, self.target_image)
                    
                    match = Match(
                        x=pt[0],
                        y=pt[1],
                        width=scaled_target.shape[1],
                        height=scaled_target.shape[0],
                        confidence=float(result[pt[1], pt[0]]),
                        method=method_name,
                        scale=scale,
                        quality=quality,
                        match_region=match_region
                    )
                    
                    all_matches.append(match)

        # Find consensus among matches
        consensus_matches = self._find_consensus_matches(all_matches)
        
        # Save debug visualization
        if consensus_matches:
            debug_path = os.path.join(self.debug_dir, f"matches_{timestamp}.png")
            self.visualize_matches(consensus_matches, debug_path)
            logging.info(f"Saved match visualization to {debug_path}")

        return consensus_matches

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
        """Calculate various quality metrics for a match with emphasis on text features."""
        try:
            # Resize target to match region size if needed
            if region.shape != target.shape:
                target = cv2.resize(target, (region.shape[1], region.shape[0]))
            
            # Convert to grayscale for structural analysis
            region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding to better handle varying lighting
            region_binary = cv2.adaptiveThreshold(region_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                cv2.THRESH_BINARY, 11, 2)
            target_binary = cv2.adaptiveThreshold(target_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                cv2.THRESH_BINARY, 11, 2)
            
            # Calculate structural similarity on binary images
            ssim = cv2.matchTemplate(region_binary, target_binary, cv2.TM_CCOEFF_NORMED)[0][0]
            
            # Enhanced edge detection with multiple thresholds
            region_edges = cv2.Canny(region_binary, 100, 200)
            target_edges = cv2.Canny(target_binary, 100, 200)
            
            # Calculate edge similarity using both overlap and orientation
            edge_overlap = np.sum(np.logical_and(region_edges > 0, target_edges > 0))
            edge_total = np.sum(np.logical_or(region_edges > 0, target_edges > 0))
            edge_sim = edge_overlap / (edge_total + 1e-6)
            
            # Calculate pixel-wise difference on binary images
            pixel_diff = 1 - (np.sum(np.abs(region_binary - target_binary)) / (region_binary.size * 255))
            
            # Calculate contour similarity and analyze text features
            region_contours, _ = cv2.findContours(region_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            target_contours, _ = cv2.findContours(target_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Compare number and size of contours
            contour_score = 0
            if len(region_contours) > 0 and len(target_contours) > 0:
                # Compare total area
                region_area = sum(cv2.contourArea(c) for c in region_contours)
                target_area = sum(cv2.contourArea(c) for c in target_contours)
                area_ratio = min(region_area, target_area) / max(region_area, target_area)
                
                # Compare number of contours (characters)
                contour_count_ratio = min(len(region_contours), len(target_contours)) / max(len(region_contours), len(target_contours))
                
                # Compare aspect ratios of contours
                def get_aspect_ratios(contours):
                    ratios = []
                    for c in contours:
                        x, y, w, h = cv2.boundingRect(c)
                        if h > 0:  # Avoid division by zero
                            ratios.append(w / h)
                    return ratios
                
                region_ratios = get_aspect_ratios(region_contours)
                target_ratios = get_aspect_ratios(target_contours)
                
                # Compare distribution of aspect ratios
                if region_ratios and target_ratios:
                    ratio_diff = abs(np.mean(region_ratios) - np.mean(target_ratios))
                    ratio_sim = 1 / (1 + ratio_diff)
                else:
                    ratio_sim = 0
                
                # Combine contour metrics
                contour_score = (area_ratio * 0.4 + contour_count_ratio * 0.4 + ratio_sim * 0.2)
            
            # Calculate histogram similarity only on the binary images
            region_hist = cv2.calcHist([region_binary], [0], None, [2], [0, 256])
            target_hist = cv2.calcHist([target_binary], [0], None, [2], [0, 256])
            cv2.normalize(region_hist, region_hist)
            cv2.normalize(target_hist, target_hist)
            hist_sim = cv2.compareHist(region_hist, target_hist, cv2.HISTCMP_CORREL)
            
            # Weight the structural similarity more heavily and incorporate contour analysis
            weighted_ssim = ssim * 0.5 + contour_score * 0.5
            
            return MatchQuality(
                structural_similarity=float(weighted_ssim),
                pixel_difference=float(pixel_diff),
                edge_similarity=float(edge_sim),
                histogram_similarity=float(max(0, hist_sim))
            )
        except Exception as e:
            logging.warning(f"Error calculating match quality: {str(e)}")
            return MatchQuality(
                structural_similarity=0.0,
                pixel_difference=0.0,
                edge_similarity=0.0,
                histogram_similarity=0.0
            )
    
    def _find_consensus_matches(self, matches: List[Match], distance_threshold=20) -> List[Match]:
        if not matches:
            return []
        
        # Group matches by proximity
        match_groups: Dict[Tuple[int, int], List[Match]] = {}
        
        for match in matches:
            matched = False
            for center in match_groups.keys():
                if self._is_overlapping((match.center_x, match.center_y), center, distance_threshold):
                    match_groups[center].append(match)
                    matched = True
                    break
            if not matched:
                match_groups[(match.center_x, match.center_y)] = [match]
        
        # Create consensus matches
        consensus_matches = []
        for group in match_groups.values():
            if len(group) < 2:  # Require at least 2 methods to agree
                continue
            
            try:
                # Calculate quality score for sorting
                def quality_score(m):
                    return (
                        m.quality.structural_similarity * 0.35 +
                        m.quality.edge_similarity * 0.25 +
                        m.confidence * 0.25 +
                        m.quality.histogram_similarity * 0.15
                    )
                
                # Use the match with highest quality as base
                best_match = max(group, key=quality_score)
                
                # Average the coordinates and scale
                avg_x = int(mean(m.x for m in group))
                avg_y = int(mean(m.y for m in group))
                avg_scale = mean(m.scale for m in group)
                
                # Create consensus match using the best match's quality metrics
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
        
        return sorted(consensus_matches, key=quality_score, reverse=True)
    
    def _is_overlapping(self, loc1: Tuple[int, int], loc2: Tuple[int, int], overlap_threshold: int) -> bool:
        x1, y1 = loc1
        x2, y2 = loc2
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance < overlap_threshold

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for template matching."""
        try:
            # Apply adaptive histogram equalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            equalized = clahe.apply(image)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(equalized, (3,3), 0)
            
            return blurred
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