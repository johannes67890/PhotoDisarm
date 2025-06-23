"""
Tests for the image navigation functionality
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from photodisarm.core.image_viewer import ImageViewer


class TestImageNavigation(unittest.TestCase):
    """Test cases for image navigation"""
    
    @patch('cv2.imshow')
    @patch('cv2.waitKeyEx')
    @patch('photodisarm.processing.background_processor.background_processor')
    def test_image_navigation_keys(self, mock_bg_processor, mock_waitkey, mock_imshow):
        """Test that navigation keys work correctly"""
        # Setup
        viewer = ImageViewer()
        viewer.image_paths = ["image1.jpg", "image2.jpg", "image3.jpg"]
        viewer.current_image_index = 1  # Start at the middle image
        
        # Mock the background processor to avoid actual image loading
        mock_bg_processor.get_image.return_value = ("image2.jpg", np.zeros((100, 100, 3)))
        
        # Test "other key" navigation (next image)
        mock_waitkey.return_value = 100  # Some key that's not specifically handled
        viewer._process_chunk(0, 3)  # Process all three images
        
        # Should have moved to the next image
        self.assertEqual(viewer.current_image_index, 2, "Failed to advance to next image on key press")
        
        # Should have added the current image to history
        self.assertEqual(len(viewer.history), 1, "Failed to add image to history")
        self.assertEqual(viewer.history[0], "image2.jpg", "Added wrong image to history")
    

if __name__ == "__main__":
    unittest.main()
