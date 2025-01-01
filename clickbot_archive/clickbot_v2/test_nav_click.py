import cv2
import numpy as np
import pyautogui
import pytesseract
from PIL import Image
import time
import mss
import json
import sys
import os
from monitor_mapper import MonitorMapper

def check_permissions():
    """Check if we have necessary permissions and guide the user"""
    while True:
        print("\nChecking permissions...")
        
        # Check AppleScript permissions first
        try:
            print("\nTesting AppleScript permissions...")
            test_script = '''
            tell application "System Events"
                return "ok"
            end tell
            '''
            result = os.popen(f"osascript -e '{test_script}'").read().strip()
            if result == "ok":
                print("✓ AppleScript control permission granted")
            else:
                raise Exception("AppleScript test failed")
        except Exception as e:
            print("\n❌ AppleScript control permission denied!")
            print("\nThis script needs permission to control your system using AppleScript.")
            print("\nPlease follow these steps:")
            print("1. Open System Preferences")
            print("2. Go to Security & Privacy > Privacy > Accessibility")
            print("3. Look for the permission request popup")
            print("4. Click 'OK' on the popup")
            print("5. Check the box next to 'Terminal.app'")
            print("\nWaiting 15 seconds for you to grant permission...")
            time.sleep(15)
            input("\nPress Enter if you've granted permission, or Ctrl+C to exit...")
            continue
        
        try:
            print("\nTesting mouse control permissions...")
            # Try to get current mouse position to test accessibility
            x, y = pyautogui.position()
            print("✓ Mouse control permission granted")
        except Exception as e:
            print("\n❌ Mouse control permission denied!")
            print("\nThis script needs permission to control your mouse.")
            print("\nPlease follow these steps:")
            print("1. Look for the permission request popup")
            print("2. Click 'OK' on the popup")
            print("3. Check the box next to 'Terminal.app' in Security & Privacy")
            print("\nWaiting 15 seconds for you to grant permission...")
            time.sleep(15)
            input("\nPress Enter if you've granted permission, or Ctrl+C to exit...")
            continue
        
        try:
            print("\nTesting screen recording permissions...")
            # Try to take a screenshot to test screen recording
            with mss.mss() as sct:
                sct.shot()
            print("✓ Screen recording permission granted")
            break  # All permissions granted, exit loop
        except Exception as e:
            print("\n❌ Screen recording permission denied!")
            print("\nThis script needs permission to capture screen content.")
            print("\nPlease follow these steps:")
            print("1. Look for the permission request popup")
            print("2. Click 'OK' on the popup")
            print("3. Check the box next to 'Terminal.app' in Screen Recording")
            print("4. You MUST quit Terminal completely after granting this permission")
            print("\nAfter clicking OK:")
            print("1. Quit Terminal (Cmd+Q)")
            print("2. Wait a few seconds")
            print("3. Reopen Terminal")
            print("4. Run this script again")
            print("\nWaiting 15 seconds for you to grant permission...")
            time.sleep(15)
            input("\nPress Enter if you've granted permission, or Ctrl+C to exit...")
            continue
    
    print("\n✨ All permissions granted! Starting in 3 seconds...")
    time.sleep(3)
    return True

class NavBarClickTest:
    def __init__(self):
        self.monitor_mapper = MonitorMapper()
        self.sct = mss.mss()
        # Fail-safe enabled by default
        pyautogui.FAILSAFE = True
        # Slightly slower movements
        pyautogui.PAUSE = 0.5
    
    def try_click(self, x, y):
        """Try clicking at absolute coordinates"""
        try:
            print(f"\nMoving to ({x}, {y})...")
            
            # Force move to coordinates (this should work even with multiple monitors)
            pyautogui.moveTo(x, y, duration=1.0, _pause=False)
            time.sleep(0.5)
            
            # Get position after move
            current_x, current_y = pyautogui.position()
            print(f"Current position: ({current_x}, {current_y})")
            
            # Click
            print("Clicking...")
            pyautogui.click(x, y, _pause=False)
            return True
            
        except Exception as e:
            print(f"Error during click: {str(e)}")
            return False
    
    def try_click_applescript(self, x, y):
        """Try clicking using AppleScript"""
        try:
            print(f"\nTrying AppleScript click at ({x}, {y})...")
            
            # Create AppleScript command with debugging
            script = f'''
            tell application "System Events"
                -- Get frontmost application
                set frontApp to first application process whose frontmost is true
                log "Clicking in " & name of frontApp
                
                -- Get menu bar
                set menuBar to menu bar 1 of frontApp
                log "Found menu bar: " & menuBar
                
                -- Click at coordinates
                set mouseLocation to {{{x}, {y}}}
                click at mouseLocation
                
                -- Try to get menu item at click location
                delay 0.5
                try
                    set clickedMenu to menu 1 of menuBar
                    log "Clicked menu: " & clickedMenu
                end try
            end tell
            '''
            
            # Run AppleScript
            os.system(f"osascript -e '{script}'")
            return True
            
        except Exception as e:
            print(f"Error during AppleScript click: {str(e)}")
            return False
    
    def try_click_menu(self, menu_name):
        """Try clicking a menu item by name using AppleScript"""
        try:
            print(f"\nTrying to click menu '{menu_name}'...")
            
            # Create AppleScript command to click menu by name
            script = f'''
            tell application "System Events"
                tell process "Cursor"
                    tell menu bar 1
                        -- Try different ways to click the menu
                        try
                            click menu bar item "{menu_name}"
                            log "Clicked using menu bar item"
                            return "clicked"
                        end try
                        
                        try
                            click (first menu bar item whose name contains "{menu_name}")
                            log "Clicked using name contains"
                            return "clicked"
                        end try
                        
                        try
                            set menuItems to name of every menu bar item
                            log "Available menus: " & menuItems
                        end try
                    end tell
                end tell
            end tell
            '''
            
            # Run AppleScript and capture output
            result = os.popen(f"osascript -e '{script}'").read().strip()
            print(f"AppleScript result: {result}")
            
            return "clicked" in result.lower()
            
        except Exception as e:
            print(f"Error clicking menu: {str(e)}")
            return False
    
    def run_test(self):
        try:
            print("\nTrying to click menus by name...")
            
            # Try clicking different menu items
            menus = [
                "Cursor",  # Try app name menu first
                "File",
                "Edit",
                "View",
                "Window",
                "Help"
            ]
            
            for menu in menus:
                print(f"\nTrying menu '{menu}'...")
                if self.try_click_menu(menu):
                    print("Click attempt completed")
                    time.sleep(1.5)  # Wait to see menu
                else:
                    print("Click attempt failed")
                
        except Exception as e:
            print(f"Error during test: {str(e)}")
            return False

if __name__ == "__main__":
    # Check permissions first
    if not check_permissions():
        print("\nPlease grant the necessary permissions and try again.")
        sys.exit(1)
    
    print("\nPermissions granted, starting test...")
    test = NavBarClickTest()
    test.run_test() 