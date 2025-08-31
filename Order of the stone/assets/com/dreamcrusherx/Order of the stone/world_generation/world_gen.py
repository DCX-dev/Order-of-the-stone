"""
Improved World Generation System
Generates beautiful Minecraft-style worlds with proper terrain layers
"""

import random
from typing import Dict, Tuple, List
import time

class WorldGenerator:
    def __init__(self, seed: int = None):
        if seed is None:
            seed = random.randint(1, 1000000)
        self.rng = random.Random(seed)
        print(f"🌍 World Generator initialized with seed: {seed}")
    
    def generate_world(self, world_width: int = 400, world_height: int = 200) -> Dict:
        """Generate a simple, clean world"""
        print("🚀 Starting clean world generation...")
        
        world_data = {
            "blocks": {},
            "width": world_width,
            "height": world_height,
            "spawn_x": 0,
            "spawn_y": 0,
            "player": {
                "x": 0.0, "y": 48.0, "vel_y": 0, "on_ground": False,
                "health": 10, "max_health": 10, "hunger": 100, "max_hunger": 100,
                "stamina": 100, "max_stamina": 100, "inventory": [], "backpack": [],
                "selected": 0, "username": "", "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
            },
            "entities": [],
            "world_settings": {
                "time": time.time(),
                "day": True,
                "weather": "clear"
            }
        }
        
        # Simple, clean terrain generation
        print("🏔️ Generating smooth terrain...")
        self._generate_simple_terrain(world_data["blocks"], world_width)
        
        # Add some basic structures
        print("🌳 Adding trees...")
        self._generate_simple_trees(world_data["blocks"], world_width)
        
        print("🏰 Adding fortresses...")
        self._generate_simple_fortresses(world_data["blocks"], world_width)
        
        print("⛏️ Adding ores...")
        self._generate_simple_ores(world_data["blocks"], world_width)
        
        # Find spawn location
        spawn_x, spawn_y = self._find_spawn_location(world_data["blocks"], world_width)
        world_data["spawn_x"] = spawn_x
        world_data["spawn_y"] = spawn_y
        
        # Update player position to spawn location
        world_data["player"]["x"] = float(spawn_x)
        world_data["player"]["y"] = float(spawn_y)  # Use the calculated spawn position directly
        
        print(f"📍 Spawn location: ({spawn_x}, {spawn_y})")
        print(f"✅ World generation complete! Generated {len(world_data['blocks'])} blocks")
        
        return world_data
    
    def _generate_simple_terrain(self, blocks: Dict[str, str], world_width: int):
        """Generate simple, smooth terrain"""
        # Simple height map with smooth transitions
        heights = []
        current_height = 115  # Base height
        
        for x in range(-world_width//2, world_width//2):
            # Very smooth height variation
            if x % 50 == 0:  # Change height much less frequently (every 50 blocks)
                target_height = self.rng.randint(112, 118)  # Smaller height range
                current_height = target_height
            
            # Add minimal random variation for very smooth terrain
            height = current_height + self.rng.randint(-1, 1)
            height = max(112, min(118, height))  # Keep within smaller bounds
            heights.append(height)
            
            # Generate terrain column
            for y in range(height, height + 15):  # 15 blocks deep
                if y == height:
                    blocks[f"{x},{y}"] = "grass"
                elif y < height + 4:
                    blocks[f"{x},{y}"] = "dirt"
                elif y < height + 12:
                    blocks[f"{x},{y}"] = "stone"
                else:
                    blocks[f"{x},{y}"] = "bedrock"
    
    def _generate_simple_trees(self, blocks: Dict[str, str], world_width: int):
        """Generate simple, clean trees in small clusters"""
        tree_count = 0
        placed_positions = set()
        
        # Generate small tree clusters
        cluster_centers = []
        for x in range(-world_width//2, world_width//2, 35):  # Trees every 35 blocks
            if self.rng.random() < 0.7:  # 70% chance for cluster
                cluster_centers.append(x)
        
        for cluster_x in cluster_centers:
            # Generate 2-4 trees in each cluster (smaller, cleaner clusters)
            cluster_size = self.rng.randint(2, 4)
            for _ in range(cluster_size):
                # Random position within cluster (within 6 blocks of center)
                tree_x = cluster_x + self.rng.randint(-6, 6)
                
                # Find surface height
                surface_y = None
                for y in range(110, 125):
                    if f"{tree_x},{y}" in blocks and blocks[f"{tree_x},{y}"] == "grass":
                        surface_y = y
                        break
                
                if surface_y and (tree_x, surface_y) not in placed_positions:
                    # Check if area is clear for tree
                    area_clear = True
                    for dx in range(-1, 2):
                        for dy in range(-1, 3):
                            check_x, check_y = tree_x + dx, surface_y + dy
                            if f"{check_x},{check_y}" in blocks and blocks[f"{check_x},{check_y}"] in ["log", "leaves", "red_brick", "stone", "chest", "door"]:
                                area_clear = False
                                break
                        if not area_clear:
                            break
                    
                    if area_clear:
                        # Place simple, clean tree
                        # Trunk (2-3 blocks tall - simple and clean)
                        trunk_height = self.rng.randint(2, 3)
                        for y in range(surface_y - 1, surface_y - trunk_height - 1, -1):
                            blocks[f"{tree_x},{y}"] = "log"
                        
                        # Simple leaf pattern (clean and organized)
                        for dx in range(-1, 2):  # Smaller leaf area
                            for dy in range(-trunk_height - 1, -trunk_height - 3, -1):
                                blocks[f"{tree_x + dx},{surface_y + dy}"] = "leaves"
                        
                        placed_positions.add((tree_x, surface_y))
                        tree_count += 1
        
        print(f"🌳 Generated {tree_count} simple trees in {len(cluster_centers)} clusters")
    
    def _generate_simple_fortresses(self, blocks: Dict[str, str], world_width: int):
        """Generate larger, rarer fortresses away from spawn"""
        fortress_count = 0
        
        # Don't spawn fortresses too close to spawn (player starts at x=0)
        spawn_safe_zone = 100  # No fortresses within 100 blocks of spawn
        
        for x in range(-world_width//2, world_width//2, 120):  # Fortress every 120 blocks (much rarer)
            if self.rng.random() < 0.4:  # 40% chance for fortress (rarer)
                # Skip if too close to spawn
                if abs(x) < spawn_safe_zone:
                    continue
                    
                # Find surface height
                surface_y = None
                for y in range(110, 125):
                    if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "grass":
                        surface_y = y
                        break
                
                if surface_y:
                    # Place larger fortress
                    # Base platform (bigger)
                    for dx in range(-6, 7):
                        for dy in range(0, 3):
                            blocks[f"{x + dx},{surface_y + dy}"] = "stone"
                    
                    # Outer walls (bigger)
                    for dx in range(-6, 7):
                        for dy in range(3, 8):
                            if dx in [-6, 6] or dy == 7:  # Outer walls
                                blocks[f"{x + dx},{surface_y + dy}"] = "stone"
                    
                    # Inner walls for rooms
                    for dx in range(-4, 5):
                        if dx % 3 == 0:  # Every 3 blocks
                            for dy in range(3, 7):
                                blocks[f"{x + dx},{surface_y + dy}"] = "stone"
                    
                    # Main entrance
                    blocks[f"{x},{surface_y + 3}"] = "door"
                    
                    # Side entrances
                    if self.rng.random() < 0.5:
                        blocks[f"{x - 3},{surface_y + 3}"] = "door"
                    if self.rng.random() < 0.5:
                        blocks[f"{x + 3},{surface_y + 3}"] = "door"
                    
                    # Multiple chests
                    for _ in range(self.rng.randint(2, 4)):  # 2-4 chests
                        chest_x = x + self.rng.randint(-5, 6)
                        chest_y = surface_y + 1
                        if f"{chest_x},{chest_y}" not in blocks:
                            blocks[f"{chest_x},{chest_y}"] = "chest"
                    
                    # Add some decorative elements
                    if self.rng.random() < 0.6:
                        blocks[f"{x},{surface_y + 6}"] = "red_brick"  # Flag
                    
                    fortress_count += 1
        
        print(f"🏰 Generated {fortress_count} large fortresses (away from spawn)")
    
    def _generate_simple_ores(self, blocks: Dict[str, str], world_width: int):
        """Generate simple ore distribution"""
        ore_count = 0
        
        for _ in range(50):  # 50 ore veins
            x = self.rng.randint(-world_width//2, world_width//2)
            y = self.rng.randint(110, 140)  # Below surface
            
            # Check if position is stone
            if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "stone":
                # Simple ore types
                if y < 120:
                    ore_type = "coal" if self.rng.random() < 0.7 else "iron"
                else:
                    ore_type = "gold" if self.rng.random() < 0.6 else "diamond"
                
                blocks[f"{x},{y}"] = ore_type
                ore_count += 1
        
        print(f"⛏️ Generated {ore_count} ore veins")
    
    def _find_spawn_location(self, blocks: Dict[str, str], world_width: int) -> Tuple[int, int]:
        """Find a good spawn location"""
        # Start at center, find grass surface
        for x in range(-10, 11):
            for y in range(110, 125):
                if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "grass":
                    return x, y - 2  # Spawn 2 blocks above grass (not inside it!)
        
        # Fallback - spawn above the expected surface level
        return 0, 112

def generate_world(seed: str = None, world_width: int = 400) -> Dict:
    """
    Generate a new Minecraft-style world
    
    Args:
        seed: Optional seed for reproducible generation
        world_width: Width of the world in blocks
        
    Returns:
        World data dictionary
    """
    generator = WorldGenerator(seed)
    return generator.generate_world(world_width)
