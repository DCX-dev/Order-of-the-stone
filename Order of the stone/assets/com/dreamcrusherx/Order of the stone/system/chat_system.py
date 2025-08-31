import pygame
import time
from typing import List, Tuple, Optional

class ChatSystem:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.messages = []  # List of (username, message, timestamp, color)
        self.max_messages = 10
        self.message_lifetime = 10.0  # seconds
        self.chat_active = False
        self.chat_input = ""
        self.chat_cursor_visible = True
        self.cursor_timer = 0
        self.font = None
        self.small_font = None
        
    def set_fonts(self, font, small_font):
        """Set the fonts for chat display"""
        self.font = font
        self.small_font = small_font
    
    def add_message(self, username: str, message: str, color: Tuple[int, int, int] = (255, 255, 255)):
        """Add a new chat message"""
        timestamp = time.time()
        self.messages.append((username, message, timestamp, color))
        
        # Keep only the latest messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        
        print(f"💬 {username}: {message}")
    
    def add_system_message(self, message: str, color: Tuple[int, int, int] = (255, 255, 0)):
        """Add a system message"""
        self.add_message("System", message, color)
    
    def add_error_message(self, message: str):
        """Add an error message"""
        self.add_message("Error", message, (255, 0, 0))
    
    def add_success_message(self, message: str):
        """Add a success message"""
        self.add_message("Success", message, (0, 255, 0))
    
    def toggle_chat(self):
        """Toggle chat input on/off"""
        self.chat_active = not self.chat_active
        if self.chat_active:
            self.chat_input = ""
            print("💬 Chat activated - press Enter to send, Escape to cancel")
        else:
            self.chat_input = ""
            print("💬 Chat deactivated")
    
    def handle_key_event(self, event) -> Optional[str]:
        """Handle key events for chat input"""
        if not self.chat_active:
            return None
        
        if event.key == pygame.K_RETURN:
            if self.chat_input.strip():
                message = self.chat_input.strip()
                self.chat_input = ""
                self.chat_active = False
                return message
            else:
                self.chat_active = False
                return None
        elif event.key == pygame.K_ESCAPE:
            self.chat_input = ""
            self.chat_active = False
            return None
        elif event.key == pygame.K_BACKSPACE:
            self.chat_input = self.chat_input[:-1]
        elif event.key == pygame.K_TAB:
            # Prevent tab from switching focus
            pass
        elif event.unicode.isprintable():
            # Add printable characters to chat input
            if len(self.chat_input) < 100:  # Limit message length
                self.chat_input += event.unicode
        
        return None
    
    def update(self, dt: float):
        """Update chat system (remove old messages, update cursor)"""
        current_time = time.time()
        
        # Remove old messages
        self.messages = [(username, message, timestamp, color) 
                        for username, message, timestamp, color in self.messages
                        if current_time - timestamp < self.message_lifetime]
        
        # Update cursor blink
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0
            self.chat_cursor_visible = not self.chat_cursor_visible
    
    def draw(self, screen):
        """Draw chat messages and input"""
        if not self.font or not self.small_font:
            return
        
        # Draw chat messages
        y_offset = self.screen_height - 200
        for username, message, timestamp, color in self.messages:
            # Format message
            if username == "System":
                text = f"🔧 {message}"
            elif username == "Error":
                text = f"❌ {message}"
            elif username == "Success":
                text = f"✅ {message}"
            else:
                text = f"{username}: {message}"
            
            # Render message
            text_surface = self.small_font.render(text, True, color)
            screen.blit(text_surface, (10, y_offset))
            y_offset += 20
        
        # Draw chat input if active
        if self.chat_active:
            # Draw chat input background
            input_rect = pygame.Rect(10, self.screen_height - 40, 400, 30)
            pygame.draw.rect(screen, (0, 0, 0, 128), input_rect)
            pygame.draw.rect(screen, (255, 255, 255), input_rect, 2)
            
            # Draw chat prompt
            prompt_text = self.small_font.render("💬 ", True, (255, 255, 255))
            screen.blit(prompt_text, (15, self.screen_height - 35))
            
            # Draw chat input text
            if self.chat_input:
                input_text = self.small_font.render(self.chat_input, True, (255, 255, 255))
                screen.blit(input_text, (35, self.screen_height - 35))
            
            # Draw blinking cursor
            if self.chat_cursor_visible:
                cursor_x = 35 + self.small_font.size(self.chat_input)[0]
                cursor_surface = self.small_font.render("|", True, (255, 255, 255))
                screen.blit(cursor_surface, (cursor_x, self.screen_height - 35))
    
    def is_chat_active(self) -> bool:
        """Check if chat input is currently active"""
        return self.chat_active
    
    def get_messages(self) -> List[Tuple[str, str, float, Tuple[int, int, int]]]:
        """Get all current chat messages"""
        return self.messages.copy()
    
    def clear_messages(self):
        """Clear all chat messages"""
        self.messages.clear()
        print("💬 Chat messages cleared")
