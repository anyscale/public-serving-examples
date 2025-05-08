import pytest
import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ["TESTING"] = "true"


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Add any test environment setup here
    yield
    # Add any test environment cleanup here
