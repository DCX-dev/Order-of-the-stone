import pygame
from world_manager_v2 import WorldManager
from world_detector import WorldDetector
from typing import Optional, Tuple

class WorldUI:
    """Enhanced UI for world selection and creation with 12-world limit"""
    
    def __init__(self, screen_width: int, screen_height: int, font: pygame.font.Font):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.title_font = pygame.font.SysFont("Arial", 48)
        self.subtitle_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Colors
        self.BACKGROUND_COLOR = (50, 50, 50)
        self.TEXT_COLOR = (255, 255, 255)
        self.BUTTON_COLOR = (100, 100, 100)
        self.BUTTON_HOVER_COLOR = (150, 150, 150)
        self.BUTTON_DISABLED_COLOR = (70, 70, 70)
        self.WORLD_ITEM_COLOR = (90, 90, 90)
        self.WORLD_ITEM_HOVER_COLOR = (120, 120, 120)
        self.SLOT_COUNT_COLOR = (100, 150, 100)
        self.SLOT_COUNT_FULL_COLOR = (200, 100, 100)
        
        # Button dimensions
        self.BUTTON_WIDTH = 200
        self.BUTTON_HEIGHT = 50
        self.WORLD_ITEM_HEIGHT = 60
        
        # Scroll position for world list
        self.scroll_y = 0
        self.max_scroll = 0
        
        # Initialize world detector
        self.world_detector = WorldDetector()
    
    def center_x(self, width: int) -> int:
        """Center an element horizontally"""
        return (self.screen_width - width) // 2
    
    def draw_button(self, text: str, x: int, y: int, width: int = None, height: int = None,
                    enabled: bool = True, hover: bool = False) -> pygame.Rect:
        """Draw a button and return its rectangle"""
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
        
        # Draw button
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(pygame.display.get_surface(), color, rect)
        pygame.draw.rect(pygame.display.get_surface(), self.TEXT_COLOR, rect, 2)
        
        # Draw text
        text_surface = self.font.render(text, True, self.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        pygame.display.get_surface().blit(text_surface, text_rect)
        
        return rect
    
    def draw_world_item(self, world_info: dict, x: int, y: int, width: int, selected: bool = False, preview_surface: pygame.Surface = None) -> pygame.Rect:
        """Draw a single world item in the list with preview thumbnail"""
        screen = pygame.display.get_surface()
        
        # Background
        rect = pygame.Rect(x, y, width, self.WORLD_ITEM_HEIGHT)
        color = self.WORLD_ITEM_HOVER_COLOR if selected else self.WORLD_ITEM_COLOR
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, self.TEXT_COLOR, rect, 2 if selected else 1)
        
        # World preview thumbnail (left side)
        if preview_surface:
            preview_rect = pygame.Rect(x + 10, y + 5, 80, 60)
            pygame.draw.rect(screen, (30, 30, 30), preview_rect)  # Dark background for preview
            pygame.draw.rect(screen, self.TEXT_COLOR, preview_rect, 1)  # Border
            
            # Scale preview to fit
            scaled_preview = pygame.transform.scale(preview_surface, (78, 58))
            screen.blit(scaled_preview, (x + 11, y + 6))
        
        # World name (right side, above preview)
        name_x = x + 100 if preview_surface else x + 10
        name_text = self.font.render(world_info['name'], True, self.TEXT_COLOR)
        screen.blit(name_text, (name_x, y + 5))
        
        # Last modified (right side, below name)
        modified_text = self.small_font.render(f"Last: {world_info['last_modified']}", True, self.TEXT_COLOR)
        screen.blit(modified_text, (name_x, y + 25))
        
        # Player info (right side, below modified)
        player_text = self.small_font.render(world_info['player_info'], True, self.TEXT_COLOR)
        screen.blit(player_text, (name_x, y + 40))
        
        return rect
    
    def draw_world_selection_screen(self, world_manager: WorldManager) -> Tuple[str, Optional[str]]:
        """Draw the world selection screen. Returns (action, world_name)."""
        screen = pygame.display.get_surface()
        screen.fill(self.BACKGROUND_COLOR)
        
        # Title
        title = self.title_font.render("World Selection", True, self.TEXT_COLOR)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        screen.blit(title, title_rect)
        
        # Refresh world detection
        self.world_detector.refresh_worlds()
        
        # World count and slot info
        world_count = self.world_detector.get_world_count()
        available_slots = self.world_detector.get_available_slots()
        
        count_text = self.subtitle_font.render(f"Worlds: {world_count}/12", True, self.TEXT_COLOR)
        count_rect = count_text.get_rect(center=(self.screen_width // 2, 100))
        screen.blit(count_text, count_rect)
        
        # Slot availability
        if available_slots > 0:
            slot_color = self.SLOT_COUNT_COLOR
            slot_text = f"Available slots: {available_slots}"
        else:
            slot_color = self.SLOT_COUNT_FULL_COLOR
            slot_text = "No more world slots available"
        
        slot_surface = self.small_font.render(slot_text, True, slot_color)
        slot_rect = slot_surface.get_rect(center=(self.screen_width // 2, 125))
        screen.blit(slot_surface, slot_rect)
        
        action = None
        world_name = None
        selected_world = None  # Track which world is selected
        
        if self.world_detector.get_world_count() > 0:
            # Worlds exist - show world selection with create option
            worlds = self.world_detector.get_world_info_for_display()
            
            # Subtitle for existing worlds
            subtitle = self.subtitle_font.render("Select a World or Create New", True, self.TEXT_COLOR)
            subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 200))
            screen.blit(subtitle, subtitle_rect)
            
            # Calculate scroll area
            list_height = min(len(worlds) * self.WORLD_ITEM_HEIGHT, 300)
            list_y = 240
            list_width = self.screen_width - 100
            
            # Draw world list
            for i, world_info in enumerate(worlds):
                world_y = list_y + i * self.WORLD_ITEM_HEIGHT - self.scroll_y
                
                # Only draw if visible
                if world_y + self.WORLD_ITEM_HEIGHT > list_y and world_y < list_y + list_height:
                    # Load world preview
                    preview_surface = None
                    try:
                        from world_preview import WorldPreview
                        preview_system = WorldPreview()
                        preview_surface = preview_system.get_world_preview(world_info['name'])
                    except:
                        pass  # Fallback if preview system fails
                    
                    # Check if this world is selected
                    is_selected = selected_world == world_info['name']
                    world_rect = self.draw_world_item(world_info, 50, world_y, list_width, is_selected, preview_surface)
                    
                    # Check for click
                    if pygame.mouse.get_pressed()[0] and world_rect.collidepoint(pygame.mouse.get_pos()):
                        # Toggle selection: if already selected, unselect; otherwise select
                        if selected_world == world_info['name']:
                            selected_world = None  # Unselect if already selected
                        else:
                            selected_world = world_info['name']  # Select if not already selected
                        action = None  # Don't immediately play, just toggle selection
            
            # Update max scroll
            self.max_scroll = max(0, len(worlds) * self.WORLD_ITEM_HEIGHT - list_height)
            
            # Show selected world info
            if selected_world:
                selected_text = self.subtitle_font.render(f"Selected: {selected_world}", True, (100, 255, 100))
                selected_rect = selected_text.get_rect(center=(self.screen_width // 2, 520))
                screen.blit(selected_text, selected_rect)
            
            # Create new world button (only if slots available)
            if self.world_detector.can_create_world():
                create_btn = self.draw_button("Create New World", 
                                            self.center_x(self.BUTTON_WIDTH), 580)
                
                if pygame.mouse.get_pressed()[0] and create_btn.collidepoint(pygame.mouse.get_pos()):
                    action = 'create'
            else:
                # Show "no slots available" message
                no_slots_text = self.subtitle_font.render("Maximum worlds reached (12/12)", True, self.SLOT_COUNT_FULL_COLOR)
                no_slots_rect = no_slots_text.get_rect(center=(self.screen_width // 2, 580))
                screen.blit(no_slots_text, no_slots_rect)
            
            # Play World button (only enabled if a world is selected)
            play_enabled = selected_world is not None
            play_btn = self.draw_button("Play World", 
                                        self.center_x(self.BUTTON_WIDTH) - 220, 580,
                                        enabled=play_enabled)
            
            if pygame.mouse.get_pressed()[0] and play_btn.collidepoint(pygame.mouse.get_pos()) and play_enabled:
                action = 'play'
                world_name = selected_world
            
            # Delete button (only enabled if a world is selected)
            delete_enabled = selected_world is not None
            delete_btn = self.draw_button("Delete World", 
                                        self.center_x(self.BUTTON_WIDTH) + 220, 580,
                                        enabled=delete_enabled)
            
            if pygame.mouse.get_pressed()[0] and delete_btn.collidepoint(pygame.mouse.get_pos()) and delete_enabled:
                action = 'delete'
                world_name = selected_world
        else:
            # No worlds exist - show create world interface
            subtitle = self.subtitle_font.render("Create Your First World", True, self.TEXT_COLOR)
            subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, 200))
            screen.blit(subtitle, subtitle_rect)
            
            # Instructions
            instructions = self.subtitle_font.render("Click the button below to create your first world:", True, self.TEXT_COLOR)
            instructions_rect = instructions.get_rect(center=(self.screen_width // 2, 250))
            screen.blit(instructions, instructions_rect)
            
            # Create button
            create_btn = self.draw_button("Create World", 
                                        self.center_x(self.BUTTON_WIDTH), 300)
            
            # Check for create button click
            if pygame.mouse.get_pressed()[0] and create_btn.collidepoint(pygame.mouse.get_pos()):
                action = 'create'
        
        # Back button
        back_btn = self.draw_button("Back to Title", self.center_x(self.BUTTON_WIDTH), 650)
        if pygame.mouse.get_pressed()[0] and back_btn.collidepoint(pygame.mouse.get_pos()):
            action = 'back'
        
        return action, world_name
    
    def handle_scroll(self, scroll_amount: int):
        """Handle mouse wheel scrolling"""
        self.scroll_y = max(0, min(self.scroll_y - scroll_amount, self.max_scroll))
