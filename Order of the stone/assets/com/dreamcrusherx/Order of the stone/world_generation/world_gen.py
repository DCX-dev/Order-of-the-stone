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
        
        # Step 2: Add oceans on BOTH edges (like Terraria)
        print("🌊 Adding oceans on both edges...")
        self._add_ocean(blocks, world_width, "left")
        self._add_ocean(blocks, world_width, "right")
        
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
        # CORRECT COORDINATES: Y increases downward
        # Land surface is at Y=115
        # Ocean surface should be at SAME level (Y=115) to be visible
        # Ocean goes DOWN from there (higher Y values = deeper)
        water_surface = 115  # Ocean surface at GROUND LEVEL (visible!)
        ocean_floor = 125    # Ocean floor 10 blocks DOWN (below water surface)
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
    
    def _find_safe_spawn(self, blocks: Dict[str, str], world_width: int) -> Tuple[int, int]:
        """Find spawn in CENTER of world (like Terraria) - guaranteed far from both oceans"""
        print("   Spawning in CENTER of world (Terraria style)...")
        
        # Terraria style: ALWAYS spawn in the middle third of the world
        # This guarantees you're far from both ocean edges
        center_start = -world_width // 6  # Middle third starts here
        center_end = world_width // 6      # Middle third ends here
        
        # Find grass in the center area
        for x in range(center_start, center_end, 3):
            for y in range(105, 130):
                if blocks.get(f"{x},{y}") == "grass":
                    # Found grass in center - use it!
                    print(f"   ✅ CENTER spawn on grass at ({x},{y}) - FAR from both oceans!")
                    return x, y - 2
        
        # Fallback: expand search slightly
        print("   ⚠️ Searching slightly wider...")
        for x in range(-world_width//4, world_width//4, 2):
            for y in range(105, 130):
                if blocks.get(f"{x},{y}") == "grass":
                    print(f"   Found grass at ({x},{y})")
                    return x, y - 2
        
        # Emergency: spawn at exact center
        print("   ❌ Using center spawn")
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
