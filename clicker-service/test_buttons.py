#!/usr/bin/env python3
from button_finder import ButtonFinder
import time
import logging
import os

# Set up logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('button_finder.log'),
        logging.StreamHandler()
    ]
)

def main():
    finder = ButtonFinder()
    
    print("\n=== Button Detection Test ===")
    print("Looking for Cursor buttons every 2 seconds")
    print("Saving debug screenshots to current directory")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            print("\nScanning screen...")
            
            # Try to find and click Accept button
            accept_coords = finder.find_button('accept')
            if accept_coords:
                print(f"Found Accept button at {accept_coords}")
                if finder.click_button('accept'):
                    print("Successfully clicked Accept button")
            else:
                print("No Accept button found")
            
            # Try to find and click Run button
            run_coords = finder.find_button('run')
            if run_coords:
                print(f"Found Run button at {run_coords}")
                if finder.click_button('run'):
                    print("Successfully clicked Run button")
            else:
                print("No Run button found")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")

if __name__ == "__main__":
    main() 