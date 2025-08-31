#!/usr/bin/env python3
"""
Order of the Stone - Game Launcher
This launcher runs the game using the bundled pygame.
"""

import sys
import os

# Add bundled pygame to path
current_dir = os.path.dirname(os.path.abspath(__file__))
pygame_path = os.path.join(current_dir, "pygame")
sys.path.insert(0, pygame_path)

# Import and run game
try:
    # Try to import from the new organized structure
    sys.path.append(os.path.join(current_dir, "..", "assets", "com", "dreamcrusherx", "Order of the stone", "main_script"))
    import order_of_the_stone
    print("🎮 Game finished!")
except Exception as e:
    print(f"❌ Error running game: {e}")
    print("   Make sure the game files are in the correct location")
    input("Press Enter to exit...")
