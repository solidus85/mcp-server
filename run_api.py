#!/usr/bin/env python3
"""
Simple script to run the API server
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.app import main

if __name__ == "__main__":
    main()