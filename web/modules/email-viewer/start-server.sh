#!/bin/bash
# Start the email viewer web server

PORT=${1:-8092}
echo "Starting Email Viewer on http://localhost:$PORT"
echo "Press Ctrl+C to stop"
python3 -m http.server $PORT