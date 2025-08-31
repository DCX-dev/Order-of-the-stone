# 🎭 Character Selection System

## Overview
The game now features a character selection system where players can unlock and choose from 8 different character skins using coins earned through gameplay.

## 🎮 How to Use

### Opening the Shop
- **P Key**: Press P anywhere in the game to open the character shop
- **Title Screen**: Click the "🏪 Shop" button from the main menu

### Navigation
- **Arrow Keys**: Use Left/Right arrows to browse characters
- **Mouse**: Click the arrow buttons to navigate
- **Space/Enter**: Select or unlock the current character

### Character Selection
- **Select**: Choose from unlocked characters
- **Unlock**: Spend coins to unlock new characters
- **Preview**: See character textures in the shop

## 💰 Character Costs

| Character | Price | Description |
|-----------|-------|-------------|
| **Default** | FREE | Basic character (uses player.gif) |
| **Warrior** | 100 coins | Strong fighter with armor |
| **Miner** | 200 coins | Expert digger with helmet |
| **Explorer** | 300 coins | Adventure seeker with gear |
| **Mage** | 500 coins | Magic user with robes |
| **Ninja** | 750 coins | Stealth master with mask |
| **Knight** | 1,000 coins | Noble warrior with full armor |
| **🚀 Hacker** | 1,000,000 coins | ULTIMATE CHARACTER |

## 🏆 Special Unlock - Hacker Character
The Hacker character is automatically unlocked when you find a diamond in a natural chest (ultimate achievement). This gives you 1,000,000 coins and unlocks the most special character!

## 🎨 Adding Custom Character Textures

### File Requirements
- **Format**: PNG files
- **Size**: 32x32 pixels (will be automatically scaled)
- **Location**: `assets/player/` folder
- **Naming**: Must match character names exactly (lowercase)

### Required Files
```
assets/player/
├── player.gif      (default character - already exists)
├── warrior.png     (you create this)
├── miner.png       (you create this)
├── explorer.png    (you create this)
├── mage.png        (you create this)
├── ninja.png       (you create this)
├── knight.png      (you create this)
└── hacker.png      (you create this)
```

### Texture Guidelines
- **32x32 pixels**: Base size for all textures
- **Transparency**: Use PNG with alpha channel for best results
- **Consistent Style**: Match the game's pixel art aesthetic
- **Clear Silhouette**: Make characters recognizable at small size

## 🚀 Quick Start

1. **Create Textures**: Design your own character textures as PNG files
2. **Place in Folder**: Put your textures in `assets/player/` folder
3. **Test**: Start the game and open the character shop with P key
4. **Earn Coins**: Mine, fight monsters, and complete achievements
5. **Unlock Characters**: Spend coins to unlock new character skins

**Note**: The default character automatically uses your existing `player.gif` file!

## 🔧 Technical Details

### Texture Loading
- Textures are loaded when the game starts
- Missing textures show placeholders with character initials
- Error textures (red with "!") indicate loading failures
- Fallback to default texture if loading fails

### Save System
- Character unlocks are saved with the game
- Selected character persists between sessions
- Progress is tied to the world save

### Performance
- Textures are loaded once at startup
- No runtime texture loading during gameplay
- Efficient memory usage with scaled textures

## 🎯 Tips for Custom Textures

1. **Start Simple**: Begin with basic shapes and colors
2. **Test In-Game**: See how textures look at 32x32 scale
3. **Consistent Palette**: Use similar colors across characters
4. **Clear Features**: Make each character distinct and recognizable
5. **Pixel Perfect**: Align to pixel grid for crisp appearance

## 🐛 Troubleshooting

### Missing Textures
- Check file names match exactly (lowercase)
- Ensure files are in `assets/player/` folder
- Verify PNG format and 32x32 size

### Texture Not Loading
- Check console for error messages
- Verify file permissions
- Ensure pygame can read the image format

### Performance Issues
- Keep texture files under 10KB each
- Use PNG with minimal color palette
- Avoid complex alpha channels if not needed

## 📝 Example Character Design

Here's a simple character design approach:
```
Head: 12x10 pixels (top area)
Body: 16x16 pixels (middle area)
Details: 4-6 pixels for accessories
Outline: 1 pixel border for definition
```

## 🎉 Have Fun!
Create unique characters that fit your game's style and let players express themselves through character selection!
