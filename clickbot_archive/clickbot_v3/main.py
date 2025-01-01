"""
Main script for Cursor accept bot
"""
import time
import sys
from cursor_monitor import CursorMonitor
from composer_detector import ComposerDetector
from accept_watcher import AcceptWatcher
from PIL import Image
import mss

def check_permissions():
    """Check required permissions"""
    # TODO: Add permission checking from v2
    return True

def main():
    print("Starting Cursor accept bot...")
    
    # Initialize components
    cursor_monitor = CursorMonitor()
    composer_detector = ComposerDetector()
    accept_watcher = AcceptWatcher()
    
    # Main loop
    while True:
        try:
            # Find Cursor window
            cursor_window = cursor_monitor.find_cursor_window()
            if not cursor_window:
                print("No Cursor window found. Retrying in 5 seconds...")
                time.sleep(5)
                continue
            
            # Get window region
            window_region = cursor_monitor.get_cursor_region()
            
            # Capture window
            with mss.mss() as sct:
                screenshot = sct.grab(window_region)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Find composer area
            composer_region = composer_detector.find_composer(img)
            if composer_region:
                x, y, w, h = composer_region
                print(f"Found composer at ({x}, {y})")
                
                # Extract composer area for accept button search
                composer_img = img.crop((x, y, x+w, y+h))
                composer_img.save('debug_composer.png')
                
                # Look for accept button in composer area
                accept_pos = accept_watcher.find_accept_button(
                    composer_img,
                    base_x=window_region['left'] + x,
                    base_y=window_region['top'] + y
                )
                
                if accept_pos:
                    accept_watcher.try_click_accept()
            
            # Short sleep to prevent high CPU usage
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(1)

if __name__ == "__main__":
    if not check_permissions():
        print("Please grant necessary permissions and try again")
        sys.exit(1)
    main() 