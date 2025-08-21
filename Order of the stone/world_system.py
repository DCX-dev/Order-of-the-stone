#!/usr/bin/env python3
"""
🌍 Modern World System for Order of the Stone
A clean, efficient world management system with proper saving and loading
"""

import os
import json
import time
import random
import pygame
# Using MinecraftWorldGenerator directly in _generate_world_data
import shutil
from typing import Dict, List, Optional, Tuple, Any

class WorldSystem:
    """Modern world management system with proper persistence"""
    
    def __init__(self, save_dir: str = "save_data"):
        self.save_dir = save_dir
        self.worlds_dir = os.path.join(save_dir, "worlds")
        self.current_world_name: Optional[str] = None
        self.current_world_data: Dict[str, Any] = {}
        self.world_list: List[Dict[str, Any]] = []
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load existing worlds
        self._load_world_list()
        
        print(f"🌍 World system initialized with {len(self.world_list)} worlds")
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.worlds_dir, exist_ok=True)
        os.makedirs(os.path.join(self.save_dir, "previews"), exist_ok=True)
    
    def _load_world_list(self):
        """Load the list of existing worlds"""
        self.world_list = []
        
        if not os.path.exists(self.worlds_dir):
            return
        
        try:
            # Load world list file
            world_list_file = os.path.join(self.save_dir, "world_list.json")
            if os.path.exists(world_list_file):
                with open(world_list_file, 'r') as f:
                    self.world_list = json.load(f)
            
            # Verify each world still exists
            valid_worlds = []
            for world_info in self.world_list:
                world_file = os.path.join(self.worlds_dir, f"{world_info['name']}.json")
                if os.path.exists(world_file):
                    valid_worlds.append(world_info)
                else:
                    print(f"⚠️ World file missing: {world_info['name']}")
            
            self.world_list = valid_worlds
            self._save_world_list()
            
        except Exception as e:
            print(f"❌ Error loading world list: {e}")
            self.world_list = []
    
    def _save_world_list(self):
        """Save the world list to disk"""
        try:
            world_list_file = os.path.join(self.save_dir, "world_list.json")
            with open(world_list_file, 'w') as f:
                json.dump(self.world_list, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving world list: {e}")
    
    def create_world(self, name: str, seed: Optional[str] = None) -> bool:
        """Create a new world with the given name and seed"""
        try:
            # Validate world name
            if not name or len(name) > 32:
                print("❌ Invalid world name")
                return False
            
            # Check if world already exists
            if self.world_exists(name):
                print(f"❌ World '{name}' already exists")
                return False
            
            # Generate world data
            world_data = self._generate_world_data(name, seed)
            
            # Set as current world data
            self.current_world_name = name
            self.current_world_data = world_data
            
            # Save world to disk
            world_file = os.path.join(self.worlds_dir, f"{name}.json")
            with open(world_file, 'w') as f:
                json.dump(world_data, f, indent=2)
            
            # Add to world list
            world_info = {
                "name": name,
                "created": time.time(),
                "last_played": time.time(),
                "seed": seed or "random",
                "size": len(world_data.get("blocks", {})),
                "player_x": world_data.get("player", {}).get("x", 0),
                "player_y": world_data.get("player", {}).get("y", 0)
            }
            
            self.world_list.append(world_info)
            self._save_world_list()
            
            print(f"✅ World '{name}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating world: {e}")
            return False
    
    def _generate_world_data(self, name: str, seed: Optional[str] = None) -> Dict[str, Any]:
        """Generate initial world data using the world_gen module."""
        try:
            from world_gen import generate_world
            
            print(f"🌍 Generating new world: {name}")
            world_data = generate_world(seed=seed, world_width=200)
            
            # Add world metadata
            world_data["name"] = name
            world_data["created"] = time.time()
            world_data["last_played"] = time.time()
            
            # Ensure player data exists
            if "player" not in world_data:
                world_data["player"] = {
                    "x": 0.0, "y": 48.0, "vel_y": 0, "on_ground": False,
                    "health": 10, "max_health": 10, "hunger": 100, "max_hunger": 100,
                    "stamina": 100, "max_stamina": 100, "inventory": [], "backpack": [],
                    "selected": 0, "username": "", "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
                }
            
            # Ensure world settings exist
            if "world_settings" not in world_data:
                world_data["world_settings"] = {
                    "time": time.time(),
                    "day": True,
                    "weather": "clear"
                }
            
            print(f"✅ World '{name}' generated successfully with {len(world_data.get('blocks', {}))} blocks")
            return world_data
            
        except Exception as e:
            print(f"❌ Error generating world data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_world(self, name: str) -> bool:
        """Load a world by name"""
        try:
            world_file = os.path.join(self.worlds_dir, f"{name}.json")
            if not os.path.exists(world_file):
                print(f"❌ World file not found: {name}")
                return False
            
            with open(world_file, 'r') as f:
                world_data = json.load(f)
            
            # Validate and fix world data structure
            world_data = self._validate_and_fix_world_data(world_data)
            
            self.current_world_name = name
            self.current_world_data = world_data
            
            # Update last played time
            self._update_world_info(name, "last_played", time.time())
            
            print(f"✅ World '{name}' loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error loading world: {e}")
            return False
    
    def _validate_and_fix_world_data(self, world_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix world data to ensure compatibility"""
        if not isinstance(world_data, dict):
            print("❌ Invalid world data, creating new structure")
            return self._generate_world_data("Recovery World")
        
        # Ensure required fields exist
        required_fields = ["name", "blocks", "entities", "player", "world_settings"]
        for field in required_fields:
            if field not in world_data:
                print(f"⚠️ Adding missing field: {field}")
                if field == "blocks":
                    world_data[field] = {}
                elif field == "entities":
                    world_data[field] = []
                elif field == "player":
                    world_data[field] = {}
                elif field == "world_settings":
                    world_data[field] = {"time": 0, "day": True, "weather": "clear"}
            else:
                # Field exists, validate its type
                if field == "blocks" and not isinstance(world_data[field], dict):
                    print(f"⚠️ Invalid blocks field type, resetting to empty dict")
                    world_data[field] = {}
                elif field == "entities" and not isinstance(world_data[field], list):
                    print(f"⚠️ Invalid entities field type, resetting to empty list")
                    world_data[field] = []
                elif field == "player" and not isinstance(world_data[field], dict):
                    print(f"⚠️ Invalid player field type, resetting to empty dict")
                    world_data[field] = {}
                elif field == "world_settings" and not isinstance(world_data[field], dict):
                    print(f"⚠️ Invalid world_settings field type, resetting to defaults")
                    world_data[field] = {"time": 0, "day": True, "weather": "clear"}
        
        # Fix player data structure
        player = world_data.get("player", {})
        if not isinstance(player, dict):
            print("⚠️ Invalid player data, resetting")
            player = {}
            world_data["player"] = player
        
        # Handle legacy data structure (hotbar -> inventory)
        if "hotbar" in player and "inventory" not in player:
            print("🔄 Converting legacy hotbar to inventory")
            player["inventory"] = player.pop("hotbar")
        
        # Ensure player has all required fields
        player_defaults = {
            "x": 0.0, "y": 48.0, "vel_y": 0, "on_ground": False,
            "health": 10, "max_health": 10, "hunger": 100, "max_hunger": 100,
            "stamina": 100, "max_stamina": 100, "inventory": [], "backpack": [],
            "selected": 0, "username": "", "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
        }
        
        for key, default_value in player_defaults.items():
            if key not in player:
                player[key] = default_value
                print(f"⚠️ Added missing player field: {key}")
        
        # Ensure inventory and backpack are lists
        if not isinstance(player.get("inventory"), list):
            player["inventory"] = []
        if not isinstance(player.get("backpack"), list):
            player["backpack"] = [None] * 27
        
        # Ensure armor is a dict
        if not isinstance(player.get("armor"), dict):
            player["armor"] = {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
        
        return world_data
    
    def save_world(self) -> bool:
        """Save the current world"""
        if not self.current_world_name or not self.current_world_data:
            print("❌ No world loaded to save")
            return False
        
        try:
            # Validate world data structure
            if not isinstance(self.current_world_data, dict):
                print("❌ Invalid world data structure")
                return False
            
            # Ensure required fields exist and have correct types
            required_fields = {
                "name": dict,
                "blocks": dict,
                "entities": list,
                "player": dict,
                "world_settings": dict
            }
            
            for field, expected_type in required_fields.items():
                if field not in self.current_world_data:
                    print(f"⚠️ Adding missing field: {field}")
                    if field == "blocks":
                        self.current_world_data[field] = {}
                    elif field == "entities":
                        self.current_world_data[field] = []
                    elif field == "player":
                        self.current_world_data[field] = {}
                    elif field == "world_settings":
                        self.current_world_data[field] = {"time": 0, "day": True, "weather": "clear"}
                elif not isinstance(self.current_world_data[field], expected_type):
                    print(f"⚠️ Fixing field type: {field} (expected {expected_type.__name__})")
                    if field == "blocks":
                        self.current_world_data[field] = {}
                    elif field == "entities":
                        self.current_world_data[field] = []
                    elif field == "player":
                        self.current_world_data[field] = {}
                    elif field == "world_settings":
                        self.current_world_data[field] = {"time": 0, "day": True, "weather": "clear"}
            
            # Ensure player data has the correct structure
            player = self.current_world_data.get("player", {})
            if not isinstance(player, dict):
                print("❌ Invalid player data structure, resetting")
                player = {}
                self.current_world_data["player"] = player
            
            # Ensure player has required fields with defaults
            player_defaults = {
                "x": 0.0, "y": 48.0, "vel_y": 0, "on_ground": False,
                "health": 10, "max_health": 10, "hunger": 100, "max_hunger": 100,
                "stamina": 100, "max_stamina": 100, "inventory": [], "backpack": [],
                "selected": 0, "username": "", "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
            }
            
            for key, default_value in player_defaults.items():
                if key not in player:
                    player[key] = default_value
                    print(f"⚠️ Added missing player field: {key}")
                elif key in ["inventory", "backpack"] and not isinstance(player[key], list):
                    player[key] = default_value
                    print(f"⚠️ Fixed player field type: {key}")
                elif key == "armor" and not isinstance(player[key], dict):
                    player[key] = default_value
                    print(f"⚠️ Fixed player field type: {key}")
            
            # Update save time
            self.current_world_data["last_saved"] = time.time()
            
            # Save world data
            world_file = os.path.join(self.worlds_dir, f"{self.current_world_name}.json")
            
            # Create backup before saving
            backup_file = world_file + ".backup"
            if os.path.exists(world_file):
                try:
                    shutil.copy2(world_file, backup_file)
                except Exception as e:
                    print(f"⚠️ Could not create backup: {e}")
            
            # Save with proper formatting
            with open(world_file, 'w') as f:
                json.dump(self.current_world_data, f, indent=2, ensure_ascii=False)
            
            # Remove backup if save was successful
            if os.path.exists(backup_file):
                try:
                    os.remove(backup_file)
                except:
                    pass
            
            # Update world info
            self._update_world_info(self.current_world_name, "last_saved", time.time())
            
            print(f"✅ World '{self.current_world_name}' saved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error saving world: {e}")
            
            # Try to restore from backup if available
            backup_file = os.path.join(self.worlds_dir, f"{self.current_world_name}.json.backup")
            if os.path.exists(backup_file):
                try:
                    shutil.copy2(backup_file, world_file)
                    print("🔄 Restored world from backup")
                except Exception as restore_error:
                    print(f"❌ Failed to restore from backup: {restore_error}")
            
            return False
    
    def _update_world_info(self, world_name: str, key: str, value: Any):
        """Update a specific field in world info"""
        for world_info in self.world_list:
            if world_info["name"] == world_name:
                world_info[key] = value
                break
        self._save_world_list()
    
    def delete_world(self, name: str) -> bool:
        """Delete a world completely"""
        try:
            # Remove from world list
            self.world_list = [w for w in self.world_list if w["name"] != name]
            
            # Delete world file
            world_file = os.path.join(self.worlds_dir, f"{name}.json")
            if os.path.exists(world_file):
                os.remove(world_file)
            
            # Delete preview if it exists
            preview_file = os.path.join(self.save_dir, "previews", f"{name}_preview.png")
            if os.path.exists(preview_file):
                os.remove(preview_file)
            
            # Save updated world list
            self._save_world_list()
            
            # If this was the current world, clear it
            if self.current_world_name == name:
                self.current_world_name = None
                self.current_world_data = {}
            
            print(f"✅ World '{name}' deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting world: {e}")
            return False
    
    def world_exists(self, name: str) -> bool:
        """Check if a world exists"""
        return any(w["name"] == name for w in self.world_list)
    
    def get_world_list(self) -> List[Dict[str, Any]]:
        """Get the list of available worlds"""
        return self.world_list.copy()
    
    def get_current_world_name(self) -> Optional[str]:
        """Get the name of the currently loaded world"""
        return self.current_world_name
    
    def get_current_world_data(self) -> Dict[str, Any]:
        """Get the data of the currently loaded world"""
        return self.current_world_data.copy()
    
    def set_block(self, x: int, y: int, block_type: str):
        """Set a block in the current world"""
        if not self.current_world_data:
            return
        
        key = f"{x},{y}"
        if block_type is None:
            # Remove block
            if key in self.current_world_data["blocks"]:
                del self.current_world_data["blocks"][key]
        else:
            # Set block
            self.current_world_data["blocks"][key] = block_type
    
    def get_block(self, x: int, y: int) -> Optional[str]:
        """Get a block from the current world"""
        if not self.current_world_data:
            return None
        
        key = f"{x},{y}"
        return self.current_world_data["blocks"].get(key)
    
    def update_player_data(self, player_data: Dict[str, Any]):
        """Update player data in the current world"""
        if not self.current_world_data:
            return
        
        self.current_world_data["player"].update(player_data)
    
    def get_player_data(self) -> Dict[str, Any]:
        """Get player data from the current world"""
        if not self.current_world_data:
            return {}
        
        return self.current_world_data["player"].copy()
    
    def add_entity(self, entity: Dict[str, Any]):
        """Add an entity to the current world"""
        if not self.current_world_data:
            return
        
        self.current_world_data["entities"].append(entity)
    
    def remove_entity(self, entity: Dict[str, Any]):
        """Remove an entity from the current world"""
        if not self.current_world_data:
            return
        
        if entity in self.current_world_data["entities"]:
            self.current_world_data["entities"].remove(entity)
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all entities from the current world"""
        if not self.current_world_data:
            return []
        
        return self.current_world_data["entities"].copy()
    
    def create_world_preview(self, world_name: str, surface: pygame.Surface) -> bool:
        """Create a preview image for a world"""
        try:
            preview_dir = os.path.join(self.save_dir, "previews")
            os.makedirs(preview_dir, exist_ok=True)
            
            preview_file = os.path.join(preview_dir, f"{world_name}_preview.png")
            pygame.image.save(surface, preview_file)
            
            print(f"✅ World preview created: {preview_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating world preview: {e}")
            return False
    
    def auto_save(self):
        """Auto-save the current world if it's been modified"""
        if self.current_world_name and self.current_world_data:
            # Check if enough time has passed since last save
            last_saved = self.current_world_data.get("last_saved", 0)
            if time.time() - last_saved > 300:  # 5 minutes
                self.save_world()
    
    def close_world(self):
        """Close the current world and save it"""
        if self.current_world_name:
            self.save_world()
            self.current_world_name = None
            self.current_world_data = {}
            print("🌍 World closed")
