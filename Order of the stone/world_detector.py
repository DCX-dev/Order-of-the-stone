import os
import json
import time
from typing import List, Dict, Optional, Tuple
from world import World

class WorldDetector:
    """Automatically detects and manages world files in the save directory"""
    
    def __init__(self, save_dir: str = "save_data"):
        self.save_dir = save_dir
        self.max_worlds = 12
        self.worlds: List[World] = []
        self.legacy_save_exists = False
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self.scan_for_worlds()
    
    def scan_for_worlds(self):
        """Scan the save directory for all world files"""
        self.worlds = []
        self.legacy_save_exists = False
        
        try:
            # First check for legacy save.json
            legacy_save_path = os.path.join(self.save_dir, "save.json")
            if os.path.exists(legacy_save_path):
                try:
                    with open(legacy_save_path, 'r') as f:
                        legacy_data = json.load(f)
                    
                    # Create a special "Legacy Save" world
                    legacy_world = World("Legacy Save", "save.json")
                    legacy_world.created = time.time() - 86400  # Set to 1 day ago for sorting
                    legacy_world.last_modified = os.path.getmtime(legacy_save_path)
                    
                    # Update metadata from legacy save
                    if 'player' in legacy_data:
                        legacy_world.update_player_info(legacy_data['player'])
                        legacy_world.player_info = "Legacy save file"
                    
                    self.worlds.append(legacy_world)
                    self.legacy_save_exists = True
                    print("Legacy save.json detected and loaded")
                    
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error loading legacy save.json: {e}")
            
            # Look for world JSON files (World X.json format)
            for filename in os.listdir(self.save_dir):
                if filename.startswith("World ") and filename.endswith(".json"):
                    world_name = filename[:-5]  # Remove ".json"
                    filepath = os.path.join(self.save_dir, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            world_data = json.load(f)
                        
                        world = World(world_name, filename)
                        
                        if 'player' in world_data:
                            world.update_player_info(world_data['player'])
                        
                        # Get file modification time
                        world.last_modified = os.path.getmtime(filepath)
                        
                        self.worlds.append(world)
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error loading world {filename}: {e}")
                        # Create a basic world entry even if loading fails
                        world = World(world_name, filename)
                        self.worlds.append(world)
            
            # Sort worlds by last modified (most recent first)
            self.worlds.sort(key=lambda w: w.last_modified, reverse=True)
            
            print(f"Detected {len(self.worlds)} world(s)")
            
        except Exception as e:
            print(f"Error scanning for worlds: {e}")
    
    def get_all_worlds(self) -> List[World]:
        """Get all detected worlds"""
        return self.worlds.copy()
    
    def get_world_count(self) -> int:
        """Get the current number of worlds"""
        return len(self.worlds)
    
    def can_create_world(self) -> bool:
        """Check if a new world can be created"""
        return len(self.worlds) < self.max_worlds
    
    def get_available_slots(self) -> int:
        """Get number of available world slots"""
        return max(0, self.max_worlds - len(self.worlds))
    
    def get_world_by_name(self, name: str) -> Optional[World]:
        """Get a world by its name"""
        for world in self.worlds:
            if world.name == name:
                return world
        return None
    
    def get_world_by_filename(self, filename: str) -> Optional[World]:
        """Get a world by its filename"""
        for world in self.worlds:
            if world.filename == filename:
                return world
        return None
    
    def refresh_worlds(self):
        """Refresh the world list by re-scanning the directory"""
        self.scan_for_worlds()
    
    def get_world_info_for_display(self) -> List[Dict]:
        """Get world information formatted for UI display"""
        world_info_list = []
        
        for world in self.worlds:
            world_info = {
                'name': world.name,
                'filename': world.filename,
                'created': world.get_created_str(),
                'last_modified': world.get_last_modified_str(),
                'player_info': world.get_player_status(),
                'is_legacy': world.name == "Legacy Save"
            }
            world_info_list.append(world_info)
        
        return world_info_list
    
    def get_next_world_number(self) -> int:
        """Get the next available world number for naming"""
        world_number = 1
        while True:
            world_name = f"World {world_number}"
            if not any(world.name == world_name for world in self.worlds):
                return world_number
            world_number += 1
    
    def has_legacy_save(self) -> bool:
        """Check if legacy save.json exists"""
        return self.legacy_save_exists
    
    def get_legacy_save_path(self) -> str:
        """Get the path to legacy save.json"""
        return os.path.join(self.save_dir, "save.json")
    
    def cleanup_deleted_worlds(self):
        """Remove world entries for files that no longer exist"""
        worlds_to_remove = []
        
        for world in self.worlds:
            if world.filename == "save.json":
                # Legacy save - check if it still exists
                if not os.path.exists(self.get_legacy_save_path()):
                    worlds_to_remove.append(world)
            else:
                # Regular world - check if file exists
                filepath = os.path.join(self.save_dir, world.filename)
                if not os.path.exists(filepath):
                    worlds_to_remove.append(world)
        
        # Remove deleted worlds
        for world in worlds_to_remove:
            self.worlds.remove(world)
            print(f"Removed deleted world: {world.name}")
        
        # Re-sort after cleanup
        if worlds_to_remove:
            self.worlds.sort(key=lambda w: w.last_modified, reverse=True)
    
    def get_world_summary(self) -> Dict:
        """Get a summary of world detection status"""
        return {
            'total_worlds': len(self.worlds),
            'max_worlds': self.max_worlds,
            'available_slots': self.get_available_slots(),
            'can_create': self.can_create_world(),
            'has_legacy': self.has_legacy_save(),
            'worlds': [world.name for world in self.worlds]
        }
