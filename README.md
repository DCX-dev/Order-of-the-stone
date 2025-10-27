# 🎮 Order of the Stone

A 2D sandbox survival adventure game built with Python and Pygame, featuring procedurally generated worlds, advanced combat mechanics, crafting systems, and multiplayer capabilities.

![Game Screenshot](https://img.shields.io/badge/Status-Active%20Development-green)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.0%2B-orange)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 🌟 Features

### 🎯 Core Gameplay
- **Procedural World Generation**: Infinite terrain with varied biomes, caves, and deep oceans
- **Advanced Combat System**: Distance-based combat with sword throwing and close-range slashing
- **Comprehensive Crafting**: Tools, weapons, armor, and building materials
- **Achievement System**: Unlock achievements and earn coins for various accomplishments
- **Survival Mechanics**: Health, hunger, stamina, and day/night cycles
- **Building & Mining**: Place and destroy blocks, construct elaborate structures
- **Multiple Worlds**: Create and manage multiple worlds with preview screenshots

### ⚔️ Combat System
- **Sword Throwing**: Throw swords at distant enemies - they return automatically!
- **Close Combat**: Slash enemies within 2 blocks for immediate damage
- **Weapon Variety**: Wooden, Stone, Diamond, Gold, and Enchanted swords
- **Monster AI**: Ground-based monsters with realistic physics and behavior
- **Blood Effects**: Visual feedback with particle effects on hits

### 🏗️ World Features
- **Procedural Biomes**: Grasslands, deserts, forests, and beaches with distinct characteristics
- **Deep Oceans**: Realistic ocean generation with natural depth variation and smooth beach transitions
- **Villages**: Procedurally generated with friendly NPCs and trading
- **Fortresses**: Dangerous but rewarding structures filled with loot
- **Underground Caves**: Rich in ores and hidden treasures
- **Mad Pigeons**: Special mobs that spawn in desert biomes
- **Sparse Desert Trees**: Natural tree generation in desert areas

### 🎨 Visual & Audio
- **GIF Animations**: Support for custom character and entity animations
- **Particle Effects**: Blood, dust, and environmental effects
- **Dynamic Lighting**: Day/night cycle with atmospheric changes
- **Sound Effects**: Damage sounds, achievement unlocks, and environmental audio
- **Modern UI**: Clean, responsive interface with drag-and-drop inventory and scrolling achievements screen
- **Easter Eggs**: Special April Fool's Day title change ("Doritos of the Stone")

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
| **Achievements** | L | View achievements screen |
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

## 🏆 Achievement System

Unlock achievements by completing various in-game tasks and earn coins as rewards!

### Achievement Categories
- **🏗️ Builder**: Master the art of placing blocks and structures
- **💰 Explorer**: Discover hidden secrets and travel the world
- **⚔️ Warrior**: Defeat monsters and survive the dangerous wilderness
- **⛏️ Miner**: Dig deep and find valuable resources
- **🎮 Miscellaneous**: Special achievements for unique accomplishments

### Example Achievements
- **First Steps**: Place your first block (25 coins)
- **Adventurer**: Travel 1000 blocks (50 coins)
- **Monster Slayer**: Kill 50 monsters (100 coins)
- **Deep Diver**: Mine 500 stone blocks (50 coins)
- **Torch Master**: Place 100 torches (25 coins)
- **Boss Conqueror**: Defeat the legendary boss (500 coins)

View all achievements and track your progress in the Achievements screen accessible from the title screen!

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

### World Generation
- **Multiple Worlds**: Create and explore multiple unique worlds
- **World Selection**: Choose from available worlds with preview screenshots
- **Auto-Screenshots**: Automatic preview generation
- **World Persistence**: Each world saves independently
- **Procedural Generation**: Infinite terrain with varied biomes
- **Biome System**: Grasslands, deserts with sparse trees, beaches, and deep oceans
- **Ocean Generation**: Realistic oceans with natural depth (12-18 blocks) and smooth beach transitions
- **Natural Features**: Desert pigeons, varied terrain, and realistic water flow

### World Features
- **Village Generation**: NPCs, trading, and quests
- **Underground Caves**: Rich in ores and hidden treasures
- **Boss Arena**: Legendary boss fight at world center (0,0)
- **Dungeon Fortresses**: Dangerous but rewarding structures

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
1. **Escape the Starting Area** - Find your way out and explore
2. **Unlock First Achievement** - Place your first block and earn coins!
3. **Gather Resources** - Collect wood, stone, and basic materials
4. **Craft Equipment** - Build better tools and weapons
5. **Explore the World** - Discover villages, caves, and deep oceans

### Long Term Goals
1. **Defeat the Boss** - Find and defeat the legendary boss at world center (500 coin achievement!)
2. **Collect All Items** - Gather every weapon, tool, and armor piece
3. **Build Epic Structures** - Create magnificent buildings and fortresses
4. **Master Achievement System** - Unlock all achievements and earn maximum coins
5. **Explore All Biomes** - Visit grasslands, deserts, oceans, and underground caves

## 🔧 Technical Features

### Performance
- **Chunk-based Rendering**: Efficient world loading and rendering
- **Lazy Generation**: Worlds generate as you explore
- **Memory Management**: Optimized for long play sessions
- **60 FPS Target**: Smooth gameplay experience
- **Optimized UI**: Efficient rendering with removed shadows and gradients for better performance

### Save System
- **Auto-Save**: Automatic saving during gameplay
- **Multiple Worlds**: Independent save files for each world
- **Legacy Support**: Compatible with older save files
- **Backup System**: Automatic backup creation
- **Achievement Tracking**: Persistent achievement progress and coin balance

### Options & Settings
- **Graphics Settings**: Customize FPS and display options
- **Fullscreen Mode**: Toggle fullscreen for immersive gameplay
- **Website Link**: Direct link to www.dreamcrusherx.com from the options menu
- **Performance**: Optimized for smooth 60 FPS gameplay

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
│   │   │   └── order_of_the_stone.py       # Main game file
│   │   ├── managers/                        # Game managers
│   │   ├── multiplayer/                     # Multiplayer code (LAN)
│   │   ├── system/                          # Game systems
│   │   ├── ui/                             # User interface
│   │   └── world_generation/               # World generation
│   ├── player/                             # Character assets
│   ├── tiles/                              # Block textures
│   ├── items/                              # Item textures
│   ├── mobs/                               # Monster assets
│   └── music/                              # Audio files
├── guides/                                 # Game documentation
└── README.md                               # This file
```

## 🆕 Recent Updates (v1.3.1+)

### 🏆 Achievements System
- **Comprehensive Achievement Tracking**: Unlock achievements across multiple categories
- **Coin Rewards**: Earn coins for completing various tasks
- **Beautiful UI**: Scrolling achievements screen with progress tracking
- **Sound Effects**: Achievement unlock sounds (when sound file is added)

### 🌊 World Generation Improvements
- **Deep Oceans**: Natural ocean depths (12-18 blocks) with smooth variations
- **Smooth Beach Transitions**: 30-block wide beach zones for realistic slopes
- **Desert Biomes**: Sparse trees and mad pigeon spawns for desert exploration
- **Natural Depth Variation**: Ocean floors with realistic hills and valleys

### 🎨 UI Enhancements
- **Achievements Button**: Access achievements from the title screen
- **Website Link**: Direct link to www.dreamcrusherx.com in options
- **Removed Shop State**: Streamlined menu system
- **Performance Optimizations**: Removed expensive UI effects for better FPS

### 🎪 Easter Eggs
- **April Fool's Day**: Special title change to "Doritos of the Stone" on April 1st

### 🐛 Bug Fixes
- Fixed player spawn position after world generation
- Improved ocean generation and beach transitions
- Fixed achievements screen rendering issues
- Removed debug features (N key block removal)

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
