import pygame
import os
import json
import time
from typing import List, Dict, Optional

class WorldManager:
    """Manages world creation, naming, and selection"""
    
    def __init__(self, save_dir: str = "save_data"):
        self.save_dir = save_dir
        self.worlds: List[Dict] = []
        self.current_world_name: Optional[str] = None
        self.new_world_name: str = ""
        self.is_typing: bool = False
        self.cursor_blink: bool = True
        self.cursor_timer: float = 0
        
        # Ensure save directory exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        self.load_worlds()
    
    def load_worlds(self):
        """Load all existing worlds from the save directory"""
        self.worlds = []
        
        if not os.path.exists(self.save_dir):
            return
            
        for filename in os.listdir(self.save_dir):
            if filename.endswith('.json') and filename != 'save.json':
                world_name = filename[:-5]  # Remove .json extension
                filepath = os.path.join(self.save_dir, filename)
                
                # Get file info
                try:
                    stat = os.stat(filepath)
                    last_modified = time.strftime('%Y-%m-%d %H:%M', time.localtime(stat.st_mtime))
                    
                    # Try to load world data to get player info
                    player_info = "Unknown"
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            if 'player' in data:
                                player = data['player']
                                health = player.get('health', 0)
                                hunger = player.get('hunger', 0)
                                player_info = f"Health: {health}, Hunger: {hunger}"
                    except:
                        player_info = "Corrupted save"
                    
                    self.worlds.append({
                        'name': world_name,
                        'filename': filename,
                        'last_modified': last_modified,
                        'player_info': player_info
                    })
                except:
                    continue
        
        # Sort worlds by last modified (newest first)
        self.worlds.sort(key=lambda w: w['last_modified'], reverse=True)
    
    def create_world(self, world_name: str) -> bool:
        """Create a new world with the given name"""
        if len(world_name.strip()) < 8:
            return False
            
        # Clean the world name (remove invalid characters)
        clean_name = "".join(c for c in world_name if c.isalnum() or c in " -_")
        clean_name = clean_name.strip()
        
        if not clean_name:
            return False
            
        # Check if world name already exists
        for world in self.worlds:
            if world['name'].lower() == clean_name.lower():
                return False
        
        # Create the world file
        filename = f"{clean_name}.json"
        filepath = os.path.join(self.save_dir, filename)
        
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
            'created': time.time()
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(world_data, f, indent=2)
            
            # Add to worlds list
            self.worlds.append({
                'name': clean_name,
                'filename': filename,
                'last_modified': time.strftime('%Y-%m-%d %H:%M'),
                'player_info': "New world"
            })
            
            self.current_world_name = clean_name
            return True
            
        except Exception as e:
            print(f"Error creating world: {e}")
            return False
    
    def delete_world(self, world_name: str) -> bool:
        """Delete a world"""
        for world in self.worlds[:]:
            if world['name'] == world_name:
                try:
                    filepath = os.path.join(self.save_dir, world['filename'])
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    self.worlds.remove(world)
                    
                    if self.current_world_name == world_name:
                        self.current_world_name = None
                    return True
                except Exception as e:
                    print(f"Error deleting world: {e}")
                    return False
        return False
    
    def load_world(self, world_name: str) -> Optional[Dict]:
        """Load a specific world"""
        for world in self.worlds:
            if world['name'] == world_name:
                try:
                    filepath = os.path.join(self.save_dir, world['filename'])
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        self.current_world_name = world_name
                        return data
                except Exception as e:
                    print(f"Error loading world: {e}")
                    return None
        return None
    
    def save_world(self, world_name: str, game_data: Dict) -> bool:
        """Save the current world"""
        for world in self.worlds:
            if world['name'] == world_name:
                try:
                    filepath = os.path.join(self.save_dir, world['filename'])
                    
                    # Update last modified time
                    world['last_modified'] = time.strftime('%Y-%m-%d %H:%M')
                    
                    # Update player info
                    if 'player' in game_data:
                        player = game_data['player']
                        health = player.get('health', 0)
                        hunger = player.get('hunger', 0)
                        world['player_info'] = f"Health: {health}, Hunger: {hunger}"
                    
                    with open(filepath, 'w') as f:
                        json.dump(game_data, f, indent=2)
                    
                    return True
                except Exception as e:
                    print(f"Error saving world: {e}")
                    return False
        return False
    
    def get_world_names(self) -> List[str]:
        """Get list of all world names"""
        return [world['name'] for world in self.worlds]
    
    def has_worlds(self) -> bool:
        """Check if there are any existing worlds"""
        return len(self.worlds) > 0
    
    def get_current_world_name(self) -> Optional[str]:
        """Get the name of the currently loaded world"""
        return self.current_world_name
    
    def start_typing(self):
        """Start typing mode for new world name"""
        self.is_typing = True
        self.new_world_name = ""
        self.cursor_timer = time.time()
    
    def stop_typing(self):
        """Stop typing mode"""
        self.is_typing = False
        self.new_world_name = ""
    
    def add_character(self, char: str):
        """Add a character to the new world name"""
        if self.is_typing and len(self.new_world_name) < 20:  # Limit to 20 characters
            self.new_world_name += char
            print(f"[DEBUG] Added '{char}', name now: '{self.new_world_name}'")
    
    def remove_character(self):
        """Remove the last character from the new world name"""
        if self.is_typing and self.new_world_name:
            self.new_world_name = self.new_world_name[:-1]
    
    def can_create_world(self) -> bool:
        """Check if world can be created (name is long enough)"""
        return len(self.new_world_name.strip()) >= 8
    
    def get_new_world_name(self) -> str:
        """Get the current new world name being typed"""
        return self.new_world_name
    
    def update_cursor(self):
        """Update cursor blink animation"""
        current_time = time.time()
        if current_time - self.cursor_timer > 0.5:
            self.cursor_blink = not self.cursor_blink
            self.cursor_timer = current_time
