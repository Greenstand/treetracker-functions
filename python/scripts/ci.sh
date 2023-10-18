#! /bin/bash
# This script is used to build and test the project written in Python.

# Exit immediately if a command exits with a non-zero status.
set -e 

# Install dependencies.
pip install -r requirements.txt

# Run tests.
python3 -m unittest discover -p "*_test.py" -v
