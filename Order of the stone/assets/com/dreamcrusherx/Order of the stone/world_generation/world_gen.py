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
            # RANDOM OCEAN BIOME - different position each world!
            is_ocean = False
            is_beach = False
            ocean_factor = 0
            
            if self.ocean_side == "center":
                # Ocean in center with beaches on both sides
                distance_from_center = abs(x)
                ocean_factor = math.exp(-(distance_from_center ** 2) / (2 * (world_width * 0.15) ** 2))
                is_ocean = ocean_factor > 0.7
                is_beach = 0.3 <= ocean_factor <= 0.7
            elif self.ocean_side == "left":
                # Ocean on left side only
                if x < -world_width * 0.2:
                    is_ocean = True
                elif -world_width * 0.2 <= x < -world_width * 0.1:
                    is_beach = True
            elif self.ocean_side == "right":
                # Ocean on right side only
                if x > world_width * 0.2:
                    is_ocean = True
                elif world_width * 0.1 < x <= world_width * 0.2:
                    is_beach = True
            # self.ocean_side == "none" means no ocean at all!
            
            # TRULY RANDOM TERRAIN using world's unique parameters
            # Each world gets different frequencies and offsets = truly unique terrain!
            primary_wave = 8 * math.sin((x + self.freq1_offset) * self.freq1_mult)
            secondary_wave = 4 * math.sin((x + self.freq2_offset) * self.freq2_mult)
            tertiary_wave = 2 * math.sin((x + self.freq3_offset) * self.freq3_mult)
            detail_wave = 1 * math.sin((x + self.freq4_offset) * self.freq4_mult)
            
            # Combine all waves for truly unique terrain per world
            height_variation = int(primary_wave + secondary_wave + tertiary_wave + detail_wave)
            surface_y = base_height + height_variation
            
            # Modify terrain based on biome
            if is_ocean:
                # Ocean floor is flat at water level - no artificial slopes
                surface_y = water_level + 8 + int(2 * math.sin(x * 0.2))  # Slight variation only
                surface_y = max(water_level + 6, min(water_level + 12, surface_y))  # Shallow, flat ocean floor
            elif is_beach:
                # Beach slopes naturally from land down to water level
                # Calculate distance from ocean for smooth slope using ocean_factor
                beach_progress = (0.7 - ocean_factor) / 0.4  # 0.0 at ocean edge, 1.0 at land edge
                beach_progress = max(0.0, min(1.0, beach_progress))
                
                # Natural slope: starts at land height, gradually slopes down to water level
                land_height = base_height + height_variation  # Normal land height
                slope_height = int(beach_progress * (land_height - water_level))  # Slope from land to water
                surface_y = water_level + slope_height + int(math.sin(x * 0.3))  # Natural beach slope
                surface_y = max(water_level - 3, min(land_height, surface_y))  # Between water and land
            else:
                # Normal terrain
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
            
            # 3. TERRAIN SURFACE LAYERS based on biome
            if is_ocean:
                # Ocean floor: sand layers
                for y in range(surface_y + 1, surface_y + 5):
                    if f"{x},{y}" not in blocks:
                        blocks[f"{x},{y}"] = "sand"
                # Ocean floor surface
                if f"{x},{surface_y}" not in blocks:
                    blocks[f"{x},{surface_y}"] = "sand"
                
                # Fill with water from ocean floor to water level
                for y in range(surface_y - 1, water_level - 1, -1):
                    if f"{x},{y}" not in blocks:
                        blocks[f"{x},{y}"] = "water"
                        
            elif is_beach:
                # Beach: sand layers
                for y in range(surface_y + 1, surface_y + 4):
                    if f"{x},{y}" not in blocks:
                        blocks[f"{x},{y}"] = "sand"
                # Beach surface
                if f"{x},{surface_y}" not in blocks:
                    blocks[f"{x},{surface_y}"] = "sand"
                
                # Add water if below water level
                if surface_y < water_level:
                    for y in range(surface_y - 1, water_level - 1, -1):
                        if f"{x},{y}" not in blocks:
                            blocks[f"{x},{y}"] = "water"
            else:
                # Normal terrain: dirt and grass
                # DIRT LAYER: 2 blocks below surface
                for y in range(surface_y + 1, surface_y + 3):
                    if f"{x},{y}" not in blocks:
                        blocks[f"{x},{y}"] = "dirt"
                
                # GRASS: ONLY at exact surface level
                if f"{x},{surface_y}" not in blocks:
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
        
        for cluster_x in cluster_centers:
            # Generate 2-3 trees in each cluster (clean, organized)
            cluster_size = self.rng.randint(2, 3)
            for _ in range(cluster_size):
                # Clean position within cluster (within 5 blocks of center)
                tree_x = cluster_x + self.rng.randint(-5, 5)
                
                # Find surface height using the SAME algorithm as terrain generation
                import math
                
                # Check if this is ocean or beach biome - no trees there
                center_x = 0
                ocean_width = world_width * 0.6
                distance_from_center = abs(tree_x - center_x)
                ocean_factor = math.exp(-(distance_from_center ** 2) / (2 * (ocean_width / 4) ** 2))
                
                is_ocean = ocean_factor > 0.7
                is_beach = 0.3 <= ocean_factor <= 0.7
                
                if is_ocean or is_beach:
                    continue  # Skip tree placement in oceans and beaches
                
                # Normal terrain tree placement
                base_height = 115
                primary_wave = 6 * math.sin(tree_x * 0.05)  # Match clean terrain
                secondary_wave = 3 * math.sin(tree_x * 0.15)
                tertiary_wave = 2 * math.sin(tree_x * 0.3)
                height_variation = int(primary_wave + secondary_wave + tertiary_wave)
                surface_y = base_height + height_variation
                surface_y = max(100, min(125, surface_y))
                
                if (tree_x, surface_y) not in placed_positions:
                    # Check if area is clear for tree
                    area_clear = True
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
                
                # Check if this is ocean or beach - no fortresses there
                import math
                center_x = 0
                ocean_width = world_width * 0.6
                distance_from_center = abs(x - center_x)
                ocean_factor = math.exp(-(distance_from_center ** 2) / (2 * (ocean_width / 4) ** 2))
                
                is_ocean = ocean_factor > 0.7
                is_beach = 0.3 <= ocean_factor <= 0.7
                
                if is_ocean or is_beach:
                    continue  # Skip fortress in ocean/beach
                    
                # Find surface height using the SAME algorithm as terrain generation
                base_height = 115
                primary_wave = 6 * math.sin(x * 0.05)
                secondary_wave = 3 * math.sin(x * 0.15)
                tertiary_wave = 2 * math.sin(x * 0.3)
                height_variation = int(primary_wave + secondary_wave + tertiary_wave)
                surface_y = base_height + height_variation
                surface_y = max(100, min(125, surface_y))
                
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
            # Calculate surface height using the same algorithm as terrain generation
            center_x = 0
            ocean_width = world_width * 0.6
            distance_from_center = abs(x - center_x)
            ocean_factor = math.exp(-(distance_from_center ** 2) / (2 * (ocean_width / 4) ** 2))
            
            is_ocean = ocean_factor > 0.7
            is_beach = 0.3 <= ocean_factor <= 0.7
            
            base_height = 115
            primary_wave = 6 * math.sin(x * 0.05)
            secondary_wave = 3 * math.sin(x * 0.15)
            tertiary_wave = 2 * math.sin(x * 0.3)
            height_variation = int(primary_wave + secondary_wave + tertiary_wave)
            surface_y = base_height + height_variation
            
            # Adjust surface based on biome
            if is_ocean:
                # Match the flat ocean floor from terrain generation
                surface_y = water_level + 8 + int(2 * math.sin(x * 0.2))
                surface_y = max(water_level + 6, min(water_level + 12, surface_y))
            elif is_beach:
                beach_progress = (0.7 - ocean_factor) / 0.4
                beach_progress = max(0.0, min(1.0, beach_progress))
                land_height = base_height + height_variation
                slope_height = int(beach_progress * (land_height - water_level))
                surface_y = water_level + slope_height + int(math.sin(x * 0.3))
                surface_y = max(water_level - 3, min(land_height, surface_y))
            else:
                surface_y = max(100, min(125, surface_y))
            
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
        """Find a good spawn location on land (not in ocean)"""
        import math
        
        # Try to find a spawn location on land, not in ocean
        for spawn_x in range(0, 100, 5):  # Search from center outward
            # Check if this is ocean or beach
            center_x = 0
            ocean_width = world_width * 0.6
            distance_from_center = abs(spawn_x - center_x)
            ocean_factor = math.exp(-(distance_from_center ** 2) / (2 * (ocean_width / 4) ** 2))
            
            is_ocean = ocean_factor > 0.7
            is_beach = 0.3 <= ocean_factor <= 0.7
            
            # Skip ocean and beach, find normal land
            if not is_ocean and not is_beach:
                # Calculate surface for normal land
                base_height = 115
                primary_wave = 6 * math.sin(spawn_x * 0.05)
                secondary_wave = 3 * math.sin(spawn_x * 0.15)
                tertiary_wave = 2 * math.sin(spawn_x * 0.3)
                height_variation = int(primary_wave + secondary_wave + tertiary_wave)
                surface_y = base_height + height_variation
                surface_y = max(100, min(125, surface_y))
                
                print(f"🏠 Spawn location found on land at x={spawn_x}")
                return spawn_x, surface_y - 2  # Spawn 2 blocks above surface
        
        # Fallback to center if no good land found (shouldn't happen)
        x = 0
        base_height = 115
        primary_wave = 6 * math.sin(x * 0.05)
        secondary_wave = 3 * math.sin(x * 0.15)
        tertiary_wave = 2 * math.sin(x * 0.3)
        height_variation = int(primary_wave + secondary_wave + tertiary_wave)
        surface_y = base_height + height_variation
        surface_y = max(100, min(125, surface_y))
        
        return x, surface_y - 2  # Spawn 2 blocks above surface

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
