# Order of the Stone

A 2D sandbox survival game built with Python and Pygame, featuring procedurally generated worlds, crafting, combat, and a modular architecture.

## 🎮 Game Overview

Order of the Stone is a 2D block-based sandbox game where players explore, mine resources, build structures, and survive in a procedurally generated world. The game features day/night cycles, hunger mechanics, village generation, and a comprehensive modding system.

## ✨ Features

### Core Gameplay
- **Procedural World Generation**: Infinite terrain with varied biomes and ore distribution
- **Survival Mechanics**: Health, hunger, and day/night cycles
- **Crafting System**: Tools, weapons, and building materials
- **Combat**: Monsters spawn at night, combat with various weapons
- **Building**: Place and destroy blocks, construct structures
- **Village Generation**: Procedurally generated villages with villagers

### Technical Features
- **Modular Architecture**: Plugin system for custom items, blocks, and entities
- **Performance Optimized**: Chunk-based rendering and lazy world generation
- **Cross-platform**: Windows, macOS, and Linux support
- **Save System**: Persistent world and player progress
- **Debug Mode**: Development tools and testing utilities

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
| **Movement** | WASD or Arrow Keys |
| **Jump** | Space |
| **Select Item** | 1-9 (Number Keys) |
| **Use Item** | Left Click |
| **Place/Remove Block** | Right Click |
| **Open Menu** | ESC |
| **Fullscreen Toggle** | F11 |
| **Save & Quit** | ESC → Quit |

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

#### `loader.py` - Mod Loading System
- **Dynamic Mod Loading**: Hot-loading of Python mods
- **Event System**: Mod event emission and handling
- **Error Handling**: Graceful mod failure recovery

#### `api/mod_api.py` - Mod API
Public interface for mods to:
- Register custom items, blocks, and entities
- Define item behavior and interactions
- Add loot tables and chest contents
- Access game systems safely

#### `registries.py` - Game Registry System
Centralized storage for:
- **Items**: Definitions, textures, properties
- **Blocks**: Block types and behaviors
- **Entities**: Entity factories and properties
- **Loot Tables**: Weighted random item generation

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

## 🔧 Modding System

### Creating a Mod

1. **Create Mod Directory**
   ```
   mods/your_mod_name/
   ├── main.py
   └── assets/
   ```

2. **Basic Mod Structure**
   ```python
   # mods/your_mod_name/main.py
   MOD_INFO = {"id": "your_mod", "version": "1.0.0"}
   
   def register(api):
       # Register custom items
       api.register_item("custom_item", "assets/custom_item.png")
       
       # Define item behavior
       def use_custom_item(ctx):
           # Custom logic here
           pass
       
       api.set_item_use("custom_item", use_custom_item)
   ```

3. **Mod API Methods**
   - `register_item()`: Add new items to the game
   - `set_item_use()`: Define custom item interactions
   - `add_chest_loot()`: Add items to loot tables
   - `register_block()`: Create new block types

### Example Mod: Blaster
The included `blaster` mod demonstrates:
- Custom weapon registration
- Projectile spawning
- Loot table integration
- Mouse-based targeting

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
- **Player State**: Position, health, hunger, inventory
- **World Data**: Block positions and types
- **Chest Contents**: Inventory of placed chests
- **Auto-save**: Automatic saving on game exit

### Save File Location
```
save_data/save.json
```

## 🐛 Debug Features

Enable debug mode by setting `DEBUG_MODE = True` in `order_of_the_stone.py`:
- **Debug HUD**: Visual indicator in-game
- **Test Inventory**: Full item kit for development
- **Enhanced Logging**: Detailed system information

## 🔧 Development

### Project Structure
```
Order-of-the-stone/
├── Order of the stone/          # Main game directory
│   ├── order_of_the_stone.py   # Main game engine
│   ├── loader.py               # Mod loading system
│   ├── registries.py           # Game registries
│   ├── api/                    # Mod API
│   │   └── mod_api.py         # Public mod interface
│   ├── mods/                   # Mod directory
│   │   └── blaster/           # Example mod
│   ├── assets/                 # Game assets
│   ├── damage/                 # Sound effects
│   └── save_data/              # Save files
└── README.md                   # This file
```

### Key Functions

#### World Generation
- `generate_initial_world()`: Creates new game world
- `maybe_generate_village_for_chunk()`: Village generation logic
- `build_house()`: Procedural house construction

#### Game Systems
- `update_player()`: Player physics and movement
- `update_monsters()`: Enemy AI and behavior
- `update_villagers()`: NPC movement and interaction
- `draw_world()`: Rendering system

#### UI Management
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
- Test mods before submission

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
- Disable debug mode in production

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

### Modding Enhancements
- **Block Behaviors**: Custom block physics and interactions
- **Entity AI**: Custom monster and NPC behaviors
- **World Generation**: Custom terrain and structure generation
- **UI Extensions**: Custom menus and HUD elements

---

**Order of the Stone** - Where creativity meets survival in a blocky 2D world.

