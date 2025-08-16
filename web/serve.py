#!/usr/bin/env python3
"""
Simple HTTP server for the MCP Web Application
"""

import http.server
import socketserver
import os
import webbrowser
import re
from pathlib import Path

# Read port from .env file
def get_port_from_env():
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('MCP_SERVER_PORT'):
                    match = re.match(r'MCP_SERVER_PORT\s*=\s*(\d+)', line)
                    if match:
                        api_port = int(match.group(1))
                        # Use API port + 80 for web server to avoid conflicts
                        return api_port + 80
    return 8090  # Default port if not found

# Check if port is in use and find an alternative
def get_available_port(preferred_port):
    import socket
    for port_offset in range(0, 10):
        port = preferred_port + port_offset
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            if port_offset > 0:
                print(f"Note: Port {preferred_port} was in use, using {port} instead")
            return port
        except OSError:
            continue
    print(f"Warning: Could not find available port near {preferred_port}, using it anyway")
    return preferred_port

PORT = get_available_port(get_port_from_env())
DIRECTORY = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Read API port for display
    api_port = PORT - 80  # Since we add 80 to the API port for web server
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 MCP Web Application")
        print(f"=" * 50)
        print(f"Web Server: http://localhost:{PORT}")
        print(f"API Server: http://localhost:{api_port}")
        print(f"=" * 50)
        print(f"Available applications:")
        print(f"  • Integrated App: http://localhost:{PORT}")
        print(f"  • Legacy API Tester: http://localhost:{PORT}/index-legacy.html")
        print(f"  • Standalone Email Viewer: http://localhost:{PORT}/email-viewer/")
        print(f"=" * 50)
        print(f"Press Ctrl+C to stop the server")
        
        # Try to open browser with main app
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✋ Server stopped")

if __name__ == "__main__":
    main()