# Example Mod for Order of the Stone
# This demonstrates how to create mods using the new mod system

def initialize(api):
    """Called when the mod is loaded"""
    api.log("Example mod is initializing...")
    
    # Register a custom item
    api.register_item("magic_staff", 
                     name="Magic Staff",
                     description="A powerful magical weapon",
                     damage=15,
                     durability=100)
    
    # Register a custom block
    api.register_block("magic_crystal",
                      name="Magic Crystal",
                      hardness=3.0,
                      light_level=8,
                      transparent=True)
    
    # Add a custom texture
    api.add_texture("magic_staff", "textures/magic_staff.png")
    api.add_texture("magic_crystal", "textures/magic_crystal.png")
    
    api.log("Example mod initialized successfully!")

def on_game_start():
    """Called when the game starts"""
    print("[Example Mod] Game started! Magic is now available!")

def on_player_move(player_data):
    """Called when the player moves"""
    # This hook would receive player position, health, etc.
    pass

def on_block_break(block_type, x, y, player_data):
    """Called when a block is broken"""
    if block_type == "magic_crystal":
        print(f"[Example Mod] Magic crystal broken at ({x}, {y})!")

def on_block_place(block_type, x, y, player_data):
    """Called when a block is placed"""
    if block_type == "magic_crystal":
        print(f"[Example Mod] Magic crystal placed at ({x}, {y})!")

def on_item_use(item_type, player_data):
    """Called when an item is used"""
    if item_type == "magic_staff":
        print("[Example Mod] Magic staff used! Casting spell...")

def on_chest_open(chest_pos, player_data):
    """Called when a chest is opened"""
    print(f"[Example Mod] Chest opened at {chest_pos}")

def on_chest_close(chest_pos, player_data):
    """Called when a chest is closed"""
    print(f"[Example Mod] Chest closed at {chest_pos}")

def on_player_damage(damage, player_data):
    """Called when player takes damage"""
    print(f"[Example Mod] Player took {damage} damage!")

def on_player_heal(heal_amount, player_data):
    """Called when player heals"""
    print(f"[Example Mod] Player healed {heal_amount} health!")

def on_world_generate(chunk_x, chunk_y):
    """Called when a new world chunk is generated"""
    print(f"[Example Mod] Generating world chunk at ({chunk_x}, {chunk_y})")

def on_tick():
    """Called every game tick"""
    # This would be called every frame/tick
    pass

def on_key_press(key, player_data):
    """Called when a key is pressed"""
    if key == "F1":
        print("[Example Mod] F1 pressed - Magic menu activated!")

def on_mouse_click(button, x, y, player_data):
    """Called when mouse is clicked"""
    print(f"[Example Mod] Mouse {button} clicked at ({x}, {y})")

def on_death(player_data):
    """Called when player dies"""
    print("[Example Mod] Player died! Magic powers fading...")

def on_respawn(player_data):
    """Called when player respawns"""
    print("[Example Mod] Player respawned! Magic powers restored!")
