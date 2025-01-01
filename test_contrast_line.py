import mss
import numpy as np
from PIL import Image
import cv2
from test_window_bounds import find_window_bounds

def find_contrast_line(img, window_bounds):
    """Find rightmost line with even contrast above and below."""
    print("\n=== Finding Contrast Line ===")
    
    # Extract window region
    window = img[
        window_bounds['y']:window_bounds['y'] + window_bounds['height'],
        window_bounds['x']:window_bounds['x'] + window_bounds['width']
    ]
    
    # Save window region for debugging
    Image.fromarray(window).save("debug_window_region.png")
    print("\nSaved window region to debug_window_region.png")
    
    # Convert to grayscale
    gray = cv2.cvtColor(window, cv2.COLOR_BGRA2GRAY)
    
    # Parameters for line detection
    min_line_width = 50  # Minimum width of line to consider
    contrast_threshold = 30  # Minimum difference in intensity to consider a line
    similarity_threshold = 10  # Maximum difference between above/below to be considered similar
    
    height, width = gray.shape
    potential_lines = []
    
    print("\nScanning for lines with even contrast...")
    
    # Only scan top portion of window
    scan_height = min(200, height)
    
    # For each row in the top portion
    for y in range(2, scan_height - 2):
        # Get current row and rows above/below
        current_row = gray[y]
        above_rows = gray[y-2:y].mean(axis=0)  # Average of 2 rows above
        below_rows = gray[y+1:y+3].mean(axis=0)  # Average of 2 rows below
        
        # Look for potential line starts
        for x in range(width - min_line_width):
            # Get sequence of pixels
            sequence = current_row[x:x + min_line_width]
            above_sequence = above_rows[x:x + min_line_width]
            below_sequence = below_rows[x:x + min_line_width]
            
            # Check if sequence is relatively uniform
            if np.std(sequence) < 10:  # Low standard deviation = uniform color
                # Check if above and below are similar to each other
                above_below_diff = np.abs(above_sequence - below_sequence)
                if np.mean(above_below_diff) < similarity_threshold:
                    # Check if line is different from above/below
                    line_contrast = np.abs(np.mean(sequence) - np.mean(above_sequence))
                    if line_contrast > contrast_threshold:
                        # Try to extend the line
                        line_width = min_line_width
                        for ext_x in range(x + min_line_width, width):
                            if abs(current_row[ext_x] - sequence[0]) < 10:
                                line_width += 1
                            else:
                                break
                        
                        potential_lines.append({
                            'y': y,
                            'x': x,
                            'width': line_width,
                            'contrast': line_contrast,
                            'color': window[y, x]  # Original color
                        })
                        break  # Move to next row
    
    print(f"\nFound {len(potential_lines)} potential lines")
    
    # Sort by x position (rightmost first)
    potential_lines.sort(key=lambda l: l['x'], reverse=True)
    
    # Create visualization
    vis_img = window.copy()
    
    # Draw all lines in red
    for line in potential_lines:
        y = line['y']
        x = line['x']
        width = line['width']
        vis_img[y, x:x + width] = [0, 0, 255, 255]  # Red
        # Draw contrast regions
        vis_img[y-1, x:x + width] = [255, 0, 0, 255]  # Blue above
        vis_img[y+1, x:x + width] = [255, 0, 0, 255]  # Blue below
    
    # Draw rightmost line in green
    if potential_lines:
        line = potential_lines[0]  # Rightmost line
        y = line['y']
        x = line['x']
        width = line['width']
        vis_img[y, x:x + width] = [0, 255, 0, 255]  # Green
        
        print("\nRightmost line found:")
        print(f"  Position: y={y}, x={x}")
        print(f"  Width: {width} pixels")
        print(f"  Contrast: {line['contrast']:.2f}")
        print(f"  Color (BGRA): {line['color']}")
        print(f"  Window coordinates: ({x + window_bounds['x']}, {y + window_bounds['y']})")
    
    # Save visualization
    Image.fromarray(vis_img).save("debug_contrast_lines.png")
    print("\nSaved visualization to debug_contrast_lines.png")
    
    return potential_lines[0] if potential_lines else None

if __name__ == "__main__":
    try:
        print("\nStep 1: Finding window bounds...")
        window_bounds = find_window_bounds()
        if not window_bounds:
            print("Failed to find window bounds!")
            exit(1)
            
        print("\nStep 2: Finding contrast line...")
        with mss.mss() as sct:
            # Capture the monitor
            monitor = sct.monitors[3]  # Monitor 3
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            
            line = find_contrast_line(img, window_bounds)
            if line:
                print("\nSuccess! Found contrast line.")
            else:
                print("\nFailed to find contrast line.")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc() 