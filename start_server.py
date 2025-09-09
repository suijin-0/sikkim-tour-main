#!/usr/bin/env python3
"""
Startup script for Sacred Sikkim AI Chat Application
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def start_flask_server():
    """Start the Flask server"""
    print("🚀 Starting Flask server...")
    try:
        subprocess.Popen([sys.executable, 'server.py'])
        print("✅ Flask server started on http://localhost:3000")
        return True
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        return False

def main():
    print("🏔️ Sacred Sikkim AI Chat Application")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path('server.py').exists():
        print("❌ server.py not found. Please run this script from the project directory.")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Check Ollama
    print("🔍 Checking Ollama connection...")
    if not check_ollama():
        print("⚠️  Warning: Ollama doesn't seem to be running.")
        print("   Please make sure Ollama is installed and running with the 'mistral' model.")
        print("   You can start Ollama with: ollama serve")
        print("   And pull the mistral model with: ollama pull mistral")
        print()
    
    # Start Flask server
    if start_flask_server():
        print()
        print("🎉 Application started successfully!")
        print("📱 Open your browser and go to: http://localhost:3000")
        print("🌐 Or open the index.html file directly in your browser")
        print()
        print("💡 Tips:")
        print("   - Make sure Ollama is running with the 'mistral' model")
        print("   - The AI chat will work when both servers are running")
        print("   - Press Ctrl+C to stop the Flask server")
        
        # Wait a moment then open browser
        time.sleep(2)
        try:
            webbrowser.open('index.html')
        except:
            print("   Please manually open index.html in your browser")
    
    print("\n🛑 Press Ctrl+C to stop the server")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
