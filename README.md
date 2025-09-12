# 🎮 Order of the Stone

A 2D sandbox survival adventure game built with Python and Pygame, featuring procedurally generated worlds, advanced combat mechanics, crafting systems, and multiplayer capabilities.

![Game Screenshot](https://img.shields.io/badge/Status-Active%20Development-green)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.0%2B-orange)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 🌟 Features

### 🎯 Core Gameplay
- **Procedural World Generation**: Infinite terrain with varied biomes, caves, and structures
- **Advanced Combat System**: Distance-based combat with sword throwing and close-range slashing
- **Comprehensive Crafting**: Tools, weapons, armor, and building materials
- **Survival Mechanics**: Health, hunger, stamina, and day/night cycles
- **Building & Mining**: Place and destroy blocks, construct elaborate structures
- **Multiple Worlds**: Create and manage up to 12 different worlds with preview screenshots

### ⚔️ Combat System
- **Sword Throwing**: Throw swords at distant enemies - they return automatically!
- **Close Combat**: Slash enemies within 2 blocks for immediate damage
- **Weapon Variety**: Wooden, Stone, Diamond, Gold, and Enchanted swords
- **Monster AI**: Ground-based monsters with realistic physics and behavior
- **Blood Effects**: Visual feedback with particle effects on hits

### 🏗️ World Features
- **Villages**: Procedurally generated with friendly NPCs and trading
- **Fortresses**: Dangerous but rewarding structures filled with loot
- **Underground Caves**: Rich in ores and hidden treasures
- **Boss Arena**: Legendary boss fight hidden under bedrock at world center
- **Chess Pieces**: Special entities that drop valuable loot when collected

### 🎨 Visual & Audio
- **GIF Animations**: Support for custom character and entity animations
- **Particle Effects**: Blood, dust, and environmental effects
- **Dynamic Lighting**: Day/night cycle with atmospheric changes
- **Sound Effects**: Damage sounds and environmental audio
- **Modern UI**: Clean, responsive interface with drag-and-drop inventory

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (3.12+ recommended)
- **Pygame 2.0+**

### Installation

1. **Clone or Download** the repository
2. **Install Python** from [python.org](https://www.python.org/downloads/)
3. **Install Pygame**:
   ```bash
   pip install pygame
   ```
4. **Run the Game**:
   ```bash
   cd "Order of the stone/assets/com/dreamcrusherx/Order of the stone/main_script"
   python order_of_the_stone.py
   ```

### 🎮 Controls

| Action | Key | Description |
|--------|-----|-------------|
| **Movement** | A/D or Arrow Keys | Move left/right |
| **Jump** | Space or W | Jump |
| **Crouch** | S or Down Arrow | Move down/crouch |
| **Attack** | Left Click | Break blocks / Attack monsters |
| **Place Block** | Right Click | Place held blocks |
| **Inventory** | T | Open/close full inventory |
| **Chests** | E | Open/close chests |
| **Shop** | P | Open character/weapon shop |
| **Chat** | H | Open chat system |
| **Hotbar** | 1-9 | Select inventory slots |
| **Pause** | ESC | Pause menu / Back |
| **Debug** | F3 | Toggle FPS and coordinates |
| **Fullscreen** | F11 | Toggle fullscreen mode |

## ⚔️ Combat Guide

### Sword Combat System
The game features an innovative distance-based combat system:

#### Close Combat (≤2 blocks)
- **Sword Slash**: Quick up-to-down slash animation
- **Immediate Damage**: Deals damage instantly
- **Visual Feedback**: Blood particles on hit

#### Long Range (>2 blocks)
- **Sword Throwing**: Throw your sword at enemies
- **Auto-Targeting**: Automatically targets closest monster to click
- **Return System**: Sword automatically returns to your inventory
- **Projectile Physics**: Sword follows realistic trajectory

### Weapon Types
| Weapon | Damage | Speed | Special |
|--------|--------|-------|---------|
| **Wooden Sword** | 2 | Fast | Basic weapon |
| **Stone Sword** | 3 | Medium | Improved damage |
| **Diamond Sword** | 4 | Medium | High durability |
| **Gold Sword** | 3 | Fast | Quick attacks |
| **Enchanted Sword** | 5 | Slow | Ultimate weapon |

## 🏗️ Crafting System

### Basic Tools
```
🗡️ Wooden Sword
[Oak Plank]
[Oak Plank]
= Wooden Sword

⛏️ Wooden Pickaxe
[Oak Plank] [Oak Plank]
    [Stone]
= Wooden Pickaxe
```

### Advanced Weapons
```
🗡️ Stone Sword
[Stone]
[Stone]
[Oak Plank]
= Stone Sword

🗡️ Diamond Sword
[Diamond]
[Diamond]
[Stick]
= Diamond Sword
```

### Armor
```
🛡️ Iron Helmet: 5 Iron + 2 Coal
🛡️ Iron Chestplate: 8 Iron + 3 Coal
🛡️ Iron Leggings: 7 Iron + 2 Coal
🛡️ Iron Boots: 4 Iron + 1 Coal
```

### Special Items
```
⚒️ Olympic Axe (Breaks Bedrock!)
25 Stone + 15 Oak Planks
= Olympic Axe
```

## 🌍 World Management

### Multiple Worlds
- **Create Worlds**: Generate up to 12 unique worlds
- **World Selection**: Choose from available worlds with preview screenshots
- **Auto-Screenshots**: Automatic preview generation every 5 minutes
- **World Persistence**: Each world saves independently

### World Features
- **Procedural Generation**: Infinite terrain with varied biomes
- **Village Generation**: NPCs, trading, and quests
- **Underground Caves**: Rich in ores and hidden treasures
- **Boss Arena**: Legendary boss fight at world center (0,0)
- **Chess Pieces**: Special collectible entities with unique loot

## 🎨 Customization

### Character System
- **Multiple Characters**: Warrior, Miner, Explorer, Mage, Ninja, Knight, Hacker
- **Custom Animations**: Support for custom GIF animations
- **Character Switching**: Change characters in the shop
- **Animation System**: Walking, jumping, fighting, breaking, placing animations

### Custom Animations
Place your custom `.gif` files in:
```
assets/player/animations/
├── standing.gif    # Idle animation
├── walking.gif     # Movement animation
├── jumping.gif     # Jump animation
├── falling.gif     # Fall animation
├── fighting.gif    # Combat animation
├── breaking.gif    # Mining animation
└── placing.gif     # Building animation
```

## 🏆 Game Objectives

### Short Term Goals
1. **Escape the Starting Fortress** - Find your way out of the spawn fortress
2. **Gather Resources** - Collect wood, stone, and basic materials
3. **Craft Equipment** - Build better tools and weapons
4. **Explore the World** - Discover villages, caves, and structures

### Long Term Goals
1. **Defeat the Boss** - Find and defeat the legendary boss at world center
2. **Collect All Items** - Gather every weapon, tool, and armor piece
3. **Build Epic Structures** - Create magnificent buildings and fortresses
4. **Master All Worlds** - Explore and conquer all 12 available worlds

## 🔧 Technical Features

### Performance
- **Chunk-based Rendering**: Efficient world loading and rendering
- **Lazy Generation**: Worlds generate as you explore
- **Memory Management**: Optimized for long play sessions
- **60 FPS Target**: Smooth gameplay experience

### Save System
- **Auto-Save**: Automatic saving every 5 minutes
- **Multiple Worlds**: Independent save files for each world
- **Legacy Support**: Compatible with older save files
- **Backup System**: Automatic backup creation

### Multiplayer (Experimental)
- **Network Play**: Connect with other players
- **Server Hosting**: Host your own game server
- **Chat System**: Communicate with other players
- **Synchronized Worlds**: Shared world state

## 🐛 Troubleshooting

### Common Issues

**Game Won't Start**
- Ensure Python 3.11+ is installed
- Install Pygame: `pip install pygame`
- Check file permissions

**Performance Issues**
- Lower graphics settings in options
- Close other applications
- Update graphics drivers

**Save File Issues**
- Check available disk space
- Verify file permissions
- Use backup saves if available

### Getting Help
- Check the console output for error messages
- Verify all dependencies are installed
- Ensure you're using the correct Python version

## 📁 Project Structure

```
Order of the stone/
├── assets/
│   ├── com/dreamcrusherx/Order of the stone/
│   │   ├── main_script/
│   │   │   └── order_of_the_stone.py    # Main game file
│   │   ├── managers/                     # Game managers
│   │   ├── network/                      # Multiplayer code
│   │   ├── system/                       # Game systems
│   │   ├── ui/                          # User interface
│   │   └── world_generation/            # World generation
│   ├── player/                          # Character assets
│   ├── tiles/                           # Block textures
│   ├── items/                           # Item textures
│   ├── mobs/                            # Monster assets
│   └── music/                           # Audio files
├── guides/                              # Game documentation
└── README.md                            # This file
```

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Bugs**: Use the issue tracker to report problems
2. **Suggest Features**: Share your ideas for new content
3. **Submit Code**: Fork the repository and submit pull requests
4. **Improve Documentation**: Help make the guides better

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Pygame Community** - For the excellent game development framework
- **Python Community** - For the powerful programming language
- **Contributors** - Everyone who has helped improve the game
- **Players** - For feedback and suggestions

## 📞 Contact

- **Issues**: Use the GitHub issue tracker
- **Discussions**: Join the community discussions
- **Email**: [Your contact email]

---

**Happy Gaming! 🎮**

*Order of the Stone* - Where every block tells a story, every sword finds its target, and every world holds infinite possibilities.
