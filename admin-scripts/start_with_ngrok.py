"""
Start FastAPI server with ngrok tunnel for M-Pesa webhooks.

This script:
1. Starts ngrok tunnel to expose localhost:8001
2. Updates MPESA_CALLBACK_URL with the public ngrok URL
3. Starts the FastAPI server

Usage:
    python start_with_ngrok.py
"""

import os
import sys
from pyngrok import ngrok
import subprocess
import signal

def update_env_file(ngrok_url: str):
    """Update .env file with ngrok URL."""
    env_path = ".env"
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update MPESA_CALLBACK_URL
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('MPESA_CALLBACK_URL='):
                f.write(f'MPESA_CALLBACK_URL={ngrok_url}/webhooks/mpesa\n')
            else:
                f.write(line)
    
    print(f"✅ Updated .env with: MPESA_CALLBACK_URL={ngrok_url}/webhooks/mpesa")

def main():
    port = 8001
    
    print("🚀 Starting TrustVoice with ngrok tunnel...")
    print(f"📡 Exposing localhost:{port} to the internet")
    
    # Start ngrok tunnel
    try:
        public_url = ngrok.connect(port, bind_tls=True)
        ngrok_url = public_url.public_url
        
        print(f"\n✅ Ngrok tunnel established!")
        print(f"🌐 Public URL: {ngrok_url}")
        print(f"🔗 M-Pesa Webhook: {ngrok_url}/webhooks/mpesa")
        print(f"📊 API Docs: {ngrok_url}/docs")
        print(f"🎯 Ngrok Dashboard: http://127.0.0.1:4040")
        
        # Update .env file
        update_env_file(ngrok_url)
        
        print(f"\n🔧 Starting FastAPI server on port {port}...")
        print("Press Ctrl+C to stop both server and tunnel\n")
        
        # Start uvicorn server
        try:
            subprocess.run([
                "uvicorn", 
                "main:app", 
                "--reload", 
                f"--port={port}",
                "--host=0.0.0.0"
            ])
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
        finally:
            # Clean up ngrok tunnel
            ngrok.disconnect(public_url.public_url)
            print("✅ Ngrok tunnel closed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure ngrok is installed: brew install ngrok")
        print("2. Check if ngrok is authenticated: ngrok config check")
        print("3. Try running manually: ngrok http 8001")
        sys.exit(1)

if __name__ == "__main__":
    main()
