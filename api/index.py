import os
import sys

# Add the 'api' directory to the python path so 'main' can be resolved
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
