# mods/blaster/main.py
MOD_INFO = {"id": "blaster", "version": "1.0.0"}

def register(api):
    # Register item (texture optional; you add assets/blaster.png)
    api.register_item("blaster", texture_rel_path="assets/blaster.png",
                      damage=10, speed=24, description="Test blaster")

    # Make sure it's always in every chest (and also heavily weighted as backup)
    api.add_guaranteed_chest_item("blaster")
    api.add_chest_loot("blaster", weight=1000)

    # Right-click behavior: shoot toward mouse/crosshair
    def use_blaster(ctx):
        player = ctx["player"]
        mouse_world = ctx["mouse_world"]
        spawn_projectile = ctx["spawn_projectile"]

        origin = _get_player_origin(player)
        direction = _direction_towards(origin, mouse_world)
        if direction and callable(spawn_projectile):
            spawn_projectile(origin, direction, speed=24, damage=10, owner="player")
        else:
            print("[blaster] Missing direction or spawn_projectile")

    api.set_item_use("blaster", use_blaster)

# ---------- helpers ----------
def _get_player_origin(player):
    # Try common shapes first (pos/position tuples), else x,y(,z)
    for attr in ("pos", "position", "world_pos", "world_position"):
        if hasattr(player, attr):
            p = getattr(player, attr)
            try:
                return tuple(p)
            except TypeError:
                pass
    if hasattr(player, "x") and hasattr(player, "y"):
        if hasattr(player, "z"):
            return (player.x, player.y, player.z)
        return (player.x, player.y)
    if isinstance(player, (tuple, list)):
        return tuple(player)
    return None

def _direction_towards(origin, target):
    if origin is None or target is None:
        return None
    try:
        o = tuple(origin); t = tuple(target)
    except TypeError:
        return None
    # Support 2D or 3D; if mismatch, fall back to 2D (x,y)
    if len(o) not in (2,3) or len(t) not in (2,3):
        return None
    if len(o) != len(t):
        o = (o[0], o[1]); t = (t[0], t[1])

    if len(o) == 2:
        dx, dy = t[0]-o[0], t[1]-o[1]
        mag = (dx*dx + dy*dy) ** 0.5
        if mag <= 1e-8: return None
        return (dx/mag, dy/mag)
    else:
        dx, dy, dz = t[0]-o[0], t[1]-o[1], t[2]-o[2]
        mag = (dx*dx + dy*dy + dz*dz) ** 0.5
        if mag <= 1e-8: return None
        return (dx/mag, dy/mag, dz/mag)