import random
from typing import Dict, List, Optional, Tuple, Any

class ChestSystem:
    """Manages chest behavior with Minecraft-style logic"""
    
    def __init__(self):
        # Track which chests are player-placed vs naturally spawned
        self.player_placed_chests: set = set()
        # Chest inventories
        self.chest_inventories: Dict[Tuple[int, int], List[Optional[Dict]]] = {}
        # Chest slots configuration
        self.CHEST_SLOTS = 27
        self.CHEST_ROWS = 3
        self.CHEST_COLS = 9
    
    def make_empty_slots(self, count: int) -> List[Optional[Dict]]:
        """Create empty chest slots"""
        return [None] * count
    
    def mark_chest_as_player_placed(self, pos: Tuple[int, int]):
        """Mark a chest as player-placed (will not get auto-loot)"""
        self.player_placed_chests.add(pos)
    
    def is_player_placed_chest(self, pos: Tuple[int, int]) -> bool:
        """Check if a chest was placed by a player"""
        return pos in self.player_placed_chests
    
    def is_natural_chest(self, pos: Tuple[int, int]) -> bool:
        """Check if a chest is naturally spawned"""
        return not self.is_player_placed_chest(pos)
    
    def ensure_chest_slots(self, pos: Tuple[int, int]):
        """Ensure a chest has inventory slots"""
        if pos not in self.chest_inventories:
            self.chest_inventories[pos] = self.make_empty_slots(self.CHEST_SLOTS)
    
    def generate_natural_chest_loot(self, pos: Tuple[int, int]):
        """Generate loot for naturally spawned chests"""
        self.ensure_chest_slots(pos)
        slots = self.chest_inventories[pos]
        
        # Always include sword and pickaxe in first two slots
        slots[0] = {"type": "sword", "count": 1}
        slots[1] = {"type": "pickaxe", "count": 1}
        
        # 99% chance to include ladders in a random empty slot
        if random.random() < 0.99:
            empty_idxs = [i for i, it in enumerate(slots) if it is None]
            if empty_idxs:
                slots[random.choice(empty_idxs)] = {"type": "ladder", "count": random.randint(3, 8)}
        
        # Fill a few random slots with blocks
        choices = ["dirt", "stone", "coal", "iron", "gold"]
        for i in range(2, self.CHEST_SLOTS):
            if random.random() < 0.5:
                slots[i] = {"type": random.choice(choices), "count": random.randint(1, 5)}
        
        # ~40% chance to include a bed in a random empty slot
        if random.random() < 0.40:
            empty_idxs = [i for i, it in enumerate(slots) if it is None]
            if empty_idxs:
                slots[random.choice(empty_idxs)] = {"type": "bed", "count": 1}
        
        # 1% chance diamond appears in a random empty slot
        if random.randint(1, 100) == 1:
            empty_idxs = [i for i, it in enumerate(slots) if it is None]
            if empty_idxs:
                idx = random.choice(empty_idxs)
                slots[idx] = {"type": "diamond", "count": 1}
    
    def create_player_placed_chest(self, pos: Tuple[int, int]):
        """Create an empty chest for player placement"""
        self.ensure_chest_slots(pos)
        self.mark_chest_as_player_placed(pos)
        # Player-placed chests start completely empty
        self.chest_inventories[pos] = self.make_empty_slots(self.CHEST_SLOTS)
    
    def open_chest(self, pos: Tuple[int, int]):
        """Open a chest - generate loot for natural chests if needed"""
        if pos not in self.chest_inventories:
            # This is a new chest that needs initialization
            if self.is_natural_chest(pos):
                # Natural chest - generate loot
                self.generate_natural_chest_loot(pos)
            else:
                # Player-placed chest - start empty
                self.create_player_placed_chest(pos)
    
    def get_chest_inventory(self, pos: Tuple[int, int]) -> List[Optional[Dict]]:
        """Get chest inventory, ensuring it exists"""
        if pos not in self.chest_inventories:
            self.open_chest(pos)
        return self.chest_inventories[pos]
    
    def set_chest_inventory(self, pos: Tuple[int, int], inventory: List[Optional[Dict]]):
        """Set chest inventory (for loading from save)"""
        self.chest_inventories[pos] = inventory
    
    def ensure_all_chests_have_inventories(self, world_data: Dict[Tuple[int, int], str]):
        """Ensure all chests in the world have proper inventories"""
        for (x, y), block_type in world_data.items():
            if block_type == "chest":
                pos = (x, y)
                if pos not in self.chest_inventories:
                    # New chest found - determine if natural or player-placed
                    if self.is_natural_chest(pos):
                        # Natural chest - generate loot
                        self.generate_natural_chest_loot(pos)
                    else:
                        # Player-placed chest - start empty
                        self.create_player_placed_chest(pos)
    
    def serialize_for_save(self) -> Dict[str, Any]:
        """Serialize chest data for saving"""
        chests_ser = {}
        for (cx, cy), slots in self.chest_inventories.items():
            key = f"{cx},{cy}"
            # Each slot is either None or a dict {"type": str, "count": int}
            safe_slots = []
            for it in slots:
                if it and isinstance(it, dict) and "type" in it:
                    safe_slots.append({"type": it["type"], "count": int(it.get("count", 1))})
                else:
                    safe_slots.append(None)
            chests_ser[key] = safe_slots
        
        # Also save which chests are player-placed
        player_placed_ser = [f"{x},{y}" for (x, y) in self.player_placed_chests]
        
        return {
            "chest_inventories": chests_ser,
            "player_placed_chests": player_placed_ser
        }
    
    def deserialize_from_save(self, data: Dict[str, Any]):
        """Load chest data from save"""
        # Load chest inventories
        self.chest_inventories = {}
        for key, slots in data.get("chest_inventories", {}).items():
            cx, cy = map(int, key.split(","))
            safe_slots = []
            for it in slots:
                if it and isinstance(it, dict) and "type" in it:
                    safe_slots.append({"type": it["type"], "count": int(it.get("count", 1))})
                else:
                    safe_slots.append(None)
            self.chest_inventories[(cx, cy)] = safe_slots
        
        # Load player-placed chest markers
        self.player_placed_chests = set()
        for key in data.get("player_placed_chests", []):
            cx, cy = map(int, key.split(","))
            self.player_placed_chests.add((cx, cy))
    
    def get_chest_slot_rect(self, col: int, row: int, ui_x: int, ui_y: int, slot_size: int, slot_margin: int) -> Tuple[int, int]:
        """Get chest slot position for UI drawing"""
        x = ui_x + 20 + col * (slot_size + slot_margin)
        y = ui_y + 50 + row * (slot_size + slot_margin)
        return x, y
