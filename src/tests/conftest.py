"""
Test configuration file for pytest
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure test environment variables if needed
os.environ['PHOTODISARM_TEST_MODE'] = 'true'
