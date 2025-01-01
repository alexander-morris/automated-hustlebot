"""
Test script for finding and clicking Accept button
"""
import time
from cursor_finder import CursorFinder

def main():
    finder = CursorFinder()
    
    print("Starting Accept button test...")
    
    while True:
        try:
            # Find Cursor window
            monitor = finder.find_cursor_window()
            if not monitor:
                print("No Cursor window found, retrying in 2 seconds...")
                time.sleep(2)
                continue
            
            # Find Accept button
            accept_pos = finder.find_accept_button()
            if accept_pos:
                # Try to click it
                if finder.click_position(accept_pos):
                    print("Successfully clicked Accept!")
                    time.sleep(1)  # Wait before next attempt
            else:
                print("Accept button not found, retrying...")
                time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main() 