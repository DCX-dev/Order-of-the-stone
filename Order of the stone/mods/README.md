# Mod System for Order of the Stone

This mod system allows players to create and install mods without modifying the main game files. Mods can add new items, blocks, entities, textures, sounds, and game mechanics.

## How It Works

The mod system uses a **hook-based architecture** where mods can register functions to be called when specific game events occur. This keeps mods separate from the main game code while allowing them to extend functionality.

## Creating a Mod

### 1. Mod Structure
```
mods/
├── your_mod_name/
│   ├── mod.json          # Mod configuration
│   ├── main.py           # Main mod code
│   ├── textures/         # Custom textures (optional)
│   ├── sounds/          # Custom sounds (optional)
│   └── README.md         # Mod documentation (optional)
```

### 2. Mod Configuration (mod.json)
```json
{
    "name": "Your Mod Name",
    "version": "1.0.0",
    "description": "What your mod does",
    "author": "Your Name",
    "main": "main.py",
    "dependencies": [],
    "tags": ["category1", "category2"]
}
```

### 3. Main Mod Code (main.py)
```python
def initialize(api):
    """Called when the mod is loaded"""
    # Register new items, blocks, entities
    # Add custom textures and sounds
    pass

def on_game_start():
    """Called when the game starts"""
    pass

def on_player_move(player_data):
    """Called when the player moves"""
    pass

# ... more hooks
```

## Available Hooks

### Game Lifecycle
- `initialize(api)` - Called when mod is loaded
- `on_game_start()` - Called when game starts
- `on_tick()` - Called every game tick/frame

### Player Events
- `on_player_move(player_data)` - Player movement
- `on_player_damage(damage, player_data)` - Player takes damage
- `on_player_heal(heal_amount, player_data)` - Player heals
- `on_death(player_data)` - Player dies
- `on_respawn(player_data)` - Player respawns

### World Events
- `on_block_break(block_type, x, y, player_data)` - Block broken
- `on_block_place(block_type, x, y, player_data)` - Block placed
- `on_world_generate(chunk_x, chunk_y)` - New chunk generated

### Item Events
- `on_item_use(item_type, player_data)` - Item used
- `on_chest_open(chest_pos, player_data)` - Chest opened
- `on_chest_close(chest_pos, player_data)` - Chest closed

### Input Events
- `on_key_press(key, player_data)` - Key pressed
- `on_mouse_click(button, x, y, player_data)` - Mouse clicked

## Mod API Functions

### Registration
```python
# Register new items
api.register_item("item_id", name="Item Name", damage=10)

# Register new blocks
api.register_block("block_id", hardness=2.0, transparent=False)

# Register new entities
api.register_entity("entity_id", health=20, speed=1.0)
```

### Assets
```python
# Add custom textures
api.add_texture("texture_id", "textures/my_texture.png")

# Add custom sounds
api.add_sound("sound_id", "sounds/my_sound.wav")
```

### Utilities
```python
# Get mod directory path
mod_path = api.get_mod_path("textures", "icon.png")

# Log messages
api.log("This is a mod message")

# Access game data (read-only)
game_data = api.get_game_data()
```

## Example Mod

See `example_mod/` for a complete working example that demonstrates:
- Mod configuration
- Item and block registration
- Hook usage
- Custom textures
- Event handling

## Installing Mods

1. **Download or create** a mod folder
2. **Place the mod folder** in the `mods/` directory
3. **Restart the game** - mods are loaded automatically
4. **Check the console** for mod loading messages

## Mod Development Tips

### 1. Keep Mods Independent
- Don't rely on other mods unless specified in dependencies
- Use unique IDs for your items/blocks to avoid conflicts

### 2. Error Handling
- Always wrap your code in try-catch blocks
- Use `api.log()` for debugging
- Don't crash the game if something goes wrong

### 3. Performance
- Keep `on_tick()` functions lightweight
- Don't perform heavy operations every frame
- Use hooks only when necessary

### 4. Compatibility
- Test your mod with different game versions
- Don't assume specific game mechanics exist
- Use the API functions provided

## Troubleshooting

### Mod Not Loading
- Check that `main.py` exists in your mod folder
- Verify `mod.json` is valid JSON
- Look for error messages in the console

### Mod Crashes
- Check for syntax errors in your Python code
- Ensure all required functions exist
- Test with minimal code first

### Items/Blocks Not Appearing
- Make sure you're calling the registration functions
- Check that texture files exist and are valid
- Verify item/block IDs are unique

## Advanced Features

### Custom Rendering
Mods can register custom rendering functions for special blocks or entities.

### Custom UI
The system supports adding custom user interface elements.

### Data Persistence
Mods can save and load their own data files.

### Network Support
Future versions will support multiplayer mod synchronization.

## Support

For help with mod development:
1. Check the example mod code
2. Look at console error messages
3. Test with simple mods first
4. Ask in the community forums

## License

Mods are subject to the same license as the main game. Respect the original creators' work.
