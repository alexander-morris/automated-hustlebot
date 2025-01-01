import cv2
import numpy as np
import pytesseract
from PIL import Image

def try_ocr_with_settings(image, scale_factor, threshold_value=200):
    """Try OCR with different settings and print results"""
    print(f"\nTrying with scale_factor={scale_factor}, threshold={threshold_value}")
    
    # Resize image
    scaled = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    
    # Convert to grayscale if needed
    if len(scaled.shape) == 3:
        scaled = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    
    # Add padding before processing
    pad_x = 20 * scale_factor
    pad_y = 10 * scale_factor
    padded = cv2.copyMakeBorder(scaled, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=255)
    
    # Try different preprocessing techniques
    
    # 1. Simple threshold with padding
    _, binary = cv2.threshold(padded, threshold_value, 255, cv2.THRESH_BINARY)
    cv2.imwrite(f'ocr_debug_binary_{scale_factor}x.png', binary)
    result = pytesseract.image_to_string(
        binary,
        config='--psm 7 --oem 1 -c tessedit_char_whitelist=ACEPTacept'
    ).strip().lower()
    print(f"Simple threshold result: '{result}'")
    
    # 2. Adaptive threshold with padding
    adaptive = cv2.adaptiveThreshold(padded, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    cv2.imwrite(f'ocr_debug_adaptive_{scale_factor}x.png', adaptive)
    result = pytesseract.image_to_string(
        adaptive,
        config='--psm 7 --oem 1 -c tessedit_char_whitelist=ACEPTacept'
    ).strip().lower()
    print(f"Adaptive threshold result: '{result}'")
    
    # 3. With extra contrast and sharpening
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(padded, -1, kernel)
    contrast = cv2.normalize(sharpened, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    _, contrast_binary = cv2.threshold(contrast, threshold_value, 255, cv2.THRESH_BINARY)
    cv2.imwrite(f'ocr_debug_contrast_{scale_factor}x.png', contrast_binary)
    result = pytesseract.image_to_string(
        contrast_binary,
        config='--psm 7 --oem 1 -c tessedit_char_whitelist=ACEPTacept'
    ).strip().lower()
    print(f"Contrast enhanced result: '{result}'")

def main():
    # Load the image
    image_path = 'debug_merged_region_1735676509450_1.png'
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return
    
    print(f"Original image size: {image.shape}")
    
    # Try different scale factors
    for scale in [8, 12, 16, 20]:
        # Try different threshold values
        for threshold in [180, 200, 220]:
            try_ocr_with_settings(image, scale, threshold)

if __name__ == "__main__":
    main() 