from PIL import Image
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

def analyze_image(image_path):
    """Analyze the image for color patterns"""
    # Load image
    img = Image.open(image_path)
    img_array = np.array(img)
    
    height, width = img_array.shape[:2]
    
    # Analyze bottom third
    bottom_third_start = height * 2 // 3
    bottom_section = img_array[bottom_third_start:, :]
    
    # Get unique colors and their counts
    colors = bottom_section.reshape(-1, 3)
    unique_colors, counts = np.unique(colors, axis=0, return_counts=True)
    
    # Sort by frequency
    sorted_indices = np.argsort(-counts)
    top_colors = unique_colors[sorted_indices[:10]]
    top_counts = counts[sorted_indices[:10]]
    
    logging.info("\nMost common colors in bottom third:")
    for color, count in zip(top_colors, top_counts):
        hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
        logging.info(f"RGB{tuple(color)} ({hex_color}) - {count} pixels")
    
    # Look for horizontal runs
    y_samples = np.linspace(bottom_third_start, height-1, 20, dtype=int)
    x_samples = np.linspace(0, width-1, 100, dtype=int)
    
    logging.info("\nAnalyzing horizontal color runs:")
    for y in y_samples[:5]:  # Just look at first few rows
        current_run = {'color': None, 'length': 0, 'start_x': 0}
        runs = []
        
        for x_idx, x in enumerate(x_samples):
            pixel = img_array[y, x]
            
            if current_run['color'] is None:
                current_run = {'color': tuple(pixel), 'length': 1, 'start_x': x}
            elif np.all(np.abs(pixel - current_run['color']) < 5):
                current_run['length'] += 1
            else:
                if current_run['length'] > 5:
                    runs.append(current_run)
                current_run = {'color': tuple(pixel), 'length': 1, 'start_x': x}
        
        if current_run['length'] > 5:
            runs.append(current_run)
        
        if runs:
            logging.info(f"\nRow {y}:")
            for run in runs:
                color = run['color']
                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                logging.info(f"  Run of {run['length']} pixels at x={run['start_x']}: RGB{color} ({hex_color})")

if __name__ == '__main__':
    analyze_image('debug_images/debug_monitor_2_092810.png') 