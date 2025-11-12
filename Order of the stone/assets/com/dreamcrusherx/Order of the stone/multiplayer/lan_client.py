"""
Simple LAN Client for Order of the Stone
Discovers and connects to games on the same Wi-Fi network
"""

import socket
import threading
import json
import time
from typing import Dict, List, Optional, Callable

class LANClient:
    """Simple LAN multiplayer client"""
    
    def __init__(self, username: str):
        self.username = username
        
        # Connection settings
        self.discovery_port = 25566
        self.game_port = 25565
        
        # Connection state
        self.connected = False
        self.server_socket = None
        self.server_address = None
        
        # Received data
        self.world_data = None
        self.other_players = {}  # {username: {"position": (x, y), "health": 10, etc}}
        
        # Game state sync
        self.game_time = 0
        self.is_day = True
        self.weather = "clear"
        
        # Callbacks for game integration
        self.on_player_joined = None  # Callback(username, position)
        self.on_player_left = None  # Callback(username)
        self.on_player_update = None  # Callback(username, position, health, facing_direction)
        self.on_block_change = None  # Callback(username, x, y, block_type)
        self.on_chat_message = None  # Callback(username, message)
        self.on_time_sync = None  # Callback(game_time, is_day, weather)
        
        # Receive thread
        self.receive_thread = None
        self.running = False
        
        print(f"🔗 LAN Client initialized for user: {username}")
    
    def discover_servers(self, timeout: float = 1.0) -> List[Dict]:
        """Discover available LAN servers on the network (fast, non-blocking)"""
        discovered_servers = []
        
        try:
            # Create UDP socket for broadcasting
            discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            discover_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            discover_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            discover_socket.settimeout(0.3)  # Very short timeout per attempt
            
            # Broadcast discovery message
            message = "DISCOVER_SERVER".encode('utf-8')
            discover_socket.sendto(message, ('<broadcast>', self.discovery_port))
            
            # Listen for responses - quick scan only
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = discover_socket.recvfrom(1024)
                    response = json.loads(data.decode('utf-8'))
                    
                    # Add server info with IP address
                    server_info = {
                        "server_name": response.get("server_name", "Unknown Server"),
                        "host_player": response.get("host_player", "Unknown"),
                        "world_name": response.get("world_name", "World"),
                        "players": response.get("players", 0),
                        "max_players": response.get("max_players", 10),
                        "ip_address": addr[0],
                        "port": response.get("port", self.game_port)
                    }
                    
                    # Avoid duplicates
                    if not any(s["ip_address"] == server_info["ip_address"] for s in discovered_servers):
                        discovered_servers.append(server_info)
                        print(f"✅ Found server: {server_info['server_name']} at {addr[0]}")
                
                except socket.timeout:
                    continue
                except Exception as e:
                    pass  # Silently ignore errors during discovery
            
            discover_socket.close()
            
        except Exception as e:
            pass  # Silently fail
        
        return discovered_servers
    
    def connect_to_server(self, server_ip: str, server_port: int = None) -> bool:
        """Connect to a LAN server"""
        if server_port is None:
            server_port = self.game_port
        
        try:
            # Create TCP socket for game connection
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.settimeout(10.0)
            self.server_socket.connect((server_ip, server_port))
            self.server_address = (server_ip, server_port)
            self.connected = True
            
            print(f"🔗 Connected to server at {server_ip}:{server_port}")
            
            # Send join request
            join_message = {
                "type": "join",
                "username": self.username
            }
            self._send_message(join_message)
            
            # Start receiving messages
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        self.connected = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        print("🔌 Disconnected from server")
    
    def send_player_update(self, position: tuple, health: int, facing_direction: int):
        """Send player position and state update to server"""
        if not self.connected:
            return
        
        message = {
            "type": "player_update",
            "position": position,
            "health": health,
            "facing_direction": facing_direction
        }
        self._send_message(message)
    
    def send_block_change(self, x: int, y: int, block_type: str):
        """Send block change to server"""
        if not self.connected:
            return
        
        message = {
            "type": "block_change",
            "x": x,
            "y": y,
            "block_type": block_type
        }
        self._send_message(message)
    
    def send_chat_message(self, text: str):
        """Send chat message to server"""
        if not self.connected:
            return
        
        message = {
            "type": "chat",
            "message": text
        }
        self._send_message(message)
    
    def _send_message(self, message: Dict):
        """Send a message to the server"""
        if not self.connected or not self.server_socket:
            return
        
        try:
            data = json.dumps(message).encode('utf-8')
            self.server_socket.send(data + b'\n')
        except Exception as e:
            print(f"⚠️ Error sending message: {e}")
            self.connected = False
    
    def _receive_messages(self):
        """Receive messages from the server"""
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.server_socket.recv(4096).decode('utf-8')
                if not data:
                    print("⚠️ Connection lost")
                    self.connected = False
                    break
                
                # Add to buffer and process complete messages
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        try:
                            message = json.loads(line)
                            self._process_server_message(message)
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Invalid JSON: {e}")
            
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠️ Error receiving message: {e}")
                self.connected = False
                break
    
    def _process_server_message(self, message: Dict):
        """Process a message from the server"""
        msg_type = message.get("type")
        
        if msg_type == "welcome":
            # Received welcome with world data
            self.world_data = message.get("world_data")
            players = message.get("players", [])
            print(f"✅ Joined server: {message.get('server_name')}")
            print(f"👥 Players online: {', '.join(players)}")
        
        elif msg_type == "player_joined":
            # Another player joined
            username = message.get("username")
            position = message.get("position", (0, 100))
            self.other_players[username] = {
                "position": position,
                "health": 10,
                "facing_direction": 1
            }
            print(f"👋 {username} joined the game")
            
            if self.on_player_joined:
                self.on_player_joined(username, position)
        
        elif msg_type == "player_left":
            # Another player left
            username = message.get("username")
            if username in self.other_players:
                del self.other_players[username]
            print(f"👋 {username} left the game")
            
            if self.on_player_left:
                self.on_player_left(username)
        
        elif msg_type == "player_update":
            # Another player moved/updated
            username = message.get("username")
            position = message.get("position")
            health = message.get("health")
            facing_direction = message.get("facing_direction", 1)
            
            # Store old position for smooth interpolation
            if username in self.other_players:
                self.other_players[username]["old_position"] = self.other_players[username]["position"]
                self.other_players[username]["position"] = position
                self.other_players[username]["health"] = health
                self.other_players[username]["facing_direction"] = facing_direction
                self.other_players[username]["last_update"] = time.time()
            else:
                # New player we just learned about
                self.other_players[username] = {
                    "position": position,
                    "old_position": position,
                    "health": health,
                    "facing_direction": facing_direction,
                    "last_update": time.time()
                }
            
            if self.on_player_update:
                self.on_player_update(username, position, health, facing_direction)
        
        elif msg_type == "block_change":
            # Block was placed/broken
            username = message.get("username")
            x, y = message.get("x"), message.get("y")
            block_type = message.get("block_type")
            
            if self.on_block_change:
                self.on_block_change(username, x, y, block_type)
        
        elif msg_type == "chat":
            # Chat message received
            username = message.get("username")
            text = message.get("message")
            print(f"💬 {username}: {text}")
            
            if self.on_chat_message:
                self.on_chat_message(username, text)
        
        elif msg_type == "time_sync":
            # Server is syncing game time to us
            self.game_time = message.get("game_time", 0)
            self.is_day = message.get("is_day", True)
            self.weather = message.get("weather", "clear")
            
            if self.on_time_sync:
                self.on_time_sync(self.game_time, self.is_day, self.weather)
    
    def is_connected(self) -> bool:
        """Check if client is connected to a server"""
        return self.connected
    
    def get_other_players(self) -> Dict:
        """Get dictionary of other players with smooth interpolation"""
        result = {}
        current_time = time.time()
        
        for username, player_data in self.other_players.items():
            # Create a copy
            player_copy = player_data.copy()
            
            # Smooth interpolation for position (prevents teleporting)
            if "old_position" in player_data and "last_update" in player_data:
                time_since_update = current_time - player_data["last_update"]
                # Interpolate over 0.1 seconds (100ms)
                t = min(time_since_update / 0.1, 1.0)
                
                old_x, old_y = player_data["old_position"]
                new_x, new_y = player_data["position"]
                
                # Linear interpolation
                smooth_x = old_x + (new_x - old_x) * t
                smooth_y = old_y + (new_y - old_y) * t
                
                player_copy["position"] = (smooth_x, smooth_y)
            
            result[username] = player_copy
        
        return result

