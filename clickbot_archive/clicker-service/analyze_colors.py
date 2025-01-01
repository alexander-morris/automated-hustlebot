#!/usr/bin/env python3
import cv2
import numpy as np
from collections import Counter
import os

def analyze_image(image_path):
    print(f"Analyzing image: {image_path}")
    
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Failed to read image: {image_path}")
        return
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    height, width = img.shape[:2]
    
    # Focus on bottom third
    start_y = height * 2 // 3
    end_y = height
    
    print(f"\nAnalyzing bottom third (y={start_y} to {end_y}):")
    
    # Get region
    region = img[start_y:end_y, :]
    
    # Analyze colors
    colors = region.reshape(-1, 3)
    color_counts = Counter(map(tuple, colors))
    
    # Get top 20 most common colors
    print("\nTop 20 most common colors:")
    for color, count in color_counts.most_common(20):
        r, g, b = color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        print(f"RGB({r},{g},{b}) {hex_color} - {count} pixels")
    
    # Analyze horizontal runs
    print("\nAnalyzing horizontal color runs:")
    run_lengths = []
    for y in range(region.shape[0]):
        current_color = None
        current_run = 0
        for x in range(region.shape[1]):
            pixel = tuple(region[y, x])
            if pixel == current_color:
                current_run += 1
            else:
                if current_run > 0:
                    run_lengths.append((current_color, current_run))
                current_color = pixel
                current_run = 1
        if current_run > 0:
            run_lengths.append((current_color, current_run))
    
    # Get statistics on run lengths
    if run_lengths:
        print("\nRun length statistics:")
        run_length_counts = Counter(length for _, length in run_lengths)
        for length, count in sorted(run_length_counts.most_common(10)):
            print(f"Length {length}: {count} occurrences")
        
        print("\nLongest runs by color:")
        color_max_runs = {}
        for color, length in run_lengths:
            if color not in color_max_runs or length > color_max_runs[color]:
                color_max_runs[color] = length
        
        for color, max_length in sorted(color_max_runs.items(), key=lambda x: x[1], reverse=True)[:10]:
            r, g, b = color
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            print(f"RGB({r},{g},{b}) {hex_color} - max run: {max_length} pixels")
    
    # Analyze color transitions
    print("\nAnalyzing vertical color transitions:")
    for x in range(0, width, width//10):  # Sample every 10% of width
        prev_color = None
        transitions = []
        for y in range(region.shape[0]):
            color = tuple(region[y, x])
            if prev_color is not None:
                diff = np.abs(np.array(color) - np.array(prev_color))
                if np.any(diff > 20):  # Significant color change
                    hex_from = f"#{prev_color[0]:02x}{prev_color[1]:02x}{prev_color[2]:02x}"
                    hex_to = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    transitions.append((prev_color, color, hex_from, hex_to))
            prev_color = color
        
        if transitions:
            print(f"\nAt x={x}:")
            for from_color, to_color, hex_from, hex_to in transitions[:3]:
                print(f"  {from_color} ({hex_from}) -> {to_color} ({hex_to})")

def main():
    # Find the most recent debug image for monitor 2
    debug_dir = "debug_images"
    if not os.path.exists(debug_dir):
        print(f"Debug directory not found: {debug_dir}")
        return
        
    monitor_2_images = [f for f in os.listdir(debug_dir) if f.startswith("debug_monitor_2_")]
    if not monitor_2_images:
        print("No debug images found for monitor 2")
        return
        
    latest_image = sorted(monitor_2_images)[-1]
    image_path = os.path.join(debug_dir, latest_image)
    
    analyze_image(image_path)

if __name__ == "__main__":
    main() 