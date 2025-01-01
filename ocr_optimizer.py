import mss
import numpy as np
import cv2
import pytesseract
import time
from datetime import datetime

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-4]
    print(f"[{timestamp}] {message}")

def try_ocr_method(img, method_name, preprocess_func):
    """Try a specific OCR method and return results"""
    processed = preprocess_func(img)
    
    # Save debug image
    timestamp = int(time.time() * 1000)
    debug_file = f'ocr_debug_{method_name}_{timestamp}.png'
    cv2.imwrite(debug_file, processed)
    
    # Try different PSM modes
    results = []
    for psm in [7, 8, 10, 13]:  # Single line, word, character, raw line
        config = f'--psm {psm} --oem 1'
        text = pytesseract.image_to_string(processed, config=config).strip()
        if text:
            # Calculate match score
            score = 0
            target = "Accept"
            for variant in [text, text.lower(), text.upper(), text.title()]:
                temp_score = 0
                last_pos = -1
                for c in variant:
                    if last_pos + 1 < len(target) and c == target[last_pos + 1]:
                        temp_score += 1
                        last_pos += 1
                score = max(score, temp_score)
            
            results.append({
                'method': method_name,
                'psm': psm,
                'text': text,
                'score': score,
                'debug_file': debug_file
            })
    
    return results

def method1(img):
    """Basic preprocessing"""
    scale = 8
    scaled = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if len(scaled.shape) == 3:
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    else:
        gray = scaled
    return cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]

def method2(img):
    """High contrast preprocessing"""
    scale = 12
    scaled = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if len(scaled.shape) == 3:
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    else:
        gray = scaled
    # Increase contrast
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
    return cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]

def method3(img):
    """Edge enhancement preprocessing"""
    scale = 16
    scaled = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if len(scaled.shape) == 3:
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    else:
        gray = scaled
    # Sharpen
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    return cv2.threshold(sharpened, 200, 255, cv2.THRESH_BINARY)[1]

def method4(img):
    """Adaptive thresholding"""
    scale = 12
    scaled = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if len(scaled.shape) == 3:
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    else:
        gray = scaled
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

def main():
    log("Starting OCR optimization...")
    
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # Primary monitor
        
        # Calculate region to capture (right 400px around target area)
        target_x = 1439
        target_y = 356
        capture_width = 400
        capture_height = 200
        
        # Calculate bounds ensuring we don't go out of screen
        x = max(0, target_x - 100)  # Start 100px left of target
        y = max(0, target_y - 100)  # Start 100px above target
        width = min(capture_width, monitor['width'] - x)
        height = min(capture_height, monitor['height'] - y)
        
        bounds = {'left': x, 'top': y, 'width': width, 'height': height}
        log(f"Capturing region: {bounds}")
        
        # Take screenshot
        screenshot = sct.grab(bounds)
        img = np.array(screenshot)
        
        # Save original
        cv2.imwrite('original.png', img)
        
        # Try different OCR methods
        methods = [
            ('basic', method1),
            ('high_contrast', method2),
            ('edge_enhanced', method3),
            ('adaptive', method4)
        ]
        
        all_results = []
        for name, func in methods:
            results = try_ocr_method(img, name, func)
            all_results.extend(results)
            
        # Sort by score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Log results
        log("\nResults (sorted by score):")
        for r in all_results:
            log(f"Method: {r['method']}, PSM: {r['psm']}, Text: '{r['text']}', Score: {r['score']}")
            log(f"Debug file: {r['debug_file']}")
            log("---")

if __name__ == "__main__":
    main() 