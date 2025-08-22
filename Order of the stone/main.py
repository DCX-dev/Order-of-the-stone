#!/usr/bin/env python3
"""
EXTREME ENGINEERING: Main Entry Point for Order of the Stone
This file ensures proper imports and game initialization for exe compilation
"""

import sys
import os
import traceback

def main():
    """Main entry point for the game"""
    try:
        print("🎮 EXTREME ENGINEERING: Order of the Stone")
        print("🚀 Initializing game...")
        
        # Add the current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Check if required files exist
        required_files = [
            "order_of_the_stone.py",
            "assets/",
            "world_ui.py",
            "world_system.py",
            "character_manager.py"
        ]
        
        print("🔍 Checking required files...")
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} - MISSING!")
                print(f"   🔧 Make sure {file_path} is in the same directory as main.py")
                input("Press Enter to exit...")
                return False
        
        print("📦 All required files found!")
        print("🎯 Importing game...")
        
        # Import the main game
        import order_of_the_stone
        
        print("✅ Game imported successfully!")
        print("🎮 Game should start automatically...")
        
        # The game will start automatically when imported
        # All the main game logic is in order_of_the_stone.py
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("🔧 This usually means a missing dependency or file")
        print("📋 Full error details:")
        traceback.print_exc()
        input("Press Enter to exit...")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("🔧 Something unexpected happened")
        print("📋 Full error details:")
        traceback.print_exc()
        input("Press Enter to exit...")
        return False

if __name__ == "__main__":
    print("🎮 Starting Order of the Stone...")
    success = main()
    if not success:
        print("❌ Game failed to start")
        sys.exit(1)
    else:
        print("✅ Game started successfully!")
