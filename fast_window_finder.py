import mss
import numpy as np
import cv2

def find_window_bounds():
    """Find Cursor window bounds without saving debug images."""
    with mss.mss() as sct:
        # Use primary monitor
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        
        # Convert to grayscale (handle both RGB and RGBA)
        if img.shape[-1] == 4:  # RGBA
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        else:  # RGB
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Edge detection with more sensitive thresholds
        edges = cv2.Canny(gray, 30, 100)  # Lower thresholds to detect more edges
        
        # Find horizontal lines
        horizontal_lines = []
        for y in range(edges.shape[0]):
            line_start = None
            for x in range(edges.shape[1]):
                if edges[y, x] > 0:
                    if line_start is None:
                        line_start = x
                elif line_start is not None:
                    length = x - line_start
                    if length > 50:  # Reduced minimum length to detect more lines
                        horizontal_lines.append((y, line_start, x, length))
                    line_start = None
        
        # Sort by length
        horizontal_lines.sort(key=lambda x: x[3], reverse=True)
        
        if len(horizontal_lines) < 5:  # Need at least 5 horizontal lines
            return None
            
        # Find vertical lines
        vertical_lines = []
        for x in range(edges.shape[1]):
            line_start = None
            for y in range(edges.shape[0]):
                if edges[y, x] > 0:
                    if line_start is None:
                        line_start = y
                elif line_start is not None:
                    length = y - line_start
                    if length > 50:  # Reduced minimum length
                        vertical_lines.append((x, line_start, y, length))
                    line_start = None
                    
        # Sort by length
        vertical_lines.sort(key=lambda x: x[3], reverse=True)
        
        if len(vertical_lines) < 3:  # Need at least 3 vertical lines
            return None
            
        # Find window bounds
        try:
            top = min(l[0] for l in horizontal_lines[:2])  # Use top 2 horizontal lines
            bottom = max(l[0] for l in horizontal_lines[:5])  # Use top 5 for bottom
            left = min(l[0] for l in vertical_lines[:3])  # Use leftmost 3 vertical lines
            right = max(l[0] for l in vertical_lines[:3])  # Use rightmost 3 vertical lines
            
            # Validate bounds
            if right <= left or bottom <= top:
                return None
                
            return {
                'x': left,
                'y': top,
                'width': right - left,
                'height': bottom - top,
                'monitor_relative_x': left,
                'monitor_relative_y': top
            }
        except Exception:
            return None 