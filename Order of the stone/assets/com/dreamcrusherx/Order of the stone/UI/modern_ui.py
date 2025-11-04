#!/usr/bin/env python3
"""
🎨 Modern UI System for Order of the Stone
Beautiful, consistent design across all game screens
"""

import pygame
import time
from typing import Dict, List, Optional, Tuple, Callable

class ModernUI:
    """Modern UI system with consistent beautiful design"""
    
    def __init__(self, screen: pygame.Surface, font, small_font, title_font, big_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.title_font = title_font
        self.big_font = big_font
        
        # Scrolling state for about page
        self.about_scroll_offset = 0
        
        # Modern color scheme
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
            "info_glow": (120, 220, 255),
            "warning": (255, 165, 0),
            "warning_glow": (255, 185, 20)
        }
        
        # Button dimensions
        self.button_width = 300
        self.button_height = 60
        self.button_spacing = 20
        
        # Animation state
        self.animation_time = 0
        self.hover_effects = {}
        
        # Splash text - fun random messages!
        self.splash_texts = [
            "Order Up!",
            "Made in California!",
            "Now with weather!",
            "Dig deep!",
            "Build high!",
            "Explore everywhere!",
            "Epic adventures await!",
            "Craft amazing things!",
            "Mine diamonds!",
            "Fight monsters!",
            "Team Banana Labs!",
            "Beta version!",
            "Torches light the way!",
            "Watch out for lightning!",
            "Snow is coming!",
            "Sunset is beautiful!",
            "Moonlight shines!",
            "Discover fortresses!",
            "Eat to survive!",
            "Build your dream!",
            "Unlimited creativity!",
            "Made with love!"
        ]
        import random
        self.current_splash = random.choice(self.splash_texts)
    
    def update(self, dt: float):
        """Update UI animations"""
        self.animation_time += dt
    
    def draw_gradient_background(self):
        """Draw beautiful gradient background"""
        # Main background
        self.screen.fill(self.colors["background"])
        
        # Gradient overlay
        for y in range(0, self.screen.get_height(), 2):
            alpha = int(255 * (1 - y / self.screen.get_height()) * 0.3)
            color = tuple(int(c * (1 - y / self.screen.get_height() * 0.2)) for c in self.colors["background_gradient"])
            pygame.draw.line(self.screen, color, (0, y), (self.screen.get_width(), y))
    
    def draw_decorative_elements(self):
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
    
    def draw_title_screen(self, mouse_pos: tuple) -> Dict[str, pygame.Rect]:
        """Draw beautiful title screen"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title with glow effect - April Fools' Day easter egg!
        import datetime
        today = datetime.date.today()
        is_april_fools = today.month == 4 and today.day == 1
        
        title_text = "Doritos of the Stone" if is_april_fools else "Order of the Stone"
        title = self.big_font.render(title_text, True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render(title_text, True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 3, 53))
        self.screen.blit(title, (title_x, 50))
        
        # Subtitle
        subtitle = self.title_font.render("Your Adventure Awaits", True, self.colors["text_secondary"])
        subtitle_x = (self.screen.get_width() - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (subtitle_x, 120))
        
        # Animated splash text (yellow, tilted, pulsing) - positioned next to title
        import math
        pulse = abs(math.sin(time.time() * 3))  # Pulse between 0 and 1 (3x per second)
        splash_size = int(28 + pulse * 10)  # Size pulses between 28 and 38 (smaller)
        splash_font = pygame.font.Font(None, splash_size)
        splash_surface = splash_font.render(self.current_splash, True, (255, 215, 0))  # Bright yellow/gold
        
        # Rotate the splash text (tilted)
        angle = -18 + math.sin(time.time() * 2) * 4  # Wiggle between -22 and -14 degrees
        rotated_splash = pygame.transform.rotate(splash_surface, angle)
        
        # Position directly overlapping on the game title
        splash_x = title_x + title.get_width() - 80
        splash_y = 55
        
        # Add bright glow effect to make it pop
        glow_splash = splash_font.render(self.current_splash, True, (255, 255, 100))  # Brighter glow
        rotated_glow = pygame.transform.rotate(glow_splash, angle)
        self.screen.blit(rotated_glow, (splash_x + 3, splash_y + 3))
        
        # Draw the splash text
        self.screen.blit(rotated_splash, (splash_x, splash_y))
        
        # Buttons with enhanced styling
        button_states = {}
        button_y = 250
        spacing = 80
        
        buttons = [
            ("Play", "play", self.colors["success"]),
            # ("Multiplayer", "multiplayer", (100, 100, 255)),  # Disabled for now - will add back later
            ("Achievements", "achievements", self.colors["accent"]),
            ("Username", "username", self.colors["info"]),
            ("Controls", "controls", self.colors["button"]),
            ("About", "about", self.colors["button"]),
            ("Options", "options", self.colors["button"]),
            ("Credits", "credits", self.colors["accent"]),
            ("Quit", "quit", self.colors["danger"])
        ]
        
        for i, (text, action, color) in enumerate(buttons):
            y_pos = button_y + i * spacing
            btn_rect = self.draw_modern_button(text, y_pos, mouse_pos, color)
            button_states[action] = btn_rect
        
        # Version info
        version_text = self.small_font.render("v1.3.1 Beta - Modern UI Edition", True, self.colors["text_dim"])
        self.screen.blit(version_text, (10, self.screen.get_height() - 30))
        
        # Copyright text - Bottom right corner
        copyright_bottom_text = self.small_font.render("Copyright © 2025 Team Banana Labs Studios. All rights reserved.", True, self.colors["text_dim"])
        copyright_bottom_x = self.screen.get_width() - copyright_bottom_text.get_width() - 10
        copyright_bottom_y = self.screen.get_height() - 30
        self.screen.blit(copyright_bottom_text, (copyright_bottom_x, copyright_bottom_y))
        
        return button_states
    
    def draw_modern_button(self, text: str, y: int, mouse_pos: tuple, base_color: tuple) -> pygame.Rect:
        """Draw a modern button with enhanced effects"""
        btn_rect = pygame.Rect((self.screen.get_width() - self.button_width) // 2, y, self.button_width, self.button_height)
        
        # Check hover and determine colors
        is_hovered = btn_rect.collidepoint(mouse_pos)
        if is_hovered:
            color = tuple(min(255, c + 40) for c in base_color)
            glow_color = tuple(min(255, c + 60) for c in base_color)
            border_color = self.colors["text"]
            # Store hover state for animations
            self.hover_effects[text] = True
        else:
            color = base_color
            glow_color = base_color
            border_color = self.colors["text_dim"]
            self.hover_effects[text] = False
        
        # Draw button glow effect
        glow_rect = pygame.Rect(btn_rect.x - 4, btn_rect.y - 4, btn_rect.width + 8, btn_rect.height + 8)
        pygame.draw.rect(self.screen, glow_color, glow_rect, border_radius=15)
        
        # Draw main button with rounded corners
        pygame.draw.rect(self.screen, color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, btn_rect, 3, border_radius=12)
        
        # Add inner highlight for 3D effect
        highlight_rect = pygame.Rect(btn_rect.x + 4, btn_rect.y + 4, btn_rect.width - 8, btn_rect.height // 2)
        highlight_color = tuple(min(255, int(c * 1.4)) for c in color)
        pygame.draw.rect(self.screen, highlight_color, highlight_rect, border_radius=10)
        
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
    
    def draw_pause_menu(self, mouse_pos: tuple) -> Dict[str, pygame.Rect]:
        """Draw beautiful pause menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill(self.colors["background"])
        self.screen.blit(overlay, (0, 0))
        
        # Menu panel
        panel_width = 400
        panel_height = 300
        panel_x = (self.screen.get_width() - panel_width) // 2
        panel_y = (self.screen.get_height() - panel_height) // 2
        
        # Panel glow
        glow_rect = pygame.Rect(panel_x - 4, panel_y - 4, panel_width + 8, panel_height + 8)
        pygame.draw.rect(self.screen, self.colors["accent_glow"], glow_rect, border_radius=20)
        
        # Main panel
        pygame.draw.rect(self.screen, self.colors["panel"], (panel_x, panel_y, panel_width, panel_height), border_radius=18)
        pygame.draw.rect(self.screen, self.colors["accent"], (panel_x, panel_y, panel_width, panel_height), 3, border_radius=18)
        
        # Title
        title = self.title_font.render("⏸️ Game Paused", True, self.colors["text"])
        title_x = panel_x + (panel_width - title.get_width()) // 2
        self.screen.blit(title, (title_x, panel_y + 30))
        
        # Buttons
        button_states = {}
        button_y = panel_y + 120
        spacing = 70
        
        buttons = [
            ("Resume", "resume", self.colors["success"]),
            ("Save Game", "save", self.colors["info"]),
            ("Quit to Title", "quit", self.colors["danger"])
        ]
        
        for i, (text, action, color) in enumerate(buttons):
            y_pos = button_y + i * spacing
            btn_rect = self.draw_modern_button(text, y_pos, mouse_pos, color)
            button_states[action] = btn_rect
        
        return button_states
    
    def draw_shop_ui(self, mouse_pos: tuple, player_coins: int) -> Dict[str, pygame.Rect]:
        """Draw beautiful shop interface"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("🏪 Shop", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("🏪 Shop", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Coins display
        coins_text = self.title_font.render(f"💰 {player_coins} Coins", True, self.colors["accent"])
        coins_x = (self.screen.get_width() - coins_text.get_width()) // 2
        self.screen.blit(coins_text, (coins_x, 120))
        
        # Shop items would go here...
        # For now, just a close button
        close_btn = self.draw_modern_button("Close Shop", 400, mouse_pos, self.colors["button"])
        
        return {"close": close_btn}
    
    def draw_controls_screen(self, mouse_pos: tuple) -> Dict[str, pygame.Rect]:
        """Draw beautiful controls screen"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("🎮 Controls", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("🎮 Controls", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Controls text
        controls = [
            "A/D - Move Left/Right",
            "Space - Jump",
            "1-9 - Select Item",
            "Left Click - Break Block / Attack",
            "Right Click - Place Block",
            "E - Open Chests",
            "H - Chat",
            "I - Inventory",
            "L - Achievements",
            "B - Test Block Breaking",
            "F3 - Toggle FPS Display",
            "F11 - Toggle Fullscreen"
        ]
        
        y_start = 150
        for i, control in enumerate(controls):
            control_text = self.font.render(control, True, self.colors["text_secondary"])
            self.screen.blit(control_text, (100, y_start + i * 30))
        
        # Back button
        back_btn = self.draw_modern_button("⬅️ Back to Title", 500, mouse_pos, self.colors["button"])
        
        return {"back": back_btn}

    def draw_about_screen(self, mouse_pos: tuple) -> Dict[str, pygame.Rect]:
        """Draw beautiful about screen with mouse wheel scrolling"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("ℹ️ About", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("ℹ️ About", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # About text with scroll offset
        y_start = 120 - self.about_scroll_offset
        
        about_texts = [
            "Order of the Stone",
            "A 2D Minecraft-inspired adventure game",
            "",
            "Features:",
            "• Procedural world generation",
            "• Fortress exploration & weather system",
            "• Crafting system (see recipes below)",
            "• Beautiful modern UI"
        ]
        
        for i, text in enumerate(about_texts):
            y_pos = y_start + i * 25
            # Only draw if visible on screen
            if 100 < y_pos < 520:
                if text.startswith("•"):
                    color = self.colors["accent"]
                elif text in ["Features:", "Order of the Stone"]:
                    color = self.colors["text"]
                else:
                    color = self.colors["text_secondary"]
                
                text_surface = self.font.render(text, True, color)
                self.screen.blit(text_surface, (50, y_pos))
        
        # Crafting Recipes Section
        recipes_y = y_start + len(about_texts) * 25 + 20
        recipes_title = self.font.render("🔨 Crafting Recipes:", True, self.colors["accent"])
        if 100 < recipes_y < 520:
            self.screen.blit(recipes_title, (50, recipes_y))
        
        # Display ALL crafting recipes
        recipes = [
            "📦 BUILDING MATERIALS:",
            "  1 Log → 4 Oak Planks",
            "  2 Stone + 1 Coal → 4 Red Bricks",
            "",
            "⛏️ TOOLS:",
            "  2 Oak Planks → Pickaxe",
            "",
            "⚔️ WEAPONS:",
            "  3 Oak Planks → Sword",
            "  3 Stone + 1 Oak Plank → Stone Sword",
            "",
            "🏠 FURNITURE & UTILITY:",
            "  4 Oak Planks → Chest",
            "  10 Oak Planks → Door",
            "  3 Oak Planks + 2 Leaves → Bed",
            "  5 Oak Planks → 3 Ladders",
            "  1 Coal + 1 Oak Plank → 4 Torches",
            "",
            "🍞 FOOD:",
            "  3 Wheat → Bread",
            "  1 Coal + 1 Beef → Steak (cook raw beef)"
        ]
        
        recipe_y = recipes_y + 30
        for i, recipe in enumerate(recipes):
            y_pos = recipe_y + i * 20
            # Only draw if visible on screen
            if 100 < y_pos < 520:
                if recipe.strip() == "":
                    continue  # Skip blank lines
                    
                # Color coding
                if recipe.startswith("📦") or recipe.startswith("⛏️") or recipe.startswith("⚔️") or recipe.startswith("🏠") or recipe.startswith("🍞"):
                    color = self.colors["accent"]  # Category headers
                else:
                    color = self.colors["text_secondary"]  # Recipe entries
                
                recipe_text = self.small_font.render(recipe, True, color)
                self.screen.blit(recipe_text, (50, y_pos))
        
        # Scroll hint
        scroll_hint = self.small_font.render("🖱️ Use mouse wheel to scroll", True, self.colors["text_dim"])
        self.screen.blit(scroll_hint, (self.screen.get_width() - scroll_hint.get_width() - 20, 105))
        
        # Back button
        back_btn = self.draw_modern_button("⬅️ Back to Title", 540, mouse_pos, self.colors["button"])
        
        return {"back": back_btn}
    
    def handle_about_scroll(self, scroll_amount: int):
        """Handle scrolling in about page"""
        self.about_scroll_offset -= scroll_amount * 30  # 30 pixels per scroll
        # Clamp scroll offset (allow scrolling down far enough to see all content)
        self.about_scroll_offset = max(0, min(300, self.about_scroll_offset))  # Max 300px scroll

    def draw_options_screen(self, mouse_pos: tuple, fullscreen: bool = False, fps_limit: int = 60, music_enabled: bool = True) -> Dict[str, pygame.Rect]:
        """Draw beautiful options screen"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("⚙️ Options", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("⚙️ Options", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Options
        fullscreen_text = f"🖥️ Fullscreen: {'On' if fullscreen else 'Off'}"
        fps_text = f"🎯 FPS Limit: {fps_limit if fps_limit > 0 else 'Unlimited'}"
        music_text = f"🎵 Music: {'On' if music_enabled else 'Off'}"
        
        fullscreen_surface = self.font.render(fullscreen_text, True, self.colors["text"])
        fps_surface = self.font.render(fps_text, True, self.colors["text"])
        music_surface = self.font.render(music_text, True, self.colors["text"])
        
        self.screen.blit(fullscreen_surface, (100, 150))
        self.screen.blit(fps_surface, (100, 200))
        self.screen.blit(music_surface, (100, 250))
        
        # Buttons
        fullscreen_btn = self.draw_modern_button("Toggle Fullscreen", 300, mouse_pos, self.colors["info"])
        fps_btn = self.draw_modern_button("Change FPS", 400, mouse_pos, self.colors["warning"])
        music_btn = self.draw_modern_button("Toggle Music", 450, mouse_pos, self.colors["success"])
        website_btn = self.draw_modern_button("🌐 Visit Website", 550, mouse_pos, self.colors["accent"])
        back_btn = self.draw_modern_button("⬅️ Back to Title", 650, mouse_pos, self.colors["button"])
        
        return {
            "fullscreen": fullscreen_btn,
            "fps": fps_btn,
            "music": music_btn,
            "website": website_btn,
            "back": back_btn
        }
    
    def draw_shop_ui(self, mouse_pos: tuple, player_coins: int, current_character: dict = None) -> Dict[str, pygame.Rect]:
        """Draw beautiful character shop interface"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("🎭 Character Selection", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("🎭 Character Selection", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Coins display
        coins_text = self.title_font.render(f"💰 {player_coins} Coins", True, self.colors["accent"])
        coins_x = (self.screen.get_width() - coins_text.get_width()) // 2
        self.screen.blit(coins_text, (coins_x, 120))
        
        # Character preview area (center)
        preview_size = 120
        preview_x = (self.screen.get_width() - preview_size) // 2
        preview_y = 180
        
        # Draw character preview box with glow
        glow_rect = pygame.Rect(preview_x - 4, preview_y - 4, preview_size + 8, preview_size + 8)
        pygame.draw.rect(self.screen, self.colors["accent_glow"], glow_rect, border_radius=15)
        
        pygame.draw.rect(self.screen, self.colors["panel"], (preview_x, preview_y, preview_size, preview_size), border_radius=12)
        pygame.draw.rect(self.screen, self.colors["accent"], (preview_x, preview_y, preview_size, preview_size), 3, border_radius=12)
        
        # Character info would go here...
        if current_character:
            char_name = self.font.render(current_character.get('name', 'Unknown').title(), True, self.colors["text"])
            self.screen.blit(char_name, (preview_x + (preview_size - char_name.get_width()) // 2, preview_y + preview_size + 10))
            
            desc_text = self.font.render(current_character.get('description', 'No description'), True, self.colors["text_secondary"])
            self.screen.blit(desc_text, (preview_x + (preview_size - desc_text.get_width()) // 2, preview_y + preview_size + 35))
            
            if current_character.get('price', 0) > 0:
                price_text = self.font.render(f"💰 {current_character['price']} coins", True, self.colors["accent"])
                self.screen.blit(price_text, (preview_x + (preview_size - price_text.get_width()) // 2, preview_y + preview_size + 60))
            else:
                price_text = self.font.render("FREE", True, self.colors["success"])
                self.screen.blit(price_text, (preview_x + (preview_size - price_text.get_width()) // 2, preview_y + preview_size + 60))
        
        # Navigation buttons
        arrow_size = 50
        left_arrow = pygame.Rect(preview_x - arrow_size - 30, preview_y + preview_size // 2 - arrow_size // 2, arrow_size, arrow_size)
        right_arrow = pygame.Rect(preview_x + preview_size + 30, preview_y + preview_size // 2 - arrow_size // 2, arrow_size, arrow_size)
        
        # Draw arrows with modern styling
        pygame.draw.rect(self.screen, self.colors["info"], left_arrow, border_radius=10)
        pygame.draw.rect(self.screen, self.colors["info"], right_arrow, border_radius=10)
        pygame.draw.rect(self.screen, self.colors["text"], left_arrow, 3, border_radius=10)
        pygame.draw.rect(self.screen, self.colors["text"], right_arrow, 3, border_radius=10)
        
        # Arrow text
        left_text = self.font.render("←", True, self.colors["text"])
        right_text = self.font.render("→", True, self.colors["text"])
        self.screen.blit(left_text, (left_arrow.x + 18, left_arrow.y + 12))
        self.screen.blit(right_text, (right_arrow.x + 18, right_arrow.y + 12))
        
        # Action buttons
        button_y = preview_y + preview_size + 120
        select_btn = self.draw_modern_button("Select Character", button_y, mouse_pos, self.colors["success"])
        close_btn = self.draw_modern_button("Close Shop", button_y + 80, mouse_pos, self.colors["button"])
        
        return {
            "left_arrow": left_arrow,
            "right_arrow": right_arrow,
            "select": select_btn,
            "close": close_btn
        }
    
    def draw_credits_screen(self, mouse_pos: tuple) -> Dict[str, pygame.Rect]:
        """Draw beautiful credits screen"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("🎬 Credits", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("🎬 Credits", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Credits content
        credits_text = [
            "Made by Team Banana Labs",
            "",
            "Development Team:",
            "• DreamCrusherX - Lead Developer",
            "• Team Banana Labs - Studio Lead",
            "",
            "Special Thanks:",
            "• Pygame Community",
            "• Python Developers",
            "• All Beta Testers",
            "",
            "Version 1.3.1 Beta",
            "© 2025 Team Banana Labs"
        ]
        
        # Draw credits text
        y_offset = 150
        for line in credits_text:
            if line == "Made by Team Banana Labs":
                text_surface = self.title_font.render(line, True, self.colors["accent"])
            elif line.startswith("•"):
                text_surface = self.font.render(line, True, self.colors["text_secondary"])
            elif line == "":
                text_surface = None
            else:
                text_surface = self.font.render(line, True, self.colors["text"])
            
            if text_surface:
                text_x = (self.screen.get_width() - text_surface.get_width()) // 2
                self.screen.blit(text_surface, (text_x, y_offset))
            
            y_offset += 30
        
        # Back button
        back_btn = self.draw_modern_button("Back", self.screen.get_height() - 100, mouse_pos, self.colors["button"])
        
        return {
            "back": back_btn
        }

    def draw_achievements_screen(self, mouse_pos: tuple, achievements_data: dict, scroll_offset: int = 0) -> Dict[str, pygame.Rect]:
        """Draw beautiful achievements screen with scrolling"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        # Local alias to satisfy static analyzers
        ach = achievements_data or {}
        
        # Title
        title = self.big_font.render("🏆 Achievements", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        self.screen.blit(title, (title_x, 50))
        
        # Achievement categories
        categories = {
            "Mining": ["first_diamond", "first_gold", "first_iron", "first_coal"],
            "Combat": ["first_monster_kill", "monster_hunter", "zombie_slayer", "pigeon_hunter"],
            "Exploration": ["first_carrot", "first_sleep", "explorer", "fortress_finder"],
            "Building": ["first_torch", "builder"],
            "Special": ["night_survivor", "ultimate_achievement"]
        }
        
        # Achievement descriptions and rewards
        achievement_info = {
            "first_diamond": ("💎 First Diamond", "Mine your first diamond", 50),
            "first_gold": ("🥇 First Gold", "Mine your first gold ore", 25),
            "first_iron": ("⚒️ First Iron", "Mine your first iron ore", 15),
            "first_coal": ("⚫ First Coal", "Mine your first coal", 10),
            "first_monster_kill": ("⚔️ First Kill", "Defeat your first monster", 30),
            "monster_hunter": ("👹 Monster Hunter", "Defeat 10 monsters", 100),
            "zombie_slayer": ("🧟 Zombie Slayer", "Defeat 5 zombies", 75),
            "pigeon_hunter": ("🐦 Pigeon Hunter", "Defeat 3 mad pigeons", 50),
            "first_carrot": ("🥕 First Carrot", "Eat your first carrot", 15),
            "first_sleep": ("🛏️ First Sleep", "Sleep in a bed for the first time", 25),
            "explorer": ("🗺️ Explorer", "Walk 1000 blocks", 100),
            "fortress_finder": ("🏰 Fortress Finder", "Find a fortress", 200),
            "first_torch": ("🔥 First Torch", "Place your first torch", 20),
            "builder": ("🏗️ Builder", "Place 50 blocks", 150),
            "night_survivor": ("🌙 Night Survivor", "Survive 5 nights", 200),
            "ultimate_achievement": ("👑 Ultimate", "Complete the ultimate challenge", 1000)
        }
        
        # Draw achievements by category
        y_offset = 150 - scroll_offset  # Apply scroll offset
        category_colors = {
            "Mining": (255, 215, 0),      # Gold
            "Combat": (220, 20, 60),       # Crimson
            "Exploration": (34, 139, 34),  # Forest Green
            "Building": (255, 140, 0),     # Dark Orange
            "Special": (138, 43, 226)      # Blue Violet
        }
        
        # Calculate total content height to determine if scrolling is needed
        total_content_height = 0
        for category, achievement_list in categories.items():
            total_content_height += 40  # Category title
            total_content_height += len(achievement_list) * 70  # Achievements
            total_content_height += 20  # Space between categories
        
        # Only draw achievements that are visible on screen
        screen_height = self.screen.get_height()
        visible_start = scroll_offset
        visible_end = scroll_offset + screen_height - 200  # Leave space for title and back button
        
        for category, achievement_list in categories.items():
            # Only draw category title if it's visible
            if 150 <= y_offset <= screen_height - 100:
                category_title = self.title_font.render(f"📋 {category}", True, category_colors[category])
                self.screen.blit(category_title, (50, y_offset))
            y_offset += 40
            
            # Draw achievements in this category
            for achievement_id in achievement_list:
                if achievement_id in achievement_info:
                    name, description, reward = achievement_info[achievement_id]
                    is_unlocked = ach.get(achievement_id, False)
                    
                    # Only draw achievement if it's visible on screen
                    if 150 <= y_offset <= screen_height - 100:
                        # Achievement background
                        achievement_rect = pygame.Rect(50, y_offset, self.screen.get_width() - 100, 60)
                        if is_unlocked:
                            pygame.draw.rect(self.screen, (50, 150, 50), achievement_rect, border_radius=10)
                            pygame.draw.rect(self.screen, (100, 200, 100), achievement_rect, 3, border_radius=10)
                            status_icon = "✅"
                        else:
                            pygame.draw.rect(self.screen, (50, 50, 50), achievement_rect, border_radius=10)
                            pygame.draw.rect(self.screen, (100, 100, 100), achievement_rect, 3, border_radius=10)
                            status_icon = "❌"
                        
                        # Achievement text
                        achievement_text = f"{status_icon} {name}"
                        text_surface = self.font.render(achievement_text, True, self.colors["text"])
                        self.screen.blit(text_surface, (achievement_rect.x + 10, achievement_rect.y + 10))
                        
                        # Description
                        desc_surface = self.small_font.render(description, True, self.colors["text_secondary"])
                        self.screen.blit(desc_surface, (achievement_rect.x + 10, achievement_rect.y + 30))
                        
                        # Reward
                        reward_text = f"+{reward} coins"
                        reward_surface = self.small_font.render(reward_text, True, (255, 215, 0))
                        reward_x = achievement_rect.right - reward_surface.get_width() - 10
                        self.screen.blit(reward_surface, (reward_x, achievement_rect.y + 20))
                    
                    y_offset += 70
            
            y_offset += 20  # Space between categories
        
        # Back button
        back_btn = self.draw_modern_button("Back", self.screen.get_height() - 100, mouse_pos, self.colors["button"])
        
        return {
            "back": back_btn
        }

    def draw_multiplayer_screen(self, mouse_pos: tuple) -> Dict[str, pygame.Rect]:
        """Draw beautiful multiplayer screen"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("🌐 Multiplayer", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("🌐 Multiplayer", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Subtitle
        subtitle = self.font.render("Connect with other players", True, self.colors["text_secondary"])
        subtitle_x = (self.screen.get_width() - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (subtitle_x, 120))
        
        # Buttons
        button_y = 200
        spacing = 80
        
        host_btn = self.draw_modern_button("🏠 Host Server", button_y, mouse_pos, self.colors["success"])
        join_btn = self.draw_modern_button("🔗 Join Server", button_y + spacing, mouse_pos, self.colors["info"])
        back_btn = self.draw_modern_button("⬅️ Back to Title", button_y + spacing * 2, mouse_pos, self.colors["button"])
        
        return {
            "host": host_btn,
            "join": join_btn,
            "back": back_btn
        }
    
    def draw_username_screen(self, mouse_pos: tuple, current_username: str = "") -> Dict[str, pygame.Rect]:
        """Draw beautiful username creation screen"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Title
        title = self.big_font.render("👤 Username", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("👤 Username", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Subtitle
        subtitle = self.title_font.render("Choose your player identity", True, self.colors["text_secondary"])
        subtitle_x = (self.screen.get_width() - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (subtitle_x, 120))
        
        # Username input field
        input_label = self.font.render("Username:", True, self.colors["text"])
        self.screen.blit(input_label, (200, 200))
        
        input_rect = pygame.Rect(200, 230, 400, 50)
        # Input field glow
        pygame.draw.rect(self.screen, self.colors["panel_glow"], input_rect, border_radius=8)
        # Main input field
        pygame.draw.rect(self.screen, self.colors["panel"], input_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors["accent"], input_rect, 3, border_radius=8)
        
        if current_username:
            username_text = self.font.render(current_username, True, self.colors["text"])
            self.screen.blit(username_text, (input_rect.x + 15, input_rect.y + 15))
        else:
            placeholder = self.font.render("Enter username...", True, self.colors["text_dim"])
            self.screen.blit(placeholder, (input_rect.x + 15, input_rect.y + 15))
        
        # Buttons
        button_y = 320
        spacing = 80
        
        save_btn = self.draw_modern_button("💾 Save Username", button_y, mouse_pos, self.colors["success"])
        back_btn = self.draw_modern_button("⬅️ Back to Title", button_y + spacing, mouse_pos, self.colors["button"])
        
        return {
            "save": save_btn,
            "back": back_btn,
            "input": input_rect
        }
    
    def draw_multiplayer_screen(self, mouse_pos: tuple, achievements_data: dict = None) -> Dict[str, pygame.Rect]:
        """Draw beautiful multiplayer screen"""
        # Enhanced background
        self.draw_gradient_background()
        self.draw_decorative_elements()
        
        # Local alias for achievements data
        ach = achievements_data or {}
        
        # Title
        title = self.big_font.render("🏆 Achievements", True, self.colors["text"])
        title_x = (self.screen.get_width() - title.get_width()) // 2
        
        # Title glow
        glow_surface = self.big_font.render("🏆 Achievements", True, self.colors["accent_glow"])
        self.screen.blit(glow_surface, (title_x + 2, 52))
        self.screen.blit(title, (title_x, 50))
        
        # Subtitle
        subtitle = self.title_font.render("Track your progress and unlock rewards", True, self.colors["text_secondary"])
        subtitle_x = (self.screen.get_width() - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (subtitle_x, 120))
        
        # Achievement list
        y_start = 180
        spacing = 40
        
        # Define all possible achievements
        all_achievements = {
            # Mining Achievements
            "first_coal": ("⛏️ First Coal", "Mine your first coal block (+50 coins)", "Mined first coal!"),
            "first_iron": ("🔩 First Iron", "Mine your first iron block (+100 coins)", "Mined first iron!"),
            "first_gold": ("🥇 First Gold", "Mine your first gold block (+200 coins)", "Mined first gold!"),
            "first_diamond": ("💎 First Diamond", "Mine your first diamond block (+500 coins)", "Mined first diamond!"),
            
            # Exploration Achievements
            "first_village": ("🏘️ Village Finder", "Discover your first village (+100 coins)", "Found first village!"),
            "first_fortress": ("🏰 Fortress Explorer", "Discover your first fortress (+150 coins)", "Found first fortress!"),
            "first_chest": ("📦 Treasure Hunter", "Open your first chest (+75 coins)", "Opened first chest!"),
            "underground_explorer": ("🕳️ Underground Explorer", "Enter the underground fortress (+300 coins)", "Entered underground fortress!"),
            "world_explorer": ("🌍 World Explorer", "Travel far from spawn (+200 coins)", "Explored the world!"),
            
            # Combat Achievements
            "first_monster_kill": ("👹 Monster Slayer", "Defeat your first monster (+25 coins)", "Defeated first monster!"),
            "boss_fighter": ("🐉 Boss Fighter", "Start the boss battle (+500 coins)", "Started boss fight!"),
            "monster_hunter": ("⚔️ Monster Hunter", "Kill 10 monsters (+100 coins)", "Killed 10 monsters!"),
            
            # Survival Achievements
            "first_carrot": ("🥕 Vegetarian", "Eat your first carrot (+10 coins)", "Ate first carrot!"),
            "first_sleep": ("😴 Well Rested", "Sleep in a bed (+20 coins)", "Slept in bed!"),
            "health_master": ("❤️ Health Master", "Reach full health (+50 coins)", "Reached full health!"),
            
            # Social Achievements
            "first_villager_talk": ("💬 Social", "Talk to your first villager (+15 coins)", "Talked to villager!"),
            "first_legend_interaction": ("🌟 Legend", "Meet The Legend NPC (+100 coins)", "Met The Legend!"),
            
            # Crafting Achievements
            "crafting_master": ("🔨 Crafting Master", "Craft your first item (+50 coins)", "Crafted first item!"),
            "tool_maker": ("🛠️ Tool Maker", "Craft a pickaxe or sword (+25 coins)", "Crafted first tool!"),
            
            # Building Achievements
            "first_block_place": ("🧱 Builder", "Place your first block (+10 coins)", "Placed first block!"),
            
            # Special Achievements
            "bedrock_breaker": ("🏰 Bedrock Breaker", "Break through bedrock with Olympic Axe (+1000 coins)", "Broke through bedrock!"),
            "fortress_escape": ("🏰 Great Escape", "Escape the starting fortress (+100 coins)", "Escaped fortress!"),
            "diamond_chest": ("💎 Diamond Luck", "Find diamond in a chest (+1,000,000 coins)", "Found diamond in chest!"),
            "ultimate_achievement": ("🏆 Ultimate", "The ultimate achievement (+1,000,000 coins)", "Ultimate achievement!")
        }
        
        # Draw achievements
        for i, (achievement_id, (name, description, message)) in enumerate(all_achievements.items()):
            y_pos = y_start + i * spacing
            
            # Check if achievement is unlocked
            is_unlocked = ach.get(achievement_id, False)
            
            # Achievement box
            box_width = 600
            box_height = 35
            box_x = (self.screen.get_width() - box_width) // 2
            box_y = y_pos
            
            # Box colors based on unlock status
            if is_unlocked:
                box_color = self.colors["success"]
                border_color = self.colors["success_glow"]
                text_color = self.colors["text"]
                icon = "✅"
            else:
                box_color = self.colors["panel"]
                border_color = self.colors["text_dim"]
                text_color = self.colors["text_dim"]
                icon = "🔒"
            
            # Draw achievement box
            pygame.draw.rect(self.screen, box_color, (box_x, box_y, box_width, box_height), border_radius=8)
            pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_width, box_height), 2, border_radius=8)
            
            # Achievement icon and name
            icon_text = self.font.render(f"{icon} {name}", True, text_color)
            self.screen.blit(icon_text, (box_x + 10, box_y + 8))
            
            # Achievement description
            desc_text = self.small_font.render(description, True, text_color)
            self.screen.blit(desc_text, (box_x + 10, box_y + 20))
            
            # Progress indicator
            if is_unlocked:
                progress_text = self.small_font.render("COMPLETED", True, self.colors["success"])
            else:
                progress_text = self.small_font.render("LOCKED", True, self.colors["text_dim"])
            
            progress_x = box_x + box_width - progress_text.get_width() - 10
            self.screen.blit(progress_text, (progress_x, box_y + 8))
        
        # Back button
        back_btn = self.draw_modern_button("⬅️ Back to Game", 650, mouse_pos, self.colors["button"])
        
        return {"back": back_btn}
