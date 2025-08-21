"""
Improved World Generation System
Generates beautiful Minecraft-style worlds with proper terrain layers
"""

import random
import math
import time
from typing import Dict, Any


class ImprovedWorldGenerator:
    """Generates beautiful Minecraft-style 2D worlds with proper terrain layers"""
    
    def __init__(self, seed: str = None):
        """Initialize the world generator with an optional seed"""
        self.seed = seed
        self.rng = random.Random(seed) if seed else random.Random()
    
    def generate_world(self, world_width: int = 200) -> Dict[str, Any]:
        """
        Generate a complete Minecraft-style world
        
        Args:
            world_width: Total width of the world (default 200 blocks)
            
        Returns:
            Dictionary containing world data with blocks, entities, and player spawn
        """
        print("🌍 Generating beautiful Minecraft-style world...")
        start_time = time.time()
        
        # Initialize world data
        world_data = {
            "blocks": {},
            "entities": [],
            "spawn_x": 0,
            "spawn_y": 0
        }
        
        # Generate terrain
        print("🏔️ Generating terrain layers...")
        self._generate_terrain(world_data["blocks"], world_width)
        
        # Generate structures
        print("🏗️ Generating structures...")
        self._generate_trees(world_data["blocks"], world_width)
        self._generate_chests(world_data["blocks"], world_width)
        self._generate_carrots(world_data["blocks"], world_width)
        self._generate_fortresses(world_data["blocks"], world_width)
        self._generate_villages(world_data["blocks"], world_width)
        self._generate_travelers(world_data["blocks"], world_width)  # Add travelers
        self._generate_ores(world_data["blocks"], world_width)  # Add ore generation
        self._generate_monsters(world_data["blocks"], world_width)
        
        # Set player spawn
        spawn_x, spawn_y = self._find_spawn_location(world_data["blocks"])
        world_data["spawn_x"] = spawn_x
        world_data["spawn_y"] = spawn_y
        
        generation_time = time.time() - start_time
        print(f"✅ World generated in {generation_time:.2f}s")
        print(f"📊 Generated {len(world_data['blocks'])} blocks")
        
        return world_data
    
    def _generate_terrain(self, blocks: Dict[str, str], world_width: int):
        """Generate terrain layers with proper Minecraft-style structure"""
        for x in range(-world_width//2, world_width//2):
            # Generate surface height with smooth variation
            base_height = 64  # Base surface level
            surface_height = base_height + int(math.sin(x * 0.1) * 8)  # Smooth hills
            
            # Ensure height is reasonable
            surface_height = max(56, min(72, surface_height))
            
            # Generate complete terrain column from surface down
            # Grass surface
            blocks[f"{x},{surface_height}"] = "grass"
            
            # Dirt layer (4 blocks deep below grass)
            for y in range(surface_height + 1, surface_height + 5):
                blocks[f"{x},{y}"] = "dirt"
            
            # Stone layer (8 blocks deep below dirt)
            for y in range(surface_height + 5, surface_height + 13):
                blocks[f"{x},{y}"] = "stone"
            
            # Bedrock at bottom (1 block at deepest level)
            blocks[f"{x},{surface_height + 13}"] = "bedrock"
            
            # Air above surface (clear sky) - leave more space for structures
            for y in range(surface_height - 1, max(0, surface_height - 25), -1):
                blocks[f"{x},{y}"] = "air"
    
    def _generate_trees(self, blocks: Dict[str, str], world_width: int):
        """Generate enhanced trees with TWO logs and improved leaf canopy"""
        print("🌳 Planting enhanced trees with TWO logs...")
        trees_generated = 0
        
        for x in range(-world_width//2, world_width//2, 8):  # Tree every 8 blocks
            surface_y = self._find_surface(blocks, x)
            if surface_y is not None:
                # Check if this area is inside a fortress (avoid spawning trees in fortresses)
                fortress_nearby = False
                for dx in range(-15, 16):  # Check 15 blocks in each direction
                    if blocks.get(f"{x + dx},{surface_y}") == "red_brick":
                        fortress_nearby = True
                        break
                
                if not fortress_nearby:
                    # Enhanced tree trunk - exactly TWO logs above grass (improved engineering)
                    blocks[f"{x},{surface_y - 1}"] = "log"  # First log above grass
                    blocks[f"{x},{surface_y - 2}"] = "log"  # Second log above first
                    
                    # Enhanced leaf canopy (3x3 rectangle above the two logs)
                    for dx in range(-1, 2):  # Left, center, right
                        for dy in range(-3, -1):  # Above the 2 logs
                            blocks[f"{x + dx},{surface_y + dy}"] = "leaves"
                    
                    # Add some random leaf variation for natural look (30% chance)
                    if random.random() < 0.3:
                        extra_dx = random.choice([-2, 2])  # Left or right extension
                        extra_dy = random.choice([-3, -4])  # Above logs
                        blocks[f"{x + extra_dx},{surface_y + extra_dy}"] = "leaves"
                    
                    trees_generated += 1
        
        print(f"🌳 Generated {trees_generated} enhanced trees (TWO logs, improved leaf canopy)")
    
    def _generate_chests(self, blocks: Dict[str, str], world_width: int):
        """Generate treasure chests above ground on grass"""
        print("📦 Hiding treasure chests...")
        chests_generated = 0
        
        for _ in range(15):  # 15 chests
            x = self.rng.randint(-world_width//2, world_width//2)
            surface_y = self._find_surface(blocks, x)
            
            if surface_y is not None:
                # Check if this area is inside a fortress (avoid spawning chests in fortresses)
                fortress_nearby = False
                for dx in range(-15, 16):  # Check 15 blocks in each direction
                    if blocks.get(f"{x + dx},{surface_y}") == "red_brick":
                        fortress_nearby = True
                        break
                
                if not fortress_nearby:
                    # Place chest above ground on grass
                    chest_y = surface_y - 1  # Above grass surface
                    blocks[f"{x},{chest_y}"] = "chest"
                    chests_generated += 1
        
        print(f"📦 Generated {chests_generated} treasure chests above ground")
    
    def _generate_carrots(self, blocks: Dict[str, str], world_width: int):
        """Generate carrots on surface"""
        print("🥕 Planting carrots...")
        carrots_generated = 0
        
        for _ in range(20):  # 20 carrots
            x = self.rng.randint(-world_width//2, world_width//2)
            surface_y = self._find_surface(blocks, x)
            
            if surface_y is not None:
                # Check if this area is inside a fortress (avoid spawning carrots in fortresses)
                fortress_nearby = False
                for dx in range(-15, 16):  # Check 15 blocks in each direction
                    if blocks.get(f"{x + dx},{surface_y}") == "red_brick":
                        fortress_nearby = True
                        break
                
                if not fortress_nearby:
                    # Place carrot above grass surface
                    blocks[f"{x},{surface_y - 1}"] = "carrot"
                    carrots_generated += 1
        
        print(f"🥕 Generated {carrots_generated} carrots")
    
    def _generate_fortresses(self, blocks: Dict[str, str], world_width: int):
        """Generate explorable fortresses without doors"""
        print("🏰 Building fortresses...")
        fortresses_generated = 0
        
        for _ in range(6):  # Fewer but bigger fortresses
            x = self.rng.randint(-world_width//2, world_width//2)
            surface_y = self._find_surface(blocks, x)
            
            if surface_y is not None:
                # Build EXTREME fortress above ground - exactly 20 blocks long!
                # Red brick outer frame (Nether Bricks) - 20x12 structure
                for dx in range(-10, 11):  # 20 blocks wide
                    for dy in range(-12, 1):  # 12 blocks tall, going UP from surface
                        fortress_y = surface_y + dy  # dy is negative, so this goes up from surface
                        if dx == -10 or dx == 10:  # Left and right pillars
                            blocks[f"{x + dx},{fortress_y}"] = "red_brick"
                        elif dy == 0:  # Top beam (at surface level)
                            blocks[f"{x + dx},{fortress_y}"] = "red_brick"
                        elif dy == -11 and (dx < -5 or dx > 5):  # Bottom beam, but leave center open
                            blocks[f"{x + dx},{fortress_y}"] = "red_brick"
                
                # Don't fill interior with stone - only platforms and ladders
                # This keeps fortresses explorable and clean
                
                # Stone brick base platform (at surface level) - full width
                for dx in range(-9, 10):
                    blocks[f"{x + dx},{surface_y}"] = "stone"
                
                # Multiple stone brick platforms at different levels going UP
                # Lower platforms (3 blocks above surface)
                for dx in range(-8, 9):
                    if dx != 0:  # Leave center open for ladder
                        blocks[f"{x + dx},{surface_y - 3}"] = "stone"
                
                # Middle platforms (6 blocks above surface)
                for dx in range(-7, 8):
                    if dx != 0:  # Leave center open for ladder
                        blocks[f"{x + dx},{surface_y - 6}"] = "stone"
                
                # Upper platforms (9 blocks above surface)
                for dx in range(-6, 7):
                    if dx != 0:  # Leave center open for ladder
                        blocks[f"{x + dx},{surface_y - 9}"] = "stone"
                
                # Top platforms (12 blocks above surface)
                for dx in range(-4, 5):
                    if dx != 0:  # Leave center open for ladder
                        blocks[f"{x + dx},{surface_y - 12}"] = "stone"
                
                # Multiple wooden ladders for easy climbing (vertical access going UP)
                # Main center ladder
                for dy in range(-11, 1):  # From bottom to top
                    blocks[f"{x},{surface_y + dy}"] = "log"  # Using log as ladder
                
                # Left side ladder
                for dy in range(-8, -2):  # Middle section
                    blocks[f"{x - 5},{surface_y + dy}"] = "log"
                
                # Right side ladder
                for dy in range(-8, -2):  # Middle section
                    blocks[f"{x + 5},{surface_y + dy}"] = "log"
                
                # Make fortress look run-down by adding some missing blocks and cracked stone
                # Randomly remove some red brick blocks to create gaps
                for dx in range(-10, 11):
                    if self.rng.random() < 0.1:  # 10% chance to remove a block
                        if dx != -10 and dx != 10:  # Don't remove corner pillars
                            blocks[f"{x + dx},{surface_y}"] = "air"  # Create gaps
                
                # Add some cracked stone blocks for run-down look
                for dx in range(-8, 9):
                    if self.rng.random() < 0.15:  # 15% chance for cracked stone
                        blocks[f"{x + dx},{surface_y - 1}"] = "stone"  # Replace some interior stone
                
                # Chests on platforms - more spread out
                blocks[f"{x - 3},{surface_y - 2}"] = "chest"  # Lower left
                blocks[f"{x + 3},{surface_y - 2}"] = "chest"  # Lower right
                blocks[f"{x - 5},{surface_y - 5}"] = "chest"  # Middle left
                blocks[f"{x + 5},{surface_y - 5}"] = "chest"  # Middle right
                blocks[f"{x - 4},{surface_y - 8}"] = "chest"  # Upper left
                blocks[f"{x + 4},{surface_y - 8}"] = "chest"  # Upper right
                blocks[f"{x - 2},{surface_y - 11}"] = "chest"  # Top left
                blocks[f"{x + 2},{surface_y - 11}"] = "chest"  # Top right
                
                fortresses_generated += 1
        
        print(f"🏰 Generated {fortresses_generated} BIG fortresses above ground")
    
    def _generate_villages(self, blocks: Dict[str, str], world_width: int):
        """Generate rare village houses with logs (smaller version of fortresses)"""
        print("🏘️ Building rare villages...")
        villages_generated = 0
        
        for _ in range(5):  # Only 5 villages - much rarer
            x = self.rng.randint(-world_width//2, world_width//2)
            
            # Make sure villages don't spawn near player spawn (0,0)
            if abs(x) < 20:  # Skip if too close to spawn
                continue
                
            surface_y = self._find_surface(blocks, x)
            
            if surface_y is not None:
                # Build village house - exactly 7 blocks long with logs
                # Log outer frame - 7 blocks wide
                for dx in range(-3, 4):  # 7 blocks wide
                    for dy in range(0, 4):  # 4 blocks tall
                        if dx == -3 or dx == 3:  # Left and right pillars
                            blocks[f"{x + dx},{surface_y + dy}"] = "log"
                        elif dy == 3:  # Top beam
                            blocks[f"{x + dx},{surface_y + dy}"] = "log"
                        elif dy == 0 and (dx < -2 or dx > 2):  # Bottom beam, but leave center open
                            blocks[f"{x + dx},{surface_y + dy}"] = "log"
                
                # Log base platform - full width
                for dx in range(-2, 3):
                    blocks[f"{x + dx},{surface_y}"] = "log"
                
                # Floating platforms inside
                blocks[f"{x - 2},{surface_y + 2}"] = "log"  # Left platform
                blocks[f"{x + 2},{surface_y + 2}"] = "log"  # Right platform
                
                # Ladder in center
                blocks[f"{x},{surface_y + 1}"] = "log"
                blocks[f"{x},{surface_y + 2}"] = "log"
                
                # Chest on left platform
                blocks[f"{x - 2},{surface_y + 3}"] = "chest"
                
                # Add a talking villager inside
                blocks[f"{x},{surface_y - 1}"] = "villager"
                
                villages_generated += 1
        
        print(f"🏘️ Generated {villages_generated} rare village houses with logs")
    
    def _generate_travelers(self, blocks: Dict[str, str], world_width: int):
        """Generate travelers around the world - some can turn into monsters"""
        print("🚶 Spawning travelers...")
        travelers_generated = 0
        
        attempts = 0
        max_attempts = 100  # Try more times to find good spots
        
        while travelers_generated < 12 and attempts < max_attempts:
            attempts += 1
            x = self.rng.randint(-world_width//2, world_width//2)
            
            # Make sure travelers don't spawn near player spawn
            if abs(x) < 15:  # Skip if too close to spawn
                continue
                
            surface_y = self._find_surface(blocks, x)
            
            if surface_y is not None:
                # Find a clear spot above the surface
                clear_y = self._find_clear_spot_above_surface(blocks, x, surface_y)
                if clear_y is not None:
                    # Some travelers are secretly monsters in disguise
                    if self.rng.random() < 0.3:  # 30% chance to be a monster
                        blocks[f"{x},{clear_y}"] = "monster"
                    else:
                        blocks[f"{x},{clear_y}"] = "traveler"
                    travelers_generated += 1
                # Continue trying to find spots
        
        print(f"🚶 Generated {travelers_generated} travelers (some are monsters in disguise)")
    
    def _generate_ores(self, blocks: Dict[str, str], world_width: int):
        """Generate ores underground in stone layers"""
        print("⛏️ Generating ores underground...")
        ores_generated = 0
        
        for _ in range(30):  # 30 ore veins
            x = self.rng.randint(-world_width//2, world_width//2)
            surface_y = self._find_surface(blocks, x)
            
            if surface_y is not None:
                # Place ores in stone layer (below dirt layer)
                ore_y = surface_y + self.rng.randint(5, 12)  # In stone layer
                
                # Different ore types with different rarity
                ore_chance = self.rng.random()
                if ore_chance < 0.4:  # 40% chance for coal
                    blocks[f"{x},{ore_y}"] = "coal"
                elif ore_chance < 0.7:  # 30% chance for iron
                    blocks[f"{x},{ore_y}"] = "iron"
                elif ore_chance < 0.85:  # 15% chance for gold
                    blocks[f"{x},{ore_y}"] = "gold"
                elif ore_chance < 0.95:  # 10% chance for diamond
                    blocks[f"{x},{ore_y}"] = "diamond"
                else:  # 5% chance for emerald
                    blocks[f"{x},{ore_y}"] = "emerald"
                
                ores_generated += 1
        
        print(f"⛏️ Generated {ores_generated} ore veins underground")
    
    def _generate_monsters(self, blocks: Dict[str, str], world_width: int):
        """Generate monster spawn points (not actual monsters) - they'll spawn at night"""
        print("👹 Setting up monster spawn points...")
        spawn_points = 0
        
        attempts = 0
        max_attempts = 50  # Try more times to find good spots
        
        while spawn_points < 15 and attempts < max_attempts:
            attempts += 1
            x = self.rng.randint(-world_width//2, world_width//2)
            surface_y = self._find_surface(blocks, x)
            
            if surface_y is not None:
                # Find a clear spot above the surface
                clear_y = self._find_clear_spot_above_surface(blocks, x, surface_y)
                if clear_y is not None:
                    # Place a monster spawn point (invisible marker)
                    blocks[f"{x},{clear_y}"] = "monster_spawn"
                    spawn_points += 1
        
        print(f"👹 Set up {spawn_points} monster spawn points (monsters spawn at night)")
    
    def _find_surface(self, blocks: Dict[str, str], x: int) -> int:
        """Find the grass surface at given X coordinate"""
        for y in range(56, 73):
            if blocks.get(f"{x},{y}") == "grass":
                return y
        return None
    
    def _find_clear_spot_above_surface(self, blocks: Dict[str, str], x: int, surface_y: int) -> int:
        """Find a clear spot above the surface for entities"""
        # Place entities at a very high level that should always be clear
        y = max(10, surface_y - 15)  # 15 blocks above surface, but at least Y=10
        return y
    
    def _find_spawn_location(self, blocks: Dict[str, str]) -> tuple:
        """Find a safe spawn location near world center"""
        spawn_x = 0
        spawn_y = self._find_surface(blocks, spawn_x)
        
        if spawn_y is not None:
            return spawn_x, spawn_y - 1  # Spawn above grass
        else:
            return 0, 63  # Fallback spawn


def generate_world(seed: str = None, world_width: int = 200) -> Dict[str, Any]:
    """
    Generate a new Minecraft-style world
    
    Args:
        seed: Optional seed for reproducible generation
        world_width: Width of the world in blocks
        
    Returns:
        World data dictionary
    """
    generator = ImprovedWorldGenerator(seed)
    return generator.generate_world(world_width)
