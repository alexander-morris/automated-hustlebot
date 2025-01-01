import mss
import numpy as np
from PIL import Image
import cv2

def find_longest_edges(img, min_length=500):
    """Find longest horizontal and vertical edges in the image."""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    
    # Get edges
    edges = cv2.Canny(gray, 50, 150)
    
    # Save edge detection for debugging
    cv2.imwrite("debug_edges.png", edges)
    print("\nSaved edge detection to debug_edges.png")
    
    height, width = edges.shape
    
    # Find horizontal edges
    horizontal_edges = []
    for y in range(height):
        edge_start = None
        for x in range(width):
            if edges[y, x] > 0:  # Found edge pixel
                if edge_start is None:
                    edge_start = x
            elif edge_start is not None:  # End of edge
                length = x - edge_start
                if length >= min_length:
                    horizontal_edges.append({
                        'y': y,
                        'x_start': edge_start,
                        'length': length
                    })
                edge_start = None
        # Check for edge that goes to screen boundary
        if edge_start is not None:
            length = width - edge_start
            if length >= min_length:
                horizontal_edges.append({
                    'y': y,
                    'x_start': edge_start,
                    'length': length
                })
    
    # Find vertical edges
    vertical_edges = []
    for x in range(width):
        edge_start = None
        for y in range(height):
            if edges[y, x] > 0:  # Found edge pixel
                if edge_start is None:
                    edge_start = y
            elif edge_start is not None:  # End of edge
                length = y - edge_start
                if length >= min_length:
                    vertical_edges.append({
                        'x': x,
                        'y_start': edge_start,
                        'length': length
                    })
                edge_start = None
        # Check for edge that goes to screen boundary
        if edge_start is not None:
            length = height - edge_start
            if length >= min_length:
                vertical_edges.append({
                    'x': x,
                    'y_start': edge_start,
                    'length': length
                })
    
    # Sort by length
    horizontal_edges.sort(key=lambda e: e['length'], reverse=True)
    vertical_edges.sort(key=lambda e: e['length'], reverse=True)
    
    return horizontal_edges, vertical_edges

def find_window_bounds():
    print("\n=== Finding Cursor Window Bounds ===")
    
    with mss.mss() as sct:
        # We know it's monitor 3
        monitor = sct.monitors[3]
        print(f"\nMonitor info:")
        print(f"  Size: {monitor['width']}x{monitor['height']}")
        print(f"  Position: ({monitor['left']}, {monitor['top']})")
        
        # Capture the entire monitor
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        
        # Save full screenshot for debugging
        Image.fromarray(img).save("debug_full.png")
        print("\nSaved full screenshot to debug_full.png")
        
        # Find longest edges
        horizontal_edges, vertical_edges = find_longest_edges(img)
        
        print("\nLongest horizontal edges:")
        for i, edge in enumerate(horizontal_edges[:5]):
            print(f"Edge {i+1}: y={edge['y']}, x={edge['x_start']}-{edge['x_start'] + edge['length']} (length={edge['length']})")
            
        print("\nLongest vertical edges:")
        for i, edge in enumerate(vertical_edges[:5]):
            print(f"Edge {i+1}: x={edge['x']}, y={edge['y_start']}-{edge['y_start'] + edge['length']} (length={edge['length']})")
        
        # Create visualization
        vis_img = img.copy()
        
        # Draw top 5 horizontal edges in blue
        for edge in horizontal_edges[:5]:
            y = edge['y']
            x_start = edge['x_start']
            length = edge['length']
            vis_img[y, x_start:x_start + length] = [255, 0, 0, 255]
        
        # Draw top 5 vertical edges in green
        for edge in vertical_edges[:5]:
            x = edge['x']
            y_start = edge['y_start']
            length = edge['length']
            vis_img[y_start:y_start + length, x] = [0, 255, 0, 255]
        
        # Save visualization
        Image.fromarray(vis_img).save("debug_longest_edges.png")
        print("\nSaved edge visualization to debug_longest_edges.png")
        
        # Try to find window bounds from longest edges
        if horizontal_edges and vertical_edges:
            # Get longest horizontal and vertical edges
            top_edge = horizontal_edges[0]
            
            # Find bottom edge (should be near bottom of screen)
            bottom_edge = None
            for edge in horizontal_edges:
                if edge['y'] > monitor['height'] - 100:  # Within 100px of bottom
                    bottom_edge = edge
                    break
            
            # Find left and right edges (should be near screen edges)
            left_edge = None
            right_edge = None
            for edge in vertical_edges:
                if edge['x'] < 100:  # Within 100px of left edge
                    left_edge = edge
                elif edge['x'] > monitor['width'] - 100:  # Within 100px of right edge
                    right_edge = edge
            
            if bottom_edge and (left_edge or right_edge):
                # Use screen edges if we're missing a vertical edge
                x = left_edge['x'] if left_edge else 0
                width = (right_edge['x'] - x) if right_edge else (monitor['width'] - x)
                
                window_bounds = {
                    'x': x,
                    'y': top_edge['y'],
                    'width': width,
                    'height': bottom_edge['y'] - top_edge['y']
                }
                
                print("\nFound window bounds:")
                print(f"  Position: ({window_bounds['x']}, {window_bounds['y']})")
                print(f"  Size: {window_bounds['width']}x{window_bounds['height']}")
                print(f"  Monitor-relative position: ({window_bounds['x'] + monitor['left']}, {window_bounds['y'] + monitor['top']})")
                
                # Draw rectangle around window
                cv2.rectangle(vis_img, 
                            (window_bounds['x'], window_bounds['y']), 
                            (window_bounds['x'] + window_bounds['width'], window_bounds['y'] + window_bounds['height']), 
                            (255, 255, 0, 255), 2)
                Image.fromarray(vis_img).save("debug_window.png")
                print("\nSaved window bounds visualization to debug_window.png")
                
                return window_bounds
        
        print("\nCould not find window bounds!")
        return None

if __name__ == "__main__":
    try:
        bounds = find_window_bounds()
        if bounds:
            print("\nSuccess! Window bounds found.")
        else:
            print("\nFailed to find window bounds.")
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc() 