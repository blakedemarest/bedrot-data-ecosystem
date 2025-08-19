#!/bin/bash
# Start the BEDROT Data Dashboard Backend

echo "Starting BEDROT Data Dashboard Backend..."

# Navigate to project directory
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_dashboard

# Activate virtual environment
source venv/bin/activate

# Start the backend server
python backend/main.py