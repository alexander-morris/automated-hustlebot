import os
import unittest
from unittest.mock import Mock, patch
from PIL import Image
import numpy as np
from error_recovery import ErrorRecoveryHandler

class TestErrorRecoveryHandler(unittest.TestCase):
    def setUp(self):
        self.handler = ErrorRecoveryHandler(debug=True)
        
        # Create test images directory
        self.test_images_dir = os.path.join(os.path.dirname(__file__), 'test_images')
        os.makedirs(self.test_images_dir, exist_ok=True)
        
        # Create test images
        self.screen = Image.new('RGB', (800, 600), color='white')
        self.error_icon = Image.new('RGB', (32, 32), color='red')
        self.note_text = Image.new('RGB', (100, 20), color='yellow')
        self.footer = Image.new('RGB', (200, 50), color='blue')
        
        # Save test images
        self.error_icon_path = os.path.join(self.test_images_dir, 'error-icon.png')
        self.note_text_path = os.path.join(self.test_images_dir, 'note-text.png')
        self.footer_path = os.path.join(self.test_images_dir, 'agent-buttons-footer.png')
        
        self.error_icon.save(self.error_icon_path)
        self.note_text.save(self.note_text_path)
        self.footer.save(self.footer_path)

    def tearDown(self):
        # Clean up test files
        for path in [self.error_icon_path, self.note_text_path, self.footer_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_images_dir):
            os.rmdir(self.test_images_dir)

    @patch('error_recovery.ImageMatcher')
    def test_error_detection(self, mock_matcher):
        # Mock error icon detection
        mock_matcher.return_value.find_template.return_value = {
            'confidence': 0.9,
            'x': 100,
            'y': 100
        }
        
        has_error, error_type = self.handler.check_for_errors(self.screen)
        self.assertTrue(has_error)
        self.assertIsNotNone(error_type)

    @patch('error_recovery.ImageMatcher')
    def test_no_error_detection(self, mock_matcher):
        # Mock no error detection
        mock_matcher.return_value.find_template.return_value = None
        
        has_error, error_type = self.handler.check_for_errors(self.screen)
        self.assertFalse(has_error)
        self.assertIsNone(error_type)

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    def test_recovery_sequence(self, mock_press, mock_write, mock_click, mock_matcher):
        # Mock footer detection
        mock_matcher.return_value.find_template.return_value = {
            'confidence': 0.9,
            'x': 400,
            'y': 500
        }
        
        success = self.handler.perform_recovery(self.screen)
        
        self.assertTrue(success)
        mock_click.assert_called_once_with(400, 470)  # y - 30
        mock_write.assert_called_once_with('continue')
        mock_press.assert_called_once_with('enter')

    @patch('error_recovery.ImageMatcher')
    def test_recovery_target_not_found(self, mock_matcher):
        # Mock footer not found
        mock_matcher.return_value.find_template.return_value = None
        
        success = self.handler.perform_recovery(self.screen)
        self.assertFalse(success)

    @patch('error_recovery.ImageMatcher')
    @patch('pyautogui.click')
    def test_recovery_click_failure(self, mock_click, mock_matcher):
        # Mock footer detection but click failure
        mock_matcher.return_value.find_template.return_value = {
            'confidence': 0.9,
            'x': 400,
            'y': 500
        }
        mock_click.side_effect = Exception("Click failed")
        
        success = self.handler.perform_recovery(self.screen)
        self.assertFalse(success)

    def test_error_image_loading(self):
        # Test with missing images
        handler = ErrorRecoveryHandler(debug=True)
        self.assertEqual(len(handler.error_images), 0)
        self.assertIsNone(handler.recovery_image)

    @patch('error_recovery.ImageMatcher')
    def test_full_error_handling_flow(self, mock_matcher):
        # Mock error detection and recovery
        def mock_find_template(screen, template, threshold=None):
            if template == self.handler.error_images.get('error-icon.png'):
                return {'confidence': 0.9, 'x': 100, 'y': 100}
            elif template == self.handler.recovery_image:
                return {'confidence': 0.9, 'x': 400, 'y': 500}
            return None
        
        mock_matcher.return_value.find_template.side_effect = mock_find_template
        
        with patch('pyautogui.click'), patch('pyautogui.write'), patch('pyautogui.press'):
            success = self.handler.handle_error_case(self.screen)
            self.assertTrue(success)

if __name__ == '__main__':
    unittest.main() 