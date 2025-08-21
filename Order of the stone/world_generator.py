import time
import random
import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class TerrainType(Enum):
    """Terrain types for proper categorization"""
    GRASS = "grass"
    DIRT = "dirt"
    STONE = "stone"
    BEDROCK = "bedrock"
    WATER = "water"
    SAND = "sand"


class OreType(Enum):
    """Ore types with proper rarity and depth constraints"""
    COAL = ("coal", 0.4, 1, 8)      # Common, shallow
    IRON = ("iron", 0.2, 3, 12)     # Uncommon, medium depth
    GOLD = ("gold", 0.1, 6, 15)     # Rare, deep
    DIAMOND = ("diamond", 0.05, 8, 18)  # Very rare, very deep


@dataclass
class WorldConfig:
    """Configuration for Minecraft-style world generation"""
    world_width: int = 400  # Wider world for more continuous terrain
    surface_height: int = 64  # Base surface level
    stone_depth: int = 8  # Stone layer depth (always 8 blocks)
    dirt_depth: int = 4  # Dirt layer depth (always 4 blocks)
    bedrock_depth: int = 1  # Bedrock depth (always 1, always flat)
    
    # Structure generation settings
    tree_density: float = 0.3  # Trees every 3-4 blocks for natural forest
    chest_density: float = 0.15  # More chests for exploration
    fortress_density: float = 0.15  # More fortresses
    village_density: float = 0.12  # More villages
    carrot_density: float = 0.2  # More carrots for survival
    
    # Terrain settings
    min_height: int = 48  # Minimum surface height
    max_height: int = 80  # Maximum surface height
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if self.world_width <= 0 or self.world_width > 10000:
            raise ValueError("World width must be between 1 and 10000")
        if self.surface_height < 32 or self.surface_height > 128:
            raise ValueError("Surface height must be between 32 and 128")
        if self.stone_depth < 1 or self.stone_depth > 20:
            raise ValueError("Stone depth must be between 1 and 20")
        if self.bedrock_depth < 1 or self.bedrock_depth > 5:
            raise ValueError("Bedrock depth must be between 1 and 5")


class MinecraftTerrainGenerator:
    """Minecraft-style 2D terrain generation with proper coordinate system"""
    
    def __init__(self, seed: Optional[str] = None):
        self.seed = seed
        self.rng = random.Random(seed) if seed else random.Random()
        self.noise_cache = {}
        
        # Minecraft-style terrain constants
        self.BASE_HEIGHT = 64
        self.MAX_HEIGHT = 128
        self.MIN_HEIGHT = 32
        self.BEDROCK_Y = 127  # Bedrock at Y=127 (bottom of screen)
    
    def generate_surface_height(self, x: int) -> int:
        """Generate smooth, continuous surface height for Minecraft-style terrain"""
        # Use multiple noise layers for natural, smooth terrain
        base_height = 64  # Base surface level
        
        # Large-scale terrain variation (mountains and valleys)
        large_scale = math.sin(x * 0.02) * 16
        
        # Medium-scale variation (hills and small mountains)
        medium_scale = math.sin(x * 0.1) * 8
        
        # Small-scale variation (gentle rolling hills)
        small_scale = math.sin(x * 0.3) * 4
        
        # Very small variation (micro-terrain)
        micro_scale = math.sin(x * 0.8) * 2
        
        # Combine all noise layers for natural terrain
        surface_height = base_height + large_scale + medium_scale + small_scale + micro_scale
        
        # Ensure terrain stays within reasonable bounds for Minecraft-style world
        surface_height = max(52, min(76, surface_height))
        
        return int(surface_height)
    
    def _get_minecraft_noise(self, x: float, layer: int) -> float:
        """Get Minecraft-style noise value with caching for performance"""
        cache_key = (int(x * 1000), layer)
        if cache_key not in self.noise_cache:
            # Use Minecraft-style noise generation (multiple sine waves)
            noise = (math.sin(x * 0.5) * 0.5 + 
                    math.sin(x * 2.0) * 0.25 + 
                    math.sin(x * 8.0) * 0.125 +
                    math.sin(x * 16.0) * 0.0625)
            self.noise_cache[cache_key] = noise
        return self.noise_cache[cache_key]
    
    def generate_terrain_column(self, x: int, surface_y: int) -> Dict[str, str]:
        """Generate a complete, smooth terrain column from bedrock to surface"""
        terrain_blocks = {}
        
        # Debug: show what we're generating
        if x % 50 == 0:
            print(f"      🔧 Generating column X={x} with surface at Y={surface_y}")
        
        # Bedrock layer (Y=127) - always flat and continuous (bottom of screen)
        terrain_blocks[f"{x},127"] = "bedrock"
        
        # Stone layer (Y=119 to Y=126) - 8 blocks deep, always continuous
        for y in range(119, 127):
            terrain_blocks[f"{x},{y}"] = "stone"
        
        # Dirt layer (Y=115 to Y=118) - 4 blocks deep, always continuous
        for y in range(115, 119):
            terrain_blocks[f"{x},{y}"] = "dirt"
        
        # Grass surface (at surface_y) - always continuous
        terrain_blocks[f"{x},{surface_y}"] = "grass"
        
        # Air above surface - ensure it's actually air for proper rendering
        for y in range(surface_y - 1, max(0, surface_y - 20), -1):
            terrain_blocks[f"{x},{y}"] = "air"
        
        # Debug: show what blocks were created
        if x % 50 == 0:
            print(f"      🔧 Column X={x}: bedrock(127), stone(119-126), dirt(115-118), grass({surface_y}), air({surface_y-1}-{max(0, surface_y-20)})")
        
        return terrain_blocks

    def generate_terrain(self, config: WorldConfig) -> Dict[str, str]:
        """Generate complete, continuous Minecraft-style terrain"""
        blocks = {}
        print(f"   🏔️ Generating terrain columns...")
        
        # Generate terrain for EVERY X coordinate to ensure continuity
        for x in range(-config.world_width//2, config.world_width//2):
            # Generate surface height for this column
            surface_y = self.generate_surface_height(x)
            
            # Generate complete terrain column
            column_blocks = self.generate_terrain_column(x, surface_y)
            blocks.update(column_blocks)
        
        print(f"   ✅ Generated {len(blocks)} terrain blocks")
        return blocks


class MinecraftStructureGenerator:
    """Minecraft-style structure generation system"""
    
    def __init__(self, seed: Optional[str] = None):
        self.seed = seed
        self.rng = random.Random(seed) if seed else random.Random()
    
    def generate_trees(self, blocks: Dict[str, str], config: WorldConfig) -> int:
        """Generate natural-looking trees on grass surfaces"""
        trees_generated = 0
        print(f"   🌳 Generating trees...")
        
        # Find all grass surfaces for tree placement
        grass_surfaces = []
        for coord, block_type in blocks.items():
            if block_type == "grass":
                x, y = map(int, coord.split(","))
                grass_surfaces.append((x, y))
        
        print(f"      🌱 Found {len(grass_surfaces)} grass surfaces for tree placement")
        
        # Place trees on grass surfaces with natural density
        for x, surface_y in grass_surfaces:
            # Roll for tree placement based on density
            if self.rng.random() < config.tree_density:
                # Check if we can place a tree here
                if self._can_place_tree(x, surface_y, blocks):
                    # Generate the tree
                    tree_blocks = self._generate_minecraft_tree(x, surface_y)
                    blocks.update(tree_blocks)
                    trees_generated += 1
                    
                    if trees_generated % 5 == 0:
                        print(f"      🌳 Generated {trees_generated} trees so far...")
        
        print(f"   ✅ Generated {trees_generated} trees")
        return trees_generated
    
    def _can_place_tree(self, x: int, surface_y: int, blocks: Dict[str, str]) -> bool:
        """Check if tree can be placed at location (Minecraft-style spacing)"""
        # Super simple check - just ensure the grass surface is clear
        # Since terrain generation only creates blocks from Y=0 to surface, 
        # there should always be air above the surface
        return True  # Always allow tree placement for now
    
    def _generate_minecraft_tree(self, x: int, surface_y: int) -> Dict[str, str]:
        """Generate a Minecraft-style tree"""
        tree_blocks = {}
        # Tree trunk (4-6 blocks tall, like Minecraft)
        trunk_height = self.rng.randint(4, 6)
        for y in range(surface_y + 1, surface_y + 1 + trunk_height):
            tree_blocks[f"{x},{y}"] = "log"
        
        # Tree leaves (dense canopy like Minecraft)
        canopy_radius = self.rng.randint(2, 3)
        for dx in range(-canopy_radius, canopy_radius + 1):
            for dy in range(-canopy_radius, canopy_radius + 1):
                leaf_x, leaf_y = x + dx, surface_y + trunk_height + dy
                
                # Higher density in center, lower at edges (Minecraft-style)
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= canopy_radius and self.rng.random() < (1.0 - distance/canopy_radius):
                    # Don't overwrite trunk
                    if not (dx == 0 and dy < trunk_height):
                        tree_blocks[f"{leaf_x},{leaf_y}"] = "leaves"
        return tree_blocks
    
    def generate_ores(self, blocks: Dict[str, str], config: WorldConfig) -> int:
        """Generate Minecraft-style ores with proper depth constraints"""
        ores_generated = 0
        
        for ore_type in OreType:
            ore_name, rarity, min_depth, max_depth = ore_type.value
            
            # Calculate ore count based on rarity and world size
            ore_count = int(config.world_width * rarity * 0.1)
            
            for _ in range(ore_count):
                x = self.rng.randint(-config.world_width//2, config.world_width//2)
                
                # Find surface at this X
                surface_y = None
                for y in range(32, 128):
                    if blocks.get(f"{x},{y}") == "grass":
                        surface_y = y
                        break
                
                if surface_y:
                    # Place ore at appropriate depth (Minecraft-style)
                    # Depth is now measured from bedrock (Y=127) towards surface
                    depth = self.rng.randint(min_depth, max_depth)
                    ore_y = 127 - depth  # Start from bedrock and go up
                    
                    # Ensure we're placing in stone layer (Y=119-126)
                    if 119 <= ore_y <= 126 and blocks.get(f"{x},{ore_y}") == "stone":
                        blocks[f"{x},{ore_y}"] = ore_name
                        ores_generated += 1
        
        return ores_generated
    
    def generate_chests(self, blocks: Dict[str, str], config: WorldConfig) -> int:
        """Generate Minecraft-style chests in appropriate locations"""
        chests_generated = 0
        
        print(f"      🔍 Searching for chest locations in world width: {config.world_width}")
        
        for _ in range(int(config.world_width * config.chest_density)):  # Use config.chest_density
            x = self.rng.randint(-config.world_width//2, config.world_width//2)
            
            # Find surface
            surface_y = None
            for y in range(32, 128):
                if blocks.get(f"{x},{y}") == "grass":
                    surface_y = y
                    break
            
            if surface_y:
                # Place chest in stone layer (Y=119 to Y=126) - NOT below surface - be more aggressive
                for chest_y in range(119, 127):  # Try multiple depths in stone layer
                    
                    if blocks.get(f"{x},{chest_y}") == "stone":
                        blocks[f"{x},{chest_y}"] = "chest"
                        chests_generated += 1
                        if chests_generated % 5 == 0:
                            print(f"      📦 Generated {chests_generated} chests so far...")
                        break  # Found a spot, move to next chest
        
        return chests_generated
    
    def generate_carrots(self, blocks: Dict[str, str], config: WorldConfig) -> int:
        """Generate Minecraft-style carrots on grass surface"""
        carrots_generated = 0
        
        for _ in range(int(config.world_width * config.carrot_density)):  # Use config.carrot_density
            x = self.rng.randint(-config.world_width//2, config.world_width//2)
            
            # Find surface
            surface_y = None
            for y in range(32, 128):
                if blocks.get(f"{x},{y}") == "grass":
                    surface_y = y
                    break
            
            if surface_y:
                # Place carrot above grass (Minecraft-style)
                carrot_y = surface_y - 1  # Above grass surface
                if not blocks.get(f"{x},{carrot_y}"):  # Ensure no collision
                    blocks[f"{x},{carrot_y}"] = "carrot"
                    carrots_generated += 1
        
        return carrots_generated
    
    def generate_fortresses(self, blocks: Dict[str, str], config: WorldConfig) -> int:
        """Generate Minecraft-style fortresses with red brick - NO DOORS, BIGGER, EXPLORABLE"""
        fortresses_generated = 0
        
        print(f"      🔍 Searching for fortress locations in world width: {config.world_width}")
        
        for _ in range(int(config.world_width * config.fortress_density)):
            x = self.rng.randint(-config.world_width//2, config.world_width//2)
            
            # Find surface
            surface_y = None
            for y in range(32, 128):
                if blocks.get(f"{x},{y}") == "grass":
                    surface_y = y
                    break
            
            if surface_y:
                # Generate fortress (larger structure, no doors, explorable)
                if self._can_place_fortress(x, surface_y, blocks):
                    self._generate_single_fortress(x, surface_y, blocks)
                    fortresses_generated += 1
                    if fortresses_generated % 2 == 0:
                        print(f"      🏰 Generated {fortresses_generated} fortresses so far...")
        
        return fortresses_generated
    
    def _can_place_fortress(self, x: int, surface_y: int, blocks: Dict[str, str]) -> bool:
        """Check if fortress can be placed at location"""
        # Check for space for fortress (5x6 base)
        # Only check for non-terrain blocks (structures, trees, etc.)
        terrain_blocks = {"grass", "dirt", "stone", "bedrock"}
        
        for dx in range(-3, 4):
            for dy in range(0, 6):  # Check base area and walls
                check_x, check_y = x + dx, surface_y + dy
                block_type = blocks.get(f"{check_x},{check_y}")
                if block_type and block_type not in terrain_blocks:
                    return False
        return True
    
    def _generate_single_fortress(self, x: int, surface_y: int, blocks: Dict[str, str]):
        """Generate a single fortress with red brick - NO DOORS, BIGGER, EXPLORABLE"""
        # Fortress base (red brick) - 5x6 foundation
        for dx in range(-3, 4):
            for dy in range(0, 3):
                blocks[f"{x + dx},{surface_y + dy}"] = "red_brick"
        
        # Fortress walls (red brick) - 5x3 walls
        for dx in range(-3, 4):
            for dy in range(3, 6):
                blocks[f"{x + dx},{surface_y + dy}"] = "red_brick"
        
        # Fortress interior rooms (hollow spaces for exploration)
        # Main hall (3x3 hollow area)
        for dx in range(-1, 2):
            for dy in range(1, 4):
                if not (dx == 0 and dy == 2):  # Keep center wall for structure
                    blocks[f"{x + dx},{surface_y + dy}"] = "air"
        
        # Side rooms (hollow areas)
        for dx in [-2, 2]:
            for dy in range(1, 4):
                blocks[f"{x + dx},{surface_y + dy}"] = "air"
        
        # NO DOORS - completely open for exploration
        # Add some decorative elements and structural supports
        blocks[f"{x},{surface_y + 2}"] = "red_brick"  # Central pillar
        blocks[f"{x - 1},{surface_y + 5}"] = "red_brick"  # Left wall support
        blocks[f"{x + 1},{surface_y + 5}"] = "red_brick"  # Right wall support
    
    def generate_villages(self, blocks: Dict[str, str], config: WorldConfig) -> int:
        """Generate Minecraft-style villages with oak planks and logs - NO DOORS, EXPLORABLE"""
        villages_generated = 0
        
        print(f"      🔍 Searching for village locations in world width: {config.world_width}")
        
        for _ in range(int(config.world_width * config.village_density)):
            x = self.rng.randint(-config.world_width//2, config.world_width//2)
            
            # Find surface
            surface_y = None
            for y in range(32, 128):
                if blocks.get(f"{x},{y}") == "grass":
                    surface_y = y
                    break
            
            if surface_y:
                # Generate village (larger structure, no doors, explorable)
                if self._can_place_village(x, surface_y, blocks):
                    self._generate_single_village(x, surface_y, blocks)
                    villages_generated += 1
                    if villages_generated % 2 == 0:
                        print(f"      🏘️ Generated {villages_generated} villages so far...")
        
        return villages_generated
    
    def _can_place_village(self, x: int, surface_y: int, blocks: Dict[str, str]) -> bool:
        """Check if village can be placed at location"""
        # Check for space for smaller village (3x4 base)
        # Only check for non-terrain blocks (structures, trees, etc.)
        terrain_blocks = {"grass", "dirt", "stone", "bedrock"}
        
        for dx in range(-2, 3):
            for dy in range(0, 5):  # Check base area and walls
                check_x, check_y = x + dx, surface_y + dy
                block_type = blocks.get(f"{check_x},{check_y}")
                if block_type and block_type not in terrain_blocks:
                    return False
        return True
    
    def _generate_single_village(self, x: int, surface_y: int, blocks: Dict[str, str]):
        """Generate a single village with oak planks and logs - NO DOORS, EXPLORABLE, WITH VILLAGERS"""
        # Village house base (oak planks) - 3x3 foundation
        for dx in range(-2, 3):
            for dy in range(0, 3):
                blocks[f"{x + dx},{surface_y + dy}"] = "oak_planks"
        
        # Village house walls (oak planks) - 3x2 walls
        for dx in range(-2, 3):
            for dy in range(3, 5):
                blocks[f"{x + dx},{surface_y + dy}"] = "oak_planks"
        
        # Village house roof (logs) - 3x1 roof
        for dx in range(-2, 3):
            blocks[f"{x + dx},{surface_y + 5}"] = "log"
        
        # Village interior (hollow spaces for exploration)
        # Main room (hollow area)
        for dx in range(-1, 2):
            for dy in range(1, 4):
                blocks[f"{x + dx},{surface_y + dy}"] = "air"
        
        # NO DOORS - completely open for exploration
        # Add some decorative elements
        blocks[f"{x},{surface_y + 1}"] = "oak_planks"  # Central floor
        blocks[f"{x - 1},{surface_y + 3}"] = "oak_planks"  # Left wall
        blocks[f"{x + 1},{surface_y + 3}"] = "oak_planks"  # Right wall
        
        # Add a villager inside the house
        villager_x = x
        villager_y = surface_y + 2  # Inside the house
        blocks[f"{villager_x},{villager_y}"] = "villager"

    def generate_monsters(self, blocks: Dict[str, str], config: WorldConfig) -> int:
        """Generate monsters throughout the world for night-time encounters"""
        monsters_generated = 0
        
        print(f"      🔍 Generating monsters...")
        
        # Calculate monster count based on world size
        monster_count = int(config.world_width * 0.05)  # 5% of world width
        
        for _ in range(monster_count):
            x = self.rng.randint(-config.world_width//2, config.world_width//2)
            
            # Find surface at this X
            surface_y = None
            for y in range(32, 128):
                if blocks.get(f"{x},{y}") == "grass":
                    surface_y = y
                    break
            
            if surface_y:
                # Place monster above grass surface
                monster_y = surface_y - 1
                # Check if the spot is clear (no other entities or structures)
                block_type = blocks.get(f"{x},{monster_y}")
                if not block_type or block_type in {"air", "grass", "dirt", "stone", "bedrock"}:
                    blocks[f"{x},{monster_y}"] = "monster"
                    monsters_generated += 1
                    
                    if monsters_generated % 10 == 0:
                        print(f"      👹 Generated {monsters_generated} monsters so far...")
        
        print(f"   ✅ Generated {monsters_generated} monsters")
        return monsters_generated


class MinecraftWorldGenerator:
    """MINECRAFT-STYLE 2D WORLD GENERATOR WITH BEST ENGINEERING PRACTICES"""
    
    def __init__(self, seed: Optional[str] = None):
        self.seed = seed
        self.config = WorldConfig()
        self.terrain_generator = MinecraftTerrainGenerator(seed)
        self.structure_generator = MinecraftStructureGenerator(seed)
        
        # Performance metrics
        self.generation_start_time = time.time()
        self.blocks_generated = 0
        self.structures_generated = 0
    
    def generate_initial_world(self, name: str) -> Dict[str, Any]:
        """Generate a complete Minecraft-style world with best engineering practices"""
        print("🚀 Starting MINECRAFT-STYLE world generation...")
        
        try:
            # Phase 1: Terrain Generation
            print("🌍 Phase 1: Generating Minecraft-style terrain...")
            blocks = self._generate_terrain()
            
            # Phase 2: Structure Generation
            print("🏗️ Phase 2: Generating Minecraft-style structures...")
            self._generate_structures(blocks)
            
            # Phase 3: Player Setup
            print("👤 Phase 3: Setting up player spawn...")
            player_data = self._setup_player(blocks)
            
            # Phase 4: World Assembly
            print("🔧 Phase 4: Assembling world...")
            world_data = self._assemble_world(name, blocks, player_data)
            
            # Performance Report
            generation_time = time.time() - self.generation_start_time
            print(f"✅ Minecraft-style world generation completed in {generation_time:.2f}s")
            print(f"📊 Generated {self.blocks_generated} blocks, {self.structures_generated} structures")
            
            return world_data
            
        except Exception as e:
            print(f"❌ Critical error in world generation: {e}")
            # Return minimal world as fallback
            return self._generate_fallback_world(name)
    
    def _generate_terrain(self) -> Dict[str, str]:
        """Generate base Minecraft-style terrain with flat bedrock"""
        blocks = {}
        
        print("   🏔️ Generating terrain columns...")
        
        # Generate terrain columns for EVERY coordinate
        total_columns = 0
        for x in range(-self.config.world_width//2, self.config.world_width//2):
            # Generate surface height for this column
            surface_y = self.terrain_generator.generate_surface_height(x)
            
            # Debug: show some surface heights
            if x % 50 == 0:
                print(f"      📍 X={x}: surface at Y={surface_y}")
            
            # Generate complete terrain column
            column_blocks = self.terrain_generator.generate_terrain_column(x, surface_y)
            
            # Debug: verify column generation
            if x % 50 == 0:
                print(f"      🔧 Column X={x}: generated {len(column_blocks)} blocks")
                grass_blocks = [k for k, v in column_blocks.items() if v == "grass"]
                print(f"      🔧 Column X={x}: grass blocks: {grass_blocks}")
            
            # Debug: check non-sample coordinates too
            if x == -49:  # Check a specific problematic coordinate
                print(f"      🔍 DEBUG X=-49: surface_y={surface_y}, column_blocks={len(column_blocks)}")
                grass_blocks = [k for k, v in column_blocks.items() if v == "grass"]
                print(f"      🔍 DEBUG X=-49: grass blocks: {grass_blocks}")
                print(f"      🔍 DEBUG X=-49: all blocks: {list(column_blocks.items())[:10]}")
            
            # CRITICAL FIX: Ensure ALL blocks from the column are properly saved
            for coord, block_type in column_blocks.items():
                blocks[coord] = block_type
            
            total_columns += 1
            self.blocks_generated += len(column_blocks)
        
        print(f"   ✅ Generated {len(blocks)} terrain blocks from {total_columns} columns")
        
        # EXTREME VALIDATION: Verify that all columns have grass surfaces
        grass_count = len([k for k, v in blocks.items() if v == "grass"])
        print(f"   🔍 EXTREME VALIDATION: Found {grass_count} grass surfaces (should be {total_columns})")
        
        if grass_count != total_columns:
            print(f"   ⚠️ EXTREME WARNING: Missing grass surfaces! Expected {total_columns}, got {grass_count}")
            # Debug: check a few missing coordinates
            for x in range(-10, 11):
                if not any(k.startswith(f"{x},") and v == "grass" for k, v in blocks.items()):
                    print(f"   🔍 Missing grass at X={x}")
        
        return blocks
    
    def _generate_structures(self, blocks: Dict[str, str]):
        """Generate all Minecraft-style structures in the world"""
        print("   🌳 Generating trees...")
        trees = self.structure_generator.generate_trees(blocks, self.config)
        print(f"   ✅ Generated {trees} trees")
        
        print("   ⛏️ Generating ores...")
        ores = self.structure_generator.generate_ores(blocks, self.config)
        print(f"   ✅ Generated {ores} ore deposits")
        
        print("   📦 Generating chests...")
        chests = self.structure_generator.generate_chests(blocks, self.config)
        print(f"   ✅ Generated {chests} chests")
        
        print("   🥕 Generating carrots...")
        carrots = self.structure_generator.generate_carrots(blocks, self.config)
        print(f"   ✅ Generated {carrots} carrots")
        
        print("   🏰 Generating fortresses...")
        fortresses = self.structure_generator.generate_fortresses(blocks, self.config)
        print(f"   ✅ Generated {fortresses} fortresses")
        
        print("   🏘️ Generating villages...")
        villages = self.structure_generator.generate_villages(blocks, self.config)
        print(f"   ✅ Generated {villages} villages")
        
        print("   👹 Generating monsters...")
        monsters = self.structure_generator.generate_monsters(blocks, self.config)
        print(f"   ✅ Generated {monsters} monsters")
        
        self.structures_generated = trees + ores + chests + carrots + fortresses + villages + monsters
    
    def _setup_player(self, blocks: Dict[str, str]) -> Dict[str, Any]:
        """Set up player with proper Minecraft-style spawn positioning"""
        # Find safe spawn location at center of world
        spawn_x, spawn_y = self._find_safe_spawn(blocks)
        
        print(f"   📍 Player spawn set to ({spawn_x}, {spawn_y})")
        
        return {
            "x": float(spawn_x),
            "y": float(spawn_y),
            "vel_y": 0.0,
            "on_ground": False,
            "health": 10,
            "max_health": 10,
            "hunger": 100,
            "max_hunger": 100,
            "stamina": 100,
            "max_stamina": 100,
            "inventory": [],
            "backpack": [None] * 27,
            "selected": 0,
            "username": "",
            "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None},
            "character_class": "default"
        }
    
    def _find_safe_spawn(self, blocks: Dict[str, str]) -> tuple[int, int]:
        """Find a safe spawn location on the surface (center of world)"""
        # Start at center of world (X=0)
        spawn_x = 0
        
        # Find surface at center
        surface_y = None
        for y in range(32, 128):  # Search in reasonable height range
            if blocks.get(f"{spawn_x},{y}") == "grass":
                surface_y = y
                break
        
        if surface_y:
            # Check if spawn area is clear
            spawn_y = surface_y - 1  # Spawn above grass
            if self._is_spawn_area_clear(spawn_x, spawn_y, blocks):
                print(f"   🎯 Safe spawn found at ({spawn_x}, {spawn_y})")
                return spawn_x, spawn_y
        
        # Fallback: create spawn area at center
        print("   ⚠️ No safe spawn found, creating one at center")
        spawn_y = 63  # Above Y=64 surface
        return spawn_x, spawn_y
    
    def _is_spawn_area_clear(self, x: int, y: int, blocks: Dict[str, str]) -> bool:
        """Check if spawn area is clear of obstacles (3x3 area)"""
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                check_x, check_y = x + dx, y + dy
                if blocks.get(f"{check_x},{check_y}"):
                    return False
        return True
    
    def _assemble_world(self, name: str, blocks: Dict[str, str], player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble the complete world data with EXTREME validation"""
        print("   🔧 Assembling world data...")
        
        # EXTREME VALIDATION: Ensure all terrain blocks are present
        grass_count = len([k for k, v in blocks.items() if v == "grass"])
        bedrock_count = len([k for k, v in blocks.items() if v == "bedrock"])
        stone_count = len([k for k, v in blocks.items() if v == "stone"])
        
        print(f"   🔍 EXTREME VALIDATION: Blocks in world data:")
        print(f"      - Grass surfaces: {grass_count}")
        print(f"      - Bedrock blocks: {bedrock_count}")
        print(f"      - Stone blocks: {stone_count}")
        
        if grass_count < 400:
            print(f"   ⚠️ EXTREME WARNING: Missing grass surfaces! Expected 400, got {grass_count}")
            # Force regenerate missing terrain
            print(f"   🔧 Regenerating missing terrain...")
            for x in range(-200, 200):
                if not any(k.startswith(f"{x},") and v == "grass" for k, v in blocks.items()):
                    surface_y = self.terrain_generator.generate_surface_height(x)
                    column_blocks = self.terrain_generator.generate_terrain_column(x, surface_y)
                    for coord, block_type in column_blocks.items():
                        blocks[coord] = block_type
                    print(f"      🔧 Regenerated terrain for X={x}")
        
        world_data = {
            "name": name,
            "blocks": blocks,
            "entities": [],
            "player": player_data,
            "world_settings": {
                "day": True,
                "time": 0,  # Start at dawn
                "day_length": 24000,  # Minecraft-style day length
                "generation_version": "minecraft_2d_v2.0.0",
                "terrain_validated": True,
                "monster_spawning": True,  # Enable monster spawning
                "day_night_cycle": True,   # Enable day/night cycle
                "spawn_protection": True   # Enable spawn protection
            }
        }
        
        # Final validation
        final_grass_count = len([k for k, v in world_data["blocks"].items() if v == "grass"])
        print(f"   ✅ EXTREME SUCCESS: Final world has {final_grass_count} grass surfaces")
        
        return world_data
    
    def _generate_fallback_world(self, name: str) -> Dict[str, Any]:
        """Generate minimal fallback world if generation fails"""
        print("🆘 Generating fallback world...")
        
        blocks = {}
        # Create simple flat world (like Minecraft superflat)
        for x in range(-50, 50):
            for y in range(0, 128):
                if y == 127:
                    blocks[f"{x},{y}"] = "bedrock"  # Flat bedrock layer at bottom
                elif y >= 119:
                    blocks[f"{x},{y}"] = "stone"    # Stone layer
                elif y >= 115:
                    blocks[f"{x},{y}"] = "dirt"     # Dirt layer
                elif y == 114:
                    blocks[f"{x},{y}"] = "grass"    # Grass surface
                else:
                    blocks[f"{x},{y}"] = "air"      # Air above surface
        
        return {
            "name": f"{name} (Fallback)",
            "seed": "fallback",
            "created": time.time(),
            "last_saved": time.time(),
            "blocks": blocks,
            "entities": [],
            "player": {
                "x": 0.0,
                "y": 113.0,  # Above grass
                "vel_y": 0.0,
                "on_ground": False,
                "health": 10,
                "max_health": 10,
                "hunger": 100,
                "max_hunger": 100,
                "stamina": 100,
                "max_stamina": 100,
                "inventory": [],
                "backpack": [None] * 27,
                "selected": 0,
                "username": "",
                "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None},
                "character_class": "default"
            },
            "world_settings": {
                "time": time.time(),
                "day": True,
                "weather": "clear",
                "generation_version": "fallback",
                "monster_spawning": True,
                "day_night_cycle": True,
                "spawn_protection": True
            }
        }


# Legacy compatibility - keep the old class name for existing code
class WorldGenerator(MinecraftWorldGenerator):
    """Legacy compatibility class - use MinecraftWorldGenerator for new code"""
    pass


