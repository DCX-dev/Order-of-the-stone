# 🎮 Order of the Stone - Setup Guide

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DCX-dev/Order-of-the-stone.git
   cd Order-of-the-stone
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   
   # Activate virtual environment
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   
   **Option A - Full installation (recommended for developers):**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Option B - Minimal installation (just to play the game):**
   ```bash
   pip install -r requirements-minimal.txt
   ```

4. **Run the game:**
   ```bash
   python "Order of the stone/assets/com/dreamcrusherx/Order of the stone/main_script/order_of_the_stone.py"
   ```

## Game Controls

- **Movement:** WASD or Arrow Keys
- **Jump:** Spacebar
- **Inventory:** I key
- **Crafting:** C key
- **Chat:** Enter key
- **Break Blocks:** Left Click
- **Place Blocks:** Right Click

## Features

✨ **Enhanced Gameplay:**
- Realistic crafting system with proper recipes
- Improved drag-and-drop inventory system
- Collision-free spawning system
- Enhanced collision detection

🎯 **Game Mechanics:**
- Infinite world generation
- Day/night cycle with monster spawning
- Death penalties (lose coins and items)
- Advanced monster AI
- Village generation with NPCs
- Underground fortress exploration

🔧 **Technical Features:**
- Organized modular codebase
- Enhanced world generation system
- Improved asset management
- Better error handling and logging

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'pygame'**
   ```bash
   pip install pygame
   ```

2. **ModuleNotFoundError: No module named 'PIL'**
   ```bash
   pip install Pillow
   ```

3. **Game won't start / Black screen**
   - Make sure you're running from the project root directory
   - Check that all asset files are present
   - Try running with Python 3.8+ 

4. **Performance Issues**
   - Close other applications to free up memory
   - Lower the game resolution in settings
   - Update your graphics drivers

### Getting Help

If you encounter issues:
1. Check the [Issues](https://github.com/DCX-dev/Order-of-the-stone/issues) page
2. Create a new issue with details about your problem
3. Include your Python version and operating system

## Development

For developers wanting to contribute:

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Format code:
   ```bash
   black .
   ```

4. Type checking:
   ```bash
   mypy "Order of the stone/assets/com/dreamcrusherx/Order of the stone/main_script/order_of_the_stone.py"
   ```

## System Requirements

**Minimum:**
- Python 3.8+
- 2GB RAM
- 500MB free disk space
- DirectX 9.0c compatible graphics

**Recommended:**
- Python 3.10+
- 4GB RAM
- 1GB free disk space
- Dedicated graphics card

Enjoy playing Order of the Stone! 🎮
