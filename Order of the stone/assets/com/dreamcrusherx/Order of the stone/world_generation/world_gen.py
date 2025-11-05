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
        
        # RANDOMIZE terrain parameters for UNIQUE worlds!
        self.terrain_freq1 = self.rng.uniform(0.02, 0.08)
        self.terrain_freq2 = self.rng.uniform(0.08, 0.15)
        self.terrain_freq3 = self.rng.uniform(0.15, 0.25)
        self.terrain_amplitude = self.rng.uniform(8, 15)  # Height variation
        self.base_height = self.rng.randint(110, 120)
        # Random offsets make the same frequencies look completely different!
        self.offset1 = self.rng.uniform(0, 1000)
        self.offset2 = self.rng.uniform(0, 1000)
        self.offset3 = self.rng.uniform(0, 1000)
        
        print(f"🌍 NEW World Generator - Seed: {seed}")
        print(f"   Terrain: amp={self.terrain_amplitude:.1f}, base={self.base_height}, offsets=({self.offset1:.0f},{self.offset2:.0f},{self.offset3:.0f})")
    
    def generate_world(self, world_width: int = 400, world_height: int = 200) -> Dict:
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
        
        # Step 2: Find spawn in CENTER first (you start in grassland/forest)
        print("🏠 Finding spawn location in center...")
        spawn_x, spawn_y = self._find_center_spawn(blocks, world_width)
        world_data["spawn_x"] = spawn_x
        world_data["spawn_y"] = spawn_y
        world_data["player"]["x"] = float(spawn_x)
        world_data["player"]["y"] = float(spawn_y)
        
        # Step 3: Add starting forest around spawn (few trees nearby)
        print("🌳 Adding starting forest near spawn...")
        self._add_spawn_forest(blocks, spawn_x, spawn_y)
        
        # Step 4: Add trees throughout world (more as you explore)
        print("🌳 Adding trees across world...")
        self._add_trees(blocks, world_width, spawn_x)
        
        # Step 5: Add oceans FAR from spawn (rare, on edges)
        if self.rng.random() < 0.15:  # 15% chance for ocean
            print("🌊 Adding ocean on far edge...")
            ocean_side = self.rng.choice(["left", "right"])  # Only ONE ocean
            self._add_ocean(blocks, world_width, ocean_side)
        else:
            print("🌍 No ocean in this world")
        
        # Step 6: Add ores (coal/iron shallow, gold/diamonds deep)
        print("⛏️  Adding ores...")
        self._add_ores(blocks, world_width)
        
        # Step 7: Add fortresses far from spawn
        print("🏰 Adding fortresses...")
        self._add_fortresses(blocks, world_width, spawn_x)
        
        # Note: Animals (cows, slimes) will be spawned by the main game
        # because they need texture references not available here
        
        print(f"✅ World complete! {len(blocks)} blocks generated")
        return world_data
    
    def _generate_terrain(self, blocks: Dict[str, str], world_width: int):
        """Generate basic terrain with variety - RANDOMIZED per world!"""
        
        for x in range(-world_width//2, world_width//2):
            # Create varied terrain using RANDOMIZED sine waves with offsets
            height_var = int(
                self.terrain_amplitude * math.sin((x + self.offset1) * self.terrain_freq1) +
                (self.terrain_amplitude * 0.5) * math.sin((x + self.offset2) * self.terrain_freq2) +
                (self.terrain_amplitude * 0.3) * math.sin((x + self.offset3) * self.terrain_freq3)
            )
            surface_y = self.base_height + height_var
            surface_y = max(self.base_height - 15, min(self.base_height + 15, surface_y))
            
            # Bedrock at bottom (fixed depth for all columns)
            bedrock_y = 315  # Fixed bedrock level for entire world
            blocks[f"{x},{bedrock_y}"] = "bedrock"
            
            # Stone layer - fill from bedrock UP to near surface (no gaps!)
            # Go from bedrock (315) up to surface+3
            for y in range(surface_y + 3, bedrock_y):
                blocks[f"{x},{y}"] = "stone"
            
            # Dirt layer (2 blocks below grass)
            blocks[f"{x},{surface_y + 1}"] = "dirt"
            blocks[f"{x},{surface_y + 2}"] = "dirt"
            
            # Grass surface
            blocks[f"{x},{surface_y}"] = "grass"
    
    def _add_ocean(self, blocks: Dict[str, str], world_width: int, side: str):
        """Add ocean on one side of the world with beaches"""
        # CORRECT COORDINATES: Y increases downward
        # Land surface is at Y=115
        # Ocean surface should be at SAME level (Y=115) to be visible
        # Ocean goes DOWN from there (higher Y values = deeper)
        water_surface = 115  # Ocean surface at GROUND LEVEL (visible!)
        ocean_floor = 125    # Ocean floor 10 blocks DOWN (below water surface)
        ocean_width = 60     # SMALLER ocean (60 blocks instead of 100) - keeps it at edge
        beach_width = 30     # SMALLER beach (30 blocks instead of 40)
        
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
        
        # Generate ocean - COMPLETELY REPLACE any existing terrain
        for x in range(ocean_start, ocean_end):
            # REMOVE ALL blocks above ocean surface (clear the entire column from sky to water!)
            # This prevents land chunks from sitting on top of ocean
            for clear_y in range(50, water_surface):  # Clear from sky (Y=50) down to water surface
                key = f"{x},{clear_y}"
                if key in blocks:
                    del blocks[key]
            
            # Ocean surface (same level as land - VISIBLE!)
            blocks[f"{x},{water_surface}"] = "water"
            
            # Water going DOWN to ocean floor (Y increases = going down)
            for y in range(water_surface + 1, ocean_floor):
                blocks[f"{x},{y}"] = "water"
            
            # Sand floor at bottom of ocean
            blocks[f"{x},{ocean_floor}"] = "sand"
            for y in range(ocean_floor + 1, ocean_floor + 4):
                blocks[f"{x},{y}"] = "sand"
            
            # Stone below sand (deep underground)
            for y in range(ocean_floor + 4, ocean_floor + 200):
                blocks[f"{x},{y}"] = "stone"
            
            # Bedrock at very bottom
            blocks[f"{x},{ocean_floor + 200}"] = "bedrock"
        
        # Generate beach (smooth transition from land to ocean)
        for x in range(beach_start, beach_end):
            # REMOVE ALL blocks above beach (clear from sky down!)
            for clear_y in range(50, water_surface):  # Clear from sky to beach level
                key = f"{x},{clear_y}"
                if key in blocks:
                    del blocks[key]
            
            # Beach at ground level (visible!)
            beach_y = water_surface  # Same level as ocean surface
            
            # Sand surface
            blocks[f"{x},{beach_y}"] = "sand"
            
            # Sand going DOWN (Y increases = down)
            for y in range(beach_y + 1, beach_y + 4):
                blocks[f"{x},{y}"] = "sand"
            
            # Stone below sand
            for y in range(beach_y + 4, beach_y + 200):
                blocks[f"{x},{y}"] = "stone"
            
            # Bedrock at bottom
            blocks[f"{x},{beach_y + 200}"] = "bedrock"
    
    def _find_center_spawn(self, blocks: Dict[str, str], world_width: int) -> Tuple[int, int]:
        """Find spawn near CENTER - nice grassland starting area"""
        print("   Finding nice grassland near center...")
        
        # Search near center (within 30 blocks of X=0)
        for x in range(-30, 31, 2):
            for y in range(100, 130):
                if blocks.get(f"{x},{y}") == "grass":
                    # Check it has dirt below (valid grass)
                    if blocks.get(f"{x},{y+1}") == "dirt":
                        print(f"   ✅ Spawn on grass at ({x},{y})")
                        return x, y - 2  # 2 blocks ABOVE grass (Y decreases = up)
        
        # Fallback: search wider
        for x in range(-50, 51):
            for y in range(100, 130):
                if blocks.get(f"{x},{y}") == "grass":
                    print(f"   Found grass at ({x},{y})")
                    return x, y - 2
        
        # Emergency
        print("   ❌ Emergency spawn")
        return 0, 110
    
    def _add_spawn_forest(self, blocks: Dict[str, str], spawn_x: int, spawn_y: int):
        """Add a few trees near spawn for starting forest feel"""
        trees_added = 0
        
        # Add 4-6 trees near spawn
        for i in range(self.rng.randint(4, 6)):
            tree_x = spawn_x + self.rng.randint(-20, 20)
            
            # Find grass at this X
            for y in range(100, 130):
                if blocks.get(f"{tree_x},{y}") == "grass":
                    # Place small tree (trunk goes UP, Y decreases)
                    trunk_height = 3
                    
                    # Trunk
                    for ty in range(y - 1, y - trunk_height - 1, -1):
                        blocks[f"{tree_x},{ty}"] = "log"
                    
                    # Leaves above trunk (Y decreases = up)
                    for dx in range(-1, 2):
                        for dy in range(-trunk_height - 1, -trunk_height - 3, -1):
                            blocks[f"{tree_x + dx},{y + dy}"] = "leaves"
                    
                    trees_added += 1
                    break
        
        print(f"      Added {trees_added} trees at spawn")
    
    def _add_trees(self, blocks: Dict[str, str], world_width: int, spawn_x: int):
        """Add trees across world - MORE as you get farther from spawn"""
        tree_count = 0
        
        for x in range(-world_width//2, world_width//2, 15):
            # Skip spawn area (already has starting forest)
            if abs(x - spawn_x) < 30:
                continue
            
            # More trees farther from spawn
            distance_from_spawn = abs(x - spawn_x)
            tree_chance = 0.3 if distance_from_spawn < 50 else 0.6
            
            if self.rng.random() < tree_chance:
                # Find grass
                for y in range(100, 130):
                    if blocks.get(f"{x},{y}") == "grass":
                        # Place tree (trunk goes UP, Y decreases)
                        trunk_height = self.rng.randint(3, 5)
                        
                        # Trunk
                        for ty in range(y - 1, y - trunk_height - 1, -1):
                            blocks[f"{x},{ty}"] = "log"
                        
                        # Leaves (above trunk, Y decreases)
                        for dx in range(-2, 3):
                            for dy in range(-trunk_height - 2, -trunk_height, 1):
                                if abs(dx) + abs(dy + trunk_height) <= 2:
                                    blocks[f"{x + dx},{y + dy}"] = "leaves"
                        
                        tree_count += 1
                        break
        
        print(f"      Generated {tree_count} trees across world")
    
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
    
    def _add_fortresses(self, blocks: Dict[str, str], world_width: int, spawn_x: int):
        """Add fortresses FAR from spawn (exploration reward)"""
        fortress_count = 0
        
        for x in range(-world_width//2, world_width//2, 150):
            # Only spawn fortresses FAR from spawn (100+ blocks away)
            if abs(x - spawn_x) < 100:
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


def generate_world(seed: str = None, world_width: int = 400) -> Dict:
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
