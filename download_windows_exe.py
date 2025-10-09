#!/usr/bin/env python3
"""
Download the Windows executable from GitHub Actions
"""

import urllib.request
import json
import os
import zipfile
from pathlib import Path

def download_windows_exe():
    """Download the latest Windows executable from GitHub Actions"""
    
    # GitHub repo info
    owner = "DCX-dev"
    repo = "Order-of-the-stone"
    
    print("🔍 Checking GitHub Actions for Windows executable...")
    
    # Get latest workflow runs
    api_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs?status=success&per_page=1"
    
    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read())
            
        if not data.get('workflow_runs'):
            print("❌ No successful workflow runs found")
            print("💡 The build might still be running - check https://github.com/DCX-dev/Order-of-the-stone/actions")
            return False
        
        run = data['workflow_runs'][0]
        run_id = run['id']
        
        print(f"✅ Found workflow run: {run['name']}")
        print(f"📅 Created: {run['created_at']}")
        print(f"🔗 URL: {run['html_url']}")
        
        # Get artifacts
        artifacts_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
        
        with urllib.request.urlopen(artifacts_url) as response:
            artifacts_data = json.loads(response.read())
        
        if not artifacts_data.get('artifacts'):
            print("❌ No artifacts found")
            print("💡 The build might have failed - check the Actions page")
            return False
        
        # Find Windows artifact
        windows_artifact = None
        for artifact in artifacts_data['artifacts']:
            if 'Windows' in artifact['name']:
                windows_artifact = artifact
                break
        
        if not windows_artifact:
            print("❌ Windows artifact not found")
            print("💡 Available artifacts:", [a['name'] for a in artifacts_data['artifacts']])
            return False
        
        print(f"\n📦 Found Windows executable artifact!")
        print(f"   Name: {windows_artifact['name']}")
        print(f"   Size: {windows_artifact['size_in_bytes'] / 1024 / 1024:.1f} MB")
        
        # Note: GitHub requires authentication to download artifacts via API
        print("\n⚠️  GitHub requires authentication to download artifacts automatically.")
        print("\n✅ EASY WAY - Download manually:")
        print(f"   1. Go to: {run['html_url']}")
        print(f"   2. Scroll to 'Artifacts' at the bottom")
        print(f"   3. Click '{windows_artifact['name']}'")
        print(f"   4. Extract the ZIP → get Order_of_the_Stone.exe")
        print(f"   5. THIS WORKS ON WINDOWS 10/11! 🎮")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Manual steps:")
        print(f"   Go to: https://github.com/{owner}/{repo}/actions")
        print(f"   Click the latest successful run (green ✅)")
        print(f"   Download the Windows artifact")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🪟 Windows Executable Downloader")
    print("=" * 70)
    print()
    
    download_windows_exe()
    
    print("\n" + "=" * 70)

