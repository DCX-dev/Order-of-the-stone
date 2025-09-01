#!/usr/bin/env python3
"""
Order of the Stone - Demo Launcher
==================================
Professional launcher for the Kickstarter demo
"""

import os
import sys
import pygame

def main():
    """Main launcher function"""
    print("🎮 Order of the Stone - Demo Launcher")
    print("=====================================")
    print("🚀 Starting your adventure...")
    
    # Add the game directory to Python path
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
        game_script_path = os.path.join(base_path, 'Order of the stone', 'assets', 'com', 'dreamcrusherx', 'Order of the stone', 'main_script', 'order_of_the_stone.py')
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
        game_script_path = os.path.join(base_path, 'Order of the stone', 'assets', 'com', 'dreamcrusherx', 'Order of the stone', 'main_script', 'order_of_the_stone.py')
    
    # Check if game script exists
    if not os.path.exists(game_script_path):
        print(f"❌ Error: Game script not found at {game_script_path}")
        print("Please ensure all game files are included in the distribution.")
        input("Press Enter to exit...")
        return 1
    
    # Add game directory to Python path
    game_dir = os.path.dirname(game_script_path)
    if game_dir not in sys.path:
        sys.path.insert(0, game_dir)
    
    # Change to the game directory
    os.chdir(os.path.dirname(game_script_path))
    
    try:
        # Import and run the game
        print("🎯 Loading game modules...")
        import order_of_the_stone
        print("✅ Game loaded successfully!")
        print("🎮 Enjoy your adventure!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed.")
        input("Press Enter to exit...")
        return 1
    except Exception as e:
        print(f"❌ Game error: {e}")
        print("Please check the game files and try again.")
        input("Press Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
