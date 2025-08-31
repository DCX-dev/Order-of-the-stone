# Order of the Stone

A 2D sandbox survival game built with Python and Pygame, featuring procedurally generated worlds, crafting, combat, and an enhanced world management system.

## 🎮 Game Overview

Order of the Stone is a 2D block-based sandbox game where players explore, mine resources, build structures, and survive in a procedurally generated world. The game features day/night cycles, hunger mechanics, village generation, and a comprehensive world management system with up to 12 worlds and automatic preview screenshots.

## ✨ Features

### Core Gameplay
- **Procedural World Generation**: Infinite terrain with varied biomes and ore distribution
- **Survival Mechanics**: Health, hunger, and day/night cycles
- **Crafting System**: Tools, weapons, and building materials
- **Combat**: Monsters spawn at night, combat with various weapons
- **Building**: Place and destroy blocks, construct structures
- **Village Generation**: Procedurally generated villages with villagers

### World Management System
- **Multiple Worlds**: Create and manage up to 12 different worlds
- **World Selection**: Enhanced UI with world previews and selection
- **Automatic Screenshots**: World previews taken every 5 minutes
- **World Persistence**: Save and load multiple worlds independently
- **Legacy Support**: Automatic detection and integration of old save files

### Technical Features
- **Performance Optimized**: Chunk-based rendering and lazy world generation
- **Cross-platform**: Windows, macOS, and Linux support
- **Enhanced Save System**: Multiple world support with automatic saving
- **Professional UI**: Modern world selection and management interface

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (recommended) or Python 3.11+
- Pygame 2.0+

### Installation

1. **Install Python**
   ```bash
   # Download from https://www.python.org/downloads/
   # Ensure Python 3.11+ is installed
   ```

2. **Install Pygame**
   ```bash
   pip3 install pygame
   ```

3. **Run the Game**
   ```bash
   cd "Order of the stone"
   python order_of_the_stone.py
   ```

## 🎯 Controls

| Action | Key |
|--------|-----|
| **Movement** | A/D or Arrow Keys |
| **Jump** | Space |
| **Select Item** | 1-9 (Number Keys) |
| **Break Block / Attack** | Left Click |
| **Place Block** | Right Click |
| **Open Chests** | E |
| **Open Shop** | P |
| **Chat** | H |
| **Inventory** | T |
| **Test Block Breaking** | B |
| **Nuclear Option** | N |
| **Toggle FPS Display** | F3 |
| **Fullscreen Toggle** | F11 |
| **Open Menu** | ESC |

## 🏗️ Architecture

### Core Components

#### `order_of_the_stone.py` - Main Game Engine
The primary game file containing:
- **Game Loop**: Main rendering and update cycle
- **World Management**: Procedural generation, chunk loading
- **Player System**: Movement, inventory, health, hunger
- **Entity System**: Monsters, villagers, projectiles
- **UI System**: Menus, HUD, chest interface
- **Physics**: Gravity, collision detection, block placement

#### `world_manager_v2.py` - World Management System
Advanced world management with:
- **World Creation**: Automatic world generation and naming
- **World Loading**: Efficient save/load system for multiple worlds
- **World Limits**: Maximum 12 worlds with slot management
- **Legacy Support**: Integration with old save.json files

#### `world_detector.py` - Automatic World Detection
Intelligent world file detection:
- **Real-time Scanning**: Automatic detection of world files
- **File Management**: Handles World X.json and legacy save.json
- **Metadata Extraction**: World creation dates and modification times
- **Smart Sorting**: Worlds ordered by last played

#### `world_ui_v2.py` - Enhanced User Interface
Modern world selection interface:
- **World Previews**: Thumbnail screenshots for each world
- **Selection System**: Click to select, click again to unselect
- **Button Management**: Play, Create, Delete, and Back buttons
- **Responsive Design**: Adapts to different screen sizes

#### `world_preview.py` - Screenshot System
Automatic world preview management:
- **Timed Screenshots**: Every 5 minutes while playing
- **Thumbnail Generation**: 160x120 pixel preview images
- **File Management**: Automatic cleanup and organization
- **Error Handling**: Fallback previews for missing images

#### `chest_system.py` - Enhanced Chest Management
Minecraft-style chest system:
- **Natural vs Player-placed**: Different behavior for different chest types
- **Loot Generation**: Automatic loot for naturally spawned chests
- **Inventory Management**: 27-slot chest interface with drag-and-drop
- **Persistence**: Chest contents saved with world data

### Asset Management

#### Texture System
- **Automatic Loading**: PNG/GIF textures from asset directories
- **Procedural Fallbacks**: Generated textures when files are missing
- **Scaling**: Automatic resizing to game tile size (32x32)

#### Asset Directories
```
assets/
├── tiles/          # Block textures
├── items/          # Item sprites
├── mobs/           # Entity sprites
├── player/         # Player character
├── HP/             # Health indicators
└── damage/         # Sound effects
```

## 🌍 World Management

### Creating Worlds
1. **Click "Play"** → Opens world selection screen
2. **Click "Create New World"** → Generates new world automatically
3. **World Naming** → Automatic naming (World 1, World 2, etc.)
4. **World Limits** → Maximum of 12 worlds supported

### World Selection
1. **Browse Worlds** → See all available worlds with previews
2. **Click World** → Select it (highlighted)
3. **Click Again** → Unselect the same world
4. **Choose Action** → Play, Delete, or Create New World

### World Features
- **Automatic Screenshots**: Previews taken every 5 minutes
- **World Information**: Creation date, last played, player status
- **Smart Organization**: Worlds sorted by most recently played
- **Legacy Integration**: Old save.json automatically detected

## 🌍 World Generation

### Terrain Features
- **Procedural Height**: Sine-wave based terrain variation
- **Ore Distribution**: Coal, iron, gold, and diamond veins
- **Tree Generation**: Random forest placement with proper spacing
- **Village Spawning**: 15% chance per 50-block chunk
- **Chest Placement**: Random treasure chests throughout the world

### Biomes
- **Carrot Biomes**: Dense carrot growth areas (10% of chunks)
- **Standard Terrain**: Normal resource distribution
- **Village Areas**: Enhanced building and NPC spawning

## 💾 Save System

### Data Persistence
- **Multiple Worlds**: Independent save files for each world
- **Player State**: Position, health, hunger, inventory
- **World Data**: Block positions and types
- **Chest Contents**: Inventory of placed chests
- **Auto-save**: Automatic saving on game exit

### Save File Structure
```
save_data/
├── World 1.json              # World 1 data
├── World 2.json              # World 2 data
├── save.json                 # Legacy save (if exists)
└── previews/                 # World preview screenshots
    ├── World 1_preview.png
    ├── World 2_preview.png
    └── Legacy Save_preview.png
```

## 🔧 Development

### Project Structure
```
Order-of-the-stone/
├── Order of the stone/          # Main game directory
│   ├── order_of_the_stone.py   # Main game engine
│   ├── world_manager_v2.py     # World management system
│   ├── world_detector.py       # Automatic world detection
│   ├── world_ui_v2.py         # Enhanced world selection UI
│   ├── world_preview.py        # Screenshot and preview system
│   ├── chest_system.py         # Enhanced chest management
│   ├── world.py                # World class definition
│   ├── assets/                 # Game assets
│   ├── damage/                 # Sound effects
│   └── save_data/              # Save files and previews
└── README.md                   # This file
```

### Key Functions

#### World Management
- `world_manager.create_world()`: Creates new world with auto-naming
- `world_detector.scan_for_worlds()`: Detects all world files
- `world_preview.take_world_screenshot()`: Captures world previews
- `chest_system.generate_natural_chest_loot()`: Generates chest contents

#### Game Systems
- `update_player()`: Player physics and movement
- `update_monsters()`: Enemy AI and behavior
- `update_villagers()`: NPC movement and interaction
- `draw_world()`: Rendering system

#### UI Management
- `draw_world_selection_screen()`: Enhanced world selection interface
- `draw_inventory()`: Hotbar and inventory display
- `draw_chest_ui()`: Chest interaction interface
- `show_message()`: Temporary notification system

## 🚀 Performance

### Optimization Strategies
- **Chunk-based Rendering**: Only render visible world areas
- **Lazy Generation**: Generate terrain as player explores
- **Efficient Collision**: Optimized block collision detection
- **Texture Caching**: Pre-loaded and scaled textures

### System Requirements
- **Minimum**: Python 3.11+, 2GB RAM, OpenGL 2.0
- **Recommended**: Python 3.12+, 4GB RAM, OpenGL 3.0
- **Display**: 1280x720 minimum resolution

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 Python conventions
- Add docstrings for public functions
- Include type hints where appropriate
- Test thoroughly before submission

## 📝 License

This project is open source. Please check individual files for specific license information.

## 🆘 Troubleshooting

### Common Issues

#### Pygame Installation
```bash
# If pip3 fails, try:
python3 -m pip install pygame

# On macOS with Homebrew:
brew install pygame
```

#### Display Issues
- **Fullscreen Problems**: Use F11 to toggle, or edit `FULLSCREEN = False`
- **Resolution Issues**: Check `WINDOWED_SIZE` in the main file
- **macOS Spaces**: Game automatically handles fullscreen spaces

#### Performance Issues
- Reduce world generation distance in the main loop
- Lower tile size (affects all textures)
- Ensure save_data directory has proper permissions

#### World Loading Issues
- Check console for debug messages about world loading
- Verify world files exist in save_data directory
- Ensure preview images are not corrupted

### Getting Help
- Check the debug console for error messages
- Verify Python and Pygame versions
- Ensure all asset files are present
- Check save file permissions

## 🔮 Future Development

### Planned Features
- **Multiplayer Support**: Network-based cooperative play
- **Advanced Crafting**: Recipe system and crafting tables
- **More Biomes**: Desert, snow, and underwater areas
- **Enhanced AI**: Smarter monsters and villagers
- **Sound System**: Background music and ambient sounds

### World System Enhancements
- **World Templates**: Pre-built world types and themes
- **World Sharing**: Export/import world files
- **Backup System**: Automatic world backups
- **World Statistics**: Detailed analytics and progress tracking

---

**Order of the Stone** - Where creativity meets survival in a blocky 2D world with professional world management.

