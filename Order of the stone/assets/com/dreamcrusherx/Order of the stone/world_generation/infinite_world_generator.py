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
        """Generate terrain at a specific world position"""
        # Use noise for height variation
        height_noise = math.sin(x * 0.01) * 3 + math.sin(x * 0.05) * 2 + math.sin(x * 0.1) * 1
        base_height = 115
        surface_height = int(base_height + height_noise)
        
        # Generate terrain layers
        if y == surface_height:
            return "grass"
        elif y > surface_height and y < surface_height + 4:
            return "dirt"
        elif y >= surface_height + 4 and y < surface_height + 204:  # 200 blocks of stone
            return "stone"
        elif y == surface_height + 204:
            return "bedrock"
        else:
            return None  # Air
    
    def generate_structures_in_chunk(self, chunk_x: int, chunk_y: int, chunk_size: int = 16) -> Dict[str, str]:
        """Generate structures (trees, ores, etc.) in a chunk"""
        structures = {}
        
        # Calculate world coordinates for this chunk
        world_start_x = chunk_x * chunk_size
        world_start_y = chunk_y * chunk_size
        
        # Generate trees occasionally
        if self.rng.random() < 0.1:  # 10% chance per chunk
            tree_x = world_start_x + self.rng.randint(2, chunk_size - 3)
            tree_y = world_start_y + self.rng.randint(2, chunk_size - 3)
            
            # Find surface height at tree position
            height_noise = math.sin(tree_x * 0.01) * 3 + math.sin(tree_x * 0.05) * 2 + math.sin(tree_x * 0.1) * 1
            base_height = 115
            surface_height = int(base_height + height_noise)
            
            # Place tree if it's on the surface
            if tree_y == surface_height:
                # Tree trunk
                structures[f"{tree_x},{tree_y - 1}"] = "log"
                structures[f"{tree_x},{tree_y - 2}"] = "log"
                
                # Tree leaves
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        leaf_x = tree_x + dx
                        leaf_y = tree_y - 3 + dy
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
