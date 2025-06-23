"""
Test for the refactored image processing and navigation
"""
import os
import sys
import unittest
import tempfile
import shutil
import numpy as np
from unittest.mock import MagicMock, patch
import cv2

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from photodisarm.processing.image_processor import resize_image_to_fit
from photodisarm.core.image_viewer import ImageViewer


class TestImageProcessing(unittest.TestCase):
    """Test the image processing functionality"""
    
    def test_resize_with_black_bars(self):
        """Test that resize_image_to_fit properly adds black bars for aspect ratio preservation"""
        # Create a test image (wider than tall)
        test_img = np.ones((300, 600, 3), dtype=np.uint8) * 255  # White image
        
        # Resize to a more square aspect ratio
        max_width, max_height = 400, 400
        result = resize_image_to_fit(test_img, max_width, max_height)
        
        # Check dimensions
        self.assertEqual(result.shape[1], max_width)  # Width should be max
        self.assertEqual(result.shape[0], max_height)  # Height should be max
        
        # Check for black bars (should be at top and bottom)
        # Middle should be white (the original image content)
        self.assertTrue(np.all(result[0, :, :] == 0))  # Top row should be black
        self.assertTrue(np.all(result[-1, :, :] == 0))  # Bottom row should be black
        
        # Middle should contain the image (not black)
        middle_y = max_height // 2
        self.assertTrue(np.any(result[middle_y, :, :] > 0))  # Middle should have content
        
        # Create a test image (taller than wide)
        test_img = np.ones((600, 300, 3), dtype=np.uint8) * 255  # White image
        
        # Resize to a more square aspect ratio
        result = resize_image_to_fit(test_img, max_width, max_height)
        
        # Check dimensions
        self.assertEqual(result.shape[1], max_width)  # Width should be max
        self.assertEqual(result.shape[0], max_height)  # Height should be max
        
        # Check for black bars (should be at left and right)
        self.assertTrue(np.all(result[:, 0, :] == 0))  # Left column should be black
        self.assertTrue(np.all(result[:, -1, :] == 0))  # Right column should be black
        
        # Middle should contain the image (not black)
        middle_x = max_width // 2
        self.assertTrue(np.any(result[:, middle_x, :] > 0))  # Middle should have content


class TestImageNavigation(unittest.TestCase):
    """Test image navigation logic more comprehensively"""

    def setUp(self):
        # Create a temporary directory for test images
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Create dummy image files
        self.img_paths = []
        for i in range(5):
            img_path = os.path.join(self.test_dir, f"test_img_{i}.jpg")
            self.img_paths.append(img_path)
            # Create an empty file (we won't actually read it)
            with open(img_path, 'wb') as f:
                f.write(b'')

    @patch('cv2.imshow')
    @patch('cv2.waitKeyEx')
    @patch('photodisarm.processing.background_processor.background_processor')
    @patch('cv2.destroyAllWindows')
    @patch('asyncio.sleep', return_value=None)
    async def test_navigation_sequence(self, mock_sleep, mock_destroy, mock_bg_processor, mock_waitkey, mock_imshow):
        """Test a sequence of navigation actions"""
        # Set up viewer
        viewer = ImageViewer()
        viewer.configure(800, 600, self.test_dir)
        viewer.image_paths = self.img_paths.copy()
        viewer.current_image_index = 0
        viewer.chunk_size = 3  # Small chunk size for testing
        
        # Mock background processor to return dummy images
        dummy_img = np.ones((600, 800, 3), dtype=np.uint8) * 127
        mock_bg_processor.get_image.return_value = (None, dummy_img)
        
        # First chunk (0-2)
        # Test forward navigation through first three images
        mock_waitkey.side_effect = [65363, 65363, 65363]  # Right arrow key code 3 times
        result = await viewer._process_chunk(0, 3)
        
        # Should have processed the chunk and moved to index 3
        self.assertEqual(viewer.current_image_index, 3)
        self.assertEqual(len(viewer.history), 3)
        self.assertTrue(result)  # Should continue processing
        
        # Reset for next test
        viewer.current_image_index = 2
        viewer.history.clear()
        
        # Test going back
        mock_waitkey.side_effect = [65361, 65361]  # Left arrow key code twice
        result = await viewer._process_chunk(0, 3)
        
        # Should have gone back to index 0
        self.assertEqual(viewer.current_image_index, 0)
        self.assertEqual(len(viewer.history), 0)

        # Test save and delete actions
        viewer.current_image_index = 0
        viewer.history.clear()
        mock_waitkey.side_effect = [32, 8]  # Space (save) then Backspace (delete)
        
        # Mock the file operations
        with patch('photodisarm.utils.file_utils.move_image_to_dir_with_date') as mock_move:
            mock_move.return_value = self.img_paths[0]  # Return the same path
            with patch('os.makedirs'), patch('shutil.move'):
                result = await viewer._process_chunk(0, 3)
                
                # Should have processed the first two images
                self.assertEqual(viewer.current_image_index, 2)
                self.assertEqual(len(viewer.history), 2)


if __name__ == "__main__":
    unittest.main()
