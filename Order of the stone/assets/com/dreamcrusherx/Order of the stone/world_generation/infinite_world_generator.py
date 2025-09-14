"""
Infinite World Generation System
Generates terrain on-demand as the player explores
"""

import random
import math
from typing import Dict, Tuple, Set

class InfiniteWorldGenerator:
    def __init__(self, seed: int = None):
        if seed is None:
            seed = random.randint(1, 1000000)
        self.rng = random.Random(seed)
        self.generated_chunks: Set[Tuple[int, int]] = set()
        print(f"🌍 Infinite World Generator initialized with seed: {seed}")
    
    def get_chunk_coordinates(self, world_x: int, world_y: int, chunk_size: int = 16) -> Tuple[int, int]:
        """Convert world coordinates to chunk coordinates"""
        chunk_x = world_x // chunk_size
        chunk_y = world_y // chunk_size
        return chunk_x, chunk_y
    
    def is_chunk_generated(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a chunk has already been generated"""
        return (chunk_x, chunk_y) in self.generated_chunks
    
    def generate_chunk(self, chunk_x: int, chunk_y: int, chunk_size: int = 16) -> Dict[str, str]:
        """Generate a chunk of terrain"""
        blocks = {}
        
        # Mark chunk as generated
        self.generated_chunks.add((chunk_x, chunk_y))
        
        # Calculate world coordinates for this chunk
        world_start_x = chunk_x * chunk_size
        world_start_y = chunk_y * chunk_size
        
        # Generate terrain for each position in the chunk
        for local_x in range(chunk_size):
            for local_y in range(chunk_size):
                world_x = world_start_x + local_x
                world_y = world_start_y + local_y
                
                # Generate terrain at this position
                block_type = self._generate_terrain_at(world_x, world_y)
                if block_type:
                    blocks[f"{world_x},{world_y}"] = block_type
        
        print(f"🌍 Generated chunk ({chunk_x}, {chunk_y}) with {len(blocks)} blocks")
        return blocks
    
    def _generate_terrain_at(self, x: int, y: int) -> str:
        """Generate terrain at a specific world position using forest-based system"""
        # Determine if this x position is in a forest area
        in_forest = self._is_in_forest_area(x)
        
        if in_forest:
            # Flat terrain for forests
            height = 115
        else:
            # Smooth hilly terrain between forests
            hill_wavelength = 120
            hill_amplitude = 12
            
            # Use sine wave for smooth hill transitions
            hill_phase = (x % hill_wavelength) / hill_wavelength * 2 * math.pi
            sine_height = int(hill_amplitude * (1 + math.sin(hill_phase)) / 2)
            
            # Add secondary wave for natural variation
            secondary_phase = (x % 60) / 60 * 2 * math.pi
            secondary_height = int(3 * (1 + math.sin(secondary_phase)) / 2)
            
            # Combine waves for natural hills
            height = 115 + sine_height + secondary_height
            height = max(110, min(135, height))  # Keep within bounds
        
        # Generate terrain layers
        if y < 100:
            return "bedrock"
        elif y < height:
            return "stone"
        elif y < height + 4:
            return "dirt"
        elif y == height:
            return "grass"
        else:
            return None  # Air
    
    def _is_in_forest_area(self, x: int) -> bool:
        """Check if x position is in a forest area"""
        # Create forest areas every 100-150 blocks
        forest_spacing = 120  # Average spacing between forests
        forest_width = 80     # Average forest width
        
        # Calculate which forest area this x position would be in
        forest_center = (x // forest_spacing) * forest_spacing
        forest_start = forest_center - forest_width // 2
        forest_end = forest_center + forest_width // 2
        
        return forest_start <= x <= forest_end
    
    def generate_structures_in_chunk(self, chunk_x: int, chunk_y: int, chunk_size: int = 16) -> Dict[str, str]:
        """Generate structures (trees, ores, etc.) in a chunk"""
        structures = {}
        
        # Calculate world coordinates for this chunk
        world_start_x = chunk_x * chunk_size
        world_start_y = chunk_y * chunk_size
        
        # Generate trees in forest areas
        for local_x in range(2, chunk_size - 2):
            world_x = world_start_x + local_x
            
            # Only generate trees in forest areas
            if self._is_in_forest_area(world_x) and self.rng.random() < 0.3:  # 30% chance in forests
                # Find surface height
                if self._is_in_forest_area(world_x):
                    surface_height = 115  # Flat in forests
                else:
                    hill_wavelength = 120
                    hill_amplitude = 12
                    hill_phase = (world_x % hill_wavelength) / hill_wavelength * 2 * math.pi
                    sine_height = int(hill_amplitude * (1 + math.sin(hill_phase)) / 2)
                    secondary_phase = (world_x % 60) / 60 * 2 * math.pi
                    secondary_height = int(3 * (1 + math.sin(secondary_phase)) / 2)
                    surface_height = 115 + sine_height + secondary_height
                    surface_height = max(110, min(135, surface_height))
                
                # Place tree
                tree_height = self.rng.randint(3, 6)  # Taller trees in forests
                for i in range(tree_height):
                    structures[f"{world_x},{surface_height - 1 - i}"] = "log"
                
                # Tree leaves with larger canopy
                leaf_radius = 2
                for dx in range(-leaf_radius, leaf_radius + 1):
                    for dy in range(-leaf_radius, leaf_radius + 1):
                        if abs(dx) + abs(dy) <= leaf_radius + 1:  # Circular-ish pattern
                            leaf_x = world_x + dx
                            leaf_y = surface_height - tree_height - 1 + dy
                            if leaf_x != world_x or leaf_y != surface_height - 1:  # Don't overwrite trunk
                                structures[f"{leaf_x},{leaf_y}"] = "leaves"
        
        # Generate ores occasionally
        for _ in range(self.rng.randint(0, 3)):  # 0-3 ores per chunk
            ore_x = world_start_x + self.rng.randint(0, chunk_size - 1)
            ore_y = world_start_y + self.rng.randint(0, chunk_size - 1)
            
            # Find surface height
            height_noise = math.sin(ore_x * 0.01) * 3 + math.sin(ore_x * 0.05) * 2 + math.sin(ore_x * 0.1) * 1
            base_height = 115
            surface_height = int(base_height + height_noise)
            
            # Place ore underground
            if ore_y > surface_height + 10:  # Deep enough
                ore_type = self.rng.choice(["coal", "iron", "gold", "diamond"])
                structures[f"{ore_x},{ore_y}"] = ore_type
        
        return structures

# Global instance
infinite_world_generator = InfiniteWorldGenerator()
