# registries.py
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, List, Tuple

# ---------- Items ----------
@dataclass
class ItemDef:
    id: str
    texture_path: str | None = None
    props: Dict[str, Any] = field(default_factory=dict)

ITEMS: Dict[str, ItemDef] = {}         # item_id -> definition
ITEM_USE: Dict[str, Callable[[dict], None]] = {}  # item_id -> use(ctx) function

def register_item(item_id: str, texture_path: str | None = None, **props):
    if item_id in ITEMS:
        raise ValueError(f"Item already exists: {item_id}")
    ITEMS[item_id] = ItemDef(id=item_id, texture_path=texture_path, props=props)

def set_item_use(item_id: str, use_fn: Callable[[dict], None]):
    ITEM_USE[item_id] = use_fn

# ---------- Blocks (optional now) ----------
@dataclass
class BlockDef:
    id: str
    texture_path: str | None = None
    props: Dict[str, Any] = field(default_factory=dict)

BLOCKS: Dict[str, BlockDef] = {}
def register_block(block_id: str, texture_path: str | None = None, **props):
    if block_id in BLOCKS:
        raise ValueError(f"Block already exists: {block_id}")
    BLOCKS[block_id] = BlockDef(id=block_id, texture_path=texture_path, props=props)

# ---------- Entities (optional now) ----------
@dataclass
class EntityDef:
    id: str
    factory: Callable[..., Any] | None = None
    props: Dict[str, Any] = field(default_factory=dict)

ENTITIES: Dict[str, EntityDef] = {}
def register_entity(entity_id: str, factory=None, **props):
    if entity_id in ENTITIES:
        raise ValueError(f"Entity already exists: {entity_id}")
    ENTITIES[entity_id] = EntityDef(id=entity_id, factory=factory, props=props)

# ---------- Loot tables ----------
# Weighted random picks + "guaranteed" items that appear in every chest.
CHEST_LOOT: List[Tuple[str, int]] = []   # list of (item_id, weight)
GUARANTEED_CHEST_ITEMS: List[str] = []   # always included

def add_chest_loot(item_id: str, weight: int = 1):
    CHEST_LOOT.append((item_id, max(1, int(weight))))

def add_guaranteed_chest_item(item_id: str):
    if item_id not in GUARANTEED_CHEST_ITEMS:
        GUARANTEED_CHEST_ITEMS.append(item_id)