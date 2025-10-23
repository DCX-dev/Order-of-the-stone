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
        """Draw the main multiplayer menu with modern styling"""
        # Solid background for better performance
        screen.fill((30, 50, 90))
        
        # Title with glow effect
        title_text = self.title_font.render("🌐 LAN Multiplayer", True, (255, 255, 255))
        title_glow = self.title_font.render("🌐 LAN Multiplayer", True, (100, 150, 255))
        title_x = self.screen_width // 2 - title_text.get_width() // 2
        screen.blit(title_glow, (title_x + 3, 53))
        screen.blit(title_text, (title_x, 50))
        
        # Subtitle
        subtitle = self.small_font.render("Play with friends on the same Wi-Fi", True, (150, 180, 255))
        subtitle_x = self.screen_width // 2 - subtitle.get_width() // 2
        screen.blit(subtitle, (subtitle_x, 120))
        
        # Modern buttons with hover effects
        button_y = 220
        button_height = 80
        button_width = 400
        button_spacing = 100
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Host Server button
        host_rect = pygame.Rect(self.screen_width // 2 - button_width // 2, button_y, button_width, button_height)
        host_hovered = host_rect.collidepoint(mouse_pos)
        host_color = (60, 180, 60) if host_hovered else (40, 140, 40)
        
        # Draw button with rounded corners and shadow
        shadow_rect = pygame.Rect(host_rect.x + 5, host_rect.y + 5, host_rect.width, host_rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=15)
        pygame.draw.rect(screen, host_color, host_rect, border_radius=15)
        pygame.draw.rect(screen, (100, 255, 100) if host_hovered else (80, 200, 80), host_rect, 3, border_radius=15)
        
        # Button icon and text
        host_text = self.font.render("🏠 Host a Game", True, (255, 255, 255))
        host_desc = self.small_font.render("Let others join your world", True, (200, 255, 200))
        screen.blit(host_text, (host_rect.centerx - host_text.get_width() // 2, host_rect.centery - 15))
        screen.blit(host_desc, (host_rect.centerx - host_desc.get_width() // 2, host_rect.centery + 15))
        self.buttons["host"] = host_rect
        
        # Join Server button
        join_rect = pygame.Rect(self.screen_width // 2 - button_width // 2, button_y + button_spacing, button_width, button_height)
        join_hovered = join_rect.collidepoint(mouse_pos)
        join_color = (60, 60, 180) if join_hovered else (40, 40, 140)
        
        shadow_rect = pygame.Rect(join_rect.x + 5, join_rect.y + 5, join_rect.width, join_rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=15)
        pygame.draw.rect(screen, join_color, join_rect, border_radius=15)
        pygame.draw.rect(screen, (100, 100, 255) if join_hovered else (80, 80, 200), join_rect, 3, border_radius=15)
        
        join_text = self.font.render("🔗 Join a Game", True, (255, 255, 255))
        join_desc = self.small_font.render("Find and join available games", True, (200, 200, 255))
        screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - 15))
        screen.blit(join_desc, (join_rect.centerx - join_desc.get_width() // 2, join_rect.centery + 15))
        self.buttons["join"] = join_rect
        
        # Back button (smaller, at bottom)
        back_rect = pygame.Rect(self.screen_width // 2 - 150, button_y + button_spacing * 2 + 20, 300, 50)
        back_hovered = back_rect.collidepoint(mouse_pos)
        back_color = (150, 50, 50) if back_hovered else (120, 30, 30)
        
        pygame.draw.rect(screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 100, 100) if back_hovered else (200, 80, 80), back_rect, 2, border_radius=10)
        
        back_text = self.font.render("⬅️ Back to Title", True, (255, 255, 255))
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))
        self.buttons["back"] = back_rect
    
    def draw_host_server(self, screen):
        """Draw the host server interface with modern styling"""
        # Solid background for better performance
        screen.fill((30, 60, 50))
        
        # Title
        title_text = self.title_font.render("🏠 Host LAN Server", True, (255, 255, 255))
        title_glow = self.title_font.render("🏠 Host LAN Server", True, (100, 255, 150))
        title_x = self.screen_width // 2 - title_text.get_width() // 2
        screen.blit(title_glow, (title_x + 3, 53))
        screen.blit(title_text, (title_x, 50))
        
        # Subtitle
        subtitle = self.small_font.render("Others on your Wi-Fi can join this game", True, (150, 255, 200))
        subtitle_x = self.screen_width // 2 - subtitle.get_width() // 2
        screen.blit(subtitle, (subtitle_x, 120))
        
        # Info panel - responsive sizing
        panel_width = min(600, self.screen_width - 100)
        panel_x = self.screen_width // 2 - panel_width // 2
        panel_y = 170
        panel_height = 170
        
        # Panel background with shadow
        shadow_rect = pygame.Rect(panel_x + 5, panel_y + 5, panel_width, panel_height)
        pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=15)
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 60, 50), panel_rect, border_radius=15)
        pygame.draw.rect(screen, (100, 200, 150), panel_rect, 3, border_radius=15)
        
        # Label
        label_text = self.font.render("World Name:", True, (150, 255, 200))
        screen.blit(label_text, (panel_x + 30, panel_y + 30))
        
        # World name input field with focus indicator
        input_rect = pygame.Rect(panel_x + 30, panel_y + 70, panel_width - 60, 50)
        input_focused = hasattr(self, 'focused_field') and self.focused_field == "world_name"
        input_color = (60, 80, 70) if not input_focused else (70, 100, 80)
        border_color = (100, 255, 150) if input_focused else (150, 200, 180)
        
        pygame.draw.rect(screen, input_color, input_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, input_rect, 3 if input_focused else 2, border_radius=10)
        
        # Input text or placeholder
        if self.world_name_input:
            input_text = self.font.render(self.world_name_input, True, (255, 255, 255))
            screen.blit(input_text, (input_rect.x + 15, input_rect.centery - input_text.get_height() // 2))
        else:
            placeholder = self.small_font.render("Type world name with keyboard...", True, (120, 150, 130))
            screen.blit(placeholder, (input_rect.x + 15, input_rect.centery - placeholder.get_height() // 2))
        
        # Blinking cursor when focused
        if input_focused and int(pygame.time.get_ticks() / 500) % 2 == 0:
            cursor_x = input_rect.x + 15 + self.font.size(self.world_name_input)[0] if self.world_name_input else input_rect.x + 15
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, input_rect.y + 12), (cursor_x, input_rect.y + input_rect.height - 12), 2)
        
        self.input_fields["world_name"] = input_rect
        
        # Hint text
        hint_text = self.small_font.render("💡 Click the box and type your world name", True, (180, 220, 200))
        screen.blit(hint_text, (panel_x + 30, panel_y + 135))
        
        # Buttons - responsive positioning
        button_y = panel_y + panel_height + 40
        button_height = 55
        button_width = min(230, (self.screen_width - 100) // 2 - 30)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Start Server button
        start_x = self.screen_width // 2 - button_width - 20
        start_rect = pygame.Rect(start_x, button_y, button_width, button_height)
        start_hovered = start_rect.collidepoint(mouse_pos)
        start_color = (60, 180, 60) if start_hovered else (40, 140, 40)
        
        shadow_rect = pygame.Rect(start_rect.x + 4, start_rect.y + 4, start_rect.width, start_rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=12)
        pygame.draw.rect(screen, start_color, start_rect, border_radius=12)
        pygame.draw.rect(screen, (100, 255, 100) if start_hovered else (80, 200, 80), start_rect, 3, border_radius=12)
        
        start_text = self.font.render("🚀 Start Server", True, (255, 255, 255))
        screen.blit(start_text, (start_rect.centerx - start_text.get_width() // 2, start_rect.centery - start_text.get_height() // 2))
        self.buttons["start_server"] = start_rect
        
        # Back button
        back_x = self.screen_width // 2 + 20
        back_rect = pygame.Rect(back_x, button_y, button_width, button_height)
        back_hovered = back_rect.collidepoint(mouse_pos)
        back_color = (150, 50, 50) if back_hovered else (120, 30, 30)
        
        shadow_rect = pygame.Rect(back_rect.x + 4, back_rect.y + 4, back_rect.width, back_rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=12)
        pygame.draw.rect(screen, back_color, back_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 100, 100) if back_hovered else (200, 80, 80), back_rect, 2, border_radius=12)
        
        back_text = self.font.render("⬅️ Cancel", True, (255, 255, 255))
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))
        self.buttons["back"] = back_rect
    
    def draw_join_server(self, screen):
        """Draw the join server interface with modern styling"""
        # Solid background for better performance
        screen.fill((30, 50, 70))
        
        # Title
        title_text = self.title_font.render("🔗 Join LAN Server", True, (255, 255, 255))
        title_glow = self.title_font.render("🔗 Join LAN Server", True, (100, 150, 255))
        title_x = self.screen_width // 2 - title_text.get_width() // 2
        screen.blit(title_glow, (title_x + 3, 53))
        screen.blit(title_text, (title_x, 50))
        
        # Subtitle
        subtitle = self.small_font.render("Scanning local network for games...", True, (150, 200, 255))
        subtitle_x = self.screen_width // 2 - subtitle.get_width() // 2
        screen.blit(subtitle, (subtitle_x, 120))
        
        # Server list header
        info_text = self.font.render("Available Servers:", True, (200, 220, 255))
        screen.blit(info_text, (50, 160))
        
        # Server list with modern cards - scrollable
        if self.server_list:
            y_offset = 200
            max_visible = 3  # Show max 3 servers at once to fit screen
            server_items = list(self.server_list.items())[:max_visible]
            
            for server_key, server_info in server_items:
                # Server card
                server_rect = pygame.Rect(50, y_offset, min(700, self.screen_width - 100), 90)
                is_selected = server_key == self.selected_server
                
                # Card background (no shadow for performance)
                if is_selected:
                    card_color = (60, 100, 140)
                    border_color = (100, 200, 255)
                    border_width = 4
                else:
                    card_color = (40, 50, 70)
                    border_color = (100, 120, 150)
                    border_width = 2
                
                pygame.draw.rect(screen, card_color, server_rect, border_radius=12)
                pygame.draw.rect(screen, border_color, server_rect, border_width, border_radius=12)
                
                # Server icon/indicator
                indicator_color = (100, 255, 100) if server_info.get('players', 0) < server_info.get('max_players', 10) else (255, 200, 100)
                pygame.draw.circle(screen, indicator_color, (server_rect.x + 25, server_rect.centery), 8)
                
                # Server name
                name_text = self.font.render(server_info.get("name", "Unknown Server"), True, (255, 255, 255))
                screen.blit(name_text, (server_rect.x + 50, server_rect.y + 12))
                
                # World and host info
                world_text = self.small_font.render(f"🌍 {server_info.get('world_name', 'Unknown')}", True, (180, 200, 255))
                screen.blit(world_text, (server_rect.x + 50, server_rect.y + 40))
                
                host_text = self.small_font.render(f"👤 {server_info.get('host_player', 'Unknown')}", True, (180, 200, 255))
                screen.blit(host_text, (server_rect.x + 50, server_rect.y + 62))
                
                # Players count in a badge
                players_str = f"{server_info.get('players', 0)}/{server_info.get('max_players', 10)}"
                badge_width = 80
                badge_rect = pygame.Rect(server_rect.right - badge_width - 20, server_rect.centery - 20, badge_width, 40)
                pygame.draw.rect(screen, (40, 80, 120), badge_rect, border_radius=8)
                pygame.draw.rect(screen, indicator_color, badge_rect, 2, border_radius=8)
                
                players_text = self.font.render(players_str, True, (255, 255, 255))
                screen.blit(players_text, (badge_rect.centerx - players_text.get_width() // 2, badge_rect.centery - players_text.get_height() // 2))
                
                # Don't handle clicks here - let handle_click do it
                
                y_offset += 100
        else:
            # No servers found - show helpful message
            no_server_panel = pygame.Rect(self.screen_width // 2 - 300, 220, 600, 120)
            pygame.draw.rect(screen, (50, 50, 60), no_server_panel, border_radius=15)
            pygame.draw.rect(screen, (100, 100, 120), no_server_panel, 2, border_radius=15)
            
            no_servers_text = self.font.render("🔍 No servers found", True, (200, 200, 220))
            screen.blit(no_servers_text, (no_server_panel.centerx - no_servers_text.get_width() // 2, no_server_panel.y + 25))
            
            hint1 = self.small_font.render("• Make sure the host is on the same Wi-Fi", True, (150, 150, 170))
            hint2 = self.small_font.render("• Click Refresh to search again", True, (150, 150, 170))
            screen.blit(hint1, (no_server_panel.x + 30, no_server_panel.y + 60))
            screen.blit(hint2, (no_server_panel.x + 30, no_server_panel.y + 85))
        
        # Modern buttons at bottom - responsive positioning
        button_y = min(self.screen_height - 100, 520)  # Adjusted for better fit
        button_height = 50
        button_width = 170
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Join Server button (enabled only if server selected)
        join_x = self.screen_width // 2 - button_width - 110
        join_rect = pygame.Rect(join_x, button_y, button_width, button_height)
        join_enabled = self.selected_server is not None
        join_hovered = join_rect.collidepoint(mouse_pos) and join_enabled
        
        if join_enabled:
            join_color = (60, 180, 60) if join_hovered else (40, 140, 40)
            border_color = (100, 255, 100) if join_hovered else (80, 200, 80)
        else:
            join_color = (60, 60, 60)
            border_color = (100, 100, 100)
        
        shadow_rect = pygame.Rect(join_rect.x + 3, join_rect.y + 3, join_rect.width, join_rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=10)
        pygame.draw.rect(screen, join_color, join_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, join_rect, 3 if join_hovered else 2, border_radius=10)
        
        join_text = self.font.render("🔗 Join", True, (255, 255, 255) if join_enabled else (150, 150, 150))
        screen.blit(join_text, (join_rect.centerx - join_text.get_width() // 2, join_rect.centery - join_text.get_height() // 2))
        self.buttons["join_selected"] = join_rect
        
        # Refresh button
        refresh_x = self.screen_width // 2 - button_width // 2
        refresh_rect = pygame.Rect(refresh_x, button_y, button_width, button_height)
        refresh_hovered = refresh_rect.collidepoint(mouse_pos)
        refresh_color = (60, 60, 180) if refresh_hovered else (40, 40, 140)
        
        shadow_rect = pygame.Rect(refresh_rect.x + 3, refresh_rect.y + 3, refresh_rect.width, refresh_rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=10)
        pygame.draw.rect(screen, refresh_color, refresh_rect, border_radius=10)
        pygame.draw.rect(screen, (100, 100, 255) if refresh_hovered else (80, 80, 200), refresh_rect, 2, border_radius=10)
        
        refresh_text = self.font.render("🔄 Refresh", True, (255, 255, 255))
        screen.blit(refresh_text, (refresh_rect.centerx - refresh_text.get_width() // 2, refresh_rect.centery - refresh_text.get_height() // 2))
        self.buttons["refresh"] = refresh_rect
        
        # Back button
        back_x = self.screen_width // 2 + 110
        back_rect = pygame.Rect(back_x, button_y, button_width, button_height)
        back_hovered = back_rect.collidepoint(mouse_pos)
        back_color = (150, 50, 50) if back_hovered else (120, 30, 30)
        
        shadow_rect = pygame.Rect(back_rect.x + 3, back_rect.y + 3, back_rect.width, back_rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=10)
        pygame.draw.rect(screen, back_color, back_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 100, 100) if back_hovered else (200, 80, 80), back_rect, 2, border_radius=10)
        
        back_text = self.font.render("⬅️ Cancel", True, (255, 255, 255))
        screen.blit(back_text, (back_rect.centerx - back_text.get_width() // 2, back_rect.centery - back_text.get_height() // 2))
        self.buttons["back"] = back_rect
    
    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse clicks on UI elements"""
        # Check buttons in reverse order so overlapping buttons work correctly
        for button_name, button_rect in list(self.buttons.items()):
            if button_rect.collidepoint(mouse_pos):
                print(f"🖱️ Button clicked: {button_name}")
                return button_name
        return None
    
    def handle_input_field_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handle clicks on input fields. Returns True if an input was clicked."""
        for field_name, field_rect in self.input_fields.items():
            if field_rect.collidepoint(mouse_pos):
                # Focus on this input field
                self.focused_field = field_name
                print(f"📝 Input field focused: {field_name}")
                return True
        # Click outside - unfocus
        self.focused_field = None
        return False
    
    def handle_server_click(self, mouse_pos: Tuple[int, int]) -> bool:
        """Handle clicks on server list items. Returns True if a server was clicked."""
        if not self.server_list:
            return False
        
        y_offset = 200
        for server_key, server_info in list(self.server_list.items())[:3]:  # Only first 3 visible
            server_rect = pygame.Rect(50, y_offset, 700, 90)
            if server_rect.collidepoint(mouse_pos):
                self.selected_server = server_key
                print(f"🖱️ Server selected: {server_info.get('name')}")
                return True
            y_offset += 100
        
        return False
    
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
