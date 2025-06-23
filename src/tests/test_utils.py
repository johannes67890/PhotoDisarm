"""
Tests for the photodisarm utility functions
"""
import os
import sys
import unittest
from datetime import datetime

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from photodisarm.utils import file_utils
from photodisarm.i18n.localization import localization


class TestFileUtils(unittest.TestCase):
    """Test cases for file utility functions"""
    
    def test_sort_images_by_date(self):
        """Test sorting images by date"""
        # Mock image paths (would need real images for full test)
        paths = ["image1.jpg", "image2.jpg"]
        
        # The function should return a list (even if it's just passing through the paths)
        sorted_paths = file_utils.sort_images_by_date(paths)
        self.assertIsInstance(sorted_paths, list)
        
    def test_center_window(self):
        """Test that center_window function exists"""
        # This is just a check that the function exists, not a functional test
        self.assertTrue(callable(file_utils.center_window))


class TestLocalization(unittest.TestCase):
    """Test cases for localization"""
    
    def test_switch_language(self):
        """Test language switching"""
        # Get initial language
        initial_lang = localization.current_language_code
        
        # Switch language
        localization.switch_language()
        
        # Should be different now
        self.assertNotEqual(initial_lang, localization.current_language_code)
        
        # Switch back
        localization.switch_language()
        
        # Should be back to the initial language
        self.assertEqual(initial_lang, localization.current_language_code)
    
    def test_get_text(self):
        """Test getting localized text"""
        # This key should exist in both languages
        key = "window_title"
        
        # Should get a string
        text = localization.get_text(key)
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) > 0)


if __name__ == "__main__":
    unittest.main()
