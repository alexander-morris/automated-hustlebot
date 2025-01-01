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

# Set up directory structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
DEBUG_DIR = os.path.join(TEMP_DIR, "debug_output")
LOG_DIR = os.path.join(TEMP_DIR, "logs")
ANNOTATED_DIR = os.path.join(BASE_DIR, "annotated_matches")  # New directory for annotated images

# Create necessary directories
for directory in [TEMP_DIR, DEBUG_DIR, LOG_DIR, ANNOTATED_DIR]:
    os.makedirs(directory, exist_ok=True)

# Clear annotated directory at startup
for file in os.listdir(ANNOTATED_DIR):
    file_path = os.path.join(ANNOTATED_DIR, file)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception as e:
        logging.warning(f"Error deleting {file_path}: {e}")

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
    def __init__(self, threshold=0.75):
        self.threshold = threshold
        self.field_image = None
        self.target_image = None
        self.field_gray = None
        self.target_gray = None
        self.debug_dir = os.path.join(BASE_DIR, "temp", "debug_output")
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # Clear and create annotated matches directory
        self.annotated_dir = os.path.join(BASE_DIR, "annotated_matches")
        if os.path.exists(self.annotated_dir):
            shutil.rmtree(self.annotated_dir)
        os.makedirs(self.annotated_dir)
        
        # Updated thresholds with strict text feature requirements
        self.quality_thresholds = {
            'confidence': 0.85,  # Increased from 0.8
            'structural_similarity': 0.8,  # Increased from 0.7
            'edge_similarity': 0.4,  # Increased from 0.3
            'pixel_difference': 0.7,  # Increased from 0.6
            'histogram_similarity': 0.9,  # Increased from 0.85
            'consensus_count': 1
        }
        
        # Reduced scale range for faster processing
        self.scales = [0.95, 1.0, 1.05]
        
        # Reduced methods for faster processing
        self.methods = [
            (cv2.TM_CCOEFF_NORMED, "TM_CCOEFF_NORMED"),
            (cv2.TM_CCORR_NORMED, "TM_CCORR_NORMED")
        ]
    
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
    
    def extract_match_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Extract the region of the field image corresponding to a match."""
        try:
            # Ensure coordinates are within image bounds
            y1 = max(0, y)
            y2 = min(self.field_original.shape[0], y + height)
            x1 = max(0, x)
            x2 = min(self.field_original.shape[1], x + width)
            
            return self.field_original[y1:y2, x1:x2].copy()
        except Exception as e:
            logging.warning(f"Error extracting match region: {str(e)}")
            return np.zeros((height, width, 3), dtype=np.uint8)
            
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for template matching."""
        # Apply adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        equalized = clahe.apply(image)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(equalized, (3,3), 0)
        
        return blurred
        
    def load_images(self, field_path: str, target_path: str):
        """Load and preprocess the field and target images."""
        # Load images
        self.field_image = cv2.imread(field_path)
        self.target_image = cv2.imread(target_path)
        
        if self.field_image is None:
            raise ValueError(f"Failed to load field image: {field_path}")
        if self.target_image is None:
            raise ValueError(f"Failed to load target image: {target_path}")
        
        # Log image sizes
        logging.info(f"Loaded field image {field_path}: {self.field_image.shape[:2]}")
        logging.info(f"Loaded target image {target_path}: {self.target_image.shape[:2]}")
        
        # Convert to grayscale
        field_gray = cv2.cvtColor(self.field_image, cv2.COLOR_BGR2GRAY)
        target_gray = cv2.cvtColor(self.target_image, cv2.COLOR_BGR2GRAY)
        
        # Preprocess grayscale images
        self.field_gray = self.preprocess_image(field_gray)
        self.target_gray = self.preprocess_image(target_gray)
        
        return True
    
    def find_matches(self) -> List[Match]:
        """Find all matches of the target image in the field image."""
        all_matches = []
        
        # Try different scales
        for scale in self.scales:
            # Resize target image
            target_resized = cv2.resize(self.target_image, None, fx=scale, fy=scale)
            target_gray_resized = cv2.resize(self.target_gray, None, fx=scale, fy=scale)
            h, w = target_gray_resized.shape
            
            # Try different methods
            for method, method_name in self.methods:
                # Apply template matching
                result = cv2.matchTemplate(self.field_gray, target_gray_resized, method)
                
                # Get matches above threshold
                if method == cv2.TM_SQDIFF_NORMED:
                    match_locations = np.where(result <= (1 - self.threshold))
                else:
                    match_locations = np.where(result >= self.threshold)
                
                # Convert to list of (x, y) coordinates
                matches = list(zip(*match_locations[::-1]))  # Convert to (x, y) format
                
                # Apply non-maximum suppression
                if len(matches) > 0:
                    confidences = [float(result[y, x]) for x, y in matches]
                    if method == cv2.TM_SQDIFF_NORMED:
                        confidences = [1 - conf for conf in confidences]
                    
                    boxes = np.array([[x, y, x + w, y + h] for x, y in matches])
                    indices = cv2.dnn.NMSBoxes(boxes.tolist(), confidences, self.threshold, 0.3)
                    
                    if len(indices) > 0:
                        indices = indices.flatten()
                        filtered_matches = [matches[i] for i in indices]
                        filtered_confidences = [confidences[i] for i in indices]
                        
                        # Create Match objects for filtered matches
                        for (x, y), confidence in zip(filtered_matches, filtered_confidences):
                            # Extract region and calculate quality
                            region = self.field_image[y:y+h, x:x+w]
                            if region.shape[:2] != target_resized.shape[:2]:
                                continue
                            
                            quality = self.calculate_match_quality(region, target_resized)
                            
                            # Create Match object
                            match = Match(
                                x=x,
                                y=y,
                                width=w,
                                height=h,
                                confidence=confidence,
                                method=method_name,
                                scale=scale,
                                quality=quality,
                                consensus_count=1,
                                match_region=region.copy()
                            )
                            all_matches.append(match)
        
        # Find consensus matches
        consensus_matches = self._find_consensus_matches(all_matches)
        
        # Filter matches based on quality thresholds
        filtered_matches = []
        for match in consensus_matches:
            if (match.confidence >= self.quality_thresholds['confidence'] and
                match.quality.structural_similarity >= self.quality_thresholds['structural_similarity'] and
                match.quality.edge_similarity >= self.quality_thresholds['edge_similarity'] and
                match.quality.pixel_difference >= self.quality_thresholds['pixel_difference'] and
                match.quality.histogram_similarity >= self.quality_thresholds['histogram_similarity'] and
                match.consensus_count >= self.quality_thresholds['consensus_count']):
                filtered_matches.append(match)
        
        return filtered_matches
    
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
    
    def visualize_matches(self, matches: List[Match], output_path: str):
        """Create a visualization of the matches."""
        # Create a copy of the field image for visualization
        vis_image = self.field_image.copy()
        
        # Draw rectangles and text for each match
        for idx, match in enumerate(matches, 1):
            # Draw rectangle
            cv2.rectangle(vis_image, 
                         (match.x, match.y),
                         (match.x + match.width, match.y + match.height),
                         (0, 255, 0), 2)
            
            # Draw center point
            cv2.circle(vis_image, 
                      (match.center_x, match.center_y),
                      5, (0, 0, 255), -1)
            
            # Add text with match info
            text = f"#{idx} Conf: {match.confidence:.2f}"
            cv2.putText(vis_image, text,
                       (match.x, match.y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                       (0, 255, 0), 2)
        
        # Save visualization
        cv2.imwrite(output_path, vis_image)
        logging.info(f"Saved visualization to {output_path}")
        
        return vis_image

    def create_annotated_image(self, matches: List[Match], field_path: str):
        """Create a copy of the field image with red dots and confidence scores at match centers."""
        # Create a copy of the field image
        annotated_image = self.field_image.copy()
        
        # Draw red dots and confidence scores at match centers
        for idx, match in enumerate(matches, 1):
            # Draw red dot
            center = (match.center_x, match.center_y)
            cv2.circle(annotated_image, center, 10, (0, 0, 255), -1)  # Red dot
            
            # Add confidence score text
            text = f"#{idx} Conf: {match.confidence:.2f}"
            cv2.putText(annotated_image, text,
                       (match.center_x - 60, match.center_y - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                       (0, 0, 255), 2)  # Red text
            
            # Add quality metrics
            quality_text = f"SSIM: {match.quality.structural_similarity:.2f}"
            cv2.putText(annotated_image, quality_text,
                       (match.center_x - 60, match.center_y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                       (0, 0, 255), 2)  # Red text
        
        # Save the annotated image
        output_filename = f"annotated_{os.path.basename(field_path)}"
        output_path = os.path.join(self.annotated_dir, output_filename)
        cv2.imwrite(output_path, annotated_image)
        logging.info(f"Saved annotated image to {output_path}")
        
        return output_path

def test_matcher():
    matcher = ImageMatcher(threshold=0.75)
    
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