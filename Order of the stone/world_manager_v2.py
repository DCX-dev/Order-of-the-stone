import os
import json
import time
from typing import List, Dict, Optional, Any
from world import World

class WorldManager:
    """Manages world creation, loading, and saving with a 12-world limit"""
    
    MAX_WORLDS = 12
    
    def __init__(self, save_dir: str = "save_data"):
        self.save_dir = save_dir
        self.worlds: List[World] = []
        self.current_world: Optional[World] = None
        
        # Ensure save directory exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self.load_worlds()
    
    def load_worlds(self):
        """Load existing worlds from save directory"""
        self.worlds = []
        
        try:
            # Look for world JSON files
            for filename in os.listdir(self.save_dir):
                if filename.startswith("world") and filename.endswith(".json"):
                    # Extract world name from filename
                    world_name = filename[:-5]  # Remove .json
                    
                    # Try to load world metadata
                    filepath = os.path.join(self.save_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            world_data = json.load(f)
                        
                        # Create world instance
                        world = World(world_name, filename)
                        
                        # Update metadata from save file
                        if 'player' in world_data:
                            world.update_player_info(world_data['player'])
                        
                        self.worlds.append(world)
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error loading world {filename}: {e}")
                        # Create basic world instance for corrupted files
                        world = World(world_name, filename)
                        self.worlds.append(world)
            
            # Sort worlds by last modified (newest first)
            self.worlds.sort(key=lambda w: w.last_modified, reverse=True)
            
        except Exception as e:
            print(f"Error loading worlds: {e}")
    
    def can_create_world(self) -> bool:
        """Check if we can create a new world (under 12 limit)"""
        return len(self.worlds) < self.MAX_WORLDS
    
    def get_available_slots(self) -> int:
        """Get number of available world slots"""
        return max(0, self.MAX_WORLDS - len(self.worlds))
    
    def create_world(self) -> Optional[World]:
        """Create a new world with auto-generated name"""
        if not self.can_create_world():
            return None
        
        # Generate a unique world name
        world_number = 1
        while True:
            world_name = f"World {world_number}"
            # Check if world name already exists
            name_exists = any(world.name == world_name for world in self.worlds)
            if not name_exists:
                break
            world_number += 1
        
        # Create the world instance
        world = World(world_name)
        
        # Create empty world data
        world_data = {
            'player': {
                'x': 10,
                'y': 0,
                'vel_y': 0,
                'on_ground': False,
                'health': 10,
                'hunger': 10,
                'inventory': [],
                'selected': 0
            },
            'world': {},
            'entities': [],
            'chest_inventories': {},
            'player_placed_chests': [],
            'created': time.time()
        }
        
        try:
            # Save the world file
            filepath = os.path.join(self.save_dir, world.filename)
            with open(filepath, 'w') as f:
                json.dump(world_data, f, indent=2)
            
            # Add to worlds list
            self.worlds.append(world)
            
            # Set as current world
            self.current_world = world
            
            return world
            
        except Exception as e:
            print(f"Error creating world: {e}")
            return None
    
    def load_world(self, world_name: str) -> Optional[Dict]:
        """Load a specific world's data"""
        for world in self.worlds:
            if world.name == world_name:
                try:
                    filepath = os.path.join(self.save_dir, world.filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    # Update world metadata
                    world.last_modified = time.time()
                    if 'player' in data:
                        world.update_player_info(data['player'])
                    
                    # Set as current world
                    self.current_world = world
                    
                    return data
                    
                except Exception as e:
                    print(f"Error loading world {world_name}: {e}")
                    return None
        
        return None
    
    def save_world(self, world_name: str, game_data: Dict) -> bool:
        """Save game data to a specific world"""
        for world in self.worlds:
            if world.name == world_name:
                try:
                    filepath = os.path.join(self.save_dir, world.filename)
                    
                    # Update world metadata
                    world.last_modified = time.time()
                    if 'player' in game_data:
                        world.update_player_info(game_data['player'])
                    
                    # Save the game data
                    with open(filepath, 'w') as f:
                        json.dump(game_data, f, indent=2)
                    
                    return True
                    
                except Exception as e:
                    print(f"Error saving world {world_name}: {e}")
                    return False
        
        return False
    
    def delete_world(self, world_name: str) -> bool:
        """Delete a world"""
        for world in self.worlds[:]:
            if world.name == world_name:
                try:
                    # Remove world file
                    filepath = os.path.join(self.save_dir, world.filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    
                    # Remove from worlds list
                    self.worlds.remove(world)
                    
                    # Clear current world if it was deleted
                    if self.current_world == world:
                        self.current_world = None
                    
                    return True
                    
                except Exception as e:
                    print(f"Error deleting world {world_name}: {e}")
                    return False
        
        return False
    
    def get_world_names(self) -> List[str]:
        """Get list of all world names"""
        return [world.name for world in self.worlds]
    
    def has_worlds(self) -> bool:
        """Check if there are any existing worlds"""
        return len(self.worlds) > 0
    
    def get_current_world_name(self) -> Optional[str]:
        """Get the name of the currently loaded world"""
        return self.current_world.name if self.current_world else None
    
    def get_current_world(self) -> Optional[World]:
        """Get the currently loaded world instance"""
        return self.current_world
    
    def get_world_by_name(self, name: str) -> Optional[World]:
        """Get world instance by name"""
        for world in self.worlds:
            if world.name == name:
                return world
        return None
    
    def get_world_count(self) -> int:
        """Get current number of worlds"""
        return len(self.worlds)
    
    def get_worlds_info(self) -> List[Dict[str, Any]]:
        """Get list of world information for UI display"""
        return [world.to_dict() for world in self.worlds]
