#!/usr/bin/env python3
"""
Start Dashboard Server

Starts a local HTTP server to view the generated health dashboard.
"""

import http.server
import socketserver
import sys
from pathlib import Path

class DashboardServer:
    """Simple HTTP server for viewing the health dashboard."""
    
    def __init__(self, port=8000, directory="output"):
        self.port = port
        self.directory = Path(directory)
        self.handler = http.server.SimpleHTTPRequestHandler
    
    def start(self):
        """Start the HTTP server."""
        if not self.directory.exists():
            print(f"❌ Directory not found: {self.directory}")
            return False
        
        print(f"🌐 Starting dashboard server...")
        print(f"📁 Serving directory: {self.directory.absolute()}")
        print(f"🔗 Dashboard URL: http://localhost:{self.port}/dashboard.html")
        print(f"📊 Stats URL: http://localhost:{self.port}/summary_stats.json")
        print(f"📈 Time Series: http://localhost:{self.port}/time_series/")
        print(f"📊 Distributions: http://localhost:{self.port}/distributions/")
        print(f"\n💡 Press Ctrl+C to stop the server")
        print(f"=" * 60)
        
        # Change to the output directory
        original_dir = Path.cwd()
        try:
            import os
            os.chdir(self.directory)
            
            # Start the server
            with socketserver.TCPServer(("", self.port), self.handler) as httpd:
                print(f"🚀 Server started on port {self.port}")
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            return True
        except Exception as e:
            print(f"❌ Server error: {e}")
            return False
        finally:
            os.chdir(original_dir)
    
    def check_dashboard_files(self):
        """Check if dashboard files exist."""
        required_files = [
            "dashboard.html",
            "summary_stats.json"
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.directory / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"⚠️  Missing dashboard files: {', '.join(missing_files)}")
            print(f"💡 Run 'python3 main.py' to generate the dashboard first")
            return False
        
        return True

def main():
    """Main function to start the dashboard server."""
    print("🍏 Apple Health Dashboard Server")
    print("=" * 40)
    
    # Create server instance
    server = DashboardServer(port=8000)
    
    # Check if dashboard files exist
    if not server.check_dashboard_files():
        return False
    
    # Start the server
    try:
        server.start()
        return True
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)