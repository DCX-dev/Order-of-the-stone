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
            # Generate a truly random seed using timestamp and random number
            import time
            seed = int(time.time() * 1000) % 1000000 + random.randint(1, 1000)
        self.rng = random.Random(seed)
        self.seed = seed
        
        # TRULY RANDOM TERRAIN: Generate random terrain parameters for this world
        self.freq1_offset = self.rng.uniform(0, 1000)
        self.freq2_offset = self.rng.uniform(0, 1000)
        self.freq3_offset = self.rng.uniform(0, 1000)
        self.freq4_offset = self.rng.uniform(0, 1000)
        
        # Random frequency multipliers (how wavy the terrain is)
        self.freq1_mult = self.rng.uniform(0.03, 0.07)   # Large rolling hills
        self.freq2_mult = self.rng.uniform(0.1, 0.2)     # Medium hills
        self.freq3_mult = self.rng.uniform(0.25, 0.35)   # Small variations
        self.freq4_mult = self.rng.uniform(0.4, 0.6)     # Fine details
        
        # Random ocean placement - make oceans RARE (70% chance of no ocean)
        ocean_options = ["left", "right", "center", "none", "none", "none", "none"]
        self.ocean_side = self.rng.choice(ocean_options)
        
        print(f"🌍 World Generator initialized with seed: {seed}")
        print(f"🎲 Truly random terrain: freq offsets=({self.freq1_offset:.1f}, {self.freq2_offset:.1f}, {self.freq3_offset:.1f}, {self.freq4_offset:.1f})")
        print(f"🌊 Ocean placement: {self.ocean_side}")
    
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
        
        # Simple, clean terrain generation with oceans
        print("🏔️ Generating terrain with oceans and beaches...")
        self._generate_simple_terrain(world_data["blocks"], world_width)
        
        # Count ocean and beach blocks
        ocean_blocks = sum(1 for block in world_data["blocks"].values() if block == "water")
        sand_blocks = sum(1 for block in world_data["blocks"].values() if block == "sand")
        grass_blocks = sum(1 for block in world_data["blocks"].values() if block == "grass")
        dirt_blocks = sum(1 for block in world_data["blocks"].values() if block == "dirt")
        stone_blocks = sum(1 for block in world_data["blocks"].values() if block == "stone")
        print(f"🌊 Generated {ocean_blocks} water blocks, {sand_blocks} sand blocks")
        print(f"🌱 Generated {grass_blocks} grass blocks, {dirt_blocks} dirt blocks, {stone_blocks} stone blocks")
        
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
        """Generate natural terrain with FLAT oceans and proper transitions"""
        import math
        
        # Clean, organized terrain generation - consistent but varied per world
        # Y increases downward (like screen coordinates): Y=115 is ground, Y=120 is below ground
        base_height = 115  # Consistent base height for land (ground level)
        water_level = 120  # Water level BELOW ground (higher Y = deeper in world, so 120 is below 115)
        ocean_floor_y = water_level + 15  # Deep flat ocean floor (15 blocks below water level, deeper in ground)
        flat_land_height = 115  # Flat land height around oceans (same as base_height for proper beach transition)
        
        # First pass: Determine ocean regions and create FLAT areas
        ocean_regions = []
        ocean_zone_size = 120  # Longer oceans - 120 blocks wide
        beach_zone_size = 60  # Wider beach transition for better visibility
        
        if self.ocean_side == "center":
            # Ocean in center - long and flat
            ocean_start = -ocean_zone_size // 2
            ocean_end = ocean_zone_size // 2
            beach_left_start = -ocean_zone_size // 2 - beach_zone_size
            beach_left_end = -ocean_zone_size // 2
            beach_right_start = ocean_zone_size // 2
            beach_right_end = ocean_zone_size // 2 + beach_zone_size
            ocean_regions.append(("ocean", ocean_start, ocean_end))
            ocean_regions.append(("beach_left", beach_left_start, beach_left_end))
            ocean_regions.append(("beach_right", beach_right_start, beach_right_end))
        elif self.ocean_side == "left":
            # Ocean on left - long and flat with beaches on BOTH sides
            ocean_start = -world_width // 2 + beach_zone_size
            ocean_end = -world_width // 2 + beach_zone_size + ocean_zone_size
            beach_left_start = -world_width // 2
            beach_left_end = -world_width // 2 + beach_zone_size
            beach_right_start = -world_width // 2 + beach_zone_size + ocean_zone_size
            beach_right_end = -world_width // 2 + beach_zone_size + ocean_zone_size + beach_zone_size
            ocean_regions.append(("ocean", ocean_start, ocean_end))
            ocean_regions.append(("beach_left", beach_left_start, beach_left_end))
            ocean_regions.append(("beach_right", beach_right_start, beach_right_end))
        elif self.ocean_side == "right":
            # Ocean on right - long and flat with beaches on BOTH sides
            ocean_start = world_width // 2 - beach_zone_size - ocean_zone_size
            ocean_end = world_width // 2 - beach_zone_size
            beach_left_start = world_width // 2 - beach_zone_size - ocean_zone_size - beach_zone_size
            beach_left_end = world_width // 2 - beach_zone_size - ocean_zone_size
            beach_right_start = world_width // 2 - beach_zone_size
            beach_right_end = world_width // 2
            ocean_regions.append(("ocean", ocean_start, ocean_end))
            ocean_regions.append(("beach_left", beach_left_start, beach_left_end))
            ocean_regions.append(("beach_right", beach_right_start, beach_right_end))
        
        for x in range(-world_width//2, world_width//2):
            # Determine if this position is in ocean/beach or normal terrain
            is_ocean = False
            is_beach = False
            region_type = None
            
            for reg_type, reg_start, reg_end in ocean_regions:
                if reg_start <= x <= reg_end:
                    if reg_type == "ocean":
                        is_ocean = True
                        region_type = "ocean"
                    elif reg_type in ["beach", "beach_left", "beach_right"]:
                        is_beach = True
                        region_type = reg_type
                    break
            
            if is_ocean:
                # OCEAN: Completely flat floor at fixed depth
                surface_y = ocean_floor_y
            elif is_beach:
                # BEACH: Smooth transition from flat land to ocean
                if region_type == "beach_left":
                    beach_start = -ocean_zone_size // 2 - beach_zone_size
                    beach_end = -ocean_zone_size // 2
                elif region_type == "beach_right":
                    beach_start = ocean_zone_size // 2
                    beach_end = ocean_zone_size // 2 + beach_zone_size
                else:
                    # Single beach region
                    if self.ocean_side == "left":
                        beach_start = -world_width // 2 + ocean_zone_size
                        beach_end = -world_width // 2 + ocean_zone_size + beach_zone_size
                    else:  # right
                        beach_start = world_width // 2 - ocean_zone_size - beach_zone_size
                        beach_end = world_width // 2 - ocean_zone_size
                
                beach_progress = (x - beach_start) / (beach_end - beach_start)  # 0.0 to 1.0
                beach_progress = max(0.0, min(1.0, beach_progress))
                # Smooth transition: flat land height down to slightly below water level for natural beach slope
                # In downward-Y: higher Y = deeper, so beach goes from flat_land_height (115) down to water_level + 2 (122)
                # This makes beaches slope gently into the water
                beach_end_y = water_level + 2  # Beach extends slightly below water level for natural transition
                surface_y = int(flat_land_height + (beach_progress * (beach_end_y - flat_land_height)))
            else:
                # NORMAL TERRAIN: Use random terrain BUT flatten areas near oceans to prevent cliffs
                # Check if near ocean (within 100 blocks) - if so, use flatter terrain
                near_ocean = False
                for reg_type, reg_start, reg_end in ocean_regions:
                    if reg_type == "ocean":
                        if abs(x - reg_start) < 100 or abs(x - reg_end) < 100:
                            near_ocean = True
                            break
                
                if near_ocean:
                    # Flatten terrain near oceans to prevent cliffs
                    reduced_height_variation = int(2 * math.sin((x + self.freq1_offset) * self.freq1_mult * 0.5))
                    surface_y = flat_land_height + reduced_height_variation
                    surface_y = max(flat_land_height - 2, min(flat_land_height + 3, surface_y))
                else:
                    # Normal terrain away from oceans
                    primary_wave = 8 * math.sin((x + self.freq1_offset) * self.freq1_mult)
                    secondary_wave = 4 * math.sin((x + self.freq2_offset) * self.freq2_mult)
                    tertiary_wave = 2 * math.sin((x + self.freq3_offset) * self.freq3_mult)
                    detail_wave = 1 * math.sin((x + self.freq4_offset) * self.freq4_mult)
                    height_variation = int(primary_wave + secondary_wave + tertiary_wave + detail_wave)
                    surface_y = base_height + height_variation
                    surface_y = max(100, min(125, surface_y))
            
            # NATURAL TERRAIN GENERATION: Build layers from bottom to top
            
            # 1. BEDROCK at bottom (200 blocks below surface)
            bedrock_y = surface_y + 200  # 200 blocks below surface
            if f"{x},{bedrock_y}" not in blocks:  # Only place if empty
                blocks[f"{x},{bedrock_y}"] = "bedrock"
            
            # 2. STONE LAYER: Fill from bedrock up to near surface
            stone_top = surface_y + 5 if is_ocean else surface_y + 3
            for y in range(stone_top, bedrock_y):
                if f"{x},{y}" not in blocks:  # Only place if empty
                    blocks[f"{x},{y}"] = "stone"
            
            # 3. TERRAIN SURFACE LAYERS - Simple and clean
            if is_ocean:
                # Ocean floor: sand layers (NO holes)
                # surface_y is the ocean floor (deeper = higher Y value in downward-Y system)
                for y in range(surface_y + 1, surface_y + 5):
                    blocks[f"{x},{y}"] = "sand"
                # Ocean floor surface
                blocks[f"{x},{surface_y}"] = "sand"
                
                # Fill with water from water level DOWN to ocean floor (NO holes)
                # In downward-Y system: water_level (120) to surface_y (135) fills downward
                # Fill all blocks from water_level down to just above ocean floor
                for y in range(water_level, surface_y):
                    blocks[f"{x},{y}"] = "water"
                # Make sure water level surface is also water
                blocks[f"{x},{water_level}"] = "water"
            elif is_beach:
                # Beach: sand layers that slope down to ocean with smooth transition
                # Beach transitions from land height (115) down to slightly below water level (122)
                # In downward-Y: Y increases downward, so 115 is land, 120 is water level, 122 is shallow water
                for y in range(surface_y + 1, surface_y + 4):
                    blocks[f"{x},{y}"] = "sand"
                # Beach surface - always sand
                blocks[f"{x},{surface_y}"] = "sand"
                
                # Add water below the beach surface when it reaches or goes below water level
                # Beach slopes from 115 (dry) down to 122 (below water level at 120)
                # When surface_y >= water_level, beach is at or below water, so fill with water below
                if surface_y >= water_level:
                    # Beach is at or below water level - fill with water below the sand surface
                    # This creates shallow water on beaches that naturally transitions into the ocean
                    if surface_y > water_level:
                        # Beach surface is below water level - fill from water level up to the sand
                        # range(water_level, surface_y) fills all Y values from 120 to just below surface_y
                        for y in range(water_level, int(surface_y)):
                            blocks[f"{x},{y}"] = "water"
                    else:
                        # Beach surface is exactly at water level - add shallow water below
                        for y in range(water_level + 1, water_level + 4):
                            blocks[f"{x},{y}"] = "water"
                # If surface_y < water_level (115-119), beach is above water - dry beach, no water needed
            else:
                # Normal terrain: PROPER LAYERS (NO holes)
                # DIRT LAYER: 2 blocks below surface
                for y in range(surface_y + 1, surface_y + 3):
                    blocks[f"{x},{y}"] = "dirt"
                
                # GRASS: ONLY at exact surface level
                blocks[f"{x},{surface_y}"] = "grass"
    
    def _generate_simple_trees(self, blocks: Dict[str, str], world_width: int):
        """Generate simple, clean trees in small clusters (not in oceans or beaches)"""
        tree_count = 0
        placed_positions = set()
        
        # Generate clean, organized tree clusters
        cluster_centers = []
        tree_spacing = 30  # Consistent tree spacing
        for x in range(-world_width//2, world_width//2, tree_spacing):
            if self.rng.random() < 0.6:  # 60% chance for cluster
                cluster_centers.append(x)
        
        # Generate VERY sparse desert trees (much rarer)
        desert_tree_centers = []
        desert_tree_spacing = 80  # Much wider spacing for desert trees
        for x in range(-world_width//2, world_width//2, desert_tree_spacing):
            if self.rng.random() < 0.15:  # Only 15% chance for desert tree cluster
                desert_tree_centers.append(x)
        
        for cluster_x in cluster_centers:
            # Generate 2-3 trees in each cluster (clean, organized)
            cluster_size = self.rng.randint(2, 3)
            for _ in range(cluster_size):
                # Clean position within cluster (within 5 blocks of center)
                tree_x = cluster_x + self.rng.randint(-5, 5)
                
                # IMPORTANT: Skip trees in ocean/beach areas - check block type
                block_at_surface = None
                surface_y = None
                for y in range(80, 130):
                    block = blocks.get(f"{tree_x},{y}")
                    if block == "grass":
                        surface_y = y
                        block_at_surface = block
                        break
                    elif block == "sand":
                        # This might be beach - check if it's actually beach or just desert
                        # Skip this position to avoid trees in beach areas
                        break
                
                # Skip if no grass surface found (might be ocean/sand)
                if surface_y is None:
                    continue
                
                if (tree_x, surface_y) not in placed_positions:
                    # Check if area is clear for tree (must have air above and grass below)
                    area_clear = True
                    
                    # Check that there's grass at surface
                    if blocks.get(f"{tree_x},{surface_y}") != "grass":
                        continue
                    
                    # Check that there's air above for tree to grow
                    for dy in range(-1, -6, -1):  # Check 5 blocks above
                        check_block = blocks.get(f"{tree_x},{surface_y + dy}")
                        if check_block and check_block != "air":
                            area_clear = False
                            break
                    
                    # Check nearby area for obstacles
                    if area_clear:
                        for dx in range(-1, 2):
                            for dy in range(-1, 3):
                                check_x, check_y = tree_x + dx, surface_y + dy
                                if f"{check_x},{check_y}" in blocks and blocks[f"{check_x},{check_y}"] in ["log", "leaves", "red_brick", "stone", "door"]:
                                    area_clear = False
                                    break
                            if not area_clear:
                                break
                    
                    if area_clear:
                        # Place clean, organized tree
                        # Trunk (2-3 blocks tall - consistent)
                        trunk_height = self.rng.randint(2, 3)
                        for y in range(surface_y - 1, surface_y - trunk_height - 1, -1):
                            blocks[f"{tree_x},{y}"] = "log"
                        
                        # Clean leaf pattern (organized)
                        for dx in range(-1, 2):  # 3x3 leaf area
                            for dy in range(-trunk_height - 1, -trunk_height - 3, -1):
                                blocks[f"{tree_x + dx},{surface_y + dy}"] = "leaves"
                        
                        # Add top leaf for better appearance
                        blocks[f"{tree_x},{surface_y - trunk_height - 2}"] = "leaves"
                        
                        placed_positions.add((tree_x, surface_y))
                        tree_count += 1
        
        print(f"🌳 Generated {tree_count} simple trees in {len(cluster_centers)} clusters")
        
        # Generate VERY sparse desert trees (only on sand)
        desert_tree_count = 0
        for cluster_x in desert_tree_centers:
            # Generate only 1 tree per desert cluster (very sparse)
            tree_x = cluster_x + self.rng.randint(-10, 10)
            
            # Find surface by searching for sand block from top down
            surface_y = None
            for y in range(80, 130):
                block = blocks.get(f"{tree_x},{y}")
                if block == "sand":  # Only on sand (desert)
                    surface_y = y
                    break
            
            # Skip if no sand surface found
            if surface_y is None:
                continue
            
            if (tree_x, surface_y) not in placed_positions:
                # Check if area is clear for tree (must have air above and sand below)
                area_clear = True
                
                # Check that there's sand at surface
                if blocks.get(f"{tree_x},{surface_y}") != "sand":
                    continue
                
                # Check that there's air above for tree to grow
                for dy in range(-1, -6, -1):  # Check 5 blocks above
                    check_block = blocks.get(f"{tree_x},{surface_y + dy}")
                    if check_block and check_block != "air":
                        area_clear = False
                        break
                
                # Check nearby area for obstacles
                if area_clear:
                    for dx in range(-1, 2):
                        for dy in range(-1, 3):
                            check_x, check_y = tree_x + dx, surface_y + dy
                            if f"{check_x},{check_y}" in blocks and blocks[f"{check_x},{check_y}"] in ["log", "leaves", "red_brick", "stone", "door"]:
                                area_clear = False
                                break
                        if not area_clear:
                            break
                
                if area_clear:
                    # Place desert tree (smaller than regular trees)
                    # Trunk (1-2 blocks tall - smaller for desert)
                    trunk_height = self.rng.randint(1, 2)
                    for y in range(surface_y - 1, surface_y - trunk_height - 1, -1):
                        blocks[f"{tree_x},{y}"] = "log"
                    
                    # Leaves (smaller canopy for desert)
                    for dx in range(-1, 2):
                        for dy in range(-trunk_height - 1, -trunk_height - 3, -1):
                            if dx == 0 or dy == -trunk_height - 1:  # Smaller leaf pattern
                                blocks[f"{tree_x + dx},{surface_y + dy}"] = "leaves"
                    
                    # Add top leaf for better appearance
                    blocks[f"{tree_x},{surface_y - trunk_height - 2}"] = "leaves"
                    
                    placed_positions.add((tree_x, surface_y))
                    desert_tree_count += 1
        
        print(f"🌵 Generated {desert_tree_count} sparse desert trees")
    
    def _generate_simple_fortresses(self, blocks: Dict[str, str], world_width: int):
        """Generate red brick fortresses away from spawn (not in oceans)"""
        fortress_count = 0
        
        # Don't spawn fortresses too close to spawn (player starts at x=0)
        spawn_safe_zone = 100  # No fortresses within 100 blocks of spawn
        
        for x in range(-world_width//2, world_width//2, 120):  # Fortress every 120 blocks
            if self.rng.random() < 0.3:  # 30% chance for fortress
                # Skip if too close to spawn
                if abs(x) < spawn_safe_zone:
                    continue
                
                # Find surface by searching for grass block from top down (expanded range)
                surface_y = None
                for y in range(90, 140):
                    block = blocks.get(f"{x},{y}")
                    if block == "grass":
                        surface_y = y
                        break
                
                # Skip if no grass surface found (might be ocean/sand)
                if surface_y is None:
                    continue
                
                # Verify there's solid ground beneath the surface (prevent floating fortresses)
                has_solid_ground = False
                for y in range(surface_y + 1, surface_y + 10):  # Check 9 blocks below surface
                    block = blocks.get(f"{x},{y}")
                    if block in ["dirt", "stone", "sand"]:
                        has_solid_ground = True
                        break
                
                if not has_solid_ground:
                    print(f"⚠️ Skipping fortress at X={x} - no solid ground beneath surface")
                    continue
                
                # Place red brick fortress at calculated surface
                width = self.rng.randint(10, 18)
                height = self.rng.randint(10, 14)
                
                # Base platform - red brick
                for dx in range(width):
                    blocks[f"{x + dx},{surface_y}"] = "red_brick"
                
                # Add support pillars beneath fortress to prevent floating (fill any gaps with stone)
                for dx in range(width):
                    # Fill from surface down to the first solid block
                    for y in range(surface_y + 1, surface_y + 20):  # Check up to 20 blocks below
                        block_key = f"{x + dx},{y}"
                        current_block = blocks.get(block_key)
                        # If there's air or water, fill with stone for support
                        if current_block in [None, "air", "water"] or block_key not in blocks:
                            blocks[block_key] = "stone"
                        elif current_block in ["dirt", "stone", "sand", "grass"]:
                            # Hit solid ground, stop filling this column
                            break
                
                # Outer walls - red brick
                for dy in range(1, height + 1):
                    for dx in range(width):
                        if dx == 0 or dx == width - 1 or dy == height:  # Exterior walls
                            blocks[f"{x + dx},{surface_y - dy}"] = "red_brick"
                        else:
                            # Clear interior
                            key = f"{x + dx},{surface_y - dy}"
                            if key in blocks and blocks[key] not in ["air", None]:
                                blocks.pop(key)
                
                # Add floors inside - red brick
                for floor_offset in [3, 6, 9]:
                    floor_y = surface_y - floor_offset
                    for dx in range(2, width - 2):
                        blocks[f"{x + dx},{floor_y}"] = "red_brick"
                    
                    # Ladder to next floor
                    ladder_x = x + width // 2
                    blocks[f"{ladder_x},{floor_y + 1}"] = "ladder"
                    blocks[f"{ladder_x},{floor_y + 2}"] = "ladder"
                
                # Main entrance
                entrance_x = x + width // 2
                blocks[f"{entrance_x},{surface_y + 1}"] = "door"
                
                # Randomly decide if this fortress has monsters (50/50)
                has_monsters = self.rng.random() < 0.5
                if has_monsters:
                    # Spawn 3-5 monsters inside
                    monster_count = self.rng.randint(3, 5)
                    for _ in range(monster_count):
                        monster_x = x + self.rng.randint(2, width - 3)
                        monster_y = surface_y - self.rng.randint(2, height - 2)
                        # Check if position is valid (air)
                        if blocks.get(f"{monster_x},{monster_y}") in [None, "air"]:
                            # Monster will be spawned by the main script's fortress generation
                            # We'll mark it here, but actual spawning happens in build_fortress
                            pass
                
                fortress_count += 1
        
        print(f"🏰 Generated {fortress_count} red brick fortresses (away from spawn)")
    
    def _generate_simple_ores(self, blocks: Dict[str, str], world_width: int):
        """Generate ore distribution with proper rarity in the deep stone layer"""
        import math
        ore_count = 0
        water_level = 108
        
        # Generate ores for each column in the world
        for x in range(-world_width//2, world_width//2):
            # Find surface by searching for any solid block from top down
            surface_y = None
            for y in range(80, 140):
                block = blocks.get(f"{x},{y}")
                if block in ["grass", "sand", "stone", "dirt"]:
                    surface_y = y
                    break
            
            # Skip if no surface found
            if surface_y is None:
                continue
            
            bedrock_y = surface_y + 200
            
            # Try to place multiple ores per column
            for _ in range(3):  # Up to 3 ores per column
                ore_chance = self.rng.random()
                
                if ore_chance < 0.8:  # 80% chance for at least one ore per column
                    # Ore can spawn anywhere in the deep stone layer (200 blocks deep!)
                    min_ore_y = surface_y + 5
                    max_ore_y = bedrock_y - 1  # Almost to bedrock
                    y = self.rng.randint(min_ore_y, max_ore_y)
                    
                    # Check if position is stone
                    if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "stone":
                        # Depth-based ore rarity system
                        depth_from_surface = y - surface_y
                        depth_percentage = depth_from_surface / (bedrock_y - surface_y)
                        
                        # Ore rarity based on depth and random chance
                        ore_roll = self.rng.random()
                        
                        # Coal: Common (60% chance), spawns at any depth
                        if ore_roll < 0.6:
                            ore_type = "coal"
                        # Iron: Uncommon (25% chance), spawns at any depth
                        elif ore_roll < 0.85:
                            ore_type = "iron"
                        # Gold: Slightly rare (12% chance), spawns deeper (50%+ depth)
                        elif ore_roll < 0.97 and depth_percentage > 0.5:
                            ore_type = "gold"
                        # Diamond: Rare (3% chance), spawns very deep (80%+ depth)
                        elif depth_percentage > 0.8:
                            ore_type = "diamond"
                        else:
                            ore_type = "coal"  # Fallback to coal if conditions not met
                        
                        blocks[f"{x},{y}"] = ore_type
                        ore_count += 1
                    
                    # Reduce chance for additional ores
                    ore_chance = self.rng.random() * 0.4  # 40% chance for second ore, 16% for third
        
        print(f"⛏️ Generated {ore_count} ore veins with proper rarity distribution (coal=common, iron=uncommon, gold=slightly rare, diamond=rare)")
    
    def _find_spawn_location(self, blocks: Dict[str, str], world_width: int) -> Tuple[int, int]:
        """Find a good spawn location on grass land (NEVER in ocean/beach) - GUARANTEED"""
        
        print(f"🔍 Searching for spawn location in world with {len(blocks)} blocks")
        print(f"   World width: {world_width}, searching from X={-world_width//2} to X={world_width//2}")
        
        # AGGRESSIVE SEARCH: Search ENTIRE world for ANY grass block first
        all_grass_locations = []
        for spawn_x in range(-world_width//2, world_width//2):
            for y in range(90, 140):
                block = blocks.get(f"{spawn_x},{y}")
                if block == "grass":
                    # Check if there's dirt/stone below (valid grass)
                    below_block = blocks.get(f"{spawn_x},{y + 1}")
                    if below_block in ["dirt", "stone"]:
                        all_grass_locations.append((spawn_x, y))
        
        print(f"   Found {len(all_grass_locations)} grass locations in world!")
        
        if not all_grass_locations:
            print("❌ ERROR: NO GRASS BLOCKS GENERATED IN WORLD!")
            return 0, 110  # Return default, emergency platform will be created
        
        # Now find the BEST grass location (farthest from water)
        best_spawn = None
        best_distance_from_water = -1
        
        for spawn_x, y in all_grass_locations:
            # Calculate distance to nearest water
            min_water_distance = 999
            for check_x in range(spawn_x - 10, spawn_x + 11):
                for check_y in range(y - 5, y + 6):
                    check_block = blocks.get(f"{check_x},{check_y}")
                    if check_block == "water":
                        distance = abs(check_x - spawn_x) + abs(check_y - y)
                        if distance < min_water_distance:
                            min_water_distance = distance
            
            # If this location is farther from water, it's better
            if min_water_distance > best_distance_from_water:
                best_distance_from_water = min_water_distance
                best_spawn = (spawn_x, y)
        
        if best_spawn:
            spawn_x, y = best_spawn
            print(f"🏠 BEST spawn found on grass at ({spawn_x}, {y})")
            print(f"   ✅ Distance from water: {best_distance_from_water} blocks")
            return spawn_x, y - 2  # Spawn 2 blocks above surface
        
        # Fallback: just use first grass found
        spawn_x, y = all_grass_locations[0]
        print(f"🏠 Using first grass location at ({spawn_x}, {y})")
        return spawn_x, y - 2

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
