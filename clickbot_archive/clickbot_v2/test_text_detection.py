#!/usr/bin/env python3
import mss
import numpy as np
from PIL import Image
import pytesseract
import time

def test_menubar_text():
    print("🔍 Testing text detection in Mac menu bar across all monitors...")
    
    # Initialize screen capture
    sct = mss.mss()
    
    # Print monitor information
    print("\n📺 Monitor Information:")
    for i, monitor in enumerate(sct.monitors):
        print(f"Monitor {i}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
    
    # Test each monitor
    for monitor_idx, monitor in enumerate(sct.monitors):
        print(f"\n🖥️  Testing Monitor {monitor_idx}...")
        
        # Menu bar area coordinates (relative to this monitor)
        area = {
            "left": monitor["left"],
            "top": monitor["top"],
            "width": 800,
            "height": 25
        }
        
        print(f"📏 Capturing menu bar area: {area['width']}x{area['height']} at ({area['left']}, {area['top']})")
        
        # Capture the area
        screenshot = sct.grab(area)
        
        # Convert to PIL Image and save original
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        debug_orig = f'menubar_orig_monitor{monitor_idx}_{int(time.time())}.png'
        img.save(debug_orig)
        print(f"💾 Saved original: {debug_orig}")
        
        # Convert to numpy and process
        img_array = np.array(img)
        
        # Try different thresholds
        thresholds = [30, 40, 50]  # Focus on lower thresholds for menu text
        
        for threshold in thresholds:
            print(f"\n🔍 Testing threshold: {threshold}")
            
            # Try both dark text on light background and light text on dark background
            for inverted in [False, True]:
                # Create mask for text
                if inverted:
                    text_mask = np.all((img_array >= [255-threshold, 255-threshold, 255-threshold]), axis=2)
                    mode = "inverted"
                else:
                    text_mask = np.all((img_array <= [threshold, threshold, threshold]), axis=2)
                    mode = "normal"
                
                # Create white text on black background
                result = np.zeros_like(img_array)
                result[text_mask] = [255, 255, 255]
                
                # Save processed image
                debug_path = f'menubar_{mode}_threshold_{threshold}_monitor{monitor_idx}_{int(time.time())}.png'
                Image.fromarray(result).save(debug_path)
                print(f"💾 Saved {mode}: {debug_path}")
                
                # Scale up image for better OCR
                result_pil = Image.fromarray(result)
                result_pil = result_pil.resize((result_pil.width * 2, result_pil.height * 2))
                
                # Try OCR with different modes
                for psm in [7, 6]:  # Focus on line and uniform block modes
                    custom_config = f'--psm {psm}'
                    text = pytesseract.image_to_string(
                        result_pil,
                        config=custom_config
                    ).strip()
                    
                    if text:
                        print(f"✨ Found text ({mode}, psm={psm}): '{text}'")
                        # If we found menu-like text, highlight this monitor
                        if any(word.lower() in text.lower() for word in ['file', 'edit', 'view', 'window', 'help']):
                            print(f"🎯 Found menu text on Monitor {monitor_idx}!")
                    else:
                        print(f"❌ No text found ({mode}, psm={psm})")

if __name__ == "__main__":
    test_menubar_text() 