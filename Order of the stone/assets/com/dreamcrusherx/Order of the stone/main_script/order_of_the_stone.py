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

# =============================================================================
# PYINSTALLER EXECUTABLE SUPPORT
# =============================================================================

def get_resource_path(relative_path=""):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        # In PyInstaller, assets are in the root of _MEIPASS
        return os.path.join(base_path, relative_path)
    except Exception:
        # Running in normal Python environment
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up to find the game root
        game_root = script_dir
        for _ in range(6):  # Go up enough levels to find "Order of the stone"
            parent = os.path.dirname(game_root)
            if os.path.basename(game_root) == "Order of the stone":
                break
            game_root = parent
        return os.path.join(game_root, relative_path)

# Ensure the game runs from the correct directory (where the game files are located)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    script_dir = os.path.dirname(sys.executable)
else:
    # Running as script
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
    # FIXED: Use proper path resolution for both development and executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
        log_dir = base_path / "logs"
    else:
        # Running as script
        base_path = Path(__file__).parent
        log_dir = base_path / ".." / ".." / ".." / ".." / ".." / "logs"
    
    # Ensure log directory exists
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Fallback to current directory if we can't create logs directory
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    
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
    STUDIO_LOADING = "studio_loading"  # New state for studio loading screen
    TITLE = "title"
    WORLD_SELECTION = "world_selection"  # New state for world selection
    WORLD_NAMING = "world_naming"  # New state for world naming
    WORLD_GENERATION = "world_generation"  # New state for world generation loading
    USERNAME_REQUIRED = "username_required"  # New state for username required
    GAME = "game"
    PAUSED = "paused"
    BACKPACK = "backpack"
    SHOP = "shop"
    MULTIPLAYER = "multiplayer"
    OPTIONS = "options"
    CONTROLS = "controls"
    ABOUT = "about"
    CREDITS = "credits"
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
            GameState.TITLE: [GameState.OPTIONS, GameState.CONTROLS, GameState.ABOUT, GameState.SHOP, GameState.MULTIPLAYER, GameState.USERNAME_CREATE, GameState.WORLD_SELECTION, GameState.CREDITS],
            GameState.WORLD_SELECTION: [GameState.TITLE, GameState.WORLD_NAMING, GameState.WORLD_GENERATION, GameState.USERNAME_REQUIRED],
            GameState.WORLD_NAMING: [GameState.WORLD_SELECTION, GameState.WORLD_GENERATION],
            GameState.WORLD_GENERATION: [GameState.GAME, GameState.TITLE],
            GameState.USERNAME_REQUIRED: [GameState.TITLE],
            GameState.GAME: [GameState.PAUSED, GameState.BACKPACK, GameState.SHOP, GameState.TITLE],
            GameState.PAUSED: [GameState.GAME, GameState.TITLE, GameState.OPTIONS],
            GameState.BACKPACK: [GameState.GAME],
            GameState.SHOP: [GameState.GAME, GameState.TITLE],
            GameState.MULTIPLAYER: [GameState.TITLE, GameState.GAME],
            GameState.OPTIONS: [GameState.TITLE, GameState.PAUSED],
            GameState.CONTROLS: [GameState.TITLE],
            GameState.ABOUT: [GameState.TITLE],
            GameState.CREDITS: [GameState.TITLE],
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
    from ui.multiplayer_ui import MultiplayerUI
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

# Background music system
background_music = None
music_playing = False
music_volume = 0.3  # 30% volume

def load_background_music():
    """Load and start playing background music"""
    global background_music, music_playing
    
    try:
        # Use PyInstaller-compatible path resolution
        if getattr(sys, 'frozen', False):
            # Running as executable - use bundled assets
            music_path = os.path.join(get_resource_path("assets"), "music", "an_adventure.wav")
        else:
            # Running as script - use relative path
            music_path = os.path.join("../../../..", "music", "an_adventure.wav")
        
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(music_volume)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            music_playing = True
            print(f"🎵 Background music loaded and playing: {music_path}")
            return True
        else:
            print(f"⚠️ Background music file not found: {music_path}")
            return False
    except Exception as e:
        print(f"❌ Error loading background music: {e}")
        return False

def stop_background_music():
    """Stop background music"""
    global music_playing
    try:
        pygame.mixer.music.stop()
        music_playing = False
        print("🔇 Background music stopped")
    except Exception as e:
        print(f"❌ Error stopping background music: {e}")

def set_music_volume(volume):
    """Set background music volume (0.0 to 1.0)"""
    global music_volume
    try:
        music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(music_volume)
        print(f"🔊 Music volume set to {music_volume}")
    except Exception as e:
        print(f"❌ Error setting music volume: {e}")

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
TILE_SIZE = 32

# =============================================================================
# FORTRESS SYSTEM CONFIGURATION
# =============================================================================

# Fortress types with different rarities and characteristics
FORTRESS_TYPES = {
    "ancient_ruins": {
        "name": "Ancient Ruins",
        "rarity": "common",
        "spawn_chance": 0.15,
        "min_size": 8,
        "max_size": 12,
        "materials": ["stone", "dirt", "grass"],
        "special_blocks": ["diamond", "gold", "iron"],
        "loot_tier": "basic"
    },
    "temple": {
        "name": "Ancient Temple",
        "rarity": "uncommon",
        "spawn_chance": 0.12,
        "min_size": 12,
        "max_size": 18,
        "materials": ["stone", "red_brick"],
        "special_blocks": ["diamond", "gold"],
        "loot_tier": "epic"
    },
    "pyramid": {
        "name": "Desert Pyramid",
        "rarity": "rare",
        "spawn_chance": 0.08,
        "min_size": 15,
        "max_size": 25,
        "materials": ["sand", "stone"],
        "special_blocks": ["diamond", "gold", "iron"],
        "loot_tier": "treasure"
    },
    "wizard_tower": {
        "name": "Wizard Tower",
        "rarity": "uncommon",
        "spawn_chance": 0.10,
        "min_size": 6,
        "max_size": 12,
        "materials": ["oak_planks", "stone"],
        "special_blocks": ["diamond"],
        "loot_tier": "magic"
    },
    "dungeon": {
        "name": "Underground Dungeon",
        "rarity": "rare",
        "spawn_chance": 0.07,
        "min_size": 10,
        "max_size": 20,
        "materials": ["stone", "red_brick"],
        "special_blocks": ["diamond", "gold", "iron"],
        "loot_tier": "epic"
    },
    "dragon_keep": {
        "name": "Dragon Keep",
        "rarity": "rare",
        "spawn_chance": 0.05,
        "min_size": 15,
        "max_size": 20,
        "materials": ["red_brick", "stone"],
        "special_blocks": ["diamond", "gold", "iron", "coal"],
        "loot_tier": "epic"
    },
    "bandit_camp": {
        "name": "Bandit Camp",
        "rarity": "common",
        "spawn_chance": 0.12,
        "min_size": 5,
        "max_size": 8,
        "materials": ["dirt", "grass", "oak_planks"],
        "special_blocks": ["iron", "coal"],
        "loot_tier": "basic"
    },
    "demon_castle": {
        "name": "Demon Castle",
        "rarity": "epic",
        "spawn_chance": 0.03,
        "min_size": 18,
        "max_size": 22,
        "materials": ["red_brick", "stone"],
        "special_blocks": ["diamond", "gold", "iron"],
        "loot_tier": "epic"
    },
    "treasure_vault": {
        "name": "Treasure Vault",
        "rarity": "rare",
        "spawn_chance": 0.06,
        "min_size": 8,
        "max_size": 12,
        "materials": ["stone", "dirt"],
        "special_blocks": ["diamond", "gold", "iron", "coal"],
        "loot_tier": "treasure"
    },
    "castle_ruins": {
        "name": "Castle Ruins",
        "rarity": "rare",
        "spawn_chance": 0.06,
        "min_size": 18,
        "max_size": 28,
        "materials": ["red_brick", "stone"],
        "special_blocks": ["diamond", "gold", "iron"],
        "loot_tier": "epic"
    }
}

# Discovery system - tracks which fortresses player has found
discovered_fortresses = set()
current_fortress_discovery = None
discovery_timer = 0
fortress_discovery_animation_scale = 1.0  # Scale for big discovery animation

# Collision system
head_bump_timer = 0
head_bump_effect = False

# Blood particle system
blood_particles = []
MAX_BLOOD_PARTICLES = 200  # Limit for performance

# Block breaking particle system
block_particles = []
MAX_BLOCK_PARTICLES = 150  # Limit for performance

# Shift key state tracking for reliable movement detection
shift_key_pressed = False


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

# Initialize background music after screen is created
load_background_music()

update_chest_ui_geometry()

# Helper for centered button rect
def centered_button(y, w=200, h=50):
    return pygame.Rect(center_x(w), y, w, h)

# COMPREHENSIVE ASSET PATH SYSTEM: Find all game directories automatically
current_script_dir = os.path.dirname(os.path.abspath(__file__))

def find_game_root():
    """Find the main 'Order of the stone' directory by searching up the directory tree"""
    search_dir = current_script_dir
    for _ in range(10):  # Limit search depth
        # Look for the main game directory containing both assets and other folders
        potential_root = os.path.join(search_dir, "Order of the stone")
        if os.path.exists(potential_root):
            # Verify it has the expected subdirectories
            if (os.path.exists(os.path.join(potential_root, "assets")) and
                os.path.exists(os.path.join(potential_root, "damage")) and
                os.path.exists(os.path.join(potential_root, "save_data"))):
                return potential_root
        
        # Check if we're already inside the Order of the stone directory
        if os.path.basename(search_dir) == "Order of the stone":
            if (os.path.exists(os.path.join(search_dir, "assets")) and
                os.path.exists(os.path.join(search_dir, "damage")) and
                os.path.exists(os.path.join(search_dir, "save_data"))):
                return search_dir
            
        # Go up one level
        parent = os.path.dirname(search_dir)
        if parent == search_dir:  # Reached root
            break
        search_dir = parent
    
    return None

# Find the game root directory
game_root = find_game_root()

# Use PyInstaller-compatible path resolution
if getattr(sys, 'frozen', False):
    # Running as executable - use get_resource_path
    print("🎮 Running as executable - using bundled assets")
    assets_root = get_resource_path("assets")
    TILE_DIR = os.path.join(assets_root, "tiles")
    ITEM_DIR = os.path.join(assets_root, "items") 
    MOB_DIR = os.path.join(assets_root, "mobs")
    PLAYER_DIR = os.path.join(assets_root, "player")
    HP_DIR = os.path.join(assets_root, "HP")
    SOUND_DIR = get_resource_path("damage")
    SAVE_DIR = os.path.join(script_dir, "save_data")  # Save data goes in exe directory
elif game_root:
    print(f"🎯 Found game root directory: {game_root}")
    # Set up all directory paths
    assets_root = os.path.join(game_root, "assets")
    TILE_DIR = os.path.join(assets_root, "tiles")
    ITEM_DIR = os.path.join(assets_root, "items") 
    MOB_DIR = os.path.join(assets_root, "mobs")
    PLAYER_DIR = os.path.join(assets_root, "player")
    HP_DIR = os.path.join(assets_root, "HP")
    SOUND_DIR = os.path.join(game_root, "damage")
    SAVE_DIR = os.path.join(game_root, "save_data")
else:
    print("⚠️ Could not find game root directory, using fallback paths")
    # Fallback paths
    game_root = os.path.join(current_script_dir, "..", "..", "..", "..", "..")
    assets_root = os.path.join(game_root, "assets")
    TILE_DIR = os.path.join(assets_root, "tiles")
    ITEM_DIR = os.path.join(assets_root, "items") 
    MOB_DIR = os.path.join(assets_root, "mobs")
    PLAYER_DIR = os.path.join(assets_root, "player")
    HP_DIR = os.path.join(assets_root, "HP")
    SOUND_DIR = os.path.join(game_root, "damage")
    SAVE_DIR = os.path.join(game_root, "save_data")

# Verify ALL paths and create missing directories
directories = {
"TILE_DIR": TILE_DIR,
"ITEM_DIR": ITEM_DIR,
"MOB_DIR": MOB_DIR,
"PLAYER_DIR": PLAYER_DIR,
"HP_DIR": HP_DIR,
"SOUND_DIR": SOUND_DIR,
"SAVE_DIR": SAVE_DIR
}

print("🔍 Verifying all game directories:")
for dir_name, dir_path in directories.items():
    if os.path.exists(dir_path):
        print(f"✅ {dir_name}: {dir_path}")
    else:
        print(f"❌ {dir_name} not found: {dir_path}")
        if dir_name == "SAVE_DIR":
            # Create save directory if it doesn't exist
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"📁 Created {dir_name}: {dir_path}")
            except Exception as e:
                print(f"⚠️ Could not create {dir_name}: {e}")

# Directory setup is now complete above

def load_texture(path):
    """Load a texture with error handling and fallback generation"""
    try:
        if os.path.exists(path):
            return pygame.transform.scale(pygame.image.load(path).convert_alpha(), (TILE_SIZE, TILE_SIZE))
        else:
            print(f"⚠️ Texture not found: {path}")
            # Generate a simple colored square as fallback
            filename = os.path.basename(path).lower()
            fallback_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            
            # Color based on filename
            if "grass" in filename:
                fallback_surface.fill((34, 139, 34))  # Forest green
            elif "dirt" in filename:
                fallback_surface.fill((139, 69, 19))   # Saddle brown
            elif "stone" in filename:
                fallback_surface.fill((128, 128, 128))  # Gray
            elif "water" in filename:
                fallback_surface.fill((0, 100, 200))    # Blue
            elif "lava" in filename:
                fallback_surface.fill((255, 69, 0))     # Red-orange
            elif "sand" in filename:
                fallback_surface.fill((238, 203, 173))  # Sandy brown
            elif "player" in filename:
                fallback_surface.fill((255, 192, 203))  # Pink
            elif "monster" in filename or "mob" in filename:
                fallback_surface.fill((139, 0, 0))      # Dark red
            elif "bread" in filename:
                fallback_surface.fill((222, 184, 135))  # Wheat bread color
            elif "cooked_fish" in filename:
                fallback_surface.fill((255, 165, 0))    # Orange fish
            elif "steak" in filename:
                fallback_surface.fill((139, 69, 19))    # Brown steak
            elif "honey_jar" in filename:
                fallback_surface.fill((255, 215, 0))    # Golden honey
            elif "carrot" in filename:
                fallback_surface.fill((255, 165, 0))    # Orange carrot
            else:
                fallback_surface.fill((200, 200, 200))  # Light gray
            
            print(f"🎨 Generated fallback texture for: {filename}")
            return fallback_surface
            
    except Exception as e:
        print(f"❌ Error loading texture {path}: {e}")
        # Generate a simple error texture
        error_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        error_surface.fill((255, 0, 255))  # Magenta for error
        return error_surface

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

# --- Snow Texture Generator ---
def make_snow_texture(size):
    """Generate a white snow texture with slight variations"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Base white color
    base_color = (255, 255, 255)
    
    # Fill with base white
    surf.fill(base_color)
    
    # Add some slight variations for texture
    for _ in range(size // 4):  # Add some random white spots
        x = random.randint(0, size - 1)
        y = random.randint(0, size - 1)
        # Slightly different white shades
        shade = random.choice([
            (250, 250, 255),  # Slightly blue-white
            (255, 255, 250),  # Slightly yellow-white
            (248, 248, 248),  # Slightly grey-white
        ])
        pygame.draw.circle(surf, shade, (x, y), random.randint(1, 2))
    
    return surf

# --- Torch Texture Generator ---
def make_torch_texture(size):
    """Generate a torch texture with wooden stick and fire"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Wooden stick (brown stick in center)
    stick_width = max(4, size // 6)
    stick_height = size // 2
    stick_x = (size - stick_width) // 2
    stick_y = size - stick_height
    
    # Draw stick
    stick_color = (101, 67, 33)  # Brown
    pygame.draw.rect(surf, stick_color, (stick_x, stick_y, stick_width, stick_height))
    
    # Fire at top (orange/yellow flame)
    flame_size = size // 3
    flame_x = size // 2
    flame_y = stick_y - flame_size // 2
    
    # Outer orange flame
    pygame.draw.circle(surf, (255, 140, 0), (flame_x, flame_y), flame_size)
    # Inner yellow flame
    pygame.draw.circle(surf, (255, 215, 0), (flame_x, flame_y), flame_size // 2)
    # Bright white core
    pygame.draw.circle(surf, (255, 255, 200), (flame_x, flame_y), flame_size // 4)
    
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

# --- Ability System Functions ---
# Ability unlock system removed - no more abilities

def show_ability_unlock_animation(ability_name, instructions):
    """Show the black screen animation for ability unlock"""
    global screen, clock
    
    # Black screen for 1 second
    black_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    black_surface.fill((0, 0, 0))
    
    for i in range(60):  # 1 second at 60 FPS
        screen.blit(black_surface, (0, 0))
        pygame.display.flip()
        clock.tick(60)
    
    # White particles coming out and back in
    particles = []
    for i in range(50):
        particles.append({
            "x": SCREEN_WIDTH // 2,
            "y": SCREEN_HEIGHT // 2,
            "vel_x": (random.random() - 0.5) * 10,
            "vel_y": (random.random() - 0.5) * 10,
            "life": 120,  # 2 seconds
            "returning": False
        })
    
    # Animate particles
    for frame in range(180):  # 3 seconds total
        screen.blit(black_surface, (0, 0))
        
        # Update particles
        for particle in particles:
            if not particle["returning"]:
                # Move outward
                particle["x"] += particle["vel_x"]
                particle["y"] += particle["vel_y"]
                particle["life"] -= 1
                
                # Start returning after 1 second
                if particle["life"] <= 60:
                    particle["returning"] = True
                    particle["vel_x"] = (SCREEN_WIDTH // 2 - particle["x"]) / 60
                    particle["vel_y"] = (SCREEN_HEIGHT // 2 - particle["y"]) / 60
            else:
                # Move back to center
                particle["x"] += particle["vel_x"]
                particle["y"] += particle["vel_y"]
        
        # Draw particles
        for particle in particles:
            if particle["life"] > 0:
                pygame.draw.circle(screen, (255, 255, 255), 
                                 (int(particle["x"]), int(particle["y"])), 3)
        
        # Show ability name and instructions
        if frame > 120:  # After particles return
            ability_text = font.render(f"ABILITY UNLOCKED: {ability_name}", True, (255, 255, 255))
            instruction_text = font.render(instructions, True, (200, 200, 200))
            
            ability_rect = ability_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            
            screen.blit(ability_text, ability_rect)
            screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()
        clock.tick(60)

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

# --- Old villager texture generator removed - using new Python-themed one ---

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

def make_potion_texture(size):
    """Procedurally draw a potion texture (upside down)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Potion colors
    bottle = (200, 200, 200)  # Clear glass
    liquid = (255, 0, 255)    # Magenta potion liquid
    cork = (101, 67, 33)      # Brown cork
    
    # Draw potion bottle (upside down)
    # Bottle body
    pygame.draw.ellipse(surf, bottle, (size//4, size//2, size//2, size//2))
    # Liquid inside
    pygame.draw.ellipse(surf, liquid, (size//4 + 2, size//2 + 2, size//2 - 4, size//2 - 4))
    # Bottle neck
    pygame.draw.rect(surf, bottle, (size//2 - 2, size//4, 4, size//4))
    # Cork
    pygame.draw.rect(surf, cork, (size//2 - 3, size//8, 6, size//8))
    
    return surf

def make_coral_texture(size):
    """Create a tropical coral reef texture programmatically"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Coral base (rocky)
    base_color = (120, 80, 60)  # Brown rocky base
    pygame.draw.rect(surf, base_color, (2, size-6, size-4, 4))
    
    # Coral branches in tropical colors
    coral_colors = [(255, 100, 150), (255, 150, 100), (255, 200, 100), (200, 100, 255)]
    
    # Create 2-3 coral branches
    for i in range(3):
        color = coral_colors[i % len(coral_colors)]
        branch_x = 4 + (i * 4)
        branch_height = 8 + (i * 2)
        branch_width = 2
        
        # Coral branch
        pygame.draw.rect(surf, color, (branch_x, size-branch_height-2, branch_width, branch_height))
        
        # Coral polyps (small dots)
        for j in range(2):
            polyp_y = size - branch_height - 2 + (j * 3)
            pygame.draw.circle(surf, (255, 255, 255), (branch_x + 1, polyp_y), 1)
    
    return surf

def make_seagrass_texture(size):
    """Create a tropical sea grass texture programmatically"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Sea grass base (sandy)
    base_color = (200, 180, 120)  # Sandy base
    pygame.draw.rect(surf, base_color, (6, size-4, size-12, 2))
    
    # Sea grass blades in tropical green
    grass_colors = [(50, 200, 100), (80, 220, 120), (60, 180, 80)]
    
    # Create 3-4 sea grass blades
    for i in range(4):
        color = grass_colors[i % len(grass_colors)]
        blade_x = 4 + (i * 3)
        blade_height = 6 + (i % 2) * 2
        blade_width = 1
        
        # Sea grass blade (curved)
        for j in range(blade_height):
            offset = int(2 * math.sin(j * 0.5))
            pygame.draw.rect(surf, color, (blade_x + offset, size - j - 4, blade_width, 1))
    
    return surf

def make_beautiful_water_texture(size):
    """Create beautiful water that looks like the reference image"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Beautiful ocean blue like in the reference
    base_color = (50, 120, 200)  # Rich, deep blue
    
    # Fill with the beautiful blue
    surf.fill(base_color)
    
    # Add just a subtle gradient - darker at bottom
    for y in range(size):
        darken = int(y * 0.3)  # Subtle darkening
        line_color = (
            max(0, base_color[0] - darken),
            max(0, base_color[1] - darken), 
            max(0, base_color[2] - darken)
        )
        pygame.draw.line(surf, line_color, (0, y), (size, y))
    
    return surf

def make_tropical_fish_texture(size):
    """Create a tropical fish texture programmatically"""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Fish body (tropical colors)
    fish_colors = [(255, 100, 100), (100, 200, 255), (255, 200, 100), (200, 100, 255)]
    body_color = fish_colors[random.randint(0, len(fish_colors)-1)]
    
    # Fish body (oval)
    pygame.draw.ellipse(surf, body_color, (4, 6, size-8, size-12))
    
    # Fish tail
    pygame.draw.polygon(surf, body_color, [(4, size//2), (0, size//2-2), (0, size//2+2)])
    
    # Fish eye
    pygame.draw.circle(surf, (255, 255, 255), (size-6, 8), 2)
    pygame.draw.circle(surf, (0, 0, 0), (size-5, 8), 1)
    
    # Fish stripes (tropical pattern)
    stripe_color = (255, 255, 255) if body_color[0] < 200 else (0, 0, 0)
    for i in range(2):
        stripe_x = 6 + (i * 4)
        pygame.draw.rect(surf, stripe_color, (stripe_x, 8, 1, size-16))
    
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



def generate_carbine_field(center_x: int, ground_y: int, world_rng):
    """Generate a carbine field - a group of carrots in a small area"""
    field_size = world_rng.randint(3, 6)  # 3x3 to 6x6 field
    carrots_placed = 0
    
    # Create a small field of carrots
    for dx in range(-field_size//2, field_size//2 + 1):
        for dy in range(-field_size//2, field_size//2 + 1):
            field_x = center_x + dx
            field_ground_y = ground_y_of_column(field_x)
            
            # Check if we can place a carrot here
            if (field_ground_y is not None and 
                can_place_surface_item(field_x, field_ground_y) and 
                world_rng.random() < 0.7):  # 70% chance for each spot in the field
                set_block(field_x, field_ground_y - 1, "carrot")
                carrots_placed += 1
    
    if carrots_placed > 0:
        print(f"🥕 Carbine field generated at ({center_x}, {ground_y}) with {carrots_placed} carrots!")

def generate_terrain_column(x):
    """Generate realistic terrain for a specific column if it hasn't been generated yet"""
    global generated_terrain_columns
    
    # Skip if already generated - CRITICAL: This prevents terrain overlap!
    if x in generated_terrain_columns:
        print(f"⏭️ Skipping terrain generation for column {x} - already generated")
        return
    
    print(f"🌍 Generating terrain for NEW column {x}")
    
    # NATURAL HILL GENERATION: Create terrain that follows natural contours
    # Use multiple noise functions for more natural terrain
    base_height = 115  # Base surface level
    
    # Primary terrain variation
    primary_wave = 8 * math.sin(x * 0.05)  # Large hills/valleys
    secondary_wave = 3 * math.sin(x * 0.15)  # Medium variations  
    tertiary_wave = 2 * math.sin(x * 0.3)   # Small details
    
    # Combine waves for natural terrain
    height_variation = int(primary_wave + secondary_wave + tertiary_wave)
    surface_y = base_height + height_variation
    
    # Ensure surface is in reasonable range
    surface_y = max(100, min(125, surface_y))
    
    # NATURAL TERRAIN GENERATION: Build hills from base up, not cutting through
    # Generate terrain layers from bottom to top to create natural hill contours
    
    # 1. BEDROCK at bottom - CHECK FOR EXISTING BLOCKS
    bedrock_y = 327  # 200 blocks below surface (surface_y + 200)
    if get_block(x, bedrock_y) is None:
        set_block(x, bedrock_y, "bedrock")
    
    # 2. STONE LAYER: Fill from bedrock up to surface (200 blocks deep!)
    for y in range(surface_y + 3, bedrock_y):  # Stone fills 200 blocks underground
        if get_block(x, y) is None:
            set_block(x, y, "stone")
    
    # 3. DIRT LAYER: 2 blocks below surface - NEVER underground
    for y in range(surface_y + 1, surface_y + 3):
        if get_block(x, y) is None:
            set_block(x, y, "dirt")
    
    # 4. GRASS: ONLY at exact surface level - NEVER underground
    if get_block(x, surface_y) is None:
        set_block(x, surface_y, "grass")  # Surface ONLY - NEVER underground!
    
    # BIOME-BASED TERRAIN GENERATION: Handle different biomes
    biome_type = get_biome_type(x)
    
    # Debug: Print biome type for first few columns
    if x < 10:
        print(f"🌍 Column {x}: Biome = {biome_type}")
    
    # CAVE SYSTEM REMOVED - No longer generating caves
    
    # DESERT BIOME TERRAIN: Replace grass with sand in desert biomes
    if biome_type == "desert":
        # Replace surface grass with sand
        if get_block(x, surface_y) == "grass":
            set_block(x, surface_y, "sand")
        # Replace underground dirt with sand too (desert sand goes deeper)
        for depth in range(1, min(8, surface_y + 1)):
            if get_block(x, surface_y - depth) == "dirt":
                set_block(x, surface_y - depth, "sand")
        
        # Deserts have very few trees (cacti would be better, but we don't have that texture)
        # So we'll just have sparse trees
        if random.random() < 0.02 and should_generate_tree(x, surface_y, biome_type):  # Very rare trees in desert
            # Same tree generation as other biomes
            if get_block(x, surface_y - 1) is None and (surface_y - 1) < surface_y:
                set_block(x, surface_y - 1, "log")
                if get_block(x, surface_y - 2) is None and (surface_y - 2) < surface_y:
                    set_block(x, surface_y - 2, "log")
                
                # Leaves
                if get_block(x - 1, surface_y - 3) is None and (surface_y - 3) < surface_y:
                    set_block(x - 1, surface_y - 3, "leaves")
                if get_block(x, surface_y - 3) is None and (surface_y - 3) < surface_y:
                    set_block(x, surface_y - 3, "leaves")
                if get_block(x + 1, surface_y - 3) is None and (surface_y - 3) < surface_y:
                    set_block(x + 1, surface_y - 3, "leaves")
                
                if get_block(x - 1, surface_y - 2) is None and (surface_y - 2) < surface_y:
                    set_block(x - 1, surface_y - 2, "leaves")
                if get_block(x + 1, surface_y - 2) is None and (surface_y - 2) < surface_y:
                    set_block(x + 1, surface_y - 2, "leaves")
    
    # NORMAL BIOME TREE GENERATION: Forests have lots of trees, fields have few
    elif biome_type in ["forest", "field", "mixed"] and should_generate_tree(x, surface_y, biome_type):
        # ABSOLUTE RULE: Trees can ONLY spawn ABOVE surface (y < surface_y) - NEVER underground!
        # Tree trunk: 2 stacked logs - CHECK FOR EXISTING BLOCKS
        # CRITICAL: Trees can NEVER EVER spawn underground or at ground level
        if get_block(x, surface_y - 1) is None and (surface_y - 1) < surface_y:
            set_block(x, surface_y - 1, "log")  # Bottom log (ABOVE surface only)
            if get_block(x, surface_y - 2) is None and (surface_y - 2) < surface_y:
                set_block(x, surface_y - 2, "log")  # Top log (ABOVE surface only)
            
            # Perfect 6-leaf formation in a block pattern - CHECK FOR EXISTING BLOCKS
            # Top row (3 leaves) - ONLY ABOVE SURFACE - NEVER underground!
            if get_block(x - 1, surface_y - 3) is None and (surface_y - 3) < surface_y:
                set_block(x - 1, surface_y - 3, "leaves")  # Left
            if get_block(x, surface_y - 3) is None and (surface_y - 3) < surface_y:
                set_block(x, surface_y - 3, "leaves")      # Center
            if get_block(x + 1, surface_y - 3) is None and (surface_y - 3) < surface_y:
                set_block(x + 1, surface_y - 3, "leaves")  # Right
            
            # Bottom row (3 leaves) - ONLY ABOVE SURFACE - NEVER underground!
            if get_block(x - 1, surface_y - 2) is None and (surface_y - 2) < surface_y:
                set_block(x - 1, surface_y - 2, "leaves")  # Left (at log level)
            if get_block(x + 1, surface_y - 2) is None and (surface_y - 2) < surface_y:
                set_block(x + 1, surface_y - 2, "leaves")  # Right (at log level)
            if get_block(x, surface_y - 4) is None and (surface_y - 4) < surface_y:
                set_block(x, surface_y - 4, "leaves")      # Top center (above the 3-leaf row)
    
    # Add underground ores with proper rarity distribution - CHECK FOR EXISTING BLOCKS
    ore_chance = random.random()
    
    # Ensure valid range for ore placement in the deep stone layer
    min_ore_y = surface_y + 5
    max_ore_y = bedrock_y - 1  # Ore can go almost to bedrock
    
    # Multiple ore chances per column for more ores underground
    for _ in range(3):  # Try to place up to 3 ores per column
        if ore_chance < 0.8:  # 80% chance for at least one ore per column
            if min_ore_y <= max_ore_y:  # Only place ore if range is valid
                ore_y = random.randint(min_ore_y, max_ore_y)

                # Depth-based ore rarity system
                depth_from_surface = ore_y - surface_y
                depth_percentage = depth_from_surface / (bedrock_y - surface_y)

                # Ore rarity based on depth and random chance
                ore_roll = random.random()

                # Coal: Common (60% chance), spawns at any depth
                if ore_roll < 0.6:
                    ore_type = "coal"
                # Iron: Uncommon (25% chance), spawns at any depth
                elif ore_roll < 0.85:
                    ore_type = "iron"
                # Gold: Slightly rare (12% chance), spawns deeper (50%+ depth)
                elif ore_roll < 0.97 and depth_percentage > 0.5:
                    ore_type = "gold"
                # Diamond: Rare (3% chance), spawns very deep (80%+ depth)
                elif depth_percentage > 0.8:
                    ore_type = "diamond"
                else:
                    ore_type = "coal"  # Fallback to coal if conditions not met
                
                # Only place ore if the location is empty
                if get_block(x, ore_y) is None:
                    set_block(x, ore_y, ore_type)
    
        # Reduce chance for additional ores
        ore_chance = random.random() * 0.4  # 40% chance for second ore, 16% for third
    
    # Add surface items (carrots and chests) - CHECK FOR EXISTING BLOCKS
    if can_place_surface_item(x, surface_y):
        # Carrots - 15% chance
        if random.random() < 0.15:
            # Only place carrot if the location is empty
            if get_block(x, surface_y - 1) is None:
                set_block(x, surface_y - 1, "carrot")
        
        # Chests removed from natural spawning - only spawn in fortresses and structures now
        # (Chest generation in fortresses is handled separately)
    
    # Safety check: Ensure at least the surface block was placed
    if get_block(x, surface_y) is None:
        print(f"⚠️ WARNING: Surface block missing at ({x}, {surface_y}), forcing placement...")
        set_block(x, surface_y, "grass")
    
    # Mark as generated
    generated_terrain_columns.add(x)
    
    print(f"✅ Generated terrain column {x}: surface at Y={surface_y}")

# Cave generation functions removed

def calculate_surface_height(x):
    """Calculate the surface height at a given x coordinate"""
    import math
    # This is a simplified version - in a real implementation you'd want to
    # store or calculate the actual surface height
    base_height = 115
    height_variation = int(8 * math.sin(x * 0.05) + 3 * math.sin(x * 0.15) + 2 * math.sin(x * 0.3))
    return max(100, min(125, base_height + height_variation))

# Cloud System
clouds = []

def generate_clouds():
    """Generate clouds for the sky background"""
    global clouds
    clouds = []
    
    # Generate 5-8 clouds across the screen
    num_clouds = random.randint(5, 8)
    
    for i in range(num_clouds):
        cloud = {
            'x': random.randint(-200, SCREEN_WIDTH + 200),  # Start off-screen
            'y': random.randint(50, 200),  # Sky level
            'width': random.randint(80, 150),  # Cloud width
            'height': random.randint(30, 60),  # Cloud height
            'speed': random.uniform(0.2, 0.8),  # Cloud movement speed
            'opacity': random.randint(150, 255)  # Cloud opacity
        }
        clouds.append(cloud)


def update_clouds():
    """Update cloud positions"""
    global clouds
    
    # Update cloud positions
    for cloud in clouds:
        cloud['x'] += cloud['speed']
        # Reset cloud if it goes off-screen
        if cloud['x'] > SCREEN_WIDTH + 200:
            cloud['x'] = -200
            cloud['y'] = random.randint(50, 200)

# Sky background optimized for performance

# Weather system variables
current_weather = "clear"  # Start with beautiful sunny weather!
weather_timer = 0
weather_duration = 72000  # Start with 20 minutes of sunny weather (1200 seconds * 60 FPS)
thunder_timer = 0
snow_blocks = []  # Track snow blocks for melting
rain_particles = []
snow_particles = []
lightning_bolts = []  # Track active lightning bolts

# Lighting system variables
light_sources = []  # List of torch positions (light sources)
monster_health_displays = []  # List of {entity, timer} for showing health bars

# Day/Night transition variables
day_transition_progress = 1.0  # 0.0 = night, 1.0 = day
transitioning_to_day = True
sun_position = 0  # Position of sun (0-1, where 0.5 is middle of sky)
moon_position = 0.5  # Position of moon (opposite of sun)

def draw_sky_background():
    """Draw the sky with sun/moon and smooth day/night transitions"""
    global current_weather, day_transition_progress, sun_position, moon_position
    
    # Calculate sky color based on day/night transition
    day_color = (135, 206, 235)  # Light blue day
    night_color = (25, 25, 60)   # Dark blue night
    
    # Modify colors based on weather
    if current_weather == "rain":
        day_color = (105, 105, 105)
        night_color = (30, 30, 30)
    elif current_weather == "thunder":
        day_color = (50, 50, 50)
        night_color = (20, 20, 20)
    elif current_weather == "snow":
        day_color = (200, 200, 220)
        night_color = (40, 40, 70)
    
    # Interpolate between day and night colors
    r = int(day_color[0] * day_transition_progress + night_color[0] * (1 - day_transition_progress))
    g = int(day_color[1] * day_transition_progress + night_color[1] * (1 - day_transition_progress))
    b = int(day_color[2] * day_transition_progress + night_color[2] * (1 - day_transition_progress))
    
    sky_color = (r, g, b)
    screen.fill(sky_color)
    
    # Draw sun during day (when transition > 0.3)
    if day_transition_progress > 0.3:
        sun_size = 50
        sun_x = SCREEN_WIDTH // 2 + int((sun_position - 0.5) * SCREEN_WIDTH * 0.8)
        sun_y = 100 + int((1 - day_transition_progress) * 200)  # Sun rises/sets
        
        # Sun glow
        glow_size = sun_size + 20
        glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 255, 200, 100), (glow_size, glow_size), glow_size)
        screen.blit(glow_surface, (sun_x - glow_size, sun_y - glow_size))
        
        # Sun
        pygame.draw.circle(screen, (255, 255, 100), (sun_x, sun_y), sun_size)
        pygame.draw.circle(screen, (255, 255, 200), (sun_x, sun_y), sun_size - 10)
    
    # Draw moon during night (when transition < 0.7)
    if day_transition_progress < 0.7:
        moon_size = 40
        moon_x = SCREEN_WIDTH // 2 + int((moon_position - 0.5) * SCREEN_WIDTH * 0.8)
        moon_y = 100 + int(day_transition_progress * 200)  # Moon rises/sets opposite to sun
        
        # Moon glow
        glow_surface = pygame.Surface((moon_size * 2 + 20, moon_size * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (200, 200, 255, 80), (moon_size + 10, moon_size + 10), moon_size + 10)
        screen.blit(glow_surface, (moon_x - moon_size - 10, moon_y - moon_size - 10))
        
        # Moon
        pygame.draw.circle(screen, (220, 220, 240), (moon_x, moon_y), moon_size)
        # Moon craters
        pygame.draw.circle(screen, (200, 200, 220), (moon_x - 10, moon_y - 5), 8)
        pygame.draw.circle(screen, (200, 200, 220), (moon_x + 8, moon_y + 8), 6)
    
    # Draw clouds (fresh each frame for proper alpha blending)
    for cloud in clouds:
        # Create cloud surface with alpha
        cloud_surface = pygame.Surface((cloud['width'], cloud['height']), pygame.SRCALPHA)
        
        # Draw fluffy cloud shape using multiple circles
        cloud_color = (255, 255, 255, cloud['opacity'])
        
        # Main cloud body
        pygame.draw.circle(cloud_surface, cloud_color, (cloud['width']//2, cloud['height']//2), cloud['height']//2)
        
        # Cloud puffs
        pygame.draw.circle(cloud_surface, cloud_color, (cloud['width']//3, cloud['height']//3), cloud['height']//3)
        pygame.draw.circle(cloud_surface, cloud_color, (2*cloud['width']//3, cloud['height']//3), cloud['height']//3)
        pygame.draw.circle(cloud_surface, cloud_color, (cloud['width']//4, 2*cloud['height']//3), cloud['height']//4)
        pygame.draw.circle(cloud_surface, cloud_color, (3*cloud['width']//4, 2*cloud['height']//3), cloud['height']//4)
        
        # Blit cloud to screen
        screen.blit(cloud_surface, (cloud['x'], cloud['y']))
    
    # Draw weather effects
    draw_weather_effects()

def draw_weather_effects():
    """Draw weather effects like rain, snow, and lightning"""
    global current_weather, thunder_timer
    
    if current_weather == "rain":
        draw_rain()
    elif current_weather == "thunder":
        draw_rain()
        draw_lightning()
    elif current_weather == "snow":
        draw_snow()
        accumulate_snow()  # Gradually add snow to world
    
    # Gradually melt snow if weather is clear
    if current_weather == "clear" and len(snow_blocks) > 0:
        start_snow_melting()
    
    # Update thunder timer
    if thunder_timer > 0:
        thunder_timer -= 1

def draw_rain():
    """Draw rain particles falling from the sky"""
    global rain_particles
    
    # Add new rain particles
    if len(rain_particles) < 100:  # Limit for performance
        for _ in range(5):
            rain_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(-50, 0),
                'speed': random.uniform(3, 8)
            })
    
    # Update and draw rain particles
    for particle in rain_particles[:]:
        particle['y'] += particle['speed']
        
        # Draw rain drop
        pygame.draw.line(screen, (173, 216, 230), 
                        (particle['x'], particle['y']), 
                        (particle['x'], particle['y'] + 8), 2)
        
        # Remove particles that fall off screen
        if particle['y'] > SCREEN_HEIGHT:
            rain_particles.remove(particle)

def draw_snow():
    """Draw snow particles falling from the sky"""
    global snow_particles
    
    # Add new snow particles
    if len(snow_particles) < 80:  # Limit for performance
        for _ in range(3):
            snow_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(-50, 0),
                'speed': random.uniform(1, 3),
                'size': random.randint(2, 4)
            })
    
    # Update and draw snow particles
    for particle in snow_particles[:]:
        particle['y'] += particle['speed']
        particle['x'] += random.uniform(-0.5, 0.5)  # Slight horizontal drift
        
        # Draw snowflake
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(particle['x']), int(particle['y'])), 
                          particle['size'])
        
        # Remove particles that fall off screen
        if particle['y'] > SCREEN_HEIGHT:
            snow_particles.remove(particle)

def draw_lightning():
    """Draw lightning flash effect with realistic lightning bolts"""
    global thunder_timer, lightning_bolts
    
    # Random lightning flash (much rarer)
    if random.random() < 0.005:  # 0.5% chance per frame (much rarer!)
        thunder_timer = 8  # Flash for 8 frames
        # Create lightning bolt at random location
        create_lightning_bolt()
    
    # Draw lightning flash
    if thunder_timer > 0:
        # Create bright white flash overlay
        flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        flash_surface.fill((255, 255, 255))
        flash_surface.set_alpha(80)  # Less intense flash
        screen.blit(flash_surface, (0, 0))
        
        # Draw lightning bolts
        for bolt in lightning_bolts:
            draw_lightning_bolt(bolt)

def create_lightning_bolt():
    """Create a lightning bolt at a random location"""
    global lightning_bolts
    
    # Choose random location (not necessarily near player)
    bolt_x = random.randint(50, SCREEN_WIDTH - 50)
    bolt_start_y = random.randint(0, 100)  # Start from sky
    
    # Create zigzag lightning bolt
    bolt_points = []
    current_x = bolt_x
    current_y = bolt_start_y
    
    # Generate zigzag path down to ground
    while current_y < SCREEN_HEIGHT:
        bolt_points.append((current_x, current_y))
        
        # Move down
        current_y += random.randint(8, 20)
        
        # Add horizontal zigzag
        current_x += random.randint(-15, 15)
        current_x = max(0, min(SCREEN_WIDTH, current_x))  # Keep in bounds
        
        # Add branch occasionally
        if random.random() < 0.3 and len(bolt_points) > 3:
            create_lightning_branch(bolt_points, current_x, current_y)
    
    # Store the bolt
    lightning_bolts.append({
        'points': bolt_points,
        'life': 8,  # How long to show the bolt
        'x': bolt_x,
        'ground_y': current_y
    })
    
    # Check if lightning hit player (much rarer now!)
    check_lightning_player_hit(bolt_x, current_y)

def create_lightning_branch(main_points, start_x, start_y):
    """Create a branch off the main lightning bolt"""
    branch_points = []
    current_x = start_x
    current_y = start_y
    
    # Create short branch
    for _ in range(random.randint(2, 5)):
        branch_points.append((current_x, current_y))
        current_y += random.randint(5, 12)
        current_x += random.randint(-10, 10)
        current_x = max(0, min(SCREEN_WIDTH, current_x))
    
    # Add branch to main points
    main_points.extend(branch_points)

def draw_lightning_bolt(bolt):
    """Draw a lightning bolt with zigzag lines"""
    if bolt['life'] <= 0:
        return
    
    # Draw the main lightning path
    points = bolt['points']
    if len(points) > 1:
        # Draw thick white line with slight blue tint
        color = (200, 220, 255)  # Slightly blue-white
        for i in range(len(points) - 1):
            pygame.draw.line(screen, color, points[i], points[i + 1], 3)
        
        # Draw bright white core
        core_color = (255, 255, 255)
        for i in range(len(points) - 1):
            pygame.draw.line(screen, core_color, points[i], points[i + 1], 1)
    
    # Decrease bolt life
    bolt['life'] -= 1
    
    # Remove dead bolts
    if bolt['life'] <= 0:
        lightning_bolts.remove(bolt)

def check_lightning_player_hit(bolt_x, bolt_ground_y):
    """Check if lightning hit the player (much rarer chance)"""
    global player
    
    # Calculate player position in screen coordinates
    player_screen_x = int(player["x"] * TILE_SIZE) - camera_x
    player_screen_y = int(player["y"] * TILE_SIZE) - camera_y
    
    # Check if lightning is close to player (within 50 pixels)
    distance = ((bolt_x - player_screen_x) ** 2 + (bolt_ground_y - player_screen_y) ** 2) ** 0.5
    
    if distance < 50:  # Lightning is close to player
        # Only 10% chance to actually hit player (much rarer!)
        if random.random() < 0.1:
            damage_player_from_lightning()

def damage_player_from_lightning():
    """Damage player when struck by lightning"""
    global player
    
    # Check if player is outside (not under a roof)
    player_x = int(player["x"])
    player_y = int(player["y"])
    
    # Simple check: if there's a block above the player, they're protected
    block_above = get_block(player_x, player_y - 1)
    if block_above and block_above != "air":
        return  # Player is protected
    
    # Damage player for 3 hearts
    player["health"] = max(0, player["health"] - 3)
    show_message("⚡ LIGHTNING STRUCK NEARBY! -3 hearts!", 3000)
    print(f"⚡ Lightning struck near player! Health: {player['health']}/10")
    
    # Check if player died
    if player["health"] <= 0:
        show_death_screen()

def update_weather():
    """Update weather system - change weather randomly"""
    global current_weather, weather_timer, weather_duration
    
    weather_timer += 1
    
    # Change weather every 10-30 MINUTES (36000-108000 frames at 60 FPS)
    if weather_timer >= weather_duration:
        # Random weather change
        weather_chances = {
            "clear": 0.5,   # 50% chance (more sunny days!)
            "rain": 0.25,   # 25% chance  
            "thunder": 0.15, # 15% chance
            "snow": 0.10    # 10% chance
        }
        
        # Choose new weather
        rand = random.random()
        cumulative = 0
        for weather, chance in weather_chances.items():
            cumulative += chance
            if rand <= cumulative:
                current_weather = weather
                break
        
        # Set new duration: 10-30 minutes (600-1800 seconds = 36000-108000 frames at 60 FPS)
        weather_duration = random.randint(36000, 108000)  # 10-30 minutes
        weather_timer = 0
        
        # Handle weather transitions
        if current_weather == "snow":
            start_snow_weather()
        elif current_weather == "clear" and len(snow_blocks) > 0:
            start_snow_melting()
        
        print(f"🌤️ Weather changed to: {current_weather}")

def accumulate_snow():
    """Gradually accumulate snow on surface blocks during snow weather"""
    global snow_blocks
    
    # Add snow more frequently for better coverage
    if random.random() > 0.3:  # 30% chance per frame (more snow!)
        return
    
    # Get player position for snow coverage area
    player_x = int(player["x"])
    player_y = int(player["y"])
    
    # Add snow to more locations around player
    for _ in range(5):  # Add to 5 random locations per frame
        dx = random.randint(-30, 30)
        x = player_x + dx
        
        # Find the top surface block by searching from a high point downward
        for search_y in range(max(0, player_y - 30), player_y + 30):
            block = get_block(x, search_y)
            block_above = get_block(x, search_y - 1)
            
            # Check if this is a surface block (solid block with air above)
            if block and block != "air" and block != "snow":
                if block_above == "air" or block_above is None:
                    # Only add snow on surface blocks (grass, dirt, stone, etc)
                    # Don't add snow on things like chests, doors, water, lava
                    if block in ["grass", "dirt", "stone", "sand", "oak_planks", "red_brick", "leaves", "coal", "iron", "gold", "diamond"]:
                        # Place snow ON TOP of the block (not replacing it)
                        snow_y = search_y - 1
                        snow_location = (x, snow_y)
                        
                        # Only add if there's air above and we haven't already placed snow here
                        if get_block(x, snow_y) == "air" and snow_location not in snow_blocks:
                            set_block(x, snow_y, "snow")
                            snow_blocks.append(snow_location)
                    break  # Found surface, move to next column

def start_snow_weather():
    """Start snow weather - initial message"""
    print("❄️ Snow weather started - snow will gradually cover the world!")

def start_snow_melting():
    """Start melting snow when weather changes from snow"""
    global snow_blocks
    
    print("☀️ Snow melting - removing snow blocks!")
    
    # Melt snow blocks one by one (slower process)
    if snow_blocks:
        # Remove a few snow blocks per frame
        for _ in range(min(5, len(snow_blocks))):
            if snow_blocks:
                x, y = snow_blocks.pop(0)
                # Remove snow (turn to air) - reveals original block underneath
                set_block(x, y, "air")

# =============================================================================
# LIGHTING AND DARKNESS SYSTEM
# =============================================================================

def draw_darkness_overlay():
    """Draw darkness overlay that gets darker as player goes deeper underground"""
    global player
    
    player_y = int(player["y"])
    surface_level = 50  # Approximate surface level
    
    # Calculate darkness based on depth
    depth = player_y - surface_level
    
    if depth <= 0:
        # Above ground - no darkness during day
        if is_day and current_weather != "thunder":
            return
        # At night or during thunder, add slight darkness
        darkness = 80
    else:
        # Underground - darkness increases with depth
        # Starts at depth 5, maximum darkness at depth 50
        darkness = min(220, int(depth * 4))
    
    # Create darkness overlay
    dark_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    dark_surface.fill((0, 0, 0))
    dark_surface.set_alpha(darkness)
    screen.blit(dark_surface, (0, 0))
    
    # Draw light circles around torches
    for torch_pos in light_sources:
        torch_x, torch_y = torch_pos
        
        # Convert to screen coordinates
        torch_screen_x = torch_x * TILE_SIZE - camera_x
        torch_screen_y = torch_y * TILE_SIZE - camera_y
        
        # Only draw light if torch is on screen
        if -100 < torch_screen_x < SCREEN_WIDTH + 100 and -100 < torch_screen_y < SCREEN_HEIGHT + 100:
            # Create light circle (cut out darkness)
            light_radius = 100  # Torch lights up 100 pixel radius
            
            # Draw gradient light circle
            for radius in range(light_radius, 0, -10):
                alpha = int((radius / light_radius) * darkness)
                light_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(light_surface, (0, 0, 0, alpha), (radius, radius), radius)
                
                # Subtract mode - removes darkness where torch is
                screen.blit(light_surface, 
                          (torch_screen_x + TILE_SIZE//2 - radius, 
                           torch_screen_y + TILE_SIZE//2 - radius),
                          special_flags=pygame.BLEND_RGBA_SUB)

def is_area_dark(x, y):
    """Check if an area is dark (for mob spawning)"""
    global player
    
    player_y = int(player["y"])
    surface_level = 50
    
    # Check if it's night time
    if not is_day:
        # Check if there's a torch nearby
        for torch_pos in light_sources:
            torch_x, torch_y = torch_pos
            distance = ((x - torch_x) ** 2 + (y - torch_y) ** 2) ** 0.5
            if distance < 3:  # Within 3 blocks of torch
                return False
        return True  # Dark at night without nearby torch
    
    # Check if underground
    if y > surface_level + 5:
        # Underground - check for nearby torches
        for torch_pos in light_sources:
            torch_x, torch_y = torch_pos
            distance = ((x - torch_x) ** 2 + (y - torch_y) ** 2) ** 0.5
            if distance < 3:  # Within 3 blocks of torch
                return False
        return True  # Dark underground without nearby torch
    
    return False  # Not dark during day above ground

def add_torch(x, y):
    """Add a torch as a light source"""
    global light_sources
    
    # Add to light sources list
    if (x, y) not in light_sources:
        light_sources.append((x, y))
        print(f"🔥 Torch placed at ({x}, {y}) - lights up area!")

def remove_torch(x, y):
    """Remove a torch light source"""
    global light_sources
    
    if (x, y) in light_sources:
        light_sources.remove((x, y))
        print(f"🔥 Torch removed at ({x}, {y})")

def update_light_sources():
    """Update light sources - remove torches that were broken"""
    global light_sources
    
    # Check each light source
    for torch_pos in light_sources[:]:
        torch_x, torch_y = torch_pos
        block = get_block(torch_x, torch_y)
        
        # Remove if torch block is gone
        if block != "torch":
            light_sources.remove(torch_pos)

# =============================================================================
# MONSTER HEALTH BAR SYSTEM
# =============================================================================

def show_monster_health(entity):
    """Show health bar for a monster when hit"""
    global monster_health_displays
    
    # Add or update health display
    found = False
    for display in monster_health_displays:
        if display["entity"] == entity:
            display["timer"] = 60  # Reset timer (1 second at 60 FPS)
            found = True
            break
    
    if not found:
        monster_health_displays.append({
            "entity": entity,
            "timer": 60
        })

def draw_monster_health_bars():
    """Draw health bars above monsters that were recently hit"""
    global monster_health_displays
    
    # Update and draw health bars
    for display in monster_health_displays[:]:
        entity = display["entity"]
        display["timer"] -= 1
        
        # Remove if timer expired
        if display["timer"] <= 0:
            monster_health_displays.remove(display)
            continue
        
        # Calculate fade alpha
        alpha = int((display["timer"] / 60.0) * 255)
        
        # Get entity position on screen
        entity_x = int(entity["x"] * TILE_SIZE) - camera_x
        entity_y = int(entity["y"] * TILE_SIZE) - camera_y
        
        # Health bar dimensions
        bar_width = 40
        bar_height = 6
        bar_x = entity_x + (TILE_SIZE - bar_width) // 2
        bar_y = entity_y - 10  # Above entity
        
        # Calculate health percentage
        hp = entity.get("hp", 0)
        max_hp = entity.get("max_hp", 1)
        health_percent = hp / max_hp if max_hp > 0 else 0
        
        # Draw background
        bg_surface = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
        bg_surface.fill((50, 50, 50, alpha))
        screen.blit(bg_surface, (bar_x, bar_y))
        
        # Draw health bar
        health_width = int(bar_width * health_percent)
        if health_width > 0:
            # Color based on health percentage
            if health_percent > 0.6:
                health_color = (0, 255, 0)  # Green
            elif health_percent > 0.3:
                health_color = (255, 255, 0)  # Yellow
            else:
                health_color = (255, 0, 0)  # Red
            
            health_surface = pygame.Surface((health_width, bar_height), pygame.SRCALPHA)
            health_surface.fill((*health_color, alpha))
            screen.blit(health_surface, (bar_x, bar_y))
        
        # Draw health numbers
        health_text = font.render(f"{hp}/{max_hp}", True, (255, 255, 255))
        health_text.set_alpha(alpha)
        text_x = bar_x + (bar_width - health_text.get_width()) // 2
        text_y = bar_y - 12
        screen.blit(health_text, (text_x, text_y))

# Village generation function removed - no more random NPCs

# Shop generation removed - now available in title screen

def generate_building(x, y, building_type):
    """Generate a specific type of building"""
    building_data = {
        "x": x,
        "y": y,
        "type": building_type,
        "spawn_point": {"x": x + 2, "y": y + 1}  # FIXED: Inside the building
    }
    
    if building_type == "house":
        # Generate a simple house (4x3 blocks)
        for dx in range(4):
            for dy in range(3):
                # Walls
                if dx == 0 or dx == 3 or dy == 2:
                    set_block(x + dx, y - dy, "oak_planks")
                # Floor
                elif dy == 1:
                    set_block(x + dx, y - dy, "oak_planks")
                # Roof
                elif dy == 0:
                    set_block(x + dx, y - dy, "oak_planks")
        
        # Door
        set_block(x + 1, y - 1, "door")
        set_block(x + 1, y - 2, "air")  # Door opening
        
        print(f"🏠 Generated house at ({x}, {y})")
        
    elif building_type == "farm":
        # Generate a farm with crops
        # Farm house (3x2 blocks)
        for dx in range(3):
            for dy in range(2):
                if dx == 0 or dx == 2 or dy == 1:
                    set_block(x + dx, y - dy, "oak_planks")
        
        # Door
        set_block(x + 1, y - 1, "door")
        
        # Farm plots around the house
        for dx in range(-2, 5):
            for dy in range(1, 4):
                if (dx + x, y + dy) not in [(x, y-1), (x, y-2), (x+1, y-1), (x+2, y-1), (x+2, y-2)]:
                    # Farm plot with carrots
                    if random.random() < 0.7:  # 70% chance for carrot
                        set_block(x + dx, y + dy, "carrot")
                    else:
                        set_block(x + dx, y + dy, "grass")
        
        print(f"🚜 Generated farm at ({x}, {y})")
        
    elif building_type == "cartographer":
        # Generate a cartographer's shop (4x3 blocks with special features)
        for dx in range(4):
            for dy in range(3):
                # Walls
                if dx == 0 or dx == 3 or dy == 2:
                    set_block(x + dx, y - dy, "red_brick")  # Fancier material
                # Floor
                elif dy == 1:
                    set_block(x + dx, y - dy, "oak_planks")
                # Roof
                elif dy == 0:
                    set_block(x + dx, y - dy, "red_brick")
        
        # Door
        set_block(x + 1, y - 1, "door")
        set_block(x + 1, y - 2, "air")
        
        # Special cartographer features
        set_block(x + 2, y - 1, "chest")  # Map storage chest
        
        print(f"🗺️ Generated cartographer shop at ({x}, {y})")
    
    # Shop building type removed - now available in title screen
    
    return building_data

def place_starter_chest(spawn_x, surface_y):
    """Place a starter chest next to the player with basic materials"""
    # Find a good spot for the starter chest (2-3 blocks to the right of spawn)
    chest_x = spawn_x + 3
    chest_y = surface_y
    
    # Check if we can place chest according to grass rule and position is clear
    if can_place_chest_on_grass(chest_x, chest_y) and get_block(chest_x, chest_y) is None:
        set_block(chest_x, chest_y, "chest")
        
        # Generate starter loot for the chest
        if hasattr(chest_system, 'generate_chest_loot'):
            generate_chest_with_shopkeeper_loot(chest_x, chest_y, "starter")
        
        print(f"🎁 Starter chest placed on grass at ({chest_x}, {chest_y})")
        return True
    else:
        # Try alternative positions if first spot doesn't work
        for offset in [2, 4, -2, -3]:
            alt_chest_x = spawn_x + offset
            if can_place_chest_on_grass(alt_chest_x, chest_y) and get_block(alt_chest_x, chest_y) is None:
                set_block(alt_chest_x, chest_y, "chest")
                if hasattr(chest_system, 'generate_chest_loot'):
                    generate_chest_with_shopkeeper_loot(alt_chest_x, chest_y, "starter")
                print(f"🎁 Starter chest placed on grass at alternative position ({alt_chest_x}, {chest_y})")
                return True
    
    print("⚠️ Could not find suitable grass position for starter chest")
    return False

def fix_player_spawn_position():
    """Ensure player spawns on the surface, not underground, or at bed spawn if available"""
    global player
    
    print(f"🏠 Fixing player spawn position from ({player['x']:.1f}, {player['y']:.1f})")
    
    # Check if player has a bed spawn point set
    if player.get("has_bed_spawn", False):
        bed_x = player["spawn_x"]
        bed_y = player["spawn_y"]
        print(f"🏠 Using bed spawn point at ({bed_x}, {bed_y})")
        
        # Set player position to bed spawn
        player["x"] = bed_x
        player["y"] = bed_y
        return
    
    # Keep the current X position but find proper Y position
    spawn_x = int(player["x"])
    
    # CRITICAL: Generate terrain at spawn point first!
    # This ensures terrain exists before we try to find a surface
    print(f"🌍 Generating terrain at spawn point ({spawn_x}) to ensure surface exists")
    
    # Generate terrain for a small area around spawn point
    for x in range(spawn_x - 5, spawn_x + 6):  # 11 columns around spawn
        generate_terrain_column(x)
        # Replace dirt/stone blocks adjacent to water with sand for natural beaches
    
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
            
            # Place starter chest next to player
            place_starter_chest(spawn_x, y)
            
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
            
            # Place starter chest next to player
            place_starter_chest(spawn_x, y)
            
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
    "water": make_beautiful_water_texture(TILE_SIZE),
    "lava": load_texture(os.path.join(TILE_DIR, "lava.png")),
    "sand": load_texture(os.path.join(TILE_DIR, "sand.png")),
    "snow": make_snow_texture(TILE_SIZE),  # Generated snow texture
    "torch": make_torch_texture(TILE_SIZE),  # Generated torch texture
    "bed": load_texture(os.path.join(TILE_DIR, "bed.png")),
    "ladder": make_ladder_texture(TILE_SIZE),
    "door": load_texture(os.path.join(TILE_DIR, "door.png")), 
    "bread": load_texture(os.path.join(ITEM_DIR, "bread.png")),
    "cooked_fish": load_texture(os.path.join(ITEM_DIR, "cooked_fish.png")),
    "steak": load_texture(os.path.join(ITEM_DIR, "steak.png")),
    "honey_jar": load_texture(os.path.join(ITEM_DIR, "honey_jar.png")),
    "wheat": load_texture(os.path.join(TILE_DIR, "carrot.gif")),  # Using carrot as wheat for now
    "stick": load_texture(os.path.join(TILE_DIR, "log.png")),  # Using log as stick for now
    
    # Potions (flipped upside down)
    "healing_potion": pygame.transform.flip(load_texture(os.path.join(ITEM_DIR, "potion.png")), False, True) if os.path.exists(os.path.join(ITEM_DIR, "potion.png")) else make_potion_texture(TILE_SIZE),
    "speed_potion": pygame.transform.flip(load_texture(os.path.join(ITEM_DIR, "potion.png")), False, True) if os.path.exists(os.path.join(ITEM_DIR, "potion.png")) else make_potion_texture(TILE_SIZE),
    "strength_potion": pygame.transform.flip(load_texture(os.path.join(ITEM_DIR, "potion.png")), False, True) if os.path.exists(os.path.join(ITEM_DIR, "potion.png")) else make_potion_texture(TILE_SIZE),
    
    "shopkeeper": load_texture(os.path.join(TILE_DIR, "shopkeeper.png")),
    "boss": load_texture(os.path.join(MOB_DIR, "boss.png")),
    
        # Portal texture removed - using ability system instead
}

# Create map texture programmatically
map_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
map_texture.fill((139, 69, 19))  # Brown background
# Draw map-like pattern
pygame.draw.rect(map_texture, (34, 139, 34), (4, 4, TILE_SIZE-8, TILE_SIZE-8))  # Green area
pygame.draw.line(map_texture, (0, 0, 0), (8, 8), (TILE_SIZE-8, TILE_SIZE-8), 2)  # Diagonal line
pygame.draw.line(map_texture, (0, 0, 0), (8, TILE_SIZE-8), (TILE_SIZE-8, 8), 2)  # Other diagonal
pygame.draw.circle(map_texture, (255, 215, 0), (TILE_SIZE//2, TILE_SIZE//2), 4)  # Gold center dot
textures["map"] = map_texture

# Villager texture removed

# --- Zombie texture (tries file, falls back to procedural) ---
try:
    textures["zombie"] = load_texture(os.path.join(MOB_DIR, "zombie.png"))
except Exception:
    textures["zombie"] = make_zombie_texture(TILE_SIZE)

# Shopkeeper texture removed

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

# Player Animation System
player_animations = {}

class PlayerAnimator:
    """Player animation system with proper GIF frame cycling"""
    
    def __init__(self):
        self.animations = {}  # Store animation data for each animation
        self.current_animation = "standing"
        self.frame_timers = {}  # Track frame timing for each animation
        self.load_animations()
    
    def load_animations(self):
        """Load all player animations from the animations folder and extract frames"""
        # Use PyInstaller-compatible path resolution
        if getattr(sys, 'frozen', False):
            # Running as executable - use bundled assets
            animations_dir = os.path.join(get_resource_path("assets"), "player", "animations")
        else:
            # Running as script - use relative path
            animations_dir = os.path.join("../../../../player", "animations")
        
        if not os.path.exists(animations_dir):
            print(f"⚠️ Animations directory not found: {animations_dir}")
            return
        
        animation_files = ["standing.gif", "walking.gif", "falling.gif"]
        
        for anim_file in animation_files:
            anim_path = os.path.join(animations_dir, anim_file)
            if os.path.exists(anim_path):
                try:
                    # Load the GIF and extract frames
                    frames = self.extract_gif_frames(anim_path)
                    if frames:
                        animation_name = anim_file.replace(".gif", "")
                        
                        # Set different frame rates for each animation
                        if animation_name == "walking":
                            frame_duration = 125  # 8 frames per second (1000ms / 8fps = 125ms)
                        elif animation_name == "standing":
                            frame_duration = 1000  # 1 frame per second (1000ms / 1fps = 1000ms)
                        elif animation_name == "falling":
                            frame_duration = 500   # 2 frames per second (1000ms / 2fps = 500ms)
                        else:
                            frame_duration = 100   # Default fallback
                        
                        self.animations[animation_name] = {
                            'frames': frames,
                            'current_frame': 0,
                            'frame_duration': frame_duration,
                            'last_frame_time': 0
                        }
                        self.frame_timers[animation_name] = 0
                        print(f"🎬 Loaded animation: {animation_name} with {len(frames)} frames at {1000//frame_duration}fps")
                    else:
                        print(f"⚠️ No frames extracted from {anim_file}")
                except Exception as e:
                    print(f"❌ Failed to load {anim_file}: {e}")
            else:
                print(f"⚠️ Animation file not found: {anim_path}")
        
        print(f"🎬 Animation system ready with {len(self.animations)} animations")
    
    def extract_gif_frames(self, gif_path):
        """Extract frames from a GIF file"""
        try:
            # Try to use PIL for proper GIF frame extraction
            try:
                from PIL import Image
                frames = []
                
                with Image.open(gif_path) as img:
                    # Check if it's animated by trying to seek to frame 1
                    is_animated = False
                    try:
                        img.seek(1)
                        is_animated = True
                        img.seek(0)  # Reset to first frame
                    except EOFError:
                        is_animated = False
                    
                    print(f"🎬 Processing {os.path.basename(gif_path)}: {'animated' if is_animated else 'static'}")
                    
                    # Convert to RGBA if needed
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    frame_count = 0
                    if is_animated:
                        # Extract all frames by reopening the image for each frame
                        frame_index = 0
                        while True:
                            try:
                                # Reopen the image for each frame to avoid corruption
                                with Image.open(gif_path) as frame_img:
                                    frame_img.seek(frame_index)
                                    
                                    # Convert to RGBA if needed
                                    if frame_img.mode != 'RGBA':
                                        frame_img = frame_img.convert('RGBA')
                                    
                                    # Convert PIL image to pygame surface
                                    frame_data = frame_img.convert('RGBA')
                                    frame_surface = pygame.image.fromstring(
                                        frame_data.tobytes(), frame_data.size, frame_data.mode
                                    )
                                    
                                    # Scale to player size
                                    scaled_frame = pygame.transform.scale(frame_surface, (TILE_SIZE, TILE_SIZE))
                                    frames.append(scaled_frame)
                                    frame_count += 1
                                    frame_index += 1
                                
                            except EOFError:
                                break
                            except Exception as e:
                                print(f"  Error extracting frame {frame_index}: {e}")
                                break
                    else:
                        # Single frame - just load it
                        frame_data = img.convert('RGBA')
                        frame_surface = pygame.image.fromstring(
                            frame_data.tobytes(), frame_data.size, frame_data.mode
                        )
                        scaled_frame = pygame.transform.scale(frame_surface, (TILE_SIZE, TILE_SIZE))
                        frames.append(scaled_frame)
                        frame_count = 1
                
                print(f"🎬 Extracted {frame_count} frames from {os.path.basename(gif_path)}")
                return frames
                
            except ImportError:
                # PIL not available, use pygame fallback
                print("⚠️ PIL not available, using single frame fallback")
                image = pygame.image.load(gif_path).convert_alpha()
                scaled_image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                return [scaled_image]
                
        except Exception as e:
            print(f"❌ Error extracting frames from {gif_path}: {e}")
            return []
    
    def get_animation(self, animation_name):
        """Get current frame of animation by name"""
        if animation_name not in self.animations:
            return None
        
        animation_data = self.animations[animation_name]
        frames = animation_data['frames']
        
        if not frames:
            return None
        
        # For single frame animations, just return the frame
        if len(frames) == 1:
            return frames[0]
        
        # For multi-frame animations, cycle through frames
        current_time = pygame.time.get_ticks()
        frame_duration = animation_data['frame_duration']
        
        # Check if it's time to advance to next frame
        if current_time - animation_data['last_frame_time'] >= frame_duration:
            old_frame = animation_data['current_frame']
            animation_data['current_frame'] = (animation_data['current_frame'] + 1) % len(frames)
            animation_data['last_frame_time'] = current_time
        
        return frames[animation_data['current_frame']]
    
    def set_animation(self, animation_name):
        """Set current animation"""
        if animation_name in self.animations:
            self.current_animation = animation_name
    
    def get_current_animation(self):
        """Get current animation frame"""
        return self.get_animation(self.current_animation)

# Initialize player animator
player_animator = PlayerAnimator()

# --- Ladder texture (tries file, falls back to procedural ladder texture) ---
try:
    textures["ladder"] = load_texture(os.path.join(TILE_DIR, "ladder.png"))  # preferred: assets/tiles/ladder.png
except Exception:
    # keep the already-generated ladder texture if file missing
    textures["ladder"] = make_ladder_texture(TILE_SIZE)


player_image = load_texture(os.path.join(PLAYER_DIR, "player.gif"))
monster_image = load_texture(os.path.join(MOB_DIR, "monster.gif"))
boss_image = load_texture(os.path.join(MOB_DIR, "boss.png"))
villager_image = load_texture(os.path.join(MOB_DIR, "villager.png"))
alive_hp = load_texture(os.path.join(HP_DIR, "alive_hp.png"))
dead_hp = load_texture(os.path.join(HP_DIR, "dead_hp.png"))

# Boss texture will be loaded when needed

# Load sound with error handling
try:
    damage_sound_path = os.path.join(SOUND_DIR, "damage_sound.wav")
    if os.path.exists(damage_sound_path):
        damage_sound = pygame.mixer.Sound(damage_sound_path)
        print(f"🔊 Loaded damage sound: {damage_sound_path}")
    else:
        print(f"⚠️ Sound file not found: {damage_sound_path}")
        damage_sound = None
except Exception as e:
    print(f"❌ Error loading damage sound: {e}")
    damage_sound = None

def play_damage_sound():
    """Safely play damage sound if available"""
    try:
        if damage_sound:
            damage_sound.play()
    except Exception as e:
        print(f"⚠️ Could not play damage sound: {e}")


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

# Map system variables
map_open = False
map_surface = None
map_scale = 4  # How many game pixels = 1 map pixel (higher = more detailed)
map_width = 200  # Map surface width in pixels
map_height = 150  # Map surface height in pixels
map_view_radius = 50  # How many blocks around player to show on map


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
            "facing_direction": 1,  # 1 = right, -1 = left
        "last_x": 10,  # Initialize last position for movement detection
        "last_y": 0,
    "spawn_x": 10,  # Bed spawn point
    "spawn_y": 0,   # Bed spawn point
    "has_bed_spawn": False,  # Whether player has set a bed spawn
    "fall_start_y": None,  # Track where fall started for damage calculation
    "fall_height": 0.0  # Current fall height
}

# Username will be loaded from username.json file

MAX_FALL_SPEED = 10
GRAVITY = 1
JUMP_STRENGTH = -12  # Increased from -8 to -12 for higher jumping to clear blocks
# Movement speeds - frame-rate independent for consistent gameplay across devices
MOVE_SPEED = 0.15  # Fast, responsive movement
SLOW_SPEED = 0.08  # Slower when holding shift

# Fall damage system
FALL_DAMAGE_THRESHOLD = 4.0  # Take damage when falling from 4+ blocks
FALL_DAMAGE_MULTIPLIER = 1.5  # Damage per block above threshold


# World and camera
world_data = {}
entities = []
camera_x = 0
camera_y = 0  # Vertical camera position
fall_start_y = None
# Village generation removed
generated_terrain_columns = set()  # Track which columns have had terrain generated
broken_grass_locations = set()  # Track grass blocks that have been broken by the player

# --- Message HUD (temporary notifications) ---
message_text = ""
message_until = 0  # pygame.time.get_ticks() deadline

# Villager dialogue system removed

# --- Door System ---
door_states = {}  # Track which doors are open/closed


# EXTREME ENGINEERING: Legendary Boss Fight System
BOSS_SPAWN_DISTANCE = 0  # Boss arena at spawn location
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

# Legend NPC system removed - no more random NPCs

# =============================================================================
# ABILITY SYSTEM - MONSTER KILL BASED
# =============================================================================

# Monster kill tracking
monsters_killed = 0
total_monsters_killed = 0  # Total monsters killed in this session

# Ability system removed - no more wall jump

# =============================================================================
# FOOD SYSTEM
# =============================================================================

# Food definitions with hunger and health restoration
FOOD_ITEMS = {
    # Existing foods
    "carrot": {"hunger": 2, "health": 1, "rarity": 0.15},  # Common
    "bread": {"hunger": 3, "health": 0, "rarity": 0.12},   # Common
    
    # NEW FOODS
    "cooked_fish": {"hunger": 4, "health": 1, "rarity": 0.10},      # Grilled fish
    "steak": {"hunger": 5, "health": 2, "rarity": 0.08},            # Cooked beef
    "honey_jar": {"hunger": 2, "health": 3, "rarity": 0.06}         # Sweet honey (best healing!)
}

# =============================================================================
# CRAFTING SYSTEM
# =============================================================================

# Crafting recipes - {result: {materials: {item: count}, output_count: num}}
CRAFTING_RECIPES = {
    "pickaxe": {
        "materials": {"oak_planks": 2},
        "output_count": 1,
        "description": "Basic tool for mining"
    },
    "sword": {
        "materials": {"oak_planks": 3},
        "output_count": 1,
        "description": "Wooden sword for combat"
    },
    "stone_sword": {
        "materials": {"stone": 3, "oak_planks": 1},
        "output_count": 1,
        "description": "Stronger stone sword"
    },
    "chest": {
        "materials": {"oak_planks": 4},
        "output_count": 1,
        "description": "Storage container"
    },
    "door": {
        "materials": {"oak_planks": 10},
        "output_count": 1,
        "description": "Wooden door"
    },
    "bed": {
        "materials": {"oak_planks": 3, "leaves": 2},
        "output_count": 1,
        "description": "Sleep through the night"
    },
    "ladder": {
        "materials": {"oak_planks": 5},
        "output_count": 3,
        "description": "Climb up and down"
    },
    "torch": {
        "materials": {"coal": 1, "oak_planks": 1},
        "output_count": 4,
        "description": "Light source"
    },
    "oak_planks": {
        "materials": {"log": 1},
        "output_count": 4,
        "description": "Building material"
    },
    "bread": {
        "materials": {"wheat": 3},
        "output_count": 1,
        "description": "Basic food"
    },
    "red_brick": {
        "materials": {"stone": 2, "coal": 1},
        "output_count": 4,
        "description": "Decorative building block"
    }
}

# Crafting UI state
crafting_mode = False
selected_crafting_materials = {}  # {item_type: count}
crafting_result = None
crafting_scroll_offset = 0  # For scrolling through recipes
show_all_recipes = False  # Whether to show all recipes or just the limited view
# Removed double-click variables - now using right-click for crafting selection

def check_can_craft(materials_dict):
    """Check what can be crafted with the given materials"""
    possible_recipes = []
    
    for recipe_name, recipe in CRAFTING_RECIPES.items():
        can_craft = True
        required = recipe.get("materials", {})
        
        # Make sure required is a dict
        if not isinstance(required, dict):
            print(f"⚠️ Warning: Recipe {recipe_name} has invalid materials format")
            continue
        
        # Check if player has all required materials
        for material, needed_count in required.items():
            player_has = materials_dict.get(material, 0)
            if player_has < needed_count:
                can_craft = False
                break
        
        if can_craft:
            possible_recipes.append(recipe_name)
    
    return possible_recipes

def craft_item(recipe_name):
    """Craft an item from selected materials"""
    global selected_crafting_materials, crafting_result
    
    if recipe_name not in CRAFTING_RECIPES:
        print(f"❌ Unknown recipe: {recipe_name}")
        return False
    
    recipe = CRAFTING_RECIPES[recipe_name]
    
    # Verify player has materials
    for material, count in recipe["materials"].items():
        if selected_crafting_materials.get(material, 0) < count:
            show_message(f"❌ Not enough {material}!", 2000)
            return False
    
    # Consume materials
    for material, count in recipe["materials"].items():
        selected_crafting_materials[material] -= count
        if selected_crafting_materials[material] <= 0:
            del selected_crafting_materials[material]
        
        # Remove from actual inventory
        remove_from_inventory(material, count)
    
    # Add crafted item to inventory
    output_count = recipe.get("output_count", 1)
    add_to_inventory(recipe_name, output_count)
    
    show_message(f"✅ Crafted {output_count}x {recipe_name.replace('_', ' ').title()}!", 2000)
    print(f"🔨 Crafted {output_count}x {recipe_name}")
    
    crafting_result = None
    return True

def remove_from_inventory(item_type, count):
    """Remove count of item_type from inventory"""
    remaining = count
    
    for item in player["inventory"]:
        if item and item.get("type") == item_type:
            if item.get("count", 1) >= remaining:
                item["count"] -= remaining
                if item["count"] <= 0:
                    player["inventory"][player["inventory"].index(item)] = None
                return
            else:
                remaining -= item.get("count", 1)
                player["inventory"][player["inventory"].index(item)] = None
    
    normalize_inventory()

def eat_food(food_type):
    """Eat a food item and restore hunger/health"""
    if food_type not in FOOD_ITEMS:
        print(f"❌ {food_type} is not a food item!")
        return False
    
    food_data = FOOD_ITEMS[food_type]
    hunger_restore = food_data["hunger"]
    health_restore = food_data["health"]
    
    # Check if player needs food (not already full)
    if player["hunger"] >= 10 and player["health"] >= 10:
        show_message(f"🍖 Already full! Can't eat {food_type.replace('_', ' ').title()}.", 1500)
        print(f"🍖 Can't eat {food_type} - hunger and health are already full")
        return False
    
    # Restore hunger (max 10)
    old_hunger = player["hunger"]
    player["hunger"] = min(10, player["hunger"] + hunger_restore)
    hunger_gained = player["hunger"] - old_hunger
    
    # Restore health (max 10)
    old_health = player["health"]
    player["health"] = min(10, player["health"] + health_restore)
    health_gained = player["health"] - old_health
    
    # Display message
    food_name = food_type.replace("_", " ").title()
    message_parts = []
    if hunger_gained > 0:
        message_parts.append(f"+{hunger_gained} Hunger")
    if health_gained > 0:
        message_parts.append(f"+{health_gained} Health")
    
    if message_parts:
        show_message(f"🍖 Ate {food_name}: {', '.join(message_parts)}!", 2000)
        print(f"🍖 Ate {food_name}: Hunger {old_hunger} → {player['hunger']}, Health {old_health} → {player['health']}")
    
        return True

# =============================================================================
# OXYGEN SYSTEM
# =============================================================================

# Oxygen system variables
oxygen_level = 100  # Maximum oxygen level
max_oxygen = 100
oxygen_timer = 0
oxygen_decrease_rate = 0.5  # Oxygen decreases by 0.5 per frame when underwater
oxygen_recovery_rate = 2.0  # Oxygen recovers by 2.0 per frame when above water
underwater = False
oxygen_bar_visible = False

def update_oxygen_system():
    """Update oxygen system based on player position"""
    global oxygen_level, underwater, oxygen_bar_visible, oxygen_timer
    
    # Check if player is underwater
    px, py = int(player["x"]), int(player["y"])
    current_block = get_block(px, py)
    
    # Check if player is in water
    if current_block == "water":
        underwater = True
        oxygen_bar_visible = True
        
        # Decrease oxygen when underwater
        oxygen_level -= oxygen_decrease_rate
        if oxygen_level < 0:
            oxygen_level = 0
            
        # Take damage if oxygen runs out
        if oxygen_level <= 0:
            player["health"] -= 0.1  # Drown damage
            if player["health"] <= 0:
                show_death_screen()
    else:
        underwater = False
        
        # Recover oxygen when above water
        if oxygen_level < max_oxygen:
            oxygen_level += oxygen_recovery_rate
            if oxygen_level > max_oxygen:
                oxygen_level = max_oxygen
        
        # Hide oxygen bar after a delay when above water
        if oxygen_level >= max_oxygen:
            oxygen_timer += 1
            if oxygen_timer >= 60:  # Hide after 1 second
                oxygen_bar_visible = False
                oxygen_timer = 0
        else:
            oxygen_timer = 0

def draw_oxygen_bar():
    """Draw the oxygen bar when underwater"""
    if not oxygen_bar_visible:
        return
    
    # Oxygen bar dimensions
    bar_width = 200
    bar_height = 20
    bar_x = 20
    bar_y = 100  # Below health bar
    
    # Background (dark blue)
    pygame.draw.rect(screen, (0, 50, 100), (bar_x, bar_y, bar_width, bar_height))
    
    # Oxygen level (light blue)
    oxygen_width = int((oxygen_level / max_oxygen) * bar_width)
    pygame.draw.rect(screen, (0, 150, 255), (bar_x, bar_y, oxygen_width, bar_height))
    
    # Border
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
    
    # Oxygen text
    oxygen_text = font.render(f"Oxygen: {int(oxygen_level)}%", True, (255, 255, 255))
    screen.blit(oxygen_text, (bar_x, bar_y - 25))

# =============================================================================
# BEACH GENERATION SYSTEM
# =============================================================================

def generate_beach(center_x, surface_y):
    """Generate a beach with water and sand"""
    global world_data
    
    # Beach dimensions
    beach_width = random.randint(20, 40)
    beach_height = random.randint(5, 10)
    
    # Generate beach area
    for x in range(center_x - beach_width//2, center_x + beach_width//2 + 1):
        for y in range(surface_y - beach_height, surface_y + 1):
            # Create beach with sand and water
            if y == surface_y:
                # Surface level - mix of sand and water
                if random.random() < 0.7:  # 70% sand
                    set_block(x, y, "sand")
                else:  # 30% water
                    set_block(x, y, "water")
            elif y < surface_y:
                # Below surface - mostly water
                if random.random() < 0.8:  # 80% water
                    set_block(x, y, "water")
                else:  # 20% sand
                    set_block(x, y, "sand")
    
    print(f"🏖️ Beach generated at ({center_x}, {surface_y}) with water and sand!")

# =============================================================================
# COOL STRUCTURES GENERATION
# =============================================================================

# Structure variables
structures = []  # List of generated structures
bosses = []  # List of boss entities

# Fortress functions removed - replaced with cool structures system

def update_fortress_bosses_removed():
    """Update fortress boss AI and behavior"""
    for boss in entities:
        if boss["type"] == "fortress_boss":
            # Boss movement
            boss["movement_timer"] += 1
            
            if boss["movement_timer"] >= 180:  # Move every 3 seconds
                boss["movement_timer"] = 0
                
                # Move towards player
                dx = player["x"] - boss["x"]
                dy = player["y"] - boss["y"]
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    speed = 0.01
                    boss["x"] += speed * dx / distance
                    boss["y"] += speed * dy / distance
            
            # Boss attacks
            boss["attack_timer"] += 1
            
            if boss["attack_timer"] >= boss["attack_cooldown"]:
                # Check if player is in range
                dx = player["x"] - boss["x"]
                dy = player["y"] - boss["y"]
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance <= 3:  # Attack range
                    # Create fireball projectile
                    entities.append({
                        "type": "fireball",
                        "x": boss["x"],
                        "y": boss["y"],
                        "dx": 0.1 * dx / distance,
                        "dy": 0.1 * dy / distance,
                        "damage": 5,
                        "lifetime": 120
                    })
                    
                    boss["attack_timer"] = 0
                    print("🔥 Fortress Boss shoots fireball!")

def update_fireball_projectiles():
    """Update fireball projectiles"""
    global entities
    
    for projectile in entities[:]:
        if projectile["type"] == "fireball":
            # Move fireball
            projectile["x"] += projectile["dx"]
            projectile["y"] += projectile["dy"]
            
            # Decrease lifetime
            projectile["lifetime"] -= 1
            
            # Check collision with player
            dx = player["x"] - projectile["x"]
            dy = player["y"] - projectile["y"]
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance <= 0.5:  # Hit player
                damage = calculate_armor_damage_reduction(projectile["damage"])
                player["health"] -= damage
                play_damage_sound()
                entities.remove(projectile)
                print(f"🔥 Fireball hit player for {damage} damage!")
                continue
            
            # Remove if lifetime expired
            if projectile["lifetime"] <= 0:
                entities.remove(projectile)

# =============================================================================
# VILLAGE SYSTEM
# =============================================================================

# Village variables
villages = []  # List of village data
villagers = []  # List of villager entities

def generate_village(center_x, surface_y):
    """Generate a proper village with houses, beds, and villagers"""
    global villages
    
    # Village size and layout
    village_width = random.randint(15, 25)
    village_height = random.randint(8, 12)
    
    # Create village data
    village_data = {
        "center": (center_x, surface_y),
        "size": (village_width, village_height),
        "houses": [],
        "villagers": [],
        "beds": [],
        "chests": []
    }
    
    # Generate houses
    num_houses = random.randint(3, 6)
    for i in range(num_houses):
        house_x = center_x + random.randint(-village_width//2, village_width//2)
        house_y = surface_y + random.randint(-village_height//2, village_height//2)
        
        # Generate individual house
        house_data = generate_house(house_x, house_y)
        village_data["houses"].append(house_data)
        
        # Add house beds to village beds
        village_data["beds"].extend(house_data["beds"])
        
        # Add house chests to village chests
        village_data["chests"].extend(house_data["chests"])
    
    # Generate villagers
    num_villagers = random.randint(2, 4)
    for i in range(num_villagers):
        villager_x = center_x + random.randint(-village_width//2, village_width//2)
        villager_y = surface_y + random.randint(-village_height//2, village_height//2)
        
        # Spawn villager
        villager_data = spawn_villager(villager_x, villager_y)
        village_data["villagers"].append(villager_data)
    
    villages.append(village_data)
    print(f"🏘️ Village generated at ({center_x}, {surface_y}) with {num_houses} houses and {num_villagers} villagers!")

def generate_house(house_x, house_y):
    """Generate a single house with beds and chest, properly embedded in ground"""
    house_width = random.randint(4, 7)
    house_height = random.randint(3, 5)
    
    house_data = {
        "center": (house_x, house_y),
        "size": (house_width, house_height),
        "beds": [],
        "chests": []
    }
    
    # Clear the ground underneath to prevent floating
    for x in range(house_x - house_width//2 - 1, house_x + house_width//2 + 2):
        # Fill ground beneath house with stone (foundation)
        for y in range(house_y + 1, house_y + 3):
            if get_block(x, y) is None:
                set_block(x, y, "stone")
    
    # Create house structure
    for x in range(house_x - house_width//2, house_x + house_width//2 + 1):
        for y in range(house_y - house_height, house_y + 1):
            # Floor
            if y == house_y:
                set_block(x, y, "oak_planks")
            # Walls
            elif x == house_x - house_width//2 or x == house_x + house_width//2 or y == house_y - house_height:
                set_block(x, y, "oak_planks")
            # Interior (air)
            else:
                set_block(x, y, "air")
    
    # Add beds inside house
    num_beds = random.randint(1, 2)
    for i in range(num_beds):
        bed_x = house_x + random.randint(-house_width//2 + 1, house_width//2 - 1)
        bed_y = house_y - random.randint(1, house_height - 1)
        
        if get_block(bed_x, bed_y) == "air":
            set_block(bed_x, bed_y, "bed")
            house_data["beds"].append((bed_x, bed_y))
    
    # Add chest inside house
    chest_x = house_x + random.randint(-house_width//2 + 1, house_width//2 - 1)
    chest_y = house_y - random.randint(1, house_height - 1)
    
    if get_block(chest_x, chest_y) == "air":
        set_block(chest_x, chest_y, "chest")
        house_data["chests"].append((chest_x, chest_y))
    
    return house_data

def spawn_villager(villager_x, villager_y):
    """Spawn a villager entity with a random job"""
    # Random villager jobs
    jobs = [
        {
            "name": "Farmer",
            "dialogue": [
                "I grow the best crops in the village!",
                "Need some food? Check our fields!",
                "The soil here is perfect for farming!",
                "I've been farming for 20 years!",
                "Fresh vegetables, anyone?"
            ]
        },
        {
            "name": "Blacksmith",
            "dialogue": [
                "I forge the finest tools in the land!",
                "Need a new pickaxe? I can help!",
                "My forge burns day and night!",
                "Quality tools for quality work!",
                "I've been smithing since I was young!"
            ]
        },
        {
            "name": "Merchant",
            "dialogue": [
                "Welcome to my shop, traveler!",
                "I have the best prices in town!",
                "Looking for something specific?",
                "Trade is the lifeblood of our village!",
                "I travel far to get rare goods!"
            ]
        },
        {
            "name": "Guard",
            "dialogue": [
                "I keep this village safe from monsters!",
                "Have you seen any threats nearby?",
                "Safety is our top priority!",
                "I patrol the village day and night!",
                "Stay alert, traveler!"
            ]
        },
        {
            "name": "Builder",
            "dialogue": [
                "I built most of these houses myself!",
                "Need help with construction?",
                "A good foundation is everything!",
                "I take pride in my craftsmanship!",
                "This village is my masterpiece!"
            ]
        }
    ]
    
    job = random.choice(jobs)
    
    villager_data = {
        "type": "villager",
        "x": float(villager_x),
        "y": float(villager_y),
        "image": villager_image,
        "hp": 20,
        "max_hp": 20,
        "job": job["name"],
        "dialogue": job["dialogue"],
        "current_dialogue": 0,
        "last_interaction": 0,
        "movement_timer": 0,
        "target_x": villager_x,
        "target_y": villager_y
    }
    
    # Add to entities
    entities.append(villager_data)
    print(f"👤 Villager spawned at ({villager_x}, {villager_y})")
    
    return villager_data

def update_villagers():
    """Update villager AI and behavior"""
    for villager in entities:
        if villager["type"] == "villager":
            # Simple villager movement (wander around)
            villager["movement_timer"] += 1
            
            if villager["movement_timer"] >= 300:  # Move every 5 seconds
                villager["movement_timer"] = 0
                
                # Choose new target position
                current_x = villager["x"]
                current_y = villager["y"]
                
                # Move in random direction
                direction = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
                new_x = current_x + direction[0] * random.randint(1, 3)
                new_y = current_y + direction[1] * random.randint(1, 3)
                
                # Check if new position is valid (not blocked)
                if get_block(int(new_x), int(new_y)) == "air":
                    villager["target_x"] = new_x
                    villager["target_y"] = new_y
                
                # Move towards target
                dx = villager["target_x"] - villager["x"]
                dy = villager["target_y"] - villager["y"]
                
                if abs(dx) > 0.1 or abs(dy) > 0.1:
                    speed = 0.02
                    villager["x"] += speed * dx
                    villager["y"] += speed * dy

def interact_with_villager(villager):
    """Handle villager interaction"""
    current_time = pygame.time.get_ticks()
    
    # Prevent spam clicking
    if current_time - villager["last_interaction"] < 2000:  # 2 second cooldown
        return
    
    villager["last_interaction"] = current_time
    
    # Cycle through dialogue
    dialogue = villager["dialogue"][villager["current_dialogue"]]
    job_name = villager.get("job", "Villager")
    show_message(f"👤 {job_name}: {dialogue}", 3000)
    print(f"👤 {job_name} says: {dialogue}")
    
    # Move to next dialogue
    villager["current_dialogue"] = (villager["current_dialogue"] + 1) % len(villager["dialogue"])

# =============================================================================
# LOST RUINS DUNGEON SYSTEM
# =============================================================================

# Lost Ruins variables
lost_ruins_entrances = []  # List of Lost Ruins entrance positions
lost_ruins_systems = []    # List of Lost Ruins system data
final_boss_active = False  # Whether the final boss is currently active
final_boss_position = None  # Position of the final boss
final_boss_health = 100  # Final boss health
final_boss_max_health = 100  # Final boss max health
credits_from_boss_defeat = False  # Whether credits screen is shown due to boss defeat

def generate_lost_ruins(center_x, surface_y):
    """Generate the Lost Ruins dungeon with portal to final boss"""
    global lost_ruins_entrances, lost_ruins_systems
    
    # Lost Ruins entrance (underground)
    entrance_width = 4
    entrance_height = 3
    entrance_y = surface_y - 10  # 10 blocks underground
    
    # Create entrance
    for x in range(center_x - entrance_width//2, center_x + entrance_width//2 + 1):
        for y in range(entrance_y - entrance_height, entrance_y + 1):
            if get_block(x, y) in ["stone", "dirt", "grass"]:
                set_block(x, y, "air")
    
    # Add entrance to list
    lost_ruins_entrances.append((center_x, entrance_y))
    
    # Generate Lost Ruins structure
    ruins_data = {
        "entrance": (center_x, entrance_y),
        "rooms": [],
        "portal_room": None,
        "boss_room": None
    }
    
    # Main hall (5x8 room)
    hall_x = center_x
    hall_y = entrance_y - 5
    hall_width = 5
    hall_height = 8
    
    for rx in range(hall_x - hall_width//2, hall_x + hall_width//2 + 1):
        for ry in range(hall_y - hall_height, hall_y + 1):
            if get_block(rx, ry) in ["stone", "dirt", "grass"]:
                set_block(rx, ry, "air")
    
    ruins_data["rooms"].append((hall_x, hall_y, hall_width, hall_height))
    
    # Portal room (4x6 room)
    portal_x = center_x - 8
    portal_y = entrance_y - 5
    portal_width = 4
    portal_height = 6
    
    for rx in range(portal_x - portal_width//2, portal_x + portal_width//2 + 1):
        for ry in range(portal_y - portal_height, portal_y + 1):
            if get_block(rx, ry) in ["stone", "dirt", "grass"]:
                set_block(rx, ry, "air")
    
    # Place portal in portal room
    set_block(portal_x, portal_y, "portal")
    ruins_data["portal_room"] = (portal_x, portal_y, portal_width, portal_height)
    
    # Boss room (6x8 room)
    boss_x = center_x + 8
    boss_y = entrance_y - 5
    boss_width = 6
    boss_height = 8
    
    for rx in range(boss_x - boss_width//2, boss_x + boss_width//2 + 1):
        for ry in range(boss_y - boss_height, boss_y + 1):
            if get_block(rx, ry) in ["stone", "dirt", "grass"]:
                set_block(rx, ry, "air")
    
    # Place final boss in boss room
    global final_boss_position
    final_boss_position = (boss_x, boss_y - 2)
    ruins_data["boss_room"] = (boss_x, boss_y, boss_width, boss_height)
    
    # Add torches for lighting
    torch_positions = [
        (center_x - 2, entrance_y - 2),
        (center_x + 2, entrance_y - 2),
        (portal_x, portal_y - 2),
        (boss_x - 2, boss_y - 2),
        (boss_x + 2, boss_y - 2)
    ]
    
    for tx, ty in torch_positions:
        if get_block(tx, ty) == "air":
            set_block(tx, ty, "torch")
    
    lost_ruins_systems.append(ruins_data)
    print(f"🏛️ Lost Ruins generated at ({center_x}, {entrance_y}) with portal and boss room!")

def spawn_final_boss():
    """Spawn the final boss in the Lost Ruins"""
    global final_boss_active, final_boss_position, final_boss_health, final_boss_max_health
    
    if final_boss_position and not final_boss_active:
        boss_x, boss_y = final_boss_position
        
        # Add boss to entities
        entities.append({
            "type": "final_boss",
            "x": float(boss_x),
            "y": float(boss_y),
            "hp": final_boss_health,
            "max_hp": final_boss_max_health,
            "cooldown": 0,
            "image": boss_image,
            "phase": 1,
            "attack_timer": 0
        })
        
        final_boss_active = True
        print(f"👹 Final boss spawned at ({boss_x}, {boss_y})!")

def update_final_boss():
    """Update final boss AI and attacks"""
    global final_boss_active, final_boss_health
    
    if not final_boss_active:
        return
    
    # Find the boss entity
    boss_entity = None
    for entity in entities:
        if entity["type"] == "final_boss":
            boss_entity = entity
            break
    
    if not boss_entity:
        final_boss_active = False
        return
    
    # Update boss health
    final_boss_health = boss_entity["hp"]
    
    # Boss AI - chase player
    player_x = player["x"]
    player_y = player["y"]
    boss_x = boss_entity["x"]
    boss_y = boss_entity["y"]
    
    dx = player_x - boss_x
    dy = player_y - boss_y
    dist = math.sqrt(dx*dx + dy*dy)
    
    if dist > 0:
        # Move towards player
        speed = 0.05
        boss_entity["x"] += speed * dx / dist
        boss_entity["y"] += speed * dy / dist
    
    # Boss attacks
    boss_entity["attack_timer"] += 1
    if boss_entity["attack_timer"] >= 120:  # Attack every 2 seconds
        boss_entity["attack_timer"] = 0
        
        # Ranged attack - fire projectiles
        if dist > 0:
            entities.append({
                "type": "boss_projectile",
                "x": boss_x,
                "y": boss_y,
                "dx": 0.2 * dx / dist,
                "dy": 0.2 * dy / dist,
                "damage": 5,
                "lifetime": 180
            })
            print("🔥 Boss fired projectile!")
    
    # Contact damage
    if dist < 1.5:
        current_time = pygame.time.get_ticks()
        if "last_attack_time" not in boss_entity:
            boss_entity["last_attack_time"] = 0
        
        if current_time - boss_entity["last_attack_time"] >= 2000:  # 2 second cooldown
            damage = calculate_armor_damage_reduction(8)  # 8 damage
            player["health"] -= damage
            play_damage_sound()
            boss_entity["last_attack_time"] = current_time
            print(f"👹 Boss attacked player for {damage} damage!")
            if player["health"] <= 0:
                show_death_screen()

# =============================================================================
# CAVE GENERATION SYSTEM REMOVED
# =============================================================================

# Cave generation variables (removed)
cave_entrances = []  # Empty list - caves disabled
cave_systems = []    # Empty list - caves disabled

# Cave generation functions removed

# =============================================================================
# PERFORMANCE MONITORING SYSTEM
# =============================================================================

# Performance monitoring variables
performance_monitor = {
    "frame_times": [],
    "max_frame_time": 0,
    "avg_frame_time": 0,
    "frame_count": 0,
    "last_fps_check": 0,
    "lag_spikes": 0,
    "show_stats": False  # Toggle for displaying performance stats
}

def update_performance_monitor():
    """Monitor game performance and detect lag spikes"""
    global performance_monitor
    
    current_time = pygame.time.get_ticks()
    frame_time = current_time - performance_monitor.get("last_frame_time", current_time)
    performance_monitor["last_frame_time"] = current_time
    
    # Track frame times
    performance_monitor["frame_times"].append(frame_time)
    if len(performance_monitor["frame_times"]) > 60:  # Keep last 60 frames
        performance_monitor["frame_times"].pop(0)
    
    # Calculate average frame time
    if performance_monitor["frame_times"]:
        performance_monitor["avg_frame_time"] = sum(performance_monitor["frame_times"]) / len(performance_monitor["frame_times"])
        performance_monitor["max_frame_time"] = max(performance_monitor["frame_times"])
    
    # Detect lag spikes (frame time > 33ms = < 30 FPS)
    if frame_time > 33:
        performance_monitor["lag_spikes"] += 1
        if performance_monitor["lag_spikes"] % 10 == 0:  # Log every 10th lag spike
            print(f"⚠️ Performance warning: Frame time {frame_time:.1f}ms (should be < 16ms for 60 FPS)")
    
    # Reset lag spike counter occasionally
    if performance_monitor["frame_count"] % 300 == 0:  # Every 5 seconds at 60 FPS
        performance_monitor["lag_spikes"] = 0
    
    performance_monitor["frame_count"] += 1

def get_performance_stats():
    """Get current performance statistics"""
    return {
        "avg_frame_time": performance_monitor["avg_frame_time"],
        "max_frame_time": performance_monitor["max_frame_time"],
        "fps": 1000 / performance_monitor["avg_frame_time"] if performance_monitor["avg_frame_time"] > 0 else 0,
        "lag_spikes": performance_monitor["lag_spikes"]
    }

def draw_performance_stats():
    """Draw performance statistics on screen with player coordinates"""
    if not performance_monitor["show_stats"]:
        return
    
    stats = get_performance_stats()
    
    # Draw semi-transparent background (moved down to not cover player info)
    overlay = pygame.Surface((300, 160), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (10, 80))  # Moved down from y=10 to y=80
    
    # Draw player coordinates
    player_x = int(player["x"])
    player_y = int(player["y"])
    coords_text = font.render(f"Position: ({player_x}, {player_y})", True, (100, 255, 100))
    screen.blit(coords_text, (20, 90))
    
    # Draw performance stats
    fps_text = font.render(f"FPS: {stats['fps']:.1f}", True, (255, 255, 255))
    screen.blit(fps_text, (20, 110))
    
    frame_time_text = font.render(f"Frame Time: {stats['avg_frame_time']:.1f}ms", True, (255, 255, 255))
    screen.blit(frame_time_text, (20, 130))
    
    max_frame_text = font.render(f"Max Frame: {stats['max_frame_time']:.1f}ms", True, (255, 255, 255))
    screen.blit(max_frame_text, (20, 150))
    
    lag_text = font.render(f"Lag Spikes: {stats['lag_spikes']}", True, (255, 100, 100) if stats['lag_spikes'] > 0 else (255, 255, 255))
    screen.blit(lag_text, (20, 170))
    
    # Draw toggle instruction
    toggle_text = font.render("Press F3 to toggle", True, (200, 200, 200))
    screen.blit(toggle_text, (20, 190))

# =============================================================================
# MERCHANT SYSTEM - BRAND NEW SHOPKEEPER
# =============================================================================

# Merchant system variables
merchant_shop_open = False  # Whether merchant shop is currently open
merchant_block_pos = None  # Position of the merchant block being used
merchant_selected_category = "tools"  # Current category being viewed
merchant_page = 0  # Current page of items

# Merchant shop items with prices and descriptions
MERCHANT_ITEMS = {
    # TOOLS & WEAPONS
    "tools": {
        "iron_pickaxe": {
            "name": "Iron Pickaxe",
            "price": 1000,
            "description": "Mines 2x faster than stone",
            "rarity": "common"
        },
        "diamond_pickaxe": {
            "name": "Diamond Pickaxe",
            "price": 5000,
            "description": "Mines 3x faster than stone",
            "rarity": "rare"
        },
        "netherite_pickaxe": {
            "name": "Netherite Pickaxe", 
            "price": 15000,
            "description": "Mines 5x faster, unbreakable",
            "rarity": "epic"
        },
        "iron_sword": {
            "name": "Iron Sword",
            "price": 800,
            "description": "Deals 5 damage per hit",
            "rarity": "common"
        },
        "diamond_sword": {
            "name": "Diamond Sword",
            "price": 3000,
            "description": "Deals 8 damage per hit",
            "rarity": "rare"
        },
        "netherite_sword": {
            "name": "Netherite Sword",
            "price": 12000,
            "description": "Deals 12 damage per hit",
            "rarity": "epic"
        }
    },
    
    # ARMOR
    "armor": {
        "leather_helmet": {
            "name": "Leather Helmet",
            "price": 200,
            "description": "Basic protection",
            "rarity": "common"
        },
        "iron_helmet": {
            "name": "Iron Helmet",
            "price": 500,
            "description": "Good protection",
            "rarity": "common"
        },
        "diamond_helmet": {
            "name": "Diamond Helmet",
            "price": 2000,
            "description": "Excellent protection",
            "rarity": "rare"
        },
        "leather_chestplate": {
            "name": "Leather Chestplate",
            "price": 400,
            "description": "Basic chest protection",
            "rarity": "common"
        },
        "iron_chestplate": {
            "name": "Iron Chestplate",
            "price": 1000,
            "description": "Good chest protection",
            "rarity": "common"
        },
        "diamond_chestplate": {
            "name": "Diamond Chestplate",
            "price": 4000,
            "description": "Excellent chest protection",
            "rarity": "rare"
        }
    },
    
    # CONSUMABLES
    "consumables": {
        "bread": {
            "name": "Bread",
            "price": 50,
            "description": "Restores 2 health",
            "rarity": "common"
        },
        "golden_apple": {
            "name": "Golden Apple",
            "price": 500,
            "description": "Restores 5 health",
            "rarity": "rare"
        },
        "enchanted_golden_apple": {
            "name": "Enchanted Golden Apple",
            "price": 2000,
            "description": "Restores 10 health",
            "rarity": "epic"
        },
        "speed_potion": {
            "name": "Speed Potion",
            "price": 300,
            "description": "Increases movement speed",
            "rarity": "rare"
        },
        "strength_potion": {
            "name": "Strength Potion",
            "price": 400,
            "description": "Increases damage",
            "rarity": "rare"
        },
        "healing_potion": {
            "name": "Healing Potion",
            "price": 250,
            "description": "Instantly restores 8 health",
            "rarity": "rare"
        }
    },
    
    # BUILDING MATERIALS
    "blocks": {
        "stone_bricks": {
            "name": "Stone Bricks",
            "price": 10,
            "description": "Decorative building block",
            "rarity": "common"
        },
        "obsidian": {
            "name": "Obsidian",
            "price": 100,
            "description": "Unbreakable building block",
            "rarity": "rare"
        },
        "nether_brick": {
            "name": "Nether Brick",
            "price": 50,
            "description": "Dark building block",
            "rarity": "uncommon"
        },
        "end_stone": {
            "name": "End Stone",
            "price": 75,
            "description": "Mystical building block",
            "rarity": "rare"
        },
        "beacon": {
            "name": "Beacon",
            "price": 5000,
            "description": "Provides special effects",
            "rarity": "epic"
        },
        "chest": {
            "name": "Chest",
            "price": 200,
            "description": "Storage container",
            "rarity": "common"
        }
    }
}

# Village system removed - no more random NPCs

# World generation system
world_generation_progress = 0
world_generation_total = 0
world_generation_status = "Initializing..."
world_generation_start_time = 0

# Pickaxe animation system
pickaxe_animation_active = False
pickaxe_animation_timer = 0
pickaxe_animation_duration = 30  # frames for one up-down cycle
pickaxe_animation_offset = 0  # vertical offset for animation
pickaxe_animation_direction = 1  # 1 for up, -1 for down

# Shop system removed

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

def draw_fortress_discovery():
    """Draw fortress discovery UI with big animation for new discoveries"""
    global discovery_timer, current_fortress_discovery, fortress_discovery_animation_scale
    
    if current_fortress_discovery is None:
        return
    
    # Decrease timer
    discovery_timer -= 1
    if discovery_timer <= 0:
        current_fortress_discovery = None
        fortress_discovery_animation_scale = 1.0
        return
    
    # Get fortress info
    fortress_info = FORTRESS_TYPES.get(current_fortress_discovery, {})
    fortress_name = fortress_info.get("name", "Unknown Fortress")
    rarity = fortress_info.get("rarity", "common")
    
    # Choose colors based on rarity
    rarity_colors = {
        "common": (200, 200, 200),      # Gray
        "uncommon": (0, 255, 0),        # Green
        "rare": (0, 100, 255),          # Blue
        "epic": (150, 0, 255),          # Purple
        "legendary": (255, 215, 0)      # Gold
    }
    
    text_color = rarity_colors.get(rarity, (255, 255, 255))
    
    # BIG ANIMATION: Start big and fade/scale down
    # Animation lasts for first 180 frames (3 seconds), then disappears
    max_timer = 180
    
    if discovery_timer > max_timer - 60:  # First second: grow in
        # Scale from 0 to 2.5x (BIG!)
        progress = (max_timer - discovery_timer) / 60.0
        fortress_discovery_animation_scale = progress * 2.5
        alpha = int(progress * 255)
    elif discovery_timer > 60:  # Middle: stay big
        fortress_discovery_animation_scale = 2.5
        alpha = 255
    else:  # Last second: fade out
        progress = discovery_timer / 60.0
        fortress_discovery_animation_scale = 2.5 * progress
        alpha = int(progress * 255)
    
    # Create discovery text
    discovery_text = f"🏰 DISCOVERED: {fortress_name}"
    rarity_text = f"Rarity: {rarity.upper()}"
    
    # Use larger font scaled by animation
    base_large_size = int(48 * fortress_discovery_animation_scale)
    base_medium_size = int(32 * fortress_discovery_animation_scale)
    large_font = pygame.font.Font(None, max(20, min(200, base_large_size)))
    medium_font = pygame.font.Font(None, max(16, min(150, base_medium_size)))
    
    # Render text
    discovery_surface = large_font.render(discovery_text, True, text_color)
    rarity_surface = medium_font.render(rarity_text, True, text_color)
    
    # Apply alpha
    discovery_surface.set_alpha(alpha)
    rarity_surface.set_alpha(alpha)
    
    # Center the text on screen
    discovery_x = (SCREEN_WIDTH - discovery_surface.get_width()) // 2
    discovery_y = SCREEN_HEIGHT // 2 - 50
    rarity_x = (SCREEN_WIDTH - rarity_surface.get_width()) // 2
    rarity_y = discovery_y + discovery_surface.get_height() + 10
    
    # Draw background with scaled size
    bg_width = int((max(discovery_surface.get_width(), rarity_surface.get_width()) + 40))
    bg_height = int((discovery_surface.get_height() + rarity_surface.get_height() + 60))
    bg_x = (SCREEN_WIDTH - bg_width) // 2
    bg_y = discovery_y - 20
    
    bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
    bg_surface.fill((0, 0, 0, min(200, alpha)))
    screen.blit(bg_surface, (bg_x, bg_y))
    
    # Draw border with pulsing effect
    border_width = 3 + int(2 * abs(math.sin(discovery_timer * 0.1)))
    pygame.draw.rect(screen, text_color, (bg_x, bg_y, bg_width, bg_height), border_width)
    
    # Draw text
    screen.blit(discovery_surface, (discovery_x, discovery_y))
    screen.blit(rarity_surface, (rarity_x, rarity_y))

def draw_fortress_minimap():
    """Draw discovered fortresses on minimap in corner"""
    if not discovered_fortresses:
        return
    
    # Minimap settings
    minimap_size = 200
    minimap_x = SCREEN_WIDTH - minimap_size - 10
    minimap_y = 10
    
    # Draw minimap background
    minimap_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
    minimap_surface.fill((0, 0, 0, 100))
    screen.blit(minimap_surface, (minimap_x, minimap_y))
    
    # Draw border
    pygame.draw.rect(screen, (100, 100, 100), (minimap_x, minimap_y, minimap_size, minimap_size), 2)
    
    # Draw title
    title_text = font.render("Fortresses", True, (255, 255, 255))
    screen.blit(title_text, (minimap_x + 5, minimap_y + 5))
    
    # Draw fortress list
    y_offset = 30
    for fortress_type in discovered_fortresses:
        fortress_info = FORTRESS_TYPES.get(fortress_type, {})
        fortress_name = fortress_info.get("name", "Unknown")
        rarity = fortress_info.get("rarity", "common")
        
        # Choose colors based on rarity
        rarity_colors = {
            "common": (200, 200, 200),      # Gray
            "uncommon": (0, 255, 0),        # Green
            "rare": (0, 100, 255),          # Blue
            "epic": (150, 0, 255),          # Purple
            "legendary": (255, 215, 0)      # Gold
        }
        
        text_color = rarity_colors.get(rarity, (255, 255, 255))
        
        # Truncate long names
        display_name = fortress_name[:15] + "..." if len(fortress_name) > 15 else fortress_name
        
        fortress_text = font.render(f"🏰 {display_name}", True, text_color)
        screen.blit(fortress_text, (minimap_x + 5, minimap_y + y_offset))
        y_offset += 20
        
        # Limit to 8 fortresses to fit in minimap
        if y_offset > minimap_size - 20:
            break

def draw_head_bump_effect(px, py):
    """Draw head bump effect when player hits ceiling"""
    global head_bump_timer, head_bump_effect
    
    if head_bump_timer <= 0 or not head_bump_effect:
        return
    
    # Decrease timer
    head_bump_timer -= 1
    if head_bump_timer <= 0:
        head_bump_effect = False
        return
    
    # Draw head bump effect - stars or sparks above player's head
    effect_y = py - 20  # Above player's head
    effect_x = px + 16  # Center above player
    
    # Draw multiple spark effects
    for i in range(3):
        spark_x = effect_x + (i - 1) * 8
        spark_y = effect_y + (head_bump_timer % 10) * 2
        
        # Draw spark as a small yellow circle
        pygame.draw.circle(screen, (255, 255, 0), (spark_x, spark_y), 2)
        pygame.draw.circle(screen, (255, 255, 255), (spark_x, spark_y), 1)
    
    # Draw "OUCH!" text
    ouch_text = font.render("OUCH!", True, (255, 0, 0))
    text_x = effect_x - ouch_text.get_width() // 2
    text_y = effect_y - 15
    screen.blit(ouch_text, (text_x, text_y))

def add_blood_particle(x, y):
    """Add a single blood particle at the specified location"""
    global blood_particles
    
    # Performance: Limit max particles
    if len(blood_particles) >= MAX_BLOOD_PARTICLES:
        return
    
    # Random direction and speed for the particle
    angle = random.uniform(0, 2 * math.pi)
    speed = random.uniform(2, 6)
    life = random.randint(20, 40)  # Frames to live
    
    particle = {
        'x': x,
        'y': y,
        'vel_x': math.cos(angle) * speed,
        'vel_y': math.sin(angle) * speed,
        'life': life,
        'max_life': life,
        'size': random.randint(2, 4)
    }
    blood_particles.append(particle)

def create_blood_particles(x, y, count=8):
    """Create blood particles at the specified location"""
    global blood_particles
    
    for _ in range(count):
        # Random direction and speed for each particle
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        life = random.randint(20, 40)  # Frames to live
        
        particle = {
            'x': x,
            'y': y,
            'vel_x': math.cos(angle) * speed,
            'vel_y': math.sin(angle) * speed,
            'life': life,
            'max_life': life,
            'size': random.randint(2, 4)
        }
        blood_particles.append(particle)

def create_monster_death_blood_spray(x, y):
    """Create dramatic blood squirting effect when monster dies"""
    global blood_particles
    
    # Create multiple bursts of blood over a few seconds
    for burst in range(3):  # 3 bursts of blood
        for _ in range(12):  # 12 particles per burst
            # Create spray pattern - more particles in random directions
            angle = random.uniform(0, 2 * math.pi)
            
            # Vary speed - some fast, some slow for realistic effect
            speed = random.uniform(3, 10)  # Faster than normal particles
            
            # Longer life for more dramatic effect
            life = random.randint(40, 80)  # Longer lasting
            
            # Slightly larger particles for visibility
            size = random.randint(3, 6)
            
            particle = {
                'x': x + random.uniform(-5, 5),  # Slight spread in starting position
                'y': y + random.uniform(-5, 5),
                'vel_x': math.cos(angle) * speed,
                'vel_y': math.sin(angle) * speed - random.uniform(0, 3),  # Slight upward bias
                'life': life,
                'max_life': life,
                'size': size
            }
            blood_particles.append(particle)
        
        # Small delay between bursts (simulated by varying particle life)
        # The delay is handled by the update timing

def update_blood_particles():
    """Update all blood particles"""
    global blood_particles
    
    # Update each particle
    for particle in blood_particles[:]:  # Use slice to avoid modification during iteration
        # Update position
        particle['x'] += particle['vel_x']
        particle['y'] += particle['vel_y']
        
        # Apply gravity
        particle['vel_y'] += 0.3
        
        # Reduce life
        particle['life'] -= 1
        
        # Remove dead particles
        if particle['life'] <= 0:
            blood_particles.remove(particle)

def draw_blood_particles():
    """Draw all blood particles with enhanced visibility - optimized"""
    for particle in blood_particles:
        # Calculate alpha based on remaining life
        alpha = int(255 * (particle['life'] / particle['max_life']))
        
        # Use cached surface or create once
        if 'surface' not in particle:
            particle['surface'] = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
        particle_surface = particle['surface']
        particle_surface.fill((0, 0, 0, 0))  # Clear previous frame
        
        # Enhanced blood colors - more vibrant red with slight variation
        base_red = 255
        green = random.randint(0, 30)  # Slight green variation for more realistic blood
        blue = random.randint(0, 20)   # Slight blue variation
        
        # Draw blood particle as red circle with slight color variation
        color = (base_red, green, blue, alpha)
        pygame.draw.circle(particle_surface, color, (particle['size'], particle['size']), particle['size'])
        
        # Add a slight highlight for more dramatic effect
        if alpha > 128:  # Only add highlight when particle is bright enough
            highlight_color = (255, min(255, green + 50), min(255, blue + 30), alpha // 2)
            pygame.draw.circle(particle_surface, highlight_color, (particle['size'], particle['size']), particle['size'] // 2)
        
        # Blit to screen
        screen.blit(particle_surface, (particle['x'] - particle['size'], particle['y'] - particle['size']))

def create_block_particles(x, y, block_type, count=12):
    """Create block breaking particles at the specified location"""
    global block_particles
    
    # Performance: Limit max particles
    if len(block_particles) >= MAX_BLOCK_PARTICLES:
        return
    
    # Reduce count if we're near the limit
    if len(block_particles) + count > MAX_BLOCK_PARTICLES:
        count = MAX_BLOCK_PARTICLES - len(block_particles)
    
    # Define particle colors for different block types
    particle_colors = {
        "leaves": [(34, 139, 34), (0, 100, 0), (50, 205, 50)],  # Green variations
        "grass": [(34, 139, 34), (0, 100, 0), (139, 69, 19), (160, 82, 45)],  # Green and brown
        "dirt": [(139, 69, 19), (160, 82, 45), (101, 67, 33), (85, 85, 85)],  # Brown variations
        "stone": [(128, 128, 128), (105, 105, 105), (169, 169, 169), (64, 64, 64)],  # Grey variations
        "coal": [(64, 64, 64), (32, 32, 32), (96, 96, 96)],  # Dark grey
        "iron": [(192, 192, 192), (169, 169, 169), (128, 128, 128)],  # Silver/grey
        "gold": [(255, 215, 0), (218, 165, 32), (184, 134, 11)],  # Gold variations
        "diamond": [(0, 191, 255), (30, 144, 255), (0, 100, 200)],  # Blue variations
        "log": [(139, 69, 19), (160, 82, 45), (101, 67, 33)],  # Brown wood
        "oak_planks": [(222, 184, 135), (205, 133, 63), (160, 82, 45)],  # Light brown
        "sand": [(238, 203, 173), (210, 180, 140), (188, 143, 143)],  # Sand colors
        "bedrock": [(64, 64, 64), (32, 32, 32), (96, 96, 96)]  # Dark grey
    }
    
    # Get colors for this block type, default to grey if not found
    colors = particle_colors.get(block_type, [(128, 128, 128), (105, 105, 105)])
    
    for _ in range(count):
        # Random direction and speed for each particle
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        life = random.randint(30, 60)  # Frames to live
        
        # Choose random color from the block's color palette
        color = random.choice(colors)
        
        particle = {
            'x': x + random.uniform(-10, 10),  # Slight random offset
            'y': y + random.uniform(-10, 10),
            'vel_x': math.cos(angle) * speed,
            'vel_y': math.sin(angle) * speed,
            'life': life,
            'max_life': life,
            'size': random.randint(2, 5),
            'color': color
        }
        block_particles.append(particle)

def update_block_particles():
    """Update all block particles"""
    global block_particles
    
    # Update each particle
    for particle in block_particles[:]:  # Use slice to avoid modification during iteration
        # Update position
        particle['x'] += particle['vel_x']
        particle['y'] += particle['vel_y']
        
        # Apply gravity
        particle['vel_y'] += 0.2
        
        # Apply air resistance
        particle['vel_x'] *= 0.98
        particle['vel_y'] *= 0.98
        
        # Reduce life
        particle['life'] -= 1
        
        # Remove dead particles
        if particle['life'] <= 0:
            block_particles.remove(particle)

def draw_block_particles():
    """Draw all block particles - optimized"""
    for particle in block_particles:
        # Calculate alpha based on remaining life
        alpha = int(255 * (particle['life'] / particle['max_life']))
        
        # Use cached surface or create once
        if 'surface' not in particle:
            particle['surface'] = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
        particle_surface = particle['surface']
        particle_surface.fill((0, 0, 0, 0))  # Clear previous frame
        
        # Use the particle's color with alpha
        color = particle['color']
        alpha_color = (*color, alpha)
        
        # Draw the particle
        pygame.draw.circle(particle_surface, alpha_color, (particle['size'], particle['size']), particle['size'])
        
        # Blit to screen
        screen.blit(particle_surface, (particle['x'] - particle['size'], particle['y'] - particle['size']))

def init_map_surface():
    """Initialize the map surface"""
    global map_surface
    map_surface = pygame.Surface((map_width, map_height))
    map_surface.fill((50, 50, 100))  # Dark blue background

def get_block_color(block_type):
    """Get the color for a block type on the map"""
    color_map = {
        "grass": (34, 139, 34),      # Forest green
        "dirt": (139, 69, 19),       # Saddle brown
        "stone": (105, 105, 105),    # Dim gray
        "bedrock": (25, 25, 25),     # Very dark gray
        "coal": (47, 79, 79),        # Dark slate gray
        "iron": (169, 169, 169),     # Dark gray
        "gold": (255, 215, 0),       # Gold
        "diamond": (0, 191, 255),    # Deep sky blue
        "water": (0, 100, 200),      # Blue
        "lava": (255, 100, 0),       # Red-orange
        "leaves": (0, 100, 0),       # Dark green
        "log": (101, 67, 33),        # Brown
        "carrot": (255, 165, 0),     # Orange
        "chest": (139, 69, 19),      # Saddle brown
        "air": (0, 0, 0, 0),         # Transparent
        None: (0, 0, 0, 0)           # Transparent for empty blocks
    }
    return color_map.get(block_type, (100, 100, 100))  # Default gray

def update_map():
    """Update the map surface with current world data around the player"""
    global map_surface
    
    if map_surface is None:
        init_map_surface()
    
    # Clear the map
    map_surface.fill((50, 50, 100))
    
    # Get player position in block coordinates
    player_x = int(player["x"])
    player_y = int(player["y"])
    
    # Ensure map_view_radius is at least 1 to avoid division by zero
    radius = max(1, map_view_radius)
    
    # Calculate the area to draw around the player
    start_x = player_x - radius
    end_x = player_x + radius
    start_y = player_y - radius
    end_y = player_y + radius
    
    # Calculate scaling factors safely
    total_width = radius * 2
    total_height = radius * 2
    
    if total_width <= 0 or total_height <= 0:
        return  # Avoid division by zero
    
    scale_x = map_width / total_width
    scale_y = map_height / total_height
    
    # Draw blocks around the player
    for x in range(start_x, end_x):
        for y in range(start_y, end_y):
            try:
                block_type = get_block(x, y)
                if block_type and block_type != "air":
                    # Calculate position on map surface
                    map_x = int((x - start_x) * scale_x)
                    map_y = int((y - start_y) * scale_y)
                    
                    # Ensure we're within map bounds
                    if 0 <= map_x < map_width and 0 <= map_y < map_height:
                        color = get_block_color(block_type)
                        if len(color) == 4:  # Has alpha channel
                            # Create a surface with alpha for transparency
                            pixel_surface = pygame.Surface((1, 1), pygame.SRCALPHA)
                            pixel_surface.fill(color)
                            map_surface.blit(pixel_surface, (map_x, map_y))
                        else:
                            map_surface.set_at((map_x, map_y), color)
            except Exception as e:
                # Skip problematic blocks to prevent crashes
                continue
    
    # Draw player position (center of map)
    player_map_x = map_width // 2
    player_map_y = map_height // 2
    
    # Draw player as a red dot
    pygame.draw.circle(map_surface, (255, 0, 0), (player_map_x, player_map_y), 2)
    # Draw a white outline around the player
    pygame.draw.circle(map_surface, (255, 255, 255), (player_map_x, player_map_y), 3, 1)

def draw_map():
    """Draw the map overlay on the screen"""
    global map_open
    try:
        if not map_open or map_surface is None:
            return
        
        # Update the map with current world data
        update_map()
        
        # Create a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Calculate map position (centered on screen)
        map_display_width = map_width * 2  # Scale up for better visibility
        map_display_height = map_height * 2
        map_x = (SCREEN_WIDTH - map_display_width) // 2
        map_y = (SCREEN_HEIGHT - map_display_height) // 2
        
        # Draw map background
        map_bg = pygame.Surface((map_display_width + 20, map_display_height + 20))
        map_bg.fill((20, 20, 40))
        screen.blit(map_bg, (map_x - 10, map_y - 10))
        
        # Draw map border
        pygame.draw.rect(screen, (255, 255, 255), (map_x - 10, map_y - 10, map_display_width + 20, map_display_height + 20), 2)
        
        # Scale and draw the map
        scaled_map = pygame.transform.scale(map_surface, (map_display_width, map_display_height))
        screen.blit(scaled_map, (map_x, map_y))
        
        # Draw map title
        title_text = BIG_FONT.render("MAP", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, map_y - 30))
        screen.blit(title_text, title_rect)
        
        # Draw instructions
        instructions = [
            "Press M or ESC to close map",
            f"Player Position: ({int(player['x'])}, {int(player['y'])})",
            f"View Radius: {map_view_radius} blocks"
        ]
        
        for i, instruction in enumerate(instructions):
            instruction_text = small_font.render(instruction, True, (200, 200, 200))
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, map_y + map_display_height + 20 + i * 20))
            screen.blit(instruction_text, instruction_rect)
    
    except Exception as e:
        print(f"⚠️ Map drawing error: {e}")
        # Close map on error to prevent further crashes
        map_open = False


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
        if multiplayer_server.start_server("My Server", world_name, 5555):
            is_hosting = True
            show_message(f"🌐 Server started! Others can join at {multiplayer_server.host}:{multiplayer_server.port}")
            print(f"🌐 Multiplayer server started: {multiplayer_server.server_name} hosting {world_name}")
            return True
        else:
            show_message("❌ Failed to start server")
            return False
    except Exception as e:
        show_message(f"❌ Server error: {e}")
        print(f"❌ Multiplayer server error: {e}")
        return False

def join_multiplayer_server(server_ip, server_port):
    """Join a multiplayer server"""
    global multiplayer_client, is_connected
    
    try:
        from network.multiplayer_server import MultiplayerClient
        multiplayer_client = MultiplayerClient()
        
        # Get username from saved data
        username = get_current_username()
        
        if multiplayer_client.connect_to_server(server_ip, server_port, username):
            is_connected = True
            show_message(f"🔗 Connected to {server_ip}:{server_port}")
            print(f"🔗 Connected to multiplayer server as {username}")
            return True
        else:
            show_message("❌ Failed to connect to server")
            return False
    except Exception as e:
        show_message(f"❌ Connection failed: {e}")
        print(f"❌ Multiplayer connection error: {e}")
        return False

def create_world_with_name(name_input):
    """Create a new world with the given name"""
    global game_state, world_name_input, world_name_cursor_pos
    
    # Determine world name
    if name_input and name_input.strip():
        # Use provided name
        world_name = name_input.strip()
        print(f"🌍 Creating world with custom name: {world_name}")
    else:
        # Use default name
        world_name = f"World {len(world_system.world_list) + 1}"
        print(f"🌍 Creating world with default name: {world_name}")
    
    # Create the world
    if world_system.create_world(world_name):
        print(f"✅ Created new world: {world_name}")
        # Refresh world selection state
        world_ui.refresh_world_selection()
        # Load the newly created world
        if world_system.load_world(world_name):
            print(f"✅ World system loaded: {world_name}")
            # Load the world data into the game
            if load_world_data():
                print(f"✅ World data loaded successfully")
                # Fix player spawn position to ensure surface spawning
                fix_player_spawn_position()
                # Start world generation instead of going directly to game
                start_world_generation()
                game_state = GameState.WORLD_GENERATION
                update_pause_state()  # Resume time when entering world generation
                print(f"🌍 Starting world generation for new world: {world_name}")
                print(f"🎮 Game state is now: {game_state}")
            else:
                print("❌ Failed to load world data into game - returning to world selection")
                game_state = GameState.WORLD_SELECTION
                update_pause_state()
        else:
            print("❌ Failed to load newly created world - returning to world selection")
            game_state = GameState.WORLD_SELECTION
            update_pause_state()
    else:
        print("❌ Failed to create new world - returning to world selection")
        game_state = GameState.WORLD_SELECTION
        update_pause_state()
    
    # Reset naming variables
    world_name_input = ""
    world_name_cursor_pos = 0

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

# --- Sword Throwing System ---
thrown_sword = None  # {'x': float, 'y': float, 'target_x': float, 'target_y': float, 'returning': bool, 'sword_type': str, 'original_slot': int}
sword_throw_speed = 0.3  # Speed of sword projectile
sword_return_speed = 0.2  # Speed of sword returning
sword_throw_range = 8  # Maximum throw range in tiles
sword_slash_range = 2  # Range for close combat slash

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
backpack_close_button = None
left_arrow_btn = None
right_arrow_btn = None
select_btn = None

# --- World Selection Button References ---
world_play_btn = None
world_delete_btn = None
world_create_btn = None
world_back_btn = None

# --- World Naming System ---
world_name_input = ""
world_name_cursor_pos = 0
world_name_cursor_blink = 0
world_name_onscreen_keyboard = True
world_name_buttons = {}
world_name_confirm_btn = None
world_name_cancel_btn = None
world_name_skip_btn = None

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
    "first_monster_kill": False,  # First monster defeated (25 coins)
    "first_carrot": False,   # First carrot eaten (10 coins)
    "first_sleep": False,    # First time sleeping in bed (20 coins)
    "ultimate_achievement": False  # Most special achievement (1,000,000 coins)
}

# --- Character selection system ---
# Character manager handles all character-related functionality
character_manager = None

def initialize_character_manager():
    """Load all character textures from the player folder"""
    global character_manager
    
    # Check if CharacterManager is available
    if CharacterManager is None:
        print("⚠️ CharacterManager not available, using fallback")
        character_manager = None
        return
    
    try:
        character_manager = CharacterManager(PLAYER_DIR, TILE_SIZE)
        print("🎭 Character manager initialized")
        
        # Debug: Show what textures were loaded
        if character_manager:
            print(f"🎭 Available characters: {[char['name'] for char in character_manager.available_characters]}")
            print(f"🎭 Current selected character: {character_manager.get_current_character_name()}")
    except Exception as e:
        print(f"⚠️ Failed to initialize character manager: {e}")
        character_manager = None

def initialize_chat_system():
    """Initialize the chat system"""
    global chat_system
    
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
        try:
            chat_system.set_fonts(font, font)  # Use the same font for now
            print("💬 Chat system initialized")
        except Exception as e:
            print(f"❌ Chat system initialization failed: {e}")
            chat_system = None

def initialize_coins_manager():
    """Initialize the coins manager"""
    global coins_manager
    
    try:
        from managers.coins_manager import CoinsManager
    except ImportError:
        print("⚠️ Warning: Coins manager not available")
        CoinsManager = None
    if CoinsManager:
        coins_manager = CoinsManager("coins.json")
    else:
        coins_manager = None
    if coins_manager:
        try:
            current_username = get_current_username()
            coins_manager.set_username(current_username)
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
    passable_blocks = {None, "air", "carrot", "ladder", "water", "chest", "door"}
    return block in passable_blocks

def is_solid_block(block_type):
    """Check if a block type is solid (cannot be walked through)"""
    if block_type is None:
        return False
    return not is_non_solid_block(block_type)

def check_collision_at_position(x, y, width=1.0, height=1.0):
    """Check for collision at a specific position with given dimensions"""
    # Check multiple points around the player's hitbox
    left = int(x)
    right = int(x + width - 0.1)  # Slightly inside the right edge
    top = int(y)
    bottom = int(y + height - 0.1)  # Slightly inside the bottom edge
    
    # Check all four corners and center points
    collision_points = [
        (left, top),      # Top-left
        (right, top),     # Top-right
        (left, bottom),   # Bottom-left
        (right, bottom),  # Bottom-right
        (int(x + width/2), int(y + height/2))  # Center
    ]
    
    for px, py in collision_points:
        block = get_block(px, py)
        if is_solid_block(block):
            return True, block, (px, py)
    
    return False, None, None

def trigger_head_bump():
    """Trigger head bump effect when player hits ceiling"""
    global head_bump_timer, head_bump_effect
    if head_bump_timer <= 0:  # Only trigger if not already active
        head_bump_timer = 30  # 0.5 seconds at 60 FPS
        head_bump_effect = True
        print("💥 Head bump! Can't jump higher!")

def is_door_open(x, y):
    """Check if a door at position (x, y) is open"""
    return door_states.get((x, y), False)

def can_pass_through_block(block_type, x, y):
    """Check if player can pass through a block, considering door states"""
    if block_type == "door":
        return is_door_open(x, y)
    return is_non_solid_block(block_type)

# Terrain helper: which blocks count as real ground for column generation
TERRAIN_BLOCKS = {"grass","dirt","stone","bedrock","coal","iron","gold","diamond","sand","water"}

# Falling blocks system
falling_blocks = []  # List of blocks that need to fall

# Water flow system
water_flow_timer = 0
water_flow_cooldown = 30  # Frames between water flow updates

def add_falling_block(x, y, block_type):
    """Add a block to the falling blocks list"""
    global falling_blocks
    falling_blocks.append({"x": x, "y": y, "type": block_type, "vel_y": 0.0})

def update_falling_blocks():
    """Update all falling blocks (sand physics)"""
    global falling_blocks, world_data
    
    if not falling_blocks:
        return  # No blocks to update
    
    blocks_to_remove = []
    blocks_to_add = []
    
    for i, block in enumerate(falling_blocks):
        x, y = block["x"], block["y"]
        block_type = block["type"]
        vel_y = block["vel_y"]
        
        # Check if block still exists at this position
        if get_block(x, y) != block_type:
            blocks_to_remove.append(i)
            continue
        
        # Apply gravity
        vel_y += 0.5  # Gravity acceleration
        new_y = y + vel_y
        
        # Check collision with blocks below
        target_y = int(new_y)
        if target_y != y:
            # Check if we can fall to the new position
            block_below = get_block(x, target_y)
            if block_below is None or block_below in ["air", "water"]:
                # Can fall - move the block
                print(f"🏖️ Sand falling from ({x}, {y}) to ({x}, {target_y})")
                # Remove from old position
                if f"{x},{y}" in world_data:
                    del world_data[f"{x},{y}"]
                
                # Add to new position
                set_block(x, target_y, block_type)
                
                # Update falling block data
                block["y"] = target_y
                block["vel_y"] = vel_y
            else:
                # Hit something - stop falling
                print(f"🏖️ Sand stopped falling at ({x}, {y}) - hit {block_below}")
                blocks_to_remove.append(i)
        else:
            # Update velocity
            block["vel_y"] = vel_y
    
    # Remove stopped blocks
    for i in reversed(blocks_to_remove):
        falling_blocks.pop(i)

def check_sand_falling(x, y):
    """Check if any sand blocks above the broken block need to fall"""
    # Check blocks above the broken position
    for check_y in range(y - 1, y - 10, -1):  # Check up to 10 blocks above
        block_above = get_block(x, check_y)
        if block_above == "sand":
            # Check if there's support below this sand block
            block_below = get_block(x, check_y + 1)
            if block_below is None or block_below in ["air", "water"]:
                # Sand has no support - make it fall
                add_falling_block(x, check_y, "sand")
                print(f"🏖️ Sand at ({x}, {check_y}) will fall!")
        elif block_above is not None and block_above != "air":
            # Hit a solid block - stop checking
            break

def update_water_flow():
    """Update water flow - make water flow to empty spaces"""
    global water_flow_timer, world_data
    
    water_flow_timer += 1
    if water_flow_timer < water_flow_cooldown:
        return
    
    water_flow_timer = 0
    
    # Find all water blocks that need to flow
    water_blocks_to_update = []
    
    for pos_key, block_type in list(world_data.items()):
        if block_type == "water":
            x, y = map(int, pos_key.split(","))
            water_blocks_to_update.append((x, y))
    
    if water_blocks_to_update:
        print(f"🌊 Updating {len(water_blocks_to_update)} water blocks")
    
    # Update water flow
    for x, y in water_blocks_to_update:
        # Check if water can flow down
        block_below = get_block(x, y + 1)
        if block_below is None or block_below == "air":
            # Water can flow down - move it
            print(f"🌊 Water flowing down from ({x}, {y}) to ({x}, {y + 1})")
            if f"{x},{y}" in world_data:
                del world_data[f"{x},{y}"]
            set_block(x, y + 1, "water")
            continue
        
        # Check if water can flow horizontally
        for dx in [-1, 1]:  # Check left and right
            block_side = get_block(x + dx, y)
            if block_side is None or block_side == "air":
                # Check if there's support below the side position
                block_side_below = get_block(x + dx, y + 1)
                if block_side_below is not None and block_side_below != "air":
                    # Water can flow horizontally - move it
                    print(f"🌊 Water flowing horizontally from ({x}, {y}) to ({x + dx}, {y})")
                    if f"{x},{y}" in world_data:
                        del world_data[f"{x},{y}"]
                    set_block(x + dx, y, "water")
                    break


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

# Villager dialogue system removed



# Village and house building functions removed


# All NPC spawning functions removed - no more random NPCs

def start_world_generation():
    """Start the world generation process"""
    global world_generation_progress, world_generation_total, world_generation_status, world_generation_start_time
    
    world_generation_progress = 0
    world_generation_total = 200  # Generate 200x200 area (40,000 chunks)
    world_generation_status = "Generating terrain..."
    world_generation_start_time = time.time()
    
    # Shop removed - now available in title screen
    
    print("🌍 Starting world generation...")

def update_world_generation():
    """Update world generation progress"""
    global world_generation_progress, world_generation_status, game_state
    
    if world_generation_progress >= world_generation_total:
        # World generation complete
        world_generation_status = "World generation complete!"
        print("🌍 World generation complete!")
        
        # Switch to game state
        game_state = GameState.GAME
        return
    
    # Generate a few chunks per frame to avoid freezing
    chunks_per_frame = 5
    
    for _ in range(chunks_per_frame):
        if world_generation_progress >= world_generation_total:
            break
            
        # Calculate position to generate
        center_x = 0  # Generate around spawn
        center_y = 0
        
        # Generate in a spiral pattern
        radius = world_generation_progress // 20  # 20 chunks per radius
        angle = (world_generation_progress % 20) * (2 * math.pi / 20)
        
        x = center_x + int(radius * math.cos(angle))
        y = center_y + int(radius * math.sin(angle))
        
        # Generate terrain for this position
        generate_terrain_column(x)
        # Replace dirt/stone blocks adjacent to water with sand for natural beaches
        
        world_generation_progress += 1
        
        # Update status
        if world_generation_progress % 100 == 0:
            elapsed = time.time() - world_generation_start_time
            world_generation_status = f"Generating terrain... {world_generation_progress}/{world_generation_total} ({world_generation_progress/world_generation_total*100:.1f}%)"
            print(f"🌍 World generation: {world_generation_progress}/{world_generation_total} ({world_generation_progress/world_generation_total*100:.1f}%) - {elapsed:.1f}s")

def start_pickaxe_animation():
    """Start the pickaxe animation"""
    global pickaxe_animation_active, pickaxe_animation_timer, pickaxe_animation_offset, pickaxe_animation_direction
    
    pickaxe_animation_active = True
    pickaxe_animation_timer = 0
    pickaxe_animation_offset = 0
    pickaxe_animation_direction = 1  # Start moving up
    print("⛏️ Pickaxe animation started!")

def update_pickaxe_animation():
    """Update the pickaxe animation"""
    global pickaxe_animation_active, pickaxe_animation_timer, pickaxe_animation_offset, pickaxe_animation_direction
    
    if not pickaxe_animation_active:
        return
    
    # Update animation timer
    pickaxe_animation_timer += 1
    
    # Calculate animation progress (0 to 1)
    progress = (pickaxe_animation_timer % pickaxe_animation_duration) / pickaxe_animation_duration
    
    # Create smooth up-down motion using sine wave
    # This creates a smooth oscillation between -8 and +8 pixels
    pickaxe_animation_offset = int(8 * math.sin(progress * 2 * math.pi))
    
    # Check if animation should continue
    # Animation continues for 2 cycles (60 frames) then stops
    if pickaxe_animation_timer >= pickaxe_animation_duration * 2:
        pickaxe_animation_active = False
        pickaxe_animation_offset = 0
        print("⛏️ Pickaxe animation completed!")

# Shop functions removed

def draw_world_generation_screen():
    """Draw the world generation loading screen"""
    global world_generation_progress, world_generation_total, world_generation_status
    
    # Clear screen
    screen.fill((20, 20, 40))  # Dark blue background
    
    # Draw title
    title_text = title_font.render("Generating World...", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
    screen.blit(title_text, title_rect)
    
    # Draw progress bar background
    bar_width = 400
    bar_height = 30
    bar_x = (SCREEN_WIDTH - bar_width) // 2
    bar_y = SCREEN_HEIGHT // 2 - 20
    
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
    
    # Draw progress bar fill
    if world_generation_total > 0:
        progress_width = int((world_generation_progress / world_generation_total) * bar_width)
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, progress_width, bar_height))
    
    # Draw progress text
    progress_text = f"{world_generation_progress}/{world_generation_total} ({world_generation_progress/world_generation_total*100:.1f}%)"
    progress_surface = font.render(progress_text, True, (255, 255, 255))
    progress_rect = progress_surface.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height + 20))
    screen.blit(progress_surface, progress_rect)
    
    # Draw status text
    status_surface = font.render(world_generation_status, True, (200, 200, 200))
    status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height + 50))
    screen.blit(status_surface, status_rect)
    
    # Draw loading animation
    loading_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    loading_char = loading_chars[(pygame.time.get_ticks() // 100) % len(loading_chars)]
    loading_surface = font.render(loading_char, True, (255, 255, 255))
    loading_rect = loading_surface.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height + 80))
    screen.blit(loading_surface, loading_rect)
    
    # Draw instruction text
    instruction_text = "Please wait while the world generates..."
    instruction_surface = font.render(instruction_text, True, (150, 150, 150))
    instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
    screen.blit(instruction_surface, instruction_rect)

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

def check_player_armor():
    """Check if player has armor equipped"""
    # Check for any armor in inventory
    armor_types = ["helmet", "chestplate", "leggings", "boots", "armor"]
    for item in player["inventory"]:
        if item and any(armor_type in item.get("type", "").lower() for armor_type in armor_types):
            return True
    return False

def show_boss_room_dialog():
    """Show boss room entry dialog with armor recommendation"""
    global game_state, dialog_active, dialog_text, dialog_options, dialog_callback
    
    # Check if player has armor
    has_armor = check_player_armor()
    
    if has_armor:
        dialog_text = [
            "🐉 BOSS ROOM ENTRY",
            "",
            "You approach the legendary boss chamber...",
            "",
            "⚔️ You have armor equipped!",
            "You are well prepared for this battle!",
            "",
            "Do you want to enter the boss room?"
        ]
    else:
        dialog_text = [
            "🐉 BOSS ROOM ENTRY",
            "",
            "You approach the legendary boss chamber...",
            "",
            "⚠️ WARNING: You don't have any armor equipped!",
            "The boss is extremely powerful and you might die!",
            "",
            "I recommend you get armor first, but you can still enter.",
            "",
            "Do you want to enter the boss room anyway?"
        ]
    
    dialog_options = ["Yes, enter!", "No, I'll get armor first"]
    dialog_callback = handle_boss_room_choice
    dialog_active = True
    game_state = GameState.DIALOG

def handle_boss_room_choice(choice):
    """Handle the player's choice for boss room entry"""
    global dialog_active, game_state
    
    dialog_active = False
    game_state = GameState.GAME
    
    if choice == 0:  # Yes, enter
        if check_player_armor():
            show_message("🛡️ Great! You're well prepared. Entering boss room...", 2000)
        else:
            show_message("⚠️ You're entering without armor! Good luck...", 2000)
        
        # Start the boss fight
        start_boss_fight()
    else:  # No, get armor first
        show_message("💡 Good idea! Find some armor before challenging the boss.", 3000)
        print("💡 Player chose to get armor before boss fight")

def start_boss_fight():
    """EXTREME ENGINEERING: Start the legendary boss battle"""
    global boss_fight_active, boss_health, boss_max_health, boss_phase
    
    if boss_fight_active:
        return
    
    # Check if player has a weapon
    if not check_weapon_requirement():
        show_message("⚔️ You need a weapon to fight the boss!", 3000)
        print("❌ Player attempted to fight boss without weapon")
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

def get_weapon_damage():
    """Get damage amount based on equipped weapon"""
    if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]:
        weapon_type = player["inventory"][player["selected"]]["type"]
        weapon_damage = {
            "sword": 30,           # Basic sword
            "stone_sword": 50,     # Stone sword (original)
            "diamond_sword": 80,   # Diamond sword
            "gold_sword": 60,      # Gold sword
            "enchanted_sword": 120 # Enchanted sword (best)
        }
        return weapon_damage.get(weapon_type, 0)
    return 0

def check_weapon_requirement():
    """Check if player has any weapon equipped"""
    if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]:
        weapon_type = player["inventory"][player["selected"]]["type"]
        return weapon_type in ["sword", "stone_sword", "diamond_sword", "gold_sword", "enchanted_sword"]
    return False

def damage_boss(damage_amount=None):
    """Damage the boss - any weapon can damage the boss with different damage amounts"""
    global boss_health
    
    if not boss_fight_active:
        return False
    
    # Check if player has a weapon
    if not check_weapon_requirement():
        show_message("⚔️ You need a weapon to damage the boss!", 2000)
        print("❌ Player attempted to damage boss without weapon")
        return False
    
    # Get damage amount from weapon if not specified
    if damage_amount is None:
        damage_amount = get_weapon_damage()
    
    # Apply damage
    boss_health = max(0, boss_health - damage_amount)
    weapon_name = player["inventory"][player["selected"]]["type"].replace("_", " ").title()
    print(f"⚔️ Boss took {damage_amount} damage from {weapon_name}! HP: {boss_health}/{boss_max_health}")
    
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
# POGO JUMP PORTAL SYSTEM FUNCTIONS
# =============================================================================

# =============================================================================
# ABILITY SYSTEM FUNCTIONS
# =============================================================================

def track_monster_kill():
    """Track when a monster is killed and check for ability unlocks"""
    global monsters_killed, total_monsters_killed
    
    monsters_killed += 1
    total_monsters_killed += 1
    
    print(f"👹 Monster killed! Total: {total_monsters_killed}")
    
    # Ability system removed

# Wall jump system removed - no more abilities

# Dash movement function removed - no more dash ability

# =============================================================================
# MERCHANT SYSTEM FUNCTIONS
# =============================================================================

def open_merchant_shop(merchant_pos):
    """Open the merchant shop interface"""
    global merchant_shop_open, merchant_block_pos, merchant_selected_category, merchant_page
    
    merchant_shop_open = True
    merchant_block_pos = merchant_pos
    merchant_selected_category = "tools"
    merchant_page = 0
    print("🏪 Merchant shop opened!")

def close_merchant_shop():
    """Close the merchant shop interface"""
    global merchant_shop_open, merchant_block_pos
    
    merchant_shop_open = False
    merchant_block_pos = None
    print("🏪 Merchant shop closed!")

def get_player_coins():
    """Get player's current coin count"""
    try:
        with open("coins.json", "r") as f:
            coins_data = json.load(f)
            return coins_data.get("coins", 0)
    except:
        return 0

def spend_coins(amount):
    """Spend coins from player's account"""
    try:
        with open("coins.json", "r") as f:
            coins_data = json.load(f)
        
        current_coins = coins_data.get("coins", 0)
        if current_coins >= amount:
            coins_data["coins"] = current_coins - amount
            with open("coins.json", "w") as f:
                json.dump(coins_data, f, indent=2)
            return True
        return False
    except:
        return False

def buy_merchant_item(category, item_id):
    """Buy an item from the merchant shop"""
    if category not in MERCHANT_ITEMS or item_id not in MERCHANT_ITEMS[category]:
        return False
    
    item = MERCHANT_ITEMS[category][item_id]
    price = item["price"]
    
    # Check if player has enough coins
    if not spend_coins(price):
        show_message(f"💰 Not enough coins! Need {price} coins.", 3000)
        return False
    
    # Add item to player inventory
    add_item_to_inventory(item_id, 1)
    
    show_message(f"✅ Bought {item['name']} for {price} coins!", 3000)
    print(f"🏪 Player bought {item['name']} for {price} coins")
    return True

def add_item_to_inventory(item_id, count):
    """Add an item to player inventory"""
    # Find empty slot
    for i, slot in enumerate(player["inventory"]):
        if slot is None:
            player["inventory"][i] = {
                "type": item_id,
                "count": count
            }
            return True
    
    # If no empty slot, try backpack
    for i, slot in enumerate(player["backpack"]):
        if slot is None:
            player["backpack"][i] = {
                "type": item_id,
                "count": count
            }
            return True
    
    # If no space, drop on ground
    drop_item_near_player(item_id, count)

def drop_item_near_player(item_id, count):
    """Drop an item near the player"""
    entities.append({
        "type": "item_drop",
        "x": player["x"] + random.uniform(-2, 2),
        "y": player["y"] + random.uniform(-2, 2),
        "item_type": item_id,
        "count": count,
        "pickup_timer": 0
    })

def draw_merchant_shop_ui():
    """Draw the merchant shop interface"""
    if not merchant_shop_open:
        return
    
    # Draw semi-transparent background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    # Draw merchant shop window
    shop_width = 900
    shop_height = 700
    shop_x = (SCREEN_WIDTH - shop_width) // 2
    shop_y = (SCREEN_HEIGHT - shop_height) // 2
    
    # Shop background with gradient effect
    pygame.draw.rect(screen, (30, 30, 50), (shop_x, shop_y, shop_width, shop_height))
    pygame.draw.rect(screen, (60, 60, 80), (shop_x, shop_y, shop_width, shop_height), 4)
    
    # Shop title with fancy styling
    title_text = title_font.render("🏪 MERCHANT'S MARKETPLACE", True, (255, 215, 0))
    title_rect = title_text.get_rect(center=(shop_x + shop_width // 2, shop_y + 40))
    screen.blit(title_text, title_rect)
    
    # Player coins display
    coins = get_player_coins()
    coins_text = font.render(f"💰 Your Coins: {coins:,}", True, (255, 215, 0))
    screen.blit(coins_text, (shop_x + 30, shop_y + 80))
    
    # Close button
    close_text = font.render("❌ Close (ESC)", True, (255, 100, 100))
    screen.blit(close_text, (shop_x + shop_width - 150, shop_y + 80))
    
    # Category buttons
    categories = ["tools", "armor", "consumables", "blocks"]
    category_names = ["🛠️ Tools", "🛡️ Armor", "🍎 Food", "🧱 Blocks"]
    
    cat_x = shop_x + 30
    cat_y = shop_y + 120
    cat_width = 180
    cat_height = 40
    
    for i, (cat, name) in enumerate(zip(categories, category_names)):
        cat_rect = pygame.Rect(cat_x + i * (cat_width + 10), cat_y, cat_width, cat_height)
        
        # Highlight selected category
        if cat == merchant_selected_category:
            pygame.draw.rect(screen, (100, 150, 255), cat_rect)
        else:
            pygame.draw.rect(screen, (60, 60, 80), cat_rect)
        
        pygame.draw.rect(screen, (150, 150, 150), cat_rect, 2)
        
        # Category text
        cat_text = font.render(name, True, (255, 255, 255))
        text_rect = cat_text.get_rect(center=cat_rect.center)
        screen.blit(cat_text, text_rect)
    
    # Draw items in selected category
    if merchant_selected_category in MERCHANT_ITEMS:
        items = list(MERCHANT_ITEMS[merchant_selected_category].items())
        items_per_page = 6
        start_idx = merchant_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        
        item_y = shop_y + 180
        items_per_row = 3
        item_width = 250
        item_height = 140
        
        for i, (item_id, item_data) in enumerate(items[start_idx:end_idx]):
            row = i // items_per_row
            col = i % items_per_row
            
            item_x = shop_x + 30 + col * (item_width + 20)
            item_y_pos = item_y + row * (item_height + 20)
            
            # Item background with rarity colors
            rarity_colors = {
                "common": (120, 120, 120),
                "uncommon": (0, 200, 0),
                "rare": (0, 100, 255),
                "epic": (150, 0, 255),
                "legendary": (255, 215, 0)
            }
            
            color = rarity_colors.get(item_data["rarity"], (120, 120, 120))
            pygame.draw.rect(screen, color, (item_x, item_y_pos, item_width, item_height))
            pygame.draw.rect(screen, (200, 200, 200), (item_x, item_y_pos, item_width, item_height), 3)
            
            # Item name
            name_text = font.render(item_data["name"], True, (255, 255, 255))
            screen.blit(name_text, (item_x + 15, item_y_pos + 15))
            
            # Item price
            price_text = font.render(f"💰 {item_data['price']:,} coins", True, (255, 215, 0))
            screen.blit(price_text, (item_x + 15, item_y_pos + 40))
            
            # Item description
            desc_text = font.render(item_data["description"], True, (200, 200, 200))
            screen.blit(desc_text, (item_x + 15, item_y_pos + 65))
            
            # Buy button
            buy_rect = pygame.Rect(item_x + 15, item_y_pos + 95, 100, 30)
            pygame.draw.rect(screen, (0, 150, 0), buy_rect)
            pygame.draw.rect(screen, (0, 200, 0), buy_rect, 2)
            buy_text = font.render("BUY", True, (255, 255, 255))
            screen.blit(buy_text, (buy_rect.x + 30, buy_rect.y + 8))
            
            # Check if mouse is over buy button
            mouse_pos = pygame.mouse.get_pos()
            if buy_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (0, 200, 0), buy_rect)
        
        # Page navigation
        if len(items) > items_per_page:
            page_text = font.render(f"Page {merchant_page + 1} of {(len(items) + items_per_page - 1) // items_per_page}", True, (200, 200, 200))
            screen.blit(page_text, (shop_x + 30, shop_y + shop_height - 60))
    
    # Instructions
    instruction_text = font.render("🖱️ Click category buttons to browse • Click BUY to purchase", True, (200, 200, 200))
    screen.blit(instruction_text, (shop_x + 30, shop_y + shop_height - 30))

def handle_merchant_shop_click(mx, my):
    """Handle clicks in the merchant shop interface"""
    if not merchant_shop_open:
        return False
    
    shop_width = 900
    shop_height = 700
    shop_x = (SCREEN_WIDTH - shop_width) // 2
    shop_y = (SCREEN_HEIGHT - shop_height) // 2
    
    # Check if click is in shop area
    if not (shop_x <= mx <= shop_x + shop_width and shop_y <= my <= shop_y + shop_height):
        return False
    
    # Check category buttons
    categories = ["tools", "armor", "consumables", "blocks"]
    cat_x = shop_x + 30
    cat_y = shop_y + 120
    cat_width = 180
    cat_height = 40
    
    for i, cat in enumerate(categories):
        cat_rect = pygame.Rect(cat_x + i * (cat_width + 10), cat_y, cat_width, cat_height)
        if cat_rect.collidepoint(mx, my):
            global merchant_selected_category, merchant_page
            merchant_selected_category = cat
            merchant_page = 0
            print(f"🏪 Switched to {cat} category")
            return True
    
    # Check buy buttons
    if merchant_selected_category in MERCHANT_ITEMS:
        items = list(MERCHANT_ITEMS[merchant_selected_category].items())
        items_per_page = 6
        start_idx = merchant_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        
        item_y = shop_y + 180
        items_per_row = 3
        item_width = 250
        item_height = 140
        
        for i, (item_id, item_data) in enumerate(items[start_idx:end_idx]):
            row = i // items_per_row
            col = i % items_per_row
            
            item_x = shop_x + 30 + col * (item_width + 20)
            item_y_pos = item_y + row * (item_height + 20)
            
            buy_rect = pygame.Rect(item_x + 15, item_y_pos + 95, 100, 30)
            
            if buy_rect.collidepoint(mx, my):
                buy_merchant_item(merchant_selected_category, item_id)
                return True
    
    return True  # Click was in shop area

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
    
    try:
        from network.multiplayer_server import ServerDiscovery
        discovery = ServerDiscovery()
        discovered_servers = discovery.discover_servers()
        
        # Convert to our format
        server_list = []
        for server in discovered_servers:
            server_info = {
                "name": server.name,
                "world": "Default World",  # Server doesn't specify world
                "players": server.players,
                "max_players": server.max_players,
                "version": server.version,
                "description": f"Server at {server.host}:{server.port}",
                "address": server.host,
                "port": server.port
            }
            server_list.append(server_info)
        
        print(f"🔍 Discovered {len(server_list)} servers")
    except Exception as e:
        print(f"⚠️ Server discovery failed: {e}")
        # Fallback to demo servers
        server_list = [
            {
                "name": "Epic Adventure Server",
                "world": "Epic World",
                "players": 3,
                "max_players": 20,
                "version": "1.0.0",
                "description": "Join us for epic adventures!",
                "address": "127.0.0.1",
                "port": 5555
            },
            {
                "name": "Creative Building Server", 
                "world": "Creative World",
                "players": 8,
                "max_players": 20,
                "version": "1.0.0",
                "description": "Build amazing creations together!",
                "address": "127.0.0.2",
                "port": 5555
            }
        ]
        print(f"🔍 Using fallback servers: {len(server_list)} servers")
    
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
        # T key now opens inventory instead of chat
            
        if chat_input_active:
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


def build_fortress(origin_x, ground_y, fortress_type="ancient_ruins"):
    """Build a fortress of the specified type with unique characteristics"""
    global discovered_fortresses, current_fortress_discovery, discovery_timer
    
    fortress_info = FORTRESS_TYPES.get(fortress_type, FORTRESS_TYPES["ancient_ruins"])
    
    # Get fortress dimensions
    width = random.randint(fortress_info["min_size"], fortress_info["max_size"])
    height = random.randint(8, 12)
    
    # Choose materials based on fortress type
    materials = fortress_info["materials"]
    primary_material = materials[0] if materials else "stone"
    
    # Build fortress ABOVE ground level
    fortress_base_y = ground_y - height
    
    # Foundation
    for dx in range(width):
        set_block(origin_x + dx, ground_y, primary_material)
    
    # Main walls
    for dy in range(1, height + 1):
        for dx in range(width):
            x = origin_x + dx
            y = ground_y - dy
            if dx == 0 or dx == width - 1 or dy == height:  # Exterior walls
                set_block(x, y, primary_material)
            else:
                # Interior air
                if get_block(x, y) not in (None, "air"):
                    world_data.pop((x, y), None)
    
    # Add floors and special features based on fortress type
    floor_levels = [ground_y - 3, ground_y - 6, ground_y - 9]
    
    # Special fortress features
    if fortress_type == "dragon_keep":
        # Dragon Keep - larger, more floors, special blocks
        floor_levels = [ground_y - 3, ground_y - 6, ground_y - 9, ground_y - 12]
        # Add special blocks
        for dx in range(2, width - 2):
            if random.random() < 0.3:
                set_block(origin_x + dx, ground_y - 1, "diamond")
    elif fortress_type == "wizard_tower":
        # Wizard Tower - tall and narrow
        height = 15
        width = 8
        floor_levels = [ground_y - 4, ground_y - 8, ground_y - 12]
        # Add magical blocks
        for dx in range(2, width - 2):
            if random.random() < 0.4:
                set_block(origin_x + dx, ground_y - 1, "gold")
    elif fortress_type == "demon_castle":
        # Demon Castle - dark and menacing
        floor_levels = [ground_y - 3, ground_y - 6, ground_y - 9, ground_y - 12]
        # Add dark blocks
        for dx in range(2, width - 2):
            if random.random() < 0.3:
                set_block(origin_x + dx, ground_y - 1, "coal")
    
    # Add floors
    for floor_y in floor_levels:
        for dx in range(2, width - 2):
            set_block(origin_x + dx, floor_y, primary_material)
        
        # Ladder to next floor
        ladder_x = origin_x + width // 2
        set_block(ladder_x, floor_y + 1, "ladder")
        set_block(ladder_x, floor_y + 2, "ladder")
    
    # Add chests with fortress-specific loot using existing chest system
    for i, floor_y in enumerate(floor_levels):
        chest_x = origin_x + 2 + (i * 3) % (width - 4)
        set_block(chest_x, floor_y + 1, "chest")
        # Use existing chest system to generate loot
        chest_system.place_chest(world_system, chest_x, floor_y + 1, "fortress")
    
    # Add enemies based on fortress type
    enemy_count = 3 if fortress_type in ["common", "uncommon"] else 5 if fortress_type in ["rare", "epic"] else 8
    for i in range(enemy_count):
        enemy_x = origin_x + random.randint(2, width - 3)
        enemy_y = ground_y - random.randint(2, height - 2)
        if get_block(enemy_x, enemy_y) == "air":
            # Different enemy types for different fortresses
            if fortress_type == "demon_castle":
                enemy_type = "zombie"
            elif fortress_type == "dragon_keep":
                enemy_type = "zombie"  # Could add dragon later
            else:
                enemy_type = "zombie"
            
            entities.append({
                "type": enemy_type,
                "x": float(enemy_x),
                "y": float(enemy_y),
                "hp": 10,
                "dir": random.choice([-1, 1])
            })
    
    # Trigger discovery if this is a new fortress type
    if fortress_type not in discovered_fortresses:
        discovered_fortresses.add(fortress_type)
        current_fortress_discovery = fortress_type
        discovery_timer = 180  # 3 seconds at 60 FPS
        print(f"🏰 DISCOVERED NEW FORTRESS: {fortress_info['name']} ({fortress_info['rarity'].upper()})")
    
    print(f"🏰 {fortress_info['name']} built at ({origin_x}, {ground_y}) with {len(floor_levels)} floors!")

def maybe_generate_fortress_for_chunk(chunk_id, base_x):
    """Generate a random fortress type in this chunk based on rarity."""
    
    # Don't generate if chunk already exists (village system removed)
    return
    
    rng = random.Random(f"fortress-{chunk_id}")
    
    # Select fortress type based on rarity
    fortress_type = select_fortress_type(rng)
    if fortress_type is None:
        return
    
    fortress_info = FORTRESS_TYPES[fortress_type]
    
    # Check if this fortress type should spawn based on its spawn chance
    if rng.random() > fortress_info["spawn_chance"]:
        return
    
    fortress_x = base_x + rng.randint(10, 40)
    fortress_y = ground_y_of_column(fortress_x)
    if fortress_y is None:
        fortress_y = 0 + int(2 * math.sin(fortress_x * 0.2))
        set_block(fortress_x, fortress_y, "grass")
    
    # Build the fortress with the selected type
    build_fortress(fortress_x, fortress_y, fortress_type)
    # Village generation removed

def select_fortress_type(rng):
    """Select a fortress type based on rarity weights"""
    # Calculate total weight
    total_weight = sum(fortress["spawn_chance"] for fortress in FORTRESS_TYPES.values())
    
    if total_weight == 0:
        return None
    
    # Random selection based on spawn chances
    random_value = rng.random() * total_weight
    current_weight = 0
    
    for fortress_type, fortress_info in FORTRESS_TYPES.items():
        current_weight += fortress_info["spawn_chance"]
        if random_value <= current_weight:
            return fortress_type
    
    # Fallback to first fortress type
    return list(FORTRESS_TYPES.keys())[0]


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

def get_biome_type(x):
    """Determine biome type based on position - creates forest, field, mixed, and desert biomes"""
    # Use sine waves to create natural biome boundaries
    import math
    
    # Distance from spawn (x=0) - deserts spawn further away
    distance_from_spawn = abs(x)
    
    # Large-scale biome variation
    forest_noise = math.sin(x * 0.02) + math.sin(x * 0.05) * 0.5
    field_noise = math.sin(x * 0.03) + math.sin(x * 0.07) * 0.3
    desert_noise = math.sin(x * 0.01) + math.sin(x * 0.04) * 0.6
    
    # Add some randomness for natural variation
    forest_noise += random.uniform(-0.3, 0.3)
    field_noise += random.uniform(-0.2, 0.2)
    desert_noise += random.uniform(-0.4, 0.4)
    
    # Desert biomes spawn far from spawn (distance > 200) with high desert noise
    if distance_from_spawn > 200 and desert_noise > 0.4:
        return "desert"
    elif forest_noise > 0.3:
        return "forest"
    elif field_noise > 0.2:
        return "field"
    else:
        # Mixed biome - sparse trees
        return "mixed"

def should_generate_tree(x, surface_y, biome_type):
    """Determine if a tree should be generated based on biome and conditions"""
    # Check if there's already a tree nearby
    for check_x in range(x - 5, x + 6):
        for check_y in range(surface_y - 4, surface_y):
            if get_block(check_x, check_y) in ["log", "leaves"]:
                return False
    
    # DON'T place trees on village structures (oak_planks, beds, chests)
    for check_x in range(x - 2, x + 3):
        for check_y in range(surface_y - 5, surface_y + 1):
            block = get_block(check_x, check_y)
            if block in ["oak_planks", "bed", "chest", "door"]:
                return False  # This is a village area - no trees!
    
    # Biome-based tree generation
    if biome_type == "forest":
        # Forests: High tree density (30% chance)
        return random.random() < 0.3
    elif biome_type == "field":
        # Fields: Very few trees (2% chance)
        return random.random() < 0.02
    else:  # mixed
        # Mixed: Moderate tree density (8% chance)
        return random.random() < 0.08

def can_place_chest_on_grass(x, y):
    """Check if a chest can be placed according to the grass rule"""
    global broken_grass_locations
    
    # Create location key for tracking
    location_key = f"{x},{y}"
    
    # If the grass at this location was broken by the player, allow chest placement
    if location_key in broken_grass_locations:
        return True
    
    # During world generation, chests can only be placed on grass blocks
    grass_block = get_block(x, y)
    if grass_block == "grass":
        return True
    
    # If there's no grass block, chest cannot be placed (rule is active)
    return False

def mark_grass_broken(x, y):
    """Mark that the grass at this location was broken by the player"""
    global broken_grass_locations
    location_key = f"{x},{y}"
    broken_grass_locations.add(location_key)
    print(f"🌱 Grass at ({x}, {y}) marked as broken - chest placement rule disabled for this location")


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
    current_username = get_current_username()
    if current_username:
        username_text = font.render(f"Player: {current_username}", True, (255, 255, 100))
        screen.blit(username_text, (10, 10))
    
    # Draw coins display at the top
    coins_display = coins_manager.get_formatted_balance() if coins_manager else "0"
    coins_text = font.render(f"💰 {coins_display}", True, (255, 215, 0))
    screen.blit(coins_text, (10, 35))
        
    # Draw HP and hunger below player info
    hp_text = font.render("Health:", True, (255, 255, 255))
    hunger_text = font.render("Hunger:", True, (255, 255, 255))
    screen.blit(hp_text, (10, 60))
    screen.blit(hunger_text, (10, 90))
    
    # Calculate text width for alignment
    hp_text_width = hp_text.get_width()
    hunger_text_width = hunger_text.get_width()
    max_text_width = max(hp_text_width, hunger_text_width)
    
    # Draw HP and hunger bars aligned with text
    bar_start_x = 10 + max_text_width + 10  # 10px padding after text
    for i in range(10):
        hp_img = alive_hp if i < player["health"] else dead_hp
        screen.blit(hp_img, (bar_start_x + i * 20, 60))
        hunger_color = (255, 165, 0) if i < player["hunger"] else (80, 80, 80)
        pygame.draw.rect(screen, hunger_color, (bar_start_x + i * 20, 90, 16, 16))
    
    
    # Character info removed as requested


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
                
                # Apply pickaxe animation offset if it's a pickaxe and animation is active
                if item_type == "pickaxe" and pickaxe_animation_active:
                    hand_y += pickaxe_animation_offset
                
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
    # OPTIMIZED: Only check blocks that could be visible on screen
    # Calculate visible area bounds (convert to integers for range())
    min_x = int(camera_x // TILE_SIZE) - 1
    max_x = int((camera_x + SCREEN_WIDTH) // TILE_SIZE) + 2
    min_y = int(camera_y // TILE_SIZE) - 1
    max_y = int((camera_y + SCREEN_HEIGHT) // TILE_SIZE) + 2
    
    # Only iterate through potentially visible blocks (HUGE performance boost!)
    for x in range(min_x, max_x):
        for y in range(min_y, max_y):
            # Get block at this position
            block = get_block(x, y)
            
            if not block or block == "air":
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
            
            # Use static texture for now
            animated_frame = None
            if animated_frame:
                img = animated_frame
            
            # NATURAL WATER RENDERING: Water blocks now have beautiful textures built-in
            screen_x = x * TILE_SIZE - camera_x
            screen_y = y * TILE_SIZE - camera_y
            screen.blit(img, (screen_x, screen_y))

    # Cave entrance indicators removed - caves are disabled

        # Draw Lost Ruins entrance indicators
        for ruins_x, ruins_y in lost_ruins_entrances:
            screen_x = (ruins_x * TILE_SIZE) - camera_x
            screen_y = (ruins_y * TILE_SIZE) - camera_y
            
            # Only draw if on screen
            if -TILE_SIZE < screen_x < SCREEN_WIDTH and -TILE_SIZE < screen_y < SCREEN_HEIGHT:
                # Draw Lost Ruins entrance indicator (ancient stone arch)
                pygame.draw.rect(screen, (80, 60, 40), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, (100, 80, 60), (screen_x + 2, screen_y + 2, TILE_SIZE - 4, TILE_SIZE - 4))
                # Draw arch shape
                pygame.draw.arc(screen, (60, 40, 20), (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 0, 3.14, 3)

    # OPTIMIZED: Draw entities with culling
    for entity in entities:
        if entity["type"] == "monster":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            
            # OPTIMIZED: Skip entities outside screen
            if ex < -TILE_SIZE or ex > SCREEN_WIDTH + TILE_SIZE or ey < -TILE_SIZE or ey > SCREEN_HEIGHT + TILE_SIZE:
                continue
            
            # Check if monster should use GIF animation
            monster_gif_path = os.path.join(MOB_DIR, "monster.gif")
            # Use static monster image
            screen.blit(entity["image"], (ex, ey))
        elif entity["type"] == "final_boss":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            
            # Skip if outside screen
            if ex < -TILE_SIZE or ex > SCREEN_WIDTH + TILE_SIZE or ey < -TILE_SIZE or ey > SCREEN_HEIGHT + TILE_SIZE:
                continue
            
            # Draw boss
            screen.blit(entity["image"], (ex, ey))
            
            # Draw boss health bar
            health_ratio = entity["hp"] / entity["max_hp"]
            bar_width = 60
            bar_height = 8
            bar_x = ex + (TILE_SIZE - bar_width) // 2
            bar_y = ey - 15
            
            # Background
            pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # Health
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))
            # Border
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
        elif entity["type"] == "projectile":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            pygame.draw.rect(screen, (200, 50, 50), (ex + 12, ey + 12, 8, 8))
        elif entity["type"] == "boss_projectile":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            pygame.draw.rect(screen, (255, 100, 0), (ex + 12, ey + 12, 12, 12))  # Larger, orange projectile
        elif entity["type"] == "fireball":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            pygame.draw.circle(screen, (255, 100, 0), (ex + 16, ey + 16), 8)  # Orange fireball
        elif entity["type"] == "villager":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            
            # Skip if outside screen
            if ex < -TILE_SIZE or ex > SCREEN_WIDTH + TILE_SIZE or ey < -TILE_SIZE or ey > SCREEN_HEIGHT + TILE_SIZE:
                continue
            
            # Draw villager
            screen.blit(entity["image"], (ex, ey))
            
            # Draw villager name with job
            job_name = entity.get("job", "Villager")
            villager_text = font.render(job_name, True, (0, 100, 0))
            text_rect = villager_text.get_rect(center=(ex + TILE_SIZE//2, ey - 10))
            screen.blit(villager_text, text_rect)
        elif entity["type"] == "fortress_boss":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            
            # Skip if outside screen
            if ex < -TILE_SIZE or ex > SCREEN_WIDTH + TILE_SIZE or ey < -TILE_SIZE or ey > SCREEN_HEIGHT + TILE_SIZE:
                continue
            
            # Draw fortress boss
            screen.blit(entity["image"], (ex, ey))
            
            # Draw boss health bar
            health_ratio = entity["hp"] / entity["max_hp"]
            bar_width = 50
            bar_height = 6
            bar_x = ex + (TILE_SIZE - bar_width) // 2
            bar_y = ey - 15
            
            # Background
            pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # Health
            pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, int(bar_width * health_ratio), bar_height))
            # Border
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
            
            # Boss name
            boss_text = font.render("Fortress Boss", True, (255, 100, 0))
            screen.blit(boss_text, (ex, ey - 30))
        elif entity["type"] == "fireball":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            pygame.draw.circle(screen, (255, 100, 0), (ex + 16, ey + 16), 8)  # Orange fireball
        elif entity["type"] == "zombie":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            screen.blit(textures["zombie"], (ex, ey))
        elif entity["type"] == "rock_projectile":
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            # Draw rock projectile as a brown circle
            pygame.draw.circle(screen, (139, 69, 19), (ex + 16, ey + 16), 8)
        
        elif entity["type"] == "villager":
            # Draw villagers with a simple character sprite
            ex = int(entity["x"] * TILE_SIZE) - camera_x
            ey = int(entity["y"] * TILE_SIZE) - camera_y
            
            # Draw villager as a simple character (brown shirt, blue pants)
            pygame.draw.rect(screen, (139, 69, 19), (ex + 4, ey + 8, 24, 16))  # Brown shirt
            pygame.draw.rect(screen, (0, 100, 200), (ex + 6, ey + 20, 20, 12))  # Blue pants
            pygame.draw.circle(screen, (255, 220, 177), (ex + 16, ey + 6), 6)  # Head
            pygame.draw.circle(screen, (0, 0, 0), (ex + 14, ey + 5), 1)  # Left eye
            pygame.draw.circle(screen, (0, 0, 0), (ex + 18, ey + 5), 1)  # Right eye
            pygame.draw.arc(screen, (0, 0, 0), (ex + 14, ey + 6, 4, 2), 0, 3.14)  # Smile
            
            # Draw name tag above villager
            villager_name = entity.get("name", "Villager")
            name_text = font.render(villager_name, True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(ex + 16, ey - 10))
            # Draw background for name tag
            pygame.draw.rect(screen, (0, 0, 0), (name_rect.x - 2, name_rect.y - 2, name_rect.width + 4, name_rect.height + 4))
            screen.blit(name_text, name_rect)
            
            # Draw interaction indicator above villager
            if entity.get("shop_type"):
                indicator_text = font.render("🏪", True, (255, 215, 0))  # Gold shop icon
            else:
                indicator_text = font.render("💬", True, (255, 255, 255))  # Regular chat icon
            indicator_x = ex + (TILE_SIZE - indicator_text.get_width()) // 2
            indicator_y = ey - 25
            screen.blit(indicator_text, (indicator_x, indicator_y))
        
        # Shopkeeper drawing removed - now available in title screen
        
        # Legend NPC drawing removed - no more random NPCs
    
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

    # Draw thrown sword projectile
    draw_thrown_sword()
    draw_thrown_sword_entities()

    # Draw player with animation system
    px = int(player["x"] * TILE_SIZE) - camera_x
    py = int(player["y"] * TILE_SIZE) - camera_y
    
    # EXTREME ENGINEERING: Draw player with proper facing direction and flipping
    facing_direction = player.get("facing_direction", 1)
    
    # Always use fallback system for now to ensure flipping works
    _draw_player_fallback(px, py, facing_direction)
    
    # Draw armor on player if equipped
    draw_player_armor(px, py)
    
    # Draw held item on player's right hand
    draw_held_item(px, py)
    
    # Draw head bump effect
    draw_head_bump_effect(px, py)
    
    # Draw blood particles
    draw_blood_particles()
    
    # Draw block particles
    draw_block_particles()
    
    # Name tag removed - no more floating name above player
    
    # Draw multiplayer chat if connected
    if is_connected:
        draw_multiplayer_chat()


def _draw_player_fallback(px, py, facing_direction):
    """Draw player with new animation system"""
    # Determine animation based on player state
    animation_name = "standing"  # Default to standing
    
    # Check if player is moving horizontally
    if "last_x" in player and "last_y" in player:
        dx = abs(player["x"] - player["last_x"])
        dy = abs(player["y"] - player["last_y"])
        
        if dx > 0.01:  # Player is moving horizontally
            animation_name = "walking"
        elif dy > 0.01 and player.get("vel_y", 0) > 0:  # Player is falling
            animation_name = "falling"
    
    # Get animation from the new system
    try:
        animation_image = player_animator.get_animation(animation_name)
        
        if animation_image:
            # Use the animation image
            if facing_direction == -1:  # Facing left
                flipped_image = pygame.transform.flip(animation_image, True, False)
                screen.blit(flipped_image, (px, py))
            else:  # Facing right (default)
                screen.blit(animation_image, (px, py))
            
            return
        else:
            print(f"⚠️ No animation image for {animation_name}")
            
    except Exception as e:
        print(f"❌ Error getting animation {animation_name}: {e}")
    
    # Fallback to static player image if animation not found
    if facing_direction == -1:  # Facing left
        flipped_image = pygame.transform.flip(player_image, True, False)
        screen.blit(flipped_image, (px, py))
    else:  # Facing right (default)
        screen.blit(player_image, (px, py))
    


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
                        # Use static carrot image
                        animated_frame = None
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
    """Give the player starting items - REMOVED: Now using starter chest instead"""
    # No longer give starting items directly - use starter chest instead
    print("📦 Starting items now available in starter chest at spawn!")

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
    global final_boss_active
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
            # Check if player has weapon selected
            if check_weapon_requirement():
                # EXTREME ENGINEERING: Deal damage to boss with weapon
                damage_amount = get_weapon_damage()
                damage_boss(damage_amount)
                weapon_name = player["inventory"][player["selected"]]["type"].replace("_", " ").title()
                show_message(f"⚔️ You hit the boss with your {weapon_name} for {damage_amount} damage!", 1500)
                print(f"⚔️ Player dealt {damage_amount} damage to boss with {weapon_name}!")
                return True  # Attack successful, don't break blocks
            else:
                show_message("⚔️ You need a weapon to attack the boss!", 2000)
                return False  # Need weapon to attack boss
    
    # Final boss combat
    if final_boss_active:
        # Find the boss entity
        for entity in entities:
            if entity["type"] == "final_boss":
                boss_x = entity["x"]
                boss_y = entity["y"]
                
                # Check if player is close enough to hit boss
                if abs(player["x"] - boss_x) < 2 and abs(player["y"] - boss_y) < 2:
                    # Check if player has weapon selected
                    if check_weapon_requirement():
                        # Deal damage to final boss
                        damage_amount = get_weapon_damage()
                        entity["hp"] -= damage_amount
                        show_message(f"👹 Final boss hit! Health: {entity['hp']}/{entity['max_hp']}", 1000)
                        print(f"👹 Final boss hit! Health: {entity['hp']}/{entity['max_hp']}")
                        
                        if entity["hp"] <= 0:
                            # Final boss defeated
                            final_boss_active = False
                            entities.remove(entity)
                            show_message("🎉 FINAL BOSS DEFEATED! You won the game!", 5000)
                            print("🎉 FINAL BOSS DEFEATED! You won the game!")
                            
                            # Give massive reward
                            for _ in range(10):
                                add_to_inventory("diamond")
                            add_to_inventory("gold")
                            add_to_inventory("gold")
                            add_to_inventory("gold")
                            show_message("💎 Rewarded with 10 diamonds and 3 gold!", 3000)
                            print("💎 Rewarded with 10 diamonds and 3 gold!")
                            
                            # Show credits screen after a delay
                            pygame.time.wait(2000)  # Wait 2 seconds
                            global credits_from_boss_defeat
                            credits_from_boss_defeat = True
                            game_state = GameState.CREDITS
                            print("🎬 Credits screen activated!")
                        return True  # Attack successful, don't break blocks
                    else:
                        show_message("⚔️ You need a weapon to attack the final boss!", 2000)
                        return False  # Need weapon to attack final boss
                break
    
    # Stone & ores require pickaxe - STRICT REQUIREMENT
    if block in ["stone", "coal", "iron", "gold", "diamond"]:
        # Check if player has pickaxe selected
        if player["selected"] >= len(player["inventory"]) or player["inventory"][player["selected"]]["type"] != "pickaxe":
            return False  # Need pickaxe, silent fail
        
        # Start pickaxe animation
        start_pickaxe_animation()
        
        # Successfully break with pickaxe
        add_to_inventory(block)
        
        # Create block breaking particles
        particle_x = (bx * TILE_SIZE) - camera_x + TILE_SIZE // 2
        particle_y = (by * TILE_SIZE) - camera_y + TILE_SIZE // 2
        create_block_particles(particle_x, particle_y, block, 15)
        
        # Track grass blocks that have been broken by the player
        if block == "grass":
            mark_grass_broken(bx, by)
        
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
            
            # Create block breaking particles
            particle_x = (bx * TILE_SIZE) - camera_x + TILE_SIZE // 2
            particle_y = (by * TILE_SIZE) - camera_y + TILE_SIZE // 2
            create_block_particles(particle_x, particle_y, "log", 12)
            
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
            
            # Create block breaking particles
            particle_x = (bx * TILE_SIZE) - camera_x + TILE_SIZE // 2
            particle_y = (by * TILE_SIZE) - camera_y + TILE_SIZE // 2
            create_block_particles(particle_x, particle_y, "log", 10)
            
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
        
        # Create block breaking particles
        particle_x = (bx * TILE_SIZE) - camera_x + TILE_SIZE // 2
        particle_y = (by * TILE_SIZE) - camera_y + TILE_SIZE // 2
        create_block_particles(particle_x, particle_y, "oak_planks", 8)  # Chest particles look like wood
        
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
        
        # Remove torch from light sources if it's a torch (disabled - lighting system off)
        # if block == "torch":
        #     remove_torch(bx, by)
        
        # Create block breaking particles
        particle_x = (bx * TILE_SIZE) - camera_x + TILE_SIZE // 2
        particle_y = (by * TILE_SIZE) - camera_y + TILE_SIZE // 2
        create_block_particles(particle_x, particle_y, block, 12)
        
        # Track grass blocks that have been broken by the player
        if block == "grass":
            mark_grass_broken(bx, by)
        
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
        
        # Check for sand blocks above that need to fall
        check_sand_falling(bx, by)
        
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
    elif item_type == "torch":
        set_block(bx, by, "torch")
        # add_torch(bx, by)  # Lighting system disabled
        print(f"🔥 Placed torch at ({bx}, {by})!")
    else:
        set_block(bx, by, item_type)
    
    # Consume one item
    item["count"] -= 1
    if item["count"] <= 0:
        player["inventory"].pop(player["selected"])
        normalize_inventory()
    
    
    return True  # Success

def is_sword_type(item_type):
    """Check if an item type is a sword"""
    return item_type in ["sword", "stone_sword", "diamond_sword", "gold_sword", "enchanted_sword", "legendary_sword"]

def throw_sword_at_target(target_x, target_y):
    """Throw sword at a target location, prioritizing closest monster"""
    global thrown_sword
    
    if not is_sword_type(player["inventory"][player["selected"]]["type"]):
        return False
    
    # Find closest monster to click location
    closest_monster = None
    closest_distance = float('inf')
    final_target_x = target_x
    final_target_y = target_y
    
    for mob in entities[:]:
        if mob["type"] in ["monster", "zombie"]:
            mob_x, mob_y = mob["x"], mob["y"]
            click_distance = math.hypot(target_x - mob_x, target_y - mob_y)
            if click_distance < closest_distance:
                closest_distance = click_distance
                closest_monster = mob
                final_target_x = mob_x
                final_target_y = mob_y
    
    # Calculate distance to final target
    px, py = player["x"], player["y"]
    distance = math.hypot(final_target_x - px, final_target_y - py)
    
    if distance > sword_throw_range:
        print(f"🎯 Target too far! Range: {distance:.1f}, Max: {sword_throw_range}")
        return False
    
    # Store sword info and remove from inventory
    sword_item = player["inventory"][player["selected"]].copy()
    original_slot = player["selected"]
    
    # Remove sword from inventory temporarily
    player["inventory"][player["selected"]] = None
    normalize_inventory()
    
    # Create thrown sword projectile
    thrown_sword = {
        'x': px,
        'y': py,
        'target_x': final_target_x,
        'target_y': final_target_y,
        'returning': False,
        'sword_type': sword_item["type"],
        'original_slot': original_slot,
        'sword_item': sword_item
    }
    
    if closest_monster:
        print(f"🗡️ Throwing {sword_item['type']} at {closest_monster['type']}!")
    else:
        print(f"🗡️ Throwing {sword_item['type']} at target location!")
    return True

def slash_sword_at_target(target_x, target_y):
    """Perform close-range sword slash"""
    px, py = player["x"], player["y"]
    distance = math.hypot(target_x - px, target_y - py)
    
    if distance > sword_slash_range:
        print(f"⚔️ Target too far for slash! Range: {distance:.1f}, Max: {sword_slash_range}")
        return False
    
    print(f"⚔️ Performing sword slash!")
    # Trigger slash animation (will be handled by animation system)
    return True

def update_thrown_sword():
    """Update thrown sword position and handle collisions"""
    global thrown_sword
    
    if not thrown_sword:
        return
    
    sword = thrown_sword
    px, py = player["x"], player["y"]
    
    if not sword["returning"]:
        # Check for monster hits along the sword's path BEFORE moving
        hit_monster = False
        for mob in entities[:]:
            if mob["type"] in ["monster", "zombie"]:
                mob_x, mob_y = mob["x"], mob["y"]
                # Check if sword is close enough to hit the monster
                if math.hypot(sword["x"] - mob_x, sword["y"] - mob_y) <= 0.8:
                    # Hit monster!
                    mob["hp"] = mob.get("hp", 4) - 1
                    hit_monster = True
                    print(f"🗡️ Sword hit {mob['type']}! HP: {mob['hp']}/4")
                    
                    # Create hit effect particles
                    hit_x = (mob["x"] * TILE_SIZE) - camera_x
                    hit_y = (mob["y"] * TILE_SIZE) - camera_y
                    create_blood_particles(hit_x, hit_y, 8)
                    
                    if mob["hp"] <= 0:
                        # Track monster kill
                        track_monster_kill()
                        
                        # Create dramatic blood spray for death
                        death_x = (mob["x"] * TILE_SIZE) - camera_x
                        death_y = (mob["y"] * TILE_SIZE) - camera_y
                        create_monster_death_blood_spray(death_x, death_y)
                        
                        # Monster defeated - chance to drop coins
                        if random.random() < 0.15 and coins_manager:
                            coin_amount = random.randint(1, 2)
                            coins_manager.add_coins(coin_amount)
                        
                        entities.remove(mob)
                        print(f"💀 {mob['type']} defeated!")
                    break
        
        if hit_monster:
            # Sword hit something, start returning immediately
            sword["returning"] = True
        else:
            # Move towards target
            dx = sword["target_x"] - sword["x"]
            dy = sword["target_y"] - sword["y"]
            distance = math.hypot(dx, dy)
            
            if distance < 0.1:  # Reached target
                # Start returning to player
                sword["returning"] = True
            else:
                # Move towards target
                move_x = (dx / distance) * sword_throw_speed
                move_y = (dy / distance) * sword_throw_speed
                sword["x"] += move_x
                sword["y"] += move_y
    else:
        # Returning to player
        dx = px - sword["x"]
        dy = py - sword["y"]
        distance = math.hypot(dx, dy)
        
        if distance < 0.5:  # Close enough to player
            # Return sword to inventory
            if sword["original_slot"] < len(player["inventory"]):
                player["inventory"][sword["original_slot"]] = sword["sword_item"]
            else:
                # Add to first available slot
                for i, slot in enumerate(player["inventory"]):
                    if slot is None:
                        player["inventory"][i] = sword["sword_item"]
                        break
            
            normalize_inventory()
            print(f"🗡️ {sword['sword_type']} returned to inventory!")
            thrown_sword = None
        else:
            # Move towards player
            move_x = (dx / distance) * sword_return_speed
            move_y = (dy / distance) * sword_return_speed
            sword["x"] += move_x
            sword["y"] += move_y

def update_thrown_sword_entities():
    """Update thrown sword entities in the entities list"""
    global entities, player
    
    entities_to_remove = []
    
    for entity in entities[:]:
        if entity["type"] == "thrown_sword":
            sword = entity
            px, py = player["x"], player["y"]
            
            if not sword["returning"]:
                # Check for monster hits
                hit_monster = False
                for mob in entities[:]:
                    if mob["type"] in ["monster", "zombie", "boss"] and mob != sword:
                        # Check if sword is close to monster
                        if abs(sword["x"] - mob["x"]) < 1.0 and abs(sword["y"] - mob["y"]) < 1.0:
                            # Hit the monster
                            damage = 3  # Sword damage
                            mob["health"] = mob.get("health", 4) - damage
                            print(f"⚔️ Sword hit {mob['type']} for {damage} damage!")
                            
                            # Add blood particle effect
                            add_blood_particle(sword["x"], sword["y"])
                            
                            # Remove monster if health is 0
                            if mob["health"] <= 0:
                                # Create dramatic blood spray for death
                                death_x = (mob["x"] * TILE_SIZE) - camera_x
                                death_y = (mob["y"] * TILE_SIZE) - camera_y
                                create_monster_death_blood_spray(death_x, death_y)
                                
                                entities.remove(mob)
                                print(f"💀 {mob['type']} defeated by thrown sword!")
                            
                            hit_monster = True
                            break
                
                if hit_monster:
                    # Sword hit something, start returning
                    sword["returning"] = True
                    continue
                
                # Move towards target monster
                if sword["target"] and sword["target"] in entities:
                    target = sword["target"]
                    dx = target["x"] - sword["x"]
                    dy = target["y"] - sword["y"]
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance < 0.1:
                        # Reached target, start returning
                        sword["returning"] = True
                    else:
                        # Move towards target
                        move_x = (dx / distance) * sword["speed"]
                        move_y = (dy / distance) * sword["speed"]
                        sword["x"] += move_x
                        sword["y"] += move_y
                else:
                    # Target lost, start returning
                    sword["returning"] = True
            else:
                # Sword is returning to player
                dx = px - sword["x"]
                dy = py - sword["y"]
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 0.5:
                    # Sword returned to player
                    # Put sword back in inventory
                    if sword["original_slot"] < len(player["inventory"]):
                        player["inventory"][sword["original_slot"]] = sword["sword_item"]
                    else:
                        # Add to first available slot
                        for i, slot in enumerate(player["inventory"]):
                            if slot is None:
                                player["inventory"][i] = sword["sword_item"]
                                break
                    
                    normalize_inventory()
                    print(f"🗡️ {sword['sword_type']} returned to inventory!")
                    entities_to_remove.append(sword)
                else:
                    # Move towards player
                    move_x = (dx / distance) * sword["speed"]
                    move_y = (dy / distance) * sword["speed"]
                    sword["x"] += move_x
                    sword["y"] += move_y
    
    # Remove returned swords
    for entity in entities_to_remove:
        if entity in entities:
            entities.remove(entity)

def draw_thrown_sword():
    """Draw the thrown sword projectile with visual effects"""
    if not thrown_sword:
        return
    
    sword = thrown_sword
    screen_x = (sword["x"] * TILE_SIZE) - camera_x
    screen_y = (sword["y"] * TILE_SIZE) - camera_y
    
    # Only draw if sword is on screen
    if -TILE_SIZE < screen_x < SCREEN_WIDTH and -TILE_SIZE < screen_y < SCREEN_HEIGHT:
        # Draw sword texture (use sword texture from textures dict)
        sword_texture = textures.get(sword["sword_type"], textures.get("sword"))
        if sword_texture:
            # Rotate sword based on direction
            dx = sword["target_x"] - sword["x"] if not sword["returning"] else player["x"] - sword["x"]
            dy = sword["target_y"] - sword["y"] if not sword["returning"] else player["y"] - sword["y"]
            angle = math.atan2(dy, dx) * 180 / math.pi
            
            # Rotate and draw sword
            rotated_sword = pygame.transform.rotate(sword_texture, -angle)
            sword_rect = rotated_sword.get_rect(center=(screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2))
            screen.blit(rotated_sword, sword_rect)
            
            # Add a glowing effect around the sword
            glow_radius = 8
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            glow_color = (255, 255, 100, 80)  # Yellow glow with transparency
            pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), glow_radius)
            glow_rect = glow_surface.get_rect(center=(screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2))
            screen.blit(glow_surface, glow_rect)
        else:
            # Fallback: draw a simple sword shape
            pygame.draw.rect(screen, (200, 200, 200), (screen_x + 12, screen_y + 8, 8, 16))
            pygame.draw.rect(screen, (139, 69, 19), (screen_x + 14, screen_y + 20, 4, 8))  # Handle

def draw_thrown_sword_entities():
    """Draw thrown sword entities in the entities list"""
    for entity in entities:
        if entity["type"] == "thrown_sword":
            sword = entity
            screen_x = (sword["x"] * TILE_SIZE) - camera_x
            screen_y = (sword["y"] * TILE_SIZE) - camera_y
            
            # Only draw if sword is on screen
            if -TILE_SIZE < screen_x < SCREEN_WIDTH and -TILE_SIZE < screen_y < SCREEN_HEIGHT:
                # Draw sword image
                sword_image = pygame.image.load("../../../../items/sword.png").convert_alpha()
                sword_image = pygame.transform.scale(sword_image, (TILE_SIZE, TILE_SIZE))
                
                # Rotate sword based on direction
                if sword["returning"]:
                    # Point towards player
                    dx = player["x"] - sword["x"]
                    dy = player["y"] - sword["y"]
                    if dx != 0 or dy != 0:
                        angle = math.degrees(math.atan2(dy, dx))
                        sword_image = pygame.transform.rotate(sword_image, -angle)
                else:
                    # Point towards target
                    if sword["target"] and sword["target"] in entities:
                        target = sword["target"]
                        dx = target["x"] - sword["x"]
                        dy = target["y"] - sword["y"]
                        if dx != 0 or dy != 0:
                            angle = math.degrees(math.atan2(dy, dx))
                            sword_image = pygame.transform.rotate(sword_image, -angle)
                
                screen.blit(sword_image, (screen_x, screen_y))
                
                # Draw sword trail effect
                trail_alpha = 100
                trail_color = (255, 255, 100, trail_alpha)
                trail_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, trail_color, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//3)
                screen.blit(trail_surface, (screen_x, screen_y))

def attack_monsters(mx, my):
    """Attack monsters with sword - distance-based combat"""
    px, py = player["x"], player["y"]
    target_x = (mx + camera_x) / TILE_SIZE
    target_y = (my + camera_y) / TILE_SIZE
    distance = math.hypot(target_x - px, target_y - py)
    
    # Check if player has a sword equipped
    if player["selected"] >= len(player["inventory"]) or not player["inventory"][player["selected"]]:
        return
    
    sword_type = player["inventory"][player["selected"]]["type"]
    if not is_sword_type(sword_type):
        return
    
    # Check if sword is already thrown
    if thrown_sword:
        print("🗡️ Sword is already thrown! Wait for it to return.")
        return
    
    # Find closest monster to click location
    closest_monster = None
    closest_distance = float('inf')
    
    for mob in entities[:]:
        if mob["type"] in ["monster", "zombie"]:
            mob_x, mob_y = mob["x"], mob["y"]
            click_distance = math.hypot(target_x - mob_x, target_y - mob_y)
            if click_distance < closest_distance:
                closest_distance = click_distance
                closest_monster = mob
    
    if not closest_monster:
        return
    
    # Determine combat type based on distance
    if distance <= sword_slash_range:
        # Close combat - slash animation
        slash_sword_at_target(target_x, target_y)
        # Deal damage immediately for close combat
        closest_monster["hp"] = closest_monster.get("hp", 4) - 1
        # Show health bar when hit
        show_monster_health(closest_monster)
        if closest_monster["hp"] <= 0:
            # Track monster kill
            track_monster_kill()
            
            # Create dramatic blood spray for death
            death_x = (closest_monster["x"] * TILE_SIZE) - camera_x
            death_y = (closest_monster["y"] * TILE_SIZE) - camera_y
            create_monster_death_blood_spray(death_x, death_y)
            
            # Monster defeated - chance to drop coins
            if random.random() < 0.15 and coins_manager:
                coin_amount = random.randint(1, 2)
                coins_manager.add_coins(coin_amount)
                        
            entities.remove(closest_monster)
    else:
        # Long range - throw sword at monster
        throw_sword_at_monster(closest_monster)


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
        play_damage_sound()
        if player["health"] <= 0:
            show_death_screen()

    # Carrots: collect to inventory
    if block_at == "carrot":
            add_to_inventory("carrot")
            # Remove carrot completely from world data (turns into air)
            if f"{px},{py}" in world_data:
                del world_data[f"{px},{py}"]
            show_message("🥕 Carrot collected! Right-click in inventory to eat", 1500)
            print(f"🥕 Carrot collected and added to inventory")
            
            # Check for first carrot achievement
            check_achievement("first_carrot", 10, "Collected first carrot!")
    elif block_below == "carrot":
        add_to_inventory("carrot")
        # Remove carrot completely from world data (turns into air)
        if f"{px},{py + 1}" in world_data:
            del world_data[f"{px},{py + 1}"]
        show_message("🥕 Carrot collected! Right-click in inventory to eat", 1500)
        print(f"🥕 Carrot collected and added to inventory")
    
    # Portal interaction (Lost Ruins portal)
    if block_at == "portal":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_e]:
            spawn_final_boss()
            show_message("🌀 Portal activated! Final boss spawned!", 3000)
    
    # Check for villager interaction
    for entity in entities:
        if entity["type"] == "villager":
            entity_x = int(entity["x"])
            entity_y = int(entity["y"])
            
            # Check if player is near villager
            if abs(px - entity_x) <= 1 and abs(py - entity_y) <= 1:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_e]:
                    interact_with_villager(entity)

    # Fall damage: apply if fall was 4+ blocks
    if not player["on_ground"]:
        if fall_start_y is None:
            fall_start_y = player["y"]
    else:
        if fall_start_y is not None and player["y"] - fall_start_y >= 4:
            damage = calculate_armor_damage_reduction(1)
            player["health"] -= damage
            play_damage_sound()
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
    current_username = get_current_username()
    player_info = font.render(f"Player: {current_username or 'Unknown'}", True, (255, 255, 100))
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
        
        # Old crafting UI removed - using new backpack crafting system
        # recipe_name = check_crafting_recipe(crafting_materials)
        # if recipe_name:
        #     recipe = CRAFTING_RECIPES[recipe_name]
        #     ...
            
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
        "I - Close inventory",
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

def draw_backpack_ui():
    """Draw the backpack interface with hotbar display"""
    global backpack_close_button
    
    # Get mouse position
    mouse_pos = pygame.mouse.get_pos()
    
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Backpack window
    backpack_width = 700
    backpack_height = 600
    backpack_x = center_x(backpack_width)
    backpack_y = (SCREEN_HEIGHT - backpack_height) // 2
    
    # Draw backpack background
    pygame.draw.rect(screen, (40, 40, 60), (backpack_x, backpack_y, backpack_width, backpack_height))
    pygame.draw.rect(screen, (100, 100, 200), (backpack_x, backpack_y, backpack_width, backpack_height), 3)  # Blue border
    
    # Backpack title
    title = BIG_FONT.render("🎒 Backpack", True, (255, 255, 255))
    screen.blit(title, (backpack_x + 20, backpack_y + 20))
    
    # Player info
    current_username = get_current_username()
    player_info = font.render(f"Player: {current_username or 'Unknown'}", True, (255, 255, 100))
    screen.blit(player_info, (backpack_x + 20, backpack_y + 70))
    
    # Instructions
    instructions = font.render("Press I to close • Drag items to move them", True, (200, 200, 200))
    screen.blit(instructions, (backpack_x + 20, backpack_y + 100))
    
    # Hotbar section (top)
    hotbar_x = backpack_x + 50
    hotbar_y = backpack_y + 130
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
    
    # Backpack slots section (bottom)
    backpack_slots_x = backpack_x + 50
    backpack_slots_y = backpack_y + 320
    backpack_slots_title = font.render("🎒 Backpack Storage", True, (255, 255, 255))
    screen.blit(backpack_slots_title, (backpack_slots_x, backpack_slots_y - 30))
    
    # Draw backpack slots (6x6 grid for 36 slots)
    slot_size = 50
    slots_per_row = 6
    total_rows = 6
    start_x = backpack_slots_x
    start_y = backpack_slots_y
    
    for row in range(total_rows):
        for col in range(slots_per_row):
            slot_idx = row * slots_per_row + col
            slot_x = start_x + col * (slot_size + 5)
            slot_y = start_y + row * (slot_size + 5)
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            
            # Draw slot background
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
                        screen.blit(count_text, (slot_x + slot_size - 15, slot_y + slot_size - 15))
    
    # CRAFTING PANEL (right side of backpack)
    crafting_x = backpack_x + backpack_width + 20
    crafting_y = backpack_y
    crafting_width = 280
    crafting_height = 600
    
    # Draw crafting panel background
    pygame.draw.rect(screen, (50, 50, 70), (crafting_x, crafting_y, crafting_width, crafting_height))
    pygame.draw.rect(screen, (150, 150, 200), (crafting_x, crafting_y, crafting_width, crafting_height), 3)
    
    # Crafting title
    craft_title = font.render("🔨 Crafting", True, (255, 215, 0))
    screen.blit(craft_title, (crafting_x + 20, crafting_y + 20))
    
    # Instructions
    inst_text = small_font.render("Right-click items to select", True, (200, 200, 200))
    screen.blit(inst_text, (crafting_x + 10, crafting_y + 50))
    
    # Selected materials display
    materials_y = crafting_y + 80
    materials_title = font.render("Materials:", True, (255, 255, 255))
    screen.blit(materials_title, (crafting_x + 10, materials_y))
    
    # Show selected materials
    mat_y = materials_y + 30
    if selected_crafting_materials:
        for material, count in selected_crafting_materials.items():
            mat_text = small_font.render(f"{count}x {material.replace('_', ' ').title()}", True, (200, 255, 200))
            screen.blit(mat_text, (crafting_x + 15, mat_y))
            mat_y += 25
    else:
        no_mat_text = small_font.render("No materials selected", True, (150, 150, 150))
        screen.blit(no_mat_text, (crafting_x + 15, mat_y))
    
    # Check what can be crafted
    possible_recipes = check_can_craft(selected_crafting_materials)
    
    # Available recipes display
    recipes_y = crafting_y + 250
    recipes_title = font.render("Can Craft:", True, (255, 255, 255))
    screen.blit(recipes_title, (crafting_x + 10, recipes_y))
    
    # Recipe list area
    recipe_list_y = recipes_y + 30
    recipe_list_height = 200  # Reduced height to make room for clear button
    max_visible_recipes = 5  # How many recipes fit in the visible area (reduced to show scrollbar sooner)
    
    recipe_y = recipe_list_y
    if possible_recipes:
        global crafting_scroll_offset
        
        # Calculate scroll bounds
        total_recipes = len(possible_recipes)
        max_scroll = max(0, total_recipes - max_visible_recipes)
        crafting_scroll_offset = max(0, min(crafting_scroll_offset, max_scroll))
        
        # Get visible recipes - either all or limited based on show_all_recipes
        global show_all_recipes
        if show_all_recipes:
            visible_recipes = possible_recipes  # Show all recipes
        else:
            visible_start = crafting_scroll_offset
            visible_end = min(visible_start + max_visible_recipes, total_recipes)
            visible_recipes = possible_recipes[visible_start:visible_end]
        
        # Draw visible recipes
        if not hasattr(draw_backpack_ui, 'recipe_buttons'):
            draw_backpack_ui.recipe_buttons = {}
        else:
            draw_backpack_ui.recipe_buttons.clear()
        
        for recipe_name in visible_recipes:
            recipe = CRAFTING_RECIPES[recipe_name]
            
            # Draw recipe button
            recipe_rect = pygame.Rect(crafting_x + 10, recipe_y, crafting_width - 40, 35)
            is_hovered = recipe_rect.collidepoint(mouse_pos)
            
            button_color = (80, 150, 80) if is_hovered else (60, 100, 60)
            pygame.draw.rect(screen, button_color, recipe_rect)
            pygame.draw.rect(screen, (100, 200, 100), recipe_rect, 2)
            
            # Draw item texture preview
            if recipe_name in textures:
                icon = pygame.transform.scale(textures[recipe_name], (28, 28))
                screen.blit(icon, (crafting_x + 15, recipe_y + 4))
            
            # Draw recipe name and output count
            recipe_text = small_font.render(f"{recipe['output_count']}x {recipe_name.replace('_', ' ').title()}", True, (255, 255, 255))
            screen.blit(recipe_text, (crafting_x + 50, recipe_y + 10))
            
            # Store recipe button for clicking
            draw_backpack_ui.recipe_buttons[recipe_name] = recipe_rect
            
            recipe_y += 40
        
        # Show "View All" / "View Less" button when there are more recipes than can fit
        print(f"🔍 Debug: total_recipes={total_recipes}, max_visible_recipes={max_visible_recipes}")
        if total_recipes > max_visible_recipes:
            # Position button more visibly - in the recipe area, not below it
            view_all_btn = pygame.Rect(crafting_x + 10, recipe_list_y + recipe_list_height - 40, 120, 35)
            is_hovered = view_all_btn.collidepoint(mouse_pos)
            
            # Make button much more visible with bright colors
            btn_color = (100, 200, 100) if is_hovered else (80, 180, 80)  # Bright green
            border_color = (150, 255, 150) if is_hovered else (120, 220, 120)  # Bright green border
            
            # Draw button with stronger visibility
            pygame.draw.rect(screen, btn_color, view_all_btn, border_radius=8)
            pygame.draw.rect(screen, border_color, view_all_btn, 3, border_radius=8)
            
            # Button text - changes based on current view
            if show_all_recipes:
                btn_text = small_font.render("View Less", True, (0, 0, 0))  # Black text for contrast
            else:
                btn_text = small_font.render(f"View All ({total_recipes})", True, (0, 0, 0))  # Black text
            
            text_x = view_all_btn.x + (view_all_btn.width - btn_text.get_width()) // 2
            text_y = view_all_btn.y + (view_all_btn.height - btn_text.get_height()) // 2
            screen.blit(btn_text, (text_x, text_y))
            
            print(f"🔍 View All button drawn at {view_all_btn}")
            # Store button for click detection
            draw_backpack_ui.view_all_button = view_all_btn
    else:
        no_recipes_text = small_font.render("Select materials to see recipes", True, (150, 150, 150))
        screen.blit(no_recipes_text, (crafting_x + 15, recipe_y))
    
    # Clear materials button (moved down to not block scrollbar)
    clear_btn = pygame.Rect(crafting_x + 10, crafting_y + crafting_height - 80, crafting_width - 40, 35)
    pygame.draw.rect(screen, (150, 50, 50), clear_btn)
    pygame.draw.rect(screen, (200, 100, 100), clear_btn, 2)
    clear_text = font.render("Clear Selection", True, (255, 255, 255))
    screen.blit(clear_text, (clear_btn.x + 50, clear_btn.y + 10))
    
    if not hasattr(draw_backpack_ui, 'clear_button'):
        draw_backpack_ui.clear_button = clear_btn
    else:
        draw_backpack_ui.clear_button = clear_btn
    
    # Close button
    close_button = pygame.Rect(backpack_x + backpack_width - 120, backpack_y + 20, 100, 30)
    pygame.draw.rect(screen, (200, 50, 50), close_button)
    pygame.draw.rect(screen, (255, 255, 255), close_button, 2)
    close_text = font.render("Close (I)", True, (255, 255, 255))
    screen.blit(close_text, (close_button.x + 10, close_button.y + 8))
    
    # Store button reference for click detection
    backpack_close_button = close_button
    
    # Draw dragged item if any
    if inventory_drag_item:
        mx, my = mouse_pos
        # Add a semi-transparent background for better visibility
        drag_bg = pygame.Surface((40, 40), pygame.SRCALPHA)
        drag_bg.fill((255, 255, 255, 100))  # Semi-transparent white background
        screen.blit(drag_bg, (mx - 20, my - 20))
        
        # Draw the item icon centered on cursor
        item_type = inventory_drag_item.get("type")
        if item_type in textures:
            screen.blit(textures[item_type], (mx - 16, my - 16))
        
        # Draw count if more than 1
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
        game_state = GameState.TITLE
        update_pause_state()  # Pause time when returning to title
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
        game_state = GameState.TITLE
        update_pause_state()  # Pause time when returning to title
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
        # Old crafting system removed - using new backpack crafting
        # craft_btn = pygame.Rect(inv_x + 700, inv_y + 220, 70, 30)
        # if craft_btn.collidepoint(mouse_pos):
        #     ... old crafting code ...
        #     return
        
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

def handle_backpack_click(mouse_pos):
    """Handle clicks in the backpack interface"""
    global backpack_close_button, inventory_drag_item, inventory_drag_from
    global selected_crafting_materials
    
    # Check if close button was clicked
    if backpack_close_button and backpack_close_button.collidepoint(mouse_pos):
        game_state = GameState.GAME
        update_pause_state()  # Resume time when closing backpack
        return
    
    # Check if clear crafting materials button was clicked
    if hasattr(draw_backpack_ui, 'clear_button') and draw_backpack_ui.clear_button.collidepoint(mouse_pos):
        selected_crafting_materials = {}
        print("🧹 Cleared crafting materials")
        return
    
    # Check if a recipe button was clicked
    if hasattr(draw_backpack_ui, 'recipe_buttons'):
        for recipe_name, rect in draw_backpack_ui.recipe_buttons.items():
            if rect.collidepoint(mouse_pos):
                craft_item(recipe_name)
                return
    
    # Check if View All button was clicked
    if hasattr(draw_backpack_ui, 'view_all_button'):
        global show_all_recipes
        if draw_backpack_ui.view_all_button.collidepoint(mouse_pos):
            show_all_recipes = not show_all_recipes
            print(f"🔍 View All button clicked! Now showing all recipes: {show_all_recipes}")
            return
    
    # Calculate backpack UI position
    backpack_width, backpack_height = 700, 600
    backpack_x = center_x(backpack_width)
    backpack_y = (SCREEN_HEIGHT - backpack_height) // 2
    
    # Handle left click for drag and drop
    if pygame.mouse.get_pressed()[0]:  # Left mouse button
        # Check hotbar slots (3x3 grid)
        hotbar_x = backpack_x + 50
        hotbar_y = backpack_y + 130
        
        for row in range(3):
            for col in range(3):
                slot_idx = row * 3 + col
                slot_x = hotbar_x + col * 60
                slot_y = hotbar_y + row * 60
                slot_rect = pygame.Rect(slot_x, slot_y, 50, 50)
                
                if slot_rect.collidepoint(mouse_pos):
                    # Check if it's a food item for left-click eating
                    if slot_idx < len(player["inventory"]) and player["inventory"][slot_idx]:
                        item = player["inventory"][slot_idx]
                        if isinstance(item, dict) and "type" in item:
                            item_type = item["type"]
                            if item_type in FOOD_ITEMS:
                                # Eat the food on left-click
                                if eat_food(item_type):
                                    # Remove one from stack or delete item
                                    if "count" in item and item["count"] > 1:
                                        item["count"] -= 1
                                    else:
                                        # Remove the item completely
                                        player["inventory"][slot_idx] = None
                                    # Normalize inventory to clean up None entries
                                    normalize_inventory()
                                return
                    # Otherwise, handle normal slot click
                    handle_inventory_slot_click("hotbar", slot_idx, mouse_pos)
                    return
        
        # Check backpack slots (6x6 grid for 36 slots)
        backpack_slots_x = backpack_x + 50
        backpack_slots_y = backpack_y + 320
        slot_size = 50
        slots_per_row = 6
        total_rows = 6
        
        for row in range(total_rows):
            for col in range(slots_per_row):
                slot_idx = row * slots_per_row + col
                slot_x = backpack_slots_x + col * (slot_size + 5)
                slot_y = backpack_slots_y + row * (slot_size + 5)
                slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
                
                if slot_rect.collidepoint(mouse_pos):
                    # Normal left-click - drag and drop
                    handle_inventory_slot_click("backpack", slot_idx, mouse_pos)
                    return

def count_item_in_inventory(item_type):
    """Count how many of a specific item type the player has in inventory and backpack"""
    total_count = 0
    
    # Count in hotbar/inventory (3x3 grid = 9 slots)
    for i in range(min(9, len(player["inventory"]))):
        item = player["inventory"][i]
        if item and isinstance(item, dict) and item.get("type") == item_type:
            total_count += item.get("count", 1)
    
    # Count in backpack (36 slots)
    for item in player.get("backpack", []):
        if item and isinstance(item, dict) and item.get("type") == item_type:
            total_count += item.get("count", 1)
    
    return total_count

def handle_inventory_right_click(mouse_pos):
    """Handle right-click on inventory items to select for crafting or eat food"""
    global selected_crafting_materials
    
    # Get backpack UI position
    backpack_width, backpack_height = 700, 600
    backpack_x = center_x(backpack_width)
    backpack_y = (SCREEN_HEIGHT - backpack_height) // 2
    
    # Check hotbar slots (3x3 grid) - can be used for eating food
    hotbar_x = backpack_x + 50
    hotbar_y = backpack_y + 130
    
    for row in range(3):
        for col in range(3):
            slot_idx = row * 3 + col
            slot_x = hotbar_x + col * 60
            slot_y = hotbar_y + row * 60
            slot_rect = pygame.Rect(slot_x, slot_y, 50, 50)
            
            if slot_rect.collidepoint(mouse_pos):
                # Try to eat food from hotbar OR select for crafting
                if slot_idx < len(player["inventory"]) and player["inventory"][slot_idx]:
                    item = player["inventory"][slot_idx]
                    if isinstance(item, dict) and "type" in item:
                        item_type = item["type"]
                        # Check how many we have vs how many already selected
                        total_available = count_item_in_inventory(item_type)
                        already_selected = selected_crafting_materials.get(item_type, 0)
                        
                        if already_selected >= total_available:
                            show_message(f"❌ You've already put all {item_type.replace('_', ' ')} in crafting!", 1500)
                            return
                        
                        # Select item for crafting
                        count_to_add = 1
                        selected_crafting_materials[item_type] = already_selected + count_to_add
                        print(f"🔨 Selected {item_type} for crafting! Total: {selected_crafting_materials[item_type]}/{total_available}")
                        show_message(f"🔨 Selected {item_type} ({selected_crafting_materials[item_type]}/{total_available})", 1000)
                        return
                return
    
    # Check backpack slots (6x6 grid for 36 slots) - select for crafting
    backpack_slots_x = backpack_x + 50
    backpack_slots_y = backpack_y + 320
    slot_size = 50
    slots_per_row = 6
    total_rows = 6
    
    for row in range(total_rows):
        for col in range(slots_per_row):
            slot_idx = row * slots_per_row + col
            slot_x = backpack_slots_x + col * (slot_size + 5)
            slot_y = backpack_slots_y + row * (slot_size + 5)
            slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
            
            if slot_rect.collidepoint(mouse_pos):
                # RIGHT CLICK - Select for crafting from backpack
                if slot_idx < len(player["backpack"]) and player["backpack"][slot_idx]:
                    item = player["backpack"][slot_idx]
                    if isinstance(item, dict) and "type" in item:
                        item_type = item["type"]
                        # Check how many we have vs how many already selected
                        total_available = count_item_in_inventory(item_type)
                        already_selected = selected_crafting_materials.get(item_type, 0)
                        
                        if already_selected >= total_available:
                            show_message(f"❌ You've already put all {item_type.replace('_', ' ')} in crafting!", 1500)
                            return
                        
                        # Select item for crafting
                        count_to_add = 1
                        selected_crafting_materials[item_type] = already_selected + count_to_add
                        print(f"🔨 Selected {item_type} for crafting! Total: {selected_crafting_materials[item_type]}/{total_available}")
                        show_message(f"🔨 Selected {item_type} ({selected_crafting_materials[item_type]}/{total_available})", 1000)
                        return
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
        # Handle armor slot - allow any item to be placed
        if inventory_drag_item:
            # Dropping any item into armor slot
            old_armor = player["armor"].get(slot_idx)
            player["armor"][slot_idx] = inventory_drag_item
            inventory_drag_item = old_armor
            if old_armor:
                inventory_drag_from = ("armor", slot_idx)
            else:
                inventory_drag_item = None
                inventory_drag_from = None
        else:
            # Picking up item from armor slot
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

# --- Map usage from inventory ---
def use_map_from_inventory():
    """Use a map from the currently selected slot to show area information."""
    if player["selected"] >= len(player["inventory"]):
        return
    item = player["inventory"][player["selected"]]
    if not item or not isinstance(item, dict) or item.get("type") != "map" or item.get("count", 0) <= 0:
        return

    # Show map information
    player_x = int(player["x"])
    player_y = int(player["y"])
    
    # Check what's around the player
    nearby_features = []
    
    # Check for ores nearby (within 10 blocks)
    ore_count = 0
    for dx in range(-10, 11):
        for dy in range(-10, 11):
            block = get_block(player_x + dx, player_y + dy)
            if block in ("coal", "iron", "gold", "diamond"):
                ore_count += 1
    
    if ore_count > 0:
        nearby_features.append(f"{ore_count} ores nearby")
    
    # Check for trees nearby
    tree_count = 0
    for dx in range(-20, 21):
        for dy in range(-20, 21):
            block = get_block(player_x + dx, player_y + dy)
            if block == "log":
                tree_count += 1
    
    if tree_count > 0:
        nearby_features.append(f"{tree_count} trees nearby")
    
    # Check for chests nearby
    chest_count = 0
    for dx in range(-15, 16):
        for dy in range(-15, 16):
            block = get_block(player_x + dx, player_y + dy)
            if block == "chest":
                chest_count += 1
    
    if chest_count > 0:
        nearby_features.append(f"{chest_count} chests nearby")
    
    # Check for villagers nearby
    villager_count = 0
    for entity in entities:
        if entity["type"] == "villager":
            distance = abs(entity["x"] - player_x) + abs(entity["y"] - player_y)
            if distance < 50:  # Within 50 blocks
                villager_count += 1
    
    if villager_count > 0:
        nearby_features.append(f"{villager_count} villagers nearby")
    
    # Show map information
    show_message("🗺️ MAP: Your location and nearby features:", 3000)
    show_message(f"🗺️ Position: ({player_x}, {player_y})", 2000)
    
    if nearby_features:
        for feature in nearby_features[:3]:  # Show up to 3 features
            show_message(f"🗺️ {feature}", 2000)
    else:
        show_message("🗺️ No special features detected nearby", 2000)
    
    print(f"🗺️ Map used at position ({player_x}, {player_y}) - Features: {nearby_features}")

# --- Missing Update Functions ---
def update_daylight():
    global is_day, day_start_time, paused_time, day_count, day_transition_progress, transitioning_to_day, sun_position, moon_position
    # Only update time when in the game state
    if game_state == GameState.GAME:
        # Check if it's time to start transitioning
        time_elapsed = time.time() - day_start_time - paused_time
        
        # Day/Night cycle is 2 minutes (120 seconds)
        # Last 20 seconds of each cycle is transition time
        if time_elapsed >= 100 and time_elapsed < 120:
            # In transition period (20 seconds)
            transition_amount = (time_elapsed - 100) / 20.0  # 0.0 to 1.0 over 20 seconds
            
            if is_day:
                # Transitioning to night (sun setting)
                transitioning_to_day = False
                day_transition_progress = 1.0 - transition_amount  # 1.0 -> 0.0
                sun_position = 0.2 + (transition_amount * 0.6)  # Sun moves across sky 0.2 -> 0.8
                moon_position = sun_position + 0.5  # Moon opposite to sun
            else:
                # Transitioning to day (sun rising)
                transitioning_to_day = True
                day_transition_progress = transition_amount  # 0.0 -> 1.0
                sun_position = 0.2 + (transition_amount * 0.6)  # Sun rises 0.2 -> 0.8
                moon_position = sun_position + 0.5  # Moon opposite to sun
        
        elif time_elapsed >= 120:
            # Transition complete, flip day/night
            is_day = not is_day
            day_start_time = time.time()
            paused_time = 0
            
            # Set final states
            if is_day:
                day_transition_progress = 1.0
                sun_position = 0.5  # Sun at zenith
                moon_position = 0.0  # Moon below horizon
                day_count += 1
                print(f"🌅 Day {day_count} has begun!")
            else:
                day_transition_progress = 0.0
                sun_position = 0.8  # Sun below horizon
                moon_position = 0.5  # Moon at zenith
                print(f"🌙 Night {day_count} has fallen!")
        else:
            # Not in transition - maintain full day or night
            if is_day:
                day_transition_progress = 1.0
                sun_position = 0.5  # Sun at zenith
            else:
                day_transition_progress = 0.0
                moon_position = 0.5  # Moon at zenith

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
    
    # Use reliable event-based shift key tracking instead of pygame.key.get_pressed()
    # This prevents the shift key from getting "stuck" in the pressed state
    global shift_key_pressed
    
    # Movement speed - normal speed by default, slow when shift is held
    base_speed = SLOW_SPEED if shift_key_pressed else MOVE_SPEED
    speed = base_speed  # Use the speed directly without frame-rate complications
    
    # Clamp speed to reasonable bounds
    speed = max(0.08, min(0.25, speed))
    

    # Horizontal movement intent - Use BOTH WASD and Arrow keys for movement AND character flipping
    move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]  # Left arrow OR A key
    move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]  # Right arrow OR D key
    
    # EXTREME ENGINEERING: Update facing direction immediately when keys are pressed
    # This allows both manual flipping (A/D) and automatic flipping during movement
    if move_left:
        player["facing_direction"] = -1  # Face left when A or left arrow is pressed
    if move_right:
        player["facing_direction"] = 1   # Face right when D or right arrow is pressed
    
    # Store current position for next frame comparison
    player["last_x"] = player["x"]

    # Check for ladder at player position (current or feet)
    px, py = player["x"], player["y"]
    on_ladder = (get_block(int(px), int(py)) == "ladder" or
                 get_block(int(px), int(py + 0.9)) == "ladder")

    if on_ladder:
        # Normal horizontal movement while on ladder
        if move_left:
            new_x = px - speed
            # Use improved collision detection for ladder movement too
            has_collision, block_type, collision_pos = check_collision_at_position(new_x, player["y"], 1.0, 1.0)
            if not has_collision:
                player["x"] = new_x
        if move_right:
            new_x = px + speed
            # Use improved collision detection for ladder movement too
            has_collision, block_type, collision_pos = check_collision_at_position(new_x, player["y"], 1.0, 1.0)
            if not has_collision:
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
        # Normal horizontal movement with enhanced collision detection
        if move_left:
            new_x = px - speed
            # Use improved collision detection
            has_collision, block_type, collision_pos = check_collision_at_position(new_x, player["y"], 1.0, 1.0)
            if not has_collision:
                player["x"] = new_x
            else:
                # Prevent movement through solid blocks
                print(f"🚫 Collision detected: {block_type} at {collision_pos} - preventing left movement")

        if move_right:
            new_x = px + speed
            # Use improved collision detection
            has_collision, block_type, collision_pos = check_collision_at_position(new_x, player["y"], 1.0, 1.0)
            if not has_collision:
                player["x"] = new_x
            else:
                # Prevent movement through solid blocks
                print(f"🚫 Collision detected: {block_type} at {collision_pos} - preventing right movement")

        # Normal gravity
        player["vel_y"] += GRAVITY
        if player["vel_y"] > MAX_FALL_SPEED:
            player["vel_y"] = MAX_FALL_SPEED

        # Normal fall speed
        next_y = player["y"] + player["vel_y"] / TILE_SIZE
        
        # Check collision at the target position using improved collision detection
        target_y = int(next_y + 1)
        
        # Check for head collision when moving up (jumping)
        if player["vel_y"] < 0:  # Moving up
            # Check for head collision at the target position (above player)
            head_y = int(next_y)  # Check where we're going to be
            has_head_collision, head_block, head_pos = check_collision_at_position(player["x"], head_y, 1.0, 0.5)
            if has_head_collision:
                # Head bump! Stop upward movement
                player["vel_y"] = 0
                trigger_head_bump()
                player["y"] = head_y + 1  # Keep player below the ceiling
                player["on_ground"] = False
            else:
                # No head collision, continue moving up
                player["y"] = next_y
                player["on_ground"] = False
        else:
            # Moving down (falling) - check for ground collision
            has_ground_collision, ground_block, ground_pos = check_collision_at_position(player["x"], target_y, 1.0, 1.0)
            if has_ground_collision:
                # Ground collision - stop falling and place player on top
                
                # Calculate fall damage before landing
                if player["fall_start_y"] is not None:
                    fall_height = player["fall_start_y"] - player["y"]
                    if fall_height >= FALL_DAMAGE_THRESHOLD:
                        # Calculate damage: 1 damage per block above threshold
                        damage = max(1, int((fall_height - FALL_DAMAGE_THRESHOLD) * FALL_DAMAGE_MULTIPLIER))
                        player["health"] = max(0, player["health"] - damage)
                        print(f"💥 FALL DAMAGE: Fell {fall_height:.1f} blocks, took {damage} damage! Health: {player['health']}")
                        
                        # Add damage particles
                        add_blood_particle(player["x"], player["y"])
                        
                        # Check if player died from fall damage
                        if player["health"] <= 0:
                            print("💀 Player died from fall damage!")
                            # Trigger death sequence
                            player["health"] = 0
                    
                    # Reset fall tracking
                    player["fall_start_y"] = None
                    player["fall_height"] = 0.0
                
                player["vel_y"] = 0
                player["on_ground"] = True
                player["y"] = target_y - 1  # Position player on top of the block
            else:
                # No ground collision - continue falling
                # Track fall height
                if player["fall_start_y"] is None:
                    player["fall_start_y"] = player["y"]
                player["fall_height"] = player["fall_start_y"] - player["y"]
                
                player["on_ground"] = False
                player["y"] = next_y

    # Simple jump system - press space to jump
    if keys[pygame.K_SPACE] and player.get("on_ground", False) and not on_ladder:
        # Check if there's a block above the player before jumping using improved collision detection
        head_y = int(player["y"] - 1)  # Check one block above current position
        has_head_collision, head_block, head_pos = check_collision_at_position(player["x"], head_y, 1.0, 0.5)
        
        # Only jump if there's no solid block above
        if not has_head_collision:
            # Simple, responsive jump
            player["vel_y"] = JUMP_STRENGTH
            # Reset fall tracking when jumping
            player["fall_start_y"] = None
            player["fall_height"] = 0.0
        else:
            print(f"🚫 Can't jump - blocked by {head_block} above!")
    
        # Ability system removed - no more wall jump

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
        villages = world_system.current_world_data.get("villages", [])
        
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
        
        # Load monster data
        monster_data = world_system.current_world_data.get("monster_data", {})
        if monster_data:
            global total_monsters_killed
            total_monsters_killed = monster_data.get("total_monsters_killed", 0)
            print(f"🌟 Monster data loaded: {total_monsters_killed} monsters killed")
        
        # Load chest data
        chest_data = world_system.current_world_data.get("chest_data", {})
        if chest_system and chest_data:
            # Restore chest inventories (convert string keys back to tuples)
            chest_inventories = chest_data.get("chest_inventories", {})
            if chest_inventories:
                # Convert string keys like "x,y" back to tuple keys (x, y)
                for key_str, inventory in chest_inventories.items():
                    try:
                        x, y = key_str.split(',')
                        key_tuple = (int(x), int(y))
                        chest_system.chest_inventories[key_tuple] = inventory
                    except (ValueError, IndexError):
                        print(f"⚠️ Invalid chest key format: {key_str}")
                print(f"📦 Loaded {len(chest_inventories)} chest inventories")
            
            # Restore player-placed chests (convert string keys back to tuples)
            player_placed_chests = chest_data.get("player_placed_chests", [])
            if player_placed_chests:
                # Convert string keys like "x,y" back to tuple keys (x, y)
                chest_system.player_placed_chests = set()
                for key_str in player_placed_chests:
                    try:
                        x, y = key_str.split(',')
                        key_tuple = (int(x), int(y))
                        chest_system.player_placed_chests.add(key_tuple)
                    except (ValueError, IndexError):
                        print(f"⚠️ Invalid player-placed chest key format: {key_str}")
                print(f"📦 Loaded {len(player_placed_chests)} player-placed chests")
        else:
            print("📦 No chest data to load or chest system not available")
        
        # Mark all existing columns as generated to prevent terrain regeneration
        global generated_terrain_columns
        generated_terrain_columns.clear()
        for block_key in world_data.keys():
            try:
                x, y = block_key.split(',')
                x = int(x)
                generated_terrain_columns.add(x)
            except (ValueError, TypeError):
                continue  # Skip invalid keys
        
        print(f"🌍 World data loaded: {len(world_data)} blocks, {len(entities)} entities")
        print(f"👤 Player loaded: health={player['health']}, hunger={player['hunger']}")
        print(f"🗺️ Marked {len(generated_terrain_columns)} columns as pre-generated")
        
        # Place starter chest at spawn location (don't fail if this errors)
        try:
            place_starter_chest()
        except Exception as chest_error:
            print(f"⚠️ Could not place starter chest: {chest_error}")
        
        print("✅ load_world_data() returning True")
        return True
        
    except Exception as e:
        print(f"❌ Error loading world data: {e}")
        return False

def throw_sword_at_monster(monster):
    """Throw sword at a specific monster"""
    global player, entities
    
    # Find sword in inventory
    sword_slot = None
    for i, item in enumerate(player["inventory"]):
        if item and item["type"] == "sword" and not item.get("throwing", False):
            sword_slot = i
            break
    
    if sword_slot is None:
        return False
    
    # Create thrown sword entity
    sword_item = player["inventory"][sword_slot].copy()
    sword_item["throwing"] = True
    sword_item["throw_target"] = monster
    sword_item["throw_distance"] = 0
    sword_item["max_throw_distance"] = 8.0  # Maximum throw distance
    
    # Create sword projectile
    thrown_sword = {
        "type": "thrown_sword",
        "x": player["x"],
        "y": player["y"],
        "target": monster,
        "sword_item": sword_item,
        "original_slot": sword_slot,
        "sword_type": "Iron Sword",
        "returning": False,
        "speed": 0.3
    }
    
    entities.append(thrown_sword)
    
    # Remove sword from inventory temporarily
    player["inventory"][sword_slot] = None
    normalize_inventory()
    
    print(f"🗡️ Sword thrown at monster!")
    return True

# Night monster spawning system
night_monster_spawn_timer = 0
night_monster_spawn_cooldown = 120  # 2 seconds at 60 FPS
max_night_monsters = 12  # Increased for more intense combat
night_monsters_spawned = False  # Track if we've spawned monsters for this night

# Nighttime visual effects
night_overlay_alpha = 0
night_overlay_surface = None

def update_monsters():
    global entities, night_monster_spawn_timer, night_monsters_spawned
    
    # OPTIMIZED: Night monster spawning system
    if not is_day:  # Only spawn monsters at night
        # Spawn monsters everywhere when night first falls
        if not night_monsters_spawned:
            spawn_monsters_everywhere_at_night()
            night_monsters_spawned = True
            print("🌙 Night has fallen! Monsters are spawning everywhere!")
        
        # Continue spawning monsters near player for intense combat
        night_monster_spawn_timer += 1
        
        # Check if it's time to spawn a monster near player
        if night_monster_spawn_timer >= night_monster_spawn_cooldown:
            # OPTIMIZED: Count monsters more efficiently
            monster_count = 0
            for mob in entities:
                if mob["type"] in ["monster", "zombie"]:
                    monster_count += 1
                    if monster_count >= max_night_monsters:
                        break
                        
            # Spawn monsters near player for intense combat
            if monster_count < max_night_monsters:
                spawn_night_monster_near_player()
                night_monster_spawn_timer = 0  # Reset timer
    else:
        # Reset timer during day and clean up night-spawned monsters
        night_monster_spawn_timer = 0
        night_monsters_spawned = False  # Reset for next night
        cleanup_night_monsters()
    
    # Update monster movement and combat
    update_monster_movement_and_combat()

def cleanup_night_monsters():
    """Remove night-spawned monsters when it becomes day"""
    global entities
    
    # Remove monsters that were spawned at night
    monsters_removed = 0
    for mob in entities[:]:
        if mob["type"] in ["monster", "zombie"] and mob.get("night_spawned", False):
            entities.remove(mob)
            monsters_removed += 1
    
    if monsters_removed > 0:
        print(f"🌅 Daytime: Removed {monsters_removed} night-spawned monsters")

def update_night_overlay():
    """Update the nighttime overlay effect"""
    global night_overlay_alpha, night_overlay_surface
    
    if not is_day:  # Nighttime
        # Fade in the overlay
        if night_overlay_alpha < 120:  # Max alpha for dark effect
            night_overlay_alpha += 2
    else:  # Daytime
        # Fade out the overlay
        if night_overlay_alpha > 0:
            night_overlay_alpha -= 2
    
    # Create overlay surface if needed
    if night_overlay_surface is None or night_overlay_surface.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
        night_overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

def draw_night_overlay():
    """Draw the nighttime overlay effect"""
    global night_overlay_alpha, night_overlay_surface
    
    if night_overlay_alpha > 0 and night_overlay_surface:
        # Fill with dark blue/purple tint
        night_overlay_surface.fill((20, 10, 40, night_overlay_alpha))
        screen.blit(night_overlay_surface, (0, 0))
        
        # Add some intensity text during night
        if not is_day and night_overlay_alpha > 100:
            monster_count = sum(1 for mob in entities if mob["type"] in ["monster", "zombie"])
            if monster_count > 0:
                intensity_text = f"👹 NIGHT INTENSITY: {monster_count} monsters nearby!"
                text_surface = font.render(intensity_text, True, (255, 100, 100))
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
                screen.blit(text_surface, text_rect)

def spawn_monsters_everywhere_at_night():
    """Spawn monsters across the entire world when night falls"""
    global entities
    import random
    
    # Get the current world bounds (explored area)
    if not world_data:
        return
    
    # Find the explored area bounds
    min_x = min(int(pos.split(',')[0]) for pos in world_data.keys())
    max_x = max(int(pos.split(',')[0]) for pos in world_data.keys())
    
    # Spawn monsters across the explored world
    monsters_spawned = 0
    max_world_monsters = 25  # Maximum monsters to spawn across the world
    
    # Spawn monsters in a grid pattern across the explored area
    for x in range(min_x, max_x + 1, 20):  # Every 20 blocks
        if monsters_spawned >= max_world_monsters:
            break
            
        # Find surface level at this position
        surface_y = find_surface_level(x)
        if surface_y is not None:
                        # Check if there's already a monster nearby
            nearby_monster = False
            for entity in entities:
                if entity["type"] in ["monster", "zombie"]:
                    distance = abs(entity["x"] - x)
                    if distance < 15:  # Within 15 blocks
                        nearby_monster = True
                        break
            
            # Spawn a monster if none nearby
            if not nearby_monster and random.random() < 0.7:  # 70% chance to spawn at night
                # Randomly choose between monster and zombie (30% chance for zombie)
                if random.random() < 0.3:  # 30% chance for zombie
                    monster_type = "zombie"
                    monster_hp = 12  # Zombies are stronger
                    monster_img = textures["zombie"]  # Use original zombie texture
                else:
                    monster_type = "monster"
                    monster_hp = 8
                    monster_img = textures["monster"]  # Use original monster texture
                
                # Spawn the monster
                entities.append({
                    "type": monster_type,
                    "x": float(x),
                    "y": float(surface_y),
                    "hp": monster_hp,
                    "cooldown": 0,
                    "image": monster_img,
                    "night_spawned": True  # Mark as night-spawned
                })
                
                monsters_spawned += 1
                print(f"👹 Night {monster_type} spawned at world position ({x}, {int(surface_y)})")
    
    print(f"🌙 Night monster spawning complete! Spawned {monsters_spawned} monsters across the world!")

def spawn_night_monster_near_player():
    """Spawn a monster right next to the player for intense nighttime combat"""
    global entities
    import random
    
    # Get player position
    player_x = player["x"]
    player_y = player["y"]
    
    # Spawn monsters RIGHT NEXT to the player (1-2 blocks away for immediate threat)
    spawn_distance = random.uniform(1, 2)
    spawn_angle = random.uniform(0, 2 * math.pi)
    
    # Calculate spawn position
    spawn_x = player_x + math.cos(spawn_angle) * spawn_distance
    spawn_y = player_y + math.sin(spawn_angle) * spawn_distance
    
    # Find surface level at spawn position (spawn ON the surface, not underground)
    surface_y = find_surface_level(int(spawn_x))
    if surface_y is not None:
        spawn_y = surface_y  # Spawn ON the surface
        
        # Check if there's already a monster very close
        too_close = False
        for mob in entities:
            if mob["type"] == "monster":
                distance = math.sqrt((mob["x"] - spawn_x)**2 + (mob["y"] - spawn_y)**2)
                if distance < 2:  # Too close to another monster
                    too_close = True
                    break
                        
        if not too_close:
            # Randomly choose between monster and zombie (30% chance for zombie)
            import random
            if random.random() < 0.3:  # 30% chance for zombie
                monster_type = "zombie"
                monster_hp = 12  # Zombies are stronger
                monster_img = textures["zombie"]  # Use original zombie texture
            else:
                monster_type = "monster"
                monster_hp = 8
                monster_img = textures["monster"]  # Use original monster texture
            
            # Spawn the monster
            entities.append({
                "type": monster_type,
                "x": float(spawn_x),
                "y": float(spawn_y),
                "hp": monster_hp,
                "cooldown": 0,
                "image": monster_img,
                "night_spawned": True  # Mark as night-spawned
            })
            
            monster_count = sum(1 for mob in entities if mob["type"] in ["monster", "zombie"])
            print(f"👹 Night {monster_type} spawned near player at ({int(spawn_x)}, {int(spawn_y)}) - Total: {monster_count}/{max_night_monsters}")

def find_ground_level(x):
    """Find the ground level at a given x coordinate"""
    # Look for the highest solid block at this x position
    for y in range(0, -50, -1):  # Check from surface down
        pos_key = f"{x},{y}"
        if pos_key in world_data:
            block_type = world_data[pos_key]
            if block_type in ["grass", "dirt", "stone", "sand", "gravel"]:
                return y
    return None

def find_surface_level(x):
    """Find the surface level at a given x coordinate (top of the world)"""
    # Look for the highest solid block at this x position from the top down
    for y in range(0, -200, -1):  # Check from surface down to bedrock
        pos_key = f"{x},{y}"
        if pos_key in world_data:
            block_type = world_data[pos_key]
            if block_type in ["grass", "dirt", "stone", "sand", "gravel", "leaves", "log"]:
                return y
    return None

def update_monster_movement_and_combat():
    """Update monster movement and combat (separated for performance)"""
    # OPTIMIZED: Cache player position to avoid repeated lookups
    player_x = player["x"]
    player_y = player["y"]
    
    # Move and attack existing monsters
    for mob in entities[:]:
        if mob["type"] == "monster":
            # Ensure each monster has health
            if "hp" not in mob:
                mob["hp"] = 7

            # OPTIMIZED: Calculate distance once and reuse
            dx = player_x - mob["x"]
            dy = player_y - mob["y"]
            dist_squared = dx * dx + dy * dy  # Avoid expensive sqrt for distance checks
            
            if dist_squared > 0:
                dist = math.sqrt(dist_squared)  # Only calculate sqrt when needed
                
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
                if dist_squared > 0:  # Use squared distance for efficiency
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

            # OPTIMIZED: Contact damage with squared distance check
            if dist_squared < 0.25:  # 0.5 * 0.5 = 0.25 (squared distance)
                # Check cooldown - monsters can only attack every 5 seconds
                current_time = pygame.time.get_ticks()
                if "last_attack_time" not in mob:
                    mob["last_attack_time"] = 0
                
                if current_time - mob["last_attack_time"] >= 5000:  # 5 seconds = 5000ms
                    damage = calculate_armor_damage_reduction(3)
                    player["health"] -= damage
                    play_damage_sound()
                    mob["last_attack_time"] = current_time  # Update attack time
                    print(f"👹 Monster attacked player! Cooldown: 5 seconds")
                    if player["health"] <= 0:
                        show_death_screen()
                else:
                    # Monster is on cooldown, no damage
                    remaining_cooldown = (5000 - (current_time - mob["last_attack_time"])) / 1000
                    if remaining_cooldown > 0:
                        print(f"👹 Monster on cooldown: {remaining_cooldown:.1f}s remaining")
        
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
                    # Check cooldown - zombies can only attack every 5 seconds
                    current_time = pygame.time.get_ticks()
                    if "last_attack_time" not in mob:
                        mob["last_attack_time"] = 0
                    
                    if current_time - mob["last_attack_time"] >= 5000:  # 5 seconds = 5000ms
                        damage = calculate_armor_damage_reduction(2)
                        player["health"] -= damage
                        play_damage_sound()
                        mob["last_attack_time"] = current_time  # Update attack time
                        print(f"🧟 Zombie attacked player! Cooldown: 5 seconds")
                        if player["health"] <= 0:
                            show_death_screen()
                    else:
                        # Zombie is on cooldown, no damage
                        remaining_cooldown = (5000 - (current_time - mob["last_attack_time"])) / 1000
                        if remaining_cooldown > 0:
                            print(f"🧟 Zombie on cooldown: {remaining_cooldown:.1f}s remaining")

    # Projectiles step and collision
    entities_to_remove = []
    
    for proj in entities[:]:
        if proj["type"] == "projectile":
            proj["x"] += proj["dx"]
            proj["y"] += proj["dy"]
            if abs(player["x"] - proj["x"]) < 0.5 and abs(player["y"] - proj["y"]) < 0.5:
                base_damage = proj.get("damage", 3)
                damage = calculate_armor_damage_reduction(base_damage)
                player["health"] -= damage
                play_damage_sound()
                entities_to_remove.append(proj)
                if player["health"] <= 0:
                    show_death_screen()
            elif proj["x"] < -100 or proj["x"] > 100 or proj["y"] > 100:
                entities_to_remove.append(proj)
        
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
                play_damage_sound()
                entities_to_remove.append(proj)
                print(f"💥 Rock projectile hit player! Damage: {damage}")
                if player["health"] <= 0:
                    show_death_screen()
            
            # Check lifetime and boundaries
            proj["lifetime"] = proj.get("lifetime", 180) - 1
            if (proj["lifetime"] <= 0 or 
                proj["x"] < -100 or proj["x"] > 100 or 
                proj["y"] > 100):
                entities_to_remove.append(proj)
        
        # Boss projectile update and collision
        elif proj["type"] == "boss_projectile":
            # Update position
            proj["x"] += proj["dx"]
            proj["y"] += proj["dy"]
            
            # Check collision with player
            if abs(player["x"] - proj["x"]) < 0.8 and abs(player["y"] - proj["y"]) < 0.8:
                base_damage = proj.get("damage", 5)
                damage = calculate_armor_damage_reduction(base_damage)
                player["health"] -= damage
                play_damage_sound()
                entities_to_remove.append(proj)
                print(f"🔥 Boss projectile hit player! Damage: {damage}")
                if player["health"] <= 0:
                    show_death_screen()
            
            # Check lifetime and boundaries
            proj["lifetime"] = proj.get("lifetime", 180) - 1
            if (proj["lifetime"] <= 0 or 
                proj["x"] < -100 or proj["x"] > 100 or 
                proj["y"] > 100):
                entities_to_remove.append(proj)
    
    # Remove entities after iteration
    for entity in entities_to_remove:
        if entity in entities:
            entities.remove(entity)



# --- Villager update logic ---

def update_hunger():
    """Update hunger system - decrease hunger every 200 seconds"""
    global hunger_timer, paused_time
    # Only update hunger when in the game state
    if game_state == GameState.GAME:
        current_time = time.time()
        if current_time - hunger_timer - paused_time >= 200:  # 200 seconds
            if player["health"] > 0:
                player["hunger"] -= 1
                print(f"🍖 Hunger decreased! Current hunger: {player['hunger']}/10")
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



# --- World Generation Function ---
def generate_initial_world(world_seed=None):
    """Generate a clean, organized world with proper layer hierarchy"""
    if world_seed is None:
        # Generate a truly random seed using timestamp and random number
        import time
        world_seed = int(time.time() * 1000) % 1000000 + random.randint(1, 1000)
        print(f"🎲 Generated random world seed: {world_seed}")
    
    # Set random seed for this world generation
    world_rng = random.Random(world_seed)
    print(f"🌍 Using world seed: {world_seed}")
    
    # Generate a clean starting area for the player
    start_x = world_rng.randint(-100, 100)  # Random starting X position
    world_width = world_rng.randint(150, 250)  # Consistent world width
    
    # Generate COMPLETELY FLAT terrain (no mountains, no variation)
    print("🌍 Generating completely flat world...")
    print(f"🌍 World width: {world_width}, Start X: {start_x}")
    print(f"🌍 Generating from X={start_x - world_width//2} to X={start_x + world_width//2}")
    
    # Generate terrain with clean layering - ALL FLAT
    for x in range(start_x - world_width//2, start_x + world_width//2):
        # EVERYTHING is completely flat at Y=10
        ground_y = 10  # Fixed height for entire world
        
        # ABSOLUTE SURFACE RULE: Grass and dirt NEVER underground, trees NEVER underground
        # CLEAN LAYER GENERATION - Stone closer to surface for building
        # Surface: Y=10 (grass)
        # Dirt: Y=11-12 (2 blocks deep) - NEVER deeper
        # Stone: Y=13-21 (9 blocks deep, starts at Y=13)
        # Bedrock: Y=22
        
        # 1. GRASS LAYER (Surface ONLY - NEVER underground!) - CHECK FOR EXISTING BLOCKS
        if get_block(x, ground_y) is None:
            set_block(x, ground_y, "grass")
            print(f"🌱 Placed grass at ({x}, {ground_y})")
        
        # 2. DIRT LAYER (Below grass, 2 blocks deep) - NEVER underground
        # STRICT RULE: Dirt can NEVER go deeper than 2 blocks below surface
        for y in range(ground_y + 1, ground_y + 3):  # Surface dirt layer only
            # CRITICAL: Only place dirt if it's DIRECTLY below surface grass
            # This ensures dirt NEVER spawns deep underground
            if y <= ground_y + 2 and get_block(x, y) is None:
                set_block(x, y, "dirt")
        
        # 3. STONE LAYER (Below dirt, starts closer to surface) - CHECK FOR EXISTING BLOCKS
        for y in range(ground_y + 3, ground_y + 12):
            if get_block(x, y) is None:  # Only place if empty
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
        
        # 4. BEDROCK LAYER (Completely flat, nothing below) - CHECK FOR EXISTING BLOCKS
        bedrock_y = 127  # Fixed bedrock level (bottom of screen)
        if get_block(x, bedrock_y) is None:
            set_block(x, bedrock_y, "bedrock")
        
        # TEMPORARILY DISABLE VALIDATION TO SEE IF GRASS GENERATES
        # validate_column_integrity(x, ground_y)
        
        # Ensure NO blocks generate below bedrock
        for y in range(bedrock_y + 1, 100):
            if get_block(x, y) is not None:
                world_data.pop((x, y), None)  # Remove any blocks below bedrock
        
        # BIOME-BASED TERRAIN: Handle desert biomes
        biome_type = get_biome_type(x)
        
        # DESERT BIOME TERRAIN: Replace grass with sand in desert biomes
        if biome_type == "desert":
            # Replace surface grass with sand
            if get_block(x, ground_y) == "grass":
                set_block(x, ground_y, "sand")
            # Replace underground dirt with sand too (desert sand goes deeper)
            for depth in range(1, min(8, ground_y + 1)):
                if get_block(x, ground_y + depth) == "dirt":
                    set_block(x, ground_y + depth, "sand")
        
        # BIOME-BASED TREE GENERATION: Forests have lots of trees, fields have few
        if biome_type == "desert":
            # Deserts have very few trees
            if random.random() < 0.02 and should_generate_tree(x, ground_y, biome_type):
                # Same tree generation as other biomes
                if get_block(x, ground_y - 1) is None and (ground_y - 1) < ground_y:
                    set_block(x, ground_y - 1, "log")
                    if get_block(x, ground_y - 2) is None and (ground_y - 2) < ground_y:
                        set_block(x, ground_y - 2, "log")
                    
                    # Leaves
                    for dx in [-1, 0, 1]:
                        for dy in [-3, -4]:
                            leaf_x, leaf_y = x + dx, ground_y + dy
                            if leaf_y < ground_y and get_block(leaf_x, leaf_y) is None:
                                set_block(leaf_x, leaf_y, "leaves")
        elif should_generate_tree(x, ground_y, biome_type):
            # ABSOLUTE RULE: Trees can ONLY spawn ABOVE surface (y < ground_y) - NEVER underground!
            # CRITICAL: Trees can NEVER EVER spawn underground or at ground level
            # Only place trees if there's clean space
            if get_block(x, ground_y - 1) is None and (ground_y - 1) < ground_y:
                set_block(x, ground_y - 1, "log")  # ABOVE surface only
                if get_block(x, ground_y - 2) is None and (ground_y - 2) < ground_y:
                    set_block(x, ground_y - 2, "log")  # ABOVE surface only
                
                # Clean leaf placement (only in empty spaces) - ONLY ABOVE SURFACE - NEVER underground!
            for dx in [-1, 0, 1]:
                for dy in [-3, -4]:
                    leaf_x, leaf_y = x + dx, ground_y + dy
                    # CRITICAL: Only place leaves if they're above surface (leaf_y < ground_y)
                    # ABSOLUTE: Leaves can NEVER EVER spawn at or below ground level
                    if leaf_y < ground_y and get_block(leaf_x, leaf_y) is None:
                        set_block(leaf_x, leaf_y, "leaves")

        # Clean carrot placement (only on grass, no messy spawning) - CHECK FOR EXISTING BLOCKS
        if in_carrot_biome(x):
            if can_place_surface_item(x, ground_y) and world_rng.random() < 0.8:  # Increased from 0.6 to 0.8
                # Only place carrot if the location is empty
                if get_block(x, ground_y - 1) is None:
                    set_block(x, ground_y - 1, "carrot")
                
                # Clean neighbor carrot spawning - CHECK FOR EXISTING BLOCKS
                gy_r = ground_y_of_column(x + 1)
                if gy_r is not None and can_place_surface_item(x + 1, gy_r) and world_rng.random() < 0.5:  # Increased from 0.35 to 0.5
                    if get_block(x + 1, gy_r - 1) is None:
                        set_block(x + 1, gy_r - 1, "carrot")
                gy_l = ground_y_of_column(x - 1)
                if gy_l is not None and can_place_surface_item(x - 1, gy_l) and world_rng.random() < 0.35:
                    if get_block(x - 1, gy_l - 1) is None:
                        set_block(x - 1, gy_l - 1, "carrot")
        else:
            if can_place_surface_item(x, ground_y) and world_rng.random() < 0.15:  # Increased from 0.05 to 0.15
                # Only place carrot if the location is empty
                if get_block(x, ground_y - 1) is None:
                    set_block(x, ground_y - 1, "carrot")

        # Chests removed from natural spawning - only spawn in fortresses and structures now
        # (Chest generation in fortresses is handled separately)
        
        # Carbine fields - groups of carrots with 10% chance
        if can_place_surface_item(x, ground_y) and world_rng.random() < 0.1:  # 10% chance for carbine field
            generate_carbine_field(x, ground_y, world_rng)
    
    # Find clean flat areas for village placement
    flat_areas = []
    for x in range(start_x - world_width//2, start_x + world_width//2):
        if get_block(x, 10) == "grass":  # Only on clean flat ground (Y=10)
            flat_areas.append(x)
    
    # Cave generation removed - caves are disabled
    
    # Generate villages (common and useful)
    village_count = 0
    for x in range(start_x - world_width//2, start_x + world_width//2):
        if get_block(x, 10) == "grass" and random.random() < 0.05:  # 5% chance for village
            generate_village(x, 10)
            village_count += 1
    
    if village_count > 0:
        print(f"🏘️ Generated {village_count} villages in the world!")
    
    # Generate beaches (common coastal areas)
    beach_count = 0
    for x in range(start_x - world_width//2, start_x + world_width//2):
        if get_block(x, 10) == "grass" and random.random() < 0.03:  # 3% chance for beach
            generate_beach(x, 10)
            beach_count += 1
    
    if beach_count > 0:
        print(f"🏖️ Generated {beach_count} beaches in the world!")
    
    # Fortress generation removed - will be replaced with cool structures
    print("🏗️ Structure generation disabled (fortresses removed)")
    
    # Generate Lost Ruins (very rare but important)
    ruins_count = 0
    for x in range(start_x - world_width//2, start_x + world_width//2):
        if get_block(x, 10) == "grass" and random.random() < 0.005:  # 0.5% chance for Lost Ruins
            generate_lost_ruins(x, 10)
            ruins_count += 1
    
    if ruins_count > 0:
        print(f"🏛️ Generated {ruins_count} Lost Ruins in the world!")
    
    # Villages removed from world generation
    
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
    
    # ENABLE STRICT VALIDATION TO ENFORCE SURFACE-ONLY RULE
    validate_and_fix_terrain()
    print("🔍 STRICT VALIDATION ENABLED: Enforcing surface-only rule!")
    
    return world_seed

def validate_and_fix_terrain():
    """ABSOLUTE VALIDATION: Grass and dirt NEVER underground, trees NEVER underground - NO EXCEPTIONS!"""
    global world_data
    
    print("🔍 STRICT VALIDATION: Enforcing surface-only rule...")
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
        
        # STEP 2: ABSOLUTE RULE - Dirt can NEVER be underground - NO EXCEPTIONS!
        # Remove ALL dirt that's deeper than 2 blocks below surface
        for y in range(surface_y + 3, 400):  # Check deep underground for misplaced dirt
            if get_block(x, y) == "dirt":
                # This dirt is underground - replace with stone immediately
                world_data.pop((x, y), None)
                set_block(x, y, "stone")
                fixes_applied += 1
                print(f"🚫 ABSOLUTE FIX: Removed underground dirt at ({x}, {y}) - replaced with stone - NEVER ALLOWED!")
        
        # Ensure dirt layer is complete (ONLY 2 blocks deep)
        for y in range(surface_y + 1, surface_y + 3):  # FIXED: Only 2 blocks deep
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
        
        # STEP 4: ABSOLUTE RULE - Trees (logs/leaves) can NEVER be underground - NO EXCEPTIONS!
        # Remove any logs or leaves that are at or below surface level
        for y in range(surface_y, 400):  # Check deep underground for misplaced tree parts
            if get_block(x, y) in ["log", "leaves"]:
                # This tree part is underground - remove it immediately
                old_block = get_block(x, y)
                world_data.pop((x, y), None)
                fixes_applied += 1
                print(f"🚫 ABSOLUTE FIX: Removed underground tree part at ({x}, {y}) - {old_block} - NEVER ALLOWED!")
        
        # STEP 5: Ensure bedrock at the bottom of the 200-block stone layer
        bedrock_y = surface_y + 200  # 200 blocks below surface
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
        
        # STEP 6: Remove any blocks below bedrock
        for y in range(bedrock_y + 1, bedrock_y + 100):  # Check a reasonable range below bedrock
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
    
    print("✅ ABSOLUTE VALIDATION COMPLETE: Rules ENFORCED - NO EXCEPTIONS!")
    print("🚫 ENFORCED: Grass NEVER underground - NO EXCEPTIONS!")
    print("🚫 ENFORCED: Dirt NEVER underground - NO EXCEPTIONS!")
    print("🚫 ENFORCED: Trees NEVER underground - NO EXCEPTIONS!")

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
    current_username = get_current_username()
    username_exists = current_username and current_username != "Player" and current_username.strip() != ""
    
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

def set_username(username):
    """Set the username and save to file"""
    global player, coins_manager
    player["username"] = username
    
    # Update coins manager with new username
    if coins_manager:
        try:
            coins_manager.set_username(username)
            print(f"💰 Updated coins manager username to: {username}")
        except Exception as e:
            print(f"❌ Failed to update coins manager username: {e}")
    
    # Save username to JSON file
    save_username_to_file(username)
    print(f"✅ Username updated to: {username}")

def load_username_from_file():
    """Load username from username.json file"""
    try:
        username_dir = os.path.join(SAVE_DIR, "username")
        username_file = os.path.join(username_dir, "username.json")
        
        if not os.path.exists(username_file):
            print("🔍 No username.json file found, using default")
            return "Player"
        
        with open(username_file, 'r') as f:
            username_data = json.load(f)
            username = username_data.get("username", "Player")
            
            if not username or username.strip() == "":
                print("🔍 Username.json is empty, using default")
                return "Player"
            
            print(f"✅ Username loaded from file: {username}")
            return username
            
    except Exception as e:
        print(f"⚠️ Error loading username from file: {e}")
        return "Player"

def get_current_username():
    """Get the current username (loads from file each time)"""
    return load_username_from_file()

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
    """Check if username is required (username.json file doesn't exist or is invalid)"""
    try:
        current_username = get_current_username()
        if not current_username or current_username.strip() == "" or current_username == "Player":
            print("🔍 Username check: No valid username found")
            return True
        
        print(f"✅ Username check: Valid username found: {current_username}")
        return False
            
    except Exception as e:
        print(f"⚠️ Username check: Error checking username: {e}")
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
                    set_username(username_input)
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
def draw_studio_loading_screen():
    """Draw the Team Banana Labs Studios loading screen with progress bar"""
    global loading_progress, loading_stage, studio_logo, loading_start_time
    
    # Load studio logo if not already loaded
    if studio_logo is None:
        try:
            logo_path = os.path.join(assets_root, "studio logo", "Banana labs logo copy.png")
            if os.path.exists(logo_path):
                studio_logo = pygame.image.load(logo_path).convert_alpha()
                # Scale logo to appropriate size
                studio_logo = pygame.transform.scale(studio_logo, (200, 200))
                print("✅ Studio logo loaded successfully")
            else:
                print("⚠️ Studio logo not found, using fallback")
                # Create a simple fallback logo
                studio_logo = pygame.Surface((200, 200), pygame.SRCALPHA)
                pygame.draw.circle(studio_logo, (255, 255, 0), (100, 100), 80)
                pygame.draw.circle(studio_logo, (0, 0, 0), (100, 100), 80, 5)
        except Exception as e:
            print(f"❌ Error loading studio logo: {e}")
            # Create a simple fallback logo
            studio_logo = pygame.Surface((200, 200), pygame.SRCALPHA)
            pygame.draw.circle(studio_logo, (255, 255, 0), (100, 100), 80)
            pygame.draw.circle(studio_logo, (0, 0, 0), (100, 100), 80, 5)
    
    # Clear screen with dark background
    screen.fill((20, 20, 40))
    
    # Draw studio logo (positioned to avoid text collision)
    if studio_logo:
        logo_x = SCREEN_WIDTH // 2 - studio_logo.get_width() // 2
        logo_y = SCREEN_HEIGHT // 2 - studio_logo.get_height() // 2 - 100  # Move up to avoid text
        screen.blit(studio_logo, (logo_x, logo_y))
    
    # Draw "Team Banana Labs Studios" text
    studio_text = title_font.render("Team Banana Labs Studios", True, (255, 255, 255))
    studio_rect = studio_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(studio_text, studio_rect)
    
    # Draw current loading stage
    current_stage_text = font.render(loading_stages[loading_stage], True, (200, 200, 200))
    stage_rect = current_stage_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    screen.blit(current_stage_text, stage_rect)
    
    # Draw progress bar background
    bar_width = 400
    bar_height = 20
    bar_x = SCREEN_WIDTH // 2 - bar_width // 2
    bar_y = SCREEN_HEIGHT // 2 + 130
    
    # Background
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 2)
    
    # Progress fill
    progress_width = int(bar_width * (loading_progress / 100))
    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, progress_width, bar_height))
    
    # Progress percentage text
    progress_text = font.render(f"{int(loading_progress)}%", True, (255, 255, 255))
    progress_rect = progress_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height + 20))
    screen.blit(progress_text, progress_rect)

def update_loading_progress():
    """Update the loading progress and handle stage transitions"""
    global loading_progress, loading_stage, game_state, loading_start_time
    
    current_time = pygame.time.get_ticks()
    
    # Initialize start time
    if loading_start_time == 0:
        loading_start_time = current_time
    
    # Calculate progress based on time elapsed
    elapsed_time = current_time - loading_start_time
    
    # Each stage takes 2 seconds (2000ms)
    stage_duration = 2000
    total_duration = len(loading_stages) * stage_duration
    
    # Calculate overall progress
    overall_progress = min(100, (elapsed_time / total_duration) * 100)
    
    # Calculate current stage
    current_stage = min(len(loading_stages) - 1, int(elapsed_time / stage_duration))
    
    # Update stage if changed
    if current_stage != loading_stage:
        loading_stage = current_stage
        print(f"🔄 Loading stage: {loading_stages[loading_stage]}")
    
    # Calculate progress within current stage
    stage_elapsed = elapsed_time % stage_duration
    stage_progress = min(100, (stage_elapsed / stage_duration) * 100)
    
    # Update loading progress
    loading_progress = overall_progress
    
    # Check if loading is complete
    if elapsed_time >= total_duration:
        print("✅ Loading complete! Moving to title screen")
        game_state = GameState.TITLE

def draw_title_screen():
    global play_btn, controls_btn, about_btn, options_btn, quit_btn, username_btn, credits_btn
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw modern title screen
    if modern_ui:
        button_states = modern_ui.draw_title_screen(mouse_pos)
        
        # Store button references for click handling
        play_btn = button_states.get("play")
        username_btn = button_states.get("username")
        controls_btn = button_states.get("controls")
        about_btn = button_states.get("about")
        options_btn = button_states.get("options")
        credits_btn = button_states.get("credits")
        quit_btn = button_states.get("quit")
    else:
        # Fallback: Draw basic title screen
        title_text = title_font.render("Order of the Stone", True, (255, 255, 255))
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # Create simple buttons
        button_y = 300
        button_spacing = 70
        button_width = 200
        button_height = 50
        
        play_btn = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, button_y, button_width, button_height)
        username_btn = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, button_y + button_spacing, button_width, button_height)
        controls_btn = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, button_y + button_spacing * 2, button_width, button_height)
        quit_btn = pygame.Rect(SCREEN_WIDTH // 2 - button_width // 2, button_y + button_spacing * 3, button_width, button_height)
        
        # Draw buttons
        pygame.draw.rect(screen, (100, 100, 100), play_btn)
        pygame.draw.rect(screen, (100, 100, 100), username_btn)
        pygame.draw.rect(screen, (100, 100, 100), controls_btn)
        pygame.draw.rect(screen, (100, 100, 100), quit_btn)
        
        # Draw button text
        play_text = font.render("Play", True, (255, 255, 255))
        username_text = font.render("Username", True, (255, 255, 255))
        controls_text = font.render("Controls", True, (255, 255, 255))
        quit_text = font.render("Quit", True, (255, 255, 255))
        
        screen.blit(play_text, (play_btn.centerx - play_text.get_width() // 2, play_btn.centery - play_text.get_height() // 2))
        screen.blit(username_text, (username_btn.centerx - username_text.get_width() // 2, username_btn.centery - username_text.get_height() // 2))
        screen.blit(controls_text, (controls_btn.centerx - controls_text.get_width() // 2, controls_btn.centery - controls_text.get_height() // 2))
        screen.blit(quit_text, (quit_btn.centerx - quit_text.get_width() // 2, quit_btn.centery - quit_text.get_height() // 2))
        
        about_btn = None
        options_btn = None
        credits_btn = None

# --- Credits Screen Drawing Function ---
def draw_credits_screen():
    """Draw the credits screen"""
    global credits_back_btn, credits_from_boss_defeat
    
    # Get mouse position for hover detection
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw modern credits screen
    button_states = modern_ui.draw_credits_screen(mouse_pos)
    
    # Store button references for click handling
    credits_back_btn = button_states.get("back")
    
    # Draw special completion message if credits are shown due to boss defeat
    if credits_from_boss_defeat:
        # Draw completion overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        
        # Draw completion message
        completion_text = font.render("🎉 CONGRATULATIONS! 🎉", True, (255, 215, 0))  # Gold color
        completion_rect = completion_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(completion_text, completion_rect)
        
        victory_text = font.render("You have defeated the Final Boss!", True, (255, 255, 255))
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, 130))
        screen.blit(victory_text, victory_rect)
        
        continue_text = font.render("Press ESC or click Back to return to your world", True, (200, 200, 200))
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, 160))
        screen.blit(continue_text, continue_rect)

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
    
    # Debug: Check if play button exists
    if world_play_btn is None:
        print("⚠️ Play World button is None!")
    else:
        print(f"✅ Play World button exists: {world_play_btn}")

# --- World Naming Screen Drawing Function ---
def draw_world_naming_screen():
    """Draw the world naming screen with keyboard input (NO mobile keyboard!)"""
    global world_name_input, world_name_cursor_pos, world_name_cursor_blink, world_seed_input
    global world_name_buttons, world_name_confirm_btn, world_name_cancel_btn, world_name_skip_btn
    
    # Update cursor blink
    world_name_cursor_blink += 1
    if world_name_cursor_blink > 60:  # Blink every second at 60 FPS
        world_name_cursor_blink = 0
    
    # Clear screen with dark background
    screen.fill((20, 20, 30))
    
    # Get screen dimensions
    screen_width, screen_height = screen.get_size()
    mouse_pos = pygame.mouse.get_pos()
    
    # Title
    title_font = pygame.font.Font(None, 48)
    title_text = title_font.render("Name Your World", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(screen_width // 2, 100))
    screen.blit(title_text, title_rect)
    
    # Subtitle
    subtitle_font = pygame.font.Font(None, 24)
    subtitle_text = subtitle_font.render("Enter a name for your new world (optional)", True, (180, 180, 180))
    subtitle_rect = subtitle_text.get_rect(center=(screen_width // 2, 140))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Input box
    input_box_width = 400
    input_box_height = 50
    input_box_x = (screen_width - input_box_width) // 2
    input_box_y = 200
    
    # Draw input box background
    pygame.draw.rect(screen, (40, 40, 50), (input_box_x, input_box_y, input_box_width, input_box_height))
    pygame.draw.rect(screen, (100, 100, 120), (input_box_x, input_box_y, input_box_width, input_box_height), 2)
    
    # Draw input text
    input_font = pygame.font.Font(None, 32)
    if world_name_input:
        input_text = input_font.render(world_name_input, True, (255, 255, 255))
        screen.blit(input_text, (input_box_x + 10, input_box_y + 10))
    
    # Draw cursor
    if world_name_cursor_blink < 30:  # Show cursor for half the blink cycle
        cursor_x = input_box_x + 10 + input_font.size(world_name_input[:world_name_cursor_pos])[0]
        pygame.draw.line(screen, (255, 255, 255), (cursor_x, input_box_y + 10), (cursor_x, input_box_y + 40), 2)
    
    # On-screen keyboard
    keyboard_y = 300
    keyboard_width = 600
    keyboard_x = (screen_width - keyboard_width) // 2
    
    # Keyboard layout
    keyboard_rows = [
        "1234567890",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm"
    ]
    
    key_width = 50
    key_height = 40
    key_spacing = 5
    
    world_name_buttons = {}
    
    for row_idx, row in enumerate(keyboard_rows):
        row_width = len(row) * (key_width + key_spacing) - key_spacing
        row_x = keyboard_x + (keyboard_width - row_width) // 2
        
        for col_idx, char in enumerate(row):
            key_x = row_x + col_idx * (key_width + key_spacing)
            key_y = keyboard_y + row_idx * (key_height + key_spacing)
            
            # Check if mouse is over this key
            key_rect = pygame.Rect(key_x, key_y, key_width, key_height)
            is_hovered = key_rect.collidepoint(mouse_pos)
            
            # Draw key
            key_color = (80, 80, 100) if is_hovered else (60, 60, 80)
            pygame.draw.rect(screen, key_color, key_rect)
            pygame.draw.rect(screen, (100, 100, 120), key_rect, 1)
            
            # Draw key text
            key_font = pygame.font.Font(None, 24)
            key_text = key_font.render(char.upper(), True, (255, 255, 255))
            key_text_rect = key_text.get_rect(center=key_rect.center)
            screen.blit(key_text, key_text_rect)
            
            # Store button reference
            world_name_buttons[char] = key_rect
    
    # Special keys
    special_keys_y = keyboard_y + len(keyboard_rows) * (key_height + key_spacing) + 20
    
    # Space bar
    space_width = 200
    space_x = keyboard_x + (keyboard_width - space_width) // 2
    space_rect = pygame.Rect(space_x, special_keys_y, space_width, key_height)
    is_space_hovered = space_rect.collidepoint(mouse_pos)
    
    space_color = (80, 80, 100) if is_space_hovered else (60, 60, 80)
    pygame.draw.rect(screen, space_color, space_rect)
    pygame.draw.rect(screen, (100, 100, 120), space_rect, 1)
    
    space_font = pygame.font.Font(None, 20)
    space_text = space_font.render("SPACE", True, (255, 255, 255))
    space_text_rect = space_text.get_rect(center=space_rect.center)
    screen.blit(space_text, space_text_rect)
    
    world_name_buttons[' '] = space_rect
    
    # Backspace
    backspace_width = 100
    backspace_x = space_x + space_width + 20
    backspace_rect = pygame.Rect(backspace_x, special_keys_y, backspace_width, key_height)
    is_backspace_hovered = backspace_rect.collidepoint(mouse_pos)
    
    backspace_color = (80, 80, 100) if is_backspace_hovered else (60, 60, 80)
    pygame.draw.rect(screen, backspace_color, backspace_rect)
    pygame.draw.rect(screen, (100, 100, 120), backspace_rect, 1)
    
    backspace_font = pygame.font.Font(None, 20)
    backspace_text = backspace_font.render("⌫", True, (255, 255, 255))
    backspace_text_rect = backspace_text.get_rect(center=backspace_rect.center)
    screen.blit(backspace_text, backspace_text_rect)
    
    world_name_buttons['backspace'] = backspace_rect
    
    # Action buttons
    button_y = special_keys_y + key_height + 40
    button_width = 120
    button_height = 50
    button_spacing = 20
    
    total_buttons_width = (button_width * 3) + (button_spacing * 2)
    buttons_start_x = (screen_width - total_buttons_width) // 2
    
    # Skip button (use default name)
    skip_rect = pygame.Rect(buttons_start_x, button_y, button_width, button_height)
    is_skip_hovered = skip_rect.collidepoint(mouse_pos)
    skip_color = (100, 100, 120) if is_skip_hovered else (80, 80, 100)
    pygame.draw.rect(screen, skip_color, skip_rect)
    pygame.draw.rect(screen, (120, 120, 140), skip_rect, 2)
    
    skip_font = pygame.font.Font(None, 24)
    skip_text = skip_font.render("Skip", True, (255, 255, 255))
    skip_text_rect = skip_text.get_rect(center=skip_rect.center)
    screen.blit(skip_text, skip_text_rect)
    world_name_skip_btn = skip_rect
    
    # Cancel button
    cancel_rect = pygame.Rect(buttons_start_x + button_width + button_spacing, button_y, button_width, button_height)
    is_cancel_hovered = cancel_rect.collidepoint(mouse_pos)
    cancel_color = (150, 80, 80) if is_cancel_hovered else (120, 60, 60)
    pygame.draw.rect(screen, cancel_color, cancel_rect)
    pygame.draw.rect(screen, (170, 100, 100), cancel_rect, 2)
    
    cancel_font = pygame.font.Font(None, 24)
    cancel_text = cancel_font.render("Cancel", True, (255, 255, 255))
    cancel_text_rect = cancel_text.get_rect(center=cancel_rect.center)
    screen.blit(cancel_text, cancel_text_rect)
    world_name_cancel_btn = cancel_rect
    
    # Create button
    create_rect = pygame.Rect(buttons_start_x + (button_width + button_spacing) * 2, button_y, button_width, button_height)
    is_create_hovered = create_rect.collidepoint(mouse_pos)
    create_color = (80, 150, 80) if is_create_hovered else (60, 120, 60)
    pygame.draw.rect(screen, create_color, create_rect)
    pygame.draw.rect(screen, (100, 170, 100), create_rect, 2)
    
    create_font = pygame.font.Font(None, 24)
    create_text = create_font.render("Create", True, (255, 255, 255))
    create_text_rect = create_text.get_rect(center=create_rect.center)
    screen.blit(create_text, create_text_rect)
    world_name_confirm_btn = create_rect
    
    # Instructions
    instructions_font = pygame.font.Font(None, 20)
    instructions_text = instructions_font.render("You can also use your physical keyboard to type", True, (150, 150, 150))
    instructions_rect = instructions_text.get_rect(center=(screen_width // 2, screen_height - 50))
    screen.blit(instructions_text, instructions_rect)

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
# Player animations are loaded automatically by PlayerAnimator

# Initialize animation system
def initialize_animation_system():
    """Initialize the proper animation system"""
    global player_animator
    
    # PlayerAnimator is already initialized globally
    print("🎬 Animation system using new PlayerAnimator")

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

def generate_chest_with_shopkeeper_loot(chest_x, chest_y, chest_type="village"):
    """Generate chest loot including rare shopkeeper blocks"""
    if not chest_system:
        return
    
    # Generate normal chest loot
    if hasattr(chest_system, 'generate_chest_loot'):
        chest_system.generate_chest_loot(chest_type)
    
    # Add rare shopkeeper block (1% chance)
    if random.random() < 0.01:  # 1% chance for shopkeeper block
        chest_inventory = chest_system.get_chest_inventory((chest_x, chest_y))
        if chest_inventory:
            # Find empty slot
            for i, slot in enumerate(chest_inventory):
                if slot is None:
                    chest_inventory[i] = {
                        "type": "shopkeeper",
                        "count": 1
                    }
                    print(f"🏪 RARE! Shopkeeper block found in chest at ({chest_x}, {chest_y})!")
                    break

# Print chest system information
print_chest_system_info()

# Enhanced save function with fallback system
def save_game():
    """Save current game state with robust fallback system"""
    try:
        # Try to use world system first
        if world_system and hasattr(world_system, 'current_world_name') and world_system.current_world_name:
            print(f"💾 Saving to world system: '{world_system.current_world_name}'")
            
            # Prepare save data
        save_data = {
            "name": world_system.current_world_name,
            "blocks": world_data.copy() if world_data else {},
            "entities": entities.copy() if entities else [],
            "player": player.copy() if player else {},
            "world_settings": {
                "time": time.time(),
                "day": is_day,
                "weather": "clear"
                },
                "monster_data": {
                    "total_monsters_killed": total_monsters_killed
                },
                "villages": villages,
                "chest_data": {
                    "chest_inventories": {f"{k[0]},{k[1]}": v for k, v in chest_system.chest_inventories.items()} if chest_system else {},
                    "player_placed_chests": [f"{k[0]},{k[1]}" for k in chest_system.player_placed_chests] if chest_system else []
                }
            }
            
            # Update world system with current data
        world_system.current_world_data = save_data
        
            # Save using world system
        if world_system.save_world():
            print(f"✅ Game saved successfully to world: {world_system.current_world_name}")
            print(f"   📊 Save statistics: {len(save_data['blocks'])} blocks, {len(save_data['entities'])} entities")
            return True
        else:
            print("⚠️ World system save failed, trying fallback...")
        
        # Fallback: Direct file save
        print("💾 Using fallback save system...")
        return save_game_fallback()
            
    except Exception as e:
        print(f"💥 Error in save_game: {e}")
        import traceback
        traceback.print_exc()
        return save_game_fallback()

def save_game_fallback():
    """Fallback save system that saves directly to files"""
    try:
        # Create save directory if it doesn't exist
        save_dir = "save_data"
        worlds_dir = os.path.join(save_dir, "worlds")
        os.makedirs(worlds_dir, exist_ok=True)
        
        # Generate world name if none exists
        world_name = getattr(world_system, 'current_world_name', None) if world_system else None
        if not world_name:
            world_name = f"World_{int(time.time())}"
            print(f"🌍 Generated world name: {world_name}")
        
        # Prepare save data
        save_data = {
            "name": world_name,
            "blocks": world_data.copy() if world_data else {},
            "entities": entities.copy() if entities else [],
            "player": player.copy() if player else {},
            "world_settings": {
                "time": time.time(),
                "day": is_day,
                "weather": "clear"
            },
            "monster_data": {
                "total_monsters_killed": total_monsters_killed
            },
            "chest_data": {
                "chest_inventories": {f"{k[0]},{k[1]}": v for k, v in chest_system.chest_inventories.items()} if chest_system else {},
                "player_placed_chests": [f"{k[0]},{k[1]}" for k in chest_system.player_placed_chests] if chest_system else []
            },
            "last_saved": time.time()
        }
        
        # Save to file
        world_file = os.path.join(worlds_dir, f"{world_name}.json")
        
        # Create backup
        backup_file = world_file + ".backup"
        if os.path.exists(world_file):
            try:
                shutil.copy2(world_file, backup_file)
            except:
                pass
        
        # Save with proper formatting
        with open(world_file, 'w') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        # Remove backup if save was successful
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
            except:
                pass
        
        print(f"✅ Fallback save successful: {world_name}")
        print(f"   📊 Saved: {len(save_data['blocks'])} blocks, {len(save_data['entities'])} entities")
        return True
        
    except Exception as e:
        print(f"💥 Fallback save failed: {e}")
        return False

# Old crafting system functions removed - using new simplified system above

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

# Old crafting recipes removed - using new simplified system above

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
        
        # Generate a truly random seed for this world
        import time
        world_seed = int(time.time() * 1000) % 1000000  # Use timestamp for unique seeds
        print(f"🎲 Generated random world seed: {world_seed}")
        
        # Generate world using the new system with random seed
        world_info = generate_world(seed=world_seed, world_width=200)
        
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
        
        # Place a guaranteed starter chest near the player spawn
        place_starter_chest()
        
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
    from ui.modern_ui import ModernUI
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
    from ui.world_ui import WorldUI
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
game_state = GameState.STUDIO_LOADING  # Start with studio loading screen

# Studio loading screen variables
loading_progress = 0
loading_stage = 0  # 0 = assets, 1 = sounds, 2 = logic
loading_stages = ["Loading Assets...", "Loading Sounds...", "Loading Logic..."]
studio_logo = None
loading_start_time = 0
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
AUTO_SAVE_INTERVAL = 60  # 1 minute (more frequent saves)

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
    
    # Initialize clouds on first frame
    if frame_count == 1:
        generate_clouds()
        print("☁️ Clouds initialized")
    
    # Update clouds every frame
    update_clouds()
    
    # Update weather system
    update_weather()
    
    # Safety check: if we've been running for more than 10 seconds without user input, allow force quit
    if frame_count % 600 == 0:  # Check every 600 frames (about 10 seconds at 60 FPS)
        current_time = time.time()
        if current_time - start_time > 10:
            start_time = current_time  # Reset timer
    # Draw beautiful sky with clouds and mountains
    if is_day:
        draw_sky_background()
    else:
        screen.fill((0, 0, 0))  # Night sky



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
            # Handle shift key press
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                shift_key_pressed = True
            
            if event.key == pygame.K_ESCAPE:
                if merchant_shop_open:
                    # Close merchant shop if it's open
                    close_merchant_shop()
                    print("🏪 Merchant shop closed")
                elif map_open:
                    # Close map if it's open
                    map_open = False
                    print("🗺️ Map closed")
                elif game_state == GameState.GAME:
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
                elif game_state == GameState.BACKPACK:
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when closing inventory
                elif game_state == GameState.CREDITS:
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when returning to game
                    credits_from_boss_defeat = False  # Reset the flag
                    print("🎮 Returned to game from credits screen!")
            
            # Map toggle with M key
            if event.key == pygame.K_m:
                if game_state == GameState.GAME:
                    map_open = not map_open
                    if map_open:
                        print("🗺️ Map opened")
                        # Initialize map surface if needed
                        if map_surface is None:
                            init_map_surface()
                    else:
                        print("🗺️ Map closed")
            # Toggle fullscreen on F11
            if event.key == pygame.K_F11:
                FULLSCREEN = not FULLSCREEN
                apply_display_mode()
                update_chest_ui_geometry()
            
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
            # Toggle performance stats with F3
            if event.key == pygame.K_F3:
                performance_monitor["show_stats"] = not performance_monitor["show_stats"]
                print(f"📊 Performance stats {'enabled' if performance_monitor['show_stats'] else 'disabled'}")
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
            
            # T key now opens inventory instead of chat
            
            # Toggle chat with C key (alternative)
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
            
            # Open/Close backpack with I key
            if event.key == pygame.K_i:
                if game_state == GameState.GAME:
                    game_state = GameState.BACKPACK
                    update_pause_state()  # Pause time when opening backpack
                elif game_state == GameState.BACKPACK:
                    game_state = GameState.GAME
                    update_pause_state()  # Resume time when closing backpack
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
                        set_username(username_input)
                        game_state = GameState.TITLE
                        update_pause_state()  # Resume time when returning to title
                    else:
                        show_username_error(message)
                        print(f"❌ {message}")
                elif event.key == pygame.K_ESCAPE:
                    game_state = GameState.TITLE
                    update_pause_state()  # Pause time when returning to title
            
            # World creation handling removed - game goes directly to play
            
            # Jump handling moved to update_player function for enhanced charging system
            if pygame.K_1 <= event.key <= pygame.K_9:
                player["selected"] = event.key - pygame.K_1
            
        elif event.type == pygame.KEYUP:
            # Handle shift key release
            if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                shift_key_pressed = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == GameState.GAME:
                mx, my = event.pos  # Define mx, my once for all mouse handling
                
                # Handle merchant shop clicks first
                if handle_merchant_shop_click(mx, my):
                    continue
                
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
                            # Check if clicking on food or special items
                            if slot < len(player["inventory"]):
                                it = player["inventory"][slot]
                                if it and isinstance(it, dict):
                                    item_type = it.get("type")
                                    # Try to eat any food item
                                    if item_type in FOOD_ITEMS:
                                        if eat_food(item_type):
                                            # Remove one from stack or delete item
                                            if "count" in it and it["count"] > 1:
                                                it["count"] -= 1
                                            else:
                                                # Remove the item completely
                                                player["inventory"][slot] = None
                                            # Normalize inventory to clean up None entries
                                            normalize_inventory()
                                    elif item_type == "map":
                                        use_map_from_inventory()
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
                    
                    # Check if clicking on a shopkeeper block
                    elif block_at_pos == "shopkeeper":
                        # Check if player is within range
                        px, py = int(player["x"]), int(player["y"])
                        if abs(bx - px) <= 2 and abs(by - py) <= 2:
                            open_merchant_shop((bx, by))
                            print(f"🏪 Opening merchant shop at ({bx}, {by})")
                        else:
                            print(f"🏪 Merchant too far away: player at ({px}, {py}), merchant at ({bx}, {by})")
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
                    # Bed interaction: sleep at night, set spawn point at day
                    if get_block(bx, by) == "bed":
                        if not is_day:
                            # Sleep at night
                            sleep_in_bed()
                        else:
                            # Set spawn point during day
                            player["spawn_x"] = bx
                            player["spawn_y"] = by
                            player["has_bed_spawn"] = True
                            show_message(f"🏠 Spawn point set at ({bx}, {by})", 2000)
                            print(f"🏠 Bed spawn point set at ({bx}, {by})")
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
                    
                    # Legend NPC interaction removed - no more random NPCs
                    # Villager interaction removed - no more random NPCs
                        # Shopkeeper interaction removed - now available in title screen
                    
                    
                    # If selected carrot, eat it; if map, use it; otherwise place block
                    if player["selected"] < len(player["inventory"]) and player["inventory"][player["selected"]]:
                        selected_item = player["inventory"][player["selected"]]
                        if selected_item["type"] == "carrot":
                            consume_carrot_from_inventory()
                        elif selected_item["type"] == "map":
                            use_map_from_inventory()
                        else:
                            # Try to place the block
                            place_block(bx, by)
            elif game_state == GameState.TITLE:
                if play_btn.collidepoint(event.pos):
                    # Check if username is required before allowing play
                    if require_username_check():
                        # Don't use continue here - just skip the rest of the button logic
                        pass
                    
                    # Go to world selection screen instead of directly loading game
                    game_state = GameState.WORLD_SELECTION
                    update_pause_state()  # Pause time when leaving title
                    print("🌍 Opening world selection screen!")
                elif username_btn.collidepoint(event.pos):
                    # If changing username, save the current one first
                    current_username = get_current_username()
                    if current_username and current_username != "Player":
                        save_username_to_file(current_username)
                        print(f"💾 Current username saved before change: {current_username}")
                    game_state = GameState.USERNAME_CREATE
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
                elif credits_btn.collidepoint(event.pos):
                    game_state = GameState.CREDITS
                    update_pause_state()  # Pause time when leaving title
                elif quit_btn.collidepoint(event.pos):
                    save_game()
                    running = False
            elif game_state == GameState.WORLD_SELECTION:
                # Handle world selection screen clicks using the world UI system
                print(f"🔍 World selection click at: {event.pos}")
                
                # Use the world UI's button handling system
                # First, check if user clicked on a world to select it
                world_click_result = world_ui.handle_world_click(event.pos)
                if world_click_result is not None:
                    print(f"🌍 World {world_click_result} selected or deselected!")
                    # World was clicked - don't process button clicks
                    continue  # Skip button handling since we just selected/deselected a world
                
                # Now handle button clicks using the world UI's button handling system
                # We need to pass the button states to the world UI's handle_mouse_click method
                # But first, let's get the current button states
                button_states = {
                    "play_world": world_play_btn,
                    "delete_world": world_delete_btn,
                    "create_world": world_create_btn,
                    "back": world_back_btn
                }
                
                # Use the world UI's button handling system
                action = world_ui.handle_world_selection_click(button_states, event.pos)
                
                # Get the selected world from world_ui
                selected_world = world_ui.get_selected_world()
                world_name = selected_world["name"] if selected_world else None
                new_selection = None
                
                # Debug output
                print(f"📊 Action: {action}, World name: {world_name}, Selected world: {selected_world}")
                
                # Handle the action returned by the world UI system
                if action == "play_world":
                    print("🎮 Play World button clicked!")
                    # EXTREME ENGINEERING: Username validation before world play
                    if require_username_check():
                        print("🚫 Username required before playing - redirecting to username creation")
                    else:
                        if world_name:
                            print(f"🌍 Loading world: {world_name}")
                            if world_system.load_world(world_name):
                                # Load the world data into the game
                                if load_world_data():
                                    # Fix player spawn position to ensure surface spawning
                                    fix_player_spawn_position()
                                    # Start world generation instead of going directly to game
                                    start_world_generation()
                                    game_state = GameState.WORLD_GENERATION
                                    update_pause_state()  # Resume time when entering world generation
                                    print(f"🌍 Starting world generation for world: {world_name}")
                                    print("🎮 Controls: WASD or Arrow Keys = Move + Flip Character, Space = Jump")
                                else:
                                    print(f"❌ Failed to load world data for: {world_name}")
                            else:
                                print(f"❌ Failed to load world: {world_name}")
                        else:
                            print("❌ No world selected - please select a world first")
                            show_message("Please select a world first!", 2000)
                elif action == "delete_world":
                    print("🗑️ Delete World button clicked!")
                    if world_name:
                        if world_system.delete_world(world_name):
                            print(f"🗑️ Deleted world: {world_name}")
                            # Refresh world selection state
                            world_ui.refresh_world_selection()
                        else:
                            print(f"❌ Failed to delete world: {world_name}")
                    else:
                        print("❌ No world selected - please select a world first")
                        show_message("Please select a world first!", 2000)
                elif action == "create_world":
                    print("✨ Create World button clicked!")
                    # EXTREME ENGINEERING: Username validation before world creation
                    if require_username_check():
                        print("🚫 Username required before creating world - redirecting to username creation")
                    else:
                        # Go to world naming screen instead of directly creating world
                        game_state = GameState.WORLD_NAMING
                        update_pause_state()  # Pause time when entering world naming
                        print("🌍 Opening world naming screen!")
                elif action == "back":
                    print("⬅️ Back button clicked!")
                    game_state = GameState.TITLE
                    update_pause_state()  # Resume time when returning to title
                    print("⬅️ Returning to title screen from world selection")
                elif action == "page_changed":
                    print("📄 Page changed!")
                elif action is None:
                    print("🔍 No button clicked")
            elif game_state == GameState.WORLD_NAMING:
                # Handle world naming screen events
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        # Check on-screen keyboard buttons
                        for char, button_rect in world_name_buttons.items():
                            if button_rect.collidepoint(event.pos):
                                if char == 'backspace':
                                    # Handle backspace
                                    if world_name_input and world_name_cursor_pos > 0:
                                        world_name_input = world_name_input[:world_name_cursor_pos-1] + world_name_input[world_name_cursor_pos:]
                                        world_name_cursor_pos -= 1
                                else:
                                    # Add character at cursor position
                                    world_name_input = world_name_input[:world_name_cursor_pos] + char + world_name_input[world_name_cursor_pos:]
                                    world_name_cursor_pos += 1
                                break
                        
                        # Check action buttons
                        if world_name_skip_btn and world_name_skip_btn.collidepoint(event.pos):
                            # Skip naming - use default name
                            create_world_with_name("")
                        elif world_name_cancel_btn and world_name_cancel_btn.collidepoint(event.pos):
                            # Cancel - go back to world selection
                            game_state = GameState.WORLD_SELECTION
                            update_pause_state()
                            print("⬅️ Cancelled world naming, returning to world selection")
                        elif world_name_confirm_btn and world_name_confirm_btn.collidepoint(event.pos):
                            # Create world with entered name
                            create_world_with_name(world_name_input.strip())
                
                elif event.type == pygame.KEYDOWN:
                    # Handle physical keyboard input
                    if event.key == pygame.K_BACKSPACE:
                        # Handle backspace
                        if world_name_input and world_name_cursor_pos > 0:
                            world_name_input = world_name_input[:world_name_cursor_pos-1] + world_name_input[world_name_cursor_pos:]
                            world_name_cursor_pos -= 1
                    elif event.key == pygame.K_DELETE:
                        # Handle delete
                        if world_name_cursor_pos < len(world_name_input):
                            world_name_input = world_name_input[:world_name_cursor_pos] + world_name_input[world_name_cursor_pos+1:]
                    elif event.key == pygame.K_LEFT:
                        # Move cursor left
                        if world_name_cursor_pos > 0:
                            world_name_cursor_pos -= 1
                    elif event.key == pygame.K_RIGHT:
                        # Move cursor right
                        if world_name_cursor_pos < len(world_name_input):
                            world_name_cursor_pos += 1
                    elif event.key == pygame.K_HOME:
                        # Move cursor to beginning
                        world_name_cursor_pos = 0
                    elif event.key == pygame.K_END:
                        # Move cursor to end
                        world_name_cursor_pos = len(world_name_input)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # Create world with entered name
                        create_world_with_name(world_name_input.strip())
                    elif event.key == pygame.K_ESCAPE:
                        # Cancel - go back to world selection
                        game_state = GameState.WORLD_SELECTION
                        update_pause_state()
                        print("⬅️ Cancelled world naming, returning to world selection")
                    elif event.unicode and event.unicode.isprintable() and len(world_name_input) < 32:
                        # Add printable character at cursor position
                        world_name_input = world_name_input[:world_name_cursor_pos] + event.unicode + world_name_input[world_name_cursor_pos:]
                        world_name_cursor_pos += 1
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
                        set_username(username_input)
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
            elif game_state == GameState.CREDITS:
                if credits_back_btn.collidepoint(event.pos):
                    game_state = GameState.TITLE
                    update_pause_state()  # Pause time when returning to title
                    credits_from_boss_defeat = False  # Reset the flag
                    print("🎮 Returned to title screen from credits!")
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
                        game_state = GameState.TITLE
                        update_pause_state()
                        print("⬅️ Returning to title screen from multiplayer host")
                
                elif multiplayer_menu_state == "join":
                    if multiplayer_search_btn and multiplayer_search_btn.collidepoint(event.pos):
                        # Search for available servers
                        discover_servers()
                        multiplayer_menu_state = "server_list"
                        show_message("🔍 Searching for servers...", 2000)
                        print("🔍 Server search initiated")
                    elif multiplayer_join_back_btn and multiplayer_join_back_btn.collidepoint(event.pos):
                        game_state = GameState.TITLE
                        update_pause_state()
                        print("⬅️ Returning to title screen from multiplayer join")
                
                elif multiplayer_menu_state == "server_list":
                    if multiplayer_server_list_back_btn and multiplayer_server_list_back_btn.collidepoint(event.pos):
                        game_state = GameState.TITLE
                        update_pause_state()
                        print("⬅️ Returning to title screen from server list")
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
            elif game_state == GameState.BACKPACK:
                # Handle backpack clicks
                if event.button == 3:  # RIGHT CLICK - Eat food
                    handle_inventory_right_click(event.pos)
                else:
                    handle_backpack_click(event.pos)
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
            # Mouse wheel scrolling removed - now using View All button instead
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
            # Generate structures for chunk - DISABLED (fortress system removed)
            # maybe_generate_fortress_for_chunk(ch, base_x)
        for x in range(left_edge, right_edge):
            # CRITICAL FIX: Only generate terrain for columns that have NEVER been generated
            # This prevents broken blocks from being replaced by terrain regeneration
            # Use the centralized terrain generation function for consistency
            if x not in generated_terrain_columns:
                # Show exploration progress every 50 blocks for infinite world feedback
                if x % 50 == 0:
                    print(f"🚀 INFINITE WORLD: Exploring new territory at X={x}")
                
                # Use the improved terrain generation function (handles terrain, trees, ores, etc.)
                generate_terrain_column(x)
                # Replace dirt/stone blocks adjacent to water with sand for natural beaches
                # EXTREME ENGINEERING: Balanced night monster spawning
                # Only spawn monsters at night when exploring new territory
                if not is_day and random.random() < 0.008:  # Slightly increased spawn rate for better gameplay
                    # Check total monster count globally to prevent overcrowding
                    total_monsters = sum(1 for entity in entities if entity["type"] in ["monster", "zombie"])
                    
                    # Check if there are already monsters nearby to prevent clustering
                    nearby_monsters = 0
                    for entity in entities:
                        if entity["type"] in ["monster", "zombie"]:
                            distance = abs(entity["x"] - x)
                            if distance < 40:  # Within 40 blocks
                                nearby_monsters += 1
                    
                    # Balanced spawning: max 8 total monsters, max 1 per 40-block radius
                    if total_monsters < 8 and nearby_monsters == 0:
                        # Find surface level for this column (spawn ON surface, not underground)
                        spawn_surface_y = find_surface_level(x)
                        if spawn_surface_y is not None:
                            # Randomly choose between monster and zombie (30% chance for zombie)
                            if random.random() < 0.3:  # 30% chance for zombie
                                monster_type = "zombie"
                                monster_hp = 10  # Zombies are stronger
                                monster_img = textures["zombie"]  # Use original zombie texture
                            else:
                                monster_type = "monster"
                                monster_hp = 6
                                monster_img = textures["monster"]  # Use original monster texture
                            
                            entities.append({
                                "type": monster_type,
                                "x": x,
                                "y": spawn_surface_y,  # Spawn ON the surface
                                "image": monster_img,
                                "hp": monster_hp,
                                "cooldown": 0
                            })
                            print(f"👹 Night {monster_type} spawned at ({x}, {spawn_surface_y}) - Total monsters: {total_monsters + 1}/8")
                
        # NPC spawning systems removed - no more random NPCs

        # OPTIMIZED: Update performance monitoring
        update_performance_monitor()

        update_daylight()
        update_player()
        update_falling_blocks()  # Update sand physics
        update_water_flow()  # Update water flow
        update_world_interactions()
        update_monsters()
        update_villagers()
        # update_fortress_bosses()  # REMOVED - fortress system disabled
        update_oxygen_system()  # Update oxygen system
        update_night_overlay()  # Update nighttime visual effects
        update_pickaxe_animation()
        update_final_boss()  # Update final boss AI
        update_boss()  # EXTREME ENGINEERING: Legendary boss AI and attacks
        update_hunger()  # Update hunger system
        update_thrown_sword()  # Update sword throwing system
        update_thrown_sword_entities()  # Update thrown sword entities
        update_blood_particles()  # Update blood particle effects
        update_block_particles()  # Update block breaking particle effects
        update_fireball_projectiles()  # Update fireball projectiles
        # update_light_sources()  # DISABLED - lighting system disabled
        
        # Ability system removed
        
        # Fallback: Reset shift key state if it gets stuck (safety mechanism)
        # This prevents the player from getting permanently stuck in slow mode
        if shift_key_pressed:
            keys = pygame.key.get_pressed()
            if not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
                shift_key_pressed = False
        
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
        # draw_darkness_overlay()  # DISABLED - caused glitches
        draw_map()  # Draw the map overlay if it's open
        draw_inventory()
        draw_status_bars()
        draw_monster_health_bars()  # Show health bars for hit monsters
        draw_boss_health_bar()  # EXTREME ENGINEERING: Legendary boss health bar
        draw_fortress_discovery()  # EXTREME ENGINEERING: Big animated fortress discovery
        draw_fortress_minimap()  # EXTREME ENGINEERING: Fortress minimap in corner
        draw_multiplayer_chat()  # EXTREME ENGINEERING: Multiplayer chat interface
        
        # Portal and boss systems removed - using ability system instead
        
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
        
        if chest_open:
            draw_chest_ui()
        
        # Draw merchant shop UI if open
        draw_merchant_shop_ui()
        
        # Draw performance stats if enabled
        draw_performance_stats()

        if player["health"] <= 0:
            show_death_screen()
    elif game_state == GameState.STUDIO_LOADING:
        update_loading_progress()
        draw_studio_loading_screen()
    elif game_state == GameState.TITLE:
        draw_title_screen()
    elif game_state == GameState.WORLD_SELECTION:
        draw_world_selection_screen()
    elif game_state == GameState.WORLD_NAMING:
        draw_world_naming_screen()
    elif game_state == GameState.WORLD_GENERATION:
        update_world_generation()
        draw_world_generation_screen()
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
    elif game_state == GameState.BACKPACK:
        draw_backpack_ui()
    elif game_state == GameState.SKIN_CREATOR:
        draw_skin_creator_ui()
    elif game_state == GameState.MULTIPLAYER:
        draw_multiplayer_screen()
    elif game_state == GameState.CREDITS:
        draw_credits_screen()

    # Draw nighttime overlay effect
    draw_night_overlay()
    
    # Draw oxygen bar when underwater
    draw_oxygen_bar()

    pygame.display.flip()
    
    # Consistent frame-rate limiting for smooth, predictable movement
    target_fps = 60  # Lock to 60 FPS for consistent timing
    clock.tick(target_fps)
    
    # Update player animation
    if game_state == GameState.GAME:
        update_player_animation()
    
    # Update all GIF animations
    # Player animations are handled by PlayerAnimator automatically
    
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

# Cleanup and exit
print("🔄 Game loop ended, cleaning up...")

# Force cleanup of any remaining resources
try:
    # Save username before quitting
    current_username = get_current_username()
    if current_username and current_username != "Player":
        try:
            save_username_to_file(current_username)
            print(f"💾 Username saved before exit: {current_username}")
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
