import pygame
from world_manager import WorldManager
from typing import Optional, Tuple

class WorldUI:
    """UI for world selection and creation"""
    
    def __init__(self, screen_width: int, screen_height: int, font: pygame.font.Font):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.title_font = pygame.font.SysFont("Arial", 48)
        self.subtitle_font = pygame.font.SysFont("Arial", 24)
        
        # Colors
        self.BACKGROUND_COLOR = (50, 50, 50)
        self.TEXT_COLOR = (255, 255, 255)
        self.BUTTON_COLOR = (100, 100, 100)
        self.BUTTON_HOVER_COLOR = (150, 150, 150)
        self.BUTTON_DISABLED_COLOR = (70, 70, 70)
        self.INPUT_BG_COLOR = (80, 80, 80)
        self.INPUT_BORDER_COLOR = (120, 120, 120)
        self.WORLD_ITEM_COLOR = (90, 90, 90)
        self.WORLD_ITEM_HOVER_COLOR = (120, 120, 120)
        
        # Button dimensions
        self.BUTTON_WIDTH = 200
        self.BUTTON_HEIGHT = 50
        self.WORLD_ITEM_HEIGHT = 60
        self.INPUT_HEIGHT = 40
        
        # Scroll position for world list
        self.scroll_y = 0
        self.max_scroll = 0
        
    def center_x(self, width: int) -> int:
        """Center an element horizontally"""
        return (self.screen_width - width) // 2
    
    def draw_button(self, text: str, x: int, y: int, width: int = None, height: int = None, 
                   enabled: bool = True, hover: bool = False) -> pygame.Rect:
        """Draw a button and return its rect"""
        if width is None:
            width = self.BUTTON_WIDTH
        if height is None:
            height = self.BUTTON_HEIGHT
            
        # Choose color based on state
        if not enabled:
            color = self.BUTTON_DISABLED_COLOR
        elif hover:
            color = self.BUTTON_HOVER_COLOR
        else:
            color = self.BUTTON_COLOR
            
        # Draw button background
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(pygame.display.get_surface(), color, button_rect)
        pygame.draw.rect(pygame.display.get_surface(), self.TEXT_COLOR, button_rect, 2)
        
        # Draw button text
        text_surface = self.font.render(text, True, self.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=button_rect.center)
        pygame.display.get_surface().blit(text_surface, text_rect)
        
        return button_rect
    
    def draw_world_selection_screen(self, world_manager: WorldManager) -> Tuple[str, Optional[str]]:
        """
        Draw the world selection screen
        Returns: (action, world_name) where action is 'play', 'create', 'delete', or 'back'
        """
        screen = pygame.display.get_surface()
        screen.fill(self.BACKGROUND_COLOR)
        
        # Title
        title = self.title_font.render("Order of the Stone", True, self.TEXT_COLOR)
        title_rect = title.get_rect(center=(self.screen_width // 2, 80))
        screen.blit(title, title_rect)
        
        action = None
        world_name = None
        
        if world_manager.has_worlds():
            # Show existing worlds
            subtitle = self.subtitle_font.render("Select a World", True, self.TEXT_COLOR)
            subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 140))
            screen.blit(subtitle, subtitle_rect)
            
            # World list
            start_y = 180
            visible_height = self.screen_height - start_y - 120  # Leave space for buttons
            
            # Calculate scroll limits
            total_height = len(world_manager.worlds) * self.WORLD_ITEM_HEIGHT
            self.max_scroll = max(0, total_height - visible_height)
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            
            # Draw scrollable world list
            for i, world in enumerate(world_manager.worlds):
                item_y = start_y + i * self.WORLD_ITEM_HEIGHT - self.scroll_y
                
                # Only draw if visible
                if item_y + self.WORLD_ITEM_HEIGHT > start_y and item_y < start_y + visible_height:
                    # Check if mouse is hovering over this item
                    mouse_pos = pygame.mouse.get_pos()
                    item_rect = pygame.Rect(50, item_y, self.screen_width - 100, self.WORLD_ITEM_HEIGHT)
                    hover = item_rect.collidepoint(mouse_pos)
                    
                    # Draw world item background
                    color = self.WORLD_ITEM_HOVER_COLOR if hover else self.WORLD_ITEM_COLOR
                    pygame.draw.rect(screen, color, item_rect)
                    pygame.draw.rect(screen, self.TEXT_COLOR, item_rect, 1)
                    
                    # Draw world name
                    name_text = self.font.render(world['name'], True, self.TEXT_COLOR)
                    screen.blit(name_text, (60, item_y + 10))
                    
                    # Draw world info
                    info_text = self.subtitle_font.render(
                        f"Last played: {world['last_modified']} | {world['player_info']}", 
                        True, (200, 200, 200)
                    )
                    screen.blit(info_text, (60, item_y + 35))
                    
                    # Check for click
                    if pygame.mouse.get_pressed()[0] and hover:
                        action = 'play'
                        world_name = world['name']
            
            # Bottom buttons
            button_y = self.screen_height - 80
            
            # Create New World button
            create_btn = self.draw_button("Create New World", 
                                        self.center_x(self.BUTTON_WIDTH), button_y)
            
            # Check for create button click
            if pygame.mouse.get_pressed()[0] and create_btn.collidepoint(pygame.mouse.get_pos()):
                action = 'create'
            
            # Show create world interface if in typing mode
            if world_manager.is_typing:
                # Overlay the create world interface
                overlay_surface = pygame.Surface((self.screen_width, self.screen_height))
                overlay_surface.set_alpha(200)
                overlay_surface.fill(self.BACKGROUND_COLOR)
                screen.blit(overlay_surface, (0, 0))
                
                # Create world title
                create_title = self.title_font.render("Create New World", True, self.TEXT_COLOR)
                create_title_rect = create_title.get_rect(center=(self.screen_width // 2, 200))
                screen.blit(create_title, create_title_rect)
                
                # Instructions
                instructions = self.subtitle_font.render("Enter a world name (at least 8 characters):", True, self.TEXT_COLOR)
                instructions_rect = instructions.get_rect(center=(self.screen_width // 2, 260))
                screen.blit(instructions, instructions_rect)
                
                # Input box
                input_rect = pygame.Rect(
                    self.center_x(400), 300, 400, self.INPUT_HEIGHT
                )
                pygame.draw.rect(screen, self.INPUT_BG_COLOR, input_rect)
                pygame.draw.rect(screen, self.INPUT_BORDER_COLOR, input_rect, 2)
                
                # Input text
                input_text = self.font.render(world_manager.get_new_world_name(), True, self.TEXT_COLOR)
                screen.blit(input_text, (input_rect.x + 10, input_rect.y + 10))
                
                # Cursor
                if world_manager.cursor_blink:
                    cursor_x = input_rect.x + 10 + input_text.get_width()
                    pygame.draw.line(screen, self.TEXT_COLOR, 
                                   (cursor_x, input_rect.y + 10), 
                                   (cursor_x, input_rect.y + self.INPUT_HEIGHT - 10), 2)
                
                # Create button
                can_create = world_manager.can_create_world()
                create_world_btn = self.draw_button("Create World", 
                                            self.center_x(self.BUTTON_WIDTH), 370,
                                            enabled=can_create)
                
                # Check for create world button click
                if can_create and pygame.mouse.get_pressed()[0] and create_world_btn.collidepoint(pygame.mouse.get_pos()):
                    action = 'create'
                    world_name = world_manager.get_new_world_name()
                
                # Cancel button
                cancel_btn = self.draw_button("Cancel", 
                                            self.center_x(self.BUTTON_WIDTH) + 220, 370)
                if pygame.mouse.get_pressed()[0] and cancel_btn.collidepoint(pygame.mouse.get_pos()):
                    world_manager.stop_typing()
            
            # Delete button (if a world is selected)
            if world_name:
                delete_btn = self.draw_button("Delete World", 
                                            self.center_x(self.BUTTON_WIDTH) + 220, button_y)
                if pygame.mouse.get_pressed()[0] and delete_btn.collidepoint(pygame.mouse.get_pos()):
                    action = 'delete'
            
        else:
            # No worlds exist - show create world interface
            subtitle = self.subtitle_font.render("Create Your First World", True, self.TEXT_COLOR)
            subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 140))
            screen.blit(subtitle, subtitle_rect)
            
            # Instructions
            instructions = self.subtitle_font.render("Enter a world name (at least 8 characters):", True, self.TEXT_COLOR)
            instructions_rect = instructions.get_rect(center=(self.screen_width // 2, 200))
            screen.blit(instructions, instructions_rect)
            
            # Input box
            input_rect = pygame.Rect(
                self.center_x(400), 250, 400, self.INPUT_HEIGHT
            )
            pygame.draw.rect(screen, self.INPUT_BG_COLOR, input_rect)
            pygame.draw.rect(screen, self.INPUT_BORDER_COLOR, input_rect, 2)
            
            # Input text
            input_text = self.font.render(world_manager.get_new_world_name(), True, self.TEXT_COLOR)
            screen.blit(input_text, (input_rect.x + 10, input_rect.y + 10))
            
            # Cursor
            if world_manager.is_typing and world_manager.cursor_blink:
                cursor_x = input_rect.x + 10 + input_text.get_width()
                pygame.draw.line(screen, self.TEXT_COLOR, 
                               (cursor_x, input_rect.y + 10), 
                               (cursor_x, input_rect.y + self.INPUT_HEIGHT - 10), 2)
            
            # Create button
            can_create = world_manager.can_create_world()
            create_btn = self.draw_button("Create World", 
                                        self.center_x(self.BUTTON_WIDTH), 320,
                                        enabled=can_create)
            
            # Check for create button click
            if can_create and pygame.mouse.get_pressed()[0] and create_btn.collidepoint(pygame.mouse.get_pos()):
                action = 'create'
                world_name = world_manager.get_new_world_name()
        
        # Back button
        back_btn = self.draw_button("Back", 20, 20)
        if pygame.mouse.get_pressed()[0] and back_btn.collidepoint(pygame.mouse.get_pos()):
            action = 'back'
        
        return action, world_name
    
    def handle_key_input(self, world_manager: WorldManager, event: pygame.event.Event):
        """Handle keyboard input for world naming"""
        if not world_manager.is_typing:
            return
            
        print(f"[DEBUG] Key pressed: {event.key}, unicode: {event.unicode}, typing: {world_manager.is_typing}")
        
        if event.key == pygame.K_RETURN:
            if world_manager.can_create_world():
                world_manager.stop_typing()
        elif event.key == pygame.K_ESCAPE:
            world_manager.stop_typing()
        elif event.key == pygame.K_BACKSPACE:
            world_manager.remove_character()
            print(f"[DEBUG] Removed character, new name: '{world_manager.get_new_world_name()}'")
        elif event.unicode.isprintable():
            world_manager.add_character(event.unicode)
            print(f"[DEBUG] Added character '{event.unicode}', new name: '{world_manager.get_new_world_name()}'")
    
    def update_cursor(self, world_manager: WorldManager):
        """Update cursor blink animation"""
        world_manager.update_cursor()
