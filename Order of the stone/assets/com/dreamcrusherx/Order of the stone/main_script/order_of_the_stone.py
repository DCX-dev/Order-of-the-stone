import pygame
import random
import os
import time
import json
import shutil
import sys
import math
import signal
import traceback
import logging
import threading
import socket
import pickle
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from PIL import Image

# Ensure the game runs from the correct directory (where the game files are located)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Add the parent directories to Python path for imports
sys.path.append(os.path.join(script_dir, ".."))
sys.path.append(os.path.join(script_dir, "../.."))
sys.path.append(os.path.join(script_dir, "../../.."))
sys.path.append(os.path.join(script_dir, "../../../.."))
sys.path.append(os.path.join(script_dir, "../../../../.."))

# =============================================================================
# COMPREHENSIVE ERROR HANDLING & LOGGING SYSTEM
# =============================================================================

class GameError(Exception):
    """Base exception class for all game-related errors"""
    pass

class WorldGenerationError(GameError):
    """Raised when world generation fails"""
    pass

class SaveSystemError(GameError):
    """Raised when save operations fail"""
    pass

class UIError(GameError):
    """Raised when UI operations fail"""
    pass

class ResourceError(GameError):
    """Raised when resource loading fails"""
    pass

# Configure comprehensive logging
def setup_logging():
    """Setup comprehensive logging system with multiple handlers"""
    log_dir = Path("../../../../../logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_dir / "game_detailed.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = logging.FileHandler(log_dir / "game_errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

# Initialize logging
logger = setup_logging()

# =============================================================================
# CONFIGURATION MANAGEMENT SYSTEM
# =============================================================================

@dataclass
class GameConfig:
    """Centralized configuration management with validation"""
    # Display settings
    screen_width: int = 1280
    screen_height: int = 720
    fullscreen: bool = False
    fps_limit: int = 60
    vsync: bool = True
    
    # Game settings
    tile_size: int = 32
    auto_save_interval: int = 300  # 5 minutes
    max_backups: int = 5
    
    # World settings
    world_chunk_size: int = 50
    max_world_height: int = 100
    min_world_height: int = 0
    
    # Performance settings
    max_entities: int = 1000
    max_particles: int = 500
    enable_particles: bool = True
    
    def validate(self) -> List[str]:
        """Validate configuration values and return list of errors"""
        errors = []
        
        if self.screen_width < 800 or self.screen_height < 600:
            errors.append("Screen dimensions must be at least 800x600")
        
        if self.fps_limit < 30 or self.fps_limit > 300:
            errors.append("FPS limit must be between 30 and 300")
        
        if self.tile_size < 16 or self.tile_size > 64:
            errors.append("Tile size must be between 16 and 64")
        
        if self.auto_save_interval < 60:
            errors.append("Auto-save interval must be at least 60 seconds")
        
        return errors
    
    def save_to_file(self, filepath: str) -> bool:
        """Save configuration to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.__dict__, f, indent=2)
            logger.info(f"Configuration saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'GameConfig':
        """Load configuration from file with defaults fallback"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            config = cls(**data)
            logger.info(f"Configuration loaded from {filepath}")
        except Exception as e:
            logger.warning(f"Failed to load configuration, using defaults: {e}")
            config = cls()
        
        # Validate loaded config
        errors = config.validate()
        if errors:
            logger.warning(f"Configuration validation errors: {errors}")
        
        return config

# =============================================================================
# RESOURCE MANAGEMENT SYSTEM
# =============================================================================

class ResourceManager:
    """Comprehensive resource management with caching and error handling"""
    
    def __init__(self):
        self._textures: Dict[str, pygame.Surface] = {}
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._fonts: Dict[str, pygame.font.Font] = {}
        self._resource_paths: Dict[str, Path] = {}
        self._load_errors: List[str] = []
        
        # Resource directories
        self.directories = {
            'tiles': Path("../../../../tiles"),
            'items': Path("../../../../items"),
            'mobs': Path("../../../../mobs"),
            'player': Path("../../../../player"),
            'hp': Path("../../../../HP"),
            'sounds': Path("../../../../../damage"),
            'fonts': Path("../../../../fonts")
        }
        
        # Validate directories exist
        self._validate_directories()
    
    def _validate_directories(self):
        """Validate that all required directories exist"""
        for name, path in self.directories.items():
            if not path.exists():
                logger.warning(f"Resource directory {name} does not exist: {path}")
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created resource directory: {path}")
                except Exception as e:
                    logger.error(f"Failed to create resource directory {path}: {e}")
    
    def load_texture(self, path: str, size: Tuple[int, int] = None) -> Optional[pygame.Surface]:
        """Load and cache texture with error handling"""
        try:
            if path in self._textures:
                return self._textures[path]
            
            if not os.path.exists(path):
                logger.error(f"Texture file not found: {path}")
                return None
            
            texture = pygame.image.load(path).convert_alpha()
            if size:
                texture = pygame.transform.scale(texture, size)
            
            self._textures[path] = texture
            logger.debug(f"Loaded texture: {path}")
            return texture
            
        except Exception as e:
            logger.error(f"Failed to load texture {path}: {e}")
            self._load_errors.append(f"Texture: {path} - {e}")
            return None
    
    def load_sound(self, path: str) -> Optional[pygame.mixer.Sound]:
        """Load and cache sound with error handling"""
        try:
            if path in self._sounds:
                return self._sounds[path]
            
            if not os.path.exists(path):
                logger.error(f"Sound file not found: {path}")
                return None
            
            sound = pygame.mixer.Sound(path)
            self._sounds[path] = sound
            logger.debug(f"Loaded sound: {path}")
            return sound
            
        except Exception as e:
            logger.error(f"Failed to load sound {path}: {e}")
            self._load_errors.append(f"Sound: {path} - {e}")
            return None
    
    def load_font(self, name: str, size: int) -> Optional[pygame.font.Font]:
        """Load and cache font with error handling"""
        cache_key = f"{name}_{size}"
        
        try:
            if cache_key in self._fonts:
                return self._fonts[cache_key]
            
            font = pygame.font.SysFont(name, size)
            self._fonts[cache_key] = font
            logger.debug(f"Loaded font: {name} size {size}")
            return font
            
        except Exception as e:
            logger.error(f"Failed to load font {name} size {size}: {e}")
            self._load_errors.append(f"Font: {name} size {size} - {e}")
            return None
    
    def get_load_errors(self) -> List[str]:
        """Get list of all resource loading errors"""
        return self._load_errors.copy()
    
    def clear_cache(self):
        """Clear all cached resources"""
        self._textures.clear()
        self._sounds.clear()
        self._fonts.clear()
        logger.info("Resource cache cleared")
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        texture_memory = sum(
            texture.get_size()[0] * texture.get_size()[1] * 4 
            for texture in self._textures.values()
        )
        
        return {
            'textures': len(self._textures),
            'sounds': len(self._sounds),
            'fonts': len(self._fonts),
            'texture_memory_bytes': texture_memory,
            'load_errors': len(self._load_errors)
        }

# =============================================================================
# STATE MANAGEMENT SYSTEM
# =============================================================================

class GameState(Enum):
    """Enumeration of all possible game states"""
    TITLE = "title"
    WORLD_SELECTION = "world_selection"  # New state for world selection
    USERNAME_REQUIRED = "username_required"  # New state for username required
    GAME = "game"
    PAUSED = "paused"
    INVENTORY = "inventory"
    SHOP = "shop"
    MULTIPLAYER = "multiplayer"
    OPTIONS = "options"
    CONTROLS = "controls"
    ABOUT = "about"
    USERNAME_CREATE = "username_create"
    SKIN_CREATOR = "skin_creator"
    LOADING = "loading"
    ERROR = "error"

class StateManager:
    """Robust state management with validation and transitions"""
    
    def __init__(self):
        self._current_state = GameState.TITLE
        self._previous_state = None
        self._state_stack: List[GameState] = []
        self._state_data: Dict[GameState, Dict[str, Any]] = {}
        self._transition_callbacks: Dict[GameState, List[callable]] = {}
        
        # Initialize state data
        for state in GameState:
            self._state_data[state] = {}
    
    @property
    def current_state(self) -> GameState:
        return self._current_state
    
    @property
    def previous_state(self) -> GameState:
        return self._previous_state
    
    def change_state(self, new_state: GameState, data: Dict[str, Any] = None) -> bool:
        """Change game state with validation and callbacks"""
        try:
            # Validate state transition
            if not self._is_valid_transition(new_state):
                logger.warning(f"Invalid state transition: {self._current_state} -> {new_state}")
                return False
            
            # Store current state
            self._previous_state = self._current_state
            self._state_stack.append(self._current_state)
            
            # Update state data
            if data:
                self._state_data[new_state].update(data)
            
            # Execute exit callbacks for current state
            self._execute_state_callbacks(self._current_state, "exit")
            
            # Change state
            self._current_state = new_state
            logger.info(f"Game state changed: {self._previous_state} -> {new_state}")
            
            # Execute enter callbacks for new state
            self._execute_state_callbacks(new_state, "enter")
            
            return True
            
        except Exception as e:
            logger.error(f"State change failed: {e}")
            return False
    
    def push_state(self, new_state: GameState, data: Dict[str, Any] = None) -> bool:
        """Push new state onto stack (for overlays)"""
        return self.change_state(new_state, data)
    
    def pop_state(self) -> bool:
        """Pop state from stack and return to previous"""
        if len(self._state_stack) < 1:
            logger.warning("Cannot pop state: stack is empty")
            return False
        
        previous_state = self._state_stack.pop()
        return self.change_state(previous_state)
    
    def _is_valid_transition(self, new_state: GameState) -> bool:
        """Check if state transition is valid"""
                # Define valid transitions
        valid_transitions = {
            GameState.TITLE: [GameState.OPTIONS, GameState.CONTROLS, GameState.ABOUT, GameState.SHOP, GameState.MULTIPLAYER, GameState.USERNAME_CREATE, GameState.WORLD_SELECTION],
            GameState.WORLD_SELECTION: [GameState.TITLE, GameState.GAME, GameState.USERNAME_REQUIRED],
            GameState.USERNAME_REQUIRED: [GameState.TITLE],
            GameState.GAME: [GameState.PAUSED, GameState.INVENTORY, GameState.SHOP, GameState.TITLE],
            GameState.PAUSED: [GameState.GAME, GameState.TITLE, GameState.OPTIONS],
            GameState.INVENTORY: [GameState.GAME],
            GameState.SHOP: [GameState.GAME, GameState.TITLE],
            GameState.MULTIPLAYER: [GameState.TITLE, GameState.GAME],
            GameState.OPTIONS: [GameState.TITLE, GameState.PAUSED],
            GameState.CONTROLS: [GameState.TITLE],
            GameState.ABOUT: [GameState.TITLE],
            GameState.USERNAME_CREATE: [GameState.TITLE],
            GameState.SKIN_CREATOR: [GameState.SHOP],
            GameState.LOADING: [GameState.GAME, GameState.ERROR],
            GameState.ERROR: [GameState.TITLE]
        }
        
        current = self._current_state
        return new_state in valid_transitions.get(current, [])
    
    def add_state_callback(self, state: GameState, callback: callable, callback_type: str = "enter"):
        """Add callback for state enter/exit events"""
        if callback_type not in ["enter", "exit"]:
            logger.error(f"Invalid callback type: {callback_type}")
            return
        
        key = f"{state}_{callback_type}"
        if key not in self._transition_callbacks:
            self._transition_callbacks[key] = []
        
        self._transition_callbacks[key].append(callback)
    
    def _execute_state_callbacks(self, state: GameState, callback_type: str):
        """Execute all callbacks for state transitions"""
        key = f"{state}_{callback_type}"
        callbacks = self._transition_callbacks.get(key, [])
        
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"State callback failed: {e}")
    
    def get_state_data(self, state: GameState) -> Dict[str, Any]:
        """Get data associated with a state"""
        return self._state_data.get(state, {}).copy()
    
    def set_state_data(self, state: GameState, data: Dict[str, Any]):
        """Set data for a state"""
        if state not in self._state_data:
            self._state_data[state] = {}
        self._state_data[state].update(data)

# =============================================================================
# ERROR RECOVERY SYSTEM
# =============================================================================

class ErrorRecovery:
    """Comprehensive error recovery and fallback system"""
    
    def __init__(self):
        self._error_count = 0
        self._max_errors = 10
        self._recovery_attempts = 0
        self._max_recovery_attempts = 3
        self._error_history: List[Dict[str, Any]] = []
    
    def handle_error(self, error: Exception, context: str = "", critical: bool = False) -> bool:
        """Handle errors with recovery attempts"""
        error_info = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'critical': critical,
            'traceback': traceback.format_exc()
        }
        
        self._error_history.append(error_info)
        self._error_count += 1
        
        logger.error(f"Error in {context}: {error}")
        
        if critical:
            logger.critical("Critical error detected - attempting recovery")
            return self._attempt_recovery()
        
        if self._error_count > self._max_errors:
            logger.error("Too many errors - entering safe mode")
            return self._enter_safe_mode()
        
        return True
    
    def _attempt_recovery(self) -> bool:
        """Attempt to recover from critical errors"""
        if self._recovery_attempts >= self._max_recovery_attempts:
            logger.critical("Maximum recovery attempts exceeded")
            return False
        
        self._recovery_attempts += 1
        logger.info(f"Recovery attempt {self._recovery_attempts}/{self._max_recovery_attempts}")
        
        try:
            # Attempt basic recovery
            pygame.display.flip()  # Refresh display
            pygame.event.pump()    # Process events
            
            logger.info("Recovery successful")
            return True
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            return False
    
    def _enter_safe_mode(self) -> bool:
        """Enter safe mode with minimal functionality"""
        logger.warning("Entering safe mode")
        
        try:
            # Disable non-essential features
            # Reset to safe state
            self._error_count = 0
            return True
            
        except Exception as e:
            logger.error(f"Failed to enter safe mode: {e}")
            return False
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        return {
            'total_errors': self._error_count,
            'recovery_attempts': self._recovery_attempts,
            'recent_errors': self._error_history[-5:] if self._error_history else [],
            'in_safe_mode': self._error_count > self._max_errors
        }
    
    def reset_error_count(self):
        """Reset error count (call after successful recovery)"""
        self._error_count = 0
        self._recovery_attempts = 0
        logger.info("Error count reset")

# =============================================================================
# PERFORMANCE MONITORING SYSTEM
# =============================================================================

class PerformanceMonitor:
    """Performance monitoring and optimization system"""
    
    def __init__(self):
        self.frame_times: List[float] = []
        self.operation_times: Dict[str, List[float]] = {}
        self.fps_history: List[float] = []
        self.memory_usage: List[int] = []
        self.start_time = time.time()
        
        logger.info("Performance monitor initialized")
    
    def record_frame_time(self, frame_time: float):
        """Record frame time for FPS calculation"""
        self.frame_times.append(frame_time)
        if len(self.frame_times) > 60:  # Keep last 60 frames
            self.frame_times.pop(0)
    
    def record_operation(self, operation_name: str, duration: float):
        """Record operation duration"""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
        
        self.operation_times[operation_name].append(duration)
        if len(self.operation_times[operation_name]) > 100:
            self.operation_times[operation_name].pop(0)
    
    def get_fps(self) -> float:
        """Calculate current FPS"""
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            'fps': self.get_fps(),
            'avg_frame_time': sum(self.frame_times) / len(self.frame_times) if self.frame_times else 0,
            'total_uptime': time.time() - self.start_time,
            'operations': {}
        }
        
        for op_name, times in self.operation_times.items():
            if times:
                report['operations'][op_name] = {
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'count': len(times)
                }
        
        return report
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get performance optimization suggestions"""
        suggestions = []
        
        current_fps = self.get_fps()
        if current_fps < 30:
            suggestions.append("FPS is low - consider reducing graphics quality")
        
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            if avg_frame_time > 0.033:  # More than 30 FPS target
                suggestions.append("Frame time is high - check for expensive operations")
        
        return suggestions

# =============================================================================
# INITIALIZE CORE SYSTEMS
# =============================================================================

# Initialize core systems
config = GameConfig()
resource_manager = ResourceManager()
state_manager = StateManager()
error_recovery = ErrorRecovery()
performance_monitor = PerformanceMonitor()

logger.info("Core systems initialized successfully")

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
# FIXED IMPORTS: Add proper path handling for modular imports
import sys
import os

# Add parent directory to path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import our modules with error handling
try:
    from managers.character_manager import CharacterManager
    from network.multiplayer_server import MultiplayerServer
    from UI.multiplayer_ui import MultiplayerUI  # Note: UI folder is capitalized
except ImportError as e:
    print(f"⚠️ Warning: Could not import some modules: {e}")
    print("🎮 Game will run in basic mode without advanced features")
    CharacterManager = None
    MultiplayerServer = None
    MultiplayerUI = None

# Add signal handler for graceful shutdown on Unix systems (macOS)
def signal_handler(signum, frame):
    print(f"\n🔄 Signal {signum} received, shutting down gracefully...")
    global running
    running = False

# Set up signal handlers for graceful shutdown
if sys.platform != 'win32':  # Unix-like systems (macOS, Linux)
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

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

# FIXED ASSET PATHS: Use absolute paths that work regardless of execution directory
current_script_dir = os.path.dirname(os.path.abspath(__file__))
assets_root = os.path.join(current_script_dir, "..", "..", "..", "..", "..")

TILE_DIR = os.path.join(assets_root, "tiles")
ITEM_DIR = os.path.join(assets_root, "items") 
MOB_DIR = os.path.join(assets_root, "mobs")
PLAYER_DIR = os.path.join(assets_root, "player")
HP_DIR = os.path.join(assets_root, "HP")

# Ensure directories exist and print paths for debugging
for dir_name, dir_path in [("TILE_DIR", TILE_DIR), ("ITEM_DIR", ITEM_DIR), ("MOB_DIR", MOB_DIR), ("PLAYER_DIR", PLAYER_DIR), ("HP_DIR", HP_DIR)]:
    if os.path.exists(dir_path):
        print(f"✅ {dir_name}: {dir_path}")
    else:
        print(f"⚠️ {dir_name} not found: {dir_path}")
        # Try alternative path
        alt_path = os.path.join(current_script_dir, "..", "..", "assets", dir_name.split("_")[0].lower())
        if os.path.exists(alt_path):
            print(f"🔄 Using alternative path: {alt_path}")
            if dir_name == "TILE_DIR": TILE_DIR = alt_path
            elif dir_name == "ITEM_DIR": ITEM_DIR = alt_path
            elif dir_name == "MOB_DIR": MOB_DIR = alt_path
            elif dir_name == "PLAYER_DIR": PLAYER_DIR = alt_path
            elif dir_name == "HP_DIR": HP_DIR = alt_path
# Fix remaining asset paths
SOUND_DIR = os.path.join(assets_root, "damage")
SAVE_DIR = os.path.join(assets_root, "save_data")

# Ensure save directory exists
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)
    print(f"📁 Created save directory: {SAVE_DIR}")

# Check sound directory
if os.path.exists(SOUND_DIR):
    print(f"✅ SOUND_DIR: {SOUND_DIR}")
else:
    print(f"⚠️ SOUND_DIR not found: {SOUND_DIR}")
    # Try alternative
    alt_sound = os.path.join(current_script_dir, "..", "..", "damage")
    if os.path.exists(alt_sound):
        SOUND_DIR = alt_sound
        print(f"🔄 Using alternative sound path: {SOUND_DIR}")

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

# --- EXTREME ENGINEERING: Enhanced Armor Texture Generators ---
def make_helmet_texture(size):
    """Procedurally draw a simple helmet texture."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Helmet colors
    metal = (169, 169, 169)  # Silver/gray
    metal_dark = (105, 105, 105)  # Darker gray
    outline = (20, 20, 20, 180)
    
    # Helmet base (rounded top)
    pygame.draw.ellipse(surf, metal, (2, 4, size - 4, size - 6))
    # Helmet rim
    pygame.draw.rect(surf, metal_dark, (2, size - 8, size - 4, 4))
    # Helmet visor area
    pygame.draw.rect(surf, metal_dark, (4, 8, size - 8, 6))
    
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)
    return surf

def make_chestplate_texture(size):
    """Procedurally draw a simple chestplate texture."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Armor colors
    metal = (169, 169, 169)  # Silver/gray
    metal_dark = (105, 105, 105)  # Darker gray
    outline = (20, 20, 20, 180)
    
    # Chestplate body
    pygame.draw.rect(surf, metal, (4, 2, size - 8, size - 4))
    # Shoulder plates
    pygame.draw.rect(surf, metal_dark, (2, 4, 4, 8))
    pygame.draw.rect(surf, metal_dark, (size - 6, 4, 4, 8))
    # Chest detail
    pygame.draw.rect(surf, metal_dark, (6, 6, size - 12, 6))
    
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)
    return surf

def make_leggings_texture(size):
    """Procedurally draw a simple leggings texture."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Armor colors
    metal = (169, 169, 169)  # Silver/gray
    metal_dark = (105, 105, 105)  # Darker gray
    outline = (20, 20, 20, 180)
    
    # Leggings body
    pygame.draw.rect(surf, metal, (4, 2, size - 8, size - 4))
    # Belt area
    pygame.draw.rect(surf, metal_dark, (2, 2, size - 4, 4))
    # Leg details
    pygame.draw.rect(surf, metal_dark, (6, 8, size - 12, 4))
    
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)
    return surf

def make_boots_texture(size):
    """Procedurally draw a simple boots texture."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Armor colors
    metal = (169, 169, 169)  # Silver/gray
    metal_dark = (105, 105, 105)  # Darker gray
    outline = (20, 20, 20, 180)
    
    # Boots base
    pygame.draw.rect(surf, metal, (4, 6, size - 8, size - 6))
    # Boots top
    pygame.draw.rect(surf, metal_dark, (2, 4, size - 4, 4))
    # Sole
    pygame.draw.rect(surf, metal_dark, (2, size - 2, size - 4, 2))
    
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)
    return surf

# --- EXTREME ENGINEERING: Additional Armor Texture Generators ---

def generate_leather_helmet_texture():
    """Generate leather helmet texture"""
    return make_armor_texture_with_color(TILE_SIZE, (139, 69, 19), "helmet")

def generate_leather_chestplate_texture():
    """Generate leather chestplate texture"""
    return make_armor_texture_with_color(TILE_SIZE, (139, 69, 19), "chestplate")

def generate_leather_leggings_texture():
    """Generate leather leggings texture"""
    return make_armor_texture_with_color(TILE_SIZE, (139, 69, 19), "leggings")

def generate_leather_boots_texture():
    """Generate leather boots texture"""
    return make_armor_texture_with_color(TILE_SIZE, (139, 69, 19), "boots")

def generate_chainmail_helmet_texture():
    """Generate chainmail helmet texture"""
    return make_armor_texture_with_color(TILE_SIZE, (169, 169, 169), "helmet")

def generate_chainmail_chestplate_texture():
    """Generate chainmail chestplate texture"""
    return make_armor_texture_with_color(TILE_SIZE, (169, 169, 169), "chestplate")

def generate_chainmail_leggings_texture():
    """Generate chainmail leggings texture"""
    return make_armor_texture_with_color(TILE_SIZE, (169, 169, 169), "leggings")

def generate_chainmail_boots_texture():
    """Generate chainmail boots texture"""
    return make_armor_texture_with_color(TILE_SIZE, (169, 169, 169), "boots")

def generate_gold_helmet_texture():
    """Generate gold helmet texture"""
    return make_armor_texture_with_color(TILE_SIZE, (255, 215, 0), "helmet")

def generate_gold_chestplate_texture():
    """Generate gold chestplate texture"""
    return make_armor_texture_with_color(TILE_SIZE, (255, 215, 0), "chestplate")

def generate_gold_leggings_texture():
    """Generate gold leggings texture"""
    return make_armor_texture_with_color(TILE_SIZE, (255, 215, 0), "leggings")

def generate_gold_boots_texture():
    """Generate gold boots texture"""
    return make_armor_texture_with_color(TILE_SIZE, (255, 215, 0), "boots")

def generate_diamond_helmet_texture():
    """Generate diamond helmet texture"""
    return make_armor_texture_with_color(TILE_SIZE, (0, 191, 255), "helmet")

def generate_diamond_chestplate_texture():
    """Generate diamond chestplate texture"""
    return make_armor_texture_with_color(TILE_SIZE, (0, 191, 255), "chestplate")

def generate_diamond_leggings_texture():
    """Generate diamond leggings texture"""
    return make_armor_texture_with_color(TILE_SIZE, (0, 191, 255), "leggings")

def generate_diamond_boots_texture():
    """Generate diamond boots texture"""
    return make_armor_texture_with_color(TILE_SIZE, (0, 191, 255), "boots")

def make_armor_texture_with_color(size, base_color, armor_type):
    """EXTREME ENGINEERING: Universal armor texture generator with material colors"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Calculate darker and lighter shades
    dark_color = tuple(max(0, int(c * 0.7)) for c in base_color)
    light_color = tuple(min(255, int(c * 1.3)) for c in base_color)
    outline = (20, 20, 20, 180)
    
    if armor_type == "helmet":
        # Helmet shape
        pygame.draw.ellipse(surf, base_color, (4, 2, size - 8, size // 2))
        pygame.draw.rect(surf, base_color, (6, size // 3, size - 12, size // 3))
        # Helmet details
        pygame.draw.line(surf, light_color, (8, 6), (size - 8, 6), 2)
        pygame.draw.line(surf, dark_color, (8, size // 2 - 2), (size - 8, size // 2 - 2), 1)
    elif armor_type == "chestplate":
        # Chestplate shape
        pygame.draw.rect(surf, base_color, (2, 4, size - 4, size - 8))
        # Chest details
        pygame.draw.line(surf, light_color, (4, 8), (size - 4, 8), 2)
        pygame.draw.line(surf, dark_color, (4, size - 8), (size - 4, size - 8), 1)
        # Side plates
        pygame.draw.rect(surf, dark_color, (2, 6, 3, size - 12))
        pygame.draw.rect(surf, dark_color, (size - 5, 6, 3, size - 12))
    elif armor_type == "leggings":
        # Leggings shape (two leg pieces)
        pygame.draw.rect(surf, base_color, (4, 2, (size - 10) // 2, size - 4))  # Left leg
        pygame.draw.rect(surf, base_color, (size // 2 + 1, 2, (size - 10) // 2, size - 4))  # Right leg
        # Leg details
        pygame.draw.line(surf, light_color, (6, 4), (6, size - 4), 1)
        pygame.draw.line(surf, light_color, (size - 6, 4), (size - 6, size - 4), 1)
    else:  # boots
        # Boots shape
        pygame.draw.rect(surf, base_color, (4, size // 2, size - 8, size // 2))
        # Boot soles
        pygame.draw.rect(surf, dark_color, (2, size - 4, size - 4, 4))
        # Boot tops
        pygame.draw.rect(surf, light_color, (6, size // 2, size - 12, 3))
    
    # Outline
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)
    return surf

def generate_iron_helmet_texture():
    """Generate iron helmet texture (enhanced version)"""
    return make_armor_texture_with_color(TILE_SIZE, (192, 192, 192), "helmet")

def generate_iron_chestplate_texture():
    """Generate iron chestplate texture (enhanced version)"""
    return make_armor_texture_with_color(TILE_SIZE, (192, 192, 192), "chestplate")

def generate_iron_leggings_texture():
    """Generate iron leggings texture (enhanced version)"""
    return make_armor_texture_with_color(TILE_SIZE, (192, 192, 192), "leggings")

def generate_iron_boots_texture():
    """Generate iron boots texture (enhanced version)"""
    return make_armor_texture_with_color(TILE_SIZE, (192, 192, 192), "boots")

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

def make_zombie_texture(size):
    """Procedural placeholder zombie texture (used if mobs/zombie.png is missing)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # Body (dark green)
    pygame.draw.rect(surf, (34, 139, 34), (4, 8, size-8, size-8))
    # Head (greenish skin)
    pygame.draw.rect(surf, (85, 107, 47), (6, 2, size-12, 8))
    # Eyes (red)
    pygame.draw.rect(surf, (255, 0, 0), (8, 4, 3, 3))
    pygame.draw.rect(surf, (255, 0, 0), (size-11, 4, 3, 3))
    # Outline
    pygame.draw.rect(surf, (0, 0, 0, 180), (0, 0, size, size), 1)
    return surf

def make_stone_sword_texture(size):
    """Procedurally draw a simple stone sword texture."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Sword colors
    stone = (128, 128, 128)  # Gray stone
    stone_dark = (96, 96, 96)  # Darker gray
    handle = (139, 69, 19)  # Brown wood
    outline = (20, 20, 20, 180)
    
    # Sword blade (vertical, centered)
    blade_w = max(3, size // 8)
    blade_h = max(8, size // 2)
    blade_x = (size - blade_w) // 2
    blade_y = 2
    
    # Blade
    pygame.draw.rect(surf, stone, (blade_x, blade_y, blade_w, blade_h))
    # Blade tip
    pygame.draw.polygon(surf, stone, [
        (blade_x, blade_y + blade_h),
        (blade_x + blade_w, blade_y + blade_h),
        (size // 2, size - 2)
    ])
    
    # Handle (horizontal, below blade)
    handle_w = max(6, size // 3)
    handle_h = max(3, size // 8)
    handle_x = (size - handle_w) // 2
    handle_y = size - handle_h - 2
    
    pygame.draw.rect(surf, handle, (handle_x, handle_y, handle_w, handle_h))
    
    # Guard (horizontal bar)
    guard_w = max(8, size // 2)
    guard_h = max(2, size // 12)
    guard_x = (size - guard_w) // 2
    guard_y = blade_y + blade_h - 2
    
    pygame.draw.rect(surf, stone_dark, (guard_x, guard_y, guard_w, guard_h))
    
    # Outline
    pygame.draw.rect(surf, outline, (0, 0, size, size), 1)
    
    return surf

def generate_terrain_column(x):
    """Generate terrain for a specific column if it hasn't been generated yet"""
    global generated_terrain_columns
    
    # Skip if already generated
    if x in generated_terrain_columns:
        return
    
    print(f"🌍 Generating terrain for column {x}")
    
    # Calculate ground height (same logic as main terrain generation)
    prev_heights = [y for y in range(0, 100) if (x - 1, y) in world_data and world_data[(x - 1, y)] == "grass"]
    if prev_heights:
        ground_y = prev_heights[0]
    else:
        height_offset = int(3 * math.sin(x * 0.2))
        ground_y = 50 + height_offset  # Base height around Y=50
    
    # Generate terrain layers
    set_block(x, ground_y, "grass")
    for y in range(ground_y + 1, ground_y + 4):  # Dirt layer
        set_block(x, y, "dirt")
    for y in range(ground_y + 4, 125):  # Stone layer
        set_block(x, y, "stone")
    set_block(x, 127, "bedrock")  # Bedrock at bottom
    
    # Mark as generated
    generated_terrain_columns.add(x)

def fix_player_spawn_position():
    """Ensure player spawns on the surface, not underground"""
    global player
    
    print(f"🏠 Fixing player spawn position from ({player['x']:.1f}, {player['y']:.1f})")
    
    # Keep the current X position but find proper Y position
    spawn_x = int(player["x"])
    
    # CRITICAL: Generate terrain at spawn point first!
    # This ensures terrain exists before we try to find a surface
    print(f"🌍 Generating terrain at spawn point ({spawn_x}) to ensure surface exists")
    
    # Generate terrain for a small area around spawn point
    for x in range(spawn_x - 5, spawn_x + 6):  # 11 columns around spawn
        generate_terrain_column(x)
    
    print(f"✅ Terrain generated around spawn point, now finding surface...")
    
    # ENHANCED COLLISION-FREE SPAWNING: Find safe spawn location
    # Search from the correct range for new world generation system
    for y in range(110, 125):  # Search in the new world generation range
        # Check if this position is safe for spawning (no blocks at player position)
        head_block = get_block(spawn_x, y)
        feet_block = get_block(spawn_x, y + 1)
        ground_block = get_block(spawn_x, y + 2)
        
        # Player needs 2 blocks of air above ground
        if (is_non_solid_block(head_block) and 
            is_non_solid_block(feet_block) and 
            ground_block and ground_block not in ["water", "lava"]):
            
            # Found safe spawn location
            player["y"] = float(y)  # Place player with air above and solid ground below
            player["vel_y"] = 0.0
            player["on_ground"] = False
            print(f"✅ COLLISION-FREE SPAWN: Player at ({player['x']:.1f}, {player['y']:.1f}) with ground: {ground_block}")
            return True
    
    # Fallback: search wider range and ensure collision-free spawn
    for y in range(50, 150):
        head_block = get_block(spawn_x, y)
        feet_block = get_block(spawn_x, y + 1)
        ground_block = get_block(spawn_x, y + 2)
        
        if (is_non_solid_block(head_block) and 
            is_non_solid_block(feet_block) and 
            ground_block and ground_block not in ["water", "lava"]):
            
            player["y"] = float(y)
            player["vel_y"] = 0.0
            player["on_ground"] = False
            print(f"✅ FALLBACK SAFE SPAWN: Player at ({player['x']:.1f}, {player['y']:.1f}) with ground: {ground_block}")
            return True
    
    # Emergency: Create a safe platform if no suitable location found
    safe_y = 10
    # Clear any blocks above and create a platform
    for clear_y in range(safe_y, safe_y + 3):
        world_data[f"{spawn_x},{clear_y}"] = None
    
    world_data[f"{spawn_x},{safe_y + 3}"] = "stone"  # Create ground
    world_data[f"{spawn_x - 1},{safe_y + 3}"] = "stone"
    world_data[f"{spawn_x + 1},{safe_y + 3}"] = "stone"
    
    player["y"] = float(safe_y)
    player["vel_y"] = 0.0
    player["on_ground"] = False
    print(f"🛠️ EMERGENCY SAFE SPAWN: Created platform at ({player['x']:.1f}, {player['y']:.1f})")
    return True

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
    "red_brick": load_texture(os.path.join(TILE_DIR, "red_brick.png")),
    "oak_planks": load_texture(os.path.join(TILE_DIR, "oak_planks.png")),
    "sword": load_texture(os.path.join(ITEM_DIR, "sword.png")),
    "stone_sword": make_stone_sword_texture(TILE_SIZE),  # Generated stone sword texture
    "pickaxe": load_texture(os.path.join(ITEM_DIR, "pickaxe.png")),
    "water": load_texture(os.path.join(TILE_DIR, "water.png")),
    "lava": load_texture(os.path.join(TILE_DIR, "lava.png")),
    "bed": load_texture(os.path.join(TILE_DIR, "bed.png")),
    "ladder": make_ladder_texture(TILE_SIZE),
    "door": load_texture(os.path.join(TILE_DIR, "door.png")),
    "bread": load_texture(os.path.join(ITEM_DIR, "bread.png")),
    "wheat": load_texture(os.path.join(TILE_DIR, "carrot.gif")),  # Using carrot as wheat for now
    "stick": load_texture(os.path.join(TILE_DIR, "log.png")),  # Using log as stick for now
}

# --- Villager texture (tries file, falls back to procedural) ---
try:
    textures["villager"] = load_texture(os.path.join(MOB_DIR, "villager.png"))
except Exception:
    textures["villager"] = make_villager_texture(TILE_SIZE)

# --- Zombie texture (tries file, falls back to procedural) ---
try:
    textures["zombie"] = load_texture(os.path.join(MOB_DIR, "zombie.png"))
except Exception:
    textures["zombie"] = make_zombie_texture(TILE_SIZE)

# --- Bed texture (tries file, falls back to a procedural bed texture) ---
try:
    textures["bed"] = load_texture(os.path.join(TILE_DIR, "bed.png"))  # preferred: assets/tiles/bed.png
except Exception:
    textures["bed"] = make_bed_texture(TILE_SIZE)

# --- Armor textures (tries files, falls back to procedural textures) ---
try:
    textures["iron_helmet"] = load_texture(os.path.join(ITEM_DIR, "iron_helmet.png"))
except Exception:
    textures["iron_helmet"] = make_helmet_texture(TILE_SIZE)

try:
    textures["iron_chestplate"] = load_texture(os.path.join(ITEM_DIR, "iron_chestplate.png"))
except Exception:
    textures["iron_chestplate"] = make_chestplate_texture(TILE_SIZE)

try:
    textures["iron_leggings"] = load_texture(os.path.join(ITEM_DIR, "iron_leggings.png"))
except Exception:
    textures["iron_leggings"] = make_leggings_texture(TILE_SIZE)

try:
    textures["iron_boots"] = load_texture(os.path.join(ITEM_DIR, "iron_boots.png"))
except Exception:
    textures["iron_boots"] = make_boots_texture(TILE_SIZE)

# --- EXTREME ENGINEERING: Enhanced armor textures with all materials ---
# Leather armor
textures["leather_helmet"] = generate_leather_helmet_texture()
textures["leather_chestplate"] = generate_leather_chestplate_texture()
textures["leather_leggings"] = generate_leather_leggings_texture()
textures["leather_boots"] = generate_leather_boots_texture()

# Chainmail armor
textures["chainmail_helmet"] = generate_chainmail_helmet_texture()
textures["chainmail_chestplate"] = generate_chainmail_chestplate_texture()
textures["chainmail_leggings"] = generate_chainmail_leggings_texture()
textures["chainmail_boots"] = generate_chainmail_boots_texture()

# Gold armor
textures["gold_helmet"] = generate_gold_helmet_texture()
textures["gold_chestplate"] = generate_gold_chestplate_texture()
textures["gold_leggings"] = generate_gold_leggings_texture()
textures["gold_boots"] = generate_gold_boots_texture()

# Diamond armor
textures["diamond_helmet"] = generate_diamond_helmet_texture()
textures["diamond_chestplate"] = generate_diamond_chestplate_texture()
textures["diamond_leggings"] = generate_diamond_leggings_texture()
textures["diamond_boots"] = generate_diamond_boots_texture()

# Enhanced iron armor (replace old versions)
textures["iron_helmet"] = generate_iron_helmet_texture()
textures["iron_chestplate"] = generate_iron_chestplate_texture()
textures["iron_leggings"] = generate_iron_leggings_texture()
textures["iron_boots"] = generate_iron_boots_texture()

# =============================================================================
# AUTOMATIC GIF ANIMATION SYSTEM
# =============================================================================

# Global GIF animation manager
gif_animations = {}
gif_frame_timers = {}

class GIFAnimator:
    """Automatic GIF animation system for any GIF files in the game"""
    
    def __init__(self, gif_path, frame_duration=100):
        self.gif_path = gif_path
        self.frame_duration = frame_duration  # milliseconds per frame
        self.frames = []
        self.current_frame = 0
        self.last_frame_time = 0
        self.load_gif()
    
    def load_gif(self):
        """Load GIF and extract frames using PIL"""
        try:
            with Image.open(self.gif_path) as img:
                # Convert to RGBA if needed
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Extract frames
                frame_count = 0
                while True:
                    try:
                        # Convert PIL image to pygame surface
                        frame_data = img.convert('RGBA')
                        frame_surface = pygame.image.fromstring(
                            frame_data.tobytes(), frame_data.size, frame_data.mode
                        )
                        self.frames.append(frame_surface)
                        frame_count += 1
                        
                        # Move to next frame
                        img.seek(img.tell() + 1)
                    except EOFError:
                        break
                
                print(f"🎬 Loaded GIF: {self.gif_path} with {frame_count} frames")
                
        except Exception as e:
            print(f"⚠️ Failed to load GIF {self.gif_path}: {e}")
            # Fallback to single frame
            try:
                fallback_surface = pygame.image.load(gif_path)
                self.frames = [fallback_surface]
            except:
                print(f"❌ Complete failure loading {self.gif_path}")
                self.frames = []
    
    def get_current_frame(self):
        """Get current frame based on timing"""
        if not self.frames:
            return None
        
        current_time = pygame.time.get_ticks()
        
        # Check if it's time for next frame
        if current_time - self.last_frame_time >= self.frame_duration:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_frame_time = current_time
        
        return self.frames[self.current_frame]
    
    def get_frame_count(self):
        """Get total number of frames"""
        return len(self.frames)

def load_all_gif_animations():
    """Automatically detect and load all GIF files in the game"""
    global gif_animations
    
    # Clear existing animations
    gif_animations.clear()
    gif_frame_timers.clear()
    
    # Search for GIF files in assets directory
    assets_dir = "../../../.."
    if os.path.exists(assets_dir):
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                if file.lower().endswith('.gif'):
                    gif_path = os.path.join(root, file)
                    try:
                        # Create animator for this GIF
                        animator = GIFAnimator(gif_path)
                        if animator.frames:
                            gif_animations[gif_path] = animator
                            print(f"🎬 Auto-loaded GIF animation: {gif_path}")
                    except Exception as e:
                        print(f"⚠️ Failed to auto-load GIF {gif_path}: {e}")
    
    print(f"🎬 Total GIF animations loaded: {len(gif_animations)}")

def get_gif_animation(gif_path):
    """Get GIF animation for a specific path"""
    return gif_animations.get(gif_path)

def update_gif_animations():
    """Update all GIF animations (call this in game loop)"""
    for animator in gif_animations.values():
        animator.get_current_frame()  # This updates the frame timing

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

# Boss texture will be loaded when needed

# Load sound
damage_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "damage_sound.wav"))

# Fonts
font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 16)
title_font = pygame.font.SysFont("Arial", 36)
BIG_FONT = pygame.font.SysFont("Arial", 48)

# World management system will be initialized later in the new system

# Game states - Using new enum system
# Add missing states that are still referenced
STATE_MENU = "menu"  # Temporary until full migration
STATE_MULTIPLAYER = "multiplayer"  # Temporary until full migration

game_state = GameState.TITLE

# Time and cycle
clock = pygame.time.Clock()
day_start_time = time.time()
is_day = True
day_count = 1  # Track current day number
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
    "inventory": [],  # Hotbar (9 slots)
    "backpack": [],   # Extended inventory (27 slots)
    "selected": 0,
    "username": "",
    "armor": {
        "helmet": None,
        "chestplate": None,
        "leggings": None,
        "boots": None
    },
    "stamina": 100,  # Current stamina
    "max_stamina": 100,  # Maximum stamina capacity
            "facing_direction": 1,  # 1 = right, -1 = left
        "last_x": 10,  # Initialize last position for movement detection
        "last_y": 0
}

# Global username for all worlds
GLOBAL_USERNAME = "dreamcrusherx"

MAX_FALL_SPEED = 10
GRAVITY = 1
JUMP_STRENGTH = -12  # Increased from -8 to -12 for higher jumping to clear blocks
# Movement speeds - frame-rate independent for consistent gameplay across devices
MOVE_SPEED = 0.15  # Fast, responsive movement
SLOW_SPEED = 0.08  # Slower when holding shift

# Stamina system
STAMINA_DRAIN_RATE = 0.8  # Reduced from 2.0 - stamina lost per frame while climbing without ladder
STAMINA_REGEN_RATE = 1.2  # Increased from 0.5 - stamina regained per frame when not climbing
STAMINA_REGEN_DELAY = 30  # Reduced from 60 - frames to wait before stamina starts regenerating (0.5 seconds)

# World and camera
world_data = {}
entities = []
camera_x = 0
camera_y = 0  # Vertical camera position
fall_start_y = None
# Village generation tracking
generated_village_chunks = set()
generated_terrain_columns = set()  # Track which columns have had terrain generated

# --- Message HUD (temporary notifications) ---
message_text = ""
message_until = 0  # pygame.time.get_ticks() deadline

# --- Villager Dialogue System ---
villager_dialogue_text = ""
villager_dialogue_until = 0

# --- Door System ---
door_states = {}  # Track which doors are open/closed

# --- Stamina System ---
stamina_regen_timer = 0  # Timer for stamina regeneration delay

# EXTREME ENGINEERING: Legendary Boss Fight System
BOSS_SPAWN_DISTANCE = 200  # 200 blocks away (more reasonable distance)
BOSS_ARENA_SIZE = 100  # 100x100 block arena
BOSS_PHASE_1_HP = 1000  # First form: 1000 HP
BOSS_PHASE_2_HP = 1500  # Second form: 1500 HP (orange form)
BOSS_SWORD_DAMAGE = 50  # Player sword damage to boss
BOSS_ATTACK_DAMAGE = {
    "fire": 2,      # Fire attack: 2 hearts (4 HP)
    "phase1": 6,    # First form attack: 6 hearts (12 HP)  
    "phase2": 16    # Second form attack: 16 hearts (32 HP)
}

# Boss fight state
boss_fight_active = False
boss_health = BOSS_PHASE_1_HP
boss_max_health = BOSS_PHASE_1_HP
boss_phase = 1
boss_attack_cooldown = 0
boss_attack_timer = 0
boss_position = {"x": 0, "y": 0}
boss_direction = 1
boss_attack_type = "phase1"
boss_arena_center = {"x": 0, "y": 0}

# Boss texture system
boss_texture = None
boss_texture_loaded = False

# Legend NPC state
legend_npc_spawned = False
legend_npc_position = {"x": 0, "y": 0}
legend_npc_dialogue_cooldown = 0

# EXTREME ENGINEERING: Professional Multiplayer System
MULTIPLAYER_PORT = 25565  # Standard Minecraft-style port
MULTIPLAYER_MAX_PLAYERS = 20
MULTIPLAYER_TPS = 20  # 20 TPS (Ticks Per Second)
MULTIPLAYER_SYNC_RATE = 5   # Sync every 5 ticks

# Multiplayer state
multiplayer_mode = False
is_host = False
is_client = False
server_socket = None
client_socket = None
server_thread = None
client_thread = None

# Multiplayer data
online_players = {}  # {player_id: player_data}
server_list = []     # List of available servers
local_server_info = None  # Current hosted server info

# Multiplayer UI state
multiplayer_menu_state = "main"  # main, host, join, server_list
selected_server = None
host_world_name = ""
server_search_results = []

# Multiplayer button references
multiplayer_host_btn = None
multiplayer_join_btn = None
multiplayer_back_btn = None
multiplayer_start_host_btn = None
multiplayer_host_back_btn = None
multiplayer_search_btn = None
multiplayer_join_back_btn = None
multiplayer_server_list_back_btn = None

# EXTREME ENGINEERING: Multiplayer Chat System
chat_messages = []
chat_input_active = False
chat_input_text = ""
chat_input_cursor = 0
chat_input_timer = 0
chat_visible = False

def show_message(text, ms=1500):
    global message_text, message_until
    message_text = text
    message_until = pygame.time.get_ticks() + ms

def send_chat_message(message):
    """Send a chat message to the multiplayer server"""
    global chat_messages, last_chat_time
    
    if not is_connected:
        return
    
    # Add message to local chat
    chat_messages.append(("You", message, time.time()))
    last_chat_time = time.time()
    
    # Keep only last 50 messages
    if len(chat_messages) > 50:
        chat_messages = chat_messages[-50:]
    
    # Send to server if connected
    if multiplayer_client:
        try:
            multiplayer_client.send_message({
                "type": "chat",
                "username": player.get("username", "Player"),
                "message": message
            })
        except Exception as e:
            print(f"⚠️ Failed to send chat message: {e}")

def add_chat_message(username, message):
    """Add a chat message from another player"""
    global chat_messages, last_chat_time
    
    chat_messages.append((username, message, time.time()))
    last_chat_time = time.time()
    
    # Keep only last 50 messages
    if len(chat_messages) > 50:
        chat_messages = chat_messages[-50:]
    
    print(f"💬 {username}: {message}")

def draw_multiplayer_chat():
    """Draw the multiplayer chat interface"""
    if not is_connected:
        return
    
    # Draw chat background
    chat_bg = pygame.Surface((400, 200))
    chat_bg.set_alpha(180)
    chat_bg.fill((0, 0, 0))
    screen.blit(chat_bg, (10, SCREEN_HEIGHT - 220))
    
    # Draw chat messages
    y_offset = SCREEN_HEIGHT - 210
    for i, (username, message, timestamp) in enumerate(chat_messages[-8:]):  # Show last 8 messages
        if time.time() - timestamp < 30:  # Only show messages from last 30 seconds
            color = (255, 255, 255) if username != "You" else (0, 255, 0)
            text = small_font.render(f"{username}: {message}", True, color)
            screen.blit(text, (15, y_offset + i * 20))
    
    # Draw chat input if active
    if chat_active:
        input_bg = pygame.Surface((400, 30))
        input_bg.set_alpha(200)
        input_bg.fill((50, 50, 50))
        screen.blit(input_bg, (10, SCREEN_HEIGHT - 40))
        
        # Draw input text with cursor
        input_text = small_font.render(chat_input, True, (255, 255, 255))
        screen.blit(input_text, (15, SCREEN_HEIGHT - 35))
        
        # Draw blinking cursor
        if time.time() % 1 < 0.5:
            cursor_x = 15 + input_text.get_width()
            pygame.draw.line(screen, (255, 255, 255), 
                           (cursor_x, SCREEN_HEIGHT - 35), 
                           (cursor_x, SCREEN_HEIGHT - 20), 2)
    
    # Draw chat hint
    if not chat_active and time.time() - last_chat_time < 5:
        hint_text = small_font.render("Press T to chat", True, (200, 200, 200))
        screen.blit(hint_text, (15, SCREEN_HEIGHT - 25))

def start_multiplayer_server(world_name):
    """Start hosting a multiplayer server"""
    global multiplayer_server, is_hosting
    
    try:
        multiplayer_server = MultiplayerServer()
        if multiplayer_server.start_server(world_name):
            is_hosting = True
            show_message(f"🌐 Server started! Others can join at {multiplayer_server.host}:{multiplayer_server.port}")
            return True
        else:
            show_message("❌ Failed to start server")
            return False
    except Exception as e:
        show_message(f"❌ Server error: {e}")
        return False

def join_multiplayer_server(server_ip, server_port):
    """Join a multiplayer server"""
    global multiplayer_client, is_connected
    
    try:
        # This would connect to the server
        # For now, just simulate connection
        is_connected = True
        show_message(f"🔗 Connected to {server_ip}:{server_port}")
        return True
    except Exception as e:
        show_message(f"❌ Connection failed: {e}")
        return False

def create_new_world_with_seed(seed_input):
    """Create a new world with the given seed"""
    global game_state, world_name_input, world_seed_input
    
    # Validate world name
    if not world_name_input or len(world_name_input) < 3:
        show_message("❌ World name must be at least 3 characters!")
        return
    
    # Generate a new world
    show_message("🌍 Generating new world...")
    if load_game():
        game_state = GameState.GAME
        update_pause_state()  # Resume time when entering game
        show_message("✅ New world generated successfully!")
    else:
        show_message("❌ Failed to generate world!")
    
    # Reset inputs
    world_name_input = ""
    world_seed_input = ""

def show_username_error(text, ms=2000):
    """Show username-specific error message"""
    global username_error_message, username_error_until
    username_error_message = text
    username_error_until = pygame.time.get_ticks() + ms

def show_world_create_error(text, ms=3000):
    """Show world creation error message"""
    global world_create_error_message, world_create_error_until
    world_create_error_message = text
    world_create_error_until = pygame.time.get_ticks() + ms

def update_stamina(is_climbing_without_ladder=False):
    """Update player stamina based on climbing state"""
    global stamina_regen_timer
    
    if is_climbing_without_ladder:
        # Drain stamina while climbing without ladder
        player["stamina"] = max(0, player["stamina"] - STAMINA_DRAIN_RATE)
        stamina_regen_timer = 0  # Reset regeneration timer
        print(f"💪 Stamina: {player['stamina']:.1f}/100 (Climbing)")
    else:
        # Regenerate stamina when not climbing
        if stamina_regen_timer > 0:
            stamina_regen_timer -= 1
        else:
            if player["stamina"] < player["max_stamina"]:
                # Bonus regeneration when on ground
                bonus_regen = STAMINA_REGEN_RATE * 1.5 if player.get("on_ground", False) else STAMINA_REGEN_RATE
                player["stamina"] = min(player["max_stamina"], player["stamina"] + bonus_regen)
                # Show regeneration progress occasionally
                if player["stamina"] % 20 < STAMINA_REGEN_RATE and player["stamina"] < player["max_stamina"]:
                    print(f"💪 Stamina regenerating: {player['stamina']:.1f}/100")
                # Only print when stamina is fully restored to avoid spam
                if player["stamina"] >= player["max_stamina"]:
                    print(f"💪 Stamina fully restored!")
    
    # Ensure stamina stays within bounds
    player["stamina"] = max(0, min(player["stamina"], player["max_stamina"]))
    
    # Set regeneration delay when player stops climbing
    if not is_climbing_without_ladder and stamina_regen_timer == 0:
        stamina_regen_timer = STAMINA_REGEN_DELAY

def restore_stamina(amount=100):
    """Restore stamina by specified amount (for potions, rest, etc.)"""
    old_stamina = player["stamina"]
    player["stamina"] = min(player["max_stamina"], player["stamina"] + amount)
    restored = player["stamina"] - old_stamina
    if restored > 0:
        print(f"💪 Stamina restored by {restored} points!")
    return restored

def can_climb_without_ladder():
    """Check if player can climb without a ladder (has stamina)"""
    return player["stamina"] > 0

def is_climbing_without_ladder():
    """Check if player is currently climbing without a ladder"""
    keys = pygame.key.get_pressed()
    return (keys[pygame.K_w] or keys[pygame.K_UP]) and not is_on_ladder()

def is_on_ladder():
    """Check if player is currently on a ladder"""
    px, py = player["x"], player["y"]
    return (get_block(int(px), int(py)) == "ladder" or
            get_block(int(px), int(py + 0.9)) == "ladder")

# --- Chest & Drag-and-Drop UI state ---
chest_open = False
open_chest_pos = None
drag_item = None           # {'type': str, 'count': int} currently held by mouse
drag_from = None           # ('chest', index) or ('hotbar', index)
mouse_pos = (0, 0)

# --- Inventory Drag-and-Drop state ---
inventory_drag_item = None  # Item being dragged in inventory
inventory_drag_from = None  # ('hotbar', index) or ('backpack', index) or ('armor', slot_name)

# --- World Generation Control ---
world_loaded_from_save = False  # Flag to prevent overwriting saved world data

# Old WorldPersistenceManager class removed - replaced with new world system

# --- UI Button References ---
play_btn = None
username_btn = None
controls_btn = None
about_btn = None
options_btn = None
quit_btn = None
resume_btn = None
inventory_close_button = None
left_arrow_btn = None
right_arrow_btn = None
select_btn = None

# --- World Selection Button References ---
world_play_btn = None
world_delete_btn = None
world_create_btn = None
world_back_btn = None

# --- Character Shop system state ---
shop_open = False
current_character_index = 0

# Character selection system - loads textures from player folder
# Coins are now managed by the coins manager

# --- Achievement tracking for special coin rewards ---
achievements = {
    "first_diamond": False,  # First diamond found (5 coins)
    "diamond_chest": False,  # Diamond found in natural chest (1,000,000 coins)
    "first_gold": False,     # First gold found (3 coins)
    "first_iron": False,     # First iron found (2 coins)
    "first_coal": False,     # First coal found (1 coin)
    "first_village": False,  # First village discovered (50 coins)
    "first_monster_kill": False,  # First monster defeated (25 coins)
    "first_carrot": False,   # First carrot eaten (10 coins)
    "first_sleep": False,    # First time sleeping in bed (20 coins)
    "first_villager_talk": False,  # First time talking to a villager (15 coins)
    "ultimate_achievement": False  # Most special achievement (1,000,000 coins)
}

# --- Character selection system ---
# Character manager handles all character-related functionality
character_manager = None

def initialize_character_manager():
    """Load all character textures from the player folder"""
    global character_manager
    
    character_manager = CharacterManager(PLAYER_DIR, TILE_SIZE)
    print("🎭 Character manager initialized")
    
    # Debug: Show what textures were loaded
    if character_manager:
        print(f"🎭 Available characters: {[char['name'] for char in character_manager.available_characters]}")
        print(f"🎭 Current selected character: {character_manager.get_current_character_name()}")
        print(f"🎭 Loaded textures: {list(character_manager.character_textures.keys())}")
    else:
        print("❌ Character manager initialization failed!")

def initialize_chat_system():
    """Initialize the chat system"""
    global chat_system
    
    try:
        try:
            from system.chat_system import ChatSystem
        except ImportError:
            print("⚠️ Warning: Chat system not available")
            ChatSystem = None
        if ChatSystem:
            chat_system = ChatSystem(SCREEN_WIDTH, SCREEN_HEIGHT)
        else:
            chat_system = None
        if chat_system:
            chat_system.set_fonts(font, font)  # Use the same font for now
        print("💬 Chat system initialized")
    except Exception as e:
        print(f"❌ Chat system initialization failed: {e}")
        chat_system = None

def initialize_coins_manager():
    """Initialize the coins manager"""
    global coins_manager
    
    try:
        try:
            from managers.coins_manager import CoinsManager
        except ImportError:
            print("⚠️ Warning: Coins manager not available")
            CoinsManager = None
        if CoinsManager:
            coins_manager = CoinsManager("coins.json")
        else:
            coins_manager = None
        if coins_manager and GLOBAL_USERNAME:
            coins_manager.set_username(GLOBAL_USERNAME)
        print("💰 Coins manager initialized")
    except Exception as e:
        print(f"❌ Coins manager initialization failed: {e}")
        coins_manager = None

def force_refresh_character():
    """Force refresh the character display - call this after character selection"""
    global player_image
    if character_manager:
        new_texture = character_manager.get_character_texture()
        if new_texture:
            player_image = new_texture
            print(f"🎭 Player texture force refreshed to: {character_manager.get_current_character_name()}")
            return True
    return False


# --- Username system state ---
username_input = ""
virtual_keys = {}
confirm_btn = None
back_btn = None
back_to_title_btn = None
username_error_message = ""
username_error_until = 0

# --- World creation system state ---
world_seed_input = ""
world_create_confirm_btn = None
world_create_back_btn = None
world_create_error_message = ""
world_create_error_until = 0

# --- Multiplayer System ---
multiplayer_server = None
multiplayer_client = None
multiplayer_ui = None
is_hosting = False
is_connected = False
connected_players = {}  # {username: player_data}
chat_messages = []  # [(username, message, timestamp), ...]
chat_input = ""
chat_active = False
chat_cursor_blink = 0
last_chat_time = 0

# --- FPS and Performance Settings ---
fps_limit = 120  # Default FPS limit
show_fps = False  # F3 debug info
fps_counter = 0  # Actual FPS counter
last_fps_time = time.time()

def get_block(x, y):
    """Get block at coordinates with validation"""
    try:
        # Convert coordinates to integers if they're floats
        x = int(x) if isinstance(x, (int, float)) else x
        y = int(y) if isinstance(y, (int, float)) else y
        
        # Validate coordinates
        if not isinstance(x, int) or not isinstance(y, int):
            print(f"⚠️ Invalid coordinates in get_block: x={x} (type: {type(x)}), y={y} (type: {type(y)})")
            return None
        
        return world_data.get(f"{x},{y}")
        
    except Exception as e:
        print(f"❌ Error getting block at ({x}, {y}): {e}")
        return None

def validate_world_integrity():
    """Validate world data integrity and fix common issues"""
    global world_data
    
    print("🔍 Validating world data integrity...")
    issues_found = 0
    fixes_applied = 0
    
    # Check for invalid keys
    invalid_keys = []
    for key in list(world_data.keys()):
        try:
            x, y = map(int, key.split(','))
            # Check if coordinates are reasonable
            if abs(x) > 10000 or abs(y) > 1000:
                invalid_keys.append(key)
                issues_found += 1
        except (ValueError, AttributeError):
            invalid_keys.append(key)
            issues_found += 1
    
    # Remove invalid keys
    for key in invalid_keys:
        del world_data[key]
        fixes_applied += 1
        print(f"🔧 Fixed: Removed invalid key: {key}")
    
    # Check for None values
    none_values = [key for key, value in world_data.items() if value is None]
    for key in none_values:
        world_data[key] = "air"  # Replace None with air
        fixes_applied += 1
        print(f"🔧 Fixed: Replaced None with air at {key}")
    
    print(f"✅ World validation complete: {issues_found} issues found, {fixes_applied} fixes applied")
    return issues_found == 0

def set_block(x, y, block_type):
    """Set block at coordinates with validation and error handling"""
    try:
        # Convert coordinates to integers if they're floats
        x = int(x) if isinstance(x, (int, float)) else x
        y = int(y) if isinstance(y, (int, float)) else y
        
        # Validate coordinates
        if not isinstance(x, int) or not isinstance(y, int):
            print(f"⚠️ Invalid coordinates: x={x} (type: {type(x)}), y={y} (type: {type(y)})")
            return False
        
        # Validate block type
        if not isinstance(block_type, str):
            print(f"⚠️ Invalid block type: {block_type} (type: {type(block_type)})")
            return False
        
        # Set the block
        world_data[f"{x},{y}"] = block_type
        return True
        
    except Exception as e:
        print(f"❌ Error setting block at ({x}, {y}): {e}")
        return False



# --- Bedrock helper ---
def bedrock_level_at(x):
    """Return the y of the first bedrock block in column x, or None if not present."""
    # Scan a reasonable vertical range; bedrock is generated at Y=127
    for y in range(120, 128):  # Check around Y=127 for bedrock
        if get_block(x, y) == "bedrock":
            return y
    return None

# Helper for non-solid blocks
def is_non_solid_block(block):
    # ENHANCED COLLISION: Non-colliding blocks the player can pass through
    # Only allow movement through truly passable blocks
    passable_blocks = {None, "air", "carrot", "ladder"}
    return block in passable_blocks

def is_door_open(x, y):
    """Check if a door at position (x, y) is open"""
    return door_states.get((x, y), False)

def can_pass_through_block(block_type, x, y):
    """Check if player can pass through a block, considering door states"""
    if block_type == "door":
        return is_door_open(x, y)
    return is_non_solid_block(block_type)

# Terrain helper: which blocks count as real ground for column generation
TERRAIN_BLOCKS = {"grass","dirt","stone","bedrock","coal","iron","gold","diamond"}


def column_has_terrain(x: int) -> bool:
    """Return True if column x already has at least one terrain block.
    This prevents leaves/carrots/chests placed in a not-yet-generated column
    from fooling the generator (which used to create vertical holes).
    
    Also prevents regenerating columns where blocks were intentionally removed."""
    # CRITICAL FIX: Once a column is generated, it should NEVER be regenerated
    # This prevents broken blocks from being replaced by terrain regeneration
    if x in generated_terrain_columns:
        print(f"✅ Column {x} already generated - will NOT regenerate")
        return True
    
    # Only check for terrain blocks if the column hasn't been generated before
    for y in range(0, 128):
        if get_block(x, y) in TERRAIN_BLOCKS:
            print(f"🌍 Column {x} has terrain at Y={y} - will NOT regenerate")
            return True
    
    print(f"🔄 Column {x} has no terrain - WILL regenerate")
    return False

# --- Ground/placement helpers to avoid spawning inside trees ---

def ground_y_of_column(x: int):
    """Return the y of the grass surface for column x, or None if not found."""
    for y in range(0, 128):  # Check in reasonable height range
        if get_block(x, y) == "grass":
            return y
    return None

# --- Villager Dialogue System ---
villager_dialogues = [
    "Hello there, traveler! How are you today?",
    "Welcome to our village! Feel free to explore.",
    "The weather is lovely today, isn't it?",
    "Have you found any interesting resources lately?",
    "We're so glad you came to visit!",
    "The crops are growing well this season.",
    "Did you know there are diamonds deep underground?",
    "We love having visitors in our village!",
    "The stars are beautiful at night.",
    "Have you tried sleeping in a bed? It's very restful!",
    "We've been building new houses for everyone.",
    "The village is growing bigger every day!",
    "We hope you're enjoying your stay!",
    "There's always something new to discover.",
    "We're grateful for peaceful times like these.",
    "The children love playing in the village square.",
    "We share everything we have with visitors.",
    "The village has a rich history of friendship.",
    "We believe in helping each other out.",
    "Welcome to our little corner of the world!",
    "Have you seen our beautiful village gardens?",
    "The villagers are very friendly here!",
    "We love sharing stories with travelers.",
    "The village is a safe place for everyone.",
    "We hope you find many treasures on your journey!",
    "The village has been here for generations.",
    "We welcome all peaceful visitors.",
    "The village square is the heart of our community.",
    "We're proud of our peaceful village.",
    "The villagers work together to help each other.",
    "We believe in kindness and friendship.",
    "The village is a place of harmony and joy."
]

def get_random_villager_dialogue(villager=None):
    """EXTREME ENGINEERING: Get personality-based villager dialogue with context awareness"""
    if villager and isinstance(villager, dict):
        personality = villager.get("personality", "friendly")
        name = villager.get("name", "Villager")
        mood = villager.get("mood", "neutral")
        
        # EXTREME ENGINEERING: Personality and mood-based dialogue
        dialogue_pools = {
            "friendly": {
                "happy": [
                    f"Hi there! I'm {name}! 👋",
                    f"Welcome to our village! I'm {name}! 🏘️",
                    f"Nice to meet you! I'm {name}! 😊",
                    f"Hello friend! I'm {name}! 🌟"
                ],
                "neutral": [
                    f"Hey, I'm {name}. How are you? 🤔",
                    f"Hi, {name} here. Nice weather today! ☀️",
                    f"Hello! I'm {name}. Need anything? 🛠️"
                ],
                "slightly_annoyed": [
                    f"*sigh* I'm {name}. What do you want? 😤",
                    f"Ugh, {name} here. Make it quick. ⏰",
                    f"Fine, I'm {name}. What is it? 😒"
                ]
            },
            "grumpy": {
                "happy": [
                    f"*grumbles* I'm {name}. Don't bother me much. 😠",
                    f"Fine, I'm {name}. What do you want? 😤",
                    f"*sigh* {name} here. Make it quick. ⏰"
                ],
                "neutral": [
                    f"*grumpy noise* I'm {name}. Leave me alone. 😒",
                    f"Ugh, {name} here. What now? 😤",
                    f"*annoyed* I'm {name}. This better be important. 😠"
                ],
                "slightly_annoyed": [
                    f"*very grumpy* I'm {name}. GO AWAY! 😡",
                    f"*extremely annoyed* {name} here. I HATE EVERYTHING! 😤",
                    f"*grumpy grumble* I'm {name}. Why are you still here? 😒"
                ]
            },
            "wise": {
                "happy": [
                    f"Greetings, young one. I am {name}. 🧙‍♂️",
                    f"Welcome, traveler. I am {name}, keeper of wisdom. 📚",
                    f"Ah, a new face! I am {name}. What knowledge do you seek? 🔮"
                ],
                "neutral": [
                    f"I am {name}. The path of wisdom is long and winding. 🛤️",
                    f"Greetings. I am {name}. Every day brings new lessons. 📖",
                    f"Hello there. I am {name}. What mysteries shall we explore? 🔍"
                ],
                "slightly_annoyed": [
                    f"I am {name}. Your questions test my patience. 😤",
                    f"*sigh* I am {name}. Must you disturb my meditation? 🧘‍♂️",
                    f"Greetings, I am {name}. Your presence disrupts my studies. 📚"
                ]
            },
            "curious": {
                "happy": [
                    f"Hi! I'm {name}! Tell me everything about your adventures! 🗺️",
                    f"Hello! I'm {name}! What's the most exciting thing you've seen? 🌟",
                    f"Hi there! I'm {name}! Can I come with you on your next journey? 🚀"
                ],
                "neutral": [
                    f"Hey! I'm {name}! What's new in the world? 🌍",
                    f"Hello! I'm {name}! Have you discovered any new places? 🏔️",
                    f"Hi! I'm {name}! What's the most interesting thing you've found? 💎"
                ],
                "slightly_annoyed": [
                    f"*impatient* I'm {name}! Tell me something interesting already! 😤",
                    f"*bouncing* I'm {name}! I need adventure stories NOW! ⚡",
                    f"*restless* I'm {name}! When are we going exploring? 🗺️"
                ]
            },
            "shy": {
                "happy": [
                    f"*whispers* Hi... I'm {name}... 👋",
                    f"*quietly* Hello... I'm {name}... 😊",
                    f"*softly* Hi there... I'm {name}... 🌸"
                ],
                "neutral": [
                    f"*whispers* Hey... I'm {name}... 🤫",
                    f"*quietly* Hello... I'm {name}... 🤔",
                    f"*softly* Hi... I'm {name}... 🌿"
                ],
                "slightly_annoyed": [
                    f"*very quiet* I'm {name}... please don't stare... 😰",
                    f"*whispers* Hi... I'm {name}... can you go away now? 😅",
                    f"*softly* Hello... I'm {name}... I'm not good at talking... 😓"
                ]
            },
            "energetic": {
                "happy": [
                    f"HELLO! I'M {name}! ARE YOU READY FOR ADVENTURE? 🚀",
                    f"HI THERE! I'M {name}! LET'S GO EXPLORING! 🗺️",
                    f"HELLO! I'M {name}! I'M SO EXCITED TO MEET YOU! ⚡"
                ],
                "neutral": [
                    f"HI! I'M {name}! WHAT ARE WE DOING TODAY? 🎯",
                    f"HELLO! I'M {name}! I'M FULL OF ENERGY! ⚡",
                    f"HI THERE! I'M {name}! READY FOR SOME ACTION? 🏃‍♂️"
                ],
                "slightly_annoyed": [
                    f"*bouncing* I'M {name}! WHY ARE YOU SO SLOW? 🐌",
                    f"*jumping* HI! I'M {name}! CAN WE GO FASTER? ⚡",
                    f"*running in place* HELLO! I'M {name}! I NEED TO MOVE! 🏃‍♂️"
                ]
            }
        }
        
        # Get dialogue based on personality and mood
        if personality in dialogue_pools and mood in dialogue_pools[personality]:
            return random.choice(dialogue_pools[personality][mood])
    
    # Fallback to generic dialogue
    return random.choice([
        "Hello there! 👋",
        "Welcome to our village! 🏘️",
        "Nice to meet you! 😊",
        "How are you today? 🤔",
        "Greetings, traveler! 🌟"
    ])

def show_villager_dialogue(dialogue, villager=None):
    """EXTREME ENGINEERING: Display enhanced villager dialogue with personality context"""
    global villager_dialogue_text, villager_dialogue_until
    
    # EXTREME ENGINEERING: Add villager name and personality to dialogue
    if villager and isinstance(villager, dict):
        name = villager.get("name", "Villager")
        personality = villager.get("personality", "friendly")
        mood = villager.get("mood", "neutral")
        
        # Enhanced dialogue display
        enhanced_dialogue = f"{dialogue}"
        villager_dialogue_text = enhanced_dialogue
    else:
        villager_dialogue_text = dialogue
    
    villager_dialogue_until = time.time() + 6  # Show for 6 seconds (longer for enhanced dialogue)

# --- Village and House helpers ---
def build_house(origin_x, ground_y, width=7, height=5):
    """EXTREME ENGINEERING: Build realistic village houses with interiors, entrances, and proper spacing"""
    # Floor - stone foundation
    for dx in range(width):
        set_block(origin_x + dx, ground_y, "stone")
    
    # Walls - use oak planks for main structure, logs for corners
    for dy in range(1, height + 1):
        for dx in range(width):
            x = origin_x + dx
            y = ground_y - dy
            edge = (dx == 0 or dx == width - 1)
            top = (dy == height)
            
            # EXTREME ENGINEERING: Create proper entrance (2 blocks tall, 1 block wide)
            door_x = origin_x + width // 2
            if (x == door_x and (y == ground_y - 1 or y == ground_y - 2)):
                # Leave doorway completely open for player to walk through
                continue
                
            if edge or top:
                # Use logs for corners and top, oak planks for main walls
                if (dx == 0 or dx == width - 1) and (dy == 1 or dy == height):
                    set_block(x, y, "log")  # Corner logs
                else:
                    set_block(x, y, "oak_planks")  # Main walls
            else:
                # Interior air - clear any obstacles
                if get_block(x, y) not in (None, "air"):
                    world_data.pop((x, y), None)
    
    # EXTREME ENGINEERING: Add interior details
    # Interior floor (wooden planks)
    for dx in range(1, width - 1):
        set_block(origin_x + dx, ground_y, "oak_planks")
    
    # Interior walls for room separation
    for dy in range(1, height):
        # Left interior wall (bedroom area)
        if random.random() < 0.7:  # 70% chance
            set_block(origin_x + 1, ground_y - dy, "oak_planks")
        # Right interior wall (living area)
        if random.random() < 0.7:  # 70% chance
            set_block(origin_x + width - 2, ground_y - dy, "oak_planks")
    
    # EXTREME ENGINEERING: Add furniture and decorations
    # Bed (left side of house)
    bed_x = origin_x + 1
    bed_y = ground_y - 1
    set_block(bed_x, bed_y, "bed")
    
    # Chest (right side of house, away from entrance)
    chest_x = origin_x + width - 2
    chest_y = ground_y - 1
    if get_block(chest_x, chest_y) is None:
        set_block(chest_x, chest_y, "chest")
        # Generate natural chest loot for village houses
        chest_system.generate_chest_loot("village")
    
    # EXTREME ENGINEERING: Add windows (small openings in walls)
    window_y = ground_y - 2
    if random.random() < 0.6:  # 60% chance for left window
        set_block(origin_x, window_y, "air")  # Window opening
    if random.random() < 0.6:  # 60% chance for right window
        set_block(origin_x + width - 1, window_y, "air")  # Window opening
    
    # EXTREME ENGINEERING: Add entrance path (stone path leading to door)
    path_x = origin_x + width // 2
    for py in range(ground_y + 1, ground_y + 4):  # Path extends 3 blocks from house
        set_block(path_x, py, "stone")
    
    print(f"🏠 Built realistic village house at ({origin_x}, {ground_y}) with interior and entrance!")
    
    # EXTREME ENGINEERING: Generate farm near the house (2 blocks away)
    farm_x = origin_x + random.choice([-8, 8])  # Left or right of house
    farm_y = ground_y
    generate_village_farm(farm_x, farm_y)

def spawn_villager(x, y):
    """EXTREME ENGINEERING: Create intelligent villagers with personalities, movement, and dialogue"""
    # EXTREME ENGINEERING: Villager personality system
    personalities = ["friendly", "grumpy", "wise", "curious", "shy", "energetic"]
    personality = random.choice(personalities)
    
    # EXTREME ENGINEERING: Villager names based on personality
    name_pools = {
        "friendly": ["Alex", "Sam", "Jordan", "Taylor", "Casey"],
        "grumpy": ["Grumpus", "Cranky", "Sour", "Grouch", "Grumpy"],
        "wise": ["Sage", "Elder", "Wise", "Oracle", "Mentor"],
        "curious": ["Explorer", "Seeker", "Wanderer", "Discoverer", "Adventurer"],
        "shy": ["Whisper", "Quiet", "Silent", "Hush", "Mute"],
        "energetic": ["Bouncy", "Zippy", "Fast", "Quick", "Swift"]
    }
    
    villager_name = random.choice(name_pools.get(personality, ["Villager"]))
    
    entities.append({
        "type": "villager",
        "x": float(x),
        "y": float(y),
        "dir": random.choice([-1, 1]),
        "step": 0,
        "dialogue_cooldown": 0,  # Prevent spam clicking
        "last_dialogue": None,
        "personality": personality,
        "name": villager_name,
        "movement_timer": 0,
        "movement_target": None,
        "home_x": x,  # Remember where they spawned
        "home_y": y,
        "wander_radius": random.randint(3, 8),  # How far they wander from home
        "dialogue_history": [],  # Remember what they've said
        "mood": random.choice(["happy", "neutral", "slightly_annoyed"]),
        "last_interaction": 0
    })
    
    print(f"👤 Spawned {personality} villager '{villager_name}' at ({x}, {y})")

def generate_village_farm(farm_x, farm_y):
    """EXTREME ENGINEERING: Generate realistic village farms with dirt platforms and carrots"""
    # Farm platform (4x4 dirt area)
    farm_size = 4
    for dx in range(farm_size):
        for dy in range(farm_size):
            x = farm_x + dx
            y = farm_y + dy
            # Create dirt platform
            set_block(x, y, "dirt")
    
    # EXTREME ENGINEERING: Plant carrots in the front row (4 carrots)
    for dx in range(farm_size):
        carrot_x = farm_x + dx
        carrot_y = farm_y - 1  # One block above the dirt platform
        set_block(carrot_x, carrot_y, "carrot")
    
    # EXTREME ENGINEERING: Add farm decorations
    # Fence around the farm
    for dx in range(farm_size + 2):  # +2 for fence posts
        fence_x = farm_x + dx - 1
        # Front fence
        set_block(fence_x, farm_y - 2, "log")
        # Back fence
        set_block(fence_x, farm_y + farm_size, "log")
    
    # Side fences
    for dy in range(farm_size + 2):
        fence_y = farm_y + dy - 1
        # Left fence
        set_block(farm_x - 1, fence_y, "log")
        # Right fence
        set_block(farm_x + farm_size, fence_y, "log")
    
    # EXTREME ENGINEERING: Add water source near farm
    water_x = farm_x + random.randint(0, farm_size - 1)
    water_y = farm_y + farm_size + 2
    set_block(water_x, water_y, "water")
    
    print(f"🌾 Generated village farm at ({farm_x}, {farm_y}) with 4 carrots and fencing!")

def spawn_legend_npc():
    """EXTREME ENGINEERING: Spawn the Legend NPC at the boss location"""
    global legend_npc_spawned, legend_npc_position
    
    if legend_npc_spawned:
        return
    
    # Position the Legend NPC at the boss arena
    legend_npc_position = {
        "x": BOSS_SPAWN_DISTANCE,
        "y": 0  # Will be adjusted to ground level
    }
    
    # Add Legend NPC to entities
    entities.append({
        "type": "legend_npc",
        "x": float(legend_npc_position["x"]),
        "y": float(legend_npc_position["y"]),
        "dir": 1,
        "step": 0,
        "dialogue_cooldown": 0,
        "name": "The Legend",
        "personality": "legendary",
        "mood": "mysterious",
        "home_x": legend_npc_position["x"],
        "home_y": legend_npc_position["y"],
        "wander_radius": 0,  # Legend NPC doesn't wander
        "dialogue_history": [],
        "last_interaction": 0
    })
    
    legend_npc_spawned = True
    print(f"🌟 LEGENDARY! Spawned The Legend NPC at ({legend_npc_position['x']}, {legend_npc_position['y']})")

def check_legend_npc_spawn():
    """EXTREME ENGINEERING: Check if player is close enough to spawn the Legend NPC"""
    global legend_npc_spawned
    
    if legend_npc_spawned:
        return
    
    # Check if player is within 1000 blocks of the Legend NPC spawn point
    distance_to_legend = abs(player["x"] - BOSS_SPAWN_DISTANCE)
    if distance_to_legend < 1000:
        spawn_legend_npc()

def generate_boss_arena():
    """EXTREME ENGINEERING: Generate the legendary boss battle arena with red bricks"""
    global boss_arena_center, boss_position
    
    # Arena center at the Legend NPC location
    arena_center_x = BOSS_SPAWN_DISTANCE
    arena_center_y = 0  # Will be adjusted to ground level
    
    boss_arena_center = {"x": arena_center_x, "y": arena_center_y}
    
    # Generate massive red brick arena (100x100 blocks)
    arena_size = BOSS_ARENA_SIZE
    half_size = arena_size // 2
    
    print(f"🏟️ GENERATING LEGENDARY BOSS ARENA at ({arena_center_x}, {arena_center_y})")
    
    # Create arena floor and walls
    for dx in range(-half_size, half_size + 1):
        for dy in range(-half_size, half_size + 1):
            x = arena_center_x + dx
            y = arena_center_y + dy
            
            # Arena floor (red bricks)
            set_block(x, y, "red_brick")
            
            # Arena walls (red bricks) - 10 blocks tall
            for wall_y in range(y + 1, y + 11):
                if dx == -half_size or dx == half_size or dy == -half_size or dy == half_size:
                    set_block(x, wall_y, "red_brick")
    
    # Create arena entrance (opening in the wall)
    entrance_x = arena_center_x
    entrance_y = arena_center_y + half_size
    for y in range(entrance_y, entrance_y + 4):  # 4-block tall entrance
        set_block(entrance_x, y, "air")
    
    # Position boss in center of arena
    boss_position = {
        "x": arena_center_x,
        "y": arena_center_y + 5  # 5 blocks above arena floor
    }
    
    print(f"🏟️ LEGENDARY BOSS ARENA COMPLETE! Boss positioned at ({boss_position['x']}, {boss_position['y']})")

def start_boss_fight():
    """EXTREME ENGINEERING: Start the legendary boss battle"""
    global boss_fight_active, boss_health, boss_max_health, boss_phase
    
    if boss_fight_active:
        return
    
    # Check if player has stone sword
    if not check_stone_sword_requirement():
        show_message("⚔️ You need a Stone Sword to fight the boss!", 3000)
        print("❌ Player attempted to fight boss without stone sword")
        return
    
    # Load boss texture if not already loaded
    if not boss_texture_loaded:
        load_boss_texture()
    
    boss_fight_active = True
    boss_health = BOSS_PHASE_1_HP
    boss_max_health = BOSS_PHASE_1_HP
    boss_phase = 1
    
    # Teleport player to boss arena
    player["x"] = boss_arena_center["x"]
    player["y"] = boss_arena_center["y"] + 5
    
    # Generate boss arena if not already generated
    if boss_arena_center["x"] == 0:
        generate_boss_arena()
    
    show_message("🐉 LEGENDARY BOSS FIGHT STARTED! Prepare for battle!", 3000)
    print(f"🐉 LEGENDARY BOSS FIGHT STARTED! Boss HP: {boss_health}/{boss_max_health}")

def update_boss():
    """EXTREME ENGINEERING: Update boss AI, attacks, and phase transitions"""
    global boss_fight_active, boss_health, boss_phase, boss_max_health, boss_attack_cooldown, boss_attack_timer, boss_attack_type
    
    if not boss_fight_active:
        return
    
    # Boss attack cooldown
    if boss_attack_cooldown > 0:
        boss_attack_cooldown -= 1
    
    # Boss attack timer
    if boss_attack_timer > 0:
        boss_attack_timer -= 1
        if boss_attack_timer == 0:
            # Execute attack
            execute_boss_attack()
    
    # Check for phase transition
    if boss_phase == 1 and boss_health <= 0:
        # Transition to phase 2 (orange form)
        boss_phase = 2
        boss_health = BOSS_PHASE_2_HP
        boss_max_health = BOSS_PHASE_2_HP
        boss_attack_type = "phase2"
        show_message("🐉 BOSS PHASE 2 ACTIVATED! Orange form unleashed!", 3000)
        print(f"🐉 BOSS PHASE 2! HP: {boss_health}/{boss_max_health}")
        
        # Reset attack cooldown for phase 2
        boss_attack_cooldown = 120  # 2 seconds
    
    elif boss_phase == 2 and boss_health <= 0:
        # Boss defeated!
        boss_fight_active = False
        show_message("🏆 LEGENDARY BOSS DEFEATED! You are victorious!", 5000)
        print("🏆 LEGENDARY BOSS DEFEATED!")
        
        # Give player rewards
        give_boss_rewards()
        return
    
    # Boss attack patterns
    if boss_attack_cooldown <= 0:
        # Choose attack type based on phase
        if boss_phase == 1:
            attack_types = ["fire", "phase1"]
        else:  # Phase 2
            attack_types = ["fire", "phase2"]
        
        boss_attack_type = random.choice(attack_types)
        boss_attack_cooldown = 180  # 3 seconds between attacks
        boss_attack_timer = 60  # 1 second attack windup

def execute_boss_attack():
    """EXTREME ENGINEERING: Execute boss attacks with different damage types"""
    global boss_fight_active, boss_attack_type
    
    if not boss_fight_active:
        return
    
    # Calculate damage based on attack type
    damage_hearts = BOSS_ATTACK_DAMAGE.get(boss_attack_type, 2)
    damage_hp = damage_hearts * 2  # Convert hearts to HP
    
    # Apply damage to player
    player["health"] = max(0, player["health"] - damage_hp)
    
    # Show attack message
    attack_messages = {
        "fire": f"🔥 BOSS FIRE ATTACK! You took {damage_hearts} hearts of damage!",
        "phase1": f"⚔️ BOSS PHASE 1 ATTACK! You took {damage_hearts} hearts of damage!",
        "phase2": f"💥 BOSS PHASE 2 ATTACK! You took {damage_hearts} hearts of damage!"
    }
    
    show_message(attack_messages.get(boss_attack_type, "Boss attack!"), 2000)
    print(f"🐉 Boss {boss_attack_type} attack dealt {damage_hearts} hearts ({damage_hp} HP) damage!")
    
    # Check if player died
    if player["health"] <= 0:
        show_message("💀 You were defeated by the boss! Game over!", 3000)
        print("💀 Player defeated by boss!")

def damage_boss(damage_amount):
    """Damage the boss - only stone sword can damage the boss"""
    global boss_health
    
    if not boss_fight_active:
        return False
    
    # Check if player has stone sword
    if not check_stone_sword_requirement():
        show_message("⚔️ Only the Stone Sword can damage the boss!", 2000)
        print("❌ Player attempted to damage boss without stone sword")
        return False
    
    # Apply damage
    boss_health = max(0, boss_health - damage_amount)
    print(f"⚔️ Boss took {damage_amount} damage! HP: {boss_health}/{boss_max_health}")
    
    # Check if boss is defeated
    if boss_health <= 0:
        print("🏆 Boss defeated!")
        return True
    
    return False

def give_boss_rewards():
    """EXTREME ENGINEERING: Give player rewards for defeating the boss"""
    # Add legendary items to inventory
    legendary_rewards = [
        {"type": "legendary_sword", "count": 1},
        {"type": "boss_trophy", "count": 1},
        {"type": "diamond", "count": 10},
        {"type": "gold", "count": 20}
    ]
    
    for reward in legendary_rewards:
        player["inventory"].append(reward)
    
    show_message("🏆 LEGENDARY REWARDS: Legendary Sword, Boss Trophy, Diamonds, Gold!", 4000)
    print("🏆 Boss rewards given to player!")

def load_boss_texture():
    """Load boss texture from assets/mobs/boss.png"""
    global boss_texture, boss_texture_loaded
    
    try:
        boss_path = os.path.join("../../../..", "mobs", "boss.png")
        if os.path.exists(boss_path):
            boss_texture = pygame.image.load(boss_path).convert_alpha()
            boss_texture = pygame.transform.scale(boss_texture, (64, 64))  # Scale to 64x64
            boss_texture_loaded = True
            print(f"🎭 Boss texture loaded successfully from {boss_path}")
            return True
        else:
            print(f"⚠️ Boss texture not found at {boss_path}")
            print("   Place your boss texture at assets/mobs/boss.png")
            boss_texture_loaded = False
            return False
    except Exception as e:
        print(f"❌ Error loading boss texture: {e}")
        boss_texture_loaded = False
        return False

def check_stone_sword_requirement():
    """Check if player has stone sword to fight the boss"""
    for item in player["inventory"]:
        if item and item.get("type") == "stone_sword":
            return True
    return False

def check_underground_fortress_trigger():
    """Check if player has reached the underground fortress area"""
    global boss_fight_active
    
    # Check if player is in the underground fortress area (around x=200)
    if (abs(player["x"] - BOSS_SPAWN_DISTANCE) < 20 and 
        player["y"] < 0 and  # Underground
        not boss_fight_active):
        
        # Check if player has broken through bedrock (deep underground)
        if player["y"] < -50:  # Very deep underground
            show_message("🏰⚒️ You've discovered the underground fortress! The final boss awaits!", 4000)
            print("🏰 Player discovered underground fortress!")
            
            # Auto-start boss fight if player has stone sword
            if check_stone_sword_requirement():
                show_message("⚔️ You have the Stone Sword! The boss fight begins!", 3000)
                start_boss_fight()
            else:
                show_message("⚔️ You need a Stone Sword to challenge the boss!", 3000)
                print("❌ Player needs stone sword for boss fight")
            
            return True
    
    return False

# =============================================================================
# EXTREME ENGINEERING: PROFESSIONAL MULTIPLAYER SYSTEM
# =============================================================================

class MultiplayerServer:
    """EXTREME ENGINEERING: Professional multiplayer server with full game synchronization"""
    
    def __init__(self, world_name: str, max_players: int = 20):
        self.world_name = world_name
        self.max_players = max_players
        self.players = {}  # {player_id: player_data}
        self.world_data = {}
        self.entities = []
        self.running = False
        self.socket = None
        self.server_thread = None
        self.tick_count = 0
        self.last_sync = 0
        
        # Server info for discovery
        self.server_info = {
            "name": f"{world_name} Server",
            "world": world_name,
            "players": 0,
            "max_players": max_players,
            "version": "1.0.0",
            "description": f"Join {world_name} for epic multiplayer adventures!"
        }
    
    def start(self, port: int = MULTIPLAYER_PORT):
        """Start the multiplayer server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', port))
            self.socket.listen(self.max_players)
            self.socket.setblocking(False)
            
            self.running = True
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            print(f"🌐 MULTIPLAYER SERVER STARTED on port {port}")
            print(f"🌐 Server: {self.server_info['name']}")
            print(f"🌐 World: {self.world_name}")
            print(f"🌐 Max Players: {self.max_players}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start multiplayer server: {e}")
            return False
    
    def stop(self):
        """Stop the multiplayer server"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.server_thread:
            self.server_thread.join(timeout=1)
        print("🌐 Multiplayer server stopped")
    
    def _server_loop(self):
        """Main server loop - handles connections and game synchronization"""
        while self.running:
            try:
                # Accept new connections
                try:
                    client_socket, address = self.socket.accept()
                    self._handle_new_connection(client_socket, address)
                except BlockingIOError:
                    pass  # No new connections
                
                # Handle existing connections
                self._handle_existing_connections()
                
                # Game synchronization
                if self.tick_count % MULTIPLAYER_SYNC_RATE == 0:
                    self._sync_game_state()
                
                self.tick_count += 1
                time.sleep(1.0 / MULTIPLAYER_TPS)
                
            except Exception as e:
                print(f"❌ Server loop error: {e}")
                time.sleep(1)
    
    def _handle_new_connection(self, client_socket, address):
        """Handle new player connection"""
        try:
            # Generate unique player ID
            player_id = str(uuid.uuid4())
            
            # Create player data
            player_data = {
                "id": player_id,
                "username": f"Player_{len(self.players) + 1}",
                "x": random.randint(-100, 100),
                "y": 10,
                "health": 10,
                "hunger": 10,
                "inventory": [],
                "connected": True,
                "last_seen": time.time()
            }
            
            self.players[player_id] = player_data
            client_socket.send(pickle.dumps({
                "type": "welcome",
                "player_id": player_id,
                "world_data": self.world_data,
                "entities": self.entities,
                "players": self.players
            }))
            
            print(f"🌐 New player connected: {player_data['username']} ({address})")
            
        except Exception as e:
            print(f"❌ Failed to handle new connection: {e}")
            client_socket.close()
    
    def _handle_existing_connections(self):
        """Handle existing player connections and data updates"""
        # This would handle ongoing communication with connected players
        # For now, we'll implement basic functionality
        pass
    
    def _sync_game_state(self):
        """Synchronize game state to all connected players"""
        if not self.players:
            return
        
        sync_data = {
            "type": "sync",
            "world_data": self.world_data,
            "entities": self.entities,
            "players": self.players,
            "tick": self.tick_count
        }
        
        # Send sync data to all players
        # In a full implementation, this would send to each connected client
        print(f"🌐 Game state synchronized (tick {self.tick_count})")

class MultiplayerClient:
    """EXTREME ENGINEERING: Professional multiplayer client for connecting to servers"""
    
    def __init__(self):
        self.connected = False
        self.server_address = None
        self.socket = None
        self.player_id = None
        self.server_data = None
        
    def connect(self, server_address: str, port: int = MULTIPLAYER_PORT):
        """Connect to a multiplayer server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_address, port))
            self.server_address = server_address
            self.connected = True
            
            # Start client thread
            self.client_thread = threading.Thread(target=self._client_loop, daemon=True)
            self.client_thread.start()
            
            print(f"🌐 Connected to server: {server_address}:{port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            self.socket.close()
        print("🌐 Disconnected from server")
    
    def _client_loop(self):
        """Client loop for receiving server updates"""
        while self.connected:
            try:
                # Receive data from server
                data = self.socket.recv(4096)
                if data:
                    self._handle_server_data(pickle.loads(data))
                else:
                    break
                    
            except Exception as e:
                print(f"❌ Client loop error: {e}")
                break
        
        self.connected = False
    
    def _handle_server_data(self, data):
        """Handle data received from server"""
        data_type = data.get("type")
        
        if data_type == "welcome":
            self.player_id = data.get("player_id")
            self.server_data = data
            print(f"🌐 Welcome to server! Player ID: {self.player_id}")
            
        elif data_type == "sync":
            # Update local game state with server data
            self.server_data = data
            print(f"🌐 Received game state sync (tick {data.get('tick')})")

def start_multiplayer_server(world_name: str):
    """EXTREME ENGINEERING: Start a multiplayer server for the specified world"""
    global local_server_info, is_host
    
    if is_host:
        print("🌐 Server already running")
        return False
    
    # Create and start server
    server = MultiplayerServer(world_name)
    if server.start():
        local_server_info = server
        is_host = True
        multiplayer_mode = True
        
        # Register server for discovery
        register_server_for_discovery(server.server_info)
        
        print(f"🌐 Multiplayer server started for world: {world_name}")
        return True
    else:
        print("❌ Failed to start multiplayer server")
        return False

def stop_multiplayer_server():
    """EXTREME ENGINEERING: Stop the current multiplayer server"""
    global local_server_info, is_host
    
    if local_server_info:
        local_server_info.stop()
        local_server_info = None
        is_host = False
        multiplayer_mode = False
        print("🌐 Multiplayer server stopped")

def discover_servers():
    """EXTREME ENGINEERING: Discover available multiplayer servers"""
    global server_list
    
    # In a real implementation, this would use UDP broadcast or a central server list
    # For now, we'll simulate server discovery
    discovered_servers = [
        {
            "name": "Epic Adventure Server",
            "world": "Epic World",
            "players": 3,
            "max_players": 20,
            "version": "1.0.0",
            "description": "Join us for epic adventures!",
            "address": "127.0.0.1"
        },
        {
            "name": "Creative Building Server", 
            "world": "Creative World",
            "players": 8,
            "max_players": 20,
            "version": "1.0.0",
            "description": "Build amazing creations together!",
            "address": "127.0.0.2"
        }
    ]
    
    server_list = discovered_servers
    print(f"🌐 Discovered {len(server_list)} servers")
    return server_list

def register_server_for_discovery(server_info: dict):
    """EXTREME ENGINEERING: Register server for discovery by other players"""
    # In a real implementation, this would register with a central server list
    print(f"🌐 Server registered for discovery: {server_info['name']}")

def join_multiplayer_server(server_info: dict):
    """EXTREME ENGINEERING: Join a multiplayer server"""
    global is_client, multiplayer_mode
    
    if is_client:
        print("🌐 Already connected to a server")
        return False
    
    # Create and start client
    client = MultiplayerClient()
    if client.connect(server_info["address"]):
        is_client = True
        multiplayer_mode = True
        print(f"🌐 Joined server: {server_info['name']}")
        return True
    else:
        print("❌ Failed to join server")
        return False

def add_chat_message(username: str, message: str):
    """EXTREME ENGINEERING: Add a chat message to the multiplayer chat"""
    global chat_messages
    
    chat_messages.append({
        "username": username,
        "message": message,
        "timestamp": time.time()
    })
    
    # Keep only last 50 messages
    if len(chat_messages) > 50:
        chat_messages = chat_messages[-50:]
    
    print(f"💬 {username}: {message}")

def send_chat_message(message: str):
    """EXTREME ENGINEERING: Send a chat message to the multiplayer server"""
    if not multiplayer_mode:
        return
    
    # Add local message
    add_chat_message("You", message)
    
    # In a full implementation, this would send to the server
    if is_host and local_server_info:
        # Broadcast to all connected players
        print(f"🌐 Broadcasting chat message: {message}")
    elif is_client:
        # Send to server
        print(f"🌐 Sending chat message to server: {message}")

def draw_multiplayer_chat():
    """EXTREME ENGINEERING: Draw the multiplayer chat interface"""
    if not multiplayer_mode or not chat_visible:
        return
    
    # Chat background
    chat_bg = pygame.Surface((400, 300))
    chat_bg.set_alpha(200)
    chat_bg.fill((0, 0, 0))
    screen.blit(chat_bg, (10, SCREEN_HEIGHT - 320))
    
    # Chat title
    chat_title = font.render("💬 Multiplayer Chat", True, (255, 255, 255))
    screen.blit(chat_title, (20, SCREEN_HEIGHT - 310))
    
    # Chat messages
    y_offset = SCREEN_HEIGHT - 280
    for i, msg in enumerate(chat_messages[-10:]):  # Show last 10 messages
        if time.time() - msg["timestamp"] < 60:  # Only show messages from last minute
            username_color = (0, 255, 0) if msg["username"] == "You" else (255, 255, 255)
            username_text = small_font.render(f"{msg['username']}:", True, username_color)
            screen.blit(username_text, (20, y_offset + i * 20))
            
            message_text = small_font.render(msg["message"], True, (200, 200, 200))
            screen.blit(message_text, (20 + username_text.get_width() + 5, y_offset + i * 20))
    
    # Chat input
    if chat_input_active:
        input_bg = pygame.Surface((380, 30))
        input_bg.fill((50, 50, 50))
        screen.blit(input_bg, (20, SCREEN_HEIGHT - 40))
        
        input_text = small_font.render(chat_input_text + "|", True, (255, 255, 255))
        screen.blit(input_text, (25, SCREEN_HEIGHT - 35))
    
    # Chat instructions
    if not chat_input_active:
        instructions = small_font.render("Press T to chat", True, (150, 150, 150))
        screen.blit(instructions, (20, SCREEN_HEIGHT - 40))

def handle_chat_input(event):
    """EXTREME ENGINEERING: Handle chat input events"""
    global chat_input_active, chat_input_text, chat_input_cursor, chat_visible
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_t and not chat_input_active:
            # Open chat input
            chat_input_active = True
            chat_input_text = ""
            chat_input_cursor = 0
            chat_visible = True
            print("💬 Chat input activated")
            
        elif chat_input_active:
            if event.key == pygame.K_RETURN:
                # Send message
                if chat_input_text.strip():
                    send_chat_message(chat_input_text.strip())
                chat_input_active = False
                chat_input_text = ""
                print("💬 Chat message sent")
                
            elif event.key == pygame.K_ESCAPE:
                # Cancel chat
                chat_input_active = False
                chat_input_text = ""
                print("💬 Chat input cancelled")
                
            elif event.key == pygame.K_BACKSPACE:
                # Backspace
                if chat_input_cursor > 0:
                    chat_input_text = chat_input_text[:chat_input_cursor-1] + chat_input_text[chat_input_cursor:]
                    chat_input_cursor -= 1
                    
            elif event.unicode.isprintable():
                # Add character
                chat_input_text = chat_input_text[:chat_input_cursor] + event.unicode + chat_input_text[chat_input_cursor:]
                chat_input_cursor += 1

def damage_boss(damage):
    """EXTREME ENGINEERING: Damage the boss and check for phase transitions"""
    global boss_fight_active, boss_health, boss_max_health
    
    if not boss_fight_active:
        return
    
    boss_health = max(0, boss_health - damage)
    print(f"🐉 Boss took {damage} damage! HP: {boss_health}/{boss_max_health}")
    
    # Show damage message
    if boss_health > 0:
        show_message(f"⚔️ Boss HP: {boss_health}/{boss_max_health}", 1000)
    else:
        if boss_phase == 1:
            show_message("🐉 BOSS PHASE 1 DEFEATED! Phase 2 incoming!", 2000)
        else:
            show_message("🏆 FINAL BOSS PHASE DEFEATED! Victory!", 2000)

def maybe_generate_village_for_chunk(chunk_id, base_x):
    """15% chance to create a small village (1-2 houses) in this 50-wide chunk.
    Allow spawning even when a world is loaded (we now route through set_block).
    """
    
    # Don't generate if chunk already exists
    if chunk_id in generated_village_chunks:
        return
        
    rng = random.Random(f"village-{chunk_id}")
    if rng.random() < 0.25:  # Increased from 18% to 25%
        # choose number of houses and spacing
        house_count = rng.randint(1, 2)
        spacing = rng.randint(10, 16)
        start_x = base_x + rng.randint(5, 15)
        last_house_ground_y = None
        for i in range(house_count):
            hx = start_x + i * spacing
            gy = ground_y_of_column(hx)
            if gy is None:
                # fallback to sine terrain estimate - y=0 is surface now
                gy = 0 + int(2 * math.sin(hx * 0.2))
                # ensure terrain exists under house
                set_block(hx, gy, "grass")
                for y in range(gy + 1, gy + 7):
                    set_block(hx, y, "dirt" if y < gy + 4 else "stone")
                set_block(hx, gy + 7, "bedrock")
            
            # Place village houses ON the ground (not floating)
            village_y = gy  # At ground level
            
            # Ensure terrain exists under the house foundation
            for dx in range(7):  # House width
                # Don't create new terrain - use existing ground
                # Just ensure the foundation blocks are solid
                if get_block(hx + dx, gy) is None:
                    set_block(hx + dx, gy, "grass")  # Surface if missing
                if get_block(hx + dx, gy + 1) is None:
                    set_block(hx + dx, gy + 1, "dirt")  # Dirt layer if missing
            
            # Fill any holes under the house foundation with clean layering
            house_width = 7  # Same width as used in build_house
            for dx in range(house_width):
                # Ensure clean layer hierarchy under houses - stone layer is now 8 blocks deep
                for y in range(gy + 1, 13):
                    if get_block(hx + dx, y) is None:
                        if y < gy + 4:
                            set_block(hx + dx, y, "dirt")
                        elif y < 13:
                            set_block(hx + dx, y, "stone")
                        else:
                            set_block(hx + dx, y, "bedrock")
            # build the house aligned to elevated village position
            build_house(hx, village_y, width=7, height=5)
            # spawn 2-3 villagers near the doorway on the ground
            spawn_villager(hx + 3, village_y + 1)
            spawn_villager(hx + 2, village_y + 1)
            if rng.random() < 0.6:  # 60% chance for third villager
                spawn_villager(hx + 4, village_y + 1)
        generated_village_chunks.add(chunk_id)
        
        # Check for first village discovery achievement
        check_achievement("first_village", 50, "Discovered first village!")

def build_fortress(origin_x, ground_y, width=15, height=12):
    """Build a large fortress with multiple levels, ladders, and enemies using red brick"""
    # Build fortress ABOVE ground level, not underground
    fortress_base_y = ground_y - height  # Start building above ground
    
    # Foundation - stone base at ground level
    for dx in range(width):
        set_block(origin_x + dx, ground_y, "stone")
    
    # Main walls - red brick exterior, building UP from ground
    for dy in range(1, height + 1):
        for dx in range(width):
            x = origin_x + dx
            y = ground_y - dy  # Build upward from ground
            if dx == 0 or dx == width - 1 or dy == height:  # Exterior walls
                set_block(x, y, "red_brick")
            else:
                # Interior air
                if get_block(x, y) not in (None, "air"):
                    world_data.pop((x, y), None)
    
    # Add multiple floors with ladders (building UP from ground)
    floor_levels = [ground_y - 3, ground_y - 6, ground_y - 9]  # Floors above ground
    for floor_y in floor_levels:
        # Floor platform
        for dx in range(2, width - 2):
            set_block(origin_x + dx, floor_y, "stone")
        
        # Ladder to next floor (going UP)
        ladder_x = origin_x + width // 2
        set_block(ladder_x, floor_y + 1, "ladder")  # Ladder going up
        set_block(ladder_x, floor_y + 2, "ladder")  # Ladder going up
    
    # Add chests on each floor
    for i, floor_y in enumerate(floor_levels):
        chest_x = origin_x + 2 + (i * 3) % (width - 4)
        set_block(chest_x, floor_y + 1, "chest")  # Chest above floor
        # Generate special fortress loot including iron armor
        generate_fortress_chest_loot((chest_x, floor_y + 1), i)
    
    # Add some enemies inside the fortress (above ground)
    for i in range(3):
        enemy_x = origin_x + random.randint(2, width - 3)
        enemy_y = ground_y - random.randint(2, height - 2)  # Enemies above ground
        if get_block(enemy_x, enemy_y) == "air":
            entities.append({
                "type": "zombie",
                "x": float(enemy_x),
                "y": float(enemy_y),
                "hp": 10,
                "dir": random.choice([-1, 1])
            })
    
    print(f"🏰 Red brick fortress built above ground at ({origin_x}, {ground_y}) with {len(floor_levels)} floors!")

def generate_fortress_chest_loot(chest_pos, floor_level):
    """EXTREME ENGINEERING: Generate epic fortress loot with guaranteed armor sets and rare materials"""
    # Create a new chest inventory for this position
    chest_inventory = []
    
    # EXTREME ENGINEERING: Enhanced loot pools with multiple armor types
    if floor_level == 0:  # Ground floor - basic loot with leather armor
        loot_pool = ["iron", "coal", "stone", "sword", "pickaxe", "leather_helmet", "leather_chestplate"]
        armor_pool = ["leather_helmet", "leather_chestplate", "leather_leggings", "leather_boots"]
        num_items = random.randint(3, 5)
        armor_chance = 0.6  # 60% chance for armor
    elif floor_level == 1:  # Middle floor - iron armor and better materials
        loot_pool = ["iron", "gold", "diamond", "sword", "pickaxe", "iron_helmet", "iron_chestplate", "chainmail_helmet"]
        armor_pool = ["iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots", "chainmail_helmet", "chainmail_chestplate"]
        num_items = random.randint(4, 7)
        armor_chance = 0.8  # 80% chance for armor
    else:  # Top floor - LEGENDARY loot with diamond/gold armor
        loot_pool = ["iron", "gold", "diamond", "sword", "pickaxe", "diamond_helmet", "diamond_chestplate", "gold_helmet", "gold_chestplate"]
        armor_pool = ["diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots", 
                     "gold_helmet", "gold_chestplate", "gold_leggings", "gold_boots",
                     "iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots"]
        num_items = random.randint(5, 8)
        armor_chance = 0.95  # 95% chance for armor
    
    # Generate base loot
    for _ in range(num_items):
        item_type = random.choice(loot_pool)
        count = 1
        if item_type in ["iron", "coal", "stone"]:
            count = random.randint(2, 5)  # More materials
        elif item_type in ["gold", "diamond"]:
            count = random.randint(1, 3)  # Rare materials
        
        chest_inventory.append({
            "type": item_type,
            "count": count
        })
    
    # EXTREME ENGINEERING: Guaranteed armor drops with set bonuses
    if random.random() < armor_chance:
        # Try to create armor sets (multiple pieces of same type)
        armor_types = ["leather", "iron", "chainmail", "gold", "diamond"]
        
        if floor_level >= 2:  # Top floor - chance for full armor set
            if random.random() < 0.4:  # 40% chance for full set
                armor_type = random.choice(["iron", "diamond", "gold"])
                full_set = [f"{armor_type}_helmet", f"{armor_type}_chestplate", 
                           f"{armor_type}_leggings", f"{armor_type}_boots"]
                
                for armor_piece in full_set:
                    chest_inventory.append({
                        "type": armor_piece,
                        "count": 1
                    })
                print(f"🏆 LEGENDARY! Full {armor_type} armor set found in fortress!")
            else:
                # Add 2-3 random armor pieces
                for _ in range(random.randint(2, 3)):
                    armor_piece = random.choice(armor_pool)
                    # Avoid duplicates
                    if armor_piece not in [item["type"] for item in chest_inventory]:
                        chest_inventory.append({
                            "type": armor_piece,
                            "count": 1
                        })
        else:
            # Lower floors - 1-2 armor pieces
            for _ in range(random.randint(1, 2)):
                armor_piece = random.choice(armor_pool)
                if armor_piece not in [item["type"] for item in chest_inventory]:
                    chest_inventory.append({
                        "type": armor_piece,
                        "count": 1
                    })
    
    # EXTREME ENGINEERING: Special fortress-exclusive items
    if floor_level >= 2 and random.random() < 0.3:  # 30% chance for special items
        special_items = ["enchanted_sword", "fortress_key", "ancient_scroll"]
        if random.choice(special_items) == "enchanted_sword":
            chest_inventory.append({
                "type": "sword",  # Enhanced sword (we'll upgrade this later)
                "count": 1,
                "enchanted": True  # Special property
            })
    
    # Store the chest inventory
    chest_system.chest_inventories[chest_pos] = chest_inventory
    armor_count = len([item for item in chest_inventory if any(armor in item["type"] for armor in ["helmet", "chestplate", "leggings", "boots"])])
    print(f"🏰 FORTRESS LOOT: {len(chest_inventory)} items, {armor_count} armor pieces at floor {floor_level}!")

def maybe_generate_fortress_for_chunk(chunk_id, base_x):
    """12% chance to create a fortress in this chunk. Allowed on saved worlds."""
    
    # Don't generate if chunk already exists
    if chunk_id in generated_village_chunks:
        return
    rng = random.Random(f"fortress-{chunk_id}")
    if rng.random() < 0.18:  # Increased from 10% to 18%
        fortress_x = base_x + rng.randint(10, 40)
        fortress_y = ground_y_of_column(fortress_x)
        if fortress_y is None:
            fortress_y = 0 + int(2 * math.sin(fortress_x * 0.2))
            set_block(fortress_x, fortress_y, "grass")
        
        build_fortress(fortress_x, fortress_y)
        generated_village_chunks.add(chunk_id)  # Mark as generated


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

def draw_button(text, x, y, w, h, hover=False):
    rect = pygame.Rect(x, y, w, h)
    
    # Hover effect - button lights up when hovered
    if hover:
        # Bright hover color with glow effect
        base_color = (150, 150, 150)  # Lighter base
        border_color = (255, 255, 100)  # Golden border
        text_color = (255, 255, 255)  # White text
    else:
        # Normal button colors
        base_color = (100, 100, 100)  # Normal base
        border_color = (255, 255, 255)  # White border
        text_color = (255, 255, 255)  # White text
    
    # Draw button with hover effect
    pygame.draw.rect(screen, base_color, rect)
    pygame.draw.rect(screen, border_color, rect, 2)
    
    # Add subtle glow effect for hover
    if hover:
        # Draw a slightly larger, semi-transparent glow behind the button
        glow_rect = pygame.Rect(x-2, y-2, w+4, h+4)
        glow_surface = pygame.Surface((w+4, h+4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (255, 255, 100, 50), glow_surface.get_rect())  # Semi-transparent glow
        screen.blit(glow_surface, glow_rect)
        # Redraw the button on top
        pygame.draw.rect(screen, base_color, rect)
        pygame.draw.rect(screen, border_color, rect, 2)
    
    # Render text
    label = font.render(text, True, text_color)
    screen.blit(label, (x + 10, y + 10))
    return rect

def draw_controls():
    global back_btn
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw modern controls screen
    button_states = modern_ui.draw_controls_screen(mouse_pos)
    
    # Store button references for click handling
    back_btn = button_states.get("back")

# --- About Screen ---
def draw_about():
    global back_btn
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw modern about screen
    button_states = modern_ui.draw_about_screen(mouse_pos)
    
    # Store button references for click handling
    back_btn = button_states.get("back")

def draw_options():
    """Options page: toggle fullscreen, FPS limiter, or go back to title."""
    global back_btn, fullscreen_btn, fps_btn
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw modern options screen
    button_states = modern_ui.draw_options_screen(mouse_pos, FULLSCREEN, fps_limit)
    
    # Store button references for click handling
    fullscreen_btn = button_states.get("fullscreen")
    fps_btn = button_states.get("fps")
    back_btn = button_states.get("back")

# Name tag function removed - no more floating name above player

def draw_fps_display():
    """Display actual FPS counter and FPS limit info"""
    global fps_counter, last_fps_time
    
    if not show_fps:
        return
    
    # Calculate actual FPS based on frame time
    current_time = time.time()
    frame_time = current_time - last_fps_time
    
    if frame_time > 0:
        # Calculate FPS from frame time (more accurate)
        current_fps = 1.0 / frame_time
        # Smooth the FPS display (average with previous value)
        fps_counter = int(fps_counter * 0.7 + current_fps * 0.3)
    
    last_fps_time = current_time
    
    # Draw FPS info with timing details
    fps_text = font.render(f"FPS: {fps_counter}", True, (255, 255, 0))
    limit_text = font.render(f"Target: 60 FPS (Locked)", True, (255, 255, 0))
    timing_text = font.render(f"Frame Time: {frame_time*1000:.1f}ms", True, (255, 255, 0))
    
    # Add movement speed info if in game
    if game_state == GameState.GAME:
        speed_text = font.render(f"Move Speed: {MOVE_SPEED:.3f}", True, (0, 255, 255))
        controls_text = font.render("Controls: WASD or Arrow Keys=Move+Flip, Space=Jump", True, (0, 255, 255))
        screen.blit(speed_text, (10, 130))
        screen.blit(controls_text, (10, 150))
    
    screen.blit(fps_text, (10, 70))
    screen.blit(limit_text, (10, 90))
    screen.blit(timing_text, (10, 110))

# --- Part Three ---
def delete_save_data():
    if os.path.exists(SAVE_DIR):
        shutil.rmtree(SAVE_DIR)
    os.makedirs(SAVE_DIR)

def show_death_screen():
    """EXTREME ENGINEERING: Enhanced death screen with escape options to prevent infinite death loops"""
    global game_state
    
    # Set game state to paused to prevent further game logic
    game_state = GameState.PAUSED
    
    # Enhanced death screen with professional styling
    screen.fill((20, 0, 0))  # Dark red background
    
    # Death title with dramatic styling
    death_text = BIG_FONT.render("💀 YOU DIED", True, (255, 0, 0))
    death_glow = BIG_FONT.render("💀 YOU DIED", True, (100, 0, 0))  # Glow effect
    screen.blit(death_glow, (SCREEN_WIDTH // 2 - death_text.get_width() // 2 + 2, 202))
    screen.blit(death_text, (SCREEN_WIDTH // 2 - death_text.get_width() // 2, 200))
    
    # Subtitle with helpful information
    subtitle_text = font.render("Choose your next action:", True, (200, 200, 200))
    screen.blit(subtitle_text, (SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2, 250))
    
    # Button positioning with proper spacing
    button_width = 200
    button_height = 60
    center_x = SCREEN_WIDTH // 2
    button_y = 320
    button_spacing = 80
    
    # Respawn button (left side)
    respawn_btn = pygame.Rect(center_x - button_width - button_spacing//2, button_y, button_width, button_height)
    pygame.draw.rect(screen, (0, 150, 0), respawn_btn, border_radius=10)  # Green
    pygame.draw.rect(screen, (255, 255, 255), respawn_btn, 3, border_radius=10)
    
    respawn_text = font.render("🔄 Respawn", True, (255, 255, 255))
    respawn_text_x = respawn_btn.x + (button_width - respawn_text.get_width()) // 2
    respawn_text_y = respawn_btn.y + (button_height - respawn_text.get_height()) // 2
    screen.blit(respawn_text, (respawn_text_x, respawn_text_y))
    
    # Back to Title button (right side) - CRITICAL ESCAPE OPTION
    title_btn = pygame.Rect(center_x + button_spacing//2, button_y, button_width, button_height)
    pygame.draw.rect(screen, (150, 0, 0), title_btn, border_radius=10)  # Red
    pygame.draw.rect(screen, (255, 255, 255), title_btn, 3, border_radius=10)
    
    title_text = font.render("🏠 Back to Title", True, (255, 255, 255))
    title_text_x = title_btn.x + (button_width - title_text.get_width()) // 2
    title_text_y = title_btn.y + (button_height - title_text.get_height()) // 2
    screen.blit(title_text, (title_text_x, title_text_y))
    
    # Additional helpful text
    help_text = font.render("💡 Tip: Use 'Back to Title' if you're stuck in a death loop!", True, (150, 150, 150))
    screen.blit(help_text, (SCREEN_WIDTH // 2 - help_text.get_width() // 2, 420))
    
    pygame.display.flip()

    # Event loop for death screen
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if respawn_btn.collidepoint(pygame.mouse.get_pos()):
                    # DEATH PENALTY: Lose coins to make game harder
                    if coins_manager:
                        current_coins = coins_manager.get_coins()
                        if current_coins > 0:
                            # Lose 25% of coins (minimum 1, maximum 50)
                            coins_lost = max(1, min(50, current_coins // 4))
                            coins_manager.spend_coins(coins_lost)
                            print(f"💀 Death penalty: Lost {coins_lost} coins! Remaining: {coins_manager.get_coins()}")
                            show_message(f"💀 Death penalty: Lost {coins_lost} coins!", 3000)
                    
                    # Reset player to spawn position
                    player["inventory"] = []
                    player["health"] = 10
                    player["hunger"] = 10
                    player["x"] = 10
                    # Fix spawn position to surface instead of hardcoded underground
                    fix_player_spawn_position()
                    player["vel_y"] = 0
                    player["on_ground"] = False
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when respawning
                    print("🔄 Player respawned successfully")
                    return  # Exit the death screen function completely
                elif title_btn.collidepoint(pygame.mouse.get_pos()):
                    # CRITICAL: Escape option to return to title screen
                    print("🏠 Player chose to return to title screen from death")
                    game_state = GameState.TITLE
                    update_pause_state()  # Pause time when returning to title
                    return  # Exit the death screen function completely

        clock.tick(30)

def draw_status_bars():
    # Draw player info at the top
    if GLOBAL_USERNAME:
        username_text = font.render(f"Player: {GLOBAL_USERNAME}", True, (255, 255, 100))
        screen.blit(username_text, (10, 10))
    
    # Draw coins display at the top
    coins_display = coins_manager.get_formatted_balance() if coins_manager else "0"
    coins_text = font.render(f"💰 {coins_display}", True, (255, 215, 0))
    screen.blit(coins_text, (10, 35))
    
    # Draw HP and hunger below player info
    hp_text = font.render("HP:", True, (255, 255, 255))
    hunger_text = font.render("Hunger:", True, (255, 255, 255))
    screen.blit(hp_text, (10, 60))
    screen.blit(hunger_text, (10, 90))
    
    # Draw HP and hunger bars
    for i in range(10):
        hp_img = alive_hp if i < player["health"] else dead_hp
        screen.blit(hp_img, (70 + i * 20, 60))
        hunger_color = (255, 165, 0) if i < player["hunger"] else (80, 80, 80)
        pygame.draw.rect(screen, hunger_color, (70 + i * 20, 90, 16, 16))
    
    # Draw stamina bar
    stamina_text = font.render("Stamina:", True, (255, 255, 255))
    screen.blit(stamina_text, (10, 120))
    
    # Draw stamina as colored rectangles
    for i in range(10):
        if i < player["stamina"] / 10:
            stamina_color = (0, 255, 0) if player["stamina"] > 50 else (255, 255, 0) if player["stamina"] > 25 else (255, 0, 0)
        else:
            stamina_color = (80, 80, 80)
        pygame.draw.rect(screen, stamina_color, (70 + i * 20, 120, 16, 16))
    
    # Show regeneration status
    if stamina_regen_timer > 0:
        regen_text = font.render(f"Regen in {stamina_regen_timer//60 + 1}s", True, (150, 150, 150))
        screen.blit(regen_text, (10, 140))
    elif player["stamina"] < player["max_stamina"]:
        regen_text = font.render("Regenerating...", True, (0, 255, 0))
        screen.blit(regen_text, (10, 140))
    
    # Draw current character info
    character_y = 170
    if character_manager:
        current_char_name = character_manager.get_current_character_name()
        character_text = font.render(f"Character: {current_char_name.title()}", True, (255, 255, 255))
        screen.blit(character_text, (10, character_y))


# --- Part Four ---
def draw_held_item(px, py):
    """EXTREME ENGINEERING: Draw the currently held item on the player's hand based on facing direction"""
    # Check if player has a selected item
    if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]:
        item = player["inventory"][player["selected"]]
        if item and isinstance(item, dict) and "type" in item:
            item_type = item["type"]
            # Check if we have a texture for this item
            if item_type in textures:
                # EXTREME ENGINEERING: Position item based on facing direction
                facing_direction = player.get("facing_direction", 1)
                
                if facing_direction == 1:  # Facing right
                    hand_x = px + 20  # Right side of player
                else:  # Facing left
                    hand_x = px - 20  # Left side of player
                
                hand_y = py + 8   # Slightly above center
                
                # Get the item texture and scale it down slightly for the hand
                item_texture = textures[item_type]
                # Scale down to 24x24 pixels (smaller than the 32x32 tile size)
                scaled_texture = pygame.transform.scale(item_texture, (24, 24))
                
                # EXTREME ENGINEERING: Flip item texture if player is facing left
                if facing_direction == -1:
                    scaled_texture = pygame.transform.flip(scaled_texture, True, False)
                
                # Draw the item on the hand
                screen.blit(scaled_texture, (hand_x, hand_y))

def draw_boss_health_bar():
    """EXTREME ENGINEERING: Draw the legendary boss health bar at the top of the screen"""
    if not boss_fight_active:
        return
    
    # Boss health bar dimensions
    bar_width = 600
    bar_height = 40
    bar_x = (SCREEN_WIDTH - bar_width) // 2
    bar_y = 20
    
    # Draw boss health bar background
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 3)
    
    # Calculate health percentage
    health_percentage = boss_health / boss_max_health
    
    # Draw health bar (changes color based on phase)
    if boss_phase == 1:
        health_color = (255, 0, 0)  # Red for phase 1
    else:
        health_color = (255, 165, 0)  # Orange for phase 2
    
    health_width = int(bar_width * health_percentage)
    pygame.draw.rect(screen, health_color, (bar_x + 2, bar_y + 2, health_width, bar_height - 4))
    
    # Draw boss health text
    health_text = f"🐉 LEGENDARY BOSS - Phase {boss_phase} - HP: {boss_health}/{boss_max_health}"
    health_surface = font.render(health_text, True, (255, 255, 255))
    text_x = bar_x + (bar_width - health_surface.get_width()) // 2
    text_y = bar_y + (bar_height - health_surface.get_height()) // 2
    screen.blit(health_surface, (text_x, text_y))
    
    # Draw phase indicator
    phase_text = f"Phase {boss_phase}" if boss_phase == 1 else "Phase {boss_phase}"
    phase_color = (255, 0, 0) if boss_phase == 1 else (255, 165, 0)
    phase_surface = font.render(phase_text, True, phase_color)
    phase_x = bar_x + 10
    phase_y = bar_y + 10
    screen.blit(phase_surface, (phase_x, phase_y))

def draw_multiplayer_screen():
    """EXTREME ENGINEERING: Draw the professional multiplayer interface"""
    global multiplayer_menu_state
    
    # Fill background
    screen.fill((20, 40, 80))  # Dark blue background
    
    # Title
    title_text = title_font.render("🌐 MULTIPLAYER", True, (255, 255, 255))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
    
    if multiplayer_menu_state == "main":
        draw_multiplayer_main_menu()
    elif multiplayer_menu_state == "host":
        draw_multiplayer_host_menu()
    elif multiplayer_menu_state == "join":
        draw_multiplayer_join_menu()
    elif multiplayer_menu_state == "server_list":
        draw_multiplayer_server_list()

def draw_multiplayer_main_menu():
    """EXTREME ENGINEERING: Draw the main multiplayer menu"""
    # Host Server button
    host_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, 200, 300, 80)
    pygame.draw.rect(screen, (0, 150, 0), host_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), host_btn, 3, border_radius=15)
    
    host_text = font.render("🌐 Host a Server", True, (255, 255, 255))
    host_text_x = host_btn.x + (host_btn.width - host_text.get_width()) // 2
    host_text_y = host_btn.y + (host_btn.height - host_text.get_height()) // 2
    screen.blit(host_text, (host_text_x, host_text_y))
    
    # Join Server button
    join_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, 320, 300, 80)
    pygame.draw.rect(screen, (0, 100, 200), join_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), join_btn, 3, border_radius=15)
    
    join_text = font.render("🔗 Join a Server", True, (255, 255, 255))
    join_text_x = join_btn.x + (join_btn.width - join_text.get_width()) // 2
    join_text_y = join_btn.y + (join_btn.height - join_text.get_height()) // 2
    screen.blit(join_text, (join_text_x, join_text_y))
    
    # Back to Title button
    back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, 440, 300, 80)
    pygame.draw.rect(screen, (150, 0, 0), back_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), back_btn, 3, border_radius=15)
    
    back_text = font.render("⬅️ Back to Title", True, (255, 255, 255))
    back_text_x = back_btn.x + (back_btn.width - back_text.get_width()) // 2
    back_text_y = back_btn.y + (back_btn.height - back_text.get_height()) // 2
    screen.blit(back_text, (back_text_x, back_text_y))
    
    # Store button references for click handling
    global multiplayer_host_btn, multiplayer_join_btn, multiplayer_back_btn
    multiplayer_host_btn = host_btn
    multiplayer_join_btn = join_btn
    multiplayer_back_btn = back_btn

def draw_multiplayer_host_menu():
    """EXTREME ENGINEERING: Draw the host server menu"""
    # Title
    title_text = font.render("🌐 HOST A SERVER", True, (255, 255, 255))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
    
    # World selection
    world_text = font.render("Select World to Host:", True, (200, 200, 200))
    screen.blit(world_text, (SCREEN_WIDTH // 2 - 200, 250))
    
    # World list (simplified for now)
    world_list = ["World 1", "World 2", "Creative World", "Adventure World"]
    for i, world in enumerate(world_list):
        world_btn = pygame.Rect(SCREEN_WIDTH // 2 - 200, 300 + i * 60, 400, 50)
        pygame.draw.rect(screen, (50, 50, 50), world_btn, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 100), world_btn, 3, border_radius=10)
        
        world_text = font.render(world, True, (255, 255, 255))
        world_text_x = world_btn.x + 20
        world_text_y = world_btn.y + (world_btn.height - world_text.get_height()) // 2
        screen.blit(world_text, (world_text_x, world_text_y))
    
    # Start Hosting button
    start_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, 600, 300, 80)
    pygame.draw.rect(screen, (0, 200, 0), start_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), start_btn, 3, border_radius=15)
    
    start_text = font.render("🚀 Start Hosting", True, (255, 255, 255))
    start_text_x = start_btn.x + (start_btn.width - start_text.get_width()) // 2
    start_text_y = start_btn.y + (start_btn.height - start_text.get_height()) // 2
    screen.blit(start_text, (start_text_x, start_text_y))
    
    # Back button
    back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, 700, 300, 80)
    pygame.draw.rect(screen, (150, 0, 0), back_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), back_btn, 3, border_radius=15)
    
    back_text = font.render("⬅️ Back", True, (255, 255, 255))
    back_text_x = back_btn.x + (back_btn.width - back_text.get_width()) // 2
    back_text_y = back_btn.y + (back_btn.height - back_text.get_height()) // 2
    screen.blit(back_text, (back_text_x, back_text_y))
    
    # Store button references
    global multiplayer_start_host_btn, multiplayer_host_back_btn
    multiplayer_start_host_btn = start_btn
    multiplayer_host_back_btn = back_btn

def draw_multiplayer_join_menu():
    """EXTREME ENGINEERING: Draw the join server menu"""
    # Title
    title_text = font.render("🔗 JOIN A SERVER", True, (255, 255, 255))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
    
    # Search for servers button
    search_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, 250, 300, 80)
    pygame.draw.rect(screen, (0, 100, 200), search_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), search_btn, 3, border_radius=15)
    
    search_text = font.render("🔍 Search for Servers", True, (255, 255, 255))
    search_text_x = search_btn.x + (search_btn.width - search_text.get_width()) // 2
    search_text_y = search_btn.y + (search_btn.height - search_text.get_height()) // 2
    screen.blit(search_text, (search_text_x, search_text_y))
    
    # Back button
    back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, 400, 300, 80)
    pygame.draw.rect(screen, (150, 0, 0), back_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), back_btn, 3, border_radius=15)
    
    back_text = font.render("⬅️ Back", True, (255, 255, 255))
    back_text_x = back_btn.x + (back_btn.width - back_text.get_width()) // 2
    back_text_y = back_btn.y + (back_btn.height - back_text.get_height()) // 2
    screen.blit(back_text, (back_text_x, back_text_y))
    
    # Store button references
    global multiplayer_search_btn, multiplayer_join_back_btn
    multiplayer_search_btn = search_btn
    multiplayer_join_back_btn = back_btn

def draw_multiplayer_server_list():
    """EXTREME ENGINEERING: Draw the server list with player counts and descriptions"""
    # Title
    title_text = font.render("🌐 AVAILABLE SERVERS", True, (255, 255, 255))
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
    
    # Server list
    if not server_list:
        no_servers_text = font.render("No servers found. Try hosting one!", True, (200, 200, 200))
        screen.blit(no_servers_text, (SCREEN_WIDTH // 2 - no_servers_text.get_width() // 2, 200))
    else:
        for i, server in enumerate(server_list[:5]):  # Show max 5 servers
            server_btn = pygame.Rect(100, 150 + i * 120, SCREEN_WIDTH - 200, 100)
            pygame.draw.rect(screen, (50, 50, 50), server_btn, border_radius=15)
            pygame.draw.rect(screen, (100, 100, 100), server_btn, 3, border_radius=15)
            
            # Server name
            name_text = font.render(server["name"], True, (255, 255, 255))
            screen.blit(name_text, (server_btn.x + 20, server_btn.y + 10))
            
            # World name
            world_text = small_font.render(f"World: {server['world']}", True, (200, 200, 200))
            screen.blit(world_text, (server_btn.x + 20, server_btn.y + 35))
            
            # Player count
            players_text = small_font.render(f"Players: {server['players']}/{server['max_players']}", True, (0, 255, 0))
            screen.blit(players_text, (server_btn.x + 20, server_btn.y + 55))
            
            # Description
            desc_text = small_font.render(server["description"], True, (150, 150, 150))
            screen.blit(desc_text, (server_btn.x + 20, server_btn.y + 75))
    
    # Back button
    back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 300, 80)
    pygame.draw.rect(screen, (150, 0, 0), back_btn, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), back_btn, 3, border_radius=15)
    
    back_text = font.render("⬅️ Back", True, (255, 255, 255))
    back_text_x = back_btn.x + (back_btn.width - back_text.get_width()) // 2
    back_text_y = back_btn.y + (back_btn.height - back_text.get_height()) // 2
    screen.blit(back_text, (back_text_x, back_text_y))
    
    # Store button reference
    global multiplayer_server_list_back_btn
    multiplayer_server_list_back_btn = back_btn

def draw_player_armor(px, py):
    """EXTREME ENGINEERING: Draw layered armor pieces with proper positioning and visual effects"""
    # EXTREME ENGINEERING: Layer armor pieces in proper order (boots -> leggings -> chestplate -> helmet)
    armor_render_order = ["boots", "leggings", "chestplate", "helmet"]
    
    # Get player facing direction for proper armor positioning
    facing_direction = player.get("facing_direction", 1)
    
    # Define armor positioning offsets for realistic layering (adjusted for facing direction)
    armor_offsets = {
        "helmet": (0, -2),      # Slightly above player head
        "chestplate": (0, 0),   # Center on player torso
        "leggings": (0, 16),    # Lower half of player
        "boots": (0, 24)        # Bottom of player
    }
    
    # Define armor colors for different materials
    armor_colors = {
        "leather": (139, 69, 19),    # Brown leather
        "iron": (192, 192, 192),     # Silver/gray iron
        "chainmail": (169, 169, 169), # Dark gray chainmail
        "gold": (255, 215, 0),       # Gold
        "diamond": (0, 191, 255)     # Cyan diamond
    }
    
    for slot_name in armor_render_order:
        equipped_armor = player["armor"].get(slot_name)
        if equipped_armor and isinstance(equipped_armor, dict) and "type" in equipped_armor:
            armor_type = equipped_armor["type"]
            
            # Extract material type (e.g., "iron" from "iron_helmet")
            material = armor_type.split("_")[0] if "_" in armor_type else "iron"
            
            # Get positioning offset for this armor piece
            offset_x, offset_y = armor_offsets.get(slot_name, (0, 0))
            armor_x = px + offset_x
            armor_y = py + offset_y
            
            # Check if we have a texture for this armor
            if armor_type in textures:
                armor_texture = textures[armor_type]
                
                # EXTREME ENGINEERING: Scale and flip armor texture based on facing direction
                if slot_name == "helmet":
                    scaled_armor = pygame.transform.scale(armor_texture, (32, 16))  # Helmet size
                elif slot_name == "chestplate":
                    scaled_armor = pygame.transform.scale(armor_texture, (32, 20))  # Torso size
                elif slot_name == "leggings":
                    scaled_armor = pygame.transform.scale(armor_texture, (32, 16))  # Legs size
                else:  # boots
                    scaled_armor = pygame.transform.scale(armor_texture, (32, 8))   # Feet size
                
                # EXTREME ENGINEERING: Flip armor if player is facing left
                if facing_direction == -1:
                    scaled_armor = pygame.transform.flip(scaled_armor, True, False)
                
                # Apply material color tinting
                if material in armor_colors:
                    tinted_armor = scaled_armor.copy()
                    color_surface = pygame.Surface(scaled_armor.get_size())
                    color_surface.fill(armor_colors[material])
                    tinted_armor.blit(color_surface, (0, 0), special_flags=pygame.BLEND_MULT)
                    screen.blit(tinted_armor, (armor_x, armor_y))
                else:
                    screen.blit(scaled_armor, (armor_x, armor_y))
                
            else:
                # EXTREME ENGINEERING: Fallback procedural armor rendering
                armor_color = armor_colors.get(material, (128, 128, 128))
                
                # EXTREME ENGINEERING: Draw procedural armor with facing direction awareness
                if slot_name == "helmet":
                    # Draw helmet shape
                    pygame.draw.ellipse(screen, armor_color, (armor_x + 4, armor_y, 24, 16))
                    pygame.draw.rect(screen, armor_color, (armor_x + 8, armor_y + 8, 16, 8))
                elif slot_name == "chestplate":
                    # Draw chestplate shape
                    pygame.draw.rect(screen, armor_color, (armor_x + 2, armor_y, 28, 20))
                    # Add armor detail lines
                    pygame.draw.line(screen, tuple(max(0, c-30) for c in armor_color), 
                                   (armor_x + 6, armor_y + 5), (armor_x + 26, armor_y + 5), 2)
                elif slot_name == "leggings":
                    # Draw leggings shape (adjusted for facing direction)
                    if facing_direction == 1:  # Facing right
                        pygame.draw.rect(screen, armor_color, (armor_x + 4, armor_y, 12, 16))  # Left leg
                        pygame.draw.rect(screen, armor_color, (armor_x + 16, armor_y, 12, 16)) # Right leg
                    else:  # Facing left
                        pygame.draw.rect(screen, armor_color, (armor_x + 4, armor_y, 12, 16))  # Left leg
                        pygame.draw.rect(screen, armor_color, (armor_x + 16, armor_y, 12, 16)) # Right leg
                else:  # boots
                    # Draw boots shape (adjusted for facing direction)
                    if facing_direction == 1:  # Facing right
                        pygame.draw.rect(screen, armor_color, (armor_x + 2, armor_y, 12, 8))   # Left boot
                        pygame.draw.rect(screen, armor_color, (armor_x + 18, armor_y, 12, 8))  # Right boot
                    else:  # Facing left
                        pygame.draw.rect(screen, armor_color, (armor_x + 2, armor_y, 12, 8))   # Left boot
                        pygame.draw.rect(screen, armor_color, (armor_x + 18, armor_y, 12, 8))  # Right boot
                
                # Add shine effect for metallic armor
                if material in ["iron", "gold", "diamond"]:
                    shine_color = tuple(min(255, c + 50) for c in armor_color)
                    if slot_name == "helmet":
                        pygame.draw.line(screen, shine_color, (armor_x + 8, armor_y + 2), (armor_x + 24, armor_y + 2), 1)
                    elif slot_name == "chestplate":
                        pygame.draw.line(screen, shine_color, (armor_x + 4, armor_y + 2), (armor_x + 28, armor_y + 2), 1)
    
    # EXTREME ENGINEERING: Armor set bonus visual effect
    equipped_pieces = [slot for slot in armor_render_order if player["armor"].get(slot)]
    if len(equipped_pieces) >= 3:  # 3+ pieces equipped
        # Add subtle glow effect around player
        glow_surface = pygame.Surface((36, 36), pygame.SRCALPHA)
        glow_color = (255, 255, 0, 30)  # Subtle yellow glow
        pygame.draw.circle(glow_surface, glow_color, (18, 18), 18)
        screen.blit(glow_surface, (px - 2, py - 2))

def calculate_armor_damage_reduction(base_damage):
    """Calculate damage reduction based on equipped armor"""
    # Check if player has any armor equipped
    has_armor = any(
        player["armor"].get(slot) and isinstance(player["armor"].get(slot), dict)
        for slot in ["helmet", "chestplate", "leggings", "boots"]
    )
    
    if has_armor:
        # With armor, reduce damage to 1 heart maximum
        return min(base_damage, 1)
    else:
        # No armor, take full damage
        return base_damage

def draw_world():
    # Draw blocks safely (skip None, air, or unknown keys)
    for key, block in world_data.items():
        if not block or block == "air":
            continue
        # Parse the "x,y" string key format
        try:
            x, y = map(int, key.split(','))
        except (ValueError, AttributeError):
            continue
        
        img = textures.get(block)
        if img is None:
            continue
        
        # Check if this is a GIF texture that should be animated
        gif_path = None
        if block == "carrot":
            gif_path = os.path.join(TILE_DIR, "carrot.gif")
        elif block == "wheat":
            gif_path = os.path.join(TILE_DIR, "carrot.gif")  # Using carrot as wheat
        
        # Use GIF animation if available, otherwise use static texture
        if gif_path and gif_path in gif_animations:
            animated_frame = gif_animations[gif_path].get_current_frame()
            if animated_frame:
                img = animated_frame
        
        screen_x = x * TILE_SIZE - camera_x
        screen_y = y * TILE_SIZE - camera_y
        if -TILE_SIZE < screen_x < SCREEN_WIDTH and -TILE_SIZE < screen_y < SCREEN_HEIGHT:
            screen.blit(img, (screen_x, screen_y))

    # Draw entities
    for entity in entities:
        if entity["type"] == "monster":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            
            # Check if monster should use GIF animation
            monster_gif_path = os.path.join(MOB_DIR, "monster.gif")
            if monster_gif_path in gif_animations:
                monster_frame = gif_animations[monster_gif_path].get_current_frame()
                if monster_frame:
                    screen.blit(monster_frame, (ex, ey))
                else:
                    screen.blit(entity["image"], (ex, ey))
            else:
                screen.blit(entity["image"], (ex, ey))
        elif entity["type"] == "projectile":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            pygame.draw.rect(screen, (200, 50, 50), (ex + 12, ey + 12, 8, 8))
        elif entity["type"] == "villager":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            screen.blit(textures["villager"], (ex, ey))

            # Draw interaction indicator above villager
            indicator_text = font.render("💬", True, (255, 255, 255))
            indicator_x = ex + (TILE_SIZE - indicator_text.get_width()) // 2
            indicator_y = ey - 25
            screen.blit(indicator_text, (indicator_x, indicator_y))
        elif entity["type"] == "zombie":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            screen.blit(textures["zombie"], (ex, ey))
        elif entity["type"] == "rock_projectile":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            # Draw rock projectile as a brown circle
            pygame.draw.circle(screen, (139, 69, 19), (ex + 16, ey + 16), 8)
    
    # Draw boss if boss fight is active
    if boss_fight_active:
        boss_screen_x = int(boss_position["x"] * TILE_SIZE) - camera_x
        boss_screen_y = int(boss_position["y"] * TILE_SIZE) - camera_y
        
        # Check if boss texture is loaded
        if boss_texture_loaded and boss_texture:
            # Draw boss with texture
            screen.blit(boss_texture, (boss_screen_x - 16, boss_screen_y - 16))  # Center the 64x64 texture
        else:
            # Fallback: draw boss as a red rectangle
            pygame.draw.rect(screen, (255, 0, 0), (boss_screen_x, boss_screen_y, TILE_SIZE * 2, TILE_SIZE * 2))
            # Draw boss label
            boss_label = font.render("BOSS", True, (255, 255, 255))
            screen.blit(boss_label, (boss_screen_x, boss_screen_y - 20))

    # Draw player with animation system
    px = int(player["x"] * TILE_SIZE) - camera_x
    py = int(player["y"] * TILE_SIZE) - camera_y
    
    # EXTREME ENGINEERING: Draw player with proper facing direction and flipping
    facing_direction = player.get("facing_direction", 1)
    
    # Use animation system if available
    if player_animator and hasattr(player_animator, 'get_current_frame'):
        try:
            # Get current animation frame
            current_frame = player_animator.get_current_frame()
            if current_frame:
                # Flip frame based on facing direction
                if facing_direction == -1:  # Facing left
                    flipped_frame = pygame.transform.flip(current_frame, True, False)
                    screen.blit(flipped_frame, (px, py))
                else:  # Facing right (default)
                    screen.blit(current_frame, (px, py))
                
                # Debug: Show animation info
                if show_fps:
                    current_anim = getattr(player_animator, 'current_animation_name', 'unknown')
                    debug_text = font.render(f"Anim: {current_anim} | Facing: {'LEFT' if facing_direction == -1 else 'RIGHT'}", True, (255, 255, 0))
                    screen.blit(debug_text, (px, py - 30))
            else:
                # Fallback to character texture
                _draw_player_fallback(px, py, facing_direction)
        except Exception as e:
            print(f"⚠️ Animation drawing failed: {e}")
            # Fallback to character texture
            _draw_player_fallback(px, py, facing_direction)
    else:
        # Fallback to character texture
        _draw_player_fallback(px, py, facing_direction)
    
    # Draw armor on player if equipped
    draw_player_armor(px, py)
    
    # Draw held item on player's right hand
    draw_held_item(px, py)
    
    # Name tag removed - no more floating name above player
    
    # Draw multiplayer chat if connected
    if is_connected:
        draw_multiplayer_chat()


def _draw_player_fallback(px, py, facing_direction):
    """Fallback function to draw player when animation system is unavailable"""
    # Use character manager to get the current character texture
    if character_manager:
        player_texture = character_manager.get_character_texture()
        current_char_name = character_manager.get_current_character_name()
        if player_texture:
            # EXTREME ENGINEERING: Flip player texture based on facing direction
            # Check if this is a GIF texture that should be animated
            current_char_name = character_manager.get_current_character_name()
            char_gif_path = os.path.join(PLAYER_DIR, f"{current_char_name}.gif")
            
            # Use GIF animation if available, otherwise use static texture
            if char_gif_path in gif_animations:
                char_frame = gif_animations[char_gif_path].get_current_frame()
                if char_frame:
                    if facing_direction == -1:  # Facing left
                        flipped_frame = pygame.transform.flip(char_frame, True, False)
                        screen.blit(flipped_frame, (px, py))
                    else:  # Facing right (default)
                        screen.blit(char_frame, (px, py))
                else:
                    # Fallback to static texture
                    if facing_direction == -1:  # Facing left
                        flipped_texture = pygame.transform.flip(player_texture, True, False)
                        screen.blit(flipped_texture, (px, py))
                    else:  # Facing right (default)
                        screen.blit(player_texture, (px, py))
            else:
                # Use static texture
                if facing_direction == -1:  # Facing left
                    flipped_texture = pygame.transform.flip(player_texture, True, False)
                    screen.blit(flipped_texture, (px, py))
                else:  # Facing right (default)
                    screen.blit(player_texture, (px, py))
            
            # Debug: Show current character name and facing direction
            if show_fps:  # Only show when F3 is pressed
                direction_text = "LEFT" if facing_direction == -1 else "RIGHT"
                debug_text = font.render(f"Char: {current_char_name} | Facing: {direction_text}", True, (255, 255, 0))
                screen.blit(debug_text, (px, py - 30))
        else:
            # Fallback to original player image with flipping
            if facing_direction == -1:  # Facing left
                flipped_image = pygame.transform.flip(player_image, True, False)
                screen.blit(flipped_image, (px, py))
            else:  # Facing right (default)
                screen.blit(player_image, (px, py))
            
            if show_fps:
                direction_text = "LEFT" if facing_direction == -1 else "RIGHT"
                debug_text = font.render(f"No texture! | Facing: {direction_text}", True, (255, 0, 0))
                screen.blit(debug_text, (px, py - 30))
    else:
        # Fallback to original player image if character manager not initialized
        # Check if player.gif should be animated
        player_gif_path = os.path.join(PLAYER_DIR, "player.gif")
        if player_gif_path in gif_animations:
            player_frame = gif_animations[player_gif_path].get_current_frame()
            if player_frame:
                if facing_direction == -1:  # Facing left
                    flipped_frame = pygame.transform.flip(player_frame, True, False)
                    screen.blit(flipped_frame, (px, py))
                else:  # Facing right (default)
                    screen.blit(player_frame, (px, py))
            else:
                # Fallback to static image
                if facing_direction == -1:  # Facing left
                    flipped_image = pygame.transform.flip(player_image, True, False)
                    screen.blit(flipped_image, (px, py))
                else:  # Facing right (default)
                    screen.blit(player_image, (px, py))
        else:
            # Use static image
            if facing_direction == -1:  # Facing left
                flipped_image = pygame.transform.flip(player_image, True, False)
                screen.blit(flipped_image, (px, py))
            else:  # Facing right (default)
                screen.blit(player_image, (px, py))
        
        if show_fps:
            direction_text = "LEFT" if facing_direction == -1 else "RIGHT"
            debug_text = font.render(f"No char manager! | Facing: {direction_text}", True, (255, 0, 0))
            screen.blit(debug_text, (px, py - 30))


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
                    # Check if this item should use GIF animation
                    item_texture = textures[item_type]
                    
                    # Check for GIF animations for specific items
                    if item_type == "carrot":
                        carrot_gif_path = os.path.join(TILE_DIR, "carrot.gif")
                        if carrot_gif_path in gif_animations:
                            animated_frame = gif_animations[carrot_gif_path].get_current_frame()
                            if animated_frame:
                                item_texture = animated_frame
                    
                    screen.blit(item_texture, (15 + i * 50, SCREEN_HEIGHT - 55))
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
        else:
            # If still no space, try to add to backpack
            add_to_backpack(item_type, count)
    normalize_inventory()

def add_to_backpack(item_type, count=1):
    """Add `count` of `item_type` into the player's backpack, stacking where possible."""
    if count <= 0:
        return
    # Ensure backpack exists
    if "backpack" not in player:
        player["backpack"] = []
    
    # Try to stack into existing slot
    for item in player["backpack"]:
        if item and item.get("type") == item_type:
            item["count"] = item.get("count", 0) + count
            normalize_backpack()
            return
    
    # Otherwise, append a new slot
    player["backpack"].append({"type": item_type, "count": count})
    normalize_backpack()

def give_starting_items():
    """Give the player starting items"""
    # Give essential tools
    add_to_inventory("sword", 1)
    add_to_inventory("pickaxe", 1)
    
    # Give some basic blocks
    add_to_inventory("stone", 10)
    add_to_inventory("dirt", 10)
    add_to_inventory("oak_planks", 5)
    
    # Give some food
    add_to_inventory("carrot", 5)
    
    # Give crafting materials in backpack
    add_to_backpack("iron", 10)  # For crafting tools and armor
    add_to_backpack("wheat", 15)  # For crafting bread
    add_to_backpack("stick", 20)  # For crafting tools
    
    print("🎁 Gave player starting items: sword, pickaxe, blocks, food, and crafting materials!")

def test_block_breaking():
    """EXTREME ENGINEERING: Comprehensive block breaking test with multiple verification layers"""
    global world_data
    
    print("🚀 EXTREME ENGINEERING BLOCK BREAKING TEST INITIATED")
    print("=" * 60)
    
    # Test coordinates
    test_x, test_y = 0, 10
    test_key = f"{test_x},{test_y}"
    
    print(f"🧪 PHASE 1: Initial State Analysis")
    print(f"   📍 Test coordinates: ({test_x}, {test_y})")
    print(f"   🔑 Test key: '{test_key}'")
    print(f"   📊 World data size: {len(world_data)} blocks")
    print(f"   🔍 Sample keys: {list(world_data.keys())[:5]}")
    
    # PHASE 1: Place test block
    print(f"\n🧪 PHASE 2: Block Placement")
    world_data[test_key] = "stone"
    print(f"   ✅ Placed 'stone' at key '{test_key}'")
    
    # Verify placement
    if test_key in world_data:
        print(f"   🔍 Verification: Key '{test_key}' exists in world_data")
        print(f"   📦 Block value: {world_data[test_key]}")
    else:
        print(f"   ❌ CRITICAL ERROR: Key '{test_key}' not found after placement!")
        return False
    
    # PHASE 2: Test get_block function
    print(f"\n🧪 PHASE 3: get_block Function Test")
    test_block = get_block(test_x, test_y)
    print(f"   🔍 get_block({test_x}, {test_y}) returns: {test_block}")
    print(f"   🔍 Type: {type(test_block)}")
    
    if test_block == "stone":
        print(f"   ✅ get_block function working correctly")
    else:
        print(f"   ❌ CRITICAL ERROR: get_block function malfunction!")
        return False
    
    # PHASE 3: Manual removal test
    print(f"\n🧪 PHASE 4: Manual Block Removal")
    print(f"   🔍 Before removal: {test_key} in world_data = {test_key in world_data}")
    
    # Force removal with multiple methods
    if test_key in world_data:
        del world_data[test_key]
        print(f"   🔨 DELETED key '{test_key}' from world_data")
    else:
        print(f"   ❌ Key not found for deletion!")
    
    # Verify removal
    print(f"   🔍 After removal: {test_key} in world_data = {test_key in world_data}")
    
    # PHASE 4: Post-removal verification
    print(f"\n🧪 PHASE 5: Post-Removal Verification")
    test_block_after = get_block(test_x, test_y)
    print(f"   🔍 get_block({test_x}, {test_y}) after removal: {test_block_after}")
    
    # Multiple verification methods
    verification_passed = True
    
    # Method 1: Direct world_data check
    if test_key in world_data:
        print(f"   ❌ VERIFICATION FAILED: Key still exists in world_data")
        verification_passed = False
    else:
        print(f"   ✅ VERIFICATION PASSED: Key removed from world_data")
    
    # Method 2: get_block check
    if test_block_after is None:
        print(f"   ✅ VERIFICATION PASSED: get_block returns None (air)")
    else:
        print(f"   ❌ VERIFICATION FAILED: get_block returns {test_block_after}")
        verification_passed = False
    
    # Method 3: Force cleanup
    print(f"\n🧪 PHASE 6: Force Cleanup Verification")
    if test_key in world_data:
        print(f"   🧹 Force cleaning up remaining key...")
        world_data.pop(test_key, None)
        print(f"   🔍 After force cleanup: {test_key} in world_data = {test_key in world_data}")
    
    # Final verification
    final_check = get_block(test_x, test_y)
    print(f"   🔍 Final get_block check: {final_check}")
    
    print(f"\n{'='*60}")
    if verification_passed and final_check is None:
        print("🎉 EXTREME ENGINEERING TEST: COMPLETE SUCCESS!")
        print("✅ Block breaking system is working correctly")
        return True
    else:
        print("💥 EXTREME ENGINEERING TEST: CRITICAL FAILURE!")
        print("❌ Block breaking system has fundamental issues")
        return False

def nuclear_block_removal():
    """NUCLEAR OPTION: Force clear all blocks from world_data if normal methods fail"""
    global world_data
    
    print("🚨 NUCLEAR OPTION ACTIVATED!")
    print("💥 Force clearing entire world_data...")
    
    # Store original size
    original_size = len(world_data)
    
    # Force clear everything
    world_data.clear()
    
    print(f"🧹 NUCLEAR CLEANUP COMPLETED!")
    print(f"   📊 Original blocks: {original_size}")
    print(f"   📊 Current blocks: {len(world_data)}")
    print(f"   ✅ All blocks forcefully removed")
    
    return True

def monitor_world_data():
    """EXTREME ENGINEERING: Continuous monitoring of world_data for anomalies"""
    global world_data
    
    print("🔍 EXTREME ENGINEERING MONITORING SYSTEM ACTIVATED")
    print("=" * 60)
    
    # Check for any blocks that might be causing issues
    problematic_blocks = []
    
    for key, value in world_data.items():
        # Check for invalid keys
        if not isinstance(key, str):
            problematic_blocks.append(f"Invalid key type: {type(key)} = {key}")
            continue
        
        # Check for invalid values
        if not isinstance(value, str):
            problematic_blocks.append(f"Invalid value type at {key}: {type(value)} = {value}")
            continue
        
        # Check for empty or None values
        if value is None or value == "":
            problematic_blocks.append(f"Empty value at {key}: {value}")
            continue
    
    if problematic_blocks:
        print("🚨 PROBLEMATIC BLOCKS DETECTED:")
        for problem in problematic_blocks[:10]:  # Show first 10 problems
            print(f"   ❌ {problem}")
        print(f"   📊 Total problems: {len(problematic_blocks)}")
        
        # Auto-fix common issues
        print("🔧 Attempting auto-fix...")
        fixed_count = 0
        
        for key in list(world_data.keys()):
            if not isinstance(key, str):
                world_data.pop(key, None)
                fixed_count += 1
            elif world_data[key] is None or world_data[key] == "":
                world_data.pop(key, None)
                fixed_count += 1
        
        print(f"   🧹 Auto-fixed {fixed_count} problematic blocks")
    else:
        print("✅ No problematic blocks detected")
    
    print(f"📊 World data status: {len(world_data)} blocks")
    print(f"🔍 Sample keys: {list(world_data.keys())[:5]}")
    print("=" * 60)
    
    return len(problematic_blocks) == 0

def break_block(mx, my):
    """EXTREME ENGINEERING: Bulletproof block breaking with multiple verification layers"""
    px, py = int(player["x"]), int(player["y"])
    # EXTREME ENGINEERING FIX: Force integer coordinates
    bx, by = int((mx + camera_x) // TILE_SIZE), int((my + camera_y) // TILE_SIZE)
    block_key = f"{bx},{by}"
    
    print(f"🚀 EXTREME ENGINEERING BLOCK BREAKING INITIATED")
    print(f"🔨 Mouse: ({mx}, {my}) -> World: ({bx}, {by})")
    print(f"👤 Player: ({px}, {py})")
    print(f"🔑 Block key: '{block_key}'")
    
    # Check distance first
    if abs(bx - px) > 2 or abs(by - py) > 2:
        print(f"❌ Too far away: distance = {abs(bx - px)}, {abs(by - py)}")
        return False  # Too far away, silent fail
    
    # Get the block at this position
    block = get_block(bx, by)
    print(f"📦 Block at ({bx}, {by}): {block} (Type: {type(block)})")
    
    if not block or block == "air":
        print(f"❌ Nothing to break or already air")
        return False  # Nothing to break or air, silent fail
    
    # Bedrock, fluids, and villagers are unbreakable
    if block in ("bedrock", "water", "lava", "villager"):
        return False  # Can't break, silent fail
    
    # EXTREME ENGINEERING: Boss damage system - check if player is attacking the boss
    if boss_fight_active:
        # Calculate distance to boss
        boss_distance = abs(bx - boss_position["x"]) + abs(by - boss_position["y"])
        if boss_distance <= 3:  # Within 3 blocks of boss
            # Check if player has sword selected
            if (player["selected"] < len(player["inventory"]) and 
                player["inventory"][player["selected"]] and 
                player["inventory"][player["selected"]]["type"] == "sword"):
                
                # EXTREME ENGINEERING: Deal damage to boss with sword
                damage_boss(BOSS_SWORD_DAMAGE)
                show_message(f"⚔️ You hit the boss with your sword for {BOSS_SWORD_DAMAGE} damage!", 1500)
                print(f"⚔️ Player dealt {BOSS_SWORD_DAMAGE} damage to boss!")
                return True  # Attack successful, don't break blocks
            else:
                show_message("⚔️ You need a sword to attack the boss!", 2000)
                return False  # Need sword to attack boss
    
    # Stone & ores require pickaxe - STRICT REQUIREMENT
    if block in ["stone", "coal", "iron", "gold", "diamond"]:
        # Check if player has pickaxe selected
        if player["selected"] >= len(player["inventory"]) or player["inventory"][player["selected"]]["type"] != "pickaxe":
            return False  # Need pickaxe, silent fail
        
        # Successfully break with pickaxe
        add_to_inventory(block)
        
        # EXTREME ENGINEERING: Multi-layer block removal with force verification
        print(f"\n🔨 PHASE 1: Primary Block Removal")
        print(f"   🔍 Block key '{block_key}' in world_data: {block_key in world_data}")
        
        if block_key in world_data:
            # Method 1: Standard deletion
            del world_data[block_key]
            print(f"   ✅ Method 1: Standard deletion completed")
        else:
            print(f"   ❌ Method 1: Block not found in world_data")
        
        # Method 2: Force cleanup with pop
        if block_key in world_data:
            world_data.pop(block_key, None)
            print(f"   ✅ Method 2: Force cleanup with pop completed")
        
        # Method 3: Direct dictionary manipulation
        try:
            if block_key in world_data:
                world_data.__delitem__(block_key)
                print(f"   ✅ Method 3: Direct dictionary deletion completed")
        except Exception as e:
            print(f"   ⚠️ Method 3: Direct deletion failed: {e}")
        
        # Method 4: Nuclear option - force clear if still exists
        if block_key in world_data:
            print(f"   🚨 NUCLEAR OPTION: Block still exists after all methods!")
            print(f"   🧹 Force clearing entire world_data for this position...")
            # Create a new world_data without this key
            new_world_data = {k: v for k, v in world_data.items() if k != block_key}
            world_data.clear()
            world_data.update(new_world_data)
            print(f"   ✅ Nuclear option completed")
        
        # VERIFICATION LAYER
        print(f"\n🔍 PHASE 2: Multi-Method Verification")
        
        # Verification Method 1: Direct world_data check
        still_in_world_data = block_key in world_data
        print(f"   🔍 Method 1: Direct world_data check: {still_in_world_data}")
        
        # Verification Method 2: get_block function check
        get_block_result = get_block(bx, by)
        print(f"   🔍 Method 2: get_block({bx}, {by}) returns: {get_block_result}")
        
        # Verification Method 3: Force get_block with error handling
        try:
            force_check = world_data.get(block_key)
            print(f"   🔍 Method 3: world_data.get('{block_key}') returns: {force_check}")
        except Exception as e:
            print(f"   ❌ Method 3: Force check failed: {e}")
        
        # Final verification
        if not still_in_world_data and get_block_result is None:
            print(f"   🎉 VERIFICATION SUCCESS: Block completely removed!")
            print(f"   ✅ Block breaking operation completed successfully")
        else:
            print(f"   💥 VERIFICATION FAILED: Block still exists!")
            print(f"   🚨 CRITICAL ERROR: Block removal system malfunction!")
            print(f"   🔧 Attempting emergency cleanup...")
            
            # Emergency cleanup
            if block_key in world_data:
                world_data.pop(block_key, None)
                print(f"   🧹 Emergency cleanup completed")
        
        print(f"   📊 Final world_data size: {len(world_data)} blocks")
        
        # Check for mining achievements
        if block == "diamond":
            check_achievement("first_diamond", 5, "Mined first diamond!")
        elif block == "gold":
            check_achievement("first_gold", 3, "Mined first gold!")
        elif block == "iron":
            check_achievement("first_iron", 2, "Mined first iron!")
        elif block == "coal":
            check_achievement("first_coal", 1, "Mined first coal!")
        
        # Chance to drop coins from valuable ores
        if block in ["gold", "diamond"] and coins_manager:
            if random.random() < 0.1:  # 10% chance
                coin_amount = 1 if block == "gold" else 2
                coins_manager.add_coins(coin_amount)
        
        return True
    
    # Logs can be carved into oak planks with pickaxe
    elif block == "log":
        if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]["type"] == "pickaxe":
            # Carve log into oak planks
            add_to_inventory("oak_planks", 4)  # 1 log = 4 planks
            
            # EXTREME ENGINEERING: Multi-layer log removal with pickaxe
            print(f"\n🔨 EXTREME ENGINEERING LOG REMOVAL (PICKAXE)")
            print(f"   🔍 Log key '{block_key}' in world_data: {block_key in world_data}")
            
            # Force removal with all methods
            if block_key in world_data:
                del world_data[block_key]
                print(f"   ✅ Log deletion completed")
            
            # Verify removal
            if block_key in world_data:
                world_data.pop(block_key, None)
                print(f"   🧹 Force cleanup completed")
            
            # Final verification
            final_check = get_block(bx, by)
            if final_check is None:
                print(f"   🎉 Log removal verification: SUCCESS")
            else:
                print(f"   💥 Log removal verification: FAILED - {final_check}")
        else:
            # Regular log breaking without pickaxe
            add_to_inventory("log")
            
            # EXTREME ENGINEERING: Multi-layer log removal without pickaxe
            print(f"\n🔨 EXTREME ENGINEERING LOG REMOVAL (NO PICKAXE)")
            print(f"   🔍 Log key '{block_key}' in world_data: {block_key in world_data}")
            
            # Force removal with all methods
            if block_key in world_data:
                del world_data[block_key]
                print(f"   ✅ Log deletion completed")
            
            # Verify removal
            if block_key in world_data:
                world_data.pop(block_key, None)
                print(f"   🧹 Force cleanup completed")
            
            # Final verification
            final_check = get_block(bx, by)
            if final_check is None:
                print(f"   🎉 Log removal verification: SUCCESS")
            else:
                print(f"   💥 Log removal verification: FAILED - {final_check}")
        
        return True
    
    # Chest: pick up contents and the chest itself
    elif block == "chest":
        inv = chest_system.get_chest_inventory((bx, by))
        # Check for special items in natural chests (not player-placed)
        is_natural_chest = (bx, by) not in chest_system.player_placed_chests
        
        # Move all items (with counts) into the player's inventory
        items_collected = 0
        for it in inv:
            if it and isinstance(it, dict) and "type" in it:
                item_type = it["type"]
                item_count = it.get("count", 1)
                add_to_inventory(item_type, item_count)
                items_collected += item_count
                
                # Check for special achievements in natural chests
                if is_natural_chest:
                    if item_type == "diamond":
                        check_achievement("diamond_chest", 1000000, "Found diamond in chest! +1,000,000 coins!")
                        if check_achievement("ultimate_achievement", 1000000, "ULTIMATE: Found diamond in chest!"):
                            if character_manager:
                                success, cost = character_manager.unlock_character("hacker", coins_manager.get_coins())
                    elif item_type == "gold":
                        check_achievement("first_gold", 3, "Found gold in chest!")
                    elif item_type == "iron":
                        check_achievement("first_iron", 2, "Found iron in chest!")
                    elif item_type == "coal":
                        check_achievement("first_coal", 1, "Found coal in chest!")
        
        # Remove the chest from the chest system
        chest_system.chest_inventories.pop((bx, by), None)
        chest_system.player_placed_chests.discard((bx, by))
        
        # Give the empty chest item back to player
        add_to_inventory("chest", 1)
        
        # EXTREME ENGINEERING: Multi-layer chest removal
        print(f"\n🔨 EXTREME ENGINEERING CHEST REMOVAL")
        print(f"   🔍 Chest key '{block_key}' in world_data: {block_key in world_data}")
        
        # Force removal with all methods
        if block_key in world_data:
            del world_data[block_key]
            print(f"   ✅ Chest deletion completed")
        
        # Verify removal
        if block_key in world_data:
            world_data.pop(block_key, None)
            print(f"   🧹 Force cleanup completed")
        
        # Final verification
        final_check = get_block(bx, by)
        if final_check is None:
            print(f"   🎉 Chest removal verification: SUCCESS")
        else:
            print(f"   💥 Chest removal verification: FAILED - {final_check}")
        
        return True
    
    # All other blocks can be broken without tools
    else:
        add_to_inventory(block)
        
        # EXTREME ENGINEERING: Multi-layer general block removal
        print(f"\n🔨 EXTREME ENGINEERING GENERAL BLOCK REMOVAL")
        print(f"   🔍 Block key '{block_key}' in world_data: {block_key in world_data}")
        
        # Force removal with all methods
        if block_key in world_data:
            del world_data[block_key]
            print(f"   ✅ Block deletion completed")
        
        # Verify removal
        if block_key in world_data:
            world_data.pop(block_key, None)
            print(f"   🧹 Force cleanup completed")
        
        # Final verification
        final_check = get_block(bx, by)
        if final_check is None:
            print(f"   🎉 Block removal verification: SUCCESS")
        else:
            print(f"   💥 Block removal verification: FAILED - {final_check}")
        
        return True

def place_block(mx, my):
    """Place a block at the mouse position - ONLY on air, with proper validation"""
    px, py = int(player["x"]), int(player["y"])
    # EXTREME ENGINEERING FIX: Force integer coordinates
    bx, by = int((mx + camera_x) // TILE_SIZE), int((my + camera_y) // TILE_SIZE)
    
    # Check distance first
    if abs(bx - px) > 2 or abs(by - py) > 2:
        return False  # Too far away, silent fail
    
    # Check if player has an item selected
    if player["selected"] >= len(player["inventory"]) or not player["inventory"][player["selected"]]:
        return False  # No item selected, silent fail
    
    item = player["inventory"][player["selected"]]
    item_type = item["type"]
    
    # Disallow placing tools, fluids, and air
    if item_type in ["sword", "pickaxe", "water", "lava", "air"]:
        return False  # Silent fail for invalid items
    
    # Check if target location is ONLY air (no other blocks)
    current_block = get_block(bx, by)
    if current_block is not None and current_block != "air":
        return False  # Can't place on existing blocks, silent fail
    
    # Special validation for carrots - must be on grass below
    if item_type == "carrot":
        block_below = get_block(bx, by + 1)
        if block_below != "grass":
            return False  # Carrots need grass below, silent fail
    
    # Special validation for ladders - check bedrock level
    if item_type == "ladder":
        br_y = bedrock_level_at(bx)
        if br_y is not None and by >= br_y:
            return False  # Can't place ladders through bedrock, silent fail
    
    # All validations passed - place the block
    if item_type == "chest":
        set_block(bx, by, "chest")
        chest_system.create_player_placed_chest((bx, by))
        print(f"📦 Placed EMPTY chest at ({bx}, {by}) - player chests start empty!")
    else:
        set_block(bx, by, item_type)
    
    # Consume one item
    item["count"] -= 1
    if item["count"] <= 0:
        player["inventory"].pop(player["selected"])
        normalize_inventory()
    
    return True  # Success

def attack_monsters(mx, my):
    """Attack monsters with sword - monsters die in exactly 4 hits"""
    px, py = player["x"], player["y"]
    
    for mob in entities[:]:
        if mob["type"] == "monster":
            dx = (mx + camera_x) / TILE_SIZE - mob["x"]
            dy = (my + camera_y) / TILE_SIZE - mob["y"]
            if math.hypot(dx, dy) <= 2:
                # Only swords can damage; each hit deals 1 (4 hits to defeat)
                if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]["type"] == "sword":
                    mob["hp"] = mob.get("hp", 4) - 1  # Start with 4 HP, die in 4 hits
                    if mob["hp"] <= 0:
                        # Check for first monster kill achievement
                        check_achievement("first_monster_kill", 25, "Defeated first monster!")
                        
                        # Monster defeated - chance to drop coins
                        if random.random() < 0.15 and coins_manager:
                            coin_amount = random.randint(1, 2)
                            coins_manager.add_coins(coin_amount)
                        
                        entities.remove(mob)
        
        elif mob["type"] == "zombie":
            dx = (mx + camera_x) / TILE_SIZE - mob["x"]
            dy = (my + camera_y) / TILE_SIZE - mob["y"]
            if math.hypot(dx, dy) <= 2:
                # Only swords can damage zombies; each hit deals 1 (4 hits to defeat)
                if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]["type"] == "sword":
                    mob["hp"] = mob.get("hp", 4) - 1  # Start with 4 HP, die in 4 hits
                    if mob["hp"] <= 0:
                        # Check for first monster kill achievement
                        check_achievement("first_monster_kill", 25, "Defeated first zombie!")
                        
                        # Zombie defeated - chance to drop coins
                        if random.random() < 0.2 and coins_manager:
                            coin_amount = random.randint(1, 3)
                            coins_manager.add_coins(coin_amount)
                        
                        entities.remove(mob)

# --- Part Six: World Interaction, Carrots, Chests, Hunger/Health, Monster Damage ---
def update_world_interactions():
    global fall_start_y, world_data, entities

    px, py = int(player["x"]), int(player["y"])
    block_below = get_block(px, py + 1)
    block_at = get_block(px, py)

    # VOID DEATH: Kill player if they fall into the void (below Y=0)
    if py < 0:
        print(f"💀 Player fell into the void at Y={py} - DEATH!")
        player["health"] = 0
        show_death_screen()
        return

    # Lava hazard: standing in or on lava hurts
    if block_at == "lava" or block_below == "lava":
        damage = calculate_armor_damage_reduction(1)
        player["health"] -= damage
        damage_sound.play()
        if player["health"] <= 0:
            show_death_screen()

    # Carrots: eat if health OR hunger not full, otherwise collect
    if block_at == "carrot":
        should_eat = False
        if player["health"] < 10:
            player["health"] += 1
            should_eat = True
        if player["hunger"] < 10:
            player["hunger"] = min(10, player["hunger"] + 1)
            should_eat = True
        
        if should_eat:
            # Check for first carrot achievement
            check_achievement("first_carrot", 10, "Ate first carrot!")
            
            # Remove carrot completely from world data (turns into air)
            if f"{px},{py}" in world_data:
                del world_data[f"{px},{py}"]
            # Show what was restored
            restored = []
            if player["health"] < 10:
                restored.append("health")
            if player["hunger"] < 10:
                restored.append("hunger")
            if restored:
                print(f"🥕 Ate world carrot: Restored {', '.join(restored)} - Health={player['health']}, Hunger={player['hunger']}")
            else:
                print(f"🥕 Ate world carrot: Both stats already full - Health={player['health']}, Hunger={player['hunger']}")
        else:
            add_to_inventory("carrot")
            # Remove carrot completely from world data (turns into air)
            if f"{px},{py}" in world_data:
                del world_data[f"{px},{py}"]
    elif block_below == "carrot":
        should_eat = False
        if player["health"] < 10:
            player["health"] += 1
            should_eat = True
        if player["hunger"] < 10:
            player["hunger"] = min(10, player["hunger"] + 1)
            should_eat = True
        
        if should_eat:
            # Check for first carrot achievement
            check_achievement("first_carrot", 10, "Ate first carrot!")
            
            # Remove carrot completely from world data (turns into air)
            if f"{px},{py + 1}" in world_data:
                del world_data[f"{px},{py + 1}"]
            # Show what was restored
            restored = []
            if player["health"] < 10:
                restored.append("health")
            if player["hunger"] < 10:
                restored.append("hunger")
            if restored:
                print(f"🥕 Ate world carrot: Restored {', '.join(restored)} - Health={player['health']}, Hunger={player['hunger']}")
            else:
                print(f"🥕 Ate world carrot: Both stats already full - Health={player['health']}, Hunger={player['hunger']}")
        else:
            add_to_inventory("carrot")
            # Remove carrot completely from world data (turns into air)
            if f"{px},{py + 1}" in world_data:
                del world_data[f"{px},{py + 1}"]

    # Fall damage: apply if fall was 4+ blocks
    if not player["on_ground"]:
        if fall_start_y is None:
            fall_start_y = player["y"]
    else:
        if fall_start_y is not None and player["y"] - fall_start_y >= 4:
            damage = calculate_armor_damage_reduction(1)
            player["health"] -= damage
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
    print(f"📦 Opened chest at ({bx}, {by})")


def chest_slot_rect(col, row):
    x = CHEST_UI_X + 20 + col * (SLOT_SIZE + SLOT_MARGIN)
    y = CHEST_UI_Y + 50 + row * (SLOT_SIZE + SLOT_MARGIN)
    return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

def hotbar_slot_rect(idx):
    return pygame.Rect(10 + idx * 50, SCREEN_HEIGHT - 60, 40, 40)

def inventory_hotbar_slot_rect(idx, inv_x, inv_y):
    """Get hotbar slot rect in inventory UI"""
    row = idx // 3
    col = idx % 3
    slot_x = inv_x + 250 + col * 60
    slot_y = inv_y + 120 + row * 60
    return pygame.Rect(slot_x, slot_y, 50, 50)

def inventory_backpack_slot_rect(idx, inv_x, inv_y):
    """Get backpack slot rect in inventory UI"""
    row = idx // 3
    col = idx % 3
    slot_x = inv_x + 500 + col * 60
    slot_y = inv_y + 120 + row * 60
    return pygame.Rect(slot_x, slot_y, 50, 50)

def inventory_armor_slot_rect(slot_name, inv_x, inv_y):
    """Get armor slot rect in inventory UI"""
    armor_slots = ["helmet", "chestplate", "leggings", "boots"]
    slot_idx = armor_slots.index(slot_name)
    slot_x = inv_x + 30
    slot_y = inv_y + 120 + slot_idx * 60
    return pygame.Rect(slot_x, slot_y, 50, 50)

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
    """Show an enhanced tooltip with item information when hovering over it"""
    if not item or not isinstance(item, dict) or "type" not in item:
        return
    
    # Get the item name (capitalize first letter)
    item_name = item["type"].replace("_", " ").title()
    
    # Get item count
    item_count = item.get("count", 1)
    
    # Create enhanced tooltip text
    if item_count > 1:
        tooltip_text = f"{item_name} x{item_count}"
    else:
        tooltip_text = item_name
    
    # Add special indicators for guaranteed items
    if item["type"] in ["sword", "pickaxe"]:
        tooltip_text += " ⚔️"
    
    # Render the tooltip text
    tooltip_surface = font.render(tooltip_text, True, (255, 255, 255))
    
    # Calculate tooltip position (above mouse, but don't go off screen)
    tooltip_x = mouse_x + 10
    tooltip_y = mouse_y - 30
    
    # Adjust if tooltip would go off screen
    if tooltip_x + tooltip_surface.get_width() > SCREEN_WIDTH:
        tooltip_x = mouse_x - tooltip_surface.get_width() - 10
    if tooltip_y < 0:
        tooltip_y = mouse_y + 20
    
    # Draw enhanced tooltip background with border
    padding = 6
    bg_rect = pygame.Rect(
        tooltip_x - padding, 
        tooltip_y - padding, 
        tooltip_surface.get_width() + padding * 2, 
        tooltip_surface.get_height() + padding * 2
    )
    
    # Draw background with alpha
    tooltip_bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(tooltip_bg, (0, 0, 0, 200), tooltip_bg.get_rect())
    pygame.draw.rect(tooltip_bg, (255, 215, 0, 255), tooltip_bg.get_rect(), 2)  # Gold border
    screen.blit(tooltip_bg, bg_rect)
    
    # Draw tooltip text
    screen.blit(tooltip_surface, (tooltip_x, tooltip_y))

def draw_chest_ui():
    update_chest_ui_geometry()
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Enhanced chest window with better styling
    pygame.draw.rect(screen, (40, 40, 60), (CHEST_UI_X, CHEST_UI_Y, CHEST_UI_W, CHEST_UI_H))
    pygame.draw.rect(screen, (255, 215, 0), (CHEST_UI_X, CHEST_UI_Y, CHEST_UI_W, CHEST_UI_H), 3)  # Gold border
    
    # Enhanced title with chest info
    title = BIG_FONT.render("📦 Treasure Chest", True, (255, 255, 255))
    screen.blit(title, (CHEST_UI_X + 20, CHEST_UI_Y + 10))
    
    # Show chest info (type and contents)
    if open_chest_pos:
        chest_info = chest_system.get_chest_info(open_chest_pos)
        if chest_info:
            info_text = f"Type: {chest_info['type'].title()} | Items: {chest_info['item_count']} | Total: {chest_info['total_items']}"
            info_surface = font.render(info_text, True, (200, 200, 200))
            screen.blit(info_surface, (CHEST_UI_X + 20, CHEST_UI_Y + 35))
            
            # Highlight guaranteed items
            if chest_info['has_sword'] and chest_info['has_pickaxe']:
                guaranteed_text = "⚔️ Guaranteed: Sword + Pickaxe"
                guaranteed_surface = font.render(guaranteed_text, True, (100, 255, 100))
                screen.blit(guaranteed_surface, (CHEST_UI_X + 20, CHEST_UI_Y + 55))

    slots = chest_system.get_chest_inventory(open_chest_pos)
    # Draw enhanced chest slots with highlighting
    for r in range(chest_system.CHEST_ROWS):
        for c in range(chest_system.CHEST_COLS):
            idx = r * chest_system.CHEST_COLS + c
            rect = chest_slot_rect(c, r)
            
            # Enhanced slot styling
            if idx < len(slots) and slots[idx]:
                item = slots[idx]
                # Highlight guaranteed items (sword and pickaxe)
                if item["type"] in ["sword", "pickaxe"]:
                    pygame.draw.rect(screen, (100, 255, 100), rect)  # Green for guaranteed
                    pygame.draw.rect(screen, (0, 200, 0), rect, 3)   # Darker green border
                else:
                    pygame.draw.rect(screen, (90, 90, 90), rect)     # Normal gray
                    pygame.draw.rect(screen, (200, 200, 200), rect, 2)
                
                draw_item_icon(item, rect.x + 2, rect.y + 2)
                
                # Show tooltip when mouse hovers over item
                if rect.collidepoint(mouse_pos):
                    show_item_tooltip(item, mouse_pos[0], mouse_pos[1])
            else:
                # Empty slot
                pygame.draw.rect(screen, (60, 60, 80), rect)
                pygame.draw.rect(screen, (150, 150, 150), rect, 1)

    # Draw enhanced hotbar with better styling
    hotbar_title = font.render("🎒 Your Inventory", True, (255, 255, 255))
    screen.blit(hotbar_title, (CHEST_UI_X + 20, CHEST_UI_Y + 140))
    
    for i in range(9):
        rect = hotbar_slot_rect(i)
        # Enhanced hotbar slot styling
        if i == player["selected"]:
            pygame.draw.rect(screen, (255, 255, 100), rect, 3)  # Yellow for selected
        else:
            pygame.draw.rect(screen, (255, 255, 255), rect, 2)
        
        if i < len(player["inventory"]):
            draw_item_icon(player["inventory"][i], rect.x + 2, rect.y + 2)
            
            # Show tooltip when mouse hovers over item
            if rect.collidepoint(mouse_pos):
                show_item_tooltip(player["inventory"][i], mouse_pos[0], mouse_pos[1])

    # Instructions
    instructions = [
        "💡 Drag items between chest and inventory",
        "🔒 Sword and Pickaxe are guaranteed in every chest",
        "📦 Right-click to close chest"
    ]
    
    for i, instruction in enumerate(instructions):
        inst_text = small_font.render(instruction, True, (200, 200, 200))
        screen.blit(inst_text, (CHEST_UI_X + 20, CHEST_UI_Y + 180 + i * 20))

    # Draw the dragged item under mouse (if any)
    if drag_item:
        mx, my = mouse_pos
        draw_item_icon(drag_item, mx - 16, my - 16)

def draw_full_inventory_ui():
    """Draw the full inventory interface with armor slots and backpack"""
    global inventory_close_button
    
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Inventory window
    inv_width = 800
    inv_height = 600
    inv_x = center_x(inv_width)
    inv_y = (SCREEN_HEIGHT - inv_height) // 2
    
    # Draw inventory background
    pygame.draw.rect(screen, (40, 40, 60), (inv_x, inv_y, inv_width, inv_height))
    pygame.draw.rect(screen, (255, 215, 0), (inv_x, inv_y, inv_width, inv_height), 3)  # Gold border
    
    # Inventory title
    title = BIG_FONT.render("🎒 Full Inventory", True, (255, 255, 255))
    screen.blit(title, (inv_x + 20, inv_y + 20))
    
    # Player info
    player_info = font.render(f"Player: {GLOBAL_USERNAME or 'Unknown'}", True, (255, 255, 100))
    screen.blit(player_info, (inv_x + 20, inv_y + 70))
    
    # Inventory tabs
    tab_width = 120
    tab_height = 35
    tab_y = inv_y + 100
    
    # Inventory tab
    inventory_tab_color = (100, 150, 255) if current_inventory_tab == "inventory" else (80, 80, 80)
    inventory_tab_rect = pygame.Rect(inv_x + 20, tab_y, tab_width, tab_height)
    pygame.draw.rect(screen, inventory_tab_color, inventory_tab_rect)
    pygame.draw.rect(screen, (255, 255, 255), inventory_tab_rect, 2)
    inventory_text = font.render("📦 Inventory", True, (255, 255, 255))
    screen.blit(inventory_text, (inv_x + 35, tab_y + 8))
    
    # Crafting tab
    crafting_tab_color = (255, 150, 100) if current_inventory_tab == "crafting" else (80, 80, 80)
    crafting_tab_rect = pygame.Rect(inv_x + 150, tab_y, tab_width, tab_height)
    pygame.draw.rect(screen, crafting_tab_color, crafting_tab_rect)
    pygame.draw.rect(screen, (255, 255, 255), crafting_tab_rect, 2)
    crafting_text = font.render("⚒️ Crafting", True, (255, 255, 255))
    screen.blit(crafting_text, (inv_x + 165, tab_y + 8))
    
    # Armor section (left side)
    armor_x = inv_x + 30
    armor_y = inv_y + 160
    armor_title = font.render("🛡️ Armor", True, (255, 255, 255))
    screen.blit(armor_title, (armor_x, armor_y - 30))
    
    # Armor slots
    armor_slots = [
        ("helmet", "iron_helmet", "Helmet"),
        ("chestplate", "iron_chestplate", "Chestplate"),
        ("leggings", "iron_leggings", "Leggings"),
        ("boots", "iron_boots", "Boots")
    ]
    
    for i, (slot_name, item_type, display_name) in enumerate(armor_slots):
        slot_y = armor_y + i * 60
        slot_rect = pygame.Rect(armor_x, slot_y, 50, 50)
        
        # Draw slot background
        pygame.draw.rect(screen, (80, 80, 100), slot_rect)
        pygame.draw.rect(screen, (200, 200, 200), slot_rect, 2)
        
        # Draw slot label
        label = font.render(display_name, True, (255, 255, 255))
        screen.blit(label, (armor_x + 60, slot_y + 15))
        
        # Draw equipped armor if any
        equipped_armor = player["armor"].get(slot_name)
        if equipped_armor:
            if isinstance(equipped_armor, dict) and "type" in equipped_armor:
                item_type = equipped_armor["type"]
                if item_type in textures:
                    screen.blit(textures[item_type], (armor_x + 2, slot_y + 2))
                else:
                    # Fallback text
                    text = font.render("ARMOR", True, (255, 255, 255))
                    screen.blit(text, (armor_x + 5, slot_y + 15))
            else:
                # Fallback text
                text = font.render("ARMOR", True, (255, 255, 255))
                screen.blit(text, (armor_x + 5, slot_y + 15))
    
    # Hotbar section (center)
    hotbar_x = inv_x + 250
    hotbar_y = inv_y + 160
    hotbar_title = font.render("⚡ Hotbar", True, (255, 255, 255))
    screen.blit(hotbar_title, (hotbar_x, hotbar_y - 30))
    
    # Draw hotbar slots (3x3 grid)
    for row in range(3):
        for col in range(3):
            slot_idx = row * 3 + col
            slot_x = hotbar_x + col * 60
            slot_y = hotbar_y + row * 60
            slot_rect = pygame.Rect(slot_x, slot_y, 50, 50)
            
            # Highlight selected slot
            if slot_idx == player["selected"]:
                pygame.draw.rect(screen, (255, 255, 100), slot_rect, 3)
            else:
                pygame.draw.rect(screen, (80, 80, 100), slot_rect, 2)
            
            # Draw item if exists
            if slot_idx < len(player["inventory"]):
                item = player["inventory"][slot_idx]
                if item and isinstance(item, dict):
                    item_type = item.get("type")
                    if item_type in textures:
                        screen.blit(textures[item_type], (slot_x + 2, slot_y + 2))
                    # Draw count
                    count = item.get("count", 1)
                    if count > 1:
                        count_text = font.render(str(count), True, (255, 255, 0))
                        screen.blit(count_text, (slot_x + 35, slot_y + 35))
    
    # Right side content based on selected tab
    if current_inventory_tab == "inventory":
        # Backpack section (right side)
        backpack_x = inv_x + 500
        backpack_y = inv_y + 160
        backpack_title = font.render("🎒 Backpack", True, (255, 255, 255))
        screen.blit(backpack_title, (backpack_x, backpack_y - 30))
        
        # Draw backpack slots (3x9 grid)
        for row in range(9):
            for col in range(3):
                slot_idx = row * 3 + col
                slot_x = backpack_x + col * 60
                slot_y = backpack_y + row * 60
                slot_rect = pygame.Rect(slot_x, slot_y, 50, 50)
                
                pygame.draw.rect(screen, (80, 80, 100), slot_rect)
                pygame.draw.rect(screen, (200, 200, 200), slot_rect, 2)
                
                # Draw item if exists
                if slot_idx < len(player["backpack"]):
                    item = player["backpack"][slot_idx]
                    if item and isinstance(item, dict):
                        item_type = item.get("type")
                        if item_type in textures:
                            screen.blit(textures[item_type], (slot_x + 2, slot_y + 2))
                        # Draw count
                        count = item.get("count", 1)
                        if count > 1:
                            count_text = font.render(str(count), True, (255, 255, 0))
                            screen.blit(count_text, (slot_x + 35, slot_y + 35))
    
    elif current_inventory_tab == "crafting":
        # Crafting section (right side)
        crafting_x = inv_x + 500
        crafting_y = inv_y + 160
        crafting_title = font.render("⚒️ Crafting Table", True, (255, 255, 255))
        screen.blit(crafting_title, (crafting_x, crafting_y - 30))
        
        # 3x3 crafting grid
        slot_size = 50
        grid_start_x = crafting_x
        grid_start_y = crafting_y
        
        for row in range(3):
            for col in range(3):
                slot_x = grid_start_x + col * (slot_size + 10)
                slot_y = grid_start_y + row * (slot_size + 10)
                slot_index = row * 3 + col
                
                # Draw slot background
                slot_color = (80, 80, 100) if crafting_materials[slot_index] else (60, 60, 80)
                pygame.draw.rect(screen, slot_color, (slot_x, slot_y, slot_size, slot_size))
                pygame.draw.rect(screen, (150, 150, 150), (slot_x, slot_y, slot_size, slot_size), 2)
                
                # Draw item in slot
                if crafting_materials[slot_index]:
                    material = crafting_materials[slot_index]
                    item_type = material.get("type")
                    if item_type in textures:
                        screen.blit(textures[item_type], (slot_x + 2, slot_y + 2))
                    
                    # Draw count
                    count = material.get("count", 1)
                    if count > 1:
                        count_text = font.render(str(count), True, (255, 255, 0))
                        screen.blit(count_text, (slot_x + slot_size - 15, slot_y + slot_size - 15))
        
        # Output slot
        output_x = crafting_x + 200
        output_y = crafting_y + 60
        pygame.draw.rect(screen, (120, 120, 120), (output_x, output_y, slot_size, slot_size))
        pygame.draw.rect(screen, (200, 200, 200), (output_x, output_y, slot_size, slot_size), 3)
        
        # Check recipe and show output
        recipe_name = check_crafting_recipe(crafting_materials)
        if recipe_name:
            recipe = CRAFTING_RECIPES[recipe_name]
            output_type = recipe["output"]["type"]
            if output_type in textures:
                screen.blit(textures[output_type], (output_x + 2, output_y + 2))
            
            # Craft button
            craft_btn = pygame.Rect(output_x - 10, output_y + 60, 70, 30)
            pygame.draw.rect(screen, (100, 255, 100), craft_btn)
            pygame.draw.rect(screen, (255, 255, 255), craft_btn, 2)
            craft_text = font.render("CRAFT", True, (0, 0, 0))
            screen.blit(craft_text, (craft_btn.x + 10, craft_btn.y + 8))
        
        # Clear button
        clear_btn = pygame.Rect(crafting_x + 200, crafting_y + 100, 70, 30)
        pygame.draw.rect(screen, (255, 100, 100), clear_btn)
        pygame.draw.rect(screen, (255, 255, 255), clear_btn, 2)
        clear_text = font.render("CLEAR", True, (255, 255, 255))
        screen.blit(clear_text, (clear_btn.x + 10, clear_btn.y + 8))
    
    # Instructions
    instructions = [
        "T - Close inventory",
        "Click items to move them",
        "Drag items between slots",
        "Right-click to equip armor"
    ]
    
    for i, instruction in enumerate(instructions):
        inst_text = font.render(instruction, True, (200, 200, 200))
        screen.blit(inst_text, (inv_x + 20, inv_y + inv_height - 100 + i * 25))
    
    # Close button
    close_button = pygame.Rect(inv_x + inv_width - 80, inv_y + 20, 60, 30)
    pygame.draw.rect(screen, (200, 100, 100), close_button)
    pygame.draw.rect(screen, (255, 255, 255), close_button, 2)
    
    close_text = font.render("X", True, (255, 255, 255))
    close_text_x = close_button.x + (close_button.width - close_text.get_width()) // 2
    close_text_y = close_button.y + (close_button.height - close_text.get_height()) // 2
    screen.blit(close_text, (close_text_x, close_text_y))
    
    # Store close button rect
    inventory_close_button = close_button
    
    # ENHANCED DRAG-AND-DROP: Draw the dragged item under mouse with better visibility
    if inventory_drag_item:
        mx, my = mouse_pos
        # Add a semi-transparent background for better visibility
        drag_bg = pygame.Surface((40, 40), pygame.SRCALPHA)
        drag_bg.fill((255, 255, 255, 100))  # Semi-transparent white background
        screen.blit(drag_bg, (mx - 20, my - 20))
        
        # Draw the item icon centered on cursor
        draw_item_icon(inventory_drag_item, mx - 20, my - 20)
        
        # Add item count if more than 1
        if inventory_drag_item.get("count", 1) > 1:
            count_text = font.render(str(inventory_drag_item["count"]), True, (255, 255, 0))
            screen.blit(count_text, (mx + 5, my + 5))

def draw_shop_ui():
    """Draw the character selection shop interface"""
    global current_character_index
    
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Shop window
    shop_width = 700
    shop_height = 600
    shop_x = center_x(shop_width)
    shop_y = (SCREEN_HEIGHT - shop_height) // 2
    
    # Draw shop background
    pygame.draw.rect(screen, (40, 40, 80), (shop_x, shop_y, shop_width, shop_height))
    pygame.draw.rect(screen, (255, 215, 0), (shop_x, shop_y, shop_width, shop_height), 3)  # Gold border
    
    # Shop title
    title = BIG_FONT.render("🎭 Character Selection", True, (255, 255, 255))
    screen.blit(title, (shop_x + 20, shop_y + 20))
    
    # Player coins display
    coins_display = coins_manager.get_formatted_balance() if coins_manager else "0"
    coins_text = font.render(f"💰 Coins: {coins_display}", True, (255, 215, 0))
    screen.blit(coins_text, (shop_x + 20, shop_y + 70))
    
    # Current character display
    if character_manager:
        current_char = character_manager.available_characters[current_character_index]
        current_text = font.render(f"Current: {current_char['name']}", True, (255, 255, 255))
        screen.blit(current_text, (shop_x + 20, shop_y + 100))
    
    # Character preview area (center)
    preview_size = 120
    preview_x = shop_x + (shop_width - preview_size) // 2
    preview_y = shop_y + 140
    
    # Draw character preview box
    pygame.draw.rect(screen, (60, 60, 100), (preview_x, preview_y, preview_size, preview_size))
    pygame.draw.rect(screen, (200, 200, 200), (preview_x, preview_y, preview_size, preview_size), 2)
    
    # Character name in preview (capitalize first letter)
    char_name = font.render(current_char['name'].title(), True, (255, 255, 255))
    screen.blit(char_name, (preview_x + (preview_size - char_name.get_width()) // 2, preview_y + preview_size + 10))
    
    # Character description
    desc_text = font.render(current_char['description'], True, (200, 200, 200))
    screen.blit(desc_text, (preview_x + (preview_size - desc_text.get_width()) // 2, preview_y + preview_size + 35))
    
    # Price display
    if current_char['price'] > 0:
        price_text = font.render(f"💰 {current_char['price']} coins", True, (255, 215, 0))
        screen.blit(price_text, (preview_x + (preview_size - price_text.get_width()) // 2, preview_y + preview_size + 60))
    else:
        price_text = font.render("FREE", True, (100, 255, 100))
        screen.blit(price_text, (preview_x + (preview_size - price_text.get_width()) // 2, preview_y + preview_size + 60))
    
    # Draw character texture preview
    if character_manager:
        char_texture = character_manager.get_character_texture(current_char['name'])
        if char_texture:
            # Scale down for preview
            preview_texture = pygame.transform.scale(char_texture, (preview_size - 20, preview_size - 20))
            screen.blit(preview_texture, (preview_x + 10, preview_y + 10))
        else:
            # Draw placeholder if texture not found
            pygame.draw.rect(screen, (100, 100, 100), (preview_x + 10, preview_y + 10, preview_size - 20, preview_size - 20))
            placeholder_text = font.render("?", True, (255, 255, 255))
            screen.blit(placeholder_text, (preview_x + (preview_size - placeholder_text.get_width()) // 2, preview_y + (preview_size - placeholder_text.get_height()) // 2))
    
    # Navigation buttons (left/right arrows)
    arrow_size = 40
    left_arrow = pygame.Rect(preview_x - arrow_size - 20, preview_y + preview_size // 2 - arrow_size // 2, arrow_size, arrow_size)
    right_arrow = pygame.Rect(preview_x + preview_size + 20, preview_y + preview_size // 2 - arrow_size // 2, arrow_size, arrow_size)
    
    # Draw arrows
    pygame.draw.rect(screen, (100, 100, 200), left_arrow)
    pygame.draw.rect(screen, (100, 100, 200), right_arrow)
    pygame.draw.rect(screen, (255, 255, 255), left_arrow, 2)
    pygame.draw.rect(screen, (255, 255, 255), right_arrow, 2)
    
    # Arrow text
    left_text = font.render("←", True, (255, 255, 255))
    right_text = font.render("→", True, (255, 255, 255))
    screen.blit(left_text, (left_arrow.x + 15, left_arrow.y + 8))
    screen.blit(right_text, (right_arrow.x + 15, right_arrow.y + 8))
    
    # Store arrow rects for click detection
    global left_arrow_btn, right_arrow_btn
    left_arrow_btn = left_arrow
    right_arrow_btn = right_arrow
    
    # Select/Unlock button
    button_y = preview_y + preview_size + 100
    if character_manager:
        if current_char['unlocked']:
            if current_char['name'] == character_manager.get_current_character_name():
                # Already selected
                select_text = "Selected"
                button_color = (100, 100, 100)
            else:
                # Can select
                select_text = "Select"
                button_color = (100, 200, 100)
        else:
            # Can unlock
            can_afford = coins_manager.can_afford(current_char['price']) if coins_manager else False
            if can_afford:
                select_text = "Unlock"
                button_color = (255, 165, 0)
            else:
                select_text = "Not Enough Coins"
                button_color = (150, 150, 150)
    
    select_button = pygame.Rect(shop_x + (shop_width - 120) // 2, button_y, 120, 40)
    pygame.draw.rect(screen, button_color, select_button)
    pygame.draw.rect(screen, (255, 255, 255), select_button, 2)
    
    select_text_surface = font.render(select_text, True, (255, 255, 255))
    text_x = select_button.x + (select_button.width - select_text_surface.get_width()) // 2
    text_y = select_button.y + (select_button.height - select_text_surface.get_height()) // 2
    screen.blit(select_text_surface, (text_x, text_y))
    
    # Store select button rect
    global select_btn
    select_btn = select_button
    
    # Skin Creator button
    skin_creator_button = pygame.Rect(shop_x + 20, button_y + 60, 150, 40)
    can_afford_skin_creator = coins_manager.can_afford(3000) if coins_manager else False
    skin_creator_color = (100, 100, 200) if can_afford_skin_creator else (100, 100, 100)
    pygame.draw.rect(screen, skin_creator_color, skin_creator_button)
    pygame.draw.rect(screen, (255, 255, 255), skin_creator_button, 2)
    
    skin_creator_text = font.render("🎨 Skin Creator", True, (255, 255, 255))
    text_x = skin_creator_button.x + (skin_creator_button.width - skin_creator_text.get_width()) // 2
    text_y = skin_creator_button.y + (skin_creator_button.height - skin_creator_text.get_height()) // 2
    screen.blit(skin_creator_text, (text_x, text_y))
    
    # Skin Creator price
    price_text = font.render("3000 coins", True, (255, 215, 0))
    screen.blit(price_text, (skin_creator_button.x, skin_creator_button.y + 45))
    
    # Store skin creator button rect
    global skin_creator_btn
    skin_creator_btn = skin_creator_button
    
    # Close button
    close_button = pygame.Rect(shop_x + shop_width - 80, shop_y + 20, 60, 30)
    pygame.draw.rect(screen, (200, 100, 100), close_button)
    pygame.draw.rect(screen, (255, 255, 255), close_button, 2)
    
    close_text = font.render("X", True, (255, 255, 255))
    close_text_x = close_button.x + (close_button.width - close_text.get_width()) // 2
    close_text_y = close_button.y + (close_button.height - close_text.get_height()) // 2
    screen.blit(close_text, (close_text_x, close_text_y))
    
    # Store close button rect
    global shop_close_button
    shop_close_button = close_button


def draw_skin_creator_ui():
    """Draw the skin creator interface"""
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Skin creator window
    creator_width = 800
    creator_height = 600
    creator_x = center_x(creator_width)
    creator_y = (SCREEN_HEIGHT - creator_height) // 2
    
    # Draw creator background
    pygame.draw.rect(screen, (40, 40, 80), (creator_x, creator_y, creator_width, creator_height))
    pygame.draw.rect(screen, (255, 215, 0), (creator_x, creator_y, creator_width, creator_height), 3)  # Gold border
    
    # Title
    title = BIG_FONT.render("🎨 Skin Creator", True, (255, 255, 255))
    screen.blit(title, (creator_x + 20, creator_y + 20))
    
    # Info text
    info_text = font.render("Create your own custom character skin!", True, (255, 255, 255))
    screen.blit(info_text, (creator_x + 20, creator_y + 70))
    
    # Canvas area
    canvas_size = 200
    canvas_x = creator_x + 50
    canvas_y = creator_y + 120
    
    # Draw canvas background
    pygame.draw.rect(screen, (60, 60, 100), (canvas_x, canvas_y, canvas_size, canvas_size))
    pygame.draw.rect(screen, (200, 200, 200), (canvas_x, canvas_y, canvas_size, canvas_size), 2)
    
    # Canvas grid (8x8 pixels)
    grid_size = canvas_size // 8
    for x in range(8):
        for y in range(8):
            grid_rect = pygame.Rect(canvas_x + x * grid_size, canvas_y + y * grid_size, grid_size, grid_size)
            pygame.draw.rect(screen, (80, 80, 120), grid_rect, 1)
    
    # Color palette
    palette_y = canvas_y + canvas_size + 20
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), 
              (255, 255, 255), (0, 0, 0), (128, 128, 128), (255, 165, 0), (128, 0, 128), (165, 42, 42)]
    
    for i, color in enumerate(colors):
        color_rect = pygame.Rect(canvas_x + i * 30, palette_y, 25, 25)
        pygame.draw.rect(screen, color, color_rect)
        pygame.draw.rect(screen, (255, 255, 255), color_rect, 1)
    
    # Buttons
    button_y = creator_y + creator_height - 80
    button_height = 40
    button_width = 120
    
    # Save button
    save_button = pygame.Rect(creator_x + 50, button_y, button_width, button_height)
    pygame.draw.rect(screen, (0, 100, 0), save_button)
    pygame.draw.rect(screen, (255, 255, 255), save_button, 2)
    save_text = font.render("💾 Save", True, (255, 255, 255))
    screen.blit(save_text, (save_button.centerx - save_text.get_width() // 2, save_button.centery - save_text.get_height() // 2))
    
    # Close button
    close_button = pygame.Rect(creator_x + creator_width - button_width - 50, button_y, button_width, button_height)
    pygame.draw.rect(screen, (200, 100, 100), close_button)
    pygame.draw.rect(screen, (255, 255, 255), close_button, 2)
    close_text = font.render("❌ Close", True, (255, 255, 255))
    screen.blit(close_text, (close_button.centerx - close_text.get_width() // 2, close_button.centery - close_text.get_height() // 2))
    
    # Store button rects for click detection
    global skin_creator_save_btn, skin_creator_close_btn
    skin_creator_save_btn = save_button
    skin_creator_close_btn = close_button


def draw_multiplayer_ui():
    """Draw the multiplayer interface"""
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Multiplayer window
    mp_width = 800
    mp_height = 600
    mp_x = center_x(mp_width)
    mp_y = (SCREEN_HEIGHT - mp_height) // 2
    
    # Draw multiplayer background
    pygame.draw.rect(screen, (40, 40, 80), (mp_x, mp_y, mp_width, mp_height))
    pygame.draw.rect(screen, (255, 215, 0), (mp_x, mp_y, mp_width, mp_height), 3)  # Gold border
    
    # Title
    title = BIG_FONT.render("🌐 Multiplayer", True, (255, 255, 255))
    screen.blit(title, (mp_x + 20, mp_y + 20))
    
    # Buttons
    button_y = mp_y + 100
    button_height = 60
    button_width = 300
    
    # Host Server button
    host_btn = pygame.Rect(mp_x + 50, button_y, button_width, button_height)
    pygame.draw.rect(screen, (0, 100, 0), host_btn)
    pygame.draw.rect(screen, (255, 255, 255), host_btn, 2)
    host_text = font.render("🏠 Host Server", True, (255, 255, 255))
    screen.blit(host_text, (host_btn.centerx - host_text.get_width() // 2, host_btn.centery - host_text.get_height() // 2))
    
    # Join Server button
    join_btn = pygame.Rect(mp_x + 50, button_y + 80, button_width, button_height)
    pygame.draw.rect(screen, (0, 0, 100), join_btn)
    pygame.draw.rect(screen, (255, 255, 255), join_btn, 2)
    join_text = font.render("🔗 Join Server", True, (255, 255, 255))
    screen.blit(join_text, (join_btn.centerx - join_text.get_width() // 2, join_btn.centery - join_text.get_height() // 2))
    
    # Back button
    back_btn = pygame.Rect(mp_x + 50, button_y + 160, button_width, button_height)
    pygame.draw.rect(screen, (100, 0, 0), back_btn)
    pygame.draw.rect(screen, (255, 255, 255), back_btn, 2)
    back_text = font.render("⬅️ Back to Title", True, (255, 255, 255))
    screen.blit(back_text, (back_btn.centerx - back_text.get_width() // 2, back_btn.centery - back_text.get_height() // 2))
    
    # Store button rects for click detection
    global mp_host_btn, mp_join_btn, mp_back_btn
    mp_host_btn = host_btn
    mp_join_btn = join_btn
    mp_back_btn = back_btn


def draw_host_server_ui():
    """Draw the host server interface"""
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Host server window
    host_width = 800
    host_height = 600
    host_x = center_x(host_width)
    host_y = (SCREEN_HEIGHT - host_height) // 2
    
    # Draw host server background
    pygame.draw.rect(screen, (40, 40, 80), (host_x, host_y, host_width, host_height))
    pygame.draw.rect(screen, (255, 215, 0), (host_x, host_y, host_width, host_height), 3)  # Gold border
    
    # Title
    title = BIG_FONT.render("🏠 Host Server", True, (255, 255, 255))
    screen.blit(title, (host_x + 20, host_y + 20))
    
    # Info text
    info_text = font.render("Select the world you want to host:", True, (255, 255, 255))
    screen.blit(info_text, (host_x + 20, host_y + 80))
    
    # World selection dropdown (simplified for now)
    world_text = font.render("World: Default World", True, (255, 255, 255))
    screen.blit(world_text, (host_x + 20, host_y + 120))
    
    # Buttons
    button_y = host_y + 200
    button_height = 50
    button_width = 200
    
    # Start Server button
    start_btn = pygame.Rect(host_x + 50, button_y, button_width, button_height)
    pygame.draw.rect(screen, (0, 100, 0), start_btn)
    pygame.draw.rect(screen, (255, 255, 255), start_btn, 2)
    start_text = font.render("🚀 Start Server", True, (255, 255, 255))
    screen.blit(start_text, (start_btn.centerx - start_text.get_width() // 2, start_btn.centery - start_text.get_height() // 2))
    
    # Back button
    back_btn = pygame.Rect(host_x + 300, button_y, button_width, button_height)
    pygame.draw.rect(screen, (100, 0, 0), back_btn)
    pygame.draw.rect(screen, (255, 255, 255), back_btn, 2)
    back_text = font.render("⬅️ Back", True, (255, 255, 255))
    screen.blit(back_text, (back_btn.centerx - back_text.get_width() // 2, back_btn.centery - back_text.get_height() // 2))
    
    # Store button rects for click detection
    global host_start_btn, host_back_btn
    host_start_btn = start_btn
    host_back_btn = back_btn


def draw_join_server_ui():
    """Draw the join server interface"""
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Join server window
    join_width = 800
    join_height = 600
    join_x = center_x(join_width)
    join_y = (SCREEN_HEIGHT - join_height) // 2
    
    # Draw join server background
    pygame.draw.rect(screen, (40, 40, 80), (join_x, join_y, join_width, join_height))
    pygame.draw.rect(screen, (255, 215, 0), (join_x, join_y, join_width, join_height), 3)  # Gold border
    
    # Title
    title = BIG_FONT.render("🔗 Join Server", True, (255, 255, 255))
    screen.blit(title, (join_x + 20, join_y + 20))
    
    # Server discovery info
    info_text = font.render("Searching for servers...", True, (255, 255, 255))
    screen.blit(info_text, (join_x + 20, join_y + 80))
    
    # Server list (placeholder)
    no_servers_text = font.render("No servers found", True, (128, 128, 128))
    screen.blit(no_servers_text, (join_x + 20, join_y + 120))
    
    # Buttons
    button_y = join_y + 200
    button_height = 50
    button_width = 200
    
    # Refresh button
    refresh_btn = pygame.Rect(join_x + 50, button_y, button_width, button_height)
    pygame.draw.rect(screen, (0, 0, 100), refresh_btn)
    pygame.draw.rect(screen, (255, 255, 255), refresh_btn, 2)
    refresh_text = font.render("🔄 Refresh", True, (255, 255, 255))
    screen.blit(refresh_text, (refresh_btn.centerx - refresh_text.get_width() // 2, refresh_btn.centery - refresh_text.get_height() // 2))
    
    # Back button
    back_btn = pygame.Rect(join_x + 300, button_y, button_width, button_height)
    pygame.draw.rect(screen, (100, 0, 0), back_btn)
    pygame.draw.rect(screen, (255, 255, 255), back_btn, 2)
    back_text = font.render("⬅️ Back", True, (255, 255, 255))
    screen.blit(back_text, (back_btn.centerx - back_text.get_width() // 2, back_btn.centery - back_text.get_height() // 2))
    
    # Store button rects for click detection
    global join_refresh_btn, join_back_btn
    join_refresh_btn = refresh_btn
    join_back_btn = back_btn


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

def open_shop():
    """Open the shop interface"""
    global shop_open
    shop_open = True

def close_shop():
    """Close the shop interface"""
    global shop_open
    shop_open = False

def open_skin_creator():
    """Open the skin creator interface"""
    global game_state
    game_state = GameState.SKIN_CREATOR
    update_pause_state()  # Pause time when opening skin creator
    print("🎨 Opening Skin Creator...")



def check_achievement(achievement_name, coin_reward, message):
    """Check and reward an achievement if it hasn't been earned yet"""
    global achievements
    
    if not achievements.get(achievement_name, False):
        achievements[achievement_name] = True
        if coins_manager:
            coins_manager.add_coins(coin_reward)
        show_message(f"🏆 {message} +{coin_reward} coins!")
        print(f"🏆 Achievement unlocked: {achievement_name} - {message} (+{coin_reward} coins)")
        return True
    return False

def handle_shop_click(mouse_pos):
    """Handle clicks in the character selection shop interface"""
    global current_character_index, player_coins
    
    if not shop_open:
        return
    
    # Check if close button was clicked
    if shop_close_button and shop_close_button.collidepoint(mouse_pos):
        close_shop()
        return
    
    # Check if left arrow was clicked
    if left_arrow_btn and left_arrow_btn.collidepoint(mouse_pos):
        if character_manager:
            current_character_index = (current_character_index - 1) % len(character_manager.available_characters)
            print(f"🎭 Left arrow clicked - switched to character: {character_manager.available_characters[current_character_index]['name']}")
        return
    
    # Check if right arrow was clicked
    if right_arrow_btn and right_arrow_btn.collidepoint(mouse_pos):
        if character_manager:
            current_character_index = (current_character_index + 1) % len(character_manager.available_characters)
            print(f"🎭 Right arrow clicked - switched to character: {character_manager.available_characters[current_character_index]['name']}")
        return
    
    # Check if select/unlock button was clicked
    if select_btn and select_btn.collidepoint(mouse_pos):
        if character_manager:
            current_char = character_manager.available_characters[current_character_index]
            print(f"🎭 Shop button clicked for character: {current_char['name']}")
            print(f"🎭 Character unlocked: {current_char['unlocked']}")
            print(f"🎭 Current selected character: {character_manager.get_current_character_name()}")
            
            if current_char['unlocked']:
                # Character is unlocked, select it
                print(f"🎭 Attempting to select: {current_char['name']}")
                success = character_manager.select_character(current_char['name'])
                print(f"🎭 After selection, selected_character is: {character_manager.get_current_character_name()}")
                if success:
                    # Force refresh the character display
                    force_refresh_character()
                    show_message(f"Character changed to {current_char['name']}!")
            else:
                # Character is locked, try to unlock it
                if player_coins >= current_char['price']:
                    success, cost = character_manager.unlock_character(current_char['name'], player_coins)
                    if success:
                        player_coins -= cost
                        show_message(f"Unlocked {current_char['name']} for {cost} coins!")
                        print(f"🎭 Character unlocked: {current_char['name']}")
                    else:
                        show_message("Not enough coins!")
                else:
                    show_message("Not enough coins!")
        return
    
    # Check if skin creator button was clicked
    if skin_creator_btn and skin_creator_btn.collidepoint(mouse_pos):
        if coins_manager and coins_manager.can_afford(3000):
            # Open skin creator
            open_skin_creator()
            coins_manager.spend_coins(3000)
            show_message("🎨 Skin Creator opened! Cost: 3000 coins")
        else:
            show_message("❌ Not enough coins! Need 3000 coins for Skin Creator")
        return


def handle_skin_creator_click(mouse_pos):
    """Handle clicks in the skin creator interface"""
    global game_state
    
    # Check if save button was clicked
    if skin_creator_save_btn and skin_creator_save_btn.collidepoint(mouse_pos):
        # Save the custom skin
        save_custom_skin()
        show_message("🎨 Custom skin saved!")
        return
    
    # Check if close button was clicked
    if skin_creator_close_btn and skin_creator_close_btn.collidepoint(mouse_pos):
        game_state = GameState.GAME
        update_pause_state()  # Resume time when closing skin creator
        return

def save_custom_skin():
    """Save the custom skin created by the player"""
    try:
        # Create custom skins directory if it doesn't exist
        custom_skins_dir = "../../../../player/custom"
        if not os.path.exists(custom_skins_dir):
            os.makedirs(custom_skins_dir)
        
        # Generate a unique filename
        timestamp = int(time.time())
        filename = f"custom_skin_{timestamp}.png"
        filepath = os.path.join(custom_skins_dir, filename)
        
        # For now, create a simple placeholder skin
        # In a full implementation, this would save the actual canvas data
        skin_surface = pygame.Surface((32, 32))
        skin_surface.fill((255, 255, 255))  # White background
        
        # Save the skin
        pygame.image.save(skin_surface, filepath)
        
        print(f"🎨 Custom skin saved to: {filepath}")
        show_message("🎨 Custom skin saved successfully!")
        
    except Exception as e:
        print(f"❌ Error saving custom skin: {e}")
        show_message("❌ Error saving skin!")

def handle_multiplayer_click(mouse_pos):
    """Handle clicks in the multiplayer interface"""
    global game_state
    
    # Check if host server button was clicked
    if mp_host_btn and mp_host_btn.collidepoint(mouse_pos):
        game_state = GameState.MULTIPLAYER
        update_pause_state()  # Pause time when entering host server
        return
    
    # Check if join server button was clicked
    if mp_join_btn and mp_join_btn.collidepoint(mouse_pos):
        game_state = GameState.MULTIPLAYER
        update_pause_state()  # Pause time when entering join server
        return
    
    # Check if back button was clicked
    if mp_back_btn and mp_back_btn.collidepoint(mouse_pos):
        game_state = GameState.TITLE
        update_pause_state()  # Resume time when returning to title
        return

def handle_host_server_click(mouse_pos):
    """Handle clicks in the host server interface"""
    global game_state
    
    # Check if start server button was clicked
    if host_start_btn and host_start_btn.collidepoint(mouse_pos):
        # Start the multiplayer server with current world name or default
        world_name = world_system.current_world_name if world_system.current_world_name else "Default World"
        start_multiplayer_server(world_name)
        return
    
    # Check if back button was clicked
    if host_back_btn and host_back_btn.collidepoint(mouse_pos):
        game_state = GameState.MULTIPLAYER
        update_pause_state()  # Resume time when returning to multiplayer
        return

def handle_join_server_click(mouse_pos):
    """Handle clicks in the join server interface"""
    global game_state
    
    # Check if refresh button was clicked
    if join_refresh_btn and join_refresh_btn.collidepoint(mouse_pos):
        # Refresh server list
        refresh_server_list()
        return
    
    # Check if back button was clicked
    if join_back_btn and join_back_btn.collidepoint(mouse_pos):
        game_state = GameState.MULTIPLAYER
        update_pause_state()  # Resume time when returning to multiplayer
        return

# REMOVED DUPLICATE FUNCTION DEFINITION - This was causing the argument mismatch error!
# The correct function is defined at line 1160: def start_multiplayer_server(world_name):

def refresh_server_list():
    """Refresh the list of available servers"""
    try:
        # For now, just show a message
        show_message("🔍 Refreshing server list...")
        print("🔍 Server discovery functionality coming soon!")
        
        # In a full implementation, this would:
        # 1. Scan the network for available servers
        # 2. Display found servers in the UI
        # 3. Allow players to select and join
        
    except Exception as e:
        print(f"❌ Error refreshing server list: {e}")
        show_message("❌ Failed to refresh servers!")


def handle_inventory_click(mouse_pos):
    """Handle clicks in the full inventory interface"""
    global inventory_close_button, inventory_drag_item, inventory_drag_from, current_inventory_tab
    
    # Check if close button was clicked
    if inventory_close_button and inventory_close_button.collidepoint(mouse_pos):
        game_state = GameState.GAME
        update_pause_state()  # Resume time when closing inventory
        return
    
    # Calculate inventory UI position
    inv_width, inv_height = 800, 600
    inv_x = center_x(inv_width)
    inv_y = (SCREEN_HEIGHT - inv_height) // 2
    
    # Check if inventory tabs were clicked
    # Inventory tab
    inventory_tab_rect = pygame.Rect(inv_x + 20, inv_y + 100, 120, 35)
    if inventory_tab_rect.collidepoint(mouse_pos):
        current_inventory_tab = "inventory"
        return
    
    # Crafting tab
    crafting_tab_rect = pygame.Rect(inv_x + 150, inv_y + 100, 120, 35)
    if crafting_tab_rect.collidepoint(mouse_pos):
        current_inventory_tab = "crafting"
        return
    
    # Check crafting buttons if in crafting tab
    if current_inventory_tab == "crafting":
        # Check craft button
        craft_btn = pygame.Rect(inv_x + 700, inv_y + 220, 70, 30)
        if craft_btn.collidepoint(mouse_pos):
            recipe_name = check_crafting_recipe(crafting_materials)
            if recipe_name:
                if craft_item(recipe_name):
                    print(f"⚒️ Successfully crafted {recipe_name}!")
                else:
                    print(f"❌ Failed to craft {recipe_name}")
            return
        
        # Check clear button
        clear_btn = pygame.Rect(inv_x + 700, inv_y + 260, 70, 30)
        if clear_btn.collidepoint(mouse_pos):
            clear_crafting()
            print("🧹 Cleared crafting grid")
            return
        
        # ENHANCED CRAFTING: Check crafting grid slots for drag-and-drop
        for row in range(3):
            for col in range(3):
                slot_x = inv_x + 500 + col * 60
                slot_y = inv_y + 160 + row * 60
                slot_rect = pygame.Rect(slot_x, slot_y, 50, 50)
                slot_index = row * 3 + col
                
                if slot_rect.collidepoint(mouse_pos):
                    # ENHANCED DRAG-AND-DROP: Handle dragged items to crafting area
                    if inventory_drag_item:
                        # Dropping item into crafting slot
                        old_item = crafting_materials[slot_index]
                        crafting_materials[slot_index] = inventory_drag_item
                        inventory_drag_item = old_item
                        if old_item:
                            inventory_drag_from = ("crafting", slot_index)
                        else:
                            inventory_drag_item = None
                            inventory_drag_from = None
                        print(f"⚒️ Placed {crafting_materials[slot_index]['type']} in crafting slot {slot_index}")
                    else:
                        # Picking up item from crafting slot
                        if crafting_materials[slot_index]:
                            inventory_drag_item = crafting_materials[slot_index]
                            inventory_drag_from = ("crafting", slot_index)
                            crafting_materials[slot_index] = None
                            print(f"⚒️ Picked up item from crafting slot {slot_index}")
                    return
    
    # Handle left click for drag and drop
    if pygame.mouse.get_pressed()[0]:  # Left mouse button
        # Check hotbar slots
        for i in range(9):
            slot_rect = inventory_hotbar_slot_rect(i, inv_x, inv_y)
            if slot_rect.collidepoint(mouse_pos):
                handle_inventory_slot_click("hotbar", i, mouse_pos)
                return
        
        # Check backpack slots
        for i in range(27):
            slot_rect = inventory_backpack_slot_rect(i, inv_x, inv_y)
            if slot_rect.collidepoint(mouse_pos):
                handle_inventory_slot_click("backpack", i, mouse_pos)
                return
        
        # Check armor slots
        for slot_name in ["helmet", "chestplate", "leggings", "boots"]:
            slot_rect = inventory_armor_slot_rect(slot_name, inv_x, inv_y)
            if slot_rect.collidepoint(mouse_pos):
                handle_inventory_slot_click("armor", slot_name, mouse_pos)
                return
    
    # Check if left arrow was clicked
    if left_arrow_btn and left_arrow_btn.collidepoint(mouse_pos):
        if character_manager:
            current_character_index = (current_character_index - 1) % len(character_manager.available_characters)
        return
    
    # Check if right arrow was clicked
    if right_arrow_btn and right_arrow_btn.collidepoint(mouse_pos):
        if character_manager:
            current_character_index = (current_character_index + 1) % len(character_manager.available_characters)
        return
    
    # Check if select/unlock button was clicked
    if select_btn and select_btn.collidepoint(mouse_pos):
        if character_manager:
            current_char = character_manager.available_characters[current_character_index]
            print(f"🎭 Shop button clicked for character: {current_char['name']}")
            print(f"🎭 Character unlocked: {current_char['unlocked']}")
            print(f"🎭 Current selected character: {character_manager.get_current_character_name()}")
            
            if current_char['unlocked']:
                # Character is unlocked, select it
                print(f"🎭 Attempting to select: {current_char['name']}")
                success = character_manager.select_character(current_char['name'])
                print(f"🎭 After selection, selected_character is: {character_manager.get_current_character_name()}")
                if success:
                    # Force refresh the character display
                    force_refresh_character()
                    show_message(f"Character changed to {current_char['name']}!")
            else:
                # Character is locked, try to unlock it
                if coins_manager and coins_manager.can_afford(current_char['price']):
                    success, cost = character_manager.unlock_character(current_char['name'], coins_manager.get_coins())
                    if success:
                        coins_manager.spend_coins(cost)
                        show_message(f"Unlocked {current_char['name']} for {cost} coins!")
                        print(f"🎭 Character unlocked: {current_char['name']}")
                    else:
                        show_message("Not enough coins!")
                else:
                    show_message("Not enough coins!")
        return

def handle_inventory_slot_click(slot_type, slot_idx, mouse_pos):
    """Handle clicks on inventory slots for drag and drop"""
    global inventory_drag_item, inventory_drag_from
    
    if slot_type == "hotbar":
        # Handle hotbar slot
        if inventory_drag_item:
            # Dropping item into hotbar
            if slot_idx < len(player["inventory"]):
                # Swap items
                old_item = player["inventory"][slot_idx]
                player["inventory"][slot_idx] = inventory_drag_item
                inventory_drag_item = old_item
                if old_item:
                    inventory_drag_from = ("hotbar", slot_idx)
                else:
                    inventory_drag_item = None
                    inventory_drag_from = None
            else:
                # Place item in empty slot
                while len(player["inventory"]) <= slot_idx:
                    player["inventory"].append(None)
                player["inventory"][slot_idx] = inventory_drag_item
                inventory_drag_item = None
                inventory_drag_from = None
        else:
            # Picking up item from hotbar
            if slot_idx < len(player["inventory"]) and player["inventory"][slot_idx]:
                inventory_drag_item = player["inventory"][slot_idx]
                inventory_drag_from = ("hotbar", slot_idx)
                player["inventory"][slot_idx] = None
    
    elif slot_type == "backpack":
        # Handle backpack slot
        if inventory_drag_item:
            # Dropping item into backpack
            if slot_idx < len(player["backpack"]):
                # Swap items
                old_item = player["backpack"][slot_idx]
                player["backpack"][slot_idx] = inventory_drag_item
                inventory_drag_item = old_item
                if old_item:
                    inventory_drag_from = ("backpack", slot_idx)
                else:
                    inventory_drag_item = None
                    inventory_drag_from = None
            else:
                # Place item in empty slot
                while len(player["backpack"]) <= slot_idx:
                    player["backpack"].append(None)
                player["backpack"][slot_idx] = inventory_drag_item
                inventory_drag_item = None
                inventory_drag_from = None
        else:
            # Picking up item from backpack
            if slot_idx < len(player["backpack"]) and player["backpack"][slot_idx]:
                inventory_drag_item = player["backpack"][slot_idx]
                inventory_drag_from = ("backpack", slot_idx)
                player["backpack"][slot_idx] = None
    
    elif slot_type == "armor":
        # Handle armor slot
        if inventory_drag_item:
            # Check if item is armor
            item_type = inventory_drag_item.get("type", "")
            if item_type.startswith("iron_"):
                # Dropping armor into slot
                old_armor = player["armor"].get(slot_idx)
                player["armor"][slot_idx] = inventory_drag_item
                inventory_drag_item = old_armor
                if old_armor:
                    inventory_drag_from = ("armor", slot_idx)
                else:
                    inventory_drag_item = None
                    inventory_drag_from = None
            else:
                # Not armor, can't equip
                show_message("That's not armor!")
        else:
            # Unequipping armor
            if player["armor"].get(slot_idx):
                inventory_drag_item = player["armor"][slot_idx]
                inventory_drag_from = ("armor", slot_idx)
                player["armor"][slot_idx] = None
    
    elif slot_type == "crafting":
        # Handle crafting slot
        if inventory_drag_item:
            # Dropping item into crafting slot
            old_item = crafting_materials[slot_idx]
            crafting_materials[slot_idx] = inventory_drag_item
            inventory_drag_item = old_item
            if old_item:
                inventory_drag_from = ("crafting", slot_idx)
            else:
                inventory_drag_item = None
                inventory_drag_from = None
        else:
            # Picking up item from crafting slot
            if crafting_materials[slot_idx]:
                inventory_drag_item = crafting_materials[slot_idx]
                inventory_drag_from = ("crafting", slot_idx)
                crafting_materials[slot_idx] = None
    
    # Clean up inventory
    normalize_inventory()
    normalize_backpack()

def normalize_backpack():
    """Remove trailing None entries from backpack"""
    global player
    if "backpack" not in player:
        player["backpack"] = []
    # Remove trailing Nones
    while player["backpack"] and player["backpack"][-1] is None:
        player["backpack"].pop()

# --- Carrot consumption from inventory ---
def consume_carrot_from_inventory():
    """Eat one carrot from the currently selected slot.
    - Always restores +1 to both health AND hunger (if below max).
    - Carrots are always consumed when eaten.
    """
    if player["selected"] >= len(player["inventory"]):
        return
    item = player["inventory"][player["selected"]]
    if not item or not isinstance(item, dict) or item.get("type") != "carrot" or item.get("count", 0) <= 0:
        return

    # Always restore health and hunger (if below max)
    if player["health"] < 10:
        player["health"] = min(10, player["health"] + 1)
    if player["hunger"] < 10:
        player["hunger"] = min(10, player["hunger"] + 1)

    # Always consume the carrot
        item["count"] -= 1
        if item["count"] <= 0:
        # Remove empty slot
            player["inventory"].pop(player["selected"])
    
    print(f"🥕 Ate carrot: Health={player['health']}, Hunger={player['hunger']}")


# --- Missing Update Functions ---
def update_daylight():
    global is_day, day_start_time, paused_time, day_count
    # Only update time when in the game state
    if game_state == GameState.GAME:
        # Change to 2 minutes (120 seconds) for day/night cycle
        if time.time() - day_start_time - paused_time >= 120:  # 2 minutes = 120 seconds
            is_day = not is_day
            day_start_time = time.time()
            paused_time = 0  # Reset paused time after day/night change
            
            # Increment day counter when switching to day
            if is_day:
                day_count += 1
                print(f"🌅 Day {day_count} has begun!")
            else:
                print(f"🌙 Night {day_count} has fallen!")

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

    # Check for first sleep achievement
    check_achievement("first_sleep", 20, "Slept in bed for the first time!")

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
    
    # Movement speed - now properly balanced for responsive gameplay
    base_speed = MOVE_SPEED if not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else SLOW_SPEED
    speed = base_speed  # Use the speed directly without frame-rate complications
    
    # Clamp speed to reasonable bounds
    speed = max(0.08, min(0.25, speed))
    
    # Update stamina based on climbing state
    update_stamina(is_climbing_without_ladder())

    # Horizontal movement intent - Use BOTH WASD and Arrow keys for movement AND character flipping
    move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]  # Left arrow OR A key
    move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]  # Right arrow OR D key
    
    # EXTREME ENGINEERING: Update facing direction based on movement intent
    # This allows both manual flipping (A/D) and automatic flipping during movement
    if move_left:
        player["facing_direction"] = -1  # Face left when moving left
    elif move_right:
        player["facing_direction"] = 1   # Face right when moving right
    
    # Store current position for next frame comparison
    player["last_x"] = player["x"]

    # Check for ladder at player position (current or feet)
    px, py = player["x"], player["y"]
    on_ladder = (get_block(int(px), int(py)) == "ladder" or
                 get_block(int(px), int(py + 0.9)) == "ladder")

    if on_ladder:
        # Gentle horizontal while on ladder
        if move_left:
            # Controlled horizontal step when exiting a ladder (use tile-based speed like ground)
            step = max(0.05, speed)  # ensure not too tiny when shift-slowed
            new_x = px - step * 0.9
            left_head = get_block(int(new_x), int(py))
            left_feet = get_block(int(new_x), int(py + 0.9))
            if is_non_solid_block(left_head) and is_non_solid_block(left_feet) and left_head != "bedrock" and left_feet != "bedrock":
                player["x"] = new_x
        if move_right:
            # Controlled horizontal step when exiting a ladder (use tile-based speed like ground)
            step = max(0.05, speed)
            new_x = px + step * 0.9
            right_head = get_block(int(new_x + 0.9), int(py))
            right_feet = get_block(int(new_x + 0.9), int(py + 0.9))
            if is_non_solid_block(right_head) and is_non_solid_block(right_feet) and right_head != "bedrock" and right_feet != "bedrock":
                player["x"] = new_x

        # Climb up/down cancels gravity
        climb_speed = 0.12  # Responsive ladder climbing
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
            # Check multiple points along the left edge for collision
            left_head_top = get_block(int(new_x), int(player["y"]))
            left_head_mid = get_block(int(new_x), int(player["y"] + 0.3))
            left_head_bottom = get_block(int(new_x), int(player["y"] + 0.6))
            left_feet = get_block(int(new_x), int(player["y"] + 0.9))
            
            # Only move if ALL collision points are clear
            if (is_non_solid_block(left_head_top) and is_non_solid_block(left_head_mid) and 
                is_non_solid_block(left_head_bottom) and is_non_solid_block(left_feet)):
                player["x"] = new_x

        if move_right:
            new_x = px + speed
            # Check multiple points along the right edge for collision
            right_head_top = get_block(int(new_x + 0.9), int(player["y"]))
            right_head_mid = get_block(int(new_x + 0.9), int(player["y"] + 0.3))
            right_head_bottom = get_block(int(new_x + 0.9), int(player["y"] + 0.6))
            right_feet = get_block(int(new_x + 0.9), int(player["y"] + 0.9))
            
            # Only move if ALL collision points are clear
            if (is_non_solid_block(right_head_top) and is_non_solid_block(right_head_mid) and 
                is_non_solid_block(right_head_bottom) and is_non_solid_block(right_feet)):
                player["x"] = new_x

        # Check for climbing without ladder (free climbing)
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and can_climb_without_ladder():
            # Free climbing - move up slowly
            climb_speed = 0.10  # Responsive free climbing
            target_y = player["y"] - climb_speed
            
            # Check if we can climb up (need air above)
            head_block = get_block(int(player["x"]), int(target_y))
            if is_non_solid_block(head_block) and head_block != "bedrock":
                player["y"] = target_y
                player["vel_y"] = 0  # Stop falling
                player["on_ground"] = False
                print(f"🧗 Free climbing! Stamina: {player['stamina']:.1f}")
            else:
                # Can't climb up, fall normally
                pass
        else:
            # Normal gravity when not climbing
            player["vel_y"] += GRAVITY
            if player["vel_y"] > MAX_FALL_SPEED:
                player["vel_y"] = MAX_FALL_SPEED

        # Normal fall speed
        next_y = player["y"] + player["vel_y"] / TILE_SIZE
        
        # Check collision at the target position (both head and feet)
        target_y = int(next_y + 1)
        
        # Check the entire player hitbox for collision (left, center, and right positions)
        left_head = get_block(int(player["x"]), target_y)
        center_head = get_block(int(player["x"] + 0.5), target_y)
        right_head = get_block(int(player["x"] + 0.9), target_y)
        
        left_feet = get_block(int(player["x"]), target_y)
        center_feet = get_block(int(player["x"] + 0.5), target_y)
        right_feet = get_block(int(player["x"] + 0.9), target_y)
        
        # Check if we're trying to move into a solid block anywhere in the hitbox
        if (not is_non_solid_block(left_head) or not is_non_solid_block(center_head) or not is_non_solid_block(right_head) or
            not is_non_solid_block(left_feet) or not is_non_solid_block(center_feet) or not is_non_solid_block(right_feet)):
            # Collision detected - stop falling and place player on top of the block
            player["vel_y"] = 0
            player["on_ground"] = True
            player["y"] = target_y - 1  # Position player on top of the block
        else:
            # No collision - continue falling
            player["on_ground"] = False
            player["y"] = next_y

    # Optional: disable jump while on ladder to avoid launch
    if keys[pygame.K_SPACE] and player.get("on_ground", False) and not on_ladder:
        # Check if there's a block above the player before jumping
        head_y = int(player["y"])
        head_block = get_block(int(player["x"]), head_y)
        head_block_right = get_block(int(player["x"] + 0.9), head_y)
        
        # Only jump if there's no solid block above
        if is_non_solid_block(head_block) and is_non_solid_block(head_block_right):
            # Strong, responsive jump
            player["vel_y"] = JUMP_STRENGTH

def load_world_data():
    """Load world data from the world system into the game"""
    global world_data, entities, player
    
    if not world_system.current_world_data:
        print("⚠️ No world data available to load")
        return False
    
    try:
        # Load world data
        world_data = world_system.current_world_data.get("blocks", {})
        entities = world_system.current_world_data.get("entities", [])
        
        # Load player data with validation
        player_data = world_system.current_world_data.get("player", {})
        if not isinstance(player_data, dict):
            print("⚠️ Invalid player data, using defaults")
            player_data = {}
        
        # Update player with loaded data, preserving any missing fields
        for key, value in player_data.items():
            if key in player:
                player[key] = value
        
        # Ensure critical player fields exist
        if "health" not in player or player["health"] <= 0:
            player["health"] = 10
        if "hunger" not in player or player["hunger"] <= 0:
            player["hunger"] = 100
        if "stamina" not in player:
            player["stamina"] = 100
        if "max_stamina" not in player:
            player["max_stamina"] = 100
        if "inventory" not in player:
            player["inventory"] = []
        if "backpack" not in player:
            player["backpack"] = []
        if "selected" not in player:
            player["selected"] = 0
        if "armor" not in player:
            player["armor"] = {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
        
        # Load world settings
        world_settings = world_system.current_world_data.get("world_settings", {})
        global is_day, day_start_time
        is_day = world_settings.get("day", True)
        day_start_time = time.time() if is_day else time.time() - 43200  # 12 hours if night
        
        print(f"🌍 World data loaded: {len(world_data)} blocks, {len(entities)} entities")
        print(f"👤 Player loaded: health={player['health']}, hunger={player['hunger']}, stamina={player['stamina']}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading world data: {e}")
        return False

def update_monsters():
    global entities
    
    # Balanced monster spawning at night from spawn points
    if not is_day:  # Only spawn monsters at night
        for pos, block_type in list(world_data.items()):
            if block_type == "monster_spawn":
                # Check if we're far enough from spawn (new terrain)
                x_str, y_str = pos.split(',')
                x, y = int(x_str), int(y_str)
                
                # Only spawn if player is exploring new terrain (reasonable distance from player)
                player_distance = abs(x - player["x"])
                if player_distance > 25 and player_distance < 100:  # Sweet spot for spawning
                    # Check total monster count globally
                    monster_count = sum(1 for mob in entities if mob["type"] == "monster")
                    if monster_count < 8:  # Increased limit to 8 monsters for better gameplay
                        # Check if there's already a monster nearby
                        monster_nearby = False
                        for mob in entities:
                            if mob["type"] == "monster":
                                dx = abs(mob["x"] - x)
                                if dx < 30:  # Increased spacing to 30 blocks
                                    monster_nearby = True
                                    break
                        
                        if not monster_nearby:
                            # Spawn balanced monster
                            entities.append({
                                "type": "monster",
                                "x": float(x),
                                "y": float(y),
                                "hp": 6,  # Balanced HP for fair combat
                                "cooldown": 0,
                                "image": monster_image
                            })
                            # Remove the spawn point so it doesn't spawn again
                            del world_data[pos]
                            print(f"👹 Night spawn: Monster spawned at ({x}, {y}) - Total: {monster_count + 1}/8")
                            break  # Only spawn one monster per update
    
    # Move and attack existing monsters
    for mob in entities[:]:
        if mob["type"] == "monster":
            # Ensure each monster has health
            if "hp" not in mob:
                mob["hp"] = 7

            dx = player["x"] - mob["x"]
            dy = player["y"] - mob["y"]
            dist = math.hypot(dx, dy)
            if dist > 0:
                # ENHANCED AI: Faster movement when player is detected nearby
                if dist < 5:  # Player is very close - aggressive pursuit
                    speed_x = 0.12  # 2x faster horizontal
                    speed_y = 0.08  # 2x faster vertical
                elif dist < 10:  # Player is close - moderate pursuit
                    speed_x = 0.09  # 1.5x faster
                    speed_y = 0.06  # 1.5x faster
                else:  # Player is far - normal speed
                    speed_x = 0.06  # Original speed
                    speed_y = 0.04  # Original speed
                
                mob["x"] += speed_x * dx / dist
                mob["y"] += speed_y * dy / dist

            # Ranged attack: throw rock projectiles every 1.5s
            mob["cooldown"] = mob.get("cooldown", 0) + 1
            if mob["cooldown"] >= 90:  # 1.5 seconds at 60 FPS
                mob["cooldown"] = 0
                if dist > 0:
                    entities.append({
                        "type": "rock_projectile",  # Changed to rock_projectile
                        "x": mob["x"],
                        "y": mob["y"],
                        "dx": 0.15 * dx / dist,  # Slightly slower for balance
                        "dy": 0.15 * dy / dist,
                        "damage": 2,  # Reduced damage to 2 hearts (4 HP)
                        "lifetime": 180  # 3 seconds lifetime
                    })
                    print(f"🪨 Monster threw a rock at player!")

            # Contact damage (3 hearts) but do NOT remove the monster
            if abs(player["x"] - mob["x"]) < 0.5 and abs(player["y"] - mob["y"]) < 1:
                damage = calculate_armor_damage_reduction(3)
                player["health"] -= damage
                damage_sound.play()
                if player["health"] <= 0:
                    show_death_screen()
        
        elif mob["type"] == "zombie":
            # Ensure each zombie has health
            if "hp" not in mob:
                mob["hp"] = 10
            
            # Simple walking AI - zombies can only walk, not fly
            dx = player["x"] - mob["x"]
            dy = player["y"] - mob["y"]
            dist = math.hypot(dx, dy)
            
            if dist > 0 and dist < 8:  # Only chase if player is close
                # ENHANCED AI: Zombies move faster when player is closer
                base_speed = 0.03
                if dist < 3:  # Player very close - zombie gets aggressive
                    zombie_speed = base_speed * 2.0  # 2x faster
                elif dist < 5:  # Player close - moderate speed boost
                    zombie_speed = base_speed * 1.5  # 1.5x faster
                else:
                    zombie_speed = base_speed  # Normal speed
                
                # Horizontal movement only (zombies can't fly)
                if abs(dx) > 0.5:
                    # Move horizontally towards player
                    new_x = mob["x"] + zombie_speed * (1 if dx > 0 else -1)
                    
                    # Check if the new position is walkable (not blocked by walls)
                    block_at_new_pos = get_block(int(new_x), int(mob["y"]))
                    block_below = get_block(int(new_x), int(mob["y"] + 1))
                    
                    if block_below in ["grass", "dirt", "stone"] and block_at_new_pos in [None, "air"]:
                        mob["x"] = new_x
                
                # Contact damage (2 hearts) when close
                if abs(player["x"] - mob["x"]) < 0.8 and abs(player["y"] - mob["y"]) < 1:
                    damage = calculate_armor_damage_reduction(2)
                    player["health"] -= damage
                    damage_sound.play()
                if player["health"] <= 0:
                    show_death_screen()

    # Projectiles step and collision
    for proj in entities[:]:
        if proj["type"] == "projectile":
            proj["x"] += proj["dx"]
            proj["y"] += proj["dy"]
            if abs(player["x"] - proj["x"]) < 0.5 and abs(player["y"] - proj["y"]) < 0.5:
                base_damage = proj.get("damage", 3)
                damage = calculate_armor_damage_reduction(base_damage)
                player["health"] -= damage
                damage_sound.play()
                entities.remove(proj)
                if player["health"] <= 0:
                    show_death_screen()
            elif proj["x"] < -100 or proj["x"] > 100 or proj["y"] > 100:
                entities.remove(proj)
        
        # Rock projectile update and collision
        elif proj["type"] == "rock_projectile":
            # Update position
            proj["x"] += proj["dx"]
            proj["y"] += proj["dy"]
            
            # Check collision with player
            if abs(player["x"] - proj["x"]) < 0.5 and abs(player["y"] - proj["y"]) < 0.5:
                base_damage = proj.get("damage", 2)
                damage = calculate_armor_damage_reduction(base_damage)
                player["health"] -= damage
                damage_sound.play()
                entities.remove(proj)
                print(f"💥 Rock projectile hit player! Damage: {damage}")
                if player["health"] <= 0:
                    show_death_screen()
            
            # Check lifetime and boundaries
            proj["lifetime"] = proj.get("lifetime", 180) - 1
            if (proj["lifetime"] <= 0 or 
                proj["x"] < -100 or proj["x"] > 100 or 
                proj["y"] > 100):
                entities.remove(proj)


# --- Villager update logic ---
def update_hunger():
    """Update hunger system - decrease hunger every 200 seconds"""
    global hunger_timer, paused_time
    # Only update hunger when in the game state
    if game_state == GameState.GAME:
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
    if game_state != GameState.GAME and last_pause_time is None:
        last_pause_time = time.time()

def resume_game_time():
    """Resume the game time when returning to the game state"""
    global last_pause_time, paused_time
    if game_state == GameState.GAME and last_pause_time is not None:
        paused_time += time.time() - last_pause_time
        last_pause_time = None

def update_pause_state():
    """Update pause state based on current game state"""
    if game_state == GameState.GAME:
        resume_game_time()
    else:
        pause_game_time()

def update_villagers():
    """EXTREME ENGINEERING: Advanced villager AI with personality-based behavior, movement, and interaction"""
    for v in entities:
        if v.get("type") != "villager":
            continue
            
        # EXTREME ENGINEERING: Personality-based movement patterns
        personality = v.get("personality", "friendly")
        movement_speed = 0.03  # Base movement speed
        
        # Adjust movement based on personality
        if personality == "energetic":
            movement_speed = 0.06  # Fast movement
        elif personality == "shy":
            movement_speed = 0.015  # Slow, cautious movement
        elif personality == "grumpy":
            movement_speed = 0.02  # Slow, reluctant movement
        
        # EXTREME ENGINEERING: Smart movement AI
        v["step"] = v.get("step", 0) + 1
        v["movement_timer"] = v.get("movement_timer", 0) + 1
        
        # Change direction based on personality and environment
        if v["step"] % 180 == 0 and random.random() < 0.5:
            # Personality affects direction change frequency
            if personality == "energetic" and random.random() < 0.7:
                v["dir"] = -v.get("dir", 1)  # Energetic villagers change direction more
            elif personality == "shy" and random.random() < 0.3:
                v["dir"] = -v.get("dir", 1)  # Shy villagers change direction less
            else:
                v["dir"] = -v.get("dir", 1)
        
        dirn = v.get("dir", 1)
        
        # EXTREME ENGINEERING: Home-based wandering (villagers stay near their homes)
        home_x = v.get("home_x", v["x"])
        home_y = v.get("home_y", v["y"])
        wander_radius = v.get("wander_radius", 5)
        
        # Check if villager is too far from home
        distance_from_home = abs(v["x"] - home_x)
        if distance_from_home > wander_radius:
            # Turn back toward home
            if v["x"] > home_x:
                v["dir"] = -1
            else:
                v["dir"] = 1
        
        # desired next position
        nx = v["x"] + movement_speed * dirn
        
        # EXTREME ENGINEERING: Advanced collision detection
        # tiles at head/feet
        head = get_block(int(nx + (0.9 if dirn > 0 else 0.0)), int(v["y"]))
        feet = get_block(int(nx + (0.9 if dirn > 0 else 0.0)), int(v["y"] + 0.9))
        ground_ahead = get_block(int(nx + (0.9 if dirn > 0 else 0.0)), int(v["y"] + 1))
        
        # avoid solid walls and cliffs
        if is_non_solid_block(head) and is_non_solid_block(feet):
            # avoid stepping into gaps (no ground ahead)
            if ground_ahead is None:
                v["dir"] = -dirn
            else:
                v["x"] = nx
        else:
            v["dir"] = -dirn
        
        # EXTREME ENGINEERING: Gravity system (very light so they stay on ground)
        below = get_block(int(v["x"]), int(v["y"] + 1))
        if below is None:
            v["y"] += 0.10
        else:
            v["y"] = float(int(v["y"]))
        
        # EXTREME ENGINEERING: Villager mood changes over time
        if v["movement_timer"] % 600 == 0:  # Every 10 seconds
            mood_changes = {
                "friendly": ["happy", "neutral", "happy"],
                "grumpy": ["slightly_annoyed", "neutral", "slightly_annoyed"],
                "wise": ["neutral", "happy", "neutral"],
                "curious": ["happy", "curious", "happy"],
                "shy": ["neutral", "slightly_annoyed", "neutral"],
                "energetic": ["happy", "happy", "energetic"]
            }
            v["mood"] = random.choice(mood_changes.get(personality, ["neutral"]))
        
        # EXTREME ENGINEERING: Villager interaction cooldown
        if v.get("dialogue_cooldown", 0) > 0:
            v["dialogue_cooldown"] -= 1


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
    print(f"🌍 World width: {world_width}, Start X: {start_x}")
    print(f"🌍 Generating from X={start_x - world_width//2} to X={start_x + world_width//2}")
    
    # Generate terrain with clean layering - ALL FLAT
    for x in range(start_x - world_width//2, start_x + world_width//2):
        # EVERYTHING is completely flat at Y=10
        ground_y = 10  # Fixed height for entire world
        
        # CLEAN LAYER GENERATION - Stone closer to surface for building
        # Surface: Y=10 (grass)
        # Dirt: Y=11-12 (2 blocks deep)
        # Stone: Y=13-21 (9 blocks deep, starts at Y=13)
        # Bedrock: Y=22
        
        # 1. GRASS LAYER (Surface) - CRITICAL: This MUST work!
        set_block(x, ground_y, "grass")
        print(f"🌱 Placed grass at ({x}, {ground_y})")
        
        # 2. DIRT LAYER (Below grass, always 2 blocks deep)
        for y in range(ground_y + 1, ground_y + 3):
            set_block(x, y, "dirt")
        
        # 3. STONE LAYER (Below dirt, starts closer to surface)
        for y in range(ground_y + 3, ground_y + 12):
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
        bedrock_y = 127  # Fixed bedrock level (bottom of screen)
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
            chest_system.generate_chest_loot("village")
    
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
    print(f"Clean terrain: Grass (Y=10) → Dirt (Y=11-12) → Stone (Y=13-21) → Bedrock (Y=22)")
    print(f"Surface height: Y=10 (completely flat)")
    print(f"Stone starts at Y=13 (3 blocks below surface)")
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

# --- Virtual Keyboard and Username Creation ---
def create_virtual_keyboard():
    """Create a virtual keyboard layout for username input"""
    # Define keyboard layout (QWERTY)
    keyboard_layout = [
        ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
        ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
        ['z', 'x', 'c', 'v', 'b', 'n', 'm', 'backspace'],
        ['space', 'enter']
    ]
    
    # Calculate keyboard dimensions
    key_size = 40
    key_margin = 5
    row_height = key_size + key_margin
    
    # Calculate total width and height
    max_keys_in_row = max(len(row) for row in keyboard_layout)
    keyboard_width = max_keys_in_row * (key_size + key_margin) - key_margin
    keyboard_height = len(keyboard_layout) * row_height - key_margin
    
    # Center the keyboard
    keyboard_x = center_x(keyboard_width)
    keyboard_y = SCREEN_HEIGHT // 2 - keyboard_height // 2
    
    # Create key rectangles
    keys = {}
    y_offset = 0
    for row_idx, row in enumerate(keyboard_layout):
        x_offset = 0
        for key_idx, key in enumerate(row):
            # Center each row
            if key == 'backspace':
                key_w = key_size * 1.5
            elif key == 'space':
                key_w = key_size * 3
            elif key == 'enter':
                key_w = key_size * 1.5
            else:
                key_w = key_size
            
            key_x = keyboard_x + x_offset + (keyboard_width - len(row) * (key_size + key_margin) + key_margin) // 2
            key_y = keyboard_y + y_offset
            
            keys[key] = pygame.Rect(key_x, key_y, key_w, key_size)
            x_offset += key_w + key_margin
        y_offset += row_height
    
    return keys, keyboard_x, keyboard_y

def draw_username_creation_screen():
    """Draw the username creation screen with virtual keyboard"""
    global username_input, confirm_btn, back_btn
    
    screen.fill((0, 0, 128))  # Blue background
    
    # EXTREME ENGINEERING: Dynamic title and instructions based on username existence
    username_exists = False
    try:
        username_dir = os.path.join("../../../../../save_data", "username")
        username_file = os.path.join(username_dir, "username.json")
        if os.path.exists(username_file):
            with open(username_file, 'r') as f:
                file_data = json.load(f)
                username_exists = bool(file_data.get("username", "").strip())
    except Exception:
        username_exists = False
    
    # Dynamic title based on whether username exists
    if username_exists:
        title_text = BIG_FONT.render("Change Your Username", True, (255, 255, 255))
    else:
        title_text = BIG_FONT.render("Create Your Username", True, (255, 255, 255))
    screen.blit(title_text, (center_x(title_text.get_width()), 80))
    
    # Dynamic instructions based on whether username exists
    if username_exists:
        instruction_text = font.render("Click the keys to change your username (3-16 characters)", True, (255, 255, 255))
    else:
        instruction_text = font.render("Click the keys to create your username (3-16 characters)", True, (255, 255, 255))
    screen.blit(instruction_text, (center_x(instruction_text.get_width()), 130))
    
    # Show error message if any
    if username_error_message and pygame.time.get_ticks() < username_error_until:
        error_text = font.render(username_error_message, True, (255, 100, 100))
        screen.blit(error_text, (center_x(error_text.get_width()), 160))
    
    # Username input box
    input_box_width = 400
    input_box_height = 50
    input_box_x = center_x(input_box_width)
    input_box_y = 180
    
    # Draw input box background
    pygame.draw.rect(screen, (255, 255, 255), (input_box_x, input_box_y, input_box_width, input_box_height))
    pygame.draw.rect(screen, (0, 0, 0), (input_box_x, input_box_y, input_box_width, input_box_height), 3)
    
    # Draw username text
    if username_input:
        username_surface = font.render(username_input, True, (0, 0, 0))
        screen.blit(username_surface, (input_box_x + 10, input_box_y + 15))
    else:
        placeholder_text = font.render("Enter username...", True, (128, 128, 128))
        screen.blit(placeholder_text, (input_box_x + 10, input_box_y + 15))
    
    # Draw virtual keyboard
    keys, keyboard_x, keyboard_y = create_virtual_keyboard()
    
    # Draw each key
    for key, rect in keys.items():
        # Different colors for different key types
        if key == 'backspace':
            color = (255, 100, 100)  # Red
        elif key == 'space':
            color = (100, 255, 100)  # Green
        elif key == 'enter':
            color = (100, 100, 255)  # Blue
        else:
            color = (200, 200, 200)  # Gray
        
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
        
        # Draw key label
        if key == 'backspace':
            key_text = font.render("←", True, (0, 0, 0))
        elif key == 'space':
            key_text = font.render("SPACE", True, (0, 0, 0))
        elif key == 'enter':
            key_text = font.render("ENTER", True, (0, 0, 0))
        else:
            key_text = font.render(key.upper(), True, (0, 0, 0))
        
        # Center text on key
        text_x = rect.x + (rect.width - key_text.get_width()) // 2
        text_y = rect.y + (rect.height - key_text.get_height()) // 2
        screen.blit(key_text, (text_x, text_y))
    
    # Buttons
    btn_width, btn_height = 200, 50
    btn_y = SCREEN_HEIGHT - 100
    
    confirm_btn = centered_button(btn_y, btn_width, btn_height)
    back_btn = centered_button(btn_y + btn_height + 20, btn_width, btn_height)
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Check hover states
    confirm_hover = confirm_btn.collidepoint(mouse_pos)
    back_hover = back_btn.collidepoint(mouse_pos)
    
    # Draw buttons with hover effects
    if confirm_hover:
        # Bright hover color with glow effect
        base_color = (150, 150, 150)  # Lighter base
        border_color = (255, 255, 100)  # Golden border
    else:
        # Normal button colors
        base_color = (100, 100, 100)  # Normal base
        border_color = (255, 255, 255)  # White border
    
    # Draw confirm button
    pygame.draw.rect(screen, base_color, confirm_btn)
    pygame.draw.rect(screen, border_color, confirm_btn, 2)
    
    # Add glow effect for hover
    if confirm_hover:
        glow_rect = pygame.Rect(confirm_btn.x-2, confirm_btn.y-2, confirm_btn.width+4, confirm_btn.height+4)
        glow_surface = pygame.Surface((confirm_btn.width+4, confirm_btn.height+4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (255, 255, 100, 50), glow_surface.get_rect())
        screen.blit(glow_surface, glow_rect)
        pygame.draw.rect(screen, base_color, confirm_btn)
        pygame.draw.rect(screen, border_color, confirm_btn, 2)
    
    confirm_text = font.render("Confirm", True, (255, 255, 255))
    screen.blit(confirm_text, (confirm_btn.x + 10, confirm_btn.y + 10))
    
    # Draw back button
    if back_hover:
        base_color = (150, 150, 150)  # Lighter base
        border_color = (255, 255, 100)  # Golden border
    else:
        base_color = (100, 100, 100)  # Normal base
        border_color = (255, 255, 255)  # White border
    
    pygame.draw.rect(screen, base_color, back_btn)
    pygame.draw.rect(screen, border_color, back_btn, 2)
    
    # Add glow effect for hover
    if back_hover:
        glow_rect = pygame.Rect(back_btn.x-2, back_btn.y-2, back_btn.width+4, back_btn.height+4)
        glow_surface = pygame.Surface((back_btn.width+4, back_btn.height+4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (255, 255, 100, 50), glow_surface.get_rect())
        screen.blit(glow_surface, glow_rect)
        pygame.draw.rect(screen, base_color, back_btn)
        pygame.draw.rect(screen, border_color, back_btn, 2)
    
    back_text = font.render("Back", True, (255, 255, 255))
    screen.blit(back_text, (back_btn.x + 10, back_btn.y + 10))
    
    # Store keys for click detection
    global virtual_keys
    virtual_keys = keys

def draw_username_required_screen():
    """Draw the screen when username is required but not set"""
    global back_to_title_btn
    
    screen.fill((128, 0, 0))  # Red background to indicate error
    
    # Error message
    error_text = BIG_FONT.render("Username Required!", True, (255, 255, 255))
    screen.blit(error_text, (center_x(error_text.get_width()), 200))
    
    # Explanation
    explanation_text = font.render("You must create a username before playing.", True, (255, 255, 255))
    screen.blit(explanation_text, (center_x(explanation_text.get_width()), 280))
    
    explanation_text2 = font.render("Please return to the title screen to create one.", True, (255, 255, 255))
    screen.blit(explanation_text2, (center_x(explanation_text2.get_width()), 310))
    
    # Button
    back_to_title_btn = centered_button(400, 300, 60)
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    hover = back_to_title_btn.collidepoint(mouse_pos)
    
    # Draw button with hover effect
    if hover:
        base_color = (150, 150, 150)  # Lighter base
        border_color = (255, 255, 100)  # Golden border
    else:
        base_color = (100, 100, 100)  # Normal base
        border_color = (255, 255, 255)  # White border
    
    pygame.draw.rect(screen, base_color, back_to_title_btn)
    pygame.draw.rect(screen, border_color, back_to_title_btn, 2)
    
    # Add glow effect for hover
    if hover:
        glow_rect = pygame.Rect(back_to_title_btn.x-2, back_to_title_btn.y-2, back_to_title_btn.width+4, back_to_title_btn.height+4)
        glow_surface = pygame.Surface((back_to_title_btn.width+4, back_to_title_btn.height+4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (255, 255, 100, 50), glow_surface.get_rect())
        screen.blit(glow_surface, glow_rect)
        pygame.draw.rect(screen, base_color, back_to_title_btn)
        pygame.draw.rect(screen, border_color, back_to_title_btn, 2)
    
    btn_text = font.render("Back to Title", True, (255, 255, 255))
    screen.blit(btn_text, (back_to_title_btn.x + 10, back_to_title_btn.y + 10))

def validate_username(username):
    """Validate username (3-16 characters, alphanumeric + underscore)"""
    if len(username) < 3 or len(username) > 16:
        return False, "Username must be 3-16 characters long"
    
    # Check if username contains only letters, numbers, and underscores
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, "Username is valid"

def validate_world_seed(seed):
    """Validate world seed (max 20 characters, alphanumeric + spaces)"""
    if len(seed) > 20:
        return False, "Seed must be 20 characters or less"
    
    # Check if seed contains only letters, numbers, spaces, and common symbols
    import re
    if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', seed):
        return False, "Seed can only contain letters, numbers, spaces, hyphens, underscores, and periods"
    
    return True, "Seed is valid"

def set_global_username(username):
    """Set the global username for all worlds"""
    global GLOBAL_USERNAME, player
    GLOBAL_USERNAME = username
    player["username"] = username
    
    # Save username to JSON file
    save_username_to_file(username)

def save_username_to_file(username):
    """Save username to username.json file"""
    # Create username directory if it doesn't exist
    username_dir = os.path.join(SAVE_DIR, "username")
    if not os.path.exists(username_dir):
        os.makedirs(username_dir)
    
    # Save username to a JSON file for persistence
    try:
        username_data = {
            "username": username,
            "created": time.time(),
            "last_updated": time.time()
        }
        with open(os.path.join(username_dir, "username.json"), "w") as f:
            json.dump(username_data, f, indent=2)
        print(f"✅ Username saved to username.json: {username}")
    except Exception as e:
        print(f"⚠️ Could not save username: {e}")
        print(f"✅ Username set to: {username} (not saved)")

def backup_corrupted_save():
    """Backup corrupted save.json file and create a new one"""
    legacy_save_path = os.path.join(SAVE_DIR, "save.json")
    if os.path.exists(legacy_save_path):
        try:
            # Create backup with timestamp
            backup_name = f"save_corrupted_{int(time.time())}.json"
            backup_path = os.path.join(SAVE_DIR, backup_name)
            shutil.copy2(legacy_save_path, backup_path)
            print(f"💾 Backed up corrupted save.json to {backup_name}")
            
            # Remove the corrupted file
            os.remove(legacy_save_path)
            print("🗑️ Removed corrupted save.json")
            
        except Exception as e:
            print(f"⚠️ Could not backup corrupted save: {e}")
            # Try to remove anyway
            try:
                os.remove(legacy_save_path)
                print("🗑️ Removed corrupted save.json")
            except:
                print("⚠️ Could not remove corrupted save.json")

def check_username_required():
    """EXTREME ENGINEERING: Comprehensive username validation checking both memory and file system"""
    global GLOBAL_USERNAME
    
    # Check if username exists in memory
    if not GLOBAL_USERNAME or GLOBAL_USERNAME.strip() == "":
        print("🔍 Username check: No username in memory")
        return True
    
    # Check if username.json file exists and is valid
    try:
        username_dir = os.path.join("../../../../../save_data", "username")
        username_file = os.path.join(username_dir, "username.json")
        
        if not os.path.exists(username_file):
            print("🔍 Username check: username.json file not found")
            return True
        
        # Try to read and validate the username file
        with open(username_file, 'r') as f:
            file_data = json.load(f)
            file_username = file_data.get("username", "")
            
            if not file_username or file_username.strip() == "":
                print("🔍 Username check: username.json is empty or invalid")
                return True
            
            # Update global username if file has valid data
            if file_username != GLOBAL_USERNAME:
                print(f"🔄 Username check: Updating global username from file: {file_username}")
                GLOBAL_USERNAME = file_username
            
            print(f"✅ Username check: Valid username found: {GLOBAL_USERNAME}")
            return False
            
    except Exception as e:
        print(f"⚠️ Username check: Error reading username file: {e}")
        return True

def require_username_check():
    """EXTREME ENGINEERING: Check if username is required and redirect if needed"""
    global game_state
    if check_username_required():
        game_state = GameState.USERNAME_REQUIRED
        return True
    return False

def handle_virtual_keyboard_click(mouse_pos):
    """Handle clicks on virtual keyboard keys"""
    global username_input, virtual_keys
    
    for key, rect in virtual_keys.items():
        if rect.collidepoint(mouse_pos):
            if key == 'backspace':
                username_input = username_input[:-1] if username_input else ""
            elif key == 'space':
                if len(username_input) < 16:  # Max length
                    username_input += " "
            elif key == 'enter':
                # Validate and confirm username
                is_valid, message = validate_username(username_input)
                if is_valid:
                    set_global_username(username_input)
                    return "confirm"
                else:
                    show_username_error(message)
                    print(f"❌ {message}")
                    return "invalid"
            else:
                # Regular letter key
                if len(username_input) < 16:  # Max length
                    username_input += key
            break
    
    return "typing"

# --- Title Screen Drawing Function ---
def draw_title_screen():
    global play_btn, controls_btn, about_btn, options_btn, quit_btn, username_btn, shop_btn, multiplayer_btn
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw modern title screen
    button_states = modern_ui.draw_title_screen(mouse_pos)
    
    # Store button references for click handling
    play_btn = button_states.get("play")
    username_btn = button_states.get("username")
    multiplayer_btn = button_states.get("multiplayer")
    controls_btn = button_states.get("controls")
    about_btn = button_states.get("about")
    options_btn = button_states.get("options")
    quit_btn = button_states.get("quit")

# --- World Selection Screen Drawing Function ---
def draw_world_selection_screen():
    """EXTREME ENGINEERING: Draw the world selection screen with username validation"""
    global world_play_btn, world_delete_btn, world_create_btn, world_back_btn
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Check if username is required
    username_required = check_username_required()
    
    # Draw world selection screen with username validation
    button_states = world_ui.draw_world_selection(mouse_pos, username_required)
    
    # Store button references for click handling
    world_play_btn = button_states.get("play_world")
    world_delete_btn = button_states.get("delete_world")
    world_create_btn = button_states.get("create_world")
    world_back_btn = button_states.get("back")

# --- Game Menu Drawing Function ---
def draw_game_menu():
    global resume_btn, quit_btn, save_btn
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw modern pause menu
    button_states = modern_ui.draw_pause_menu(mouse_pos)
    
    # Store button references for click handling
    resume_btn = button_states.get("resume")
    save_btn = button_states.get("save")
    quit_btn = button_states.get("quit")

# --- Multiplayer Screen Drawing Function ---
def draw_multiplayer_screen():
    """Draw the multiplayer menu screen"""
    screen.fill((0, 0, 64))  # Dark blue background
    
    # Title
    title_text = BIG_FONT.render("🌐 Multiplayer", True, (255, 255, 255))
    screen.blit(title_text, (center_x(title_text.get_width()), 80))
    
    # Buttons
    button_y = 200
    button_height = 50
    button_width = 300
    
    # Host Server button
    host_rect = pygame.Rect(center_x(button_width), button_y, button_width, button_height)
    pygame.draw.rect(screen, (0, 100, 0), host_rect)
    pygame.draw.rect(screen, (255, 255, 255), host_rect, 2)
    host_text = font.render("🏠 Host Server", True, (255, 255, 255))
    screen.blit(host_text, (host_rect.centerx - host_text.get_width() // 2, host_rect.centery - host_text.get_height() // 2))
    
    # Join Server button
    join_rect = pygame.Rect(center_x(button_width), button_y + 70, button_width, button_height)
    pygame.draw.rect(screen, (0, 0, 100), join_rect)
    pygame.draw.rect(screen, (255, 255, 255), join_rect, 2)
    join_text = font.render("🔗 Join Server", True, (255, 255, 255))
    screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))
    
    # Back button
    back_rect = pygame.Rect(center_x(button_width), button_y + 140, button_width, button_height)
    pygame.draw.rect(screen, (100, 0, 0), back_rect)
    pygame.draw.rect(screen, (255, 255, 255), back_rect, 2)
    back_text = font.render("⬅️ Back", True, (255, 255, 255))
    screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))
    
    # Store button references for click handling
    global multiplayer_host_btn, multiplayer_join_btn, multiplayer_back_btn
    multiplayer_host_btn = host_rect
    multiplayer_join_btn = join_rect
    multiplayer_back_btn = back_rect

# --- Main Game Loop ---
# Add game menu toggle state
STATE_MENU = "menu"
STATE_MULTIPLAYER = "multiplayer"

running = True

# Crafting system variables
current_inventory_tab = "inventory"
crafting_materials = [None] * 9  # 3x3 grid

# Initialize character manager BEFORE loading game data
initialize_character_manager()

# Initialize GIF animation system
load_all_gif_animations()

# Initialize animation system
def initialize_animation_system():
    """Initialize the proper animation system"""
    global player_animator
    
    try:
        # Import the proper animation classes
        from templates_clean.temp_clean import ProperPlayerAnimator
        
        print("🎬 Setting up PROPER animation system...")
        player_animator = ProperPlayerAnimator()
        print("🎬 Animation system initialized with proper player animator")
        
    except Exception as e:
        print(f"⚠️ Animation system initialization failed: {e}")
        player_animator = None

initialize_animation_system()

# Initialize chat system
initialize_chat_system()

# Initialize coins manager
initialize_coins_manager()

# Initialize enhanced systems
try:
    from system.chest_system import ChestSystem
except ImportError:
    print("⚠️ Warning: Chest system not available")
    ChestSystem = None

if ChestSystem:
    chest_system = ChestSystem()
else:
    chest_system = None

def print_chest_system_info():
    """Print information about the enhanced chest system"""
    print("📦 Enhanced Chest System Initialized!")
    print("   - Guaranteed items: Sword + Pickaxe in every chest")
    print("   - Chest types: Village, Fortress, Dungeon")
    print("   - Enhanced loot tables with better item distribution")
    print("   - Improved UI with guaranteed item highlighting")
    print("   - Better error handling and validation")

# Print chest system information
print_chest_system_info()

# Enhanced save function using world system with EXTREME ENGINEERING
def save_game():
    """EXTREME ENGINEERING: Save current game state using the world system with comprehensive validation and error handling"""
    try:
        # Validate world system state
        if not hasattr(world_system, 'current_world_name') or not world_system.current_world_name:
            print("⚠️ No world loaded, cannot save")
            return False
        
        print(f"💾 EXTREME ENGINEERING: Starting save process for world '{world_system.current_world_name}'")
        
        # EXTREME ENGINEERING: Prepare and validate save data
        save_data = {
            "name": world_system.current_world_name,
            "blocks": world_data.copy() if world_data else {},
            "entities": entities.copy() if entities else [],
            "player": player.copy() if player else {},
            "world_settings": {
                "time": time.time(),
                "day": is_day,
                "weather": "clear"
            }
        }
        
        # EXTREME ENGINEERING: Validate save data integrity
        print(f"   📊 Save data validation:")
        print(f"      - Blocks: {len(save_data['blocks'])} (type: {type(save_data['blocks'])})")
        print(f"      - Entities: {len(save_data['entities'])} (type: {type(save_data['entities'])})")
        print(f"      - Player: {type(save_data['player'])}")
        print(f"      - World settings: {type(save_data['world_settings'])}")
        
        # EXTREME ENGINEERING: Update world system with current data
        world_system.current_world_data = save_data
        
        # EXTREME ENGINEERING: Save using world system (no arguments needed)
        if world_system.save_world():
            print(f"✅ EXTREME ENGINEERING: Game saved successfully to world: {world_system.current_world_name}")
            print(f"   📊 Final save statistics:")
            print(f"      - Blocks saved: {len(save_data['blocks'])}")
            print(f"      - Entities saved: {len(save_data['entities'])}")
            print(f"      - Player data: {len(save_data['player'])} fields")
            print(f"      - Save time: {time.strftime('%H:%M:%S')}")
            return True
        else:
            print("❌ EXTREME ENGINEERING: Failed to save world using world system")
            return False
            
    except Exception as e:
        print(f"💥 EXTREME ENGINEERING ERROR in save_game: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_world_data():
    """Load world data from the world system into the game"""
    global world_data, entities, player
    
    if not world_system.current_world_data:
        print("⚠️ No world data available to load")
        return False
    
    try:
        # Load world data
        world_data = world_system.current_world_data.get("blocks", {})
        entities = world_system.current_world_data.get("entities", [])
        
        # Load player data with validation
        player_data = world_system.current_world_data.get("player", {})
        if not isinstance(player_data, dict):
            print("⚠️ Invalid player data, using defaults")
            player_data = {}
        
        # Update player with loaded data, preserving any missing fields
        for key, value in player_data.items():
            if key in player:
                player[key] = value
        
        # Ensure critical player fields exist
        if "health" not in player or player["health"] <= 0:
            player["health"] = 10
        if "hunger" not in player or player["hunger"] <= 0:
            player["hunger"] = 100
        if "stamina" not in player:
            player["stamina"] = 100
        if "max_stamina" not in player:
            player["max_stamina"] = 100
        if "inventory" not in player:
            player["inventory"] = []
        if "backpack" not in player:
            player["backpack"] = []
        if "selected" not in player:
            player["selected"] = 0
        if "armor" not in player:
            player["armor"] = {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
        
        # Load world settings
        world_settings = world_system.current_world_data.get("world_settings", {})
        global is_day, day_start_time
        is_day = world_settings.get("day", True)
        day_start_time = time.time() if is_day else time.time() - 43200  # 12 hours if night
        
        print(f"🌍 World data loaded: {len(world_data)} blocks, {len(entities)} entities")
        print(f"👤 Player loaded: health={player['health']}, hunger={player['hunger']}, stamina={player['stamina']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading world data: {e}")
        return False

# Crafting system functions
def check_crafting_recipe(materials):
    """Check if the given materials match any crafting recipe"""
    # Convert materials to a recipe key
    recipe_key = []
    for material in materials:
        if material:
            recipe_key.append(material.get("type", ""))
        else:
            recipe_key.append("")
    
    # Check against recipes
    for recipe_name, recipe in CRAFTING_RECIPES.items():
        if recipe["materials"] == recipe_key:
            return recipe_name
    return None

def craft_item(recipe_name):
    """Craft an item using the given recipe"""
    if recipe_name not in CRAFTING_RECIPES:
        return False
    
    recipe = CRAFTING_RECIPES[recipe_name]
    output = recipe["output"]
    
    # Add crafted item to inventory
    add_to_inventory(output["type"], output["count"])
    
    # Clear crafting materials
    clear_crafting()
    
    return True

def add_to_crafting(material, slot_index=None):
    """Add a material to the crafting grid"""
    if slot_index is None:
        # Find first empty slot
        for i, slot in enumerate(crafting_materials):
            if slot is None:
                slot_index = i
                break
    
    if slot_index is not None and slot_index < len(crafting_materials):
        crafting_materials[slot_index] = material

def remove_from_crafting(slot_index):
    """Remove a material from the crafting grid"""
    if 0 <= slot_index < len(crafting_materials):
        crafting_materials[slot_index] = None

def clear_crafting():
    """Clear all materials from the crafting grid"""
    global crafting_materials
    crafting_materials = [None] * 9

def update_player_animation():
    """Update the player animation based on current state"""
    global player_animator
    
    if not player_animator:
        return
    
    # Get player state for animation selection
    player_state = "idle"  # Default state
    
    # Check if player is moving
    if "last_x" not in player:
        player["last_x"] = player["x"]
        player["last_y"] = player["y"]
    
    # Calculate movement
    dx = abs(player["x"] - player["last_x"])
    dy = abs(player["y"] - player["last_y"])
    
    # Determine animation state
    if dy > 0.1:  # Player is falling or jumping
        if player["y"] > player["last_y"]:
            player_state = "fall"
        else:
            player_state = "jump"
    elif dx > 0.05:  # Player is walking
        player_state = "walking"
    else:
        player_state = "idle"
    
    # Update animation if state changed
    if hasattr(player_animator, 'current_animation_name') and player_animator.current_animation_name != player_state:
        player_animator.current_animation_name = player_state
        print(f"🎬 Animation state changed to: {player_state}")
    
    # Update animation frame
    if hasattr(player_animator, 'update'):
        # Get facing direction from player
        facing_direction = player.get("facing_direction", 1)
        
        # Create player state dictionary for animation system
        player_state_dict = {
            "x": player["x"],
            "y": player["y"],
            "vel_y": player.get("vel_y", 0),
            "facing_right": facing_direction == 1,
            "breaking": False,  # TODO: Add breaking state
            "placing": False,   # TODO: Add placing state
            "attacking": False  # TODO: Add attacking state
        }
        player_animator.update(0.016, player_state_dict)  # 0.016 = ~60 FPS
    
    # Store current position for next frame
    player["last_x"] = player["x"]
    player["last_y"] = player["y"]

# Crafting recipes
CRAFTING_RECIPES = {
    # Tools & Weapons - REALISTIC ONLY
    "iron_sword": {
        "materials": ["iron", "", "", "iron", "", "", "stick", "", ""],
        "output": {"type": "sword", "count": 1}
    },
    "iron_pickaxe": {
        "materials": ["iron", "iron", "iron", "", "stick", "", "", "stick", ""],
        "output": {"type": "pickaxe", "count": 1}
    },
    "stone_sword": {
        "materials": ["stone", "", "", "stone", "", "", "stick", "", ""],
        "output": {"type": "stone_sword", "count": 1}
    },
    "stone_pickaxe": {
        "materials": ["stone", "stone", "stone", "", "stick", "", "", "stick", ""],
        "output": {"type": "pickaxe", "count": 1}
    },
    
    # Food - REALISTIC ONLY
    "bread": {
        "materials": ["wheat", "wheat", "wheat", "", "", "", "", "", ""],
        "output": {"type": "bread", "count": 1}
    },
    
    # Armor - REALISTIC CRAFTED ITEMS
    "iron_helmet": {
        "materials": ["iron", "iron", "iron", "iron", "", "iron", "", "", ""],
        "output": {"type": "iron_helmet", "count": 1}
    },
    "iron_chestplate": {
        "materials": ["iron", "", "iron", "iron", "iron", "iron", "iron", "iron", "iron"],
        "output": {"type": "iron_chestplate", "count": 1}
    },
    "iron_leggings": {
        "materials": ["iron", "iron", "iron", "iron", "", "iron", "iron", "", "iron"],
        "output": {"type": "iron_leggings", "count": 1}
    },
    "iron_boots": {
        "materials": ["iron", "", "iron", "", "", "", "iron", "", "iron"],
        "output": {"type": "iron_boots", "count": 1}
    },
    
    # Building Materials - REALISTIC PROCESSING ONLY
    "oak_planks": {
        "materials": ["log", "", "", "", "", "", "", "", ""],
        "output": {"type": "oak_planks", "count": 4}
    },
    "stick": {
        "materials": ["oak_planks", "", "", "oak_planks", "", "", "", "", ""],
        "output": {"type": "stick", "count": 4}
    },
    
    # Advanced Recipes - REALISTIC CONSTRUCTION
    "chest": {
        "materials": ["oak_planks", "oak_planks", "oak_planks", "oak_planks", "", "oak_planks", "oak_planks", "oak_planks", "oak_planks"],
        "output": {"type": "chest", "count": 1}
    },
    "door": {
        "materials": ["oak_planks", "oak_planks", "", "oak_planks", "oak_planks", "", "oak_planks", "oak_planks", ""],
        "output": {"type": "door", "count": 3}
    },
    
    # Smelting-like recipes (realistic material processing)
    "iron_ingot": {
        "materials": ["iron", "", "", "", "", "", "", "", ""],
        "output": {"type": "iron", "count": 1}
    }
}

def load_game():
    """Load game using improved world generation system"""
    global world_data, entities, player, is_day, day_start_time
    
    try:
        # Use the new world generation module
        try:
            from world_generation.world_gen import generate_world
        except ImportError:
            print("⚠️ Warning: Advanced world generation not available, using basic generation")
            generate_world = None
        
        print("🌍 Loading game with improved world generation...")
        
        # Generate world using the new system
        world_info = generate_world(seed=None, world_width=200)
        
        # Extract world data
        world_data = world_info["blocks"]
        entities = world_info["entities"]
        
        # Convert traveler blocks to entities (monsters will spawn at night)
        travelers_converted = 0
        for pos, block_type in list(world_data.items()):
            if block_type == "traveler":
                x_str, y_str = pos.split(',')
                x, y = int(x_str), int(y_str)
                entities.append({
                    "type": "traveler",
                    "x": float(x),
                    "y": float(y),
                    "hp": 5,
                    "dialogue": ["Hello, traveler!", "The world is dangerous at night...", "Be careful out there!"],
                    "image": player_image  # Use player image for travelers
                })
                del world_data[pos]  # Remove from blocks
                travelers_converted += 1
        
        print(f"🎮 Converted {travelers_converted} travelers to entities (monsters spawn at night)")
        
        # Set up player at spawn location
        spawn_x = world_info["spawn_x"]
        spawn_y = world_info["spawn_y"]
        
        player.update({
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
            "backpack": [],
            "selected": 0,
            "username": "Player",
            "armor": {"helmet": None, "chestplate": None, "leggings": None, "boots": None},
            "character_class": "default"
        })
        
        # Set world settings
        is_day = True
        day_start_time = time.time()
        
        print(f"🎉 Game loaded successfully!")
        print(f"  - Total blocks: {len(world_data)}")
        print(f"  - Player spawn: ({spawn_x}, {spawn_y})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading game: {e}")
        import traceback
        traceback.print_exc()
        return False

# Initialize multiplayer system
if MultiplayerUI:
    multiplayer_ui = MultiplayerUI(SCREEN_WIDTH, SCREEN_HEIGHT)
    multiplayer_ui.set_fonts(font, small_font, title_font)
else:
    multiplayer_ui = None

# Initialize modern UI system
try:
    from UI.modern_ui import ModernUI  # Note: UI folder is capitalized
except ImportError:
    print("⚠️ Warning: Modern UI not available")
    ModernUI = None
if ModernUI:
    modern_ui = ModernUI(screen, font, small_font, title_font, BIG_FONT)
else:
    modern_ui = None

# Initialize world system and UI
try:
    from system.world_system import WorldSystem
    from UI.world_ui import WorldUI  # Note: UI folder is capitalized
except ImportError:
    print("⚠️ Warning: World system/UI not available")
    WorldSystem = None
    WorldUI = None
if WorldSystem and WorldUI:
    world_system = WorldSystem()
    world_ui = WorldUI(screen, world_system, font, title_font)
else:
    world_system = None
    world_ui = None

# Game state variables
game_state = GameState.TITLE
# World creation variables removed - game goes directly to play
world_deletion_state = None  # None or world name to delete

# Button references for world creation and deletion
world_create_confirm_btn = None
world_create_back_btn = None
world_delete_btn = None
world_cancel_btn = None

# Error message system for world creation
world_create_error_message = ""
world_create_error_until = 0

# Load username - function removed, will be handled elsewhere

# Initialize pause state - start paused since we begin at title screen
update_pause_state()

# Add a frame counter to detect potential infinite loops
frame_count = 0
start_time = time.time()

# Add auto-save timer
last_auto_save = time.time()
AUTO_SAVE_INTERVAL = 300  # 5 minutes

def auto_save_game():
    """Auto-save the game if enough time has passed"""
    global last_auto_save
    
    current_time = time.time()
    if current_time - last_auto_save >= AUTO_SAVE_INTERVAL:
        if game_state == GameState.GAME:
            print("🔄 Auto-saving game...")
            if save_game():
                last_auto_save = current_time
                print("✅ Auto-save completed")
            else:
                print("❌ Auto-save failed")

# Main game loop
while running:
    frame_count += 1
    
    # Safety check: if we've been running for more than 10 seconds without user input, allow force quit
    if frame_count % 600 == 0:  # Check every 600 frames (about 10 seconds at 60 FPS)
        current_time = time.time()
        if current_time - start_time > 10:
            start_time = current_time  # Reset timer
    screen.fill((0, 191, 255) if is_day else (0, 0, 0))



    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print("🔄 Quit event received, closing game...")
            try:
                save_game()
                print("✅ Game saved successfully")
            except Exception as e:
                print(f"⚠️ Error saving game: {e}")
            running = False
            break
        # Auto-save every 5 minutes (300 seconds) to prevent losing progress
        if game_state == GameState.GAME and frame_count % 18000 == 0:  # 18000 frames = 5 minutes at 60 FPS
            try:
                save_game()
                print("💾 Auto-save completed")
            except Exception as e:
                print(f"⚠️ Auto-save failed: {e}")
        if event.type == pygame.VIDEORESIZE and not FULLSCREEN:
            # Remember new windowed size and reapply geometry
            WINDOWED_SIZE = (event.w, event.h)
            SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
            update_chest_ui_geometry()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == GameState.GAME:
                    # Auto-save when leaving game to prevent losing progress
                    try:
                        save_game()
                        print("💾 Auto-save when leaving game")
                    except Exception as e:
                        print(f"⚠️ Auto-save failed: {e}")
                    game_state = GameState.PAUSED
                    update_pause_state()  # Pause time when leaving game
                elif game_state == GameState.PAUSED:
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when returning to game



                elif game_state == GameState.INVENTORY:
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when closing inventory
            # Toggle fullscreen on F11
            if event.key == pygame.K_F11:
                FULLSCREEN = not FULLSCREEN
                apply_display_mode()
                update_chest_ui_geometry()
            # Toggle FPS display on F3
            if event.key == pygame.K_F3:
                show_fps = not show_fps
            
            # A and D keys now work through the movement system for both movement and character flipping
            
            # Test block breaking with B key
            if event.key == pygame.K_b:
                print("🧪 Manual block breaking test triggered!")
                test_block_breaking()
            
            # Nuclear option with N key
            if event.key == pygame.K_n:
                print("🚨 NUCLEAR OPTION TRIGGERED!")
                nuclear_block_removal()
            
            # Force quit with Ctrl+Q
            if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                print("🔄 Force quit with Ctrl+Q")
                running = False
                break
            # Close chest UI with E, U, or ESC
            if chest_open and event.key in (pygame.K_e, pygame.K_u, pygame.K_ESCAPE):
                close_chest_ui()
                continue
            # Open shop with P key
            if event.key == pygame.K_p:
                # Auto-save when opening shop to prevent losing progress
                if game_state == GameState.GAME:
                    try:
                        save_game()
                        print("💾 Auto-save when opening shop")
                    except Exception as e:
                        print(f"⚠️ Auto-save failed: {e}")
                open_shop()
                game_state = GameState.SHOP
                update_pause_state()  # Pause time when opening shop
                continue
            
            # Toggle chat with C key (and keep slash as alternative)
            if event.key == pygame.K_c and game_state == GameState.GAME:
                if chat_system:
                    chat_system.toggle_chat()
                continue
            
            # Toggle chat with slash key (alternative)
            if event.key == pygame.K_SLASH and game_state == GameState.GAME:
                if chat_system:
                    chat_system.toggle_chat()
                continue
            
            # Multiplayer chat with C key
            if event.key == pygame.K_c and game_state == GameState.GAME and is_connected:
                chat_active = True
                chat_input = ""
                continue
            
            # World creation handling removed - game goes directly to play
            
            # Handle chat input
            if chat_system and chat_system.is_chat_active():
                message = chat_system.handle_key_event(event)
                if message:
                    # Send chat message (in multiplayer, this would go to the server)
                    if chat_system:
                        chat_system.add_message("You", message, (0, 255, 0))
                    print(f"💬 Chat message: {message}")
                continue
            
            # Handle multiplayer chat input
            if chat_active and is_connected:
                if event.key == pygame.K_RETURN:
                    if chat_input.strip():
                        # Send chat message to server
                        send_chat_message(chat_input.strip())
                        chat_input = ""
                    chat_active = False
                    continue
                elif event.key == pygame.K_ESCAPE:
                    chat_active = False
                    chat_input = ""
                    continue
                elif event.key == pygame.K_BACKSPACE:
                    chat_input = chat_input[:-1]
                    continue
                elif event.unicode.isprintable():
                    if len(chat_input) < 100:  # Limit chat message length
                        chat_input += event.unicode
                    continue
            
            # Open/Close full inventory with T key
            if event.key == pygame.K_t:
                if game_state == GameState.GAME:
                    game_state = GameState.INVENTORY
                    update_pause_state()  # Pause time when opening inventory
                elif game_state == GameState.INVENTORY:
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when closing inventory
                continue
            
            # Restore stamina with R key (for testing)
            if event.key == pygame.K_r:
                if game_state == GameState.GAME:
                    restore_stamina(50)
                    show_message("Stamina restored!")
                continue
            # Shop navigation with arrow keys when shop is open
            if shop_open:
                if event.key == pygame.K_LEFT:
                    if character_manager:
                        current_character_index = (current_character_index - 1) % len(character_manager.available_characters)
                    continue
                elif event.key == pygame.K_RIGHT:
                    if character_manager:
                        current_character_index = (current_character_index + 1) % len(character_manager.available_characters)
                    continue
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Select/unlock current character
                    if character_manager:
                        current_char = character_manager.available_characters[current_character_index]
                        print(f"🎭 Keyboard selection for character: {current_char['name']}")
                        print(f"🎭 Character unlocked: {current_char['unlocked']}")
                        
                        if current_char['unlocked']:
                            print(f"🎭 Keyboard: Attempting to select: {current_char['name']}")
                            old_char = character_manager.get_current_character_name()
                            success = character_manager.select_character(current_char['name'])
                            new_char = character_manager.get_current_character_name()
                            print(f"🎭 Keyboard: Selection result: {success}")
                            print(f"🎭 Keyboard: Changed from {old_char} to {new_char}")
                            if success:
                                show_message(f"Character changed to {current_char['name']}!")
                                # Force refresh the character display
                                force_refresh_character()
                            else:
                                show_message("Character selection failed!")
                        else:
                            if player_coins >= current_char['price']:
                                success, cost = character_manager.unlock_character(current_char['name'], player_coins)
                                if success:
                                    player_coins -= cost
                                    show_message(f"Unlocked {current_char['name']} for {cost} coins!")
                                    print(f"🎭 Character unlocked: {current_char['name']}")
                                else:
                                    show_message("Not enough coins!")
                            else:
                                show_message("Not enough coins!")
                    continue
            
            # Username input handling
            if game_state == GameState.USERNAME_CREATE:
                if event.unicode.isprintable():
                    if len(username_input) < 16:  # Max 16 characters
                        username_input += event.unicode
                elif event.key == pygame.K_BACKSPACE:
                    username_input = username_input[:-1]
                elif event.key == pygame.K_RETURN:
                    # Validate username
                    is_valid, message = validate_username(username_input)
                    if is_valid:
                        set_global_username(username_input)
                        game_state = GameState.TITLE
                        update_pause_state()  # Resume time when returning to title
                    else:
                        show_username_error(message)
                        print(f"❌ {message}")
                elif event.key == pygame.K_ESCAPE:
                    game_state = GameState.TITLE
                    update_pause_state()  # Pause time when returning to title
            
            # World creation handling removed - game goes directly to play
            
            if event.key == pygame.K_SPACE and player["on_ground"]:
                player["vel_y"] = JUMP_STRENGTH
            if pygame.K_1 <= event.key <= pygame.K_9:
                player["selected"] = event.key - pygame.K_1
            


        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == GameState.GAME:
                mx, my = event.pos  # Define mx, my once for all mouse handling
                if chest_open:
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
                        
                # Handle mouse clicks for world interaction
                if event.button == 1:  # LEFT CLICK - Break blocks and attack monsters
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
                    print(f"🎯 Left click at ({mx}, {my}) - attempting to break blocks/attack monsters")
                    attack_monsters(mx, my)
                    break_block(mx, my)

                elif event.button == 3:  # RIGHT CLICK - Place blocks and open chests
                    # Convert mouse to world tile
                    bx, by = (mx + camera_x) // TILE_SIZE, (my + camera_y) // TILE_SIZE
                    
                    # Check if clicking on a chest to open it
                    block_at_pos = get_block(bx, by)
                    if block_at_pos == "chest":
                        # Check if player is within range (same as break_block)
                        px, py = int(player["x"]), int(player["y"])
                        if abs(bx - px) <= 2 and abs(by - py) <= 2:
                            open_chest_at(bx, by)
                            print(f"📦 Opening chest at ({bx}, {by})")
                        else:
                            print(f"📦 Chest too far away: player at ({px}, {py}), chest at ({bx}, {by})")
                        continue
                    
                    # Log interaction: right-click to convert to oak planks
                    if block_at_pos == "log":
                        # Convert log to oak planks
                        add_to_inventory("oak_planks", 4)  # 1 log = 4 planks
                        # Remove block completely from world data (turns into air)
                        if f"{bx},{by}" in world_data:
                            del world_data[f"{bx},{by}"]
                        show_message("🪵 Log converted to 4 oak planks!")
                        print("🪵 Log converted to 4 oak planks!")
                        continue
                    
                    # Try to place a block FIRST (this handles air placement)
                    if place_block(mx, my):
                        # Block was placed successfully, don't do other interactions
                        continue
                    
                    # If block placement failed, try other interactions
                    # Bed interaction: sleep at night, message at day
                    if get_block(bx, by) == "bed":
                        if not is_day:
                            sleep_in_bed()
                        else:
                            show_message("You can only sleep at night")
                        continue
                    
                    # Door interaction
                    if get_block(bx, by) == "door":
                        # Toggle door state
                        door_pos = (bx, by)
                        if door_pos not in door_states:
                            door_states[door_pos] = False  # Start closed
                        
                        door_states[door_pos] = not door_states[door_pos]
                        if door_states[door_pos]:
                            show_message("🚪 Door opened!")
                            print("🚪 Door opened at", door_pos)
                        else:
                            show_message("🚪 Door closed!")
                            print("🚪 Door closed at", door_pos)
                        continue
                    
                    # EXTREME ENGINEERING: Legend NPC interaction - initiate boss fight
                    for entity in entities:
                        if entity["type"] == "legend_npc":
                            entity_x = int(entity["x"] * TILE_SIZE)
                            entity_y = int(entity["y"] * TILE_SIZE) - 100
                            # Check if click is within Legend NPC bounds
                            if (bx * TILE_SIZE - camera_x <= entity_x + TILE_SIZE and 
                                bx * TILE_SIZE - camera_x + TILE_SIZE >= entity_x and
                                by * TILE_SIZE <= entity_y + TILE_SIZE and 
                                by * TILE_SIZE + TILE_SIZE >= entity_y):
                                
                                # EXTREME ENGINEERING: Legend NPC dialogue and boss fight initiation
                                if entity.get("dialogue_cooldown", 0) <= 0:
                                    show_message("🌟 THE LEGEND: 'You have traveled far, warrior. Are you ready for the ultimate challenge?'", 4000)
                                    show_message("🌟 THE LEGEND: 'Click me again to enter the BATTLE ARENA and face the LEGENDARY BOSS!'", 4000)
                                    
                                    # Set dialogue cooldown
                                    entity["dialogue_cooldown"] = 300  # 5 seconds
                                    entity["last_interaction"] = time.time()
                                    
                                    print("🌟 Legend NPC interaction - boss fight initiation available!")
                                    
                                    # Check for first Legend NPC interaction achievement
                                    check_achievement("first_legend_interaction", 100, "Met The Legend NPC!")
                                else:
                                    # Start boss fight on second click
                                    show_message("🌟 THE LEGEND: 'Entering BATTLE ARENA! Prepare for the LEGENDARY BOSS!'", 3000)
                                    start_boss_fight()
                                
                                continue
                    
                    # EXTREME ENGINEERING: Enhanced villager interaction with personality-based dialogue
                    for entity in entities:
                        if entity["type"] == "villager":
                            entity_x = int(entity["x"] * TILE_SIZE)
                            entity_y = int(entity["y"] * TILE_SIZE) - 100
                            # Check if click is within villager bounds
                            if (bx * TILE_SIZE - camera_x <= entity_x + TILE_SIZE and 
                                bx * TILE_SIZE - camera_x + TILE_SIZE >= entity_x and
                                by * TILE_SIZE <= entity_y + TILE_SIZE and 
                                by * TILE_SIZE + TILE_SIZE >= entity_y):
                                
                                # EXTREME ENGINEERING: Check dialogue cooldown
                                if entity.get("dialogue_cooldown", 0) <= 0:
                                    # Get personality-based dialogue
                                    dialogue = get_random_villager_dialogue(entity)
                                    show_villager_dialogue(dialogue, entity)
                                    
                                    # EXTREME ENGINEERING: Update villager state
                                    entity["dialogue_cooldown"] = 120  # 2 second cooldown
                                    entity["last_interaction"] = time.time()
                                    
                                    # EXTREME ENGINEERING: Mood changes based on interaction
                                    if random.random() < 0.3:  # 30% chance for mood change
                                        current_mood = entity.get("mood", "neutral")
                                        if current_mood == "slightly_annoyed":
                                            entity["mood"] = "neutral"
                                        elif current_mood == "neutral":
                                            entity["mood"] = "happy"
                                    
                                    print(f"🗣️ {entity.get('name', 'Villager')} ({entity.get('personality', 'friendly')}) says: {dialogue}")
                                    
                                    # Check for first villager talk achievement
                                    check_achievement("first_villager_talk", 15, "Talked to a villager for the first time!")
                                else:
                                    # Show cooldown message
                                    show_message(f"⏰ {entity.get('name', 'Villager')} is busy talking to someone else!")
                                
                                continue
                    
                    # If selected carrot, eat it; otherwise place block
                    if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]] and player["inventory"][player["selected"]]["type"] == "carrot":
                        consume_carrot_from_inventory()
            elif game_state == GameState.TITLE:
                if play_btn.collidepoint(event.pos):
                    # Check if username is required before allowing play
                    if require_username_check():
                        continue  # Don't proceed to game
                    
                    # Go to world selection screen instead of directly loading game
                    game_state = GameState.WORLD_SELECTION
                    update_pause_state()  # Pause time when leaving title
                    print("🌍 Opening world selection screen!")
                elif username_btn.collidepoint(event.pos):
                    # If changing username, save the current one first
                    if GLOBAL_USERNAME:
                        save_username_to_file(GLOBAL_USERNAME)
                        print(f"💾 Current username saved before change: {GLOBAL_USERNAME}")
                    game_state = GameState.USERNAME_CREATE
                    update_pause_state()  # Pause time when leaving title

                elif multiplayer_btn.collidepoint(event.pos):
                    game_state = GameState.MULTIPLAYER
                    update_pause_state()  # Pause time when leaving title
                elif controls_btn.collidepoint(event.pos):
                    game_state = GameState.CONTROLS
                    update_pause_state()  # Pause time when leaving title
                elif about_btn.collidepoint(event.pos):
                    game_state = GameState.ABOUT
                    update_pause_state()  # Pause time when leaving title
                elif options_btn.collidepoint(event.pos):
                    game_state = GameState.OPTIONS
                    update_pause_state()  # Pause time when leaving title
                elif quit_btn.collidepoint(event.pos):
                    save_game()
                    running = False
            elif game_state == GameState.WORLD_SELECTION:
                # Handle world selection screen clicks
                
                # First, check if user clicked on a world to select it
                world_click_result = world_ui.handle_world_click(event.pos)
                if world_click_result is not None:
                    print(f"🌍 World {world_click_result} selected!")
                    continue  # Skip other button checks for this click
                
                if world_back_btn and world_back_btn.collidepoint(event.pos):
                    game_state = GameState.TITLE
                    update_pause_state()  # Resume time when returning to title
                    print("⬅️ Returning to title screen from world selection")
                elif world_create_btn and world_create_btn.collidepoint(event.pos):
                    # EXTREME ENGINEERING: Username validation before world creation
                    if require_username_check():
                        print("🚫 Username required before creating world - redirecting to username creation")
                        continue  # Don't proceed to world creation
                    
                    # Create a new world
                    world_name = f"World {len(world_system.world_list) + 1}"
                    if world_system.create_world(world_name):
                        print(f"🌍 Created new world: {world_name}")
                        # Refresh world selection state
                        world_ui.refresh_world_selection()
                        # Load the newly created world
                        if world_system.load_world(world_name):
                            # Load the world data into the game
                            if load_world_data():
                                # Fix player spawn position to ensure surface spawning
                                fix_player_spawn_position()
                                game_state = GameState.GAME
                                update_pause_state()  # Resume time when entering game
                                print(f"🎮 Starting game with new world: {world_name}")
                                # give_starting_items()  # Removed starting items
                            else:
                                print("❌ Failed to load world data into game")
                        else:
                            print("❌ Failed to load newly created world")
                    else:
                        print("❌ Failed to create new world")
                elif world_play_btn and world_play_btn.collidepoint(event.pos):
                    # EXTREME ENGINEERING: Username validation before world play
                    if require_username_check():
                        print("🚫 Username required before playing - redirecting to username creation")
                        continue  # Don't proceed to game
                    
                    # Play selected world (if any world is selected)
                    selected_world = world_ui.get_selected_world()
                    if selected_world:
                        world_name = selected_world["name"]
                        if world_system.load_world(world_name):
                            # Load the world data into the game
                            if load_world_data():
                                # Fix player spawn position to ensure surface spawning
                                fix_player_spawn_position()
                                game_state = GameState.GAME
                                update_pause_state()  # Resume time when entering game
                                print(f"🎮 Starting game with world: {world_name}")
                                print("🎮 Controls: WASD or Arrow Keys = Move + Flip Character, Space = Jump")
                                # give_starting_items()  # Removed starting items
                            else:
                                print(f"❌ Failed to load world data for: {world_name}")
                        else:
                            print(f"❌ Failed to load world: {world_name}")
                    else:
                        print("❌ No world selected")
                elif world_delete_btn and world_delete_btn.collidepoint(event.pos):
                    # Delete selected world (if any world is selected)
                    selected_world = world_ui.get_selected_world()
                    if selected_world:
                        world_name = selected_world["name"]
                        if world_system.delete_world(world_name):
                            print(f"🗑️ Deleted world: {world_name}")
                            # Refresh the world selection screen and selection state
                            world_system._load_world_list()
                            world_ui.refresh_world_selection()
                        else:
                            print(f"❌ Failed to delete world: {world_name}")
                    else:
                        print("❌ No world selected")
            elif game_state == GameState.PAUSED:
                if resume_btn.collidepoint(event.pos):
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when returning to game
                    
                    # Give starting items if player doesn't have them
                    if not player["inventory"]:
                        give_starting_items()
                elif save_btn.collidepoint(event.pos):
                    if save_game():
                        show_message("✅ Game saved successfully!")
                    else:
                        show_message("❌ Failed to save game!")
                elif quit_btn.collidepoint(event.pos):
                    save_game()
                    game_state = GameState.TITLE
                    update_pause_state()  # Pause time when returning to title
            elif game_state == GameState.USERNAME_CREATE:
                # Handle virtual keyboard clicks
                if event.button == 1:  # Left click
                    result = handle_virtual_keyboard_click(event.pos)
                    if result == "confirm":
                        game_state = GameState.TITLE
                        update_pause_state()  # Resume time when returning to title
                        continue
                    elif result == "invalid":
                        continue  # Stay on username creation screen
                
                # Handle button clicks
                if confirm_btn and confirm_btn.collidepoint(event.pos):
                    # Validate username
                    is_valid, message = validate_username(username_input)
                    if is_valid:
                        set_global_username(username_input)
                        game_state = GameState.TITLE
                        update_pause_state()  # Resume time when returning to title
                    else:
                        show_username_error(message)
                        print(f"❌ {message}")
                elif back_btn and back_btn.collidepoint(event.pos):
                    game_state = GameState.TITLE
                    update_pause_state()  # Resume time when returning to title
            

                    
            elif game_state == GameState.USERNAME_CREATE:
                if back_to_title_btn and back_to_title_btn.collidepoint(event.pos):
                    game_state = GameState.TITLE
                    update_pause_state()  # Resume time when returning to title
                    
            elif game_state == GameState.USERNAME_REQUIRED:
                if back_to_title_btn and back_to_title_btn.collidepoint(event.pos):
                    game_state = GameState.TITLE
                    update_pause_state()  # Resume time when returning to title
                    
            elif game_state == GameState.OPTIONS:
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
                    game_state = GameState.TITLE
                    update_pause_state()  # Pause time when returning to title
            elif game_state in [GameState.CONTROLS, GameState.ABOUT]:
                if back_btn.collidepoint(event.pos):
                    game_state = GameState.TITLE
                    update_pause_state()  # Pause time when returning to title
            elif game_state == GameState.MULTIPLAYER:
                # EXTREME ENGINEERING: Professional multiplayer click handling
                if multiplayer_menu_state == "main":
                    if multiplayer_host_btn and multiplayer_host_btn.collidepoint(event.pos):
                        multiplayer_menu_state = "host"
                        print("🌐 Switching to host server menu")
                    elif multiplayer_join_btn and multiplayer_join_btn.collidepoint(event.pos):
                        multiplayer_menu_state = "join"
                        print("🔗 Switching to join server menu")
                    elif multiplayer_back_btn and multiplayer_back_btn.collidepoint(event.pos):
                        game_state = GameState.TITLE
                        update_pause_state()
                        print("⬅️ Returning to title screen from multiplayer")
                
                elif multiplayer_menu_state == "host":
                    if multiplayer_start_host_btn and multiplayer_start_host_btn.collidepoint(event.pos):
                        # Start hosting server with selected world
                        if start_multiplayer_server("Default World"):
                            game_state = GameState.GAME
                            update_pause_state()
                            show_message("🌐 Multiplayer server started! Players can now join!", 3000)
                            print("🌐 Multiplayer server started successfully")
                        else:
                            show_message("❌ Failed to start server")
                    elif multiplayer_host_back_btn and multiplayer_host_back_btn.collidepoint(event.pos):
                        multiplayer_menu_state = "main"
                        print("⬅️ Returning to multiplayer main menu")
                
                elif multiplayer_menu_state == "join":
                    if multiplayer_search_btn and multiplayer_search_btn.collidepoint(event.pos):
                        # Search for available servers
                        discover_servers()
                        multiplayer_menu_state = "server_list"
                        show_message("🔍 Searching for servers...", 2000)
                        print("🔍 Server search initiated")
                    elif multiplayer_join_back_btn and multiplayer_join_back_btn.collidepoint(event.pos):
                        multiplayer_menu_state = "main"
                        print("⬅️ Returning to multiplayer main menu")
                
                elif multiplayer_menu_state == "server_list":
                    if multiplayer_server_list_back_btn and multiplayer_server_list_back_btn.collidepoint(event.pos):
                        multiplayer_menu_state = "join"
                        print("⬅️ Returning to join server menu")
                    elif server_list:
                        # Check if player clicked on a server
                        for i, server in enumerate(server_list[:5]):
                            server_btn = pygame.Rect(100, 150 + i * 120, SCREEN_WIDTH - 200, 100)
                            if server_btn.collidepoint(event.pos):
                                # Join the selected server
                                if join_multiplayer_server(server):
                                    game_state = GameState.GAME
                                    update_pause_state()
                                    show_message(f"🔗 Joined server: {server['name']}!", 3000)
                                    print(f"🔗 Successfully joined server: {server['name']}")
                                else:
                                    show_message("❌ Failed to join server", 2000)
                                break
            elif game_state == GameState.SHOP:
                # Handle shop clicks
                handle_shop_click(event.pos)
                # Check if shop was closed
                if not shop_open:
                    game_state = GameState.TITLE
                    update_pause_state()  # Resume time when returning to title
            elif game_state == GameState.INVENTORY:
                # Handle inventory clicks
                handle_inventory_click(event.pos)
                continue
            elif game_state == GameState.SKIN_CREATOR:
                # Handle skin creator clicks
                handle_skin_creator_click(event.pos)
                continue
            elif game_state == GameState.MULTIPLAYER:
                # Handle multiplayer clicks
                handle_multiplayer_click(event.pos)
                continue
            elif game_state == GameState.MULTIPLAYER:
                # Handle host server clicks
                handle_host_server_click(event.pos)
                continue
            elif game_state == GameState.MULTIPLAYER:
                # Handle join server clicks
                handle_join_server_click(event.pos)
                continue
            # World selection states removed - game goes directly to play
            # All world management is now automatic
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
        
        elif event.type == pygame.MOUSEWHEEL:
            # Mouse wheel scrolling (can be used for other purposes later)
            pass
        
        # EXTREME ENGINEERING: Handle multiplayer chat input
        if multiplayer_mode:
            handle_chat_input(event)

    if game_state == GameState.GAME:
        # Update camera to follow player both horizontally and vertically
        target_camera_x = int((player["x"] * TILE_SIZE) - SCREEN_WIDTH // 2)
        target_camera_y = int((player["y"] * TILE_SIZE) - SCREEN_HEIGHT // 2)
        
        # Smooth camera follow for better platformer feel
        camera_x += (target_camera_x - camera_x) * 0.1  # Smooth horizontal follow
        camera_y += (target_camera_y - camera_y) * 0.1  # Smooth vertical follow
        
        # Ensure camera doesn't go above the world (keep ground visible)
        camera_y = max(camera_y, 0)
        
        # Infinite world generation: calculate terrain generation bounds
        left_edge = int((camera_x) // TILE_SIZE) - 8  # Increased buffer for smoother exploration
        right_edge = int((camera_x + SCREEN_WIDTH) // TILE_SIZE) + 8  # Increased buffer
        # Village check per 50‑column chunk
        chunk_left = left_edge // 50
        chunk_right = right_edge // 50
        for ch in range(chunk_left, chunk_right + 1):
            base_x = ch * 50
            # Generate structures for chunk
            maybe_generate_village_for_chunk(ch, base_x)
            maybe_generate_fortress_for_chunk(ch, base_x)
        for x in range(left_edge, right_edge):
            # CRITICAL FIX: Only generate terrain for columns that have NEVER been generated
            # This prevents broken blocks from being replaced by terrain regeneration
            if x not in generated_terrain_columns:
                # Show exploration progress every 50 blocks for infinite world feedback
                if x % 50 == 0:
                    print(f"🚀 INFINITE WORLD: Exploring new territory at X={x}")
                elif x % 10 == 0:
                    print(f"🌍 Generating terrain for column {x}")
                prev_heights = [y for y in range(0, 100) if (x - 1, y) in world_data and world_data[(x - 1, y)] == "grass"]
                if prev_heights:
                    ground_y = prev_heights[0]
                else:
                    # Infinite world: varied terrain generation for endless exploration
                    height_offset = int(4 * math.sin(x * 0.15) + 2 * math.cos(x * 0.3))
                    ground_y = 114 + height_offset  # Varied terrain height for infinite world

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
                set_block(x, 127, "bedrock")  # Bedrock at Y=127 (bottom)
                
                # Mark this column as generated so it won't be regenerated
                generated_terrain_columns.add(x)
                # Enhanced Trees with TWO logs (improved engineering)
                if random.random() < 0.08:  # Slightly reduced density for better spacing
                    # Place TWO logs above grass (improved tree structure)
                    set_block(x, ground_y - 1, "log")      # First log above grass
                    set_block(x, ground_y - 2, "log")      # Second log above first
                    
                    # Enhanced leaf canopy (3x3 rectangle above the two logs)
                    for dx in [-1, 0, 1]:  # Left, center, right
                        for dy in [-3, -4]:  # Above the two logs
                            set_block(x + dx, ground_y + dy, "leaves")
                    
                    # Add some random leaf variation for natural look
                    if random.random() < 0.3:  # 30% chance for extra leaves
                        extra_dx = random.choice([-2, 2])  # Left or right extension
                        extra_dy = random.choice([-3, -4])  # Above logs
                        set_block(x + extra_dx, ground_y + extra_dy, "leaves")

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
                    chest_system.generate_chest_loot("village")
                # EXTREME ENGINEERING: Balanced night monster spawning
                # Only spawn monsters at night when exploring new territory
                if not is_day and random.random() < 0.008:  # Slightly increased spawn rate for better gameplay
                    # Check total monster count globally to prevent overcrowding
                    total_monsters = sum(1 for entity in entities if entity["type"] == "monster")
                    
                    # Check if there are already monsters nearby to prevent clustering
                    nearby_monsters = 0
                    for entity in entities:
                        if entity["type"] == "monster":
                            distance = abs(entity["x"] - x)
                            if distance < 40:  # Within 40 blocks
                                nearby_monsters += 1
                    
                    # Balanced spawning: max 8 total monsters, max 1 per 40-block radius
                    if total_monsters < 8 and nearby_monsters == 0:
                        entities.append({
                            "type": "monster",
                            "x": x,
                            "y": ground_y - 1,
                            "image": monster_image,
                            "hp": 6,  # Balanced HP for fair combat
                            "cooldown": 0
                        })
                        print(f"👹 Night monster spawned at ({x}, {ground_y - 1}) - Total monsters: {total_monsters + 1}/8")
                
                        # EXTREME ENGINEERING: Check for Legend NPC spawn
        check_legend_npc_spawn()
        
        # EXTREME ENGINEERING: Controlled villager spawning - much less frequent
        if random.random() < 0.01:  # Reduced from 0.05 to 0.01 (5x less)
                    # Check for nearby villagers to prevent overcrowding
                    nearby_villagers = 0
                    for entity in entities:
                        if entity["type"] == "villager":
                            distance = abs(entity["x"] - x)
                            if distance < 30:  # Within 30 blocks
                                nearby_villagers += 1
                    
                    # Only spawn if there are less than 1 villager in a 30-block radius
                    if nearby_villagers < 1:
                        entities.append({
                            "type": "villager",
                            "x": x,
                            "y": ground_y - 1,
                            "dialogue_cooldown": 0
                        })
                        print(f"👤 Spawned random villager at ({x}, {ground_y - 1})")

        update_daylight()
        update_player()
        update_world_interactions()
        update_monsters()
        update_villagers()  # EXTREME ENGINEERING: Enhanced villager AI
        update_boss()  # EXTREME ENGINEERING: Legendary boss AI and attacks
        update_hunger()  # Update hunger system
        
        # Check for underground fortress trigger
        check_underground_fortress_trigger()
        
        # Update chat system
        if chat_system:
            chat_system.update(1.0 / 60.0)  # Assume 60 FPS for delta time
        
        # Auto-save world every 5 minutes
        auto_save_game()
        
        # Validate world integrity every 10 minutes (600 frames at 60 FPS)
        if frame_count % 36000 == 0:  # Every 10 minutes
            validate_world_integrity()

        draw_world()
        draw_inventory()
        draw_status_bars()
        draw_fps_display()
        draw_boss_health_bar()  # EXTREME ENGINEERING: Legendary boss health bar
        draw_multiplayer_chat()  # EXTREME ENGINEERING: Multiplayer chat interface
        
        # Draw chat system
        if chat_system:
            chat_system.draw(screen)
        
        # Take world preview screenshot every 5 minutes
        # TODO: Implement world preview system
        # Draw temporary message if any
        now_ms = pygame.time.get_ticks()
        if message_until > now_ms and message_text:
            m = font.render(message_text, True, (255, 255, 255))
            screen.blit(m, (SCREEN_WIDTH // 2 - m.get_width() // 2, 70))
        
        # Draw villager dialogue if any
        if villager_dialogue_until > time.time() and villager_dialogue_text:
            # Create a nice dialogue box
            dialogue_surface = font.render(villager_dialogue_text, True, (255, 255, 255))
            dialogue_width = dialogue_surface.get_width() + 40
            dialogue_height = dialogue_surface.get_height() + 20
            
            # Draw dialogue box background
            dialogue_x = SCREEN_WIDTH // 2 - dialogue_width // 2
            dialogue_y = 100
            pygame.draw.rect(screen, (50, 50, 100), (dialogue_x, dialogue_y, dialogue_width, dialogue_height))
            pygame.draw.rect(screen, (100, 100, 200), (dialogue_x, dialogue_y, dialogue_width, dialogue_height), 3)
            
            # Draw dialogue text
            screen.blit(dialogue_surface, (dialogue_x + 20, dialogue_y + 10))
        if chest_open:
            draw_chest_ui()

        if player["health"] <= 0:
            show_death_screen()
    elif game_state == GameState.TITLE:
        draw_title_screen()
    elif game_state == GameState.WORLD_SELECTION:
        draw_world_selection_screen()
    elif game_state == GameState.USERNAME_CREATE:
        draw_username_creation_screen()
    elif game_state == GameState.USERNAME_REQUIRED:
        draw_username_required_screen()
    elif game_state == GameState.PAUSED:
        draw_game_menu()
    elif game_state == GameState.CONTROLS:
        draw_controls()
    elif game_state == GameState.ABOUT:
        draw_about()
    elif game_state == GameState.OPTIONS:
        draw_options()
    elif game_state == GameState.SHOP:
        draw_shop_ui()
    elif game_state == GameState.INVENTORY:
        draw_full_inventory_ui()
    elif game_state == GameState.SKIN_CREATOR:
        draw_skin_creator_ui()
    elif game_state == GameState.MULTIPLAYER:
        draw_multiplayer_screen()

    pygame.display.flip()
    
    # Consistent frame-rate limiting for smooth, predictable movement
    target_fps = 60  # Lock to 60 FPS for consistent timing
    clock.tick(target_fps)
    
    # Update player animation
    if game_state == GameState.GAME:
        update_player_animation()
    
    # Update all GIF animations
    update_gif_animations()
    
    # Auto-save every 5 minutes (300 seconds) when in game
    if game_state == GameState.GAME and time.time() - last_auto_save > 300:
        if save_game():
            print("💾 Auto-save completed")
            last_auto_save = time.time()
        else:
            print("⚠️ Auto-save failed")
    
    # Check if we should exit
    if not running:
        print("🔄 Exit flag set, breaking game loop...")
        break
    



# World selection action handler removed - game goes directly to play

def load_world_data():
    """Load world data from the world system into the game"""
    global world_data, entities, player
    
    if not world_system.current_world_data:
        print("⚠️ No world data available to load")
        return False
    
    try:
        # Load world data
        world_data = world_system.current_world_data.get("blocks", {})
        entities = world_system.current_world_data.get("entities", [])
        
        # Load player data with validation
        player_data = world_system.current_world_data.get("player", {})
        if not isinstance(player_data, dict):
            print("⚠️ Invalid player data, using defaults")
            player_data = {}
        
        # Update player with loaded data, preserving any missing fields
        for key, value in player_data.items():
            if key in player:
                player[key] = value
        
        # Ensure critical player fields exist
        if "health" not in player or player["health"] <= 0:
            player["health"] = 10
        if "hunger" not in player or player["hunger"] <= 0:
            player["hunger"] = 100
        if "stamina" not in player:
            player["stamina"] = 100
        if "max_stamina" not in player:
            player["max_stamina"] = 100
        if "inventory" not in player:
            player["inventory"] = []
        if "backpack" not in player:
            player["backpack"] = []
        if "selected" not in player:
            player["selected"] = 0
        if "armor" not in player:
            player["armor"] = {"helmet": None, "chestplate": None, "leggings": None, "boots": None}
        
        # Load world settings
        world_settings = world_system.current_world_data.get("world_settings", {})
        global is_day, day_start_time
        is_day = world_settings.get("day", True)
        day_start_time = time.time() if is_day else time.time() - 43200  # 12 hours if night
        
        # CRITICAL: Mark all pre-generated terrain columns to prevent conflicts
        # This connects the new world generation system with the old dynamic system
        global generated_terrain_columns
        generated_terrain_columns.clear()  # Start fresh
        
        # Extract X coordinates from all blocks in the world
        for block_key in world_data.keys():
            try:
                x_str, y_str = block_key.split(',')
                x = int(x_str)
                generated_terrain_columns.add(x)
            except (ValueError, AttributeError):
                continue  # Skip invalid block keys
        
        print(f"🌍 World data loaded: {len(world_data)} blocks, {len(entities)} entities")
        print(f"🔗 Connected world systems: marked {len(generated_terrain_columns)} pre-generated columns")
        print(f"👤 Player loaded: health={player['health']}, hunger={player['hunger']}, stamina={player['stamina']}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading world data: {e}")
        return False

# Cleanup and exit
print("🔄 Game loop ended, cleaning up...")

# Force cleanup of any remaining resources
try:
    # Save username before quitting
    if GLOBAL_USERNAME:
        try:
            save_username_to_file(GLOBAL_USERNAME)
            print(f"💾 Username saved before exit: {GLOBAL_USERNAME}")
        except Exception as e:
            print(f"⚠️ Error saving username: {e}")

    if game_state == GameState.GAME:
        try:
            save_game()
            print("✅ Final game save completed")
        except Exception as e:
            print(f"⚠️ Error in final game save: {e}")
except Exception as e:
    print(f"⚠️ Error during cleanup: {e}")

print("🔄 Quitting pygame...")
try:
    pygame.quit()
    print("✅ Pygame quit successfully")
except Exception as e:
    print(f"⚠️ Error quitting pygame: {e}")

print("✅ Game closed successfully")
print("🎮 Thanks for playing! You can now safely close this window.")

# Final cleanup - force exit if needed
try:
    sys.exit(0)
except:
    # If sys.exit fails, force quit
    os._exit(0)
