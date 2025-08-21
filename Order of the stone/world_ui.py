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
    
    def draw_world_selection(self, mouse_pos: tuple) -> Dict[str, any]:
        """Draw the world selection screen and return button states"""
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
        
        # Action buttons
        action_y = nav_y + 80
        
        if worlds:
            # Play selected world
            play_btn = self._draw_button("▶️ Play World", 200, action_y, mouse_pos, self.colors["success"])
            button_states["play_world"] = play_btn
            
            # Delete selected world
            delete_btn = self._draw_button("🗑️ Delete World", 400, action_y, mouse_pos, self.colors["danger"])
            button_states["delete_world"] = delete_btn
            
            # Create new world
            create_btn = self._draw_button("✨ Create New World", 600, action_y, mouse_pos, self.colors["success"])
            button_states["create_world"] = create_btn
        
        # Back button
        back_btn = self._draw_button("⬅️ Back to Title", 400, action_y + 80, mouse_pos, self.colors["button"])
        button_states["back"] = back_btn
        
        return button_states
    
    def _draw_world_button(self, world: Dict, y_pos: int, mouse_pos: tuple, is_selected: bool, is_current: bool) -> pygame.Rect:
        """Draw a world selection button with enhanced visual effects"""
        # Button background with rounded corners effect
        btn_rect = pygame.Rect(50, y_pos, self.screen.get_width() - 100, self.button_height)
        
        # Determine button color and effects
        if is_current:
            base_color = self.colors["accent"]
            glow_color = self.colors["accent_glow"]
            border_color = self.colors["accent"]
        elif is_selected:
            base_color = self.colors["button_selected"]
            glow_color = self.colors["button_glow"]
            border_color = self.colors["text"]
        elif btn_rect.collidepoint(mouse_pos):
            base_color = self.colors["button_hover"]
            glow_color = self.colors["button_glow"]
            border_color = self.colors["text"]
        else:
            base_color = self.colors["button"]
            glow_color = self.colors["button"]
            border_color = self.colors["text_dim"]
        
        # Draw button glow effect
        glow_rect = pygame.Rect(btn_rect.x - 2, btn_rect.y - 2, btn_rect.width + 4, btn_rect.height + 4)
        pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=8)
        
        # Draw main button
        pygame.draw.rect(self.screen, base_color, btn_rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, btn_rect, 3, border_radius=6)
        
        # Add subtle inner highlight
        highlight_rect = pygame.Rect(btn_rect.x + 2, btn_rect.y + 2, btn_rect.width - 4, btn_rect.height // 2)
        highlight_color = tuple(min(255, int(c * 1.2)) for c in base_color)
        pygame.draw.rect(self.screen, highlight_color, highlight_rect, border_radius=4)
        
        # World name with enhanced typography
        name_text = self.font.render(world["name"], True, self.colors["text"])
        self.screen.blit(name_text, (btn_rect.x + 20, btn_rect.y + 12))
        
        # World info with better formatting
        seed_text = f"🌱 Seed: {world['seed']}"
        created_text = f"📅 {self._format_time(world['created'])}"
        
        seed_surface = self.font.render(seed_text, True, self.colors["text_secondary"])
        created_surface = self.font.render(created_text, True, self.colors["text_dim"])
        
        self.screen.blit(seed_surface, (btn_rect.x + 20, btn_rect.y + 32))
        self.screen.blit(created_surface, (btn_rect.x + 20, btn_rect.y + 48))
        
        # Current world indicator with badge
        if is_current:
            # Badge background
            badge_rect = pygame.Rect(btn_rect.right - 120, btn_rect.y + 8, 100, 20)
            pygame.draw.rect(self.screen, self.colors["accent"], badge_rect, border_radius=10)
            pygame.draw.rect(self.screen, self.colors["text"], badge_rect, 2, border_radius=10)
            
            # Badge text
            current_text = self.font.render("⭐ CURRENT", True, self.colors["text"])
            text_x = badge_rect.x + (badge_rect.width - current_text.get_width()) // 2
            text_y = badge_rect.y + (badge_rect.height - current_text.get_height()) // 2
            self.screen.blit(current_text, (text_x, text_y))
        
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
        button_y = 380
        
        # Create world button
        create_btn = self._draw_button("🚀 Create World", 200, button_y, mouse_pos, self.colors["success"])
        
        # Back button
        back_btn = self._draw_button("⬅️ Back", 500, button_y, mouse_pos, self.colors["button"])
        
        return {
            "create_world": create_btn,
            "back": back_btn,
            "name_input": name_input_rect,
            "seed_input": seed_input_rect
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
