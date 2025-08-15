import pygame
import random
import os
import time
import json
import shutil
import sys
import math

# Ensure the game runs from the correct directory (where the game files are located)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Allow proper macOS fullscreen Spaces behavior (must be set before set_mode)
if sys.platform == 'darwin':
    os.environ.setdefault('SDL_VIDEO_MAC_FULLSCREEN_SPACES', '1')



# --- Fullscreen/window settings ---
FULLSCREEN = False            # toggled via F11 or Options menu
WINDOWED_SIZE = (1280, 720)    # remember last windowed size for returning from fullscreen

# --- UI Centering Helpers ---
def center_x(w):
    return SCREEN_WIDTH // 2 - w // 2

def update_chest_ui_geometry():
    global CHEST_UI_W, CHEST_UI_H, CHEST_UI_X, CHEST_UI_Y, SLOT_SIZE, SLOT_MARGIN
    CHEST_UI_W = 480
    CHEST_UI_H = 210
    CHEST_UI_X = center_x(CHEST_UI_W)
    CHEST_UI_Y = (SCREEN_HEIGHT - CHEST_UI_H) // 2
    SLOT_SIZE = 40
    SLOT_MARGIN = 10

# Initialize
import pygame
from world_manager_v2 import WorldManager
from world_ui_v2 import WorldUI
from chest_system import ChestSystem
from world_preview import WorldPreview

pygame.init()



SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 32

def apply_display_mode():
    """Apply windowed or fullscreen mode and keep SCREEN_WIDTH/HEIGHT in sync."""
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT
    flags = pygame.RESIZABLE
    if FULLSCREEN:
        flags |= pygame.FULLSCREEN
        # 0,0 picks the desktop resolution in fullscreen
        screen = pygame.display.set_mode((0, 0), flags)
        info = pygame.display.Info()
        SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
    else:
        # Use the remembered windowed size
        w, h = WINDOWED_SIZE
        SCREEN_WIDTH, SCREEN_HEIGHT = w, h
        screen = pygame.display.set_mode((w, h), flags)
    pygame.display.set_caption("Order of the Stone")

apply_display_mode()

update_chest_ui_geometry()

# Helper for centered button rect
def centered_button(y, w=200, h=50):
    return pygame.Rect(center_x(w), y, w, h)

# Folders
TILE_DIR = "assets/tiles"
ITEM_DIR = "assets/items"
MOB_DIR = "assets/mobs"
PLAYER_DIR = "assets/player"
HP_DIR = "assets/HP"
SOUND_DIR = "damage"
SAVE_DIR = "save_data"

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def load_texture(path):
    return pygame.transform.scale(pygame.image.load(path).convert_alpha(), (TILE_SIZE, TILE_SIZE))

# --- Ladder Texture Generator ---
def make_ladder_texture(size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    base = (210, 160, 50)   # wood/yellow-orange
    rung = (180, 120, 30)
    # side rails
    rail_w = max(3, size // 8)
    pygame.draw.rect(surf, base, (0, 0, rail_w, size))
    pygame.draw.rect(surf, base, (size - rail_w, 0, rail_w, size))
    # rungs
    rung_h = max(2, size // 10)
    gap = size // 5
    y = rung_h
    while y < size - rung_h:
        pygame.draw.rect(surf, rung, (rail_w + 2, y, size - 2*rail_w - 4, rung_h))
        y += gap
    return surf

# --- Bed Texture Generator ---
def make_bed_texture(size):
    """Procedurally draw a simple bed (wood base, mattress, pillow, blanket)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # Colors
    wood = (140, 90, 40)
    wood_dark = (110, 70, 30)
    sheet = (232, 232, 232)
    pillow = (255, 255, 255)
    blanket = (190, 20, 20)
    outline = (20, 20, 20, 180)

    # Wooden base (bottom third)
    base_h = max(6, size // 3)
    pygame.draw.rect(surf, wood, (0, size - base_h, size, base_h))
    # Base shadow/edge
    pygame.draw.rect(surf, wood_dark, (0, size - base_h, size, 2))

    # Mattress (middle third)
    matt_h = max(5, size // 3)
    matt_y = size - base_h - matt_h
    pygame.draw.rect(surf, sheet, (2, matt_y, size - 4, matt_h))

    # Pillow (top area)
    pil_h = max(4, size // 6)
    pygame.draw.rect(surf, pillow, (2, 2, size - 4, pil_h))

    # Blanket (between pillow and mattress)
    blank_h = max(5, size // 4)
    blank_y = pil_h + 2
    if blank_y + blank_h > matt_y + matt_h:
        blank_h = max(4, (matt_y + matt_h) - blank_y - 2)
    pygame.draw.rect(surf, blanket, (2, blank_y, size - 4, blank_h))

    # Simple outline
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)

    return surf

# --- Door Texture Generator ---
def make_door_texture(size):
    """Procedurally draw a simple wooden door with handle."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    # Colors
    wood = (140, 90, 40)
    wood_dark = (110, 70, 30)
    wood_light = (160, 100, 50)
    handle = (200, 150, 50)
    outline = (20, 20, 20, 180)

    # Main door panel (full size)
    pygame.draw.rect(surf, wood, (0, 0, size, size))
    
    # Door frame/trim (darker wood around edges)
    trim_width = max(2, size // 16)
    pygame.draw.rect(surf, wood_dark, (0, 0, size, trim_width))  # Top
    pygame.draw.rect(surf, wood_dark, (0, size - trim_width, size, trim_width))  # Bottom
    pygame.draw.rect(surf, wood_dark, (0, 0, trim_width, size))  # Left
    pygame.draw.rect(surf, wood_dark, (size - trim_width, 0, trim_width, size))  # Right

    # Door panels (lighter wood sections)
    panel_width = (size - 2 * trim_width) // 2
    panel_height = (size - 2 * trim_width) // 2
    
    # Top left panel
    pygame.draw.rect(surf, wood_light, (trim_width, trim_width, panel_width, panel_height))
    # Top right panel
    pygame.draw.rect(surf, wood_light, (size - trim_width - panel_width, trim_width, panel_width, panel_height))
    # Bottom left panel
    pygame.draw.rect(surf, wood_light, (trim_width, size - trim_width - panel_height, panel_width, panel_height))
    # Bottom right panel
    pygame.draw.rect(surf, wood_light, (size - trim_width - panel_width, size - trim_width - panel_height, panel_width, panel_height))

    # Door handle (right side, middle height)
    handle_size = max(3, size // 10)
    handle_x = size - trim_width - handle_size - 2
    handle_y = size // 2 - handle_size // 2
    pygame.draw.circle(surf, handle, (handle_x, handle_y), handle_size)
    pygame.draw.circle(surf, wood_dark, (handle_x, handle_y), handle_size, 1)

    # Simple outline
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)

    return surf

# --- Villager Texture Generator ---
def make_villager_texture(size):
    """Procedural placeholder villager texture (used if mobs/villager.png is missing)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # Robe/body
    pygame.draw.rect(surf, (150, 85, 45), (4, 10, size - 8, size - 12))
    # Head
    pygame.draw.rect(surf, (230, 200, 170), (8, 0, size - 16, 14))
    # Eyes
    pygame.draw.rect(surf, (20, 20, 20), (size//2 - 6, 5, 3, 3))
    pygame.draw.rect(surf, (20, 20, 20), (size//2 + 3, 5, 3, 3))
    # Nose
    pygame.draw.rect(surf, (205, 170, 140), (size//2 - 1, 7, 2, 5))
    # Outline
    pygame.draw.rect(surf, (0, 0, 0, 180), (0, 0, size, size), 1)
    return surf

# Load textures
textures = {
    "grass": load_texture(os.path.join(TILE_DIR, "grass.png")),
    "dirt": load_texture(os.path.join(TILE_DIR, "dirt.png")),
    "stone": load_texture(os.path.join(TILE_DIR, "stone.png")),
    "bedrock": load_texture(os.path.join(TILE_DIR, "bedrock.png")),
    "carrot": load_texture(os.path.join(TILE_DIR, "carrot.gif")),
    "chest": load_texture(os.path.join(TILE_DIR, "chest.png")),
    "coal": load_texture(os.path.join(TILE_DIR, "coal.png")),
    "iron": load_texture(os.path.join(TILE_DIR, "iron.png")),
    "gold": load_texture(os.path.join(TILE_DIR, "gold.png")),
    "diamond": load_texture(os.path.join(TILE_DIR, "diamond.png")),
    "log": load_texture(os.path.join(TILE_DIR, "log.png")),
    "leaves": load_texture(os.path.join(TILE_DIR, "leaves.png")),
    "sword": load_texture(os.path.join(ITEM_DIR, "sword.png")),
    "pickaxe": load_texture(os.path.join(ITEM_DIR, "pickaxe.png")),
    "water": load_texture(os.path.join(TILE_DIR, "water.png")),
    "lava": load_texture(os.path.join(TILE_DIR, "lava.png")),
    "bed": load_texture(os.path.join(TILE_DIR, "bed.png")),
    "ladder": make_ladder_texture(TILE_SIZE),
    "door": make_door_texture(TILE_SIZE),
}

# --- Villager texture (tries file, falls back to procedural) ---
try:
    textures["villager"] = load_texture(os.path.join(MOB_DIR, "villager.png"))
except Exception:
    textures["villager"] = make_villager_texture(TILE_SIZE)

# --- Bed texture (tries file, falls back to a procedural bed texture) ---
try:
    textures["bed"] = load_texture(os.path.join(TILE_DIR, "bed.png"))  # preferred: assets/tiles/bed.png
except Exception:
    textures["bed"] = make_bed_texture(TILE_SIZE)

# --- Ladder texture (tries file, falls back to procedural ladder texture) ---
try:
    textures["ladder"] = load_texture(os.path.join(TILE_DIR, "ladder.png"))  # preferred: assets/tiles/ladder.png
except Exception:
    # keep the already-generated ladder texture if file missing
    textures["ladder"] = make_ladder_texture(TILE_SIZE)


player_image = load_texture(os.path.join(PLAYER_DIR, "player.gif"))
monster_image = load_texture(os.path.join(MOB_DIR, "monster.gif"))
alive_hp = load_texture(os.path.join(HP_DIR, "alive_hp.png"))
dead_hp = load_texture(os.path.join(HP_DIR, "dead_hp.png"))

# Load sound
damage_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "damage_sound.wav"))

# Fonts
font = pygame.font.SysFont("Arial", 24)
BIG_FONT = pygame.font.SysFont("Arial", 48)

# Initialize world management system
world_manager = WorldManager("save_data")
world_ui = WorldUI(SCREEN_WIDTH, SCREEN_HEIGHT, font)

# Initialize chest system
chest_system = ChestSystem()

# Initialize world preview system
world_preview = WorldPreview("save_data")

# Game states
STATE_TITLE = "title"
STATE_WORLD_SELECT = "world_select"
STATE_GAME = "game"
STATE_CONTROLS = "controls"
STATE_ABOUT = "about"
STATE_OPTIONS = "options"
STATE_DEAD = "dead"
game_state = STATE_TITLE

# Time and cycle
clock = pygame.time.Clock()
day_start_time = time.time()
is_day = True
hunger_timer = time.time()
paused_time = 0  # Track how long the game has been paused
last_pause_time = None  # Track when we last paused

# Player Data
player = {
    "x": 10,
    "y": 0,
    "vel_y": 0,
    "on_ground": False,
    "health": 10,
    "hunger": 10,
    "inventory": [],
    "selected": 0
}

MAX_FALL_SPEED = 10
GRAVITY = 1
JUMP_STRENGTH = -15
MOVE_SPEED = 0.1
SLOW_SPEED = 0.05

# World and camera
world_data = {}
entities = []
camera_x = 0
fall_start_y = None
# Village generation tracking
generated_village_chunks = set()

# --- Message HUD (temporary notifications) ---
message_text = ""
message_until = 0  # pygame.time.get_ticks() deadline

def show_message(text, ms=1500):
    global message_text, message_until
    message_text = text
    message_until = pygame.time.get_ticks() + ms

# --- Chest & Drag-and-Drop UI state ---
chest_open = False
open_chest_pos = None
drag_item = None           # {'type': str, 'count': int} currently held by mouse
drag_from = None           # ('chest', index) or ('hotbar', index)
mouse_pos = (0, 0)

# --- FPS and Performance Settings ---
fps_limit = 120  # Default FPS limit
show_fps = False  # F3 debug info
fps_counter = 0  # Actual FPS counter
last_fps_time = time.time()

def get_block(x, y):
    return world_data.get((x, y), None)

def set_block(x, y, block_type):
    world_data[(x, y)] = block_type



# --- Bedrock helper ---
def bedrock_level_at(x):
    """Return the y of the first bedrock block in column x, or None if not present."""
    # Scan a reasonable vertical range; bedrock is generated around ground_y + 7
    for y in range(0, 256):
        if get_block(x, y) == "bedrock":
            return y
    return None

# Helper for non-solid blocks
def is_non_solid_block(block):
    # Non-colliding blocks the player can pass through horizontally
    return block in (None, "air", "water", "lava", "carrot", "chest", "ladder", "door")

# Terrain helper: which blocks count as real ground for column generation
TERRAIN_BLOCKS = {"grass","dirt","stone","bedrock","coal","iron","gold","diamond"}


def column_has_terrain(x: int) -> bool:
    """Return True if column x already has at least one terrain block.
    This prevents leaves/carrots/chests placed in a not-yet-generated column
    from fooling the generator (which used to create vertical holes)."""
    for y in range(0, 128):
        if get_block(x, y) in TERRAIN_BLOCKS:
            return True
    return False

# --- Ground/placement helpers to avoid spawning inside trees ---

def ground_y_of_column(x: int):
    """Return the y of the grass surface for column x, or None if not found."""
    for y in range(0, 256):
        if get_block(x, y) == "grass":
            return y
    return None

# --- Village and House helpers ---
def build_house(origin_x, ground_y, width=7, height=5):
    """Build an improved log house with stone floor, open doorway, and interior chest."""
    # Floor
    for dx in range(width):
        set_block(origin_x + dx, ground_y, "stone")
    
    # Walls
    for dy in range(1, height + 1):
        for dx in range(width):
            x = origin_x + dx
            y = ground_y - dy
            edge = (dx == 0 or dx == width - 1)
            top = (dy == height)
            # doorway in the middle (2 blocks tall)
            door_x = origin_x + width // 2
            if (x == door_x and (y == ground_y - 1 or y == ground_y - 2)):
                # leave doorway empty for now, we'll add doors after
                continue
            if edge or top:
                set_block(x, y, "log")
            else:
                # interior air
                if get_block(x, y) not in (None, "air"):
                    # clear any leaves/logs, etc.
                    world_data.pop((x, y), None)
    
    # Leave doorway empty for players to place doors if they want
    # The opening is already created by the wall building loop above
    
    # Add a chest inside the house (left side, away from door)
    chest_x = origin_x + 1
    chest_y = ground_y - 1
    if get_block(chest_x, chest_y) is None:
        set_block(chest_x, chest_y, "chest")
        # Generate natural chest loot for village houses
        chest_system.generate_natural_chest_loot((chest_x, chest_y))

def spawn_villager(x, y):
    """Create a villager entity at tile x,y."""
    entities.append({
        "type": "villager",
        "x": float(x),
        "y": float(y),
        "dir": random.choice([-1, 1]),
        "step": 0
    })

def maybe_generate_village_for_chunk(chunk_id, base_x):
    """70% chance to create a small village (2-4 houses) in this 50-wide chunk."""
    if chunk_id in generated_village_chunks:
        return
    rng = random.Random(f"village-{chunk_id}")
    if rng.random() < 0.15:
        # choose number of houses and spacing
        house_count = rng.randint(1, 2)
        spacing = rng.randint(10, 16)
        start_x = base_x + rng.randint(5, 15)
        last_house_ground_y = None
        for i in range(house_count):
            hx = start_x + i * spacing
            gy = ground_y_of_column(hx)
            if gy is None:
                # fallback to sine terrain estimate
                gy = 10 + int(3 * math.sin(hx * 0.2))
                # ensure terrain exists under house
                set_block(hx, gy, "grass")
                for y in range(gy + 1, gy + 7):
                    set_block(hx, y, "dirt" if y < gy + 4 else "stone")
                set_block(hx, gy + 7, "bedrock")
            
            # Fill any holes under the house foundation with clean layering
            house_width = 7  # Same width as used in build_house
            for dx in range(house_width):
                # Ensure clean layer hierarchy under houses
                for y in range(gy + 1, 22):  # Fill down to flat bedrock at Y=22
                    if get_block(hx + dx, y) is None:
                        if y < gy + 4:
                            set_block(hx + dx, y, "dirt")      # Dirt layer
                        elif y < 22:
                            set_block(hx + dx, y, "stone")     # Stone layer
                        else:
                            set_block(hx + dx, y, "bedrock")   # Bedrock layer
                
                # Ensure NO blocks below bedrock
                for y in range(23, 100):
                    if get_block(hx + dx, y) is not None:
                        world_data.pop((hx + dx, y), None)  # Remove any blocks below bedrock
            # build the house aligned to current ground
            build_house(hx, gy, width=7, height=5)
            # spawn 1–2 villagers near the doorway
            spawn_villager(hx + 3, gy - 1)
            if rng.random() < 0.5:
                spawn_villager(hx + 2, gy - 1)
        generated_village_chunks.add(chunk_id)


def can_place_surface_item(x: int, ground_y: int) -> bool:
    """True if we can place a surface item (carrot/chest) at (x, ground_y-1)
    without intersecting tree trunks or leaf canopies and only if the spot is empty.
    """
    # must be grass at ground and air directly above
    if get_block(x, ground_y) != "grass":
        return False
    if get_block(x, ground_y - 1) is not None:
        return False

    # avoid tree trunk in this column
    if get_block(x, ground_y - 1) == "log" or get_block(x, ground_y - 2) == "log":
        return False

    # avoid leaf canopy immediately above the ground (from any direction)
    for dy in (-2, -3, -4):
        if get_block(x, ground_y + dy) == "leaves":
            return False

    return True

# --- Carrot biome helper (10% chance per 50-wide chunk) ---
def in_carrot_biome(x):
    """Return True if world column x belongs to a 'carrot biome'.
    Deterministic per 50-column chunk so the same columns stay in the same biome across sessions.
    """
    chunk = math.floor(x / 50)
    rng = random.Random(f"carrot-{chunk}")
    return rng.random() < 0.10

# --- Hotbar normalization helper ---
def normalize_inventory():
    """Remove trailing None entries and collapse any internal Nones to the end so UI code is safe."""
    # Keep at most 9 slots
    inv = player.get("inventory", [])
    # Compact: keep only dict items or well-formed entries
    compacted = [it for it in inv if it and isinstance(it, dict) and "type" in it and "count" in it and it["count"] > 0]
    player["inventory"] = compacted[:9]

def draw_button(text, x, y, w, h):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, (100, 100, 100), rect)
    pygame.draw.rect(screen, (255, 255, 255), rect, 2)
    label = font.render(text, True, (255, 255, 255))
    screen.blit(label, (x + 10, y + 10))
    return rect

def draw_controls():
    global back_btn
    screen.fill((0, 0, 0))
    controls = [
        "Controls:", "A/D - Move", "Space - Jump", "1–9 - Select Item",
        "Left Click - Break Block / Attack (with sword)", "Right Click - Place Block",
        "Right Click on Chest - Open chest UI", "Right Click on Bed (night) - Sleep (fade to day)",
        "ESC - Pause/Menu"
        ]
    for i, line in enumerate(controls):
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (100, 100 + i * 30))
    back_btn = draw_button("Back", 320, 500, 160, 40)

# --- About Screen ---
def draw_about():
    global back_btn
    screen.fill((0, 0, 0))
    about_lines = [
        "Order of the Stone",
        "A 2D sandbox survival game.",
        "Explore, mine, and fight off monsters.",
        "Find carrots to restore health.",
        "Use swords to battle enemies.",
        "Sleep in beds at night to skip to day (with a fade).",
        "Open chests to loot items and manage inventory.",
        "Ladders let you climb; bedrock is unbreakable.",
        "Inspired by Minecraft.",
        "Created by DreamCrusherX"
    ]
    for i, line in enumerate(about_lines):
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (100, 100 + i * 30))
    back_btn = draw_button("Back", 320, 500, 160, 40)

def draw_options():
    """Options page: toggle fullscreen, FPS limiter, or go back to title."""
    global back_btn, fullscreen_btn, fps_btn
    screen.fill((20, 20, 20))

    title = BIG_FONT.render("Options", True, (255, 255, 255))
    screen.blit(title, (center_x(title.get_width()), 90))

    # Buttons (centered)
    btn_w, btn_h, gap = 300, 54, 14
    y0 = 180

    fs_label = f"Fullscreen: {'ON' if FULLSCREEN else 'OFF'}"
    fps_label = f"FPS Limit: {fps_limit}"

    fullscreen_btn = centered_button(y0, btn_w, btn_h)
    fps_btn       = centered_button(y0 + btn_h + gap, btn_w, btn_h)
    back_btn      = centered_button(y0 + 2 * (btn_h + gap), btn_w, btn_h)

    for rect, label in [
        (fullscreen_btn, fs_label),
        (fps_btn,        fps_label),
        (back_btn,       "Back"),
    ]:
        pygame.draw.rect(screen, (60, 60, 60), rect)
        pygame.draw.rect(screen, (220, 220, 220), rect, 2)
        txt = font.render(label, True, (255, 255, 255))
        screen.blit(txt, (rect.x + 12, rect.y + 12))
    
    # FPS limit info
    info_text = font.render("Click FPS button to cycle: 30 → 60 → 120 → Unlimited", True, (200, 200, 200))
    screen.blit(info_text, (center_x(info_text.get_width()), y0 + 3 * (btn_h + gap) + 20))

def draw_fps_display():
    """Display actual FPS counter and FPS limit info"""
    global fps_counter, last_fps_time
    
    if not show_fps:
        return
    
    # Calculate actual FPS
    current_time = time.time()
    if current_time - last_fps_time >= 1.0:  # Update every second
        fps_counter = int(1.0 / (current_time - last_fps_time))
        last_fps_time = current_time
    
    # Draw FPS info
    fps_text = font.render(f"FPS: {fps_counter}", True, (255, 255, 0))
    limit_text = font.render(f"Limit: {fps_limit}", True, (255, 255, 0))
    
    screen.blit(fps_text, (10, 70))
    screen.blit(limit_text, (10, 90))

# --- Part Three ---
def delete_save_data():
    if os.path.exists(SAVE_DIR):
        shutil.rmtree(SAVE_DIR)
    os.makedirs(SAVE_DIR)

def show_death_screen():
    global game_state
    game_state = STATE_DEAD
    screen.fill((0, 0, 0))
    death_text = BIG_FONT.render("You Died", True, (255, 0, 0))
    screen.blit(death_text, (SCREEN_WIDTH // 2 - death_text.get_width() // 2, 200))
    respawn_btn = draw_button("Respawn", 320, 300, 160, 50)
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if respawn_btn.collidepoint(pygame.mouse.get_pos()):
                    # Reset player to spawn position
                    player["inventory"] = []
                    player["health"] = 10
                    player["hunger"] = 10
                    player["x"] = 10
                    player["y"] = 0
                    player["vel_y"] = 0
                    player["on_ground"] = False
                    game_state = STATE_GAME
                    update_pause_state()  # Resume time when respawning
                    return  # Exit the death screen function completely



        clock.tick(30)

def draw_status_bars():
    hp_text = font.render("HP:", True, (255, 255, 255))
    hunger_text = font.render("Hunger:", True, (255, 255, 255))
    screen.blit(hp_text, (10, 10))
    screen.blit(hunger_text, (10, 40))
    for i in range(10):
        hp_img = alive_hp if i < player["health"] else dead_hp
        screen.blit(hp_img, (70 + i * 20, 10))
        hunger_color = (255, 165, 0) if i < player["hunger"] else (80, 80, 80)
        pygame.draw.rect(screen, hunger_color, (70 + i * 20, 40, 16, 16))


# --- Part Four ---
def draw_held_item(px, py):
    """Draw the currently held item on the player's right hand"""
    # Check if player has a selected item
    if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]:
        item = player["inventory"][player["selected"]]
        if item and isinstance(item, dict) and "type" in item:
            item_type = item["type"]
            # Check if we have a texture for this item
            if item_type in textures:
                # Position the item on the player's right hand
                # Adjust these offsets to change which hand and position:
                # hand_x = px + 20  # Right side of player (change to px - 20 for left hand)
                # hand_y = py + 8   # Slightly above center (adjust for different heights)
                hand_x = px + 20  # Right side of player
                hand_y = py + 8   # Slightly above center
                
                # Get the item texture and scale it down slightly for the hand
                item_texture = textures[item_type]
                # Scale down to 24x24 pixels (smaller than the 32x32 tile size)
                scaled_texture = pygame.transform.scale(item_texture, (24, 24))
                
                # Draw the item on the hand
                screen.blit(scaled_texture, (hand_x, hand_y))

def draw_world():
    # Draw blocks safely (skip None or unknown keys)
    for (x, y), block in world_data.items():
        if not block:
            continue
        img = textures.get(block)
        if img is None:
            continue
        screen_x = x * TILE_SIZE - camera_x
        screen_y = y * TILE_SIZE - 100
        if -TILE_SIZE < screen_x < SCREEN_WIDTH and -TILE_SIZE < screen_y < SCREEN_HEIGHT:
            screen.blit(img, (screen_x, screen_y))

    # Draw entities
    for entity in entities:
        if entity["type"] == "monster":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - 100
            screen.blit(entity["image"], (ex, ey))
        elif entity["type"] == "projectile":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - 100
            pygame.draw.rect(screen, (200, 50, 50), (ex + 12, ey + 12, 8, 8))
        elif entity["type"] == "villager":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - 100
            screen.blit(textures["villager"], (ex, ey))

    # Draw player
    px = int(player["x"] * TILE_SIZE) - camera_x
    py = int(player["y"] * TILE_SIZE) - 100
    screen.blit(player_image, (px, py))
    
    # Draw held item on player's right hand
    draw_held_item(px, py)


def draw_inventory():
    # Make sure inventory is in a drawable state
    normalize_inventory()
    # Draw hotbar background and items (no event handling here)
    for i in range(9):
        rect = pygame.Rect(10 + i * 50, SCREEN_HEIGHT - 60, 40, 40)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2 if i == player["selected"] else 1)
        if i < len(player["inventory"]):
            item = player["inventory"][i]
            if item and isinstance(item, dict):
                item_type = item.get("type")
                if item_type in textures:
                    screen.blit(textures[item_type], (15 + i * 50, SCREEN_HEIGHT - 55))
                cnt = item.get("count", 1)
                if isinstance(cnt, int) and cnt > 1:
                    count_text = font.render(str(cnt), True, (255, 255, 0))
                    screen.blit(count_text, (30 + i * 50, SCREEN_HEIGHT - 35))


# --- Part Five: Inventory Logic, Item Interaction, Block Breaking/Placing, Sword Combat ---
def add_to_inventory(item_type, count=1):
    """Add `count` of `item_type` into the player's inventory, stacking where possible."""
    if count <= 0:
        return
    # Try to stack into existing slot
    for item in player["inventory"]:
        if item and item.get("type") == item_type:
            item["count"] = item.get("count", 0) + count
            normalize_inventory()
            return
    # Otherwise, append a new slot if space
    if len(player["inventory"]) < 9:
        player["inventory"].append({"type": item_type, "count": count})
    else:
        # If inventory is full, try to merge into any slot with same type again (in case of Nones)
        for idx, it in enumerate(player["inventory"]):
            if not it:
                player["inventory"][idx] = {"type": item_type, "count": count}
                break
    normalize_inventory()

def break_block(mx, my):
    px, py = int(player["x"]), int(player["y"])
    bx, by = (mx + camera_x) // TILE_SIZE, (my + 100) // TILE_SIZE
    if abs(bx - px) <= 2 and abs(by - py) <= 2:
        block = get_block(bx, by)
        if not block:
            return
        # Bedrock, fluids are unbreakable
        if block in ("bedrock", "water", "lava"):
            return
        # Stone & ores require pickaxe
        if block in ["stone", "coal", "iron", "gold", "diamond"]:
            if not (player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]["type"] == "pickaxe"):
                return
            add_to_inventory(block)
            world_data.pop((bx, by))
            # Generate air block to allow digging down
            world_data[(bx, by)] = "air"
            return
        # Chest: pick up contents and the chest itself
        if block == "chest":
            inv = chest_system.get_chest_inventory((bx, by))
            # Move all items (with counts) into the player's inventory
            for it in inv:
                if it and isinstance(it, dict) and "type" in it:
                    add_to_inventory(it["type"], it.get("count", 1))
            # Remove the chest from the chest system
            chest_system.chest_inventories.pop((bx, by), None)
            # Also remove player-placed marker if it exists
            chest_system.player_placed_chests.discard((bx, by))
            # Give the empty chest item back to player
            add_to_inventory("chest", 1)
            # Remove the chest block from the world
            world_data.pop((bx, by), None)
            return
        # Soft blocks (now includes "bed" so you can pick it up)
        if block in ["dirt", "grass", "leaves", "carrot", "log", "ladder", "bed"]:
            add_to_inventory(block)
            world_data.pop((bx, by))
            # Generate air block to allow digging down
            world_data[(bx, by)] = "air"

def place_block(mx, my):
    px, py = int(player["x"]), int(player["y"])
    bx, by = (mx + camera_x) // TILE_SIZE, (my + 100) // TILE_SIZE
    if abs(bx - px) <= 2 and abs(by - py) <= 2:
        if get_block(bx, by) is None and player["selected"] < len(player["inventory"]):
            item = player["inventory"][player["selected"]]
            item_type = item["type"]

            # Disallow placing tools and fluids
            if item_type in ["sword", "pickaxe", "water", "lava"]:
                return
            
            # Special handling for carrots - only allow placing on grass
            if item_type == "carrot":
                if get_block(bx, by + 1) != "grass":
                    return  # Can only place carrots on grass

            # If placing ladders, forbid positions at or below bedrock level
            if item_type == "ladder":
                br_y = bedrock_level_at(bx)
                if br_y is not None and by >= br_y:
                    return  # Prevent creating a ladder path through bedrock

            # If placing a chest, make it EMPTY (no auto-generated loot)
            if item_type == "chest":
                set_block(bx, by, "chest")
                # Create empty player-placed chest
                chest_system.create_player_placed_chest((bx, by))
            else:
                set_block(bx, by, item_type)

            # consume one item
            item["count"] -= 1
            if item["count"] <= 0:
                player["inventory"].pop(player["selected"])

def attack_monsters(mx, my):
    px, py = player["x"], player["y"]
    for mob in entities[:]:
        if mob["type"] == "monster":
            dx = (mx + camera_x) / TILE_SIZE - mob["x"]
            dy = (my + 100) / TILE_SIZE - mob["y"]
            if math.hypot(dx, dy) <= 2:
                # Only swords can damage; each hit deals 1 (7 hits to defeat)
                if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]["type"] == "sword":
                    mob["hp"] = mob.get("hp", 7) - 1
                    if mob["hp"] <= 0:
                        entities.remove(mob)

# --- Part Six: World Interaction, Carrots, Chests, Hunger/Health, Monster Damage ---
def update_world_interactions():
    global fall_start_y

    px, py = int(player["x"]), int(player["y"])
    block_below = get_block(px, py + 1)
    block_at = get_block(px, py)

    # Lava hazard: standing in or on lava hurts
    if block_at == "lava" or block_below == "lava":
        player["health"] -= 1
        damage_sound.play()
        if player["health"] <= 0:
            show_death_screen()

    # Carrots: eat if health not full, otherwise collect
    if block_at == "carrot":
        if player["health"] < 10:
            player["health"] += 1
            world_data.pop((px, py))
        else:
            add_to_inventory("carrot")
            world_data.pop((px, py))
    elif block_below == "carrot":
        if player["health"] < 10:
            player["health"] += 1
            world_data.pop((px, py + 1))
        else:
            add_to_inventory("carrot")
            world_data.pop((px, py + 1))

    # Fall damage: apply if fall was 4+ blocks
    if not player["on_ground"]:
        if fall_start_y is None:
            fall_start_y = player["y"]
    else:
        if fall_start_y is not None and player["y"] - fall_start_y >= 4:
            player["health"] -= 1
            damage_sound.play()
        fall_start_y = None

# --- Chest UI & logic ---

    


def open_chest_at(bx, by):
    global chest_open, open_chest_pos, drag_item, drag_from
    chest_open = True
    open_chest_pos = (bx, by)
    drag_item = None
    drag_from = None
    # Open chest using chest system (handles loot generation for natural chests)
    chest_system.open_chest((bx, by))


def chest_slot_rect(col, row):
    x = CHEST_UI_X + 20 + col * (SLOT_SIZE + SLOT_MARGIN)
    y = CHEST_UI_Y + 50 + row * (SLOT_SIZE + SLOT_MARGIN)
    return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

def hotbar_slot_rect(idx):
    return pygame.Rect(10 + idx * 50, SCREEN_HEIGHT - 60, 40, 40)

def find_chest_slot_at(mx, my):
    for r in range(chest_system.CHEST_ROWS):
        for c in range(chest_system.CHEST_COLS):
            if chest_slot_rect(c, r).collidepoint(mx, my):
                return r * chest_system.CHEST_COLS + c
    return None

def find_hotbar_slot_at(mx, my):
    for i in range(9):
        if hotbar_slot_rect(i).collidepoint(mx, my):
            return i
    return None

def draw_item_icon(item, x, y):
    if not item:
        return
    img = textures.get(item["type"])
    if img:
        screen.blit(img, (x, y))
    if item.get("count", 1) > 1:
        count_text = font.render(str(item["count"]), True, (255, 255, 0))
        screen.blit(count_text, (x + 20, y + 20))

def show_item_tooltip(item, mouse_x, mouse_y):
    """Show a tooltip with the item's name when hovering over it"""
    if not item or not isinstance(item, dict) or "type" not in item:
        return
    
    # Get the item name (capitalize first letter)
    item_name = item["type"].replace("_", " ").title()
    
    # Render the tooltip text
    tooltip_text = font.render(item_name, True, (255, 255, 255))
    
    # Calculate tooltip position (above mouse, but don't go off screen)
    tooltip_x = mouse_x + 10
    tooltip_y = mouse_y - 30
    
    # Adjust if tooltip would go off screen
    if tooltip_x + tooltip_text.get_width() > SCREEN_WIDTH:
        tooltip_x = mouse_x - tooltip_text.get_width() - 10
    if tooltip_y < 0:
        tooltip_y = mouse_y + 20
    
    # Draw tooltip background
    padding = 4
    bg_rect = pygame.Rect(
        tooltip_x - padding, 
        tooltip_y - padding, 
        tooltip_text.get_width() + padding * 2, 
        tooltip_text.get_height() + padding * 2
    )
    pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
    pygame.draw.rect(screen, (255, 255, 255), bg_rect, 1)
    
    # Draw tooltip text
    screen.blit(tooltip_text, (tooltip_x, tooltip_y))

def draw_chest_ui():
    update_chest_ui_geometry()
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Window
    pygame.draw.rect(screen, (30, 30, 30), (CHEST_UI_X, CHEST_UI_Y, CHEST_UI_W, CHEST_UI_H))
    pygame.draw.rect(screen, (200, 200, 200), (CHEST_UI_X, CHEST_UI_Y, CHEST_UI_W, CHEST_UI_H), 2)
    title = BIG_FONT.render("Chest", True, (255, 255, 255))
    screen.blit(title, (CHEST_UI_X + 20, CHEST_UI_Y + 10))

    slots = chest_system.get_chest_inventory(open_chest_pos)
    # Draw chest slots
    for r in range(chest_system.CHEST_ROWS):
        for c in range(chest_system.CHEST_COLS):
            idx = r * chest_system.CHEST_COLS + c
            rect = chest_slot_rect(c, r)
            pygame.draw.rect(screen, (90, 90, 90), rect)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)
            if idx < len(slots) and slots[idx]:
                draw_item_icon(slots[idx], rect.x + 2, rect.y + 2)
                
                # Show tooltip when mouse hovers over item
                if rect.collidepoint(mouse_pos):
                    show_item_tooltip(slots[idx], mouse_pos[0], mouse_pos[1])

    # Draw hotbar so you can drag to it
    for i in range(9):
        rect = hotbar_slot_rect(i)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2 if i == player["selected"] else 1)
        if i < len(player["inventory"]):
            draw_item_icon(player["inventory"][i], rect.x + 2, rect.y + 2)
            
            # Show tooltip when mouse hovers over hotbar item
            if rect.collidepoint(mouse_pos):
                show_item_tooltip(player["inventory"][i], mouse_pos[0], mouse_pos[1])

    # Draw the dragged item under mouse (if any)
    if drag_item:
        mx, my = mouse_pos
        draw_item_icon(drag_item, mx - 16, my - 16)


# --- Chest UI close helper ---
def close_chest_ui():
    global chest_open, open_chest_pos, drag_item, drag_from
    # If dragging an item, return it to its origin before closing
    if drag_item and drag_from:
        if drag_from[0] == "chest":
            slots = chest_system.get_chest_inventory(open_chest_pos)
            idx = drag_from[1]
            if idx < len(slots) and slots[idx] is None:
                slots[idx] = drag_item
        elif drag_from[0] == "hotbar":
            idx = drag_from[1]
            while len(player["inventory"]) <= idx:
                player["inventory"].append(None)
            if player["inventory"][idx] is None:
                player["inventory"][idx] = drag_item
    drag_item = None
    drag_from = None
    # Clean up the player's inventory so UI remains safe
    normalize_inventory()
    chest_open = False
    open_chest_pos = None


# --- Carrot consumption from inventory ---
def consume_carrot_from_inventory():
    """Eat one carrot from the currently selected slot if it can help.
    - If health &amp;/or hunger are below max (10), restore +1 to each that is below.
    - Only consume a carrot if it restores at least one stat.
    """
    if player["selected"] >= len(player["inventory"]):
        return
    item = player["inventory"][player["selected"]]
    if not item or not isinstance(item, dict) or item.get("type") != "carrot" or item.get("count", 0) <= 0:
        return

    restored = False
    # Restore health if not full
    if player["health"] < 10:
        player["health"] = min(10, player["health"] + 1)
        restored = True
    # Restore hunger if not full
    if player["hunger"] < 10:
        player["hunger"] = min(10, player["hunger"] + 1)
        restored = True

            # Only consume a carrot if something was restored
        if restored:
            item["count"] -= 1
            if item["count"] <= 0:
                # remove empty slot
                player["inventory"].pop(player["selected"])


# --- Missing Update Functions ---
def update_daylight():
    global is_day, day_start_time, paused_time
    # Only update time when in the game state
    if game_state == STATE_GAME:
        if time.time() - day_start_time - paused_time >= 120:
            is_day = not is_day
            day_start_time = time.time()
            paused_time = 0  # Reset paused time after day/night change

# --- Bed sleep: fade to black -> set day -> fade in ---
def sleep_in_bed():
    """Fade to black, switch to day, then fade back in."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((0, 0, 0))
    # Fade to black
    for a in range(0, 256, 12):
        overlay.set_alpha(a)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # Flip to daytime
    global is_day, day_start_time
    is_day = True
    day_start_time = time.time()

    # Small notification
    show_message("You feel rested.")

    # Fade back in
    for a in range(255, -1, -12):
        overlay.set_alpha(a)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)

def update_player():
    keys = pygame.key.get_pressed()
    speed = SLOW_SPEED if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else MOVE_SPEED

    # Horizontal movement intent
    move_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
    move_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

    # Check for ladder at player position (current or feet)
    px, py = player["x"], player["y"]
    on_ladder = (get_block(int(px), int(py)) == "ladder" or
                 get_block(int(px), int(py + 0.9)) == "ladder")

    if on_ladder:
        # Gentle horizontal while on ladder
        if move_left:
            # Faster horizontal step when exiting a ladder (use tile-based speed like ground)
            step = max(0.08, speed)  # ensure not too tiny when shift-slowed
            new_x = px - step * 0.9
            left_head = get_block(int(new_x), int(py))
            left_feet = get_block(int(new_x), int(py + 0.9))
            if is_non_solid_block(left_head) and is_non_solid_block(left_feet) and left_head != "bedrock" and left_feet != "bedrock":
                player["x"] = new_x
        if move_right:
            # Faster horizontal step when exiting a ladder (use tile-based speed like ground)
            step = max(0.08, speed)
            new_x = px + step * 0.9
            right_head = get_block(int(new_x + 0.9), int(py))
            right_feet = get_block(int(new_x + 0.9), int(py + 0.9))
            if is_non_solid_block(right_head) and is_non_solid_block(right_feet) and right_head != "bedrock" and right_feet != "bedrock":
                player["x"] = new_x

        # Climb up/down cancels gravity
        climb_speed = 0.12
        # Attempt to move up/down on the ladder with collision and bedrock checks
        target_y = player["y"]
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            target_y = player["y"] - climb_speed
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            target_y = player["y"] + climb_speed

        # Check collisions at head and feet at the new Y
        head_blk = get_block(int(px), int(target_y))
        feet_blk = get_block(int(px), int(target_y + 0.9))

        # Disallow moving into bedrock or other solid tiles
        if is_non_solid_block(head_blk) and is_non_solid_block(feet_blk):
            # Extra guard: never cross bedrock level even if cells above are empty
            br_y = bedrock_level_at(int(px))
            if not ((head_blk == "bedrock") or (feet_blk == "bedrock") or (br_y is not None and target_y + 0.9 >= br_y)):
                player["y"] = target_y

        player["vel_y"] = 0
        player["on_ground"] = False
    else:
        # Normal horizontal movement with collision
        if move_left:
            new_x = px - speed
            # Check both head and feet positions for collision
            left_head = get_block(int(new_x), int(player["y"]))
            left_feet = get_block(int(new_x), int(player["y"] + 0.9))
            if is_non_solid_block(left_head) and is_non_solid_block(left_feet):
                player["x"] = new_x

        if move_right:
            new_x = px + speed
            # Check both head and feet positions for collision
            right_head = get_block(int(new_x + 0.9), int(player["y"]))
            right_feet = get_block(int(new_x + 0.9), int(player["y"] + 0.9))
            if is_non_solid_block(right_head) and is_non_solid_block(right_feet):
                player["x"] = new_x

        # Gravity
        player["vel_y"] += GRAVITY
        if player["vel_y"] > MAX_FALL_SPEED:
            player["vel_y"] = MAX_FALL_SPEED

        next_y = player["y"] + player["vel_y"] / TILE_SIZE
        
        # Check collision at the target position (both head and feet)
        target_y = int(next_y + 1)
        head_block = get_block(int(player["x"]), target_y)
        feet_block = get_block(int(player["x"] + 0.9), target_y)
        
        # Check if we're trying to move into a solid block
        if not is_non_solid_block(head_block) or not is_non_solid_block(feet_block):
            # Collision detected - stop falling and place player on top of the block
            player["vel_y"] = 0
            player["on_ground"] = True
            player["y"] = target_y - 1  # Position player on top of the block
        else:
            # No collision - continue falling
            player["on_ground"] = False
            player["y"] = next_y

    # Optional: disable jump while on ladder to avoid launch
    if (keys[pygame.K_SPACE] and player.get("on_ground", False)) and (not on_ladder):
        # Check if there's a block above the player before jumping
        head_y = int(player["y"])
        head_block = get_block(int(player["x"]), head_y)
        head_block_right = get_block(int(player["x"] + 0.9), head_y)
        
        # Only jump if there's no solid block above
        if is_non_solid_block(head_block) and is_non_solid_block(head_block_right):
            player["vel_y"] = JUMP_STRENGTH
# --- Title Screen Drawing Function ---
def save_game():
    """Save the current game state"""
    global world_data
    
    # Ensure world_data exists and is not None
    if world_data is None:
        world_data = {}
    
    # Serialize world blocks
    world_ser = {f"{x},{y}": block for (x, y), block in world_data.items() if block}
    
    # Get chest data from chest system
    chest_data = chest_system.serialize_for_save()
    
    data = {
        "player": player,
        "world": world_ser,
        "entities": entities,
        "chest_inventories": chest_data["chest_inventories"],
        "player_placed_chests": chest_data["player_placed_chests"],
    }
    
    # Save to current world if one is loaded, otherwise save to legacy save.json
    current_world = world_manager.get_current_world_name()
    if current_world:
        if current_world == "Legacy Save":
            # Save to legacy save.json
            world_manager.save_to_legacy(data)
        else:
            # Save to specific world file
            world_manager.save_world(current_world, data)
    else:
        # Legacy save
        with open(os.path.join(SAVE_DIR, "save.json"), "w") as f:
            json.dump(data, f)

def load_game_data(data):
    """Load game data from a world save"""
    global world_data, player, chest_inventories, entities
    
    # Restore player
    if "player" in data:
        player.update(data["player"])
    
    # Restore world
    world_raw = data.get("world", {})
    world_data = {(int(k.split(",")[0]), int(k.split(",")[1])): v for k, v in world_raw.items() if v}
    
    # Restore entities
    entities = data.get("entities", [])
    
    # Load chest data using chest system
    chest_system.deserialize_from_save(data)
    
    # Ensure all chests in the world have proper inventories
    # This handles cases where chests were placed but inventories weren't saved
    chest_system.ensure_all_chests_have_inventories(world_data)
    
    # Ensure player stands on ground
    if get_block(int(player["x"]), int(player["y"])) in [None, "air"]:
        for y in range(100):
            if get_block(int(player["x"]), y) == "grass":
                player["y"] = y - 1
                break
    
    # If this is a new world with a seed, regenerate the world consistently
    if "world_seed" in data and not world_data:
        print(f"Regenerating world with seed: {data['world_seed']}")
        generate_initial_world(data["world_seed"])

def load_game():
    """Load the legacy save.json file (for backward compatibility)"""
    try:
        with open(os.path.join(SAVE_DIR, "save.json"), "r") as f:
            data = json.load(f)
            load_game_data(data)
    except FileNotFoundError:
        generate_initial_world()  # Generate with random seed for legacy saves

def update_monsters():
    # Move and attack monsters
    for mob in entities[:]:
        if mob["type"] == "monster":
            # Ensure each monster has health
            if "hp" not in mob:
                mob["hp"] = 7

            dx = player["x"] - mob["x"]
            dy = player["y"] - mob["y"]
            dist = math.hypot(dx, dy)
            if dist > 0:
                # Faster movement toward player
                mob["x"] += 0.06 * dx / dist
                mob["y"] += 0.04 * dy / dist

            # Ranged attack: throw a faster projectile every 1.5s
            mob["cooldown"] = mob.get("cooldown", 0) + 1
            if mob["cooldown"] >= 90:
                mob["cooldown"] = 0
                if dist > 0:
                    entities.append({
                        "type": "projectile",
                        "x": mob["x"],
                        "y": mob["y"],
                        "dx": 0.18 * dx / dist,
                        "dy": 0.18 * dy / dist,
                        "damage": 3
                    })

            # Contact damage (3 hearts) but do NOT remove the monster
            if abs(player["x"] - mob["x"]) < 0.5 and abs(player["y"] - mob["y"]) < 1:
                player["health"] -= 3
                damage_sound.play()
                if player["health"] <= 0:
                    show_death_screen()

    # Projectiles step and collision
    for proj in entities[:]:
        if proj["type"] == "projectile":
            proj["x"] += proj["dx"]
            proj["y"] += proj["dy"]
            if abs(player["x"] - proj["x"]) < 0.5 and abs(player["y"] - proj["y"]) < 0.5:
                player["health"] -= proj.get("damage", 3)
                damage_sound.play()
                entities.remove(proj)
                if player["health"] <= 0:
                    show_death_screen()
            elif proj["x"] < -100 or proj["x"] > 100 or proj["y"] > 100:
                entities.remove(proj)


# --- Villager update logic ---
def update_hunger():
    """Update hunger system - decrease hunger every 200 seconds"""
    global hunger_timer, paused_time
    # Only update hunger when in the game state
    if game_state == STATE_GAME:
        current_time = time.time()
        if current_time - hunger_timer - paused_time >= 200:  # 200 seconds = ~3.33 minutes
            if player["health"] > 0:
                player["hunger"] -= 1
            hunger_timer = current_time
            paused_time = 0  # Reset paused time after hunger update

# --- Pause Management Functions ---
def pause_game_time():
    """Pause the game time when leaving the game state"""
    global last_pause_time
    if game_state != STATE_GAME and last_pause_time is None:
        last_pause_time = time.time()

def resume_game_time():
    """Resume the game time when returning to the game state"""
    global last_pause_time, paused_time
    if game_state == STATE_GAME and last_pause_time is not None:
        paused_time += time.time() - last_pause_time
        last_pause_time = None

def update_pause_state():
    """Update pause state based on current game state"""
    if game_state == STATE_GAME:
        resume_game_time()
    else:
        pause_game_time()

def update_villagers():
    """Simple wander AI for villagers. They avoid walking off cliffs and bump into walls."""
    for v in entities:
        if v.get("type") != "villager":
            continue
        # step timer changes direction occasionally
        v["step"] = v.get("step", 0) + 1
        if v["step"] % 180 == 0 and random.random() < 0.5:
            v["dir"] = -v.get("dir", 1)
        dirn = v.get("dir", 1)

        # desired next position
        nx = v["x"] + 0.04 * dirn
        # tiles at head/feet
        head = get_block(int(nx + (0.9 if dirn > 0 else 0.0)), int(v["y"]))
        feet = get_block(int(nx + (0.9 if dirn > 0 else 0.0)), int(v["y"] + 0.9))
        ground_ahead = get_block(int(nx + (0.9 if dirn > 0 else 0.0)), int(v["y"] + 1))

        # avoid solid walls
        if is_non_solid_block(head) and is_non_solid_block(feet):
            # avoid stepping into gaps (no ground ahead)
            if ground_ahead is None:
                v["dir"] = -dirn
            else:
                v["x"] = nx
        else:
            v["dir"] = -dirn

        # gravity (very light so they stay on ground)
        below = get_block(int(v["x"]), int(v["y"] + 1))
        if below is None:
            v["y"] += 0.10
        else:
            v["y"] = float(int(v["y"]))


# --- World Generation Function ---
def generate_initial_world(world_seed=None):
    """Generate a clean, organized world with proper layer hierarchy"""
    if world_seed is None:
        world_seed = random.randint(1, 999999)
    
    # Set random seed for this world generation
    world_rng = random.Random(world_seed)
    
    # Generate a random starting area for the player
    start_x = world_rng.randint(-100, 100)  # Random starting X position
    world_width = world_rng.randint(80, 150)  # Random world width
    
    # Generate COMPLETELY FLAT terrain (no mountains, no variation)
    print("🌍 Generating completely flat world...")
    
    # Generate terrain with clean layering - ALL FLAT
    for x in range(start_x - world_width//2, start_x + world_width//2):
        # EVERYTHING is completely flat at Y=10
        ground_y = 10  # Fixed height for entire world
        
        # CLEAN LAYER GENERATION - Always follow proper hierarchy
        
        # 1. GRASS LAYER (Surface) - CRITICAL: This MUST work!
        set_block(x, ground_y, "grass")
        print(f"🌱 Placed grass at ({x}, {ground_y})")
        
        # 2. DIRT LAYER (Below grass, always 3 blocks deep)
        for y in range(ground_y + 1, ground_y + 4):
            set_block(x, y, "dirt")
        
        # 3. STONE LAYER (Below dirt, always 8 blocks deep)
        for y in range(ground_y + 4, ground_y + 12):
            # Clean ore generation within stone layer (REDUCED spawn rates)
            ore_chance = world_rng.random()
            if ore_chance < 0.02:  # Reduced from 0.05 to 0.02
                set_block(x, y, "coal")
            elif ore_chance < 0.03:  # Reduced from 0.08 to 0.03
                set_block(x, y, "iron")
            elif ore_chance < 0.035:  # Reduced from 0.10 to 0.035
                set_block(x, y, "gold")
            elif ore_chance < 0.036:  # Reduced from 0.11 to 0.036
                set_block(x, y, "diamond")
            else:
                set_block(x, y, "stone")
        
        # 4. BEDROCK LAYER (Completely flat, nothing below)
        bedrock_y = 22  # Fixed bedrock level
        set_block(x, bedrock_y, "bedrock")
        
        # TEMPORARILY DISABLE VALIDATION TO SEE IF GRASS GENERATES
        # validate_column_integrity(x, ground_y)
        
        # Ensure NO blocks generate below bedrock
        for y in range(bedrock_y + 1, 100):
            if get_block(x, y) is not None:
                world_data.pop((x, y), None)  # Remove any blocks below bedrock
        
        # Clean tree generation (only on grass, no messy placement)
        if world_rng.random() < 0.08:  # Reduced tree density for cleaner look
            # Only place trees if there's clean space
            if get_block(x, ground_y - 1) is None:
                set_block(x, ground_y - 1, "log")
            if get_block(x, ground_y - 2) is None:
                set_block(x, ground_y - 2, "log")
            
            # Clean leaf placement (only in empty spaces)
            for dx in [-1, 0, 1]:
                for dy in [-3, -4]:
                    leaf_x, leaf_y = x + dx, ground_y + dy
                    if get_block(leaf_x, leaf_y) is None:
                        set_block(leaf_x, leaf_y, "leaves")

        # Clean carrot placement (only on grass, no messy spawning)
        if in_carrot_biome(x):
            if can_place_surface_item(x, ground_y) and world_rng.random() < 0.6:
                set_block(x, ground_y - 1, "carrot")
            
            # Clean neighbor carrot spawning
            gy_r = ground_y_of_column(x + 1)
            if gy_r is not None and can_place_surface_item(x + 1, gy_r) and world_rng.random() < 0.35:
                set_block(x + 1, gy_r - 1, "carrot")
            gy_l = ground_y_of_column(x - 1)
            if gy_l is not None and can_place_surface_item(x - 1, gy_l) and world_rng.random() < 0.35:
                set_block(x - 1, gy_l - 1, "carrot")
        else:
            if can_place_surface_item(x, ground_y) and world_rng.random() < 0.05:
                set_block(x, ground_y - 1, "carrot")

        # Clean chest placement (only on grass, no messy spawning)
        if can_place_surface_item(x, ground_y) and world_rng.random() < 0.05:
            set_block(x, ground_y - 1, "chest")
            chest_system.generate_natural_chest_loot((x, ground_y - 1))
    
    # Find clean flat areas for village placement
    flat_areas = []
    for x in range(start_x - world_width//2, start_x + world_width//2):
        if get_block(x, 10) == "grass":  # Only on clean flat ground (Y=10)
            flat_areas.append(x)
    
    # Place starter village in clean flat area
    if flat_areas:
        village_x = world_rng.choice(flat_areas)
        village_chunk = (village_x // 50)
        maybe_generate_village_for_chunk(village_chunk, village_chunk * 50)
        print(f"Placed village in clean flat area at X: {village_x}")
    else:
        # Fallback: place village near starting area
        village_chunk = world_rng.randint(-2, 2)
        maybe_generate_village_for_chunk(village_chunk, start_x + village_chunk * 50)
        print(f"Placed village in fallback location at chunk: {village_chunk}")
    
    # Set player spawn position
    player["x"] = start_x
    # Ensure player spawns on clean ground
    for y in range(100):
        if get_block(int(player["x"]), y) == "grass":
            player["y"] = y - 1
            break
    
    print(f"Generated COMPLETELY FLAT world with seed: {world_seed}, starting at X: {start_x}")
    print(f"Clean terrain: Grass → Dirt → Stone → Bedrock")
    print(f"Surface height: Y=10 (completely flat)")
    print(f"Bedrock at Y: 22")
    
    # TEMPORARILY DISABLE VALIDATION TO SEE IF GRASS GENERATES
    # validate_and_fix_terrain()
    print("🔍 Skipping terrain validation for now...")
    
    return world_seed

def validate_and_fix_terrain():
    """Commercial-grade terrain validation and repair system"""
    global world_data
    
    print("🔍 Validating terrain integrity...")
    print(f"🌱 Checking for grass blocks...")
    fixes_applied = 0
    
    # Get all X coordinates that have terrain
    terrain_columns = set()
    grass_count = 0
    for (x, y), block in world_data.items():
        if block in ["grass", "dirt", "stone", "bedrock"]:
            terrain_columns.add(x)
        if block == "grass":
            grass_count += 1
    
    print(f"🌱 Found {grass_count} grass blocks in world")
    print(f"🏗️ Found {len(terrain_columns)} terrain columns")
    
    for x in sorted(terrain_columns):
        # Find the surface grass block for this column
        surface_y = None
        for y in range(100):
            if get_block(x, y) == "grass":
                surface_y = y
                break
        
        if surface_y is None:
            # No grass found - this is a critical error
            print(f"❌ CRITICAL: Column {x} has no grass surface - fixing...")
            # Find the highest terrain block and place grass above it
            highest_y = -1
            for y in range(100):
                if get_block(x, y) in ["dirt", "stone", "bedrock"]:
                    highest_y = max(highest_y, y)
            
            if highest_y >= 0:
                set_block(x, highest_y + 1, "grass")
                surface_y = highest_y + 1
                fixes_applied += 1
                print(f"✅ Fixed: Added grass at Y={surface_y} for column {x}")
            else:
                # No terrain at all - place at default height
                set_block(x, 10, "grass")
                surface_y = 10
                fixes_applied += 1
                print(f"✅ Fixed: Added grass at Y=10 for column {x}")
        
        # STEP 1: Remove ALL underground grass (guaranteed)
        for y in range(surface_y + 1, 100):
            if get_block(x, y) == "grass":
                world_data.pop((x, y), None)
                fixes_applied += 1
                print(f"✅ Fixed: Removed underground grass at ({x}, {y})")
        
        # STEP 2: Ensure dirt layer is complete (3 blocks deep)
        for y in range(surface_y + 1, surface_y + 4):
            if get_block(x, y) != "dirt":
                if get_block(x, y) is None:
                    set_block(x, y, "dirt")
                    fixes_applied += 1
                    print(f"✅ Fixed: Added missing dirt at ({x}, {y})")
                elif get_block(x, y) != "dirt":
                    # Replace non-dirt blocks with dirt
                    world_data.pop((x, y), None)
                    set_block(x, y, "dirt")
                    fixes_applied += 1
                    print(f"✅ Fixed: Replaced {get_block(x, y)} with dirt at ({x}, {y})")
        
        # STEP 3: Ensure stone layer is complete (8 blocks deep, NO HOLES)
        for y in range(surface_y + 4, surface_y + 12):
            if get_block(x, y) is None:
                # Fill hole with stone
                set_block(x, y, "stone")
                fixes_applied += 1
                print(f"✅ Fixed: Filled stone layer hole at ({x}, {y})")
            elif get_block(x, y) not in ["stone", "coal", "iron", "gold", "diamond"]:
                # Replace non-stone blocks with stone
                old_block = get_block(x, y)
                world_data.pop((x, y), None)
                set_block(x, y, "stone")
                fixes_applied += 1
                print(f"✅ Fixed: Replaced {old_block} with stone at ({x}, {y})")
        
        # STEP 4: Ensure bedrock at Y=22
        bedrock_y = 22
        if get_block(x, bedrock_y) != "bedrock":
            if get_block(x, bedrock_y) is None:
                set_block(x, bedrock_y, "bedrock")
                fixes_applied += 1
                print(f"✅ Fixed: Added missing bedrock at ({x}, {bedrock_y})")
            else:
                # Replace non-bedrock with bedrock
                old_block = get_block(x, bedrock_y)
                world_data.pop((x, bedrock_y), None)
                set_block(x, bedrock_y, "bedrock")
                fixes_applied += 1
                print(f"✅ Fixed: Replaced {old_block} with bedrock at ({x}, {bedrock_y})")
        
        # STEP 5: Remove any blocks below bedrock
        for y in range(bedrock_y + 1, 100):
            if get_block(x, y) is not None:
                world_data.pop((x, y), None)
                fixes_applied += 1
                print(f"✅ Fixed: Removed block below bedrock at ({x}, {y})")
    
    # FINAL VERIFICATION: Double-check no grass exists underground
    underground_grass_found = 0
    # Create a copy of items to avoid RuntimeError when modifying dictionary
    grass_positions = [(x, y) for (x, y), block in world_data.items() if block == "grass"]
    
    for x, y in grass_positions:
        # Check if this grass has any blocks above it (only remove if truly underground)
        has_blocks_above = False
        for check_y in range(y + 1, 100):
            if get_block(x, check_y) is not None:
                has_blocks_above = True
                break
        
        if has_blocks_above:
            # This grass is underground - CRITICAL ERROR
            world_data.pop((x, y), None)
            underground_grass_found += 1
            print(f"🚨 CRITICAL: Found and removed underground grass at ({x}, {y})")
        else:
            # This grass is on the surface - KEEP IT
            print(f"✅ Surface grass verified at ({x}, {y})")
    
    if fixes_applied > 0:
        print(f"🔧 Applied {fixes_applied} terrain fixes")
    
    if underground_grass_found > 0:
        print(f"🚨 Removed {underground_grass_found} underground grass blocks")
    
    print("✅ Terrain validation complete - commercial quality guaranteed!")

def validate_column_integrity(x, ground_y):
    """Validate and fix a single column during generation"""
    global world_data
    
    # Ensure grass is ONLY at the surface (but don't remove surface grass)
    for y in range(ground_y + 1, 100):
        if get_block(x, y) == "grass":
            # Only remove grass that's truly underground (has blocks above it)
            has_blocks_above = False
            for check_y in range(y + 1, 100):
                if get_block(x, check_y) is not None:
                    has_blocks_above = True
                    break
            
            if has_blocks_above:
                world_data.pop((x, y), None)
                print(f"🚨 CRITICAL: Removed underground grass during generation at ({x}, {y})")
            # If no blocks above, this grass is fine (surface grass)
    
    # Ensure dirt layer is complete (3 blocks deep)
    for y in range(ground_y + 1, ground_y + 4):
        if get_block(x, y) != "dirt":
            if get_block(x, y) is None:
                set_block(x, y, "dirt")
            elif get_block(x, y) != "dirt":
                world_data.pop((x, y), None)
                set_block(x, y, "dirt")
    
    # Ensure stone layer is complete (8 blocks deep, NO HOLES)
    for y in range(ground_y + 4, ground_y + 12):
        if get_block(x, y) is None:
            set_block(x, y, "stone")
        elif get_block(x, y) not in ["stone", "coal", "iron", "gold", "diamond"]:
            world_data.pop((x, y), None)
            set_block(x, y, "stone")
    
    # Ensure bedrock at Y=22
    bedrock_y = 22
    if get_block(x, bedrock_y) != "bedrock":
        if get_block(x, bedrock_y) is None:
            set_block(x, bedrock_y, "bedrock")
        else:
            world_data.pop((x, bedrock_y), None)
            set_block(x, bedrock_y, "bedrock")

# --- Title Screen Drawing Function ---
def draw_title_screen():
    global play_btn, controls_btn, about_btn, options_btn, quit_btn
    screen.fill((0, 0, 128))  # Blue background
    title_text = BIG_FONT.render("Order of the Stone", True, (255, 255, 255))
    title_y = max(30, SCREEN_HEIGHT // 8)
    screen.blit(title_text, (center_x(title_text.get_width()), title_y))

    # Buttons centered vertically with spacing
    spacing = 16
    btn_w, btn_h = 220, 54
    top_y = title_y + title_text.get_height() + 40
    play_btn     = centered_button(top_y + 0 * (btn_h + spacing), btn_w, btn_h)
    controls_btn = centered_button(top_y + 1 * (btn_h + spacing), btn_w, btn_h)
    about_btn    = centered_button(top_y + 2 * (btn_h + spacing), btn_w, btn_h)
    options_btn  = centered_button(top_y + 3 * (btn_h + spacing), btn_w, btn_h)
    quit_btn     = centered_button(top_y + 4 * (btn_h + spacing), btn_w, btn_h)

    # Draw the button rectangles + labels
    for rect, label in [(play_btn, "Play"), (controls_btn, "Controls"),
                        (about_btn, "About"), (options_btn, "Options"),
                        (quit_btn, "Quit")]:
        pygame.draw.rect(screen, (100, 100, 100), rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)
        txt = font.render(label, True, (255, 255, 255))
        screen.blit(txt, (rect.x + 12, rect.y + 12))

    # Version bottom‑left
    version_text = font.render("1.0", True, (255, 255, 255))
    screen.blit(version_text, (10, SCREEN_HEIGHT - 30))

# --- Game Menu Drawing Function ---
def draw_game_menu():
    global resume_btn, quit_btn
    screen.fill((50, 50, 50))
    resume_btn = draw_button("Resume", 320, 260, 160, 50)
    quit_btn = draw_button("Quit to Title", 320, 320, 160, 50)

# --- Main Game Loop ---
# Add game menu toggle state
STATE_MENU = "menu"

running = True
load_game()
# Initialize pause state - start paused since we begin at title screen
update_pause_state()

while running:
    screen.fill((0, 191, 255) if is_day else (0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
        if event.type == pygame.VIDEORESIZE and not FULLSCREEN:
            # Remember new windowed size and reapply geometry
            WINDOWED_SIZE = (event.w, event.h)
            SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
            update_chest_ui_geometry()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == STATE_GAME:
                    game_state = STATE_MENU
                    update_pause_state()  # Pause time when leaving game
                elif game_state == STATE_MENU:
                    game_state = STATE_GAME
                    update_pause_state()  # Resume time when returning to game
                elif game_state == STATE_WORLD_SELECT:
                    game_state = STATE_TITLE
                    update_pause_state()  # Pause time when leaving world select
            # Toggle fullscreen on F11
            if event.key == pygame.K_F11:
                FULLSCREEN = not FULLSCREEN
                apply_display_mode()
                update_chest_ui_geometry()
            # Toggle FPS display on F3
            if event.key == pygame.K_F3:
                show_fps = not show_fps
            # Close chest UI with E, U, or ESC
            if chest_open and event.key in (pygame.K_e, pygame.K_u, pygame.K_ESCAPE):
                close_chest_ui()
                continue
            if event.key == pygame.K_SPACE and player["on_ground"]:
                player["vel_y"] = JUMP_STRENGTH
            if pygame.K_1 <= event.key <= pygame.K_9:
                player["selected"] = event.key - pygame.K_1
            


        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == STATE_WORLD_SELECT:
                # Handle world selection clicks
                action, world_name, new_selection = world_ui.handle_mouse_click(event.pos, world_ui.world_rects)
                if action == 'select':
                    world_ui.selected_world = new_selection
                
                # Handle button clicks
                button_action, button_world_name = world_ui.handle_button_click(event.pos)
                if button_action != 'none':
                    # Store the action to be processed in the main loop
                    world_ui.pending_action = button_action
                    world_ui.pending_world_name = button_world_name
            elif game_state == STATE_GAME:
                if chest_open:
                    mx, my = event.pos
                    # Left click: pick up or place item
                    if event.button == 1:
                        # If dragging, try to place into a slot
                        if drag_item:
                            # Try chest slot first
                            idx = find_chest_slot_at(mx, my)
                            if idx is not None:
                                slots = chest_system.get_chest_inventory(open_chest_pos)
                                # Place or swap
                                if slots[idx] is None:
                                    slots[idx] = drag_item
                                    drag_item = None
                                    drag_from = None
                                else:
                                    slots[idx], drag_item = drag_item, slots[idx]
                                continue
                            # Try hotbar
                            hot = find_hotbar_slot_at(mx, my)
                            if hot is not None:
                                # Place into player's hotbar/inventory list
                                while len(player["inventory"]) <= hot:
                                    player["inventory"].append(None)
                                if hot < len(player["inventory"]):
                                    if hot >= len(player["inventory"]):
                                        player["inventory"].append(drag_item)
                                        drag_item = None
                                        drag_from = None
                                    else:
                                        if hot < len(player["inventory"]):
                                            if player["inventory"][hot] is None:
                                                player["inventory"][hot] = drag_item
                                                drag_item = None
                                                drag_from = None
                                            else:
                                                player["inventory"][hot], drag_item = drag_item, player["inventory"][hot]
                                continue
                        else:
                            # Not dragging: try to pick up from chest/hotbar
                            idx = find_chest_slot_at(mx, my)
                            if idx is not None:
                                slots = chest_system.get_chest_inventory(open_chest_pos)
                                if idx < len(slots) and slots[idx]:
                                    drag_item = slots[idx]
                                    drag_from = ("chest", idx)
                                    slots[idx] = None
                                continue
                            hot = find_hotbar_slot_at(mx, my)
                            if hot is not None and hot < len(player["inventory"]) and player["inventory"][hot]:
                                drag_item = player["inventory"][hot]
                                drag_from = ("hotbar", hot)
                                player["inventory"][hot] = None
                                normalize_inventory()
                                continue
                    # Right click while UI open closes it (and drops any dragged item back to origin)
                    if event.button == 3:
                        close_chest_ui()
                        continue  # don't fall through to world interactions
                mx, my = event.pos
                if event.button == 1:
                    # Check if clicking on hotbar
                    if SCREEN_HEIGHT - 60 <= my <= SCREEN_HEIGHT:
                        # Determine slot index from mouse x
                        slot = (mx - 10) // 50
                        # Confirm within slot bounds
                        if 0 <= slot < 9 and (10 + slot * 50) <= mx <= (10 + slot * 50 + 40):
                            player["selected"] = slot
                            # If it's a carrot, try to consume it (safely)
                            if slot < len(player["inventory"]):
                                it = player["inventory"][slot]
                                if it and isinstance(it, dict) and it.get("type") == "carrot":
                                    consume_carrot_from_inventory()
                            # Do not interact with world when clicking UI
                            continue
                    # Not clicking the UI: attack/break in world
                    attack_monsters(mx, my)
                    break_block(mx, my)

                elif event.button == 3:
                    # Convert mouse to world tile
                    mx, my = event.pos
                    bx, by = (mx + camera_x) // TILE_SIZE, (my + 100) // TILE_SIZE
                    # Bed interaction: sleep at night, message at day
                    if get_block(bx, by) == "bed":
                        if not is_day:
                            sleep_in_bed()
                        else:
                            show_message("You can only sleep at night")
                        continue
                    if get_block(bx, by) == "chest":
                        open_chest_at(bx, by)
                        continue
                    # If selected carrot, eat it; otherwise place block
                    if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]] and player["inventory"][player["selected"]]["type"] == "carrot":
                        consume_carrot_from_inventory()
                    else:
                        place_block(mx, my)
            elif game_state == STATE_TITLE:
                if play_btn.collidepoint(event.pos):
                    game_state = STATE_WORLD_SELECT
                    update_pause_state()  # Pause time when leaving title
                    world_manager.load_worlds()  # Refresh world list
                elif controls_btn.collidepoint(event.pos):
                    game_state = STATE_CONTROLS
                    update_pause_state()  # Pause time when leaving title
                elif about_btn.collidepoint(event.pos):
                    game_state = STATE_ABOUT
                    update_pause_state()  # Pause time when leaving title
                elif options_btn.collidepoint(event.pos):
                    game_state = STATE_OPTIONS
                    update_pause_state()  # Pause time when leaving title
                elif quit_btn.collidepoint(event.pos):
                    save_game()
                    running = False
            elif game_state == STATE_MENU:
                if resume_btn.collidepoint(event.pos):
                    game_state = STATE_GAME
                    update_pause_state()  # Resume time when returning to game
                elif quit_btn.collidepoint(event.pos):
                    save_game()
                    game_state = STATE_TITLE
                    update_pause_state()  # Pause time when returning to title
            elif game_state == STATE_OPTIONS:
                if fullscreen_btn.collidepoint(event.pos):
                    FULLSCREEN = not FULLSCREEN
                    apply_display_mode()
                    update_chest_ui_geometry()
                elif fps_btn.collidepoint(event.pos):
                    # Cycle through FPS limits: 30 → 60 → 120 → Unlimited
                    if fps_limit == 30:
                        fps_limit = 60
                    elif fps_limit == 60:
                        fps_limit = 120
                    elif fps_limit == 120:
                        fps_limit = 0  # Unlimited (0 means no limit)
                    else:
                        fps_limit = 30  # Back to 30
                elif back_btn.collidepoint(event.pos):
                    game_state = STATE_TITLE
                    update_pause_state()  # Pause time when returning to title
            elif game_state in [STATE_CONTROLS, STATE_ABOUT]:
                if back_btn.collidepoint(event.pos):
                    game_state = STATE_TITLE
                    update_pause_state()  # Pause time when returning to title
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
        
        elif event.type == pygame.MOUSEWHEEL:
            # Handle mouse wheel scrolling in world selection
            if game_state == STATE_WORLD_SELECT:
                world_ui.handle_scroll(event.y * 30)  # Scroll by 30 pixels per wheel unit

    if game_state == STATE_GAME:
        camera_x = int((player["x"] * TILE_SIZE) - SCREEN_WIDTH // 2)
        left_edge = int((camera_x) // TILE_SIZE) - 5
        right_edge = int((camera_x + SCREEN_WIDTH) // TILE_SIZE) + 5
        # Village check per 50‑column chunk
        chunk_left = left_edge // 50
        chunk_right = right_edge // 50
        for ch in range(chunk_left, chunk_right + 1):
            base_x = ch * 50
            maybe_generate_village_for_chunk(ch, base_x)
        for x in range(left_edge, right_edge):
            if not column_has_terrain(x):
                prev_heights = [y for y in range(0, 100) if (x - 1, y) in world_data and world_data[(x - 1, y)] == "grass"]
                if prev_heights:
                    ground_y = prev_heights[0]
                else:
                    height_offset = int(3 * math.sin(x * 0.2))
                    ground_y = 10 + height_offset

                set_block(x, ground_y, "grass")
                for y in range(ground_y + 1, ground_y + 4):
                    set_block(x, y, "dirt")
                for y in range(ground_y + 4, ground_y + 12):
                    ore_chance = random.random()
                    if ore_chance < 0.05:
                        set_block(x, y, "coal")
                    elif ore_chance < 0.08:
                        set_block(x, y, "iron")
                    elif ore_chance < 0.10:
                        set_block(x, y, "gold")
                    elif ore_chance < 0.11:
                        set_block(x, y, "diamond")
                    else:
                        set_block(x, y, "stone")
                set_block(x, ground_y + 12, "bedrock")
                # Trees
                if random.random() < 0.1:
                    set_block(x, ground_y - 1, "log")
                    set_block(x, ground_y - 2, "log")
                    for dx in [-1, 0, 1]:
                        for dy in [-3, -4]:
                            set_block(x + dx, ground_y + dy, "leaves")

                # Carrots: only spawn when not in trees and with better placement logic
                if in_carrot_biome(x):
                    if can_place_surface_item(x, ground_y) and random.random() < 0.6:
                        set_block(x, ground_y - 1, "carrot")
                    # Reduced neighbor spawning to avoid tree conflicts
                    gy_r = ground_y_of_column(x + 1)
                    if gy_r is not None and can_place_surface_item(x + 1, gy_r) and random.random() < 0.25:
                        set_block(x + 1, gy_r - 1, "carrot")
                    gy_l = ground_y_of_column(x - 1)
                    if gy_l is not None and can_place_surface_item(x - 1, gy_l) and random.random() < 0.25:
                        set_block(x - 1, gy_l - 1, "carrot")
                else:
                    if can_place_surface_item(x, ground_y) and random.random() < 0.03:
                        set_block(x, ground_y - 1, "carrot")

                # Chests: never inside trees, reduced spawn rate
                if can_place_surface_item(x, ground_y) and random.random() < 0.03:
                    set_block(x, ground_y - 1, "chest")
                    # Generate loot for naturally spawned chests
                    chest_system.generate_natural_chest_loot((x, ground_y - 1))
                if not is_day and random.random() < 0.03:
                    entities.append({
                        "type": "monster",
                        "x": x,
                        "y": ground_y - 1,
                        "image": monster_image,
                        "hp": 7
                    })

        update_daylight()
        update_player()
        update_world_interactions()
        update_monsters()
        update_villagers()
        update_hunger()  # Update hunger system
        
        draw_world()
        draw_inventory()
        draw_status_bars()
        draw_fps_display()
        
        # Take world preview screenshot every 5 minutes
        current_world = world_manager.get_current_world_name()
        if current_world and world_preview.should_take_screenshot():
            world_preview.take_world_screenshot(current_world, screen)
        # Draw temporary message if any
        now_ms = pygame.time.get_ticks()
        if message_until > now_ms and message_text:
            m = font.render(message_text, True, (255, 255, 255))
            screen.blit(m, (SCREEN_WIDTH // 2 - m.get_width() // 2, 70))
        if chest_open:
            draw_chest_ui()

        if player["health"] <= 0:
            show_death_screen()
    elif game_state == STATE_TITLE:
        draw_title_screen()
    elif game_state == STATE_WORLD_SELECT:
        # Handle world selection screen
        action, world_name = world_ui.draw_world_selection_screen(world_manager)
        
        # Check for pending button actions
        if world_ui.pending_action:
            action = world_ui.pending_action
            world_name = world_ui.pending_world_name
            # Clear pending actions
            world_ui.pending_action = None
            world_ui.pending_world_name = None
        
        if action == 'play' and world_name:
            # Load existing world using WorldDetector
            world_data = world_ui.world_detector.load_world_data(world_name)
            
            if world_data:
                load_game_data(world_data)
                game_state = STATE_GAME
                update_pause_state()  # Resume time when entering game
                print(f"Successfully loaded world: {world_name}")
            else:
                show_message(f"Failed to load world: {world_name}")
                print(f"Debug: Failed to load world '{world_name}' - no data returned")
                
        elif action == 'create':
            # Check if we can create a new world (under 12 limit)
            if world_manager.can_create_world():
                # Create a new world with auto-generated name
                world = world_manager.create_world()
                if world:
                    world_name = world.name
                    show_message(f"Created world: {world_name}")
                    # Generate initial world data with unique seed
                    world_seed = generate_initial_world()
                    # Store the seed in the world data for consistency
                    new_world_data = {
                        'player': player,
                        'world': world_data,
                        'entities': entities,
                        'chest_inventories': chest_system.serialize_for_save()['chest_inventories'],
                        'player_placed_chests': chest_system.serialize_for_save()['player_placed_chests'],
                        'world_seed': world_seed,
                        'created': time.time()
                    }
                    # Ensure new worlds start in daytime
                    is_day = True
                    day_start_time = time.time()
                    # Save the generated world data immediately
                    save_game()
                    # Load the newly created world
                    loaded_world_data = world_manager.load_world(world_name)
                    if loaded_world_data:
                        load_game_data(loaded_world_data)
                        game_state = STATE_GAME
                        update_pause_state()  # Resume time when entering new game
                else:
                    show_message("Failed to create world!")
            else:
                show_message("Maximum worlds reached (12/12)!")
                
        elif action == 'delete' and world_name:
            # Delete world confirmation
            if world_manager.delete_world(world_name):
                # Also delete the world's preview screenshot
                world_preview.delete_world_preview(world_name)
                show_message(f"Deleted world: {world_name}")
            else:
                show_message("Failed to delete world!")
                
        elif action == 'back':
            game_state = STATE_TITLE
            update_pause_state()  # Pause time when returning to title
            

        
    elif game_state == STATE_MENU:
        draw_game_menu()
    elif game_state == STATE_CONTROLS:
        draw_controls()
    elif game_state == STATE_ABOUT:
        draw_about()
    elif game_state == STATE_OPTIONS:
        draw_options()

    pygame.display.flip()
    clock.tick(fps_limit)


if game_state == STATE_GAME:
    save_game()
pygame.quit()
