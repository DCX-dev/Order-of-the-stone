# api/mod_api.py
from typing import Callable, Any
import os
import registries as R

class ModAPI:
    """
    Public API for mods.
    NOTE: Mods are arbitrary Python — only load mods you trust.
    """
    def __init__(self, mod_id: str, mod_dir: str):
        self.mod_id = mod_id
        self.mod_dir = mod_dir   # folder of this mod (for textures, etc.)

    # Items
    def register_item(self, item_id: str, texture_rel_path: str | None = None, **props):
        tex = os.path.join(self.mod_dir, texture_rel_path) if texture_rel_path else None
        R.register_item(item_id, tex, **props)
        return item_id

    def set_item_use(self, item_id: str, use_fn: Callable[[dict], None]):
        """use_fn(ctx): ctx has player, mouse_world, spawn_projectile(...), etc."""
        R.set_item_use(item_id, use_fn)

    # Loot
    def add_chest_loot(self, item_id: str, weight: int = 1):
        R.add_chest_loot(item_id, weight)

    def add_guaranteed_chest_item(self, item_id: str):
        R.add_guaranteed_chest_item(item_id)

    # Blocks / Entities (available for later)
    def register_block(self, block_id: str, texture_rel_path: str | None = None, **props):
        tex = os.path.join(self.mod_dir, texture_rel_path) if texture_rel_path else None
        R.register_block(block_id, tex, **props)
        return block_id

    def register_entity(self, entity_id: str, factory=None, **props):
        R.register_entity(entity_id, factory, **props)
        return entity_id

    # Handy path for mod assets
    def mod_path(self, *parts: str) -> str:
        return os.path.join(self.mod_dir, *parts)