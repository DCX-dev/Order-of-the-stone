# Mod System for Order of the Stone
# This allows players to create mods without modifying the main game files

import os
import sys
import importlib.util
import json
import traceback
from typing import Dict, List, Any, Callable

class ModManager:
    """Manages loading and running mods for the game"""
    
    def __init__(self):
        self.mods: Dict[str, 'Mod'] = {}
        self.mod_apis: Dict[str, 'ModAPI'] = {}
        self.hooks: Dict[str, List[Callable]] = {
            'on_game_start': [],
            'on_player_move': [],
            'on_block_break': [],
            'on_block_place': [],
            'on_item_use': [],
            'on_chest_open': [],
            'on_chest_close': [],
            'on_player_damage': [],
            'on_player_heal': [],
            'on_world_generate': [],
            'on_tick': [],
            'on_key_press': [],
            'on_mouse_click': [],
            'on_death': [],
            'on_respawn': []
        }
        self.registered_items: Dict[str, Dict[str, Any]] = {}
        self.registered_blocks: Dict[str, Dict[str, Any]] = {}
        self.registered_entities: Dict[str, Dict[str, Any]] = {}
        self.custom_textures: Dict[str, str] = {}
        self.custom_sounds: Dict[str, str] = {}
        
    def load_mods(self, mods_directory: str = "mods"):
        """Load all mods from the specified directory"""
        if not os.path.exists(mods_directory):
            print(f"[Mod System] No mods directory found at {mods_directory}")
            return
            
        print(f"[Mod System] Loading mods from {mods_directory}")
        
        for mod_folder in os.listdir(mods_directory):
            mod_path = os.path.join(mods_directory, mod_folder)
            if os.path.isdir(mod_path):
                self.load_mod(mod_folder, mod_path)
                
        print(f"[Mod System] Loaded {len(self.mods)} mods")
    
    def load_mod(self, mod_id: str, mod_path: str):
        """Load a single mod from its directory"""
        try:
            # Check for mod.json configuration
            config_path = os.path.join(mod_path, "mod.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {"name": mod_id, "version": "1.0", "description": "No description"}
            
            # Check for main.py entry point
            main_path = os.path.join(mod_path, "main.py")
            if not os.path.exists(main_path):
                print(f"[Mod System] Skipping {mod_id}: no main.py found")
                return
                
            # Load the mod module
            spec = importlib.util.spec_from_file_location(f"mod_{mod_id}", main_path)
            if not spec or not spec.loader:
                print(f"[Mod System] Failed to load {mod_id}: invalid module spec")
                return
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create mod instance
            mod = Mod(mod_id, mod_path, config, module)
            self.mods[mod_id] = mod
            
            # Create mod API
            api = ModAPI(mod_id, mod_path, self)
            self.mod_apis[mod_id] = api
            
            # Initialize the mod
            if hasattr(module, 'initialize'):
                try:
                    module.initialize(api)
                    print(f"[Mod System] Initialized {mod_id} v{config.get('version', '1.0')}")
                except Exception as e:
                    print(f"[Mod System] Error initializing {mod_id}: {e}")
                    traceback.print_exc()
            
            # Register hooks
            self.register_mod_hooks(mod_id, module)
            
        except Exception as e:
            print(f"[Mod System] Failed to load mod {mod_id}: {e}")
            traceback.print_exc()
    
    def register_mod_hooks(self, mod_id: str, module):
        """Register all hooks that the mod provides"""
        for hook_name in self.hooks.keys():
            if hasattr(module, hook_name):
                hook_func = getattr(module, hook_name)
                if callable(hook_func):
                    self.hooks[hook_name].append(hook_func)
                    print(f"[Mod System] {mod_id} registered hook: {hook_name}")
    
    def call_hook(self, hook_name: str, *args, **kwargs):
        """Call all registered hooks for a specific event"""
        if hook_name in self.hooks:
            for hook in self.hooks[hook_name]:
                try:
                    hook(*args, **kwargs)
                except Exception as e:
                    print(f"[Mod System] Hook {hook_name} error: {e}")
                    traceback.print_exc()
    
    def register_item(self, item_id: str, **properties):
        """Register a new item type"""
        self.registered_items[item_id] = properties
        print(f"[Mod System] Registered item: {item_id}")
    
    def register_block(self, block_id: str, **properties):
        """Register a new block type"""
        self.registered_blocks[block_id] = properties
        print(f"[Mod System] Registered block: {block_id}")
    
    def register_entity(self, entity_id: str, **properties):
        """Register a new entity type"""
        self.registered_entities[entity_id] = properties
        print(f"[Mod System] Registered entity: {entity_id}")
    
    def add_texture(self, texture_id: str, texture_path: str):
        """Add a custom texture"""
        self.custom_textures[texture_id] = texture_path
        print(f"[Mod System] Added texture: {texture_id} -> {texture_path}")
    
    def add_sound(self, sound_id: str, sound_path: str):
        """Add a custom sound"""
        self.custom_sounds[sound_id] = sound_path
        print(f"[Mod System] Added sound: {sound_id} -> {sound_path}")

class Mod:
    """Represents a loaded mod"""
    
    def __init__(self, mod_id: str, mod_path: str, config: Dict[str, Any], module):
        self.mod_id = mod_id
        self.mod_path = mod_path
        self.config = config
        self.module = module
        self.enabled = True

class ModAPI:
    """API that mods can use to interact with the game"""
    
    def __init__(self, mod_id: str, mod_path: str, mod_manager: ModManager):
        self.mod_id = mod_id
        self.mod_path = mod_path
        self.mod_manager = mod_manager
    
    def register_item(self, item_id: str, **properties):
        """Register a new item type"""
        self.mod_manager.register_item(item_id, **properties)
    
    def register_block(self, block_id: str, **properties):
        """Register a new block type"""
        self.mod_manager.register_block(block_id, **properties)
    
    def register_entity(self, entity_id: str, **properties):
        """Register a new entity type"""
        self.mod_manager.register_entity(entity_id, **properties)
    
    def add_texture(self, texture_id: str, texture_path: str):
        """Add a custom texture (relative to mod directory)"""
        full_path = os.path.join(self.mod_path, texture_path)
        self.mod_manager.add_texture(texture_id, full_path)
    
    def add_sound(self, sound_id: str, sound_path: str):
        """Add a custom sound (relative to mod directory)"""
        full_path = os.path.join(self.mod_path, sound_path)
        self.mod_manager.add_sound(sound_id, full_path)
    
    def get_mod_path(self, *parts: str) -> str:
        """Get a path relative to this mod's directory"""
        return os.path.join(self.mod_path, *parts)
    
    def log(self, message: str):
        """Log a message from this mod"""
        print(f"[{self.mod_id}] {message}")
    
    def get_game_data(self) -> Dict[str, Any]:
        """Get access to game data (read-only)"""
        # This would be populated by the main game
        return {}
    
    def set_game_data(self, key: str, value: Any):
        """Set game data (if allowed)"""
        # This would be controlled by the main game
        pass

# Global mod manager instance
mod_manager = ModManager()

# Convenience functions for the main game
def load_all_mods(mods_dir: str = "mods"):
    """Load all mods - call this from the main game"""
    mod_manager.load_mods(mods_dir)

def call_mod_hook(hook_name: str, *args, **kwargs):
    """Call a mod hook - use this in the main game"""
    mod_manager.call_hook(hook_name, *args, **kwargs)

def get_mod_items() -> Dict[str, Dict[str, Any]]:
    """Get all items registered by mods"""
    return mod_manager.registered_items.copy()

def get_mod_blocks() -> Dict[str, Dict[str, Any]]:
    """Get all blocks registered by mods"""
    return mod_manager.registered_blocks.copy()

def get_mod_entities() -> Dict[str, Dict[str, Any]]:
    """Get all entities registered by mods"""
    return mod_manager.registered_entities.copy()

def get_mod_textures() -> Dict[str, str]:
    """Get all textures added by mods"""
    return mod_manager.custom_textures.copy()

def get_mod_sounds() -> Dict[str, str]:
    """Get all sounds added by mods"""
    return mod_manager.custom_sounds.copy()
