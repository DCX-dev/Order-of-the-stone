"""
BRAND NEW World Generation System - Built from Scratch
Clean, reliable, Minecraft-style world generation
"""

import random
import math
from typing import Dict, Tuple, List

class WorldGenerator:
    def __init__(self, seed: int = None):
        if seed is None:
            import time
            seed = int(time.time() * 1000) % 1000000 + random.randint(1, 1000)
        
        self.rng = random.Random(seed)
        self.seed = seed
        
        print(f"🌍 NEW World Generator - Seed: {seed}")
    
    def generate_world(self, world_width: int = 300, world_height: int = 200) -> Dict:
        """Generate a complete Minecraft-style world"""
        print("🚀 Generating brand new world...")
        
        world_data = {
            "blocks": {},
            "width": world_width,
            "height": world_height,
            "spawn_x": 0,
            "spawn_y": 0,
            "player": {
                "x": 0.0, "y": 100.0, "vel_y": 0, "on_ground": False,
                "health": 10, "max_health": 10, "hunger": 100, "max_hunger": 100,
                "stamina": 100, "max_stamina": 100, "inventory": [], "backpack": [],
                "selected": 0, "username": "", "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
            },
            "entities": [],
            "world_settings": {
                "time": 0,
                "day": True,
                "weather": "clear"
            }
        }
        
        blocks = world_data["blocks"]
        
        # Step 1: Generate basic terrain
        print("⛰️  Generating terrain...")
        self._generate_terrain(blocks, world_width)
        
        # Step 2: Add oceans (20% chance)
        if self.rng.random() < 0.2:
            print("🌊 Adding ocean...")
            ocean_side = self.rng.choice(["left", "right"])
            self._add_ocean(blocks, world_width, ocean_side)
        else:
            print("🌍 No ocean in this world")
        
        # Step 3: Find safe spawn on large grassland (FAR from water)
        print("🏠 Finding spawn location...")
        spawn_x, spawn_y = self._find_safe_spawn(blocks, world_width)
        world_data["spawn_x"] = spawn_x
        world_data["spawn_y"] = spawn_y
        world_data["player"]["x"] = float(spawn_x)
        world_data["player"]["y"] = float(spawn_y)
        
        # Step 4: Add trees
        print("🌳 Adding trees...")
        self._add_trees(blocks, world_width)
        
        # Step 5: Add ores
        print("⛏️  Adding ores...")
        self._add_ores(blocks, world_width)
        
        # Step 6: Add structures (fortresses)
        print("🏰 Adding fortresses...")
        self._add_fortresses(blocks, world_width)
        
        # Step 7: Add animals near spawn
        print("🐄 Adding animals...")
        self._add_animals(world_data["entities"], spawn_x, spawn_y, blocks)
        
        print(f"✅ World complete! {len(blocks)} blocks, {len(world_data['entities'])} entities")
        return world_data
    
    def _generate_terrain(self, blocks: Dict[str, str], world_width: int):
        """Generate basic terrain with variety"""
        # Terrain parameters
        base_height = 115
        
        for x in range(-world_width//2, world_width//2):
            # Create varied terrain using sine waves
            height_var = int(
                10 * math.sin(x * 0.05) +
                5 * math.sin(x * 0.1) +
                3 * math.sin(x * 0.2)
            )
            surface_y = base_height + height_var
            surface_y = max(105, min(125, surface_y))
            
            # Bedrock at bottom
            blocks[f"{x},{surface_y + 200}"] = "bedrock"
            
            # Stone layer (deep)
            for y in range(surface_y + 3, surface_y + 200):
                blocks[f"{x},{y}"] = "stone"
            
            # Dirt layer (2 blocks)
            for y in range(surface_y + 1, surface_y + 3):
                blocks[f"{x},{y}"] = "dirt"
            
            # Grass surface
            blocks[f"{x},{surface_y}"] = "grass"
    
    def _add_ocean(self, blocks: Dict[str, str], world_width: int, side: str):
        """Add ocean on one side of the world with beaches"""
        water_level = 120
        ocean_floor = 135
        ocean_width = 100
        beach_width = 40
        
        if side == "left":
            ocean_start = -world_width//2
            ocean_end = -world_width//2 + ocean_width
            beach_start = ocean_end
            beach_end = ocean_end + beach_width
        else:  # right
            ocean_end = world_width//2
            ocean_start = world_width//2 - ocean_width
            beach_end = ocean_start
            beach_start = ocean_start - beach_width
        
        # Generate ocean
        for x in range(ocean_start, ocean_end):
            # Sand floor
            for y in range(ocean_floor, ocean_floor + 4):
                blocks[f"{x},{y}"] = "sand"
            blocks[f"{x},{ocean_floor}"] = "sand"
            
            # Water above sand
            for y in range(water_level, ocean_floor):
                blocks[f"{x},{y}"] = "water"
            blocks[f"{x},{water_level}"] = "water"
            
            # Stone below sand
            for y in range(ocean_floor + 4, ocean_floor + 200):
                blocks[f"{x},{y}"] = "stone"
        
        # Generate beach (transition)
        for x in range(beach_start, beach_end):
            progress = abs(x - beach_start) / beach_width
            beach_y = int(115 + progress * 5)  # Slope from 115 to 120
            
            # Sand layers
            for y in range(beach_y + 1, beach_y + 4):
                blocks[f"{x},{y}"] = "sand"
            blocks[f"{x},{beach_y}"] = "sand"
            
            # Add shallow water if below water level
            if beach_y >= water_level:
                for y in range(water_level, beach_y):
                    blocks[f"{x},{y}"] = "water"
    
    def _find_safe_spawn(self, blocks: Dict[str, str], world_width: int) -> Tuple[int, int]:
        """Find spawn on LARGE grassland, FAR from water"""
        print("   Searching for large grassland far from ocean...")
        
        # Find all grass locations on large landmasses
        safe_spawns = []
        
        for x in range(-world_width//2, world_width//2, 5):
            for y in range(105, 130):
                if blocks.get(f"{x},{y}") == "grass":
                    # Count nearby grass (large landmass check)
                    grass_count = 0
                    for cx in range(x - 15, x + 16):
                        for cy in range(y - 2, y + 3):
                            if blocks.get(f"{cx},{cy}") == "grass":
                                grass_count += 1
                    
                    # Need at least 30 grass blocks nearby = LARGE land
                    if grass_count < 30:
                        continue
                    
                    # Check for water within 60 blocks
                    has_water = False
                    for cx in range(x - 60, x + 61):
                        for cy in range(y - 10, y + 11):
                            if blocks.get(f"{cx},{cy}") == "water":
                                has_water = True
                                break
                        if has_water:
                            break
                    
                    # Only add if NO water within 60 blocks
                    if not has_water:
                        safe_spawns.append((x, y, grass_count))
        
        if safe_spawns:
            # Pick the one with most grass (biggest landmass)
            best = max(safe_spawns, key=lambda s: s[2])
            x, y, count = best
            print(f"   ✅ Spawn on LARGE grassland at ({x},{y}) - {count} grass nearby, FAR from ocean!")
            return x, y - 2
        
        # Fallback: find ANY grass far from water
        print("   ⚠️ Relaxing requirements...")
        for x in range(-world_width//2, world_width//2, 3):
            for y in range(105, 130):
                if blocks.get(f"{x},{y}") == "grass":
                    # Just check no water within 40 blocks
                    water_found = False
                    for cx in range(x - 40, x + 41, 5):
                        if blocks.get(f"{cx},{y}") == "water":
                            water_found = True
                            break
                    
                    if not water_found:
                        print(f"   Found grass at ({x},{y}) with no nearby water")
                        return x, y - 2
        
        # Emergency: spawn at center
        print("   ❌ Using emergency spawn")
        return 0, 113
    
    def _add_trees(self, blocks: Dict[str, str], world_width: int):
        """Add trees on grass"""
        tree_count = 0
        
        for x in range(-world_width//2, world_width//2, 20):
            if self.rng.random() < 0.6:  # 60% chance
                # Find grass
                for y in range(105, 130):
                    if blocks.get(f"{x},{y}") == "grass":
                        # Place tree
                        trunk_height = self.rng.randint(3, 5)
                        
                        # Trunk
                        for ty in range(y - 1, y - trunk_height - 1, -1):
                            blocks[f"{x},{ty}"] = "log"
                        
                        # Leaves
                        for dx in range(-2, 3):
                            for dy in range(-trunk_height - 2, -trunk_height, 1):
                                if abs(dx) + abs(dy + trunk_height) <= 2:
                                    blocks[f"{x + dx},{y + dy}"] = "leaves"
                        
                        tree_count += 1
                        break
        
        print(f"   🌳 Generated {tree_count} trees")
    
    def _add_ores(self, blocks: Dict[str, str], world_width: int):
        """Add ores in stone"""
        ore_count = 0
        
        for x in range(-world_width//2, world_width//2, 2):
            for y in range(120, 250):
                if blocks.get(f"{x},{y}") == "stone" and self.rng.random() < 0.02:
                    # Pick ore type
                    roll = self.rng.random()
                    if roll < 0.5:
                        ore = "coal"
                    elif roll < 0.8:
                        ore = "iron"
                    elif roll < 0.95:
                        ore = "gold"
                    else:
                        ore = "diamond"
                    
                    blocks[f"{x},{y}"] = ore
                    ore_count += 1
        
        print(f"   ⛏️  Generated {ore_count} ores")
    
    def _add_fortresses(self, blocks: Dict[str, str], world_width: int):
        """Add fortresses on grass only"""
        fortress_count = 0
        
        for x in range(-world_width//2, world_width//2, 150):
            if abs(x) < 80:  # Not near spawn
                continue
            
            if self.rng.random() < 0.3:
                # Find grass
                surface_y = None
                for y in range(105, 130):
                    if blocks.get(f"{x},{y}") == "grass":
                        surface_y = y
                        break
                
                if surface_y:
                    # Check entire fortress width has grass
                    width = 12
                    all_grass = True
                    for dx in range(width):
                        if blocks.get(f"{x+dx},{surface_y}") != "grass":
                            all_grass = False
                            break
                    
                    if all_grass:
                        # Build fortress
                        height = 10
                        
                        # Floor
                        for dx in range(width):
                            blocks[f"{x+dx},{surface_y}"] = "red_brick"
                        
                        # Walls
                        for dy in range(1, height + 1):
                            for dx in range(width):
                                if dx == 0 or dx == width-1 or dy == height:
                                    blocks[f"{x+dx},{surface_y - dy}"] = "red_brick"
                        
                        # Door
                        blocks[f"{x + width//2},{surface_y - 1}"] = "door"
                        
                        fortress_count += 1
        
        print(f"   🏰 Generated {fortress_count} fortresses")
    
    def _add_animals(self, entities: List, spawn_x: int, spawn_y: int, blocks: Dict):
        """Add cows and slimes near spawn with proper entity data"""
        # Add 3-4 cows
        cow_count = self.rng.randint(3, 4)
        for i in range(cow_count):
            # Place near spawn but not too close
            cow_x = spawn_x + self.rng.randint(-30, 30)
            cow_y = spawn_y + self.rng.randint(-5, 5)
            
            # Make sure on ground
            for y in range(cow_y, cow_y + 20):
                if blocks.get(f"{int(cow_x)},{y}") in ["grass", "dirt"]:
                    entities.append({
                        "type": "cow",
                        "x": float(cow_x),
                        "y": float(y - 2),
                        "hp": 10,
                        "cooldown": 0,
                        "direction": 1
                    })
                    break
        
        # Add 3-4 slimes with ALL required fields
        slime_count = self.rng.randint(3, 4)
        for i in range(slime_count):
            slime_x = spawn_x + self.rng.randint(-40, 40)
            slime_y = spawn_y + self.rng.randint(-5, 5)
            
            # Make sure on ground
            for y in range(slime_y, slime_y + 20):
                if blocks.get(f"{int(slime_x)},{y}") in ["grass", "dirt"]:
                    entities.append({
                        "type": "slime",
                        "x": float(slime_x),
                        "y": float(y - 2),
                        "hp": 3,
                        "cooldown": 0,
                        "aggressive": False,
                        "vel_y": 0,
                        "on_ground": True,
                        "jump_cooldown": 0,
                        "squish_amount": 0
                    })
                    break
        
        print(f"   🐄 Added {cow_count} cows and {slime_count} slimes")


def generate_world(seed: str = None, world_width: int = 300) -> Dict:
    """
    Generate a new world
    
    Args:
        seed: Optional seed for reproducible generation
        world_width: Width of the world in blocks
        
    Returns:
        World data dictionary
    """
    generator = WorldGenerator(seed)
    return generator.generate_world(world_width)
