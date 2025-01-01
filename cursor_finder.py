import mss
import numpy as np
from PIL import Image
import pyautogui
import time
from datetime import datetime
import sys
import os

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

def log(message):
    """Print message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    message = f"[{timestamp}] {message}"
    try:
        print(message, file=sys.stderr, flush=True)
    except:
        try:
            sys.stderr.write(message + "\n")
            sys.stderr.flush()
        except:
            try:
                sys.stdout.write(message + "\n")
                sys.stdout.flush()
            except:
                pass  # Give up if all output methods fail

def check_permissions():
    """Check if we have necessary permissions"""
    print("Checking permissions...", flush=True)
    try:
        # Test mouse control
        print("Testing mouse control...", flush=True)
        original_x, original_y = pyautogui.position()
        print(f"Current mouse position: ({original_x}, {original_y})", flush=True)
        pyautogui.moveTo(original_x, original_y)
        print("✓ Mouse control permission granted", flush=True)
        
        # Test screen capture
        print("Testing screen recording...", flush=True)
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # Get primary monitor
            print(f"Found monitor: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})", flush=True)
            screenshot = sct.grab(monitor)
            print(f"Captured screenshot: {screenshot.width}x{screenshot.height}", flush=True)
        print("✓ Screen recording permission granted", flush=True)
        print("✨ All permissions granted!", flush=True)
        return True
        
    except Exception as e:
        print(f"Error details: {str(e)}", flush=True)
        if "not been enabled" in str(e):
            print("❌ Mouse control permission denied!", flush=True)
            print("Please grant mouse control permission in System Settings > Privacy & Security > Accessibility", flush=True)
            print("Then run the script again", flush=True)
        elif "not been allowed" in str(e):
            print("❌ Screen recording permission denied!", flush=True)
            print("Please grant screen recording permission in System Settings > Privacy & Security > Screen Recording", flush=True)
            print("Then run the script again", flush=True)
        else:
            print(f"❌ Error checking permissions: {str(e)}", flush=True)
        return False

class CursorFinder:
    def __init__(self):
        self.sct = mss.mss()
        self.cursor_monitor = None
        # Speed up mouse movement
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0
        pyautogui.PAUSE = 0
        
    def log(self, message):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}", flush=True)
        
    def find_cursor_window(self):
        """Find monitor with Cursor window"""
        try:
            self.log("\n=== Stage 1: Finding Cursor Window ===")
            self.log("Listing all monitors:")
            # Skip first monitor (represents all monitors combined)
            for i, monitor in enumerate(self.sct.monitors[1:], 1):
                self.log(f"Monitor {i}:")
                self.log(f"  Size: {monitor['width']}x{monitor['height']}")
                self.log(f"  Position: ({monitor['left']}, {monitor['top']})")
                self.log(f"  Bounds: ({monitor['left']}, {monitor['top']}) to ({monitor['left'] + monitor['width']}, {monitor['top'] + monitor['height']})")
                
                # Capture full monitor
                screenshot = self.sct.grab(monitor)
                img_array = np.array(screenshot)
                
                # Convert BGRA to RGB
                img_array = img_array[:, :, [2,1,0]]
                
                # Look for dark theme UI colors (background should be dark)
                dark_mask = np.all(img_array <= [30, 30, 30], axis=2)
                dark_pixel_ratio = np.sum(dark_mask) / (monitor['width'] * monitor['height'])
                self.log(f"  Dark pixel ratio: {dark_pixel_ratio:.2%}")
                
                # If more than 40% dark pixels, likely the Cursor window
                if dark_pixel_ratio > 0.4:
                    self.log("\n✓ Found Cursor window!")
                    self.log(f"  Monitor: {i}")
                    self.log(f"  Window size: {monitor['width']}x{monitor['height']}")
                    self.log(f"  Window position: ({monitor['left']}, {monitor['top']})")
                    self.log(f"  Window bounds: ({monitor['left']}, {monitor['top']}) to ({monitor['left'] + monitor['width']}, {monitor['top'] + monitor['height']})")
                    self.cursor_monitor = monitor
                    return monitor
            
            self.log("\n❌ Could not find Cursor window on any monitor")
            return None
            
        except Exception as e:
            self.log(f"\n❌ Error scanning monitors: {str(e)}")
            return None
            
    def find_pink_line(self):
        """Find pink line in top portion of window"""
        try:
            self.log("\n=== Stage 2: Finding Pink Line ===")
            
            # Scan top 100 pixels of window
            top_region = {
                'left': self.cursor_monitor['left'],
                'top': self.cursor_monitor['top'],
                'width': self.cursor_monitor['width'],
                'height': 100
            }
            
            self.log("Scanning top region of window:")
            self.log(f"  Size: {top_region['width']}x{top_region['height']}")
            self.log(f"  Position: ({top_region['left']}, {top_region['top']})")
            self.log(f"  Bounds: ({top_region['left']}, {top_region['top']}) to ({top_region['left'] + top_region['width']}, {top_region['top'] + top_region['height']})")
            
            # Capture region
            screenshot = self.sct.grab(top_region)
            img_array = np.array(screenshot)
            
            # Debug color info
            self.log("\nImage Analysis:")
            self.log(f"  Shape: {img_array.shape}")
            self.log(f"  Data type: {img_array.dtype}")
            self.log(f"  Memory layout: {img_array.flags}")
            
            # Save raw screenshot data
            np.save("debug_raw_screenshot.npy", img_array)
            self.log("\nSaved raw screenshot data to debug_raw_screenshot.npy")
            
            # Analyze each channel
            self.log("\nChannel Analysis (BGRA format):")
            channel_names = ['Blue', 'Green', 'Red', 'Alpha']
            for i, name in enumerate(channel_names):
                channel = img_array[:, :, i]
                self.log(f"\n{name} Channel:")
                self.log(f"  Range: {np.min(channel)} to {np.max(channel)}")
                self.log(f"  Mean: {np.mean(channel):.2f}")
                self.log(f"  Std dev: {np.std(channel):.2f}")
                unique_vals = np.unique(channel)
                self.log(f"  Unique values: {len(unique_vals)} values")
                self.log(f"  Most common values: {np.bincount(channel.flatten()).argsort()[-5:][::-1]}")
            
            # Find potential pink pixels (very loose thresholds)
            self.log("\nSearching for pink-ish pixels:")
            # Look for any pixels where red > green and red > blue
            potential_pink = (img_array[:, :, 2] > img_array[:, :, 1]) & (img_array[:, :, 2] > img_array[:, :, 0])
            pink_count = np.sum(potential_pink)
            self.log(f"Found {pink_count} pixels where red is dominant")
            
            if pink_count > 0:
                # Analyze these pixels
                pink_y, pink_x = np.where(potential_pink)
                self.log("\nAnalyzing pixels where red is dominant:")
                self.log(f"Found pixels at {len(pink_y)} positions")
                
                # Group by y-coordinate to find horizontal lines
                y_counts = np.bincount(pink_y)
                lines = np.where(y_counts >= 10)[0]  # Lines with at least 10 pink pixels
                self.log(f"\nFound {len(lines)} rows with 10+ red-dominant pixels:")
                
                for y in lines:
                    x_coords = pink_x[pink_y == y]
                    self.log(f"\nRow {y}:")
                    self.log(f"  {len(x_coords)} pixels")
                    self.log(f"  X range: {np.min(x_coords)} to {np.max(x_coords)}")
                    # Sample some colors from this line
                    for x in x_coords[:5]:  # Show first 5 pixels
                        color = img_array[y, x]
                        self.log(f"  Color at ({x}, {y}): BGRA = {color}")
            
            # Save visualization
            vis_img = img_array.copy()
            vis_img[potential_pink] = [0, 255, 0, 255]  # Mark potential pink pixels in green
            Image.fromarray(vis_img).save("debug_pink_pixels.png")
            self.log("\nSaved visualization to debug_pink_pixels.png")
            
            # Now try our original pink detection
            pink_mask = (
                (img_array[:, :, 2] >= 200) & (img_array[:, :, 2] <= 255) &  # R: High
                (img_array[:, :, 1] >= 80) & (img_array[:, :, 1] <= 160) &   # G: Medium
                (img_array[:, :, 0] >= 150) & (img_array[:, :, 0] <= 220)    # B: Medium-high
            )
            
            pink_pixels = np.where(pink_mask)
            pink_count = len(pink_pixels[0])
            
            self.log(f"\nFound {pink_count} pixels matching our pink threshold")
            
            if pink_count == 0:
                self.log("❌ No pink pixels found matching our threshold")
                return None
                
            # Find rightmost pink line
            min_x = np.min(pink_pixels[1])
            max_x = np.max(pink_pixels[1])
            min_y = np.min(pink_pixels[0])
            max_y = np.max(pink_pixels[0])
            
            self.log("\n✓ Found pink line!")
            self.log(f"  Width: {max_x - min_x + 1} pixels")
            self.log(f"  Height: {max_y - min_y + 1} pixels")
            self.log(f"  Window-relative position: ({min_x}, {min_y}) to ({max_x}, {max_y})")
            
            return {
                'min_x': min_x + self.cursor_monitor['left'],
                'max_x': max_x + self.cursor_monitor['left'],
                'min_y': min_y + self.cursor_monitor['top'],
                'max_y': max_y + self.cursor_monitor['top'],
                'width': max_x - min_x + 1,
                'height': max_y - min_y + 1
            }
            
        except Exception as e:
            self.log(f"\n❌ Error finding pink line: {str(e)}")
            return None

def main():
    # Print directly to make sure output is working
    print("\n=== Starting Cursor Finder Bot ===", flush=True)
    
    # Keep checking permissions until granted
    while not check_permissions():
        print("\nWaiting for permissions to be granted...", flush=True)
        time.sleep(2)
    
    finder = CursorFinder()
    
    # Stage 1: Find Cursor window
    print("\nStarting Stage 1: Find Cursor Window", flush=True)
    print("Scanning monitors...", flush=True)
    cursor_monitor = finder.find_cursor_window()
    if not cursor_monitor:
        print("\nStage 1 failed: Could not find Cursor window", flush=True)
        return
    print("\nStage 1 completed successfully!", flush=True)
    print(f"Found Cursor window on monitor:", flush=True)
    print(f"  Size: {cursor_monitor['width']}x{cursor_monitor['height']}", flush=True)
    print(f"  Position: ({cursor_monitor['left']}, {cursor_monitor['top']})", flush=True)
    print(f"  Bounds: ({cursor_monitor['left']}, {cursor_monitor['top']}) to ({cursor_monitor['left'] + cursor_monitor['width']}, {cursor_monitor['top'] + cursor_monitor['height']})", flush=True)
        
    # Stage 2: Find pink line
    print("\nStarting Stage 2: Find Pink Line", flush=True)
    print("Scanning top portion of window...", flush=True)
    pink_line = finder.find_pink_line()
    if not pink_line:
        print("\nStage 2 failed: Could not find pink line", flush=True)
        return
    print("\nStage 2 completed successfully!", flush=True)
    print(f"Found rightmost pink line:", flush=True)
    print(f"  Size: {pink_line['width']}x{pink_line['height']} pixels", flush=True)
    print(f"  Position: ({pink_line['min_x']}, {pink_line['min_y']}) to ({pink_line['max_x']}, {pink_line['max_y']})", flush=True)
    print(f"  Search area will be to the right of x={pink_line['max_x']}", flush=True)
    
    # Keep script running
    try:
        print("\nAll stages completed successfully! Press Ctrl+C to stop...", flush=True)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBot stopped", flush=True)

if __name__ == "__main__":
    # Redirect stderr to stdout
    sys.stderr = sys.stdout
    
    try:
        print("Script starting...", flush=True)
        main()
    except KeyboardInterrupt:
        print("\nBot stopped", flush=True)
    except Exception as e:
        print(f"\nError: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        
    # Make sure all output is flushed
    sys.stdout.flush()
    print("Script finished.", flush=True) 