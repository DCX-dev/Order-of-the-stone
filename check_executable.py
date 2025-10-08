#!/usr/bin/env python3
"""
Check if executables are for the correct platform
"""

import subprocess
import sys
from pathlib import Path

def check_executable(exe_path):
    """Check what platform an executable is for"""
    path = Path(exe_path)
    
    if not path.exists():
        print(f"❌ File not found: {exe_path}")
        return False
    
    try:
        result = subprocess.run(['file', str(path)], capture_output=True, text=True)
        output = result.stdout.strip()
        
        print(f"\n📁 Checking: {path.name}")
        print(f"📄 Full path: {path}")
        print(f"📊 Type: {output}")
        
        # Determine platform
        if "Mach-O" in output:
            print(f"🍎 Platform: macOS")
            if exe_path.endswith('.exe'):
                print(f"⚠️  WARNING: This has .exe extension but is NOT a Windows executable!")
                print(f"    It will NOT work on Windows computers!")
                return False
        elif "PE32" in output or "PE executable" in output:
            print(f"🪟 Platform: Windows")
            print(f"✅ This is a REAL Windows executable - will work on Windows 10/11!")
            return True
        elif "ELF" in output:
            print(f"🐧 Platform: Linux")
        else:
            print(f"❓ Platform: Unknown")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking file: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 Executable Platform Checker")
    print("=" * 70)
    
    # Check releases directory
    releases_dir = Path("releases")
    if releases_dir.exists():
        # Check Mac executable
        mac_exe = releases_dir / "mac" / "Order_of_the_Stone"
        if mac_exe.exists():
            check_executable(str(mac_exe))
        
        # Check Windows executable
        win_exe = releases_dir / "windows" / "Order_of_the_Stone.exe"
        if win_exe.exists():
            check_executable(str(win_exe))
    
    # Check dist directory (old build)
    dist_dir = Path("dist")
    if dist_dir.exists():
        for exe_file in dist_dir.glob("Order_of_the_Stone*"):
            if exe_file.is_file() and not exe_file.name.endswith('.app'):
                check_executable(str(exe_file))
    
    print("\n" + "=" * 70)
    print("💡 TIP: Real Windows executables MUST be built on Windows!")
    print("   Use GitHub Actions to build true Windows 10/11 executables.")
    print("=" * 70)

