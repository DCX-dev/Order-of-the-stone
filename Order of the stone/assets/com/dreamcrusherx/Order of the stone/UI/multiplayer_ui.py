import pygame
import sys
import os
from typing import List, Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import LAN multiplayer modules
try:
    from multiplayer.lan_client import LANClient
    from multiplayer.lan_server import LANServer
except ImportError:
    print("⚠️ Warning: LAN multiplayer modules not found")
    LANClient = None
    LANServer = None

class MultiplayerUI:
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = None
        self.small_font = None
        self.title_font = None
        
        # UI states
        self.current_screen = "main"  # main, host, join, server_list
        self.selected_server = None
        self.server_list = {}
        self.refresh_timer = 0
        
        # Multiplayer components
        self.lan_server = None
        self.lan_client = None
        
        # Input fields
        self.world_name_input = ""
        self.username_input = ""
        self.server_ip_input = "localhost"
        self.server_port_input = "5555"
        
        # UI elements
        self.buttons = {}
        self.input_fields = {}
        self.scroll_offset = 0
        
    def set_fonts(self, font, small_font, title_font):
        """Set the fonts for UI display"""
        self.font = font
        self.small_font = small_font
        self.title_font = title_font
    
    def draw_main_menu(self, screen):
        """Draw the main multiplayer menu"""
        # Title
        title_text = self.title_font.render("🌐 Multiplayer", True, (255, 255, 255))
        screen.blit(title_text, (self.screen_width // 2 - title_text.get_width() // 2, 100))
        
        # Buttons
        button_y = 250
        button_height = 50
        button_width = 300
        
        # Host Server button
        host_rect = pygame.Rect(self.screen_width // 2 - button_width // 2, button_y, button_width, button_height)
        pygame.draw.rect(screen, (0, 100, 0), host_rect)
        pygame.draw.rect(screen, (255, 255, 255), host_rect, 2)
        host_text = self.font.render("🏠 Host Server", True, (255, 255, 255))
        screen.blit(host_text, (host_rect.centerx - host_text.get_width() // 2, host_rect.centery - host_text.get_height() // 2))
        self.buttons["host"] = host_rect
        
        # Join Server button
        join_rect = pygame.Rect(self.screen_width // 2 - button_width // 2, button_y + 70, button_width, button_height)
        pygame.draw.rect(screen, (0, 0, 100), join_rect)
        pygame.draw.rect(screen, (255, 255, 255), join_rect, 2)
        join_text = self.font.render("🔗 Join Server", True, (255, 255, 255))
        screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))
        self.buttons["join"] = join_rect
        
        # Back button
        back_rect = pygame.Rect(self.screen_width // 2 - button_width // 2, button_y + 140, button_width, button_height)
        pygame.draw.rect(screen, (100, 0, 0), back_rect)
        pygame.draw.rect(screen, (255, 255, 255), back_rect, 2)
        back_text = self.font.render("⬅️ Back", True, (255, 255, 255))
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))
        self.buttons["back"] = back_rect
    
    def draw_host_server(self, screen):
        """Draw the host server interface"""
        # Title
        title_text = self.title_font.render("🏠 Host Server", True, (255, 255, 255))
        screen.blit(title_text, (self.screen_width // 2 - title_text.get_width() // 2, 80))
        
        # World selection info
        info_text = self.font.render("Select the world you want to host:", True, (255, 255, 255))
        screen.blit(info_text, (50, 150))
        
        # World name input
        input_rect = pygame.Rect(50, 200, 400, 40)
        pygame.draw.rect(screen, (50, 50, 50), input_rect)
        pygame.draw.rect(screen, (255, 255, 255), input_rect, 2)
        
        if self.world_name_input:
            input_text = self.font.render(self.world_name_input, True, (255, 255, 255))
            screen.blit(input_text, (input_rect.x + 10, input_rect.centery - input_text.get_height() // 2))
        else:
            placeholder = self.small_font.render("Enter world name...", True, (128, 128, 128))
            screen.blit(placeholder, (input_rect.x + 10, input_rect.centery - placeholder.get_height() // 2))
        
        self.input_fields["world_name"] = input_rect
        
        # Buttons
        button_y = 300
        button_height = 50
        button_width = 200
        
        # Start Server button
        start_rect = pygame.Rect(50, button_y, button_width, button_height)
        pygame.draw.rect(screen, (0, 100, 0), start_rect)
        pygame.draw.rect(screen, (255, 255, 255), start_rect, 2)
        start_text = self.font.render("🚀 Start Server", True, (255, 255, 255))
        screen.blit(start_text, (start_rect.centerx - start_text.get_width() // 2, start_rect.centery - start_text.get_height() // 2))
        self.buttons["start_server"] = start_rect
        
        # Back button
        back_rect = pygame.Rect(300, button_y, button_width, button_height)
        pygame.draw.rect(screen, (100, 0, 0), back_rect)
        pygame.draw.rect(screen, (255, 255, 255), back_rect, 2)
        back_text = self.font.render("⬅️ Back", True, (255, 255, 255))
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))
        self.buttons["back"] = back_rect
    
    def draw_join_server(self, screen):
        """Draw the join server interface"""
        # Title
        title_text = self.title_font.render("🔗 Join Server", True, (255, 255, 255))
        screen.blit(title_text, (self.screen_width // 2 - title_text.get_width() // 2, 80))
        
        # Server discovery info
        info_text = self.font.render("Available LAN Servers:", True, (255, 255, 255))
        screen.blit(info_text, (50, 150))
        
        # Server list
        if self.server_list:
            y_offset = 200
            for server_key, server_info in self.server_list.items():
                # Server entry background
                server_rect = pygame.Rect(50, y_offset, 700, 80)
                color = (80, 120, 80) if server_key == self.selected_server else (60, 60, 70)
                pygame.draw.rect(screen, color, server_rect, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 255) if server_key == self.selected_server else (150, 150, 150), server_rect, 2, border_radius=10)
                
                # Server name and host
                name_text = self.font.render(server_info.get("name", "Unknown Server"), True, (255, 255, 255))
                screen.blit(name_text, (server_rect.x + 15, server_rect.y + 10))
                
                # World and host info
                world_text = self.small_font.render(f"World: {server_info.get('world_name', 'Unknown')}", True, (200, 200, 200))
                screen.blit(world_text, (server_rect.x + 15, server_rect.y + 35))
                
                host_text = self.small_font.render(f"Host: {server_info.get('host_player', 'Unknown')}", True, (200, 200, 200))
                screen.blit(host_text, (server_rect.x + 15, server_rect.y + 55))
                
                # Players count (right side)
                players_text = self.font.render(f"👥 {server_info.get('players', 0)}/{server_info.get('max_players', 10)}", True, (100, 255, 100))
                screen.blit(players_text, (server_rect.x + server_rect.width - 100, server_rect.y + 25))
                
                # Click to select
                if pygame.mouse.get_pressed()[0]:
                    mouse_pos = pygame.mouse.get_pos()
                    if server_rect.collidepoint(mouse_pos):
                        self.selected_server = server_key
                
                y_offset += 90
        else:
            no_servers_text = self.font.render("No servers found on local network", True, (128, 128, 128))
            screen.blit(no_servers_text, (50, 200))
            
            hint_text = self.small_font.render("Make sure the host is on the same Wi-Fi network", True, (100, 100, 100))
            screen.blit(hint_text, (50, 230))
        
        # Buttons
        button_y = 500
        button_height = 50
        button_width = 200
        
        # Join Server button
        join_rect = pygame.Rect(50, button_y, button_width, button_height)
        color = (0, 100, 0) if self.selected_server else (50, 50, 50)
        pygame.draw.rect(screen, color, join_rect)
        pygame.draw.rect(screen, (255, 255, 255), join_rect, 2)
        join_text = self.font.render("🔗 Join Server", True, (255, 255, 255))
        screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))
        self.buttons["join_selected"] = join_rect
        
        # Refresh button
        refresh_rect = pygame.Rect(300, button_y, button_width, button_height)
        pygame.draw.rect(screen, (0, 0, 100), refresh_rect)
        pygame.draw.rect(screen, (255, 255, 255), refresh_rect, 2)
        refresh_text = self.font.render("🔄 Refresh", True, (255, 255, 255))
        screen.blit(refresh_text, (refresh_rect.centerx - refresh_text.get_width() // 2, refresh_rect.centery - refresh_text.get_height() // 2))
        self.buttons["refresh"] = refresh_rect
        
        # Back button
        back_rect = pygame.Rect(550, button_y, button_width, button_height)
        pygame.draw.rect(screen, (100, 0, 0), back_rect)
        pygame.draw.rect(screen, (255, 255, 255), back_rect, 2)
        back_text = self.font.render("⬅️ Back", True, (255, 255, 255))
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))
        self.buttons["back"] = back_rect
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse clicks on UI elements"""
        for button_name, button_rect in self.buttons.items():
            if button_rect.collidepoint(mouse_pos):
                return button_name
        return None
    
    def handle_input_field_click(self, mouse_pos: Tuple[int, int]):
        """Handle clicks on input fields"""
        for field_name, field_rect in self.input_fields.items():
            if field_rect.collidepoint(mouse_pos):
                # Focus on this input field
                self.focused_field = field_name
                return
    
    def handle_key_input(self, event) -> Optional[str]:
        """Handle keyboard input for input fields"""
        if not hasattr(self, 'focused_field'):
            return None
        
        if event.key == pygame.K_RETURN:
            # Process the input
            if self.focused_field == "world_name":
                return self.world_name_input
            self.focused_field = None
            return None
        elif event.key == pygame.K_ESCAPE:
            self.focused_field = None
            return None
        elif event.key == pygame.K_BACKSPACE:
            if self.focused_field == "world_name":
                self.world_name_input = self.world_name_input[:-1]
        elif event.unicode.isprintable():
            if self.focused_field == "world_name":
                if len(self.world_name_input) < 30:
                    self.world_name_input += event.unicode
        
        return None
    
    def update(self, dt: float):
        """Update the multiplayer UI"""
        self.refresh_timer += dt
        
        # Auto-refresh server list every 5 seconds
        if self.refresh_timer >= 5.0:
            self.refresh_timer = 0
            if self.current_screen == "join":
                self.refresh_server_list()
    
    def refresh_server_list(self):
        """Refresh the list of available servers (LAN discovery)"""
        try:
            if LANClient:
                # Create temporary client for discovery
                temp_client = LANClient("Discovery")
                servers = temp_client.discover_servers(timeout=2.0)
                
                self.server_list = {}
                for i, server in enumerate(servers):
                    self.server_list[f"server_{i}"] = {
                        "name": server.get("server_name", "Unknown Server"),
                        "host": server.get("ip_address", "Unknown"),
                        "port": server.get("port", 25565),
                        "players": server.get("players", 0),
                        "max_players": server.get("max_players", 10),
                        "world_name": server.get("world_name", "World"),
                        "host_player": server.get("host_player", "Unknown")
                    }
                print(f"🔍 Found {len(self.server_list)} LAN servers")
            else:
                print("⚠️ LAN multiplayer not available")
        except Exception as e:
            print(f"⚠️ Error refreshing server list: {e}")
    
    def start_server_discovery(self):
        """Start server discovery (refresh the list)"""
        try:
            self.refresh_server_list()
        except Exception as e:
            print(f"⚠️ Error starting server discovery: {e}")
    
    def stop_server_discovery(self):
        """Stop server discovery (clear the list)"""
        # No continuous discovery needed, just clear the list
        pass
    
    def get_current_screen(self) -> str:
        """Get the current UI screen"""
        return self.current_screen
    
    def set_current_screen(self, screen: str):
        """Set the current UI screen"""
        self.current_screen = screen
        if screen == "join":
            self.start_server_discovery()
        else:
            self.stop_server_discovery()
    
    def get_selected_server(self) -> Optional[str]:
        """Get the currently selected server"""
        return self.selected_server
    
    def get_world_name_input(self) -> str:
        """Get the world name input"""
        return self.world_name_input
    
    def get_selected_server_info(self) -> Optional[Dict]:
        """Get the full info of the selected server"""
        if self.selected_server and self.selected_server in self.server_list:
            return self.server_list[self.selected_server]
        return None
    
    def set_lan_server(self, server: 'LANServer'):
        """Set the LAN server instance"""
        self.lan_server = server
    
    def set_lan_client(self, client: 'LANClient'):
        """Set the LAN client instance"""
        self.lan_client = client
    
    def get_lan_server(self) -> Optional['LANServer']:
        """Get the LAN server instance"""
        return self.lan_server
    
    def get_lan_client(self) -> Optional['LANClient']:
        """Get the LAN client instance"""
        return self.lan_client
