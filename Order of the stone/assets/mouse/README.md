# Mouse Folder

This folder contains custom mouse cursor images for the game.

## Required Files

Place your custom mouse cursor image in this folder:

- `mouse.png` - Custom mouse cursor image (any size - will be resized to 50%)

## File Format

- **PNG** format recommended
- **Any size** - the game will automatically resize it to 50% of original size
- Transparent background (alpha channel)
- Clear, visible design for gameplay

## How It Works

The game will automatically:
1. Load the custom mouse cursor from this folder
2. Resize it to 50% of the original size (makes it smaller)
3. Hide the default system cursor
4. Draw the custom cursor at the mouse position
5. Follow the mouse movement in real-time

## Example

```
mouse/
├── mouse.png
└── README.md
```

## Notes

- The cursor will be drawn on top of all game elements
- If the image file is not found, the game will use the default system cursor
- The cursor position is updated every frame for smooth movement
