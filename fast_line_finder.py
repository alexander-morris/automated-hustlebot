import numpy as np
import cv2

def find_contrast_line(img, window_bounds):
    """Find contrast line without saving debug images."""
    # Extract window region
    window_region = img[
        window_bounds['y']:window_bounds['y'] + window_bounds['height'],
        window_bounds['x']:window_bounds['x'] + window_bounds['width']
    ]
    
    # Convert to grayscale and ensure float type for calculations
    if window_region.shape[-1] == 4:  # RGBA
        gray = cv2.cvtColor(window_region, cv2.COLOR_BGRA2GRAY).astype(np.float32)
    else:  # RGB
        gray = cv2.cvtColor(window_region, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Find lines with even contrast
    potential_lines = []
    
    # Only scan top portion
    scan_height = min(300, gray.shape[0])  # Increased scan height
    
    for y in range(scan_height):
        for x in range(10, gray.shape[1]-10):  # Skip edges
            # Check if this could be start of a line
            current_color = gray[y, x]
            
            # Look left and right
            sequence = []
            for ext_x in range(x, min(x+100, gray.shape[1])):
                # Compare as floats to avoid overflow
                if abs(float(gray[y, ext_x]) - float(sequence[0] if sequence else current_color)) < 15:  # Increased tolerance
                    sequence.append(gray[y, ext_x])
                else:
                    break
            
            if len(sequence) >= 30:  # Reduced minimum line width
                # Check contrast above and below
                if y > 0 and y < gray.shape[0]-1:
                    # Check multiple pixels above and below
                    above = np.mean(gray[max(0, y-2):y, x:x+len(sequence)])
                    below = np.mean(gray[y+1:min(gray.shape[0], y+3), x:x+len(sequence)])
                    contrast = abs(above - below)
                    if contrast > 50:  # Reduced contrast threshold
                        potential_lines.append({
                            'y': y + window_bounds['y'],  # Convert to absolute coordinates
                            'x': x + window_bounds['x'],
                            'width': len(sequence),
                            'contrast': contrast,
                            'color': window_region[y, x].tolist() if len(window_region[y, x].shape) > 0 else window_region[y, x]
                        })
                        x += len(sequence)  # Skip the rest of this line
    
    if not potential_lines:
        return None
        
    # Find rightmost line with good contrast
    rightmost_lines = sorted(potential_lines, key=lambda l: (l['x'] + l['width'], l['contrast']), reverse=True)
    
    # Return the line with highest contrast among the rightmost ones
    for line in rightmost_lines[:5]:  # Check top 5 rightmost lines
        if line['contrast'] > 80:  # Higher contrast threshold for final selection
            return line
            
    return rightmost_lines[0] if rightmost_lines else None 