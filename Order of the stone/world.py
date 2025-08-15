import json
import os
import time
from typing import Dict, List, Optional, Any

class World:
    """Represents a single world with its data and metadata"""
    
    def __init__(self, name: str, filename: str = None):
        self.name = name
        self.filename = filename or f"{name}.json"
        self.created = time.time()
        self.last_modified = time.time()
        self.player_info = "New world"
        self.is_loaded = False
        
        # World data
        self.player_data = None
        self.world_data = {}
        self.entities = []
        self.chest_data = {}
    
    def get_display_name(self) -> str:
        """Get formatted display name for UI"""
        return self.name
    
    def get_last_modified_str(self) -> str:
        """Get formatted last modified time"""
        return time.strftime('%Y-%m-%d %H:%M', time.localtime(self.last_modified))
    
    def get_created_str(self) -> str:
        """Get formatted creation time"""
        return time.strftime('%Y-%m-%d %H:%M', time.localtime(self.created))
    
    def get_player_status(self) -> str:
        """Get player status string for display"""
        if not self.player_data:
            return "New world"
        
        health = self.player_data.get('health', 0)
        hunger = self.player_data.get('hunger', 0)
        return f"Health: {health}, Hunger: {hunger}"
    
    def update_player_info(self, player_data: Dict):
        """Update player information from game data"""
        self.player_data = player_data
        self.player_info = self.get_player_status()
        self.last_modified = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert world metadata to dictionary for saving"""
        return {
            'name': self.name,
            'filename': self.filename,
            'created': self.created,
            'last_modified': self.last_modified,
            'player_info': self.player_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'World':
        """Create World instance from dictionary data"""
        world = cls(data['name'], data['filename'])
        world.created = data.get('created', time.time())
        world.last_modified = data.get('last_modified', time.time())
        world.player_info = data.get('player_info', 'New world')
        return world
