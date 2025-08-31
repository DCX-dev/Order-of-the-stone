# 🎬 Custom Animations Guide

## How to Add Your Own Custom Animations

This guide will help you add your own custom walking, fighting, and jumping animations to the game!

### 📁 Animation File Structure

Place your custom animation files in these locations:

```
Order of the stone/
└── assets/
    └── player/
        ├── animations/
        │   ├── standing.gif     ← PUT YOUR STANDING ANIMATION HERE (breathing/idle)
        │   ├── walking.gif      ← PUT YOUR WALKING ANIMATION HERE (movement)
        │   ├── jumping.gif      ← PUT YOUR JUMPING ANIMATION HERE (jumping up)
        │   ├── falling.gif      ← PUT YOUR FALLING ANIMATION HERE (falling down)
        │   ├── fighting.gif     ← PUT YOUR FIGHTING ANIMATION HERE (combat)
        │   ├── breaking.gif     ← PUT YOUR BREAKING ANIMATION HERE (mining)
        │   └── placing.gif      ← PUT YOUR PLACING ANIMATION HERE (building)
        └── player.gif           ← Your default idle animation (fallback)
```

### 🎮 Animation Controls

Once you add your custom .gif files, you can trigger them with these keys:

- **No input**: Standing (automatically triggers standing animation - breathing/idle effects)
- **W, A, S, D**: Movement (automatically triggers walking animation)
- **SPACE**: Jump (triggers jumping animation)
- **Falling**: Automatically triggers falling animation when moving down
- **LEFT CLICK**: Attack/Fight (triggers fighting animation)
- **Mining blocks**: Automatically triggers breaking animation
- **Building blocks**: Automatically triggers placing animation

### 📐 File Requirements

- **Format**: .gif files (animated GIFs work best)
- **Size**: Any size (will be automatically scaled to 32x32 pixels)
- **Naming**: Must be exactly `walking.gif`, `fighting.gif`, `jumping.gif`
- **Location**: Must be in `assets/player/animations/` folder

### 🔧 How It Works

1. The game automatically checks for your custom .gif files when it starts
2. If found, it loads them as animations
3. If not found, it creates colorful placeholder animations:
   - 🟦 Blue = Idle
   - 🟢 Green = Walking  
   - 🔴 Red = Fighting
   - 🟡 Yellow = Jumping

### 📝 Step-by-Step Instructions

1. **Create your animations** in your favorite animation software
2. **Export as .gif files** with these exact names:
   - `walking.gif`
   - `fighting.gif` 
   - `jumping.gif`
3. **Place them** in the `assets/player/animations/` folder
4. **Run the game** - your animations will load automatically!

### 🎨 Animation Tips

- **Frame Rate**: 8-12 frames work well for smooth animation
- **Loop**: Make sure your animations loop seamlessly
- **Style**: Match the pixel art style of the game (32x32 works best)
- **Colors**: Use colors that stand out against the game background

### 🐛 Troubleshooting

If your animations don't show up:

1. **Check file names** - they must be exactly `walking.gif`, `fighting.gif`, `jumping.gif`
2. **Check location** - files must be in `assets/player/animations/` folder
3. **Check console** - the game prints messages about loading animations
4. **File format** - make sure they're valid .gif files

### 🎭 Example Console Output

When the game loads, you should see:
```
🎬 Setting up player animations...
📁 Looking for custom .gif files in assets/player/animations/
🎬 Loading standing from GIF: assets/player/animations/standing.gif
✅ Successfully loaded standing.gif!
🎬 Loading walking from GIF: assets/player/animations/walking.gif
✅ Successfully loaded walking.gif!
🎬 Loading jumping from GIF: assets/player/animations/jumping.gif
✅ Successfully loaded jumping.gif!
🎬 Loading falling from GIF: assets/player/animations/falling.gif
✅ Successfully loaded falling.gif!
🎬 Loading fighting from GIF: assets/player/animations/fighting.gif
✅ Successfully loaded fighting.gif!
🎬 Loading breaking from GIF: assets/player/animations/breaking.gif
✅ Successfully loaded breaking.gif!
🎬 Loading placing from GIF: assets/player/animations/placing.gif
✅ Successfully loaded placing.gif!
✅ Player animations setup complete!
```

### 🚀 Advanced Features

- **Multiple Frames**: If you want to use individual frame files instead of GIFs, you can name them:
  - `walking_1.png`, `walking_2.png`, `walking_3.png`, etc.
  - `fighting_1.png`, `fighting_2.png`, `fighting_3.png`, etc.
  - `jumping_1.png`, `jumping_2.png`, `jumping_3.png`, etc.

- **Animation Speed**: The system automatically sets good speeds, but you can modify the code to adjust timing

Have fun creating your custom animations! 🎨✨
