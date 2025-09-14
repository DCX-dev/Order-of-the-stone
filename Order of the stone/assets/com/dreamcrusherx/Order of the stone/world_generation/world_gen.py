"""
Improved World Generation System
Generates beautiful Minecraft-style worlds with proper terrain layers
"""

import random
import math
from typing import Dict, Tuple, List
import time

class WorldGenerator:
    def __init__(self, seed: int = None):
        if seed is None:
            seed = random.randint(1, 1000000)
        self.rng = random.Random(seed)
        print(f"🌍 World Generator initialized with seed: {seed}")
    
    def generate_world(self, world_width: int = 400, world_height: int = 200, progress_callback=None) -> Dict:
        """Generate an infinite world with loading progress"""
        print(f"🌍 Starting infinite world generation ({world_width} blocks wide)...")
        
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
        
        # Generate terrain with progress updates
        print("🏔️ Generating infinite terrain...")
        self._generate_infinite_terrain(world_data["blocks"], world_width, progress_callback)
        
        # Add structures with progress updates
        print("🌳 Adding trees and forests...")
        self._generate_infinite_trees(world_data["blocks"], world_width, progress_callback)
        
        print("🏰 Adding villages and fortresses...")
        self._generate_infinite_structures(world_data["blocks"], world_width, progress_callback)
        
        print("⛏️ Adding ores...")
        self._generate_infinite_ores(world_data["blocks"], world_width, progress_callback)
        
        print("📦 Adding treasure chests...")
        self._generate_infinite_chests(world_data["blocks"], world_width, progress_callback)
        
        # Find spawn location
        spawn_x, spawn_y = self._find_spawn_location(world_data["blocks"], world_width)
        world_data["spawn_x"] = spawn_x
        world_data["spawn_y"] = spawn_y
        
        # Update player position to spawn location
        world_data["player"]["x"] = float(spawn_x)
        world_data["player"]["y"] = float(spawn_y)
        
        print(f"📍 Spawn location: ({spawn_x}, {spawn_y})")
        print(f"✅ Infinite world generation complete! Generated {len(world_data['blocks'])} blocks")
        
        return world_data
    
    def _generate_simple_terrain(self, blocks: Dict[str, str], world_width: int):
        """Generate terrain with flat forest areas and hills between them"""
        print("🌲 Generating forest-based terrain...")
        
        # First, determine forest areas (flat areas where trees will be)
        forest_areas = self._identify_forest_areas(world_width)
        
        # Generate terrain based on forest areas
        heights = []
        base_height = 115  # Base height for flat areas
        
        for x in range(-world_width//2, world_width//2):
            # Check if this x position is in a forest area
            in_forest = any(start <= x <= end for start, end in forest_areas)
            
            if in_forest:
                # Flat terrain for forests
                height = base_height
            else:
                # Smooth hilly terrain between forests
                # Create gentle, rolling hills using sine waves for smoothness
                hill_wavelength = 120  # Longer wavelength for smoother hills
                hill_amplitude = 12   # Height variation
                
                # Use sine wave for smooth hill transitions
                hill_phase = (x % hill_wavelength) / hill_wavelength * 2 * 3.14159
                sine_height = int(hill_amplitude * (1 + math.sin(hill_phase)) / 2)
                
                # Add a secondary smaller wave for more natural variation
                secondary_phase = (x % 60) / 60 * 2 * 3.14159
                secondary_height = int(3 * (1 + math.sin(secondary_phase)) / 2)
                
                # Combine the waves for natural-looking hills
                height = base_height + sine_height + secondary_height
                
                # Add very small random variation for natural feel
                height += self.rng.randint(-1, 1)
                height = max(110, min(135, height))  # Keep within reasonable bounds
            
            heights.append(height)
            
            # Generate terrain column
            for y in range(height, height + 200 + 15):
                if y == height:
                    blocks[f"{x},{y}"] = "grass"
                elif y < height + 4:
                    blocks[f"{x},{y}"] = "dirt"
                elif y < height + 200 + 4:
                    blocks[f"{x},{y}"] = "stone"
                else:
                    blocks[f"{x},{y}"] = "bedrock"
        
        print(f"🌲 Generated terrain with {len(forest_areas)} flat forest areas")
    
    def _identify_forest_areas(self, world_width: int) -> List[Tuple[int, int]]:
        """Identify areas where forests (flat terrain) should be placed"""
        forest_areas = []
        
        # Create forest areas every 100-150 blocks
        current_x = -world_width//2 + 50  # Start 50 blocks from edge
        
        while current_x < world_width//2 - 50:
            # Forest area size: 60-100 blocks wide
            forest_width = self.rng.randint(60, 100)
            forest_end = current_x + forest_width
            
            # Don't go beyond world bounds
            if forest_end > world_width//2 - 10:
                forest_end = world_width//2 - 10
            
            if forest_end > current_x + 40:  # Minimum forest size
                forest_areas.append((current_x, forest_end))
                print(f"🌲 Forest area: {current_x} to {forest_end} (width: {forest_end - current_x})")
            
            # Gap between forests: 40-80 blocks
            gap = self.rng.randint(40, 80)
            current_x = forest_end + gap
        
        # Ensure spawn area (around x=0) is in a forest
        spawn_forest = None
        for start, end in forest_areas:
            if start <= 0 <= end:
                spawn_forest = (start, end)
                break
        
        if not spawn_forest:
            # Create a forest around spawn if none exists
            spawn_forest = (-50, 50)
            forest_areas.append(spawn_forest)
            print(f"🌲 Created spawn forest: {spawn_forest[0]} to {spawn_forest[1]}")
        
        return forest_areas
    
    def _generate_infinite_terrain(self, blocks: Dict[str, str], world_width: int, progress_callback=None):
        """Generate infinite terrain with progress updates"""
        print("🌲 Generating infinite forest-based terrain...")
        
        # First, determine forest areas (flat areas where trees will be)
        forest_areas = self._identify_forest_areas(world_width)
        
        # Generate terrain based on forest areas
        heights = []
        base_height = 115  # Base height for flat areas
        
        total_columns = world_width
        for x in range(-world_width//2, world_width//2):
            # Update progress every 100 columns
            if progress_callback and x % 100 == 0:
                progress = (x + world_width//2) / total_columns * 25  # 25% for terrain
                progress_callback(f"Generating terrain... {int(progress)}%")
            
            # Check if this x position is in a forest area
            in_forest = any(start <= x <= end for start, end in forest_areas)
            
            if in_forest:
                # Flat terrain for forests
                height = base_height
            else:
                # Smooth hilly terrain between forests
                hill_wavelength = 120
                hill_amplitude = 12
                
                # Use sine wave for smooth hill transitions
                hill_phase = (x % hill_wavelength) / hill_wavelength * 2 * 3.14159
                sine_height = int(hill_amplitude * (1 + math.sin(hill_phase)) / 2)
                
                # Add secondary wave for natural variation
                secondary_phase = (x % 60) / 60 * 2 * 3.14159
                secondary_height = int(3 * (1 + math.sin(secondary_phase)) / 2)
                
                # Combine waves for natural hills
                height = base_height + sine_height + secondary_height
                height = max(110, min(135, height))
            
            heights.append(height)
            
            # Generate terrain column
            for y in range(height, height + 200 + 15):
                if y == height:
                    blocks[f"{x},{y}"] = "grass"
                elif y < height + 4:
                    blocks[f"{x},{y}"] = "dirt"
                elif y < height + 200 + 4:
                    blocks[f"{x},{y}"] = "stone"
                else:
                    blocks[f"{x},{y}"] = "bedrock"
        
        print(f"🌲 Generated infinite terrain with {len(forest_areas)} flat forest areas")
    
    def _generate_infinite_trees(self, blocks: Dict[str, str], world_width: int, progress_callback=None):
        """Generate trees only in flat forest areas with progress updates"""
        tree_count = 0
        placed_positions = set()
        
        # Get forest areas (same as terrain generation)
        forest_areas = self._identify_forest_areas(world_width)
        
        print(f"🌳 Placing trees in {len(forest_areas)} forest areas...")
        
        total_forests = len(forest_areas)
        for i, (forest_start, forest_end) in enumerate(forest_areas):
            # Update progress
            if progress_callback:
                progress = 25 + (i / total_forests) * 25  # 25-50% for trees
                progress_callback(f"Adding trees... {int(progress)}%")
            
            # Generate trees densely in each forest area
            forest_width = forest_end - forest_start
            tree_density = max(3, forest_width // 8)  # More trees in larger forests
            
            for _ in range(tree_density):
                # Random position within this forest area
                tree_x = self.rng.randint(forest_start + 5, forest_end - 5)
                
                # Find surface height (should be flat in forest areas)
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
                        # Place tree with varied height
                        trunk_height = self.rng.randint(3, 6)  # Taller trees in forests
                        for y in range(surface_y - 1, surface_y - trunk_height - 1, -1):
                            blocks[f"{tree_x},{y}"] = "log"
                        
                        # Larger leaf canopy for forest feel
                        leaf_radius = 2
                        for dx in range(-leaf_radius, leaf_radius + 1):
                            for dy in range(-trunk_height - 1, -trunk_height - 4, -1):
                                if abs(dx) + abs(dy + trunk_height + 2) <= leaf_radius + 1:  # Circular-ish pattern
                                    blocks[f"{tree_x + dx},{surface_y + dy}"] = "leaves"
                        
                        placed_positions.add((tree_x, surface_y))
                        tree_count += 1
        
        print(f"🌳 Generated {tree_count} trees in {len(forest_areas)} forest areas")
    
    def _generate_infinite_structures(self, blocks: Dict[str, str], world_width: int, progress_callback=None):
        """Generate villages and fortresses across the infinite world"""
        village_count = 0
        fortress_count = 0
        
        # Generate structures every 100-150 blocks
        structure_spacing = 120
        current_x = -world_width//2 + 100
        
        total_structures = world_width // structure_spacing
        structure_index = 0
        
        while current_x < world_width//2 - 100:
            # Update progress
            if progress_callback:
                progress = 50 + (structure_index / total_structures) * 25  # 50-75% for structures
                progress_callback(f"Building villages and fortresses... {int(progress)}%")
            
            # 40% chance for village
            if self.rng.random() < 0.4:
                self._generate_village_at(blocks, current_x)
                village_count += 1
            
            # 30% chance for fortress
            if self.rng.random() < 0.3:
                self._generate_fortress_at(blocks, current_x)
                fortress_count += 1
            
            # Move to next structure location
            current_x += structure_spacing + self.rng.randint(-20, 20)
            structure_index += 1
        
        print(f"🏰 Generated {village_count} villages and {fortress_count} fortresses")
    
    def _generate_infinite_ores(self, blocks: Dict[str, str], world_width: int, progress_callback=None):
        """Generate ores across the infinite world"""
        ore_count = 0
        
        # Generate ores every 50 blocks
        for x in range(-world_width//2, world_width//2, 50):
            # Update progress
            if progress_callback:
                progress = 75 + ((x + world_width//2) / world_width) * 25  # 75-100% for ores
                progress_callback(f"Adding ores... {int(progress)}%")
            
            # Generate 1-3 ore veins per location
            for _ in range(self.rng.randint(1, 3)):
                ore_x = x + self.rng.randint(-25, 25)
                ore_y = self.rng.randint(110, 140)  # Below surface
                
                # Check if position is stone
                if f"{ore_x},{ore_y}" in blocks and blocks[f"{ore_x},{ore_y}"] == "stone":
                    # Simple ore types
                    if ore_y < 120:
                        ore_type = "coal" if self.rng.random() < 0.7 else "iron"
                    else:
                        ore_type = "gold" if self.rng.random() < 0.6 else "diamond"
                    
                    blocks[f"{ore_x},{ore_y}"] = ore_type
                    ore_count += 1
        
        print(f"⛏️ Generated {ore_count} ore veins")
    
    def _generate_village_at(self, blocks: Dict[str, str], x: int):
        """Generate a village at a specific x coordinate"""
        # Find ground level
        ground_y = None
        for y in range(110, 125):
            if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "grass":
                ground_y = y
                break
        
        if not ground_y:
            return
        
        # Generate 2-4 houses
        house_count = self.rng.randint(2, 4)
        for i in range(house_count):
            house_x = x + self.rng.randint(-30, 30)
            house_y = ground_y
            
            # Simple house
            for dx in range(-3, 4):
                for dy in range(0, 4):
                    if dx in [-3, 3] or dy == 3:  # Walls
                        blocks[f"{house_x + dx},{house_y + dy}"] = "oak_planks"
                    else:  # Interior air
                        if f"{house_x + dx},{house_y + dy}" in blocks:
                            blocks.pop(f"{house_x + dx},{house_y + dy}")
            
            # Door
            blocks[f"{house_x},{house_y + 1}"] = "door"
    
    def _generate_fortress_at(self, blocks: Dict[str, str], x: int):
        """Generate a fortress at a specific x coordinate"""
        # Find ground level
        ground_y = None
        for y in range(110, 125):
            if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "grass":
                ground_y = y
                break
        
        if not ground_y:
            return
        
        # Simple fortress
        width = self.rng.randint(8, 15)
        height = self.rng.randint(6, 10)
        
        for dx in range(-width//2, width//2 + 1):
            for dy in range(0, height):
                if dx in [-width//2, width//2] or dy == height - 1:  # Walls
                    blocks[f"{x + dx},{ground_y + dy}"] = "stone"
                else:  # Interior air
                    if f"{x + dx},{ground_y + dy}" in blocks:
                        blocks.pop(f"{x + dx},{ground_y + dy}")
        
        # Entrance
        blocks[f"{x},{ground_y + 1}"] = "door"
    
    def _generate_simple_trees(self, blocks: Dict[str, str], world_width: int):
        """Generate trees only in flat forest areas"""
        tree_count = 0
        placed_positions = set()
        
        # Get forest areas (same as terrain generation)
        forest_areas = self._identify_forest_areas(world_width)
        
        print(f"🌳 Placing trees in {len(forest_areas)} forest areas...")
        
        for forest_start, forest_end in forest_areas:
            # Generate trees densely in each forest area
            forest_width = forest_end - forest_start
            tree_density = max(3, forest_width // 8)  # More trees in larger forests
            
            for _ in range(tree_density):
                # Random position within this forest area
                tree_x = self.rng.randint(forest_start + 5, forest_end - 5)
                
                # Find surface height (should be flat in forest areas)
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
                        # Place tree with varied height
                        trunk_height = self.rng.randint(3, 6)  # Taller trees in forests
                        for y in range(surface_y - 1, surface_y - trunk_height - 1, -1):
                            blocks[f"{tree_x},{y}"] = "log"
                        
                        # Larger leaf canopy for forest feel
                        leaf_radius = 2
                        for dx in range(-leaf_radius, leaf_radius + 1):
                            for dy in range(-trunk_height - 1, -trunk_height - 4, -1):
                                if abs(dx) + abs(dy + trunk_height + 2) <= leaf_radius + 1:  # Circular-ish pattern
                                    blocks[f"{tree_x + dx},{surface_y + dy}"] = "leaves"
                        
                        placed_positions.add((tree_x, surface_y))
                        tree_count += 1
        
        print(f"🌳 Generated {tree_count} trees in {len(forest_areas)} forest areas")
    
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
    
    def _generate_infinite_chests(self, blocks: Dict[str, str], world_width: int, progress_callback=None):
        """Generate chests throughout the world"""
        chest_count = 0
        
        for x in range(-world_width//2, world_width//2, 6):  # Every 6 blocks
            if progress_callback and x % 200 == 0:
                progress = (x + world_width//2) / world_width * 10  # 10% for chests
                progress_callback(f"Adding chests... {int(progress)}%")
            
            # 35% chance to place a chest at this location
            if self.rng.random() < 0.35:
                # Find ground level
                ground_y = None
                for y in range(110, 125):
                    if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "grass":
                        ground_y = y
                        break
                
                if ground_y is not None:
                    # Place chest on the ground
                    chest_x = x
                    chest_y = ground_y + 1
                    
                    # Make sure there's space for the chest
                    if f"{chest_x},{chest_y}" not in blocks:
                        blocks[f"{chest_x},{chest_y}"] = "chest"
                        chest_count += 1
                        
                        # Sometimes place underground chests too
                        if self.rng.random() < 0.4:  # 40% chance for underground chest
                            underground_y = ground_y - self.rng.randint(3, 8)
                            if f"{chest_x},{underground_y}" not in blocks:
                                blocks[f"{chest_x},{underground_y}"] = "chest"
                                chest_count += 1
        
        print(f"📦 Generated {chest_count} treasure chests")
    
    def _find_spawn_location(self, blocks: Dict[str, str], world_width: int) -> Tuple[int, int]:
        """Find a good spawn location in a forest area"""
        # Get forest areas to ensure spawn is in a forest
        forest_areas = self._identify_forest_areas(world_width)
        
        # Find spawn forest (the one containing x=0)
        spawn_forest = None
        for start, end in forest_areas:
            if start <= 0 <= end:
                spawn_forest = (start, end)
                break
        
        if not spawn_forest:
            # Fallback - use the first forest area
            spawn_forest = forest_areas[0] if forest_areas else (-50, 50)
        
        print(f"🌲 Looking for spawn in forest: {spawn_forest[0]} to {spawn_forest[1]}")
        
        # Look for a good spawn spot in the forest area
        forest_start, forest_end = spawn_forest
        
        # Try to find a clear spot in the forest (preferably near center)
        for x in range(max(forest_start, -20), min(forest_end, 21)):
            for y in range(110, 125):
                if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "grass":
                    # Check if area is clear (no trees or structures)
                    area_clear = True
                    for dx in range(-2, 3):
                        for dy in range(-1, 3):
                            check_x, check_y = x + dx, y + dy
                            if f"{check_x},{check_y}" in blocks and blocks[f"{check_x},{check_y}"] in ["log", "leaves", "red_brick", "stone", "chest", "door"]:
                                area_clear = False
                                break
                        if not area_clear:
                            break
                    
                    if area_clear:
                        print(f"🌲 Found clear spawn spot at ({x}, {y-2}) in forest")
                        return x, y - 2  # Spawn 2 blocks above grass
        
        # Fallback - spawn in forest even if not perfectly clear
        for x in range(forest_start, forest_end):
            for y in range(110, 125):
                if f"{x},{y}" in blocks and blocks[f"{x},{y}"] == "grass":
                    print(f"🌲 Fallback spawn at ({x}, {y-2}) in forest")
                    return x, y - 2
        
        # Last resort - spawn above expected surface level
        print("🌲 Emergency spawn at (0, 112)")
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
