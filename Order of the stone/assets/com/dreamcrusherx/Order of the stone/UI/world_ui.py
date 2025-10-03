#!/usr/bin/env python3
"""
🎮 Modern World UI System for Order of the Stone
Clean, intuitive interface for world management
"""

import pygame
import time
from typing import Dict, List, Optional, Callable

class WorldUI:
    """Modern world selection and management interface"""
    
    def __init__(self, screen: pygame.Surface, world_system, font, big_font):
        self.screen = screen
        self.world_system = world_system
        self.font = font
        self.big_font = big_font
        
        # UI state
        self.current_page = 0
        self.worlds_per_page = 6
        self.selected_world_index = 0
        self.world_rects = {}  # Store world button rectangles
        self.pending_action = None  # Store pending actions
        self.pending_world_name = None  # Store pending world names

        
        # Button dimensions
        self.button_width = 300
        self.button_height = 60
        self.button_spacing = 20
        
        # Colors - Modern gradient theme
        self.colors = {
            "background": (15, 15, 35),
            "background_gradient": (25, 25, 55),
            "panel": (45, 45, 85),
            "panel_glow": (65, 65, 105),
            "button": (70, 70, 130),
            "button_hover": (90, 90, 150),
            "button_selected": (110, 110, 170),
            "button_glow": (130, 130, 190),
            "text": (255, 255, 255),
            "text_secondary": (220, 220, 220),
            "text_dim": (180, 180, 200),
            "accent": (255, 215, 0),
            "accent_glow": (255, 235, 100),
            "danger": (255, 100, 100),
            "danger_glow": (255, 120, 120),
            "success": (100, 255, 100),
            "success_glow": (120, 255, 120),
            "info": (100, 200, 255),
            "info_glow": (120, 220, 255)
        }
    
    def draw_world_selection(self, mouse_pos: tuple, username_required: bool = False) -> Dict[str, any]:
        """EXTREME ENGINEERING: Draw the world selection screen with username validation and return button states"""
        # Enhanced background with gradient
        self._draw_gradient_background()
        
        # Decorative elements
        self._draw_decorative_elements()
        
        # Title with glow effect
        title = self.big_font.render("🌍 Select World", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("🌍 Select World", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Subtitle
        subtitle = self.font.render("Choose your adventure or create a new one", True, self.colors["text_secondary"])
        subtitle_x = (self.screen.get_width() - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (subtitle_x, 90))
        
        # Get world list
        worlds = self.world_system.get_world_list()
        
        if not worlds:
            # No worlds message
            no_worlds_text = self.font.render("No worlds found. Create your first world!", True, self.colors["text_secondary"])
            text_x = (self.screen.get_width() - no_worlds_text.get_width()) // 2
            self.screen.blit(no_worlds_text, (text_x, 200))
            
            # Create world button
            create_btn = self._draw_button("✨ Create New World", 400, 300, mouse_pos, self.colors["success"])
            
            # Back button
            back_btn = self._draw_button("⬅️ Back to Title", 400, 380, mouse_pos, self.colors["button"])
            
            return {
                "create_world": create_btn,
                "back": back_btn
            }
        
        # EXTREME ENGINEERING: Username validation check
        if username_required:
            # Username required message
            username_title = self.big_font.render("🚫 Username Required", True, self.colors["danger"])
            title_x = (self.screen.get_width() - username_title.get_width()) // 2
            self.screen.blit(username_title, (title_x, 150))
            
            username_message = self.font.render("You cannot play this game without creating a username!", True, self.colors["text"])
            message_x = (self.screen.get_width() - username_message.get_width()) // 2
            self.screen.blit(username_message, (message_x, 200))
            
            username_subtitle = self.font.render("Please go back to the title screen to create your username.", True, self.colors["text_secondary"])
            subtitle_x = (self.screen.get_width() - username_subtitle.get_width()) // 2
            self.screen.blit(username_subtitle, (subtitle_x, 230))
            
            # Go back to title button
            back_btn = self._draw_button("⬅️ Go Back to Title", 400, 300, mouse_pos, self.colors["danger"])
            
            return {
                "back": back_btn
            }
        
        # World list
        start_index = self.current_page * self.worlds_per_page
        end_index = min(start_index + self.worlds_per_page, len(worlds))
        page_worlds = worlds[start_index:end_index]
        
        # Draw worlds
        button_states = {}
        self.world_rects = {}  # Clear and rebuild world rectangles
        y_start = 150
        
        for i, world in enumerate(page_worlds):
            world_index = start_index + i
            y_pos = y_start + i * (self.button_height + self.button_spacing)
            
            # Check if this world is selected
            is_selected = world_index == self.selected_world_index
            is_current = world["name"] == self.world_system.get_current_world_name()
            
            # Draw world button
            btn_rect = self._draw_world_button(world, y_pos, mouse_pos, is_selected, is_current)
            button_states[f"world_{world_index}"] = btn_rect
            self.world_rects[f"world_{world_index}"] = btn_rect  # Store for mouse handling
        
        # Navigation buttons
        nav_y = y_start + len(page_worlds) * (self.button_height + self.button_spacing) + 40
        
        # Previous page
        if self.current_page > 0:
            prev_btn = self._draw_button("◀️ Previous", 200, nav_y, mouse_pos, self.colors["button"])
            button_states["prev_page"] = prev_btn
        
        # Next page
        if end_index < len(worlds):
            next_btn = self._draw_button("Next ▶️", 600, nav_y, mouse_pos, self.colors["button"])
            button_states["next_page"] = next_btn
        
        # Action buttons with EXTREME ENGINEERING spacing
        action_y = nav_y + 80
        
        if worlds:
            # Check if a world is selected
            is_selected = self.is_world_selected()
            
            # Calculate button positions with proper spacing
            screen_width = self.screen.get_width()
            button_spacing = 50  # Space between buttons
            total_button_width = (self.button_width * 3) + (button_spacing * 2)  # 3 buttons + 2 gaps
            start_x = (screen_width - total_button_width) // 2  # Center the button group
            
            # Play selected world (always present, but disabled when no world selected)
            if is_selected:
                play_btn = self._draw_button("▶️ Play World", start_x, action_y, mouse_pos, self.colors["success"])
            else:
                # Disabled play button
                play_btn = self._draw_button("▶️ Play World (Select a World)", start_x, action_y, mouse_pos, self.colors["text_dim"])
            button_states["play_world"] = play_btn
            
            # Delete selected world (always present, but disabled when no world selected)
            if is_selected:
                delete_btn = self._draw_button("🗑️ Delete World", start_x + self.button_width + button_spacing, action_y, mouse_pos, self.colors["danger"])
            else:
                # Disabled delete button
                delete_btn = self._draw_button("🗑️ Delete World (Select a World)", start_x + self.button_width + button_spacing, action_y, mouse_pos, self.colors["text_dim"])
            button_states["delete_world"] = delete_btn
            
            # Create new world (always enabled)
            create_btn = self._draw_button("✨ Create New World", start_x + (self.button_width + button_spacing) * 2, action_y, mouse_pos, self.colors["success"])
            button_states["create_world"] = create_btn
        
        # Back button
        back_btn = self._draw_button("⬅️ Back to Title", 400, action_y + 80, mouse_pos, self.colors["button"])
        button_states["back"] = back_btn
        
        return button_states
    
    def _draw_world_button(self, world: Dict, y_pos: int, mouse_pos: tuple, is_selected: bool, is_current: bool) -> pygame.Rect:
        """Draw a world selection button with enhanced visual effects"""
        # Button background with rounded corners effect
        btn_rect = pygame.Rect(50, y_pos, self.screen.get_width() - 100, self.button_height)
        
        # EXTREME ENGINEERING: Enhanced button color and effects with priority system
        if is_current:
            # Current world gets highest priority - bright accent colors
            base_color = self.colors["accent"]
            glow_color = self.colors["accent_glow"]
            border_color = self.colors["accent"]
            glow_intensity = 8  # Stronger glow for current world
        elif is_selected:
            # Selected world gets second priority - bright selection colors
            base_color = self.colors["success"]  # Use success color for better visibility
            glow_color = self.colors["success_glow"]
            border_color = self.colors["text"]
            glow_intensity = 6  # Strong glow for selected world
        elif btn_rect.collidepoint(mouse_pos):
            # Hover state gets third priority
            base_color = self.colors["button_hover"]
            glow_color = self.colors["button_glow"]
            border_color = self.colors["text"]
            glow_intensity = 4  # Moderate glow for hover
        else:
            # Default state gets lowest priority
            base_color = self.colors["button"]
            glow_color = self.colors["button"]
            border_color = self.colors["text_dim"]
            glow_intensity = 2  # Subtle glow for default
        
        # EXTREME ENGINEERING: Dynamic button glow effect based on state
        glow_rect = pygame.Rect(btn_rect.x - glow_intensity, btn_rect.y - glow_intensity, 
                               btn_rect.width + (glow_intensity * 2), btn_rect.height + (glow_intensity * 2))
        pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=8 + glow_intensity)
        
        # Draw main button
        pygame.draw.rect(self.screen, base_color, btn_rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, btn_rect, 3, border_radius=6)
        
        # EXTREME ENGINEERING: Enhanced inner highlight with selection emphasis
        highlight_rect = pygame.Rect(btn_rect.x + 2, btn_rect.y + 2, btn_rect.width - 4, btn_rect.height // 2)
        
        if is_selected:
            # Selected worlds get a brighter, more prominent highlight
            highlight_color = tuple(min(255, int(c * 1.4)) for c in base_color)
            # Add a subtle pulsing effect for selected worlds
            pulse_factor = 1.0 + (0.1 * (time.time() % 2))  # Subtle pulse over 2 seconds
            highlight_color = tuple(min(255, int(c * pulse_factor)) for c in highlight_color)
        else:
            # Normal highlight for other states
            highlight_color = tuple(min(255, int(c * 1.2)) for c in base_color)
        
        pygame.draw.rect(self.screen, highlight_color, highlight_rect, border_radius=4)
        
        # EXTREME ENGINEERING: Enhanced world name display with selection indicators
        
        # Add selection arrow for selected worlds
        if is_selected:
            # Draw a bright selection arrow on the left
            arrow_text = self.font.render("▶", True, self.colors["success"])
            self.screen.blit(arrow_text, (btn_rect.x + 5, btn_rect.y + 12))
            # Adjust name position to make room for arrow
            name_x = btn_rect.x + 25
        else:
            name_x = btn_rect.x + 20
        
        # World name with enhanced typography
        name_text = self.font.render(world["name"], True, self.colors["text"])
        self.screen.blit(name_text, (name_x, btn_rect.y + 12))
        
        # World info with better formatting
        seed_text = f"🌱 Seed: {world['seed']}"
        created_text = f"📅 {self._format_time(world['created'])}"
        
        seed_surface = self.font.render(seed_text, True, self.colors["text_secondary"])
        created_surface = self.font.render(created_text, True, self.colors["text_dim"])
        
        self.screen.blit(seed_surface, (btn_rect.x + 20, btn_rect.y + 32))
        self.screen.blit(created_surface, (btn_rect.x + 20, btn_rect.y + 48))
        
        # EXTREME ENGINEERING: Enhanced selection and current world indicators
        
        # Selection indicator badge (LEFT SIDE)
        if is_selected:
            # Selection badge background
            selection_badge_rect = pygame.Rect(btn_rect.x + 10, btn_rect.y + 8, 100, 20)
            pygame.draw.rect(self.screen, self.colors["success"], selection_badge_rect, border_radius=10)
            pygame.draw.rect(self.screen, self.colors["text"], selection_badge_rect, 2, border_radius=10)
            
            # Selection badge text
            selection_text = self.font.render("✅ SELECTED", True, self.colors["text"])
            selection_text_x = selection_badge_rect.x + (selection_badge_rect.width - selection_text.get_width()) // 2
            selection_text_y = selection_badge_rect.y + (selection_badge_rect.height - selection_text.get_height()) // 2
            self.screen.blit(selection_text, (selection_text_x, selection_text_y))
        
        # Current world indicator badge (RIGHT SIDE)
        if is_current:
            # Current world badge background
            current_badge_rect = pygame.Rect(btn_rect.right - 120, btn_rect.y + 8, 100, 20)
            pygame.draw.rect(self.screen, self.colors["accent"], current_badge_rect, border_radius=10)
            pygame.draw.rect(self.screen, self.colors["text"], current_badge_rect, 2, border_radius=10)
            
            # Current world badge text
            current_text = self.font.render("⭐ CURRENT", True, self.colors["text"])
            current_text_x = current_badge_rect.x + (current_badge_rect.width - current_text.get_width()) // 2
            current_text_y = current_badge_rect.y + (current_badge_rect.height - current_text.get_height()) // 2
            self.screen.blit(current_text, (current_text_x, current_text_y))
        
        return btn_rect
    
    def _draw_button(self, text: str, x: int, y: int, mouse_pos: tuple, base_color: tuple) -> pygame.Rect:
        """Draw a standard button with enhanced visual effects"""
        btn_rect = pygame.Rect(x, y, self.button_width, self.button_height)
        
        # Check hover and determine colors
        if btn_rect.collidepoint(mouse_pos):
            color = tuple(min(255, c + 30) for c in base_color)
            glow_color = tuple(min(255, c + 50) for c in base_color)
            border_color = self.colors["text"]
        else:
            color = base_color
            glow_color = base_color
            border_color = self.colors["text_dim"]
        
        # Draw button glow effect
        glow_rect = pygame.Rect(btn_rect.x - 3, btn_rect.y - 3, btn_rect.width + 6, btn_rect.height + 6)
        pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=12)
        
        # Draw main button with rounded corners
        pygame.draw.rect(self.screen, color, btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, btn_rect, 3, border_radius=10)
        
        # Add inner highlight for 3D effect
        highlight_rect = pygame.Rect(btn_rect.x + 3, btn_rect.y + 3, btn_rect.width - 6, btn_rect.height // 2)
        highlight_color = tuple(min(255, int(c * 1.3)) for c in color)
        pygame.draw.rect(self.screen, highlight_color, highlight_rect, border_radius=8)
        
        # Draw text with shadow effect
        shadow_surface = self.font.render(text, True, (0, 0, 0))
        text_surface = self.font.render(text, True, self.colors["text"])
        
        # Shadow offset
        text_x = btn_rect.x + (btn_rect.width - text_surface.get_width()) // 2
        text_y = btn_rect.y + (btn_rect.height - text_surface.get_height()) // 2
        
        # Draw shadow first
        self.screen.blit(shadow_surface, (text_x + 2, text_y + 2))
        # Draw main text
        self.screen.blit(text_surface, (text_x, text_y))
        
        return btn_rect
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp into readable date"""
        try:
            dt = time.localtime(timestamp)
            return time.strftime("%m/%d/%Y", dt)
        except:
            return "Unknown"
    
    def handle_world_click(self, mouse_pos: tuple) -> Optional[int]:
        """EXTREME ENGINEERING: Robust world selection with toggle functionality and comprehensive error handling"""
        try:
            # Validate input parameters
            if not isinstance(mouse_pos, tuple) or len(mouse_pos) != 2:
                print(f"❌ Invalid mouse position: {mouse_pos}")
                return None
            
            # EXTREME ENGINEERING: Comprehensive world selection logic with toggle support
            for world_key, rect in self.world_rects.items():
                # Validate world key format
                if not isinstance(world_key, str) or not world_key.startswith("world_"):
                    print(f"⚠️ Invalid world key format: {world_key}")
                    continue
                
                # Validate rectangle object
                if not isinstance(rect, pygame.Rect):
                    print(f"⚠️ Invalid rectangle object for key {world_key}: {type(rect)}")
                    continue
                
                # Check collision with proper bounds validation
                if rect.collidepoint(mouse_pos):
                    try:
                        # Extract world index with robust parsing
                        world_index_str = world_key.split("_", 1)[1]  # Split only once, get second part
                        world_index = int(world_index_str)
                        
                        # Validate index bounds
                        worlds = self.world_system.get_world_list()
                        if 0 <= world_index < len(worlds):
                            # EXTREME ENGINEERING: Toggle selection logic
                            old_selection = self.selected_world_index
                            
                            if self.selected_world_index == world_index:
                                # Toggle: Clicking selected world again deselects it
                                self.selected_world_index = -1  # -1 means no selection
                                print(f"🔄 EXTREME ENGINEERING: World deselection successful!")
                                print(f"   📍 Previous selection: {old_selection}")
                                print(f"   📍 New selection: {self.selected_world_index} (none)")
                                print(f"   🌍 World deselected: {worlds[world_index].get('name', 'Unknown')}")
                                return -1  # Return -1 to indicate deselection
                            else:
                                # Select new world
                                self.selected_world_index = world_index
                                
                                # Get world info for logging
                                selected_world = worlds[world_index]
                                world_name = selected_world.get("name", "Unknown")
                                
                                print(f"🌍 EXTREME ENGINEERING: World selection successful!")
                                print(f"   📍 Old selection: {old_selection}")
                                print(f"   📍 New selection: {world_index}")
                                print(f"   🌍 World name: {world_name}")
                                print(f"   🎯 Total worlds: {len(worlds)}")
                                
                                return world_index
                        else:
                            print(f"❌ World index out of bounds: {world_index} (max: {len(worlds) - 1})")
                            return None
                            
                    except (ValueError, IndexError) as e:
                        print(f"❌ Error parsing world index from key '{world_key}': {e}")
                        continue
            
            # No world clicked
            print(f"🔍 No world clicked at position {mouse_pos}")
            return None
            
        except Exception as e:
            print(f"💥 EXTREME ENGINEERING ERROR in world selection: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_selected_world(self) -> Optional[Dict]:
        """EXTREME ENGINEERING: Robust world data retrieval with comprehensive validation and toggle support"""
        try:
            # Check for explicit deselection
            if self.selected_world_index == -1:
                print("🔍 EXTREME ENGINEERING: No world selected (explicit deselection)")
                return None
            
            # Validate world system
            if not hasattr(self, 'world_system') or self.world_system is None:
                print("❌ World system not available")
                return None
            
            # Get world list with error handling
            try:
                worlds = self.world_system.get_world_list()
            except Exception as e:
                print(f"❌ Error getting world list: {e}")
                return None
            
            # Validate world list
            if not isinstance(worlds, list):
                print(f"❌ Invalid world list type: {type(worlds)}")
                return None
            
            # Validate selection index
            if not isinstance(self.selected_world_index, int):
                print(f"❌ Invalid selection index type: {type(self.selected_world_index)}")
                return None
            
            # Check bounds
            if self.selected_world_index < 0:
                print(f"❌ Selection index negative: {self.selected_world_index}")
                return None
            
            if self.selected_world_index >= len(worlds):
                print(f"❌ Selection index out of bounds: {self.selected_world_index} >= {len(worlds)}")
                return None
            
            # Get selected world
            selected_world = worlds[self.selected_world_index]
            
            # Validate world data structure
            if not isinstance(selected_world, dict):
                print(f"❌ Invalid world data type: {type(selected_world)}")
                return None
            
            # Validate required fields
            required_fields = ["name", "created", "seed"]
            for field in required_fields:
                if field not in selected_world:
                    print(f"⚠️ Missing required field in world data: {field}")
                    return None
            
            print(f"✅ EXTREME ENGINEERING: Successfully retrieved world '{selected_world['name']}'")
            return selected_world
            
        except Exception as e:
            print(f"💥 EXTREME ENGINEERING ERROR in get_selected_world: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def is_world_selected(self) -> bool:
        """EXTREME ENGINEERING: Robust world selection state validation with toggle support"""
        try:
            # Check if selection index indicates no selection
            if self.selected_world_index == -1:
                print(f"🔍 EXTREME ENGINEERING: No world currently selected (explicit deselection)")
                return False
            
            # Get selected world with full validation
            selected_world = self.get_selected_world()
            
            # Check if we have valid world data
            if selected_world is None:
                print(f"🔍 EXTREME ENGINEERING: No world currently selected")
                return False
            
            # Additional validation: ensure world still exists in system
            try:
                worlds = self.world_system.get_world_list()
                world_names = [w.get("name", "") for w in worlds]
                
                if selected_world.get("name") not in world_names:
                    print(f"⚠️ Selected world '{selected_world.get('name')}' no longer exists in system")
                    self.reset_world_selection()  # Use proper reset method
                    return False
                
            except Exception as e:
                print(f"⚠️ Error validating world existence: {e}")
                return False
            
            print(f"✅ EXTREME ENGINEERING: World '{selected_world.get('name')}' is validly selected")
            return True
            
        except Exception as e:
            print(f"💥 EXTREME ENGINEERING ERROR in is_world_selected: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def reset_world_selection(self):
        """EXTREME ENGINEERING: Reset world selection to safe default state"""
        try:
            old_selection = self.selected_world_index
            self.selected_world_index = -1  # -1 means no selection
            
            print(f"🔄 EXTREME ENGINEERING: World selection reset")
            print(f"   📍 Old selection: {old_selection}")
            print(f"   📍 New selection: {self.selected_world_index} (none)")
            
        except Exception as e:
            print(f"💥 EXTREME ENGINEERING ERROR in reset_world_selection: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_world_selection(self):
        """EXTREME ENGINEERING: Refresh world selection state and validate current selection"""
        try:
            print(f"🔄 EXTREME ENGINEERING: Refreshing world selection state")
            
            # Get current world list
            try:
                worlds = self.world_system.get_world_list()
                world_count = len(worlds)
            except Exception as e:
                print(f"❌ Error getting world list during refresh: {e}")
                self.reset_world_selection()
                return
            
            print(f"   📊 Total worlds available: {world_count}")
            print(f"   📍 Current selection index: {self.selected_world_index}")
            
            # Validate current selection
            if world_count == 0:
                print(f"   ⚠️ No worlds available, resetting selection")
                self.reset_world_selection()
                return
            
            # Check if current selection is still valid
            if self.selected_world_index >= world_count:
                print(f"   ⚠️ Selection index out of bounds, resetting")
                self.reset_world_selection()
                return
            
            # Check for explicit deselection
            if self.selected_world_index == -1:
                print(f"   🔍 No world selected (explicit deselection)")
                return
            
            # Validate selected world data
            if self.is_world_selected():
                selected_world = self.get_selected_world()
                print(f"   ✅ Selection validated: '{selected_world.get('name', 'Unknown')}'")
            else:
                print(f"   ⚠️ Selection invalid, resetting")
                self.reset_world_selection()
            
        except Exception as e:
            print(f"💥 EXTREME ENGINEERING ERROR in refresh_world_selection: {e}")
            import traceback
            traceback.print_exc()
            self.reset_world_selection()
    
    def draw_world_creation(self, mouse_pos: tuple, world_name: str = "", seed: str = "") -> Dict[str, any]:
        """Draw the world creation screen with enhanced design"""
        # Enhanced background
        self._draw_gradient_background()
        self._draw_decorative_elements()
        
        # Title with glow effect
        title = self.big_font.render("✨ Create New World", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("✨ Create New World", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Subtitle
        subtitle = self.font.render("Begin your new adventure with a custom world", True, self.colors["text_secondary"])
        subtitle_x = (self.screen.get_width() - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (subtitle_x, 90))
        
        # World name input with enhanced styling
        name_label = self.font.render("🌍 World Name:", True, self.colors["text"])
        self.screen.blit(name_label, (200, 150))
        
        name_input_rect = pygame.Rect(200, 180, 400, 50)
        # Input field glow
        pygame.draw.rect(self.screen, self.colors["panel_glow"], name_input_rect, border_radius=8)
        # Main input field
        pygame.draw.rect(self.screen, self.colors["panel"], name_input_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors["accent"], name_input_rect, 3, border_radius=8)
        
        if world_name:
            name_text = self.font.render(world_name, True, self.colors["text"])
            self.screen.blit(name_text, (name_input_rect.x + 15, name_input_rect.y + 15))
        else:
            placeholder = self.font.render("Enter world name...", True, self.colors["text_dim"])
            self.screen.blit(placeholder, (name_input_rect.x + 15, name_input_rect.y + 15))
        
        # Seed input with enhanced styling
        seed_label = self.font.render("🎲 Seed (optional):", True, self.colors["text"])
        self.screen.blit(seed_label, (200, 250))
        
        seed_input_rect = pygame.Rect(200, 280, 400, 50)
        # Input field glow
        pygame.draw.rect(self.screen, self.colors["panel_glow"], seed_input_rect, border_radius=8)
        # Main input field
        pygame.draw.rect(self.screen, self.colors["panel"], seed_input_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors["info"], seed_input_rect, 3, border_radius=8)
        
        if seed:
            seed_text = self.font.render(seed, True, self.colors["text"])
            self.screen.blit(seed_text, (seed_input_rect.x + 15, seed_input_rect.y + 15))
        else:
            placeholder = self.font.render("Leave empty for random...", True, self.colors["text_dim"])
            self.screen.blit(placeholder, (seed_input_rect.x + 15, seed_input_rect.y + 15))
        
        # Buttons
        button_y = 360
        
        # Create world button
        create_btn = self._draw_button("🚀 Create World", 200, button_y, mouse_pos, self.colors["success"])
        
        # Back button
        back_btn = self._draw_button("⬅️ Back", 500, button_y, mouse_pos, self.colors["button"])
        
        return {
            "create_world": create_btn,
            "back": back_btn,
            "name_input": name_input_rect,
            "seed_input": seed_input_rect,

        }
    
    def draw_world_deletion_confirmation(self, world_name: str, mouse_pos: tuple) -> Dict[str, any]:
        """Draw world deletion confirmation dialog"""
        # Dim background
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Confirmation dialog
        dialog_width = 500
        dialog_height = 300
        dialog_x = (self.screen.get_width() - dialog_width) // 2
        dialog_y = (self.screen.get_height() - dialog_height) // 2
        
        # Dialog background
        pygame.draw.rect(self.screen, self.colors["panel"], (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, self.colors["text"], (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        # Warning text
        warning_text = self.big_font.render("⚠️ Delete World?", True, self.colors["danger"])
        warning_x = dialog_x + (dialog_width - warning_text.get_width()) // 2
        self.screen.blit(warning_text, (warning_x, dialog_y + 30))
        
        # World name
        name_text = self.font.render(f"World: {world_name}", True, self.colors["text"])
        name_x = dialog_x + (dialog_width - name_text.get_width()) // 2
        self.screen.blit(name_text, (name_x, dialog_y + 80))
        
        # Warning message
        msg_text = self.font.render("This action cannot be undone!", True, self.colors["text_secondary"])
        msg_x = dialog_x + (dialog_width - msg_text.get_width()) // 2
        self.screen.blit(msg_text, (msg_x, dialog_y + 120))
        
        # Buttons
        button_y = dialog_y + 180
        
        # Delete button
        delete_btn = self._draw_button("🗑️ Delete", dialog_x + 50, button_y, mouse_pos, self.colors["danger"])
        
        # Cancel button
        cancel_btn = self._draw_button("❌ Cancel", dialog_x + 300, button_y, mouse_pos, self.colors["button"])
        
        return {
            "delete": delete_btn,
            "cancel": cancel_btn
        }
    
    def handle_world_selection_click(self, button_states: Dict, mouse_pos: tuple) -> Optional[str]:
        """Handle clicks in the world selection screen"""
        for button_name, button_rect in button_states.items():
            if button_rect.collidepoint(mouse_pos):
                if button_name.startswith("world_"):
                    # Select world
                    world_index = int(button_name.split("_")[1])
                    self.selected_world_index = world_index
                    return "world_selected"
                
                elif button_name == "play_world":
                    return "play_world"
                
                elif button_name == "delete_world":
                    return "delete_world"
                
                elif button_name == "create_world":
                    return "create_world"
                
                elif button_name == "back":
                    return "back"
                
                elif button_name == "prev_page":
                    self.current_page = max(0, self.current_page - 1)
                    return "page_changed"
                
                elif button_name == "next_page":
                    self.current_page += 1
                    return "page_changed"
        
        return None
    
    def get_selected_world(self) -> Optional[Dict]:
        """Get the currently selected world"""
        worlds = self.world_system.get_world_list()
        if 0 <= self.selected_world_index < len(worlds):
            return worlds[self.selected_world_index]
        return None
    
    def reset_selection(self):
        """Reset the world selection"""
        self.selected_world_index = 0
        self.current_page = 0
    
    def handle_mouse_click(self, mouse_pos: tuple, world_rects: Dict) -> tuple:
        """Handle mouse clicks and return (action, world_name, new_selection)"""
        for button_name, button_rect in world_rects.items():
            if button_rect.collidepoint(mouse_pos):
                if button_name.startswith("world_"):
                    # Select world
                    world_index = int(button_name.split("_")[1])
                    self.selected_world_index = world_index
                    return "select", None, world_index
                
                elif button_name == "play_world":
                    selected_world = self.get_selected_world()
                    return "play", selected_world["name"] if selected_world else None, None
                
                elif button_name == "delete_world":
                    selected_world = self.get_selected_world()
                    return "delete", selected_world["name"] if selected_world else None, None
                
                elif button_name == "create_world":
                    return "create", None, None
                
                elif button_name == "back":
                    return "back", None, None
                
                elif button_name == "prev_page":
                    self.current_page = max(0, self.current_page - 1)
                    return "page_changed", None, None
                
                elif button_name == "next_page":
                    self.current_page += 1
                    return "page_changed", None, None
        
        return "none", None, None
    
    def handle_button_click(self, mouse_pos: tuple) -> tuple:
        """Handle button clicks and return (action, world_name)"""
        # This method is called from the main game loop
        # We'll use the handle_mouse_click method instead
        action, world_name, new_selection = self.handle_mouse_click(mouse_pos, {})
        return action, world_name
    
    def handle_scroll(self, scroll_amount: int):
        """Handle mouse wheel scrolling"""
        # Scroll through pages
        if scroll_amount > 0 and self.current_page > 0:
            self.current_page -= 1
        elif scroll_amount < 0:
            # Check if there are more pages
            worlds = self.world_system.get_world_list()
            max_pages = (len(worlds) - 1) // self.worlds_per_page
            if self.current_page < max_pages:
                self.current_page += 1
    
    def _draw_gradient_background(self):
        """Draw a beautiful gradient background"""
        # Main background
        self.screen.fill(self.colors["background"])
        
        # Gradient overlay
        for y in range(0, self.screen.get_height(), 2):
            alpha = int(255 * (1 - y / self.screen.get_height()) * 0.3)
            color = tuple(int(c * (1 - y / self.screen.get_height() * 0.2)) for c in self.colors["background_gradient"])
            pygame.draw.line(self.screen, color, (0, y), (self.screen.get_width(), y))
    
    def _draw_decorative_elements(self):
        """Draw decorative UI elements"""
        # Corner accents
        accent_size = 60
        accent_color = self.colors["accent"]
        
        # Top-left corner
        pygame.draw.polygon(self.screen, accent_color, [
            (0, 0), (accent_size, 0), (0, accent_size)
        ])
        
        # Top-right corner
        pygame.draw.polygon(self.screen, accent_color, [
            (self.screen.get_width(), 0), 
            (self.screen.get_width() - accent_size, 0), 
            (self.screen.get_width(), accent_size)
        ])
        
        # Bottom-left corner
        pygame.draw.polygon(self.screen, accent_color, [
            (0, self.screen.get_height()), 
            (accent_size, self.screen.get_height()), 
            (0, self.screen.get_height() - accent_size)
        ])
        
        # Bottom-right corner
        pygame.draw.polygon(self.screen, accent_color, [
            (self.screen.get_width(), self.screen.get_height()), 
            (self.screen.get_width() - accent_size, self.screen.get_height()), 
            (self.screen.get_width(), self.screen.get_height() - accent_size)
        ])
        
        # Subtle grid pattern
        grid_color = tuple(int(c * 0.1) for c in self.colors["accent"])
        for x in range(0, self.screen.get_width(), 100):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.screen.get_height()), 1)
        for y in range(0, self.screen.get_height(), 100):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.screen.get_width(), y), 1)
