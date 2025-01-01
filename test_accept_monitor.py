import mss
import numpy as np
import cv2
import pytesseract
import time
import pyautogui
from fast_window_finder import find_window_bounds
from fast_line_finder import find_contrast_line
from datetime import datetime

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-4]
    print(f"[{timestamp}] {message}")

def click_accept_button(button_info):
    """Click the Accept button and verify click permissions."""
    try:
        # Calculate target coordinates - center of the button
        target_x = button_info['x'] + button_info['width'] // 2
        target_y = button_info['y'] + button_info['height'] // 2
        
        # Log detailed click information
        log(f"Attempting click at center: ({target_x}, {target_y})")
        log(f"Button info: {button_info}")
        
        # Move to button position first
        pyautogui.moveTo(target_x, target_y, duration=0.2)
        time.sleep(0.1)  # Brief pause to ensure movement completed
        
        # Perform click
        pyautogui.click(target_x, target_y)
        log("Click performed successfully")
        return True
        
    except Exception as e:
        log(f"Click failed: {str(e)}")
        return False

def get_accept_match_score(text):
    """Calculate how well the text matches 'Accept'"""
    target = "Accept"
    if not text:
        return 0
    
    # Convert to title case to ensure first letter is capital
    text = text.title()
    
    # Count matching characters in sequence
    score = 0
    last_match_pos = -1
    for c in text:
        if last_match_pos + 1 < len(target) and c == target[last_match_pos + 1]:
            score += 1
            last_match_pos += 1
            
    return score

def monitor_accept_button(img, window_bounds, special_line):
    """Monitor area to right of special line for Accept button."""
    # Calculate monitoring region - focus on right side where button should be
    x_start = max(0, window_bounds['width'] - 400)  # Last 400 pixels from right edge
    y_start = max(0, window_bounds['height'] // 2)  # Start from middle of window
    width = min(400, window_bounds['width'] - x_start)  # Wider scan area
    height = min(500, window_bounds['height'] - y_start)  # Taller scan area
    
    if width <= 0 or height <= 0:
        log("Invalid monitoring region dimensions")
        return []
        
    # Target area for button (around 1817 x coordinate)
    target_x = 1817 - x_start  # Convert to relative coordinates
    log(f"Target X coordinate (relative): {target_x}")
    
    # Expected button characteristics
    EXPECTED_WIDTH_RANGE = (70, 100)  # Expected width of Accept button (slightly wider range)
    EXPECTED_HEIGHT_RANGE = (15, 35)  # Expected height of Accept button (slightly taller range)
    EXPECTED_AREA_RANGE = (1000, 3000)  # Expected total white pixel area (wider range)
    
    # Log original image resolution
    log(f"Original image resolution: {img.shape[1]}x{img.shape[0]}")
    
    # Extract monitoring region
    monitor_region = img[
        y_start:y_start + height,
        x_start:x_start + width
    ]
    log(f"Monitor region resolution: {monitor_region.shape[1]}x{monitor_region.shape[0]}")
    log(f"Scanning area: X={x_start} to {x_start + width}, Y={y_start} to {y_start + height}")
    
    # Save the tight scan area for debugging
    timestamp = int(time.time() * 1000)
    debug_filename = f'debug_scan_area_{timestamp}.png'
    scan_area_debug = monitor_region.copy()
    
    # Draw a grid every 10 pixels for scale reference
    for i in range(0, scan_area_debug.shape[0], 10):
        cv2.line(scan_area_debug, (0, i), (width, i), (0, 255, 0), 1)
    for i in range(0, scan_area_debug.shape[1], 10):
        cv2.line(scan_area_debug, (i, 0), (i, height), (0, 255, 0), 1)
    
    # Add Y-coordinate and X-coordinate markers every 50 pixels
    font = cv2.FONT_HERSHEY_SIMPLEX
    for i in range(0, scan_area_debug.shape[0], 50):
        actual_y = y_start + i
        cv2.putText(scan_area_debug, str(actual_y), (2, i+10), font, 0.3, (0, 255, 0), 1)
    for i in range(0, scan_area_debug.shape[1], 50):
        actual_x = x_start + i
        cv2.putText(scan_area_debug, str(actual_x), (i, 10), font, 0.3, (0, 255, 0), 1)
    
    cv2.imwrite(debug_filename, cv2.cvtColor(scan_area_debug, cv2.COLOR_RGB2BGR))
    log(f"Saved scan area debug image: {debug_filename}")
    
    # Convert to grayscale
    gray_region = cv2.cvtColor(monitor_region, cv2.COLOR_RGB2GRAY)
    
    # Find all white regions (threshold > 200)
    _, white_mask = cv2.threshold(gray_region, 200, 255, cv2.THRESH_BINARY)
    
    # Find connected components of white pixels
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(white_mask, connectivity=8)
    
    # First group nearby regions
    merged_groups = []
    processed = set()
    
    for i in range(1, num_labels):
        if i in processed:
            continue
            
        group = []
        to_check = [i]
        
        while to_check:
            current = to_check.pop()
            if current in processed:
                continue
                
            processed.add(current)
            x = stats[current, cv2.CC_STAT_LEFT]
            y = stats[current, cv2.CC_STAT_TOP]
            w = stats[current, cv2.CC_STAT_WIDTH]
            h = stats[current, cv2.CC_STAT_HEIGHT]
            area = stats[current, cv2.CC_STAT_AREA]
            
            if area < 10:  # Skip very tiny regions
                continue
                
            group.append((x, y, w, h, area))
            
            # Look for nearby regions
            for j in range(1, num_labels):
                if j in processed:
                    continue
                    
                x2 = stats[j, cv2.CC_STAT_LEFT]
                y2 = stats[j, cv2.CC_STAT_TOP]
                w2 = stats[j, cv2.CC_STAT_WIDTH]
                h2 = stats[j, cv2.CC_STAT_HEIGHT]
                
                # Check if regions are within 15 pixels
                x_dist = min(abs(x2 - (x + w)), abs(x - (x2 + w2)))
                y_dist = min(abs(y2 - (y + h)), abs(y - (y2 + h2)))
                
                if x_dist <= 15 and y_dist <= 15:
                    to_check.append(j)
        
        if group:
            # Only add groups that are close to target X coordinate
            group_center_x = sum(r[0] + r[2]/2 for r in group) / len(group)
            if abs(group_center_x - target_x) < 100:  # Increased range to 100 pixels
                merged_groups.append(group)
                log(f"Added group centered at X={x_start + group_center_x}")
    
    log(f"\nFound {len(merged_groups)} merged white regions near target X:")
    
    # Process each merged group
    regions = []
    log("\nProcessing white regions:")
    for group_idx, group in enumerate(merged_groups):
        # Calculate bounding box for entire group
        min_x = min(r[0] for r in group)
        min_y = min(r[1] for r in group)
        max_x = max(r[0] + r[2] for r in group)
        max_y = max(r[1] + r[3] for r in group)
        total_area = sum(r[4] for r in group)
        
        w = max_x - min_x
        h = max_y - min_y
        aspect = w/h if h > 0 else float('inf')
        
        # Extract and process this region for OCR
        region_slice = monitor_region[min_y:max_y, min_x:max_x]
        
        # Scale up for OCR
        scale_factor = 16
        scaled = cv2.resize(region_slice, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale if needed
        if len(scaled.shape) == 3:
            scaled = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
        
        # Add padding
        pad_x = 20 * scale_factor
        pad_y = 10 * scale_factor
        padded = cv2.copyMakeBorder(scaled, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=255)
        
        # Simple threshold
        _, binary = cv2.threshold(padded, 200, 255, cv2.THRESH_BINARY)
        
        # Save debug image of processed region
        debug_region_file = f'debug_merged_region_{timestamp}_{group_idx+1}.png'
        cv2.imwrite(debug_region_file, binary)
        
        # Run OCR with optimized settings
        custom_config = r'--psm 8 --oem 1'
        text = pytesseract.image_to_string(binary, config=custom_config).strip()
        
        # Calculate match score
        score = 0
        target = "Accept"
        if text:
            # Try different case variations
            variations = [text, text.lower(), text.upper(), text.title()]
            for variant in variations:
                temp_score = 0
                last_pos = -1
                for c in variant:
                    if last_pos + 1 < len(target) and c == target[last_pos + 1]:
                        temp_score += 1
                        last_pos += 1
                score = max(score, temp_score)
        
        # Calculate white pixel density
        gray_slice = cv2.cvtColor(region_slice, cv2.COLOR_RGB2GRAY) if len(region_slice.shape) == 3 else region_slice
        _, density_binary = cv2.threshold(gray_slice, 200, 255, cv2.THRESH_BINARY)
        white_density = np.sum(density_binary == 255) / (w * h)
        
        abs_x = x_start + min_x
        abs_y = y_start + min_y
        
        # Log all regions with their characteristics
        log(f"Region {group_idx + 1}:")
        log(f"  Position: ({abs_x}, {abs_y})")
        log(f"  Size: {w}x{h}")
        log(f"  Total Area: {total_area}")
        log(f"  White Density: {white_density:.2f}")
        log(f"  Aspect ratio: {aspect:.2f}")
        log(f"  OCR text: '{text}'")
        log(f"  Accept match score: {score}")
        log(f"  Saved as: {debug_region_file}")
        
        # Now check if this is a potential Accept button
        if (EXPECTED_WIDTH_RANGE[0] <= w <= EXPECTED_WIDTH_RANGE[1] and
            EXPECTED_HEIGHT_RANGE[0] <= h <= EXPECTED_HEIGHT_RANGE[1] and
            EXPECTED_AREA_RANGE[0] <= total_area <= EXPECTED_AREA_RANGE[1] and
            0.2 <= white_density <= 0.6 and  # Wider density range
            score >= 2):  # At least 2 matching characters
            
            log("  *** MATCHES ACCEPT BUTTON CRITERIA ***")
            regions.append({
                'x': abs_x,
                'y': abs_y,
                'width': w,
                'height': h,
                'text': text,
                'area': total_area,
                'density': white_density,
                'match_score': score
            })
        log("---")
    
    # Return the best matching region if any found
    if regions:
        # Sort by match score first, then by proximity to target X coordinate
        regions.sort(key=lambda r: (-r['match_score'], abs((r['x'] + r['width']/2) - 1817)))
        return [regions[0]]
    
    return []

if __name__ == "__main__":
    log("Starting Accept button monitor (Press Ctrl+C to stop)")
    
    # Initialize monitor selection
    target_monitor = None
    try:
        with mss.mss() as sct:
            if len(sct.monitors) == 0:
                log("No monitors found!")
                exit(1)
                
            log(f"Available monitors: {len(sct.monitors)}")
            for i, m in enumerate(sct.monitors):
                log(f"Monitor {i}: {m['width']}x{m['height']} at ({m['left']}, {m['top']})")
            
            # Use primary monitor (index 0) by default
            target_monitor = 0
            log(f"Using monitor {target_monitor}")
        
        if target_monitor is None:
            log("Failed to select a monitor!")
            exit(1)
        
        scan_count = 0
        last_status = time.time()
        error_count = 0  # Track consecutive errors
        MAX_ERRORS = 5   # Maximum consecutive errors before exit
        
        while True:
            try:
                scan_count += 1
                if time.time() - last_status >= 5:
                    log(f"Still monitoring... ({scan_count} scans in last 5s)")
                    scan_count = 0
                    last_status = time.time()
                    error_count = 0  # Reset error count on successful status update
                
                # Find window bounds
                window_bounds = find_window_bounds()
                if not window_bounds or not isinstance(window_bounds, dict) or 'width' not in window_bounds or 'height' not in window_bounds:
                    time.sleep(0.05)
                    continue
                
                # Take screenshot and find special line
                with mss.mss() as sct:
                    if target_monitor >= len(sct.monitors):
                        log(f"Error: Monitor {target_monitor} no longer available!")
                        break
                        
                    monitor = sct.monitors[target_monitor]
                    screenshot = sct.grab(monitor)
                    img = np.array(screenshot)
                    
                    # Verify image dimensions
                    if len(img.shape) < 2 or img.shape[0] == 0 or img.shape[1] == 0:
                        log("Invalid screenshot dimensions")
                        time.sleep(0.05)
                        continue
                    
                    special_line = find_contrast_line(img, window_bounds)
                    if not special_line:
                        time.sleep(0.05)
                        continue
                    
                    # Monitor for Accept button
                    accept_regions = monitor_accept_button(img, window_bounds, special_line)
                    
                    if accept_regions:
                        # Click the first Accept button found
                        click_accept_button(accept_regions[0])
                        time.sleep(0.1)
                    else:
                        time.sleep(0.01)
                    
            except KeyboardInterrupt:
                log("Received interrupt signal, stopping monitor...")
                break
            except Exception as e:
                error_count += 1
                log(f"Error ({error_count}/{MAX_ERRORS}): {str(e)}")
                if error_count >= MAX_ERRORS:
                    log("Too many consecutive errors, stopping monitor...")
                    break
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log(f"Fatal error: {str(e)}")
    finally:
        log("Monitor stopped.") 