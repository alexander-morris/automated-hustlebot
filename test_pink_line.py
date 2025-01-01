import mss
import numpy as np
from PIL import Image
import pytesseract
import cv2
import sys

def find_cursor_window():
    print("\nLooking for Cursor window...")
    with mss.mss() as sct:
        # We know it's monitor 3
        monitor = sct.monitors[3]  # Monitor 3
        print(f"\nChecking monitor 3:")
        print(f"  Size: {monitor['width']}x{monitor['height']}")
        print(f"  Position: ({monitor['left']}, {monitor['top']})")
        
        # Capture top-left region where nav bar should be
        region = {
            'left': monitor['left'],
            'top': monitor['top'],
            'width': 200,  # Wide enough for "Cursor"
            'height': 30   # Tall enough for nav bar
        }
        
        # Capture the region
        screenshot = sct.grab(region)
        img = np.array(screenshot)
        
        # Save raw image
        Image.fromarray(img).save("debug_nav.png")
        print("\nSaved raw screenshot to debug_nav.png")
        
        # Convert to grayscale for OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        
        # Apply thresholding to make text more visible
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Save processed image
        cv2.imwrite("debug_nav_processed.png", thresh)
        print("Saved processed image to debug_nav_processed.png")
        
        # Run OCR
        text = pytesseract.image_to_string(thresh)
        print("\nOCR Result:")
        print(text)
        
        # Check if "Cursor" is in the text
        if "Cursor" in text:
            print("\nFound 'Cursor' in the nav bar!")
            return monitor
        
        # Try with different threshold
        _, thresh2 = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        cv2.imwrite("debug_nav_processed2.png", thresh2)
        print("\nTrying with different threshold...")
        text = pytesseract.image_to_string(thresh2)
        print("\nOCR Result (second attempt):")
        print(text)
        
        if "Cursor" in text:
            print("\nFound 'Cursor' in the nav bar!")
            return monitor
        
        print("\nCould not find 'Cursor' in the nav bar")
        return None

def analyze_region():
    print("\n=== Line Detection Test ===")
    
    # First find the Cursor window
    cursor_monitor = find_cursor_window()
    if not cursor_monitor:
        print("Could not find Cursor window!")
        return
    
    print("\nFound Cursor window:")
    print(f"  Size: {cursor_monitor['width']}x{cursor_monitor['height']}")
    print(f"  Position: ({cursor_monitor['left']}, {cursor_monitor['top']})")
    
    # Scan the full width of the window
    region = {
        'left': cursor_monitor['left'],         # Start from left edge
        'top': cursor_monitor['top'],           # Start from very top
        'width': cursor_monitor['width'],       # Full width
        'height': 200                           # Tall enough region
    }
    
    print(f"\nAnalyzing region:")
    print(f"  Size: {region['width']}x{region['height']}")
    print(f"  Position: ({region['left']}, {region['top']})")
    print(f"  Bounds: ({region['left']}, {region['top']}) to ({region['left'] + region['width']}, {region['top'] + region['height']})")
    
    with mss.mss() as sct:
        # Capture region
        screenshot = sct.grab(region)
        img_array = np.array(screenshot)
        
        print(f"\nImage info:")
        print(f"  Shape: {img_array.shape}")
        print(f"  Data type: {img_array.dtype}")
        
        # Save raw image
        Image.fromarray(img_array).save("debug_region.png")
        print("\nSaved raw image to debug_region.png")
        
        # Look for horizontal lines where colors above and below are similar
        height, width = img_array.shape[:2]
        potential_lines = []
        
        # For each row (except first and last few)
        for y in range(2, height - 2):
            # Get colors of current row and rows above/below
            current_row = img_array[y]
            above_row = img_array[y - 2:y].mean(axis=0)  # Average of 2 rows above
            below_row = img_array[y + 1:y + 3].mean(axis=0)  # Average of 2 rows below
            
            # Look for sequences of similar pixels in the current row
            for x in range(width - 30):  # Look for lines at least 30px wide
                # Get the current sequence of pixels
                sequence = current_row[x:x + 30]
                
                # Check if sequence is relatively uniform (all pixels similar to each other)
                color_diff = np.abs(sequence - sequence.mean(axis=0))
                if np.all(color_diff.max(axis=0)[:3] < 20):  # More lenient uniformity check
                    # Get colors above and below this sequence
                    above_colors = above_row[x:x + 30]
                    below_colors = below_row[x:x + 30]
                    
                    # Check if colors above and below are very similar to each other
                    above_below_diff = np.abs(above_colors - below_colors)
                    if np.all(above_below_diff.max(axis=0)[:3] < 30):  # More lenient similarity check
                        # Check if line color is significantly different from above/below
                        line_diff = np.abs(sequence.mean(axis=0) - above_colors.mean(axis=0))
                        if np.any(line_diff[:3] > 30):  # More lenient difference required
                            # Check if line isn't too long (avoid borders)
                            line_length = 30
                            # Try to extend the line
                            for ext_x in range(x + 30, min(x + 200, width)):  # Cap at 200px
                                if np.all(np.abs(current_row[ext_x] - sequence[0]) < 20):
                                    line_length += 1
                                else:
                                    break
                            
                            # Only keep lines between 30 and 150 pixels
                            if 30 <= line_length <= 150:
                                potential_lines.append({
                                    'y': y,
                                    'x_start': x,
                                    'length': line_length,
                                    'color': sequence[0],
                                    'above_color': above_colors[0],
                                    'below_color': below_colors[0]
                                })
                            break  # Move to next row
        
        print(f"\nFound {len(potential_lines)} potential lines")
        
        # Sort by x_start position (from right to left)
        potential_lines.sort(key=lambda x: x['x_start'], reverse=True)
        
        if potential_lines:
            rightmost_line = potential_lines[0]
            print("\nRightmost line found:")
            print(f"  Position: y={rightmost_line['y']}, x={rightmost_line['x_start']}-{rightmost_line['x_start'] + rightmost_line['length']}")
            print(f"  Length: {rightmost_line['length']} pixels")
            print(f"  Line color (BGRA): {rightmost_line['color']}")
            print(f"  Above color (BGRA): {rightmost_line['above_color']}")
            print(f"  Below color (BGRA): {rightmost_line['below_color']}")
            print(f"  Window coordinates: ({rightmost_line['x_start'] + region['left']}, {rightmost_line['y'] + region['top']})")
            print(f"\nSearch area for Accept button should be to the right of x={rightmost_line['x_start'] + region['left']}")
        
        # Visualize the lines
        vis_img = img_array.copy()
        # Draw all lines in red
        for line in potential_lines:
            y = line['y']
            x_start = line['x_start']
            length = line['length']
            vis_img[y, x_start:x_start + length] = [0, 0, 255, 255]  # Red
        
        # Draw rightmost line in green
        if potential_lines:
            line = potential_lines[0]  # Rightmost line
            y = line['y']
            x_start = line['x_start']
            length = line['length']
            vis_img[y, x_start:x_start + length] = [0, 255, 0, 255]  # Green
            # Also mark the rows above and below
            vis_img[y-1:y, x_start:x_start + length] = [255, 0, 0, 255]  # Blue above
            vis_img[y+1:y+2, x_start:x_start + length] = [255, 0, 0, 255]  # Blue below
            # Draw vertical line at x_start to show search boundary
            vis_img[:, x_start:x_start + 2] = [255, 255, 0, 255]  # Yellow vertical line
            
        Image.fromarray(vis_img).save("debug_lines.png")
        print("\nSaved visualization to debug_lines.png")

if __name__ == "__main__":
    try:
        analyze_region()
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc() 