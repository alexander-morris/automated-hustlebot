#!/usr/bin/env python3
import pyautogui
import time
import json
import os
import mss
import numpy as np
import logging
from mss import tools

logging.basicConfig(
    filename='button_finder.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ButtonFinder:
    def __init__(self):
        self.sct = mss.mss()
        # Calibrate colors for Cursor buttons
        self.buttons = {
            'accept': {
                'color': [
                    (0, 122, 255),  # iOS blue
                    (88, 166, 255),  # Light blue
                    (58, 139, 255),  # Medium blue
                ],
                'text': 'Accept',
                'min_width': 50,
                'min_height': 20
            },
            'run': {
                'color': [
                    (40, 167, 69),  # Bootstrap success green
                    (0, 184, 148),  # Teal green
                    (34, 197, 94),  # Tailwind green
                ],
                'text': '▶',
                'min_width': 20,
                'min_height': 20
            }
        }
        self.last_found = {}  # Cache last found positions
        
    def find_button(self, button_type):
        """Find a specific button on screen"""
        screen = self.sct.grab(self.sct.monitors[0])
        button_data = self.buttons[button_type]
        
        # Save screenshot for debugging
        tools.to_png(screen.rgb, screen.size, output=f'debug_{button_type}.png')
        
        img = np.array(screen)
        
        # Try each color variation
        for color in button_data['color']:
            matches = np.where(
                (abs(img[:, :, 0] - color[0]) <= 10) &
                (abs(img[:, :, 1] - color[1]) <= 10) &
                (abs(img[:, :, 2] - color[2]) <= 10)
            )
            
            if len(matches[0]) > 0:
                # Group matches into potential buttons
                points = list(zip(matches[1], matches[0]))  # x, y coordinates
                buttons = self._group_points(points, button_data['min_width'], button_data['min_height'])
                
                if buttons:
                    # Use the largest group of points (most likely the button)
                    button = max(buttons, key=len)
                    x = sum(p[0] for p in button) // len(button)
                    y = sum(p[1] for p in button) // len(button)
                    
                    logging.debug(f"Found {button_type} button at {x}, {y} with color {color}")
                    self.last_found[button_type] = (x, y)
                    return (x, y)
        
        # If not found, try last known position
        if button_type in self.last_found:
            logging.debug(f"Using last known position for {button_type}: {self.last_found[button_type]}")
            return self.last_found[button_type]
            
        return None

    def _group_points(self, points, min_width, min_height):
        """Group nearby points into potential buttons"""
        buttons = []
        used = set()
        
        for x, y in points:
            if (x, y) in used:
                continue
                
            # Find all points within button dimensions
            button = [(x, y)]
            used.add((x, y))
            
            for x2, y2 in points:
                if (x2, y2) not in used and \
                   abs(x2 - x) <= min_width and \
                   abs(y2 - y) <= min_height:
                    button.append((x2, y2))
                    used.add((x2, y2))
            
            if len(button) >= 5:  # Minimum points to consider it a button
                buttons.append(button)
        
        return buttons

    def click_button(self, button_type):
        """Find and click a specific button"""
        coords = self.find_button(button_type)
        if coords:
            x, y = coords
            try:
                current_x, current_y = pyautogui.position()
                
                # Move to button position
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.1)
                
                # Click and verify
                pyautogui.click()
                time.sleep(0.1)
                
                # Move back
                pyautogui.moveTo(current_x, current_y, duration=0.2)
                
                logging.info(f"Clicked {button_type} button at {x}, {y}")
                return True
            except Exception as e:
                logging.error(f"Click failed: {str(e)}")
                return False
                
        logging.warning(f"Could not find {button_type} button")
        return False

    def __del__(self):
        self.sct.close() 