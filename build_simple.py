#!/usr/bin/env python3
"""
Simple PyInstaller build script for Order of the Stone
Builds for both Mac and Windows
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def build_executable(platform="mac"):
    """Build the executable with PyInstaller for specified platform"""
    
    # Get the main script path
    main_script = Path("Order of the stone/assets/com/dreamcrusherx/Order of the stone/main_script/order_of_the_stone.py")
    
    if not main_script.exists():
        print(f"[ERROR] Main script not found: {main_script}")
        return False
    
    # Get the assets directory
    assets_dir = Path("Order of the stone/assets")
    damage_dir = Path("Order of the stone/damage")
    music_dir = assets_dir / "music"
    
    if not assets_dir.exists():
        print(f"[ERROR] Assets directory not found: {assets_dir}")
        return False
    
    print(f"Building Order of the Stone executable for {platform.upper()}...")
    print(f"Main script: {main_script}")
    print(f"Assets: {assets_dir}")
    print(f"Damage sounds: {damage_dir}")
    print(f"Music: {music_dir}")
    
    # Get the game modules directory
    game_modules = Path("Order of the stone/assets/com/dreamcrusherx/Order of the stone")
    ui_dir = game_modules / "ui"
    system_dir = game_modules / "system"
    managers_dir = game_modules / "managers"
    
    # Set executable name based on platform
    if platform == "windows":
        exe_name = "Order_of_the_Stone.exe"
    else:
        exe_name = "Order_of_the_Stone"
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Single executable file
        "--windowed",  # No console window
        "--name", exe_name,
        # Add paths for module discovery
        "--paths", str(game_modules),
        "--add-data", f"{assets_dir}{os.pathsep}assets",  # Include assets
        "--add-data", f"{damage_dir}{os.pathsep}damage",  # Include damage sounds
        # Add game module directories as data (so they can be imported)
        "--add-data", f"{ui_dir}{os.pathsep}ui",
        "--add-data", f"{system_dir}{os.pathsep}system",
        "--add-data", f"{managers_dir}{os.pathsep}managers",
        # Add game modules as hidden imports
        "--hidden-import", "ui.modern_ui",
        "--hidden-import", "ui.world_ui",
        "--hidden-import", "ui.multiplayer_ui",
        "--hidden-import", "system.world_system",
        "--hidden-import", "system.chest_system",
        "--hidden-import", "system.chat_system",
        "--hidden-import", "managers.character_manager",
        "--hidden-import", "managers.coins_manager",
        "--exclude-module", "pygame.sndarray",  # Exclude to avoid numpy conflict
        "--exclude-module", "numpy",  # Exclude numpy completely since it's not needed
        str(main_script)
    ]
    
    print(f"Running PyInstaller...")
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print(f"[SUCCESS] Build successful for {platform.upper()}!")
            
            # Check if executable was created
            exe_path = Path(f"dist/{exe_name}")
            if exe_path.exists():
                # Copy to platform-specific directory
                output_dir = Path(f"releases/{platform}")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / exe_name
                shutil.copy2(exe_path, output_file)
                
                print(f"[SUCCESS] Executable created: {output_file}")
                print(f"[SUCCESS] {platform.upper()} executable is ready!")
                return True
            else:
                print(f"[ERROR] Executable not found in dist/")
                return False
        else:
            print("[ERROR] Build failed!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def build_all():
    """Build executables for all platforms"""
    print("=" * 60)
    print("Building Order of the Stone for ALL platforms")
    print("=" * 60)
    
    platforms = ["mac", "windows"]
    results = {}
    
    for platform in platforms:
        print(f"\n{'='*60}")
        print(f"Building for {platform.upper()}...")
        print(f"{'='*60}\n")
        
        # Clean build directories
        if Path("build").exists():
            shutil.rmtree("build")
        if Path("dist").exists():
            shutil.rmtree("dist")
        for spec_file in Path(".").glob("*.spec"):
            spec_file.unlink()
        
        results[platform] = build_executable(platform)
    
    # Print summary
    print("\n" + "=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    for platform, success in results.items():
        status = "[SUCCESS]" if success else "[FAILED]"
        print(f"{platform.upper()}: {status}")
    
    print("\nExecutables are in the 'releases/' directory")
    print("=" * 60)
    
    return all(results.values())

if __name__ == "__main__":
    # Check if user wants to build for specific platform
    if len(sys.argv) > 1:
        platform = sys.argv[1].lower()
        if platform in ["mac", "windows"]:
            success = build_executable(platform)
        else:
            print(f"[ERROR] Unknown platform: {platform}")
            print("Usage: python build_simple.py [mac|windows|all]")
            sys.exit(1)
    else:
        # Build for all platforms
        success = build_all()
    
    sys.exit(0 if success else 1)

