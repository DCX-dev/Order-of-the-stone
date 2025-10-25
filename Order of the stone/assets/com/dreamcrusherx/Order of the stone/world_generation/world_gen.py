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
        
        # Random ocean placement
        self.ocean_side = self.rng.choice(["left", "right", "center", "none"])
        
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
        print(f"🌊 Generated {ocean_blocks} water blocks and {sand_blocks} sand blocks")
        
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
        """Generate natural terrain with oceans, beaches, and proper hill contours"""
        import math
        
        # Clean, organized terrain generation - consistent but varied per world
        base_height = 115  # Consistent base height
        water_level = 108  # Water level for oceans
        
        for x in range(-world_width//2, world_width//2):
            # TRULY RANDOM TERRAIN using world's unique parameters
            # Each world gets different frequencies and offsets = truly unique terrain!
            primary_wave = 8 * math.sin((x + self.freq1_offset) * self.freq1_mult)
            secondary_wave = 4 * math.sin((x + self.freq2_offset) * self.freq2_mult)
            tertiary_wave = 2 * math.sin((x + self.freq3_offset) * self.freq3_mult)
            detail_wave = 1 * math.sin((x + self.freq4_offset) * self.freq4_mult)
            
            # Combine all waves for truly unique terrain per world
            height_variation = int(primary_wave + secondary_wave + tertiary_wave + detail_wave)
            surface_y = base_height + height_variation
            surface_y = max(100, min(125, surface_y))  # Normal land terrain
            
            # Check if this location should be ocean (based on world's ocean setting)
            is_ocean = False
            is_beach = False
            
            if self.ocean_side == "center":
                # Ocean in center with natural beach slopes
                distance_from_center = abs(x)
                if distance_from_center < 40:
                    # Deep ocean in center - MUCH DEEPER with natural variation
                    is_ocean = True
                    # Add natural variation to ocean depth (10-20 blocks deep)
                    depth_variation = self.rng.randint(-3, 3)
                    surface_y = water_level + 15 + depth_variation  # Ocean floor 12-18 blocks below water level
                elif distance_from_center < 80:
                    # Beach transition zone - WIDER transition for smoother slopes
                    is_beach = True
                    # Calculate beach slope: starts at normal land height, slopes down to ocean
                    beach_progress = (80 - distance_from_center) / 40  # 1.0 at ocean edge, 0.0 at land edge
                    normal_height = surface_y
                    ocean_height = water_level + 15  # Ocean floor depth
                    surface_y = int(normal_height - (beach_progress * (normal_height - ocean_height)))
            elif self.ocean_side == "left":
                # Ocean on left with beach transition
                if x < -60:
                    is_ocean = True
                    # Add natural variation to ocean depth
                    depth_variation = self.rng.randint(-3, 3)
                    surface_y = water_level + 15 + depth_variation  # Ocean floor 12-18 blocks below water level
                elif -90 < x < -60:
                    is_beach = True
                    beach_progress = (x + 90) / 30  # 0.0 at ocean edge, 1.0 at land edge (wider transition)
                    normal_height = surface_y
                    ocean_height = water_level + 15  # Ocean floor depth
                    surface_y = int(normal_height - (beach_progress * (normal_height - ocean_height)))
            elif self.ocean_side == "right":
                # Ocean on right with beach transition
                if x > 60:
                    is_ocean = True
                    # Add natural variation to ocean depth
                    depth_variation = self.rng.randint(-3, 3)
                    surface_y = water_level + 15 + depth_variation  # Ocean floor 12-18 blocks below water level
                elif 60 < x < 90:
                    is_beach = True
                    beach_progress = (90 - x) / 30  # 0.0 at ocean edge, 1.0 at land edge (wider transition)
                    normal_height = surface_y
                    ocean_height = water_level + 15  # Ocean floor depth
                    surface_y = int(normal_height - (beach_progress * (normal_height - ocean_height)))
            # self.ocean_side == "none" means no ocean at all - just normal terrain
            
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
                for y in range(surface_y + 1, surface_y + 5):
                    blocks[f"{x},{y}"] = "sand"
                # Ocean floor surface
                blocks[f"{x},{surface_y}"] = "sand"
                
                # Fill with water from water level DOWN to ocean floor (NO holes)
                # Water level is at y=108, ocean floor is at y=114 (deeper)
                # Fill from water_level (108) down to surface_y (114)
                for y in range(water_level, int(surface_y)):
                    blocks[f"{x},{y}"] = "water"
            elif is_beach:
                # Beach: sand layers that slope down to ocean
                for y in range(surface_y + 1, surface_y + 4):
                    blocks[f"{x},{y}"] = "sand"
                # Beach surface
                blocks[f"{x},{surface_y}"] = "sand"
                
                # Add water if beach is below water level (natural slope)
                if surface_y < water_level:
                    # Fill from water level DOWN to beach floor (not overwriting sand surface)
                    for y in range(water_level, int(surface_y)):
                        blocks[f"{x},{y}"] = "water"
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
                
                # Find surface by searching for grass block from top down
                surface_y = None
                for y in range(80, 130):
                    block = blocks.get(f"{tree_x},{y}")
                    if block == "grass":
                        surface_y = y
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
        """Generate larger, rarer fortresses away from spawn (not in oceans)"""
        fortress_count = 0
        
        # Don't spawn fortresses too close to spawn (player starts at x=0)
        spawn_safe_zone = 100  # No fortresses within 100 blocks of spawn
        
        for x in range(-world_width//2, world_width//2, 120):  # Fortress every 120 blocks (much rarer)
            if self.rng.random() < 0.4:  # 40% chance for fortress (rarer)
                # Skip if too close to spawn
                if abs(x) < spawn_safe_zone:
                    continue
                
                # Find surface by searching for grass block from top down
                surface_y = None
                for y in range(80, 130):
                    block = blocks.get(f"{x},{y}")
                    if block == "grass":
                        surface_y = y
                        break
                
                # Skip if no grass surface found (might be ocean/sand)
                if surface_y is None:
                    continue
                
                # Place fortress at calculated surface
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
                
                # Add some decorative elements
                if self.rng.random() < 0.6:
                    blocks[f"{x},{surface_y + 6}"] = "red_brick"  # Flag
                
                fortress_count += 1
        
        print(f"🏰 Generated {fortress_count} large fortresses (away from spawn)")
    
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
        """Find a good spawn location on grass land"""
        # Search from center outward for a grass block
        for spawn_x in range(0, 100, 5):
            # Find grass surface at this x
            for y in range(80, 130):
                block = blocks.get(f"{spawn_x},{y}")
                if block == "grass":
                    # Found grass! Spawn here
                    print(f"🏠 Spawn location found on grass at ({spawn_x}, {y})")
                    return spawn_x, y - 2  # Spawn 2 blocks above surface
        
        # Fallback - search harder
        for spawn_x in range(-50, 50):
            for y in range(80, 130):
                block = blocks.get(f"{spawn_x},{y}")
                if block == "grass":
                    print(f"🏠 Fallback spawn found at ({spawn_x}, {y})")
                    return spawn_x, y - 2
        
        # Last resort - spawn at center
        print("⚠️ No grass found, spawning at default location")
        return 0, 100

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
