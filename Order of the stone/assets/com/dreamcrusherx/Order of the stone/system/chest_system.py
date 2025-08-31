#!/usr/bin/env python3
"""
📦 Enhanced Chest System for Order of the Stone
Guarantees sword and pickaxe in every chest with improved loot tables
"""

import random
from typing import Dict, List, Optional

class ChestSystem:
    """Enhanced chest management system with guaranteed essential items"""
    
    def __init__(self):
        # Add missing attributes needed by the main game
        self.chest_inventories = {}
        self.player_placed_chests = set()
        self.CHEST_ROWS = 4
        self.CHEST_COLS = 6
        
        # Enhanced loot tables with guaranteed essential items
        self.chest_loot_tables = {
            "village": [
                # GUARANTEED ITEMS (always included)
                {"item": "sword", "count": (1, 1), "chance": 1.0, "guaranteed": True},
                {"item": "pickaxe", "count": (1, 1), "chance": 1.0, "guaranteed": True},
                
                # COMMON ITEMS (high chance)
                {"item": "bread", "count": (1, 3), "chance": 0.9},
                {"item": "carrot", "count": (2, 5), "chance": 0.8},
                {"item": "coal", "count": (3, 6), "chance": 0.7},
                {"item": "stone", "count": (2, 4), "chance": 0.6},
                
                # UNCOMMON ITEMS (medium chance)
                {"item": "iron", "count": (1, 2), "chance": 0.5},
                {"item": "oak_planks", "count": (2, 4), "chance": 0.4},
                {"item": "dirt", "count": (3, 6), "chance": 0.4},
                
                # RARE ITEMS (low chance)
                {"item": "gold", "count": (1, 1), "chance": 0.3},
                {"item": "red_brick", "count": (1, 2), "chance": 0.2},
                {"item": "ladder", "count": (1, 1), "chance": 0.2},
                
                # VERY RARE ITEMS (very low chance)
                {"item": "diamond", "count": (1, 1), "chance": 0.1},
                {"item": "bed", "count": (1, 1), "chance": 0.05}
            ],
            "fortress": [
                # GUARANTEED ITEMS (always included)
                {"item": "sword", "count": (1, 1), "chance": 1.0, "guaranteed": True},
                {"item": "pickaxe", "count": (1, 1), "chance": 1.0, "guaranteed": True},
                
                # COMMON ITEMS (high chance)
                {"item": "iron", "count": (2, 4), "chance": 0.9},
                {"item": "coal", "count": (3, 8), "chance": 0.8},
                {"item": "stone", "count": (3, 6), "chance": 0.7},
                
                # UNCOMMON ITEMS (medium chance)
                {"item": "gold", "count": (1, 3), "chance": 0.6},
                {"item": "red_brick", "count": (2, 4), "chance": 0.5},
                {"item": "oak_planks", "count": (3, 6), "chance": 0.4},
                
                # RARE ITEMS (low chance)
                {"item": "diamond", "count": (1, 2), "chance": 0.4},
                {"item": "ladder", "count": (1, 2), "chance": 0.3},
                {"item": "bed", "count": (1, 1), "chance": 0.2}
            ],
            "dungeon": [
                # GUARANTEED ITEMS (always included)
                {"item": "sword", "count": (1, 1), "chance": 1.0, "guaranteed": True},
                {"item": "pickaxe", "count": (1, 1), "chance": 1.0, "guaranteed": True},
                
                # COMMON ITEMS (high chance)
                {"item": "diamond", "count": (2, 5), "chance": 0.9},
                {"item": "gold", "count": (3, 8), "chance": 0.8},
                {"item": "iron", "count": (5, 10), "chance": 0.7},
                
                # UNCOMMON ITEMS (medium chance)
                {"item": "coal", "count": (4, 8), "chance": 0.6},
                {"item": "stone", "count": (3, 6), "chance": 0.5},
                {"item": "red_brick", "count": (2, 4), "chance": 0.4},
                
                # RARE ITEMS (low chance)
                {"item": "bed", "count": (1, 1), "chance": 0.3},
                {"item": "ladder", "count": (1, 2), "chance": 0.2}
            ]
        }
    
    def generate_chest_loot(self, chest_type: str = "village") -> List[Dict]:
        """Generate enhanced loot for a chest based on its type with guaranteed items"""
        if chest_type not in self.chest_loot_tables:
            chest_type = "village"  # Default to village
        
        loot = []
        loot_table = self.chest_loot_tables[chest_type]
        
        # First, add all guaranteed items
        for item_data in loot_table:
            if item_data.get("guaranteed", False):
                count_range = item_data["count"]
                if isinstance(count_range, tuple):
                    count = random.randint(count_range[0], count_range[1])
                else:
                    count = count_range
                
                loot.append({
                    "type": item_data["item"],
                    "count": count
                })
        
        # Then, add random items based on chance
        for item_data in loot_table:
            if not item_data.get("guaranteed", False):  # Skip guaranteed items
                if random.random() < item_data["chance"]:
                    count_range = item_data["count"]
                    if isinstance(count_range, tuple):
                        count = random.randint(count_range[0], count_range[1])
                    else:
                        count = count_range
                    
                    loot.append({
                        "type": item_data["item"],
                        "count": count
                    })
        
        return loot
    
    def place_chest(self, world_system, x: int, y: int, chest_type: str = "village"):
        """Place a chest in the world with generated loot"""
        # Place chest block
        world_system.set_block(x, y, "chest")
        
        # Generate and store loot
        loot = self.generate_chest_loot(chest_type)
        
        # Store chest data in world
        chest_data = {
            "type": "chest",
            "x": x,
            "y": y,
            "chest_type": chest_type,
            "loot": loot,
            "opened": False
        }
        
        world_system.add_entity(chest_data)
    
    def is_chest_at(self, world_system, x: int, y: int) -> bool:
        """Check if there's a chest at the given coordinates"""
        entities = world_system.get_entities()
        
        for entity in entities:
            if (entity.get("type") == "chest" and 
                entity.get("x") == x and 
                entity.get("y") == y):
                return True
        
        return False
    
    # Add methods needed by the main game
    def get_chest_inventory(self, pos):
        """Get chest inventory at given position with guaranteed items"""
        if pos not in self.chest_inventories:
            # Check if this is a player-placed chest
            if pos in self.player_placed_chests:
                # Player-placed chests start empty
                self.chest_inventories[pos] = [None] * (self.CHEST_ROWS * self.CHEST_COLS)
                print(f"📦 Created EMPTY inventory for player-placed chest at {pos}")
            else:
                # Natural chests get generated loot
                self.chest_inventories[pos] = self._generate_chest_inventory(pos)
                print(f"📦 Generated loot for natural chest at {pos}")
        return self.chest_inventories[pos]
    
    def _generate_chest_inventory(self, pos):
        """Generate enhanced inventory for a chest at given position with guaranteed items"""
        # Determine chest type based on position (fortress vs village)
        x, y = pos
        chest_type = "fortress" if abs(x) > 20 else "village"  # Fortresses are far from spawn
        
        # Generate enhanced loot with guaranteed items
        loot = self.generate_chest_loot(chest_type)
        
        # Convert to inventory format (list of 24 slots)
        inventory = [None] * 24
        
        # Place guaranteed items first (sword and pickaxe)
        guaranteed_items = [item for item in loot if item["type"] in ["sword", "pickaxe"]]
        other_items = [item for item in loot if item["type"] not in ["sword", "pickaxe"]]
        
        # Place guaranteed items in first slots
        for i, item in enumerate(guaranteed_items):
            if i < len(inventory):
                inventory[i] = item
        
        # Place other items in random slots
        for item_data in other_items:
            if len(inventory) > 0:
                # Find empty slot
                empty_slots = [i for i, slot in enumerate(inventory) if slot is None]
                if empty_slots:
                    slot = random.choice(empty_slots)
                    inventory[slot] = item_data
        
        return inventory
    
    def create_player_placed_chest(self, pos):
        """Create a player-placed chest (empty)"""
        if pos not in self.player_placed_chests:
            self.player_placed_chests.add(pos)
            # Player-placed chests start completely empty
            self.chest_inventories[pos] = [None] * (self.CHEST_ROWS * self.CHEST_COLS)
            print(f"📦 Created EMPTY player-placed chest at {pos}")
        else:
            print(f"📦 Player-placed chest already exists at {pos}")
    
    def is_player_placed_chest(self, pos):
        """Check if a chest at the given position is player-placed"""
        return pos in self.player_placed_chests
    
    def open_chest(self, pos):
        """Open a chest at given position"""
        # This method is called when opening a chest
        # The actual inventory is handled by get_chest_inventory
        if pos not in self.chest_inventories:
            # Check if this is a player-placed chest
            if pos in self.player_placed_chests:
                # Player-placed chests start empty
                self.chest_inventories[pos] = [None] * (self.CHEST_ROWS * self.CHEST_COLS)
                print(f"📦 Opening EMPTY player-placed chest at {pos}")
            else:
                # Natural chests get generated loot
                self.chest_inventories[pos] = self._generate_chest_inventory(pos)
                print(f"📦 Opening natural chest with loot at {pos}")
        return self.chest_inventories[pos]
    
    def get_chest_info(self, pos):
        """Get information about a chest including its type and contents"""
        if pos in self.chest_inventories:
            inventory = self.chest_inventories[pos]
            item_count = sum(1 for item in inventory if item is not None)
            total_items = sum(item.get("count", 1) for item in inventory if item is not None)
            
            return {
                "type": "player_placed" if pos in self.player_placed_chests else "natural",
                "item_count": item_count,
                "total_items": total_items,
                "has_sword": any(item and item.get("type") == "sword" for item in inventory),
                "has_pickaxe": any(item and item.get("type") == "pickaxe" for item in inventory)
            }
        return None
