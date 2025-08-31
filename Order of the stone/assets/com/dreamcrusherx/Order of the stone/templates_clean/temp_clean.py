import pygame
import random
import os
import time
import json
import shutil
import sys
import math
import signal
import copy
import traceback
import logging
import threading
import socket
import pickle
import struct
import select
import hashlib
import uuid
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import weakref

# Ensure the game runs from the correct directory (where the game files are located)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

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
# ANIMATION SYSTEM
# =============================================================================
class Animation:
    """Base animation class for smooth player animations"""
    
    def __init__(self, frames, speed=0.1):
        self.frames = frames  # List of textures for animation
        self.speed = speed    # Animation speed (frames per second)
        self.current_frame = 0
        self.timer = 0
        self.looping = True
    
    def update(self, dt):
        """Update animation frame"""
        self.timer += dt
        if self.timer >= self.speed:
            self.timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def get_current_frame(self):
        """Get current animation frame"""
        return self.frames[self.current_frame]
    
    def reset(self):
        """Reset animation to first frame"""
        self.current_frame = 0
        self.timer = 0

# PlayerAnimator class moved to new_animation_system.py
    
# All animation methods moved to new_animation_system.py
    
# create_fallback_animation method moved to new_animation_system.py
    
    def update(self, dt, player_state):
        """Update current animation based on player state"""
# All old animation methods removed - using new system

# Create a properly engineered animation system
class ProperAnimation:
    """Properly engineered animation class with frame-based timing"""
    
    def __init__(self, frames, frame_duration=0.1):
        if not frames:
            raise ValueError("Animation requires at least one frame")
        
        self.frames = frames
        self.frame_duration = frame_duration
        self.current_frame_index = 0
        self.elapsed_time = 0.0
        self.is_playing = True
    
    def update(self, delta_time):
        """Update animation based on actual time"""
        if not self.is_playing or len(self.frames) <= 1:
            return
        
        self.elapsed_time += delta_time
        
        if self.elapsed_time >= self.frame_duration:
            self.elapsed_time = 0.0
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
    
    def get_current_frame(self):
        """Get current frame with bounds checking"""
        if not self.frames:
            return None
        
        # Safety check: ensure frame index is within bounds
        if self.current_frame_index >= len(self.frames):
            print(f"⚠️ Frame index {self.current_frame_index} out of bounds, resetting to 0")
            self.current_frame_index = 0
        
        if self.current_frame_index < 0:
            print(f"⚠️ Frame index {self.current_frame_index} negative, resetting to 0")
            self.current_frame_index = 0
        
        return self.frames[self.current_frame_index]
    
    def reset(self):
        """Reset animation to beginning"""
        self.current_frame_index = 0
        self.elapsed_time = 0.0
    
    def get_frame_count(self):
        """Get total frame count"""
        return len(self.frames)

# =============================================================================
# CHARACTER FLIPPING SYSTEM FEATURES:
# 
# 1. INPUT HANDLING:
#    - A key (or LEFT arrow): Character faces left
#    - D key (or RIGHT arrow): Character faces right
#    - Facing direction persists when no keys are pressed
#    - Smooth transitions between directions
# 
# 2. VISUAL CONSISTENCY:
#    - Player sprite automatically flips horizontally
#    - Held items reposition based on facing direction
#    - Armor pieces flip to maintain visual consistency
#    - Procedural armor rendering respects facing direction
# 
# 3. PERFORMANCE OPTIMIZATION:
#    - Texture caching system prevents repeated transformations
#    - Cache size limited to 100 textures to prevent memory issues
#    - Automatic cache management and cleanup methods
# 
# 4. ENGINEERING BEST PRACTICES:
#    - Separation of concerns (input, state, rendering)
#    - Error handling and logging
#    - Memory management with texture caching
#    - Debug information and testing functions
#    - Consistent API design
# 
# 5. DEBUG FEATURES:
#    - FPS display shows current animation and facing direction
#    - Texture cache information display
#    - Logging of direction changes
#    - System testing and validation
# =============================================================================

class ProperPlayerAnimator:
    """Properly engineered player animation manager with advanced character flipping system"""
    
    def __init__(self):
        self.animations = {}
        self.current_animation_name = "idle"
        self.facing_right = True
        self.last_position = None
        self.movement_threshold = 0.05
        
        # ENGINEERING: Setup animations immediately to protect your custom animations
        self.setup_animations()
        
    def setup_animations(self):
        """Initialize all animations with proper error handling"""
        print("🎬 Setting up PROPER animation system...")
        
        try:
            # Load custom GIF animations
            self._load_custom_animations()
            
            # ENGINEERING: Fallback system permanently disabled to protect your custom animations
            # self._create_fallback_animations()  # REMOVED - Your animations are now protected!
            
            print(f"✅ Animation system ready: {len(self.animations)} animations loaded")
            
            # ENGINEERING: Verify that your custom animations are protected
            self.verify_custom_animations()
            
        except Exception as e:
            print(f"❌ Failed to setup animations: {e}")
            # ENGINEERING: Emergency animations also disabled to protect your custom animations
            # self._create_emergency_animations()  # REMOVED - Your animations are now protected!
    
    def _load_custom_animations(self):
        """Load custom GIF animations with proper error handling"""
        animation_paths = {
            "idle": "../../../../player/animations/standing.gif",
            "walking": "../../../../player/animations/walking.gif",
            "jump": "../../../../player/animations/jumping.gif",
            "fall": "../../../../player/animations/falling.gif",
            "attack": "../../../../player/animations/fighting.gif",
            "breaking": "../../../../player/animations/breaking.gif",
            "placing": "../../../../player/animations/placing.gif"
        }
        
        for anim_name, gif_path in animation_paths.items():
            if os.path.exists(gif_path):
                try:
                    frames = self._load_gif_frames(gif_path)
                    if frames:
                        self.animations[anim_name] = ProperAnimation(frames, 0.2)
                        print(f"✅ Loaded custom {anim_name} animation: {len(frames)} frames from {gif_path}")
                    else:
                        print(f"⚠️ Failed to load {anim_name} from {gif_path}")
                except Exception as e:
                    print(f"⚠️ Error loading {anim_name}: {e}")
            else:
                print(f"📁 Custom {anim_name} animation not found: {gif_path}")
    
    def _load_gif_frames(self, gif_path):
        """Load GIF frames with proper error handling"""
        try:
            import PIL
            from PIL import Image
            
            frames = []
            with Image.open(gif_path) as gif:
                for frame_index in range(gif.n_frames):
                    gif.seek(frame_index)
                    
                    # Convert PIL image to pygame surface with proper size handling
                    try:
                        # First try RGBA
                        frame_data = gif.convert("RGBA").tobytes()
                        frame_size = gif.size
                        frame_surface = pygame.image.fromstring(frame_data, frame_size, "RGBA")
                    except pygame.error:
                        # Fallback: convert to RGB if RGBA fails
                        frame_data = gif.convert("RGB").tobytes()
                        frame_surface = pygame.image.fromstring(frame_data, frame_size, "RGB")
                    
                    # Scale to 32x32
                    if frame_surface.get_size() != (32, 32):
                        frame_surface = pygame.transform.scale(frame_surface, (32, 32))
                    
                    frames.append(frame_surface)
            
            return frames
            
        except ImportError:
            print("⚠️ PIL not available, using fallback")
            return None
        except Exception as e:
            print(f"⚠️ GIF loading failed: {e}")
            return None
    
    def _create_fallback_animations(self):
        """PERMANENTLY DISABLED - Only use custom animations to prevent loss"""
        print("🛡️ FALLBACK SYSTEM PERMANENTLY DISABLED - Your custom animations are protected!")
        print("🎬 Only custom animations will be used - no fallbacks will override them")
        
        # ENGINEERING: CRITICAL - This method is now completely disabled
        # Your custom animations will NEVER be overridden again
        return
    
    def _create_fallback_frames(self, color, frame_count, anim_type):
        """Create fallback animation frames"""
        frames = []
        
        for i in range(frame_count):
            surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            
            # Base body - make it asymmetrical so flipping is obvious
            pygame.draw.rect(surface, color, (8, 4, 16, 20))
            pygame.draw.circle(surface, (255, 220, 180), (16, 12), 6)  # Head
            
            # Add asymmetrical details to make flipping obvious
            if anim_type == "idle" or anim_type == "walking":
                # Left arm (will be on right when flipped) - Blue arm
                pygame.draw.rect(surface, (100, 150, 255), (6, 8, 4, 8))
                # Right arm (will be on left when flipped) - Green arm
                pygame.draw.rect(surface, (100, 255, 100), (22, 8, 4, 8))
                # Left eye (will be on right when flipped) - Blue eye
                pygame.draw.circle(surface, (0, 0, 255), (13, 10), 2)
                # Right eye (will be on left when flipped) - Green eye
                pygame.draw.circle(surface, (0, 255, 0), (19, 10), 2)
                # Left foot (will be on right when flipped) - Blue foot
                pygame.draw.rect(surface, (100, 150, 255), (10, 24, 4, 8))
                # Right foot (will be on left when flipped) - Green foot
                pygame.draw.rect(surface, (100, 255, 100), (18, 24, 4, 8))
            
            # Animation-specific details
            if anim_type == "walking":
                # Walking motion - arms and legs move in alternating pattern
                arm_swing = (i % 2) * 2  # Arms swing up/down
                leg_swing = ((i + 1) % 2) * 2  # Legs swing opposite to arms
                
                # Animate arms
                pygame.draw.rect(surface, (100, 150, 255), (6, 8 + arm_swing, 4, 8))  # Left arm
                pygame.draw.rect(surface, (100, 255, 100), (22, 8 - arm_swing, 4, 8))  # Right arm
                
                # Animate feet
                pygame.draw.rect(surface, (100, 150, 255), (10, 24 + leg_swing, 4, 8))  # Left foot
                pygame.draw.rect(surface, (100, 255, 100), (18, 24 - leg_swing, 4, 8))  # Right foot
                
            elif anim_type == "idle":
                # Idle animation - subtle breathing motion
                breath_offset = (i % 2) * 1  # Subtle up/down movement
                pygame.draw.rect(surface, (100, 150, 255), (6, 8 + breath_offset, 4, 8))  # Left arm
                pygame.draw.rect(surface, (100, 255, 100), (22, 8 + breath_offset, 4, 8))  # Right arm
                
            elif anim_type == "jump":
                # Jumping motion
                if i > 0:
                    pygame.draw.rect(surface, (200, 150, 50), (6, 6, 4, 6))
                    pygame.draw.rect(surface, (200, 150, 50), (22, 6, 4, 6))
            
            frames.append(surface)
        
        return frames
    
    def _create_emergency_animations(self):
        """Create emergency animations if everything else fails"""
        print("🚨 Creating emergency animations...")
        
        # Create emergency animations with basic shapes and colors
        for anim_name in ["idle", "walking", "jump", "fall", "attack", "breaking", "placing"]:
            emergency_surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            
            # Different colors for different animation types
            if anim_name == "idle":
                color = (100, 150, 255)  # Blue
            elif anim_name == "walking":
                color = (100, 255, 100)  # Green
            elif anim_name == "jump":
                color = (255, 255, 100)  # Yellow
            elif anim_name == "fall":
                color = (255, 150, 100)  # Orange
            elif anim_name == "attack":
                color = (255, 100, 100)  # Red
            elif anim_name == "breaking":
                color = (255, 100, 255)  # Magenta
            else:  # placing
                color = (100, 255, 255)  # Cyan
            
            # Draw a simple character shape
            pygame.draw.rect(emergency_surface, color, (8, 4, 16, 20))  # Body
            pygame.draw.circle(emergency_surface, (255, 220, 180), (16, 12), 6)  # Head
            
            # Add asymmetrical details for flipping visibility
            pygame.draw.rect(emergency_surface, (100, 150, 255), (6, 8, 4, 8))   # Left arm (blue)
            pygame.draw.rect(emergency_surface, (100, 255, 100), (22, 8, 4, 8))  # Right arm (green)
            pygame.draw.circle(emergency_surface, (0, 0, 255), (13, 10), 2)       # Left eye (blue)
            pygame.draw.circle(emergency_surface, (0, 255, 0), (19, 10), 2)       # Right eye (green)
            
            self.animations[anim_name] = ProperAnimation([emergency_surface], 0.5)
    
    def update(self, delta_time, player_state):
        """Update animations based on player state"""
        if not self.animations:
            self.setup_animations()
        
        # Update facing direction
        self.facing_right = player_state.get("facing_right", True)
        
        # Determine current animation
        new_animation = self._determine_animation(player_state)
        
        # Change animation if needed
        if new_animation != self.current_animation_name:
            if new_animation in self.animations:
                self.current_animation_name = new_animation
                self.animations[new_animation].reset()
                print(f"🎬 Animation: {self.current_animation_name}")
        
        # Update current animation
        if self.current_animation_name in self.animations:
            self.animations[self.current_animation_name].update(delta_time)
    
    def _determine_animation(self, player_state):
        """Determine which animation to play based on player state"""
        # Priority order: breaking > placing > attacking > jumping/falling > walking > idle
        
        if player_state.get("breaking", False):
            return "breaking"
        elif player_state.get("placing", False):
            return "placing"
        elif player_state.get("attacking", False):
            return "attack"
        elif player_state.get("vel_y", 0) < 0:
            return "jump"
        elif player_state.get("vel_y", 0) > 0:
            return "fall"
        elif self._is_moving_horizontally(player_state):
            return "walking"
        else:
            return "idle"
    
    def _is_moving_horizontally(self, player_state):
        """Detect horizontal movement with proper threshold"""
        current_x = player_state.get("x", 0)
        
        if self.last_position is None:
            self.last_position = current_x
            return False
        
        if abs(current_x - self.last_position) > self.movement_threshold:
            self.last_position = current_x
            return True
        
        self.last_position = current_x
        return False
    
    def get_current_frame(self):
        """Get current animation frame with error handling"""
        # Safety check: ensure animations are loaded
        if not self.animations:
            print("❌ No animations loaded, setting up animations...")
            self.setup_animations()
            if not self.animations:
                print("❌ Failed to setup animations")
                return None
        
        if self.current_animation_name not in self.animations:
            print(f"❌ Animation '{self.current_animation_name}' not found in {list(self.animations.keys())}")
            # Try to fall back to idle animation
            if "idle" in self.animations:
                self.current_animation_name = "idle"
                print(f"🔄 Falling back to idle animation")
            else:
                return None
        
        frame = self.animations[self.current_animation_name].get_current_frame()
        if frame is None:
            print(f"❌ No frame returned for animation '{self.current_animation_name}'")
            return None
        
        # Apply horizontal flipping if needed
        return self.flip_horizontal(frame)
    
    def flip_horizontal(self, surface):
        """Flip surface horizontally if facing left with texture caching for performance"""
        if not self.facing_right:
            # Create a cache key for this surface
            surface_id = id(surface)
            cache_key = f"flipped_{surface_id}"
            
            # Check if we already have this flipped texture cached
            if hasattr(self, '_flipped_cache') and cache_key in self._flipped_cache:
                return self._flipped_cache[cache_key]
            
            # Create flipped texture and cache it
            flipped_surface = pygame.transform.flip(surface, True, False)
            
            # Initialize cache if it doesn't exist
            if not hasattr(self, '_flipped_cache'):
                self._flipped_cache = {}
            
            # Cache the flipped texture (limit cache size to prevent memory issues)
            if len(self._flipped_cache) < 100:  # Limit to 100 cached textures
                self._flipped_cache[cache_key] = flipped_surface
            
            return flipped_surface
        
        return surface
    
    def get_animation_info(self):
        """Get debug information about current animation"""
        if self.current_animation_name not in self.animations:
            return "No animation"
        
        anim = self.animations[self.current_animation_name]
        return f"{self.current_animation_name} ({anim.current_frame_index + 1}/{anim.get_frame_count()})"
    
    def clear_texture_cache(self):
        """Clear the flipped texture cache to free memory"""
        if hasattr(self, '_flipped_cache'):
            self._flipped_cache.clear()
            logger.debug("Texture cache cleared")
    
    def get_cache_info(self):
        """Get information about the texture cache"""
        if hasattr(self, '_flipped_cache'):
            return {
                'cached_textures': len(self._flipped_cache),
                'cache_size_limit': 100
            }
        return {'cached_textures': 0, 'cache_size_limit': 100}
    
    def verify_custom_animations(self):
        """Verify that custom animations are loaded and protected"""
        print("🛡️ CUSTOM ANIMATION PROTECTION VERIFICATION:")
        print(f"   Total animations loaded: {len(self.animations)}")
        
        custom_animations = []
        for anim_name in ["idle", "walking", "jump", "fall", "attack", "breaking", "placing"]:
            if anim_name in self.animations:
                custom_animations.append(anim_name)
                print(f"   ✅ {anim_name}: CUSTOM ANIMATION LOADED")
            else:
                print(f"   ⚠️ {anim_name}: No custom animation found")
        
        print(f"   🎬 Custom animations protected: {len(custom_animations)}/7")
        print("   🛡️ Fallback system: PERMANENTLY DISABLED")
        print("   🎯 Your animations will NEVER be overridden again!")
        
        return custom_animations

# Create the properly engineered animator
player_animator = ProperPlayerAnimator()

def test_character_flipping_system():
    """Test function to verify the character flipping system is working correctly"""
    logger.info("Testing character flipping system...")
    
    # Test 1: Check if player_animator is properly initialized
    if not hasattr(player_animator, 'flip_horizontal'):
        logger.error("❌ Character flipping system not properly initialized")
        return False
    
    # Test 2: Check if facing direction tracking is working
    if "facing_right" not in player:
        logger.error("❌ Player facing direction not initialized")
        return False
    
    # Test 3: Test texture cache system
    if not hasattr(player_animator, 'get_cache_info'):
        logger.error("❌ Texture cache system not properly initialized")
        return False
    
    # Test 4: Verify cache info method works
    try:
        cache_info = player_animator.get_cache_info()
        logger.info(f"✅ Texture cache system working: {cache_info}")
    except Exception as e:
        logger.error(f"❌ Texture cache system error: {e}")
        return False
    
    logger.info("✅ Character flipping system test completed successfully")
    return True

# =============================================================================
# CRAFTING SYSTEM
# =============================================================================
CRAFTING_RECIPES = {
    "pickaxe": {
        "name": "Wooden Pickaxe",
        "materials": {"oak_planks": 2, "stone": 1},
        "description": "Basic mining tool",
        "recipe_image": "Two oak planks in a T-shape with stone on top"
    },
    "sword": {
        "name": "Wooden Sword",
        "materials": {"oak_planks": 2},
        "description": "Basic combat weapon",
        "recipe_image": "Two oak planks stacked vertically"
    },
    "stone_sword": {
        "name": "Stone Sword",
        "materials": {"stone": 2, "oak_planks": 1},
        "description": "Stronger combat weapon"
    },
    "iron_helmet": {
        "name": "Iron Helmet",
        "materials": {"iron": 5, "coal": 2},
        "description": "Protective iron helmet"
    },
    "iron_chestplate": {
        "name": "Iron Chestplate", 
        "materials": {"iron": 8, "coal": 3},
        "description": "Heavy iron chestplate"
    },
    "iron_leggings": {
        "name": "Iron Leggings",
        "materials": {"iron": 7, "coal": 2},
        "description": "Iron leg protection"
    },
    "iron_boots": {
        "name": "Iron Boots",
        "materials": {"iron": 4, "coal": 1},
        "description": "Iron foot protection"
    },
    "ultimate_sword": {
        "name": "Ultimate Stone Sword",
        "materials": {"stone": 50, "oak_planks": 20},
        "description": "The most powerful stone sword"
    },
    "olympic_axe": {
        "name": "Olympic Axe",
        "materials": {"stone": 25, "oak_planks": 15},
        "description": "The legendary bedrock-breaking axe"
    }
}

def check_crafting_recipe(materials):
    """Check if materials match any crafting recipe"""
    for recipe_name, recipe in CRAFTING_RECIPES.items():
        if materials == recipe["materials"]:
            return recipe_name
    return None

def craft_item(recipe_name):
    """Craft an item using the specified recipe"""
    if recipe_name not in CRAFTING_RECIPES:
        return False
    
    recipe = CRAFTING_RECIPES[recipe_name]
    materials_needed = recipe["materials"]
    
    # Check if player has all required materials
    for material, count in materials_needed.items():
        if not has_material(material, count):
            return False
    
    # Remove materials from inventory
    for material, count in materials_needed.items():
        remove_material(material, count)
    
    # Add crafted item to inventory
    add_to_inventory(recipe_name)
    print(f"⚒️ Crafted {recipe['name']}!")
    
    # Check for crafting achievements
    check_achievement("crafting_master", "Crafted first item!")
    if recipe_name in ["pickaxe", "sword"]:
        check_achievement("tool_maker", "Crafted your first tool!")
    
    return True

def has_material(material, count):
    """Check if player has enough of a material"""
    total = 0
    for item in player["inventory"]:
        if item and item.get("type") == material:
            total += item.get("count", 1)
    return total >= count

def remove_material(material, count):
    """Remove material from inventory"""
    remaining = count
    for item in player["inventory"]:
        if item and item.get("type") == material and remaining > 0:
            item_count = item.get("count", 1)
            if item_count <= remaining:
                remaining -= item_count
                item["count"] = 0
            else:
                item["count"] = item_count - remaining
                remaining = 0
            if item["count"] <= 0:
                item.clear()
    
    # Clean up empty slots
    normalize_inventory()

def draw_crafting_interface():
    """Draw the crafting interface"""
    if not show_crafting:
        return
    
    # Crafting background
    crafting_x = SCREEN_WIDTH // 2 - 200
    crafting_y = SCREEN_HEIGHT // 2 - 150
    crafting_width = 400
    crafting_height = 300
    
    pygame.draw.rect(screen, (50, 50, 50), (crafting_x, crafting_y, crafting_width, crafting_height))
    pygame.draw.rect(screen, (100, 100, 100), (crafting_x, crafting_y, crafting_width, crafting_height), 3)
    
    # Title
    title_text = font.render("⚒️ CRAFTING", True, (255, 255, 255))
    screen.blit(title_text, (crafting_x + crafting_width // 2 - title_text.get_width() // 2, crafting_y + 10))
    
    # Material input slots (3x3 grid)
    slot_size = 40
    start_x = crafting_x + 50
    start_y = crafting_y + 50
    
    for i in range(9):
        row = i // 3
        col = i % 3
        slot_x = start_x + col * (slot_size + 10)
        slot_y = start_y + row * (slot_size + 10)
        
        # Draw slot
        pygame.draw.rect(screen, (100, 100, 100), (slot_x, slot_y, slot_size, slot_size))
        pygame.draw.rect(screen, (200, 200, 200), (slot_x, slot_y, slot_size, slot_size), 2)
        
        # Draw item if exists
        if i < len(crafting_materials):
            material = crafting_materials[i]
            if material in textures:
                screen.blit(textures[material], (slot_x + 4, slot_y + 4))
            # Draw count
            count_text = font.render(str(material_counts.get(material, 1)), True, (255, 255, 0))
            screen.blit(count_text, (slot_x + 25, slot_y + 25))
    
    # Output slot
    output_x = crafting_x + 300
    output_y = crafting_y + 100
    pygame.draw.rect(screen, (150, 150, 150), (output_x, output_y, slot_size, slot_size))
    pygame.draw.rect(screen, (255, 255, 255), (output_x, output_y, slot_size, slot_size), 3)
    
    # Check recipe and show output
    recipe_name = check_crafting_recipe(material_counts)
    if recipe_name:
        recipe = CRAFTING_RECIPES[recipe_name]
        # Show crafted item
        if recipe_name in textures:
            screen.blit(textures[recipe_name], (slot_x + 4, slot_y + 4))
        
        # Show recipe name
        recipe_text = font.render(recipe["name"], True, (255, 255, 0))
        screen.blit(recipe_text, (output_x - 150, output_y + 50))
        
        # Show description
        desc_text = font.render(recipe["description"], True, (200, 200, 200))
        screen.blit(desc_text, (output_x - 150, output_y + 70))
        
        # Craft button
        craft_btn = pygame.Rect(output_x - 150, output_y + 100, 120, 30)
        pygame.draw.rect(screen, (0, 150, 0), craft_btn)
        pygame.draw.rect(screen, (255, 255, 255), craft_btn, 2)
        
        craft_text = font.render("CRAFT", True, (255, 255, 255))
        screen.blit(craft_text, (craft_btn.x + 10, craft_btn.y + 5))
        
        # Check for craft button click
        if pygame.mouse.get_pressed()[0]:  # Left click
            mouse_pos = pygame.mouse.get_pos()
            if craft_btn.collidepoint(mouse_pos):
                if craft_item(recipe_name):
                    # Clear crafting materials
                    crafting_materials.clear()
                    material_counts.clear()
    
    # Instructions
    instruction_text = font.render("Place materials in slots to see recipes", True, (200, 200, 200))
    screen.blit(instruction_text, (crafting_x + 20, crafting_y + 250))
    
    # Close button
    close_btn = pygame.Rect(crafting_x + crafting_width - 40, crafting_y + 10, 30, 30)
    pygame.draw.rect(screen, (200, 0, 0), close_btn)
    pygame.draw.rect(screen, (255, 255, 255), close_btn, 2)
    
    close_text = font.render("X", True, (255, 255, 255))
    screen.blit(close_text, (close_btn.x + 10, close_btn.y + 5))

# Crafting variables

crafting_materials = []
material_counts = {}

def add_to_crafting(material):
    """Add material to crafting grid"""
    if len(crafting_materials) < 9:
        crafting_materials.append(material)
        material_counts[material] = material_counts.get(material, 0) + 1
        print(f"⚒️ Added {material} to crafting grid")
    else:
        print("⚒️ Crafting grid is full!")

def clear_crafting():
    """Clear crafting grid and return materials to inventory"""
    for material in crafting_materials:
        add_to_inventory(material)
    crafting_materials.clear()
    material_counts.clear()
    print("⚒️ Cleared crafting grid")

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
    
    def load_animation_frames(self, animation_type, fallback_name, speed):
        """Load animation frames - tries custom files first, then creates fallbacks"""
        frames = []
        
        # First, try to load a custom .gif file from animations folder
        gif_path = f"../../../../player/animations/{fallback_name}.gif"
        if os.path.exists(gif_path):
            try:
                print(f"🎬 Loading {animation_type} from GIF: {gif_path}")
                
                # Try to extract multiple frames from GIF using PIL (Pillow)
                try:
                    try:
                        import PIL
                        from PIL import Image
                    except ImportError:
                        print("⚠️ PIL (Pillow) not available, using fallback animation")
                        raise ImportError("PIL not available")
                    gif_image = Image.open(gif_path)
                    
                    # Extract all frames from the GIF
                    frame_count = 0
                    for frame_num in range(gif_image.n_frames):
                        gif_image.seek(frame_num)
                        
                        # Convert PIL image to Pygame surface
                        frame_data = gif_image.convert("RGBA").tobytes()
                        frame_size = gif_image.size
                        
                        # Create Pygame surface from the frame data
                        frame_surface = pygame.image.fromstring(frame_data, frame_size, "RGBA")
                        
                        # Scale to 32x32 if needed
                        if frame_surface.get_size() != (32, 32):
                            frame_surface = pygame.transform.scale(frame_surface, (32, 32))
                        
                        frames.append(frame_surface)
                        frame_count += 1
                    
                    print(f"✅ Successfully loaded {fallback_name}.gif with {frame_count} frames!")
                    
                    # Adjust animation speed based on frame count
                    if frame_count > 1:
                        adjusted_speed = speed * (frame_count / 6)  # Normalize to 6 frames
                    else:
                        adjusted_speed = speed
                    
                    animation = Animation(frames, adjusted_speed)
                    animation.is_custom = True  # Mark as custom animation
                    return animation
                    
                except ImportError:
                    print("⚠️ PIL not available, using single frame from GIF")
                    # Fallback: load single frame if PIL is not available
                    gif_frame = pygame.image.load(gif_path).convert_alpha()
                    
                    # Scale to 32x32 if needed
                    if gif_frame.get_size() != (32, 32):
                        gif_frame = pygame.transform.scale(gif_frame, (32, 32))
                    
                    frames.append(gif_frame)
                    print(f"✅ Loaded single frame from {fallback_name}.gif")
                    animation = Animation(frames, speed)
                    animation.is_custom = True  # Mark as custom animation
                    return animation
                
            except Exception as e:
                print(f"⚠️ Could not load {fallback_name}.gif: {e}")
        
        # If no custom GIF found, create a proper fallback animation
        print(f"🔄 Creating fallback animation for {animation_type}")
        fallback_frames = self.create_fallback_animation(animation_type, fallback_name)
        animation = Animation(fallback_frames, speed)
        animation.is_custom = False  # Mark as fallback animation
        return animation
    
    def create_fallback_animation(self, animation_type, fallback_name):
        """Create proper fallback animations with multiple frames for smooth movement"""
        frames = []
        
        if animation_type == "idle" or fallback_name == "standing":
            # Breathing/idle animation - subtle up/down movement
            for i in range(4):
                frame = pygame.Surface((32, 32))
                frame.set_colorkey((0, 0, 0))
                
                # Body with slight vertical movement
                body_y = 4 + (i % 2) * 2  # Subtle breathing effect
                pygame.draw.rect(frame, (100, 150, 255), (8, body_y, 16, 20))
                pygame.draw.circle(frame, (255, 220, 180), (16, 12 + (i % 2)), 6)  # Head
                
                # Add breathing indicator
                indicator_color = (255, 255, 255)
                pygame.draw.rect(frame, indicator_color, (2, 2, 6, 6))
                
                frames.append(frame)
                
        elif animation_type == "walking" or fallback_name == "walking":
            # Walking animation - arm and leg movement
            for i in range(6):
                frame = pygame.Surface((32, 32))
                frame.set_colorkey((0, 0, 0))
                
                # Body
                pygame.draw.rect(frame, (100, 255, 100), (8, 4, 16, 20))
                pygame.draw.circle(frame, (255, 220, 180), (16, 12), 6)  # Head
                
                # Animated arms and legs
                arm_swing = math.sin(i * math.pi / 3) * 3
                leg_swing = math.cos(i * math.pi / 3) * 2
                
                # Arms
                pygame.draw.rect(frame, (200, 150, 50), (6, 8 + arm_swing, 4, 8))
                pygame.draw.rect(frame, (200, 150, 50), (22, 8 - arm_swing, 4, 8))
                
                # Legs
                pygame.draw.rect(frame, (139, 69, 19), (10, 24 + leg_swing, 4, 8))
                pygame.draw.rect(frame, (139, 69, 19), (18, 24 - leg_swing, 4, 8))
                
                frames.append(frame)
                
        elif animation_type == "jump" or fallback_name == "jumping":
            # Jumping animation - crouch and extend
            for i in range(4):
                frame = pygame.Surface((32, 32))
                frame.set_colorkey((0, 0, 0))
                
                # Body with jump animation
                body_height = 20 - (i * 2)  # Get smaller as jumping
                body_y = 4 + (i * 2)
                pygame.draw.rect(frame, (255, 255, 100), (8, body_y, 16, body_height))
                pygame.draw.circle(frame, (255, 220, 180), (16, 12), 6)  # Head
                
                # Arms up during jump
                if i > 0:
                    pygame.draw.rect(frame, (200, 150, 50), (6, 6, 4, 6))
                    pygame.draw.rect(frame, (200, 150, 50), (22, 6, 4, 6))
                
                frames.append(frame)
                
        elif animation_type == "fall" or fallback_name == "falling":
            # Falling animation - arms flailing
            for i in range(4):
                frame = pygame.Surface((32, 32))
                frame.set_colorkey((0, 0, 0))
                
                # Body
                pygame.draw.rect(frame, (255, 150, 100), (8, 4, 16, 20))
                pygame.draw.circle(frame, (255, 220, 180), (16, 12), 6)  # Head
                
                # Flailing arms
                arm_angle = i * math.pi / 2
                arm1_x = 16 + int(math.cos(arm_angle) * 8)
                arm1_y = 8 + int(math.sin(arm_angle) * 4)
                arm2_x = 16 + int(math.cos(arm_angle + math.pi) * 8)
                arm2_y = 8 + int(math.sin(arm_angle + math.pi) * 4)
                
                pygame.draw.rect(frame, (200, 150, 50), (arm1_x, arm1_y, 4, 6))
                pygame.draw.rect(frame, (200, 150, 50), (arm2_x, arm2_y, 4, 6))
                
                frames.append(frame)
                
        elif animation_type == "attack" or fallback_name == "fighting":
            # Fighting animation - swinging motion
            for i in range(6):
                frame = pygame.Surface((32, 32))
                frame.set_colorkey((0, 0, 0))
                
                # Body
                pygame.draw.rect(frame, (255, 100, 100), (8, 4, 16, 20))
                pygame.draw.circle(frame, (255, 220, 180), (16, 12), 6)  # Head
                
                # Swinging arm with weapon
                swing_angle = (i * math.pi / 3) - math.pi/2
                arm_x = 16 + int(math.cos(swing_angle) * 10)
                arm_y = 8 + int(math.sin(swing_angle) * 6)
                
                pygame.draw.rect(frame, (200, 150, 50), (arm_x, arm_y, 6, 8))
                pygame.draw.rect(frame, (139, 69, 19), (arm_x + 6, arm_y - 2, 2, 12))  # Weapon
                
                frames.append(frame)
                
        elif animation_type == "breaking" or fallback_name == "breaking":
            # Breaking animation - mining motion
            for i in range(8):
                frame = pygame.Surface((32, 32))
                frame.set_colorkey((0, 0, 0))
                
                # Body
                pygame.draw.rect(frame, (255, 100, 255), (8, 4, 16, 20))
                pygame.draw.circle(frame, (255, 220, 180), (16, 12), 6)  # Head
                
                # Mining motion - pickaxe swinging
                swing_angle = (i * math.pi / 4) - math.pi/2
                tool_x = 16 + int(math.cos(swing_angle) * 12)
                tool_y = 8 + int(math.sin(swing_angle) * 8)
                
                pygame.draw.rect(frame, (200, 150, 50), (tool_x, tool_y, 4, 8))  # Arm
                pygame.draw.rect(frame, (139, 69, 19), (tool_x + 4, tool_y - 4, 2, 16))  # Pickaxe
                
                frames.append(frame)
import pygame
import random
import os
import time
import json
import shutil
import sys
import math
import signal
import copy
import traceback
import logging
import threading
import socket
import pickle
import struct
import select
import hashlib
import uuid
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import weakref

# Ensure the game runs from the correct directory (where the game files are located)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

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
