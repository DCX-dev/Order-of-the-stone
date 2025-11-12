"""
Simple LAN Server for Order of the Stone
Hosts a game world that other players on the same Wi-Fi can join
"""

import socket
import threading
import json
import time
from typing import Dict, List, Any

class LANServer:
    """Simple LAN multiplayer server"""
    
    def __init__(self, host_player_name: str, world_name: str):
        self.host_player_name = host_player_name
        self.world_name = world_name
        self.server_name = f"{host_player_name}'s World"
        
        # Server settings
        self.host = '0.0.0.0'  # Listen on all network interfaces
        self.port = 25565  # Default game port
        self.discovery_port = 25566  # Port for server discovery broadcasts
        
        # Server state
        self.running = False
        self.server_socket = None
        self.discovery_socket = None
        
        # Connected players
        self.players = {}  # {username: {"socket": socket, "position": (x, y), "health": 10, etc}}
        self.player_lock = threading.Lock()
        
        # World state (synchronized across all clients)
        self.world_blocks = {}  # Shared block changes
        self.world_data = None
        
        # Game state (time/weather sync)
        self.game_time = 0  # Server is the source of truth for time
        self.is_day = True
        self.weather = "clear"
        
        print(f"🌐 LAN Server initialized: {self.server_name}")
    
    def start(self, world_data: Dict) -> bool:
        """Start the LAN server"""
        try:
            self.world_data = world_data
            
            # Add host as a player (so clients can see them!)
            with self.player_lock:
                self.players[self.host_player_name] = {
                    "socket": None,  # Host doesn't have a socket
                    "address": ("localhost", 0),
                    "position": (world_data.get("player", {}).get("x", 0), world_data.get("player", {}).get("y", 100)),
                    "health": world_data.get("player", {}).get("health", 10),
                    "facing_direction": 1
                }
            print(f"👤 Added host player: {self.host_player_name}")
            
            # Start main game server
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            
            # Start accepting connections
            accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            accept_thread.start()
            
            # Start discovery responder (so others can find this server)
            discovery_thread = threading.Thread(target=self._discovery_responder, daemon=True)
            discovery_thread.start()
            
            # Start game state sync broadcaster (time/weather)
            sync_thread = threading.Thread(target=self._broadcast_game_state, daemon=True)
            sync_thread.start()
            
            print(f"✅ LAN Server started on port {self.port}")
            print(f"🔍 Server discoverable on port {self.discovery_port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start LAN server: {e}")
            return False
    
    def stop(self):
        """Stop the LAN server"""
        self.running = False
        
        # Disconnect all players
        with self.player_lock:
            for username, player_data in list(self.players.items()):
                try:
                    player_data["socket"].close()
                except:
                    pass
            self.players.clear()
        
        # Close sockets
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        if self.discovery_socket:
            try:
                self.discovery_socket.close()
            except:
                pass
        
        print("🛑 LAN Server stopped")
    
    def _accept_connections(self):
        """Accept incoming player connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"🔌 New connection from {address[0]}:{address[1]}")
                
                # Handle this client in a separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"⚠️ Error accepting connection: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle communication with a connected player"""
        username = None
        buffer = ""  # Buffer for incomplete messages
        
        try:
            # Set socket to non-blocking mode to avoid hanging
            client_socket.settimeout(30.0)
            
            # First message should be login
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            buffer += data
            if '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                message = json.loads(line)
            else:
                message = json.loads(data)
            
            if message.get("type") == "join":
                username = message.get("username", f"Player_{address[1]}")
                
                # Add player to server
                with self.player_lock:
                    self.players[username] = {
                        "socket": client_socket,
                        "address": address,
                        "position": (0, 100),
                        "health": 10,
                        "facing_direction": 1
                    }
                
                # Send welcome message with world data
                welcome = {
                    "type": "welcome",
                    "server_name": self.server_name,
                    "world_name": self.world_name,
                    "world_data": self.world_data,
                    "players": list(self.players.keys())
                }
                self._send_to_client(client_socket, welcome)
                
                # Notify other players
                self._broadcast({
                    "type": "player_joined",
                    "username": username,
                    "position": self.players[username]["position"]
                }, exclude_username=username)
                
                print(f"👋 {username} joined the game! ({len(self.players)} players total)")
                
                # Keep receiving messages from this client
                while self.running:
                    try:
                        data = client_socket.recv(4096).decode('utf-8')
                        if not data:
                            break
                        
                        buffer += data
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if line.strip():
                                try:
                                    message = json.loads(line)
                                    self._process_client_message(username, message)
                                except json.JSONDecodeError:
                                    pass  # Ignore malformed messages
                    
                    except socket.timeout:
                        continue  # Keep connection alive
        
        except Exception as e:
            print(f"⚠️ Error handling client {username}: {e}")
        
        finally:
            # Remove player on disconnect
            if username:
                with self.player_lock:
                    if username in self.players:
                        del self.players[username]
                
                # Notify other players
                self._broadcast({
                    "type": "player_left",
                    "username": username
                })
                
                print(f"👋 {username} left the game")
            
            try:
                client_socket.close()
            except:
                pass
    
    def _process_client_message(self, username: str, message: Dict):
        """Process a message from a client"""
        msg_type = message.get("type")
        
        if msg_type == "player_update":
            # Update player position and state
            with self.player_lock:
                if username in self.players:
                    self.players[username]["position"] = message.get("position", (0, 0))
                    self.players[username]["health"] = message.get("health", 10)
                    self.players[username]["facing_direction"] = message.get("facing_direction", 1)
            
            # Broadcast to other players
            self._broadcast({
                "type": "player_update",
                "username": username,
                "position": message.get("position"),
                "health": message.get("health"),
                "facing_direction": message.get("facing_direction")
            }, exclude_username=username)
        
        elif msg_type == "block_change":
            # Synchronize block changes
            x, y = message.get("x"), message.get("y")
            block_type = message.get("block_type")
            self.world_blocks[f"{x},{y}"] = block_type
            
            # Broadcast to all players
            self._broadcast({
                "type": "block_change",
                "username": username,
                "x": x,
                "y": y,
                "block_type": block_type
            })
        
        elif msg_type == "chat":
            # Broadcast chat message
            chat_text = message.get("message", "")
            self._broadcast({
                "type": "chat",
                "username": username,
                "message": chat_text
            })
            print(f"💬 {username}: {chat_text}")
        
        elif msg_type == "time_update":
            # Host is updating the game time (server should sync this)
            self.game_time = message.get("game_time", 0)
            self.is_day = message.get("is_day", True)
            self.weather = message.get("weather", "clear")
    
    def _send_to_client(self, client_socket: socket.socket, message: Dict):
        """Send a message to a specific client"""
        try:
            data = json.dumps(message).encode('utf-8')
            client_socket.send(data + b'\n')
        except Exception as e:
            print(f"⚠️ Error sending to client: {e}")
    
    def _broadcast(self, message: Dict, exclude_username: str = None):
        """Broadcast a message to all connected players"""
        with self.player_lock:
            for username, player_data in self.players.items():
                if username != exclude_username and player_data["socket"] is not None:
                    self._send_to_client(player_data["socket"], message)
    
    def _discovery_responder(self):
        """Respond to server discovery broadcasts"""
        try:
            # Create UDP socket for discovery
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.discovery_socket.bind(('', self.discovery_port))
            
            print(f"🔍 Discovery responder listening on port {self.discovery_port}")
            
            while self.running:
                try:
                    data, addr = self.discovery_socket.recvfrom(1024)
                    message = data.decode('utf-8')
                    
                    if message == "DISCOVER_SERVER":
                        # Respond with server info
                        response = {
                            "server_name": self.server_name,
                            "host_player": self.host_player_name,
                            "world_name": self.world_name,
                            "players": len(self.players),
                            "max_players": 10,
                            "port": self.port
                        }
                        response_data = json.dumps(response).encode('utf-8')
                        self.discovery_socket.sendto(response_data, addr)
                        print(f"📡 Responded to discovery request from {addr[0]}")
                
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"⚠️ Discovery error: {e}")
        
        except Exception as e:
            print(f"⚠️ Failed to start discovery responder: {e}")
    
    def get_player_count(self) -> int:
        """Get the current number of connected players"""
        with self.player_lock:
            return len(self.players)
    
    def get_players(self) -> List[str]:
        """Get list of connected player usernames"""
        with self.player_lock:
            return list(self.players.keys())
    
    def _broadcast_game_state(self):
        """Periodically broadcast game state (time/weather) to all clients"""
        while self.running:
            try:
                # Broadcast game state every second (not every frame!)
                time.sleep(1.0)
                
                # Send time sync to all clients
                self._broadcast({
                    "type": "time_sync",
                    "game_time": self.game_time,
                    "is_day": self.is_day,
                    "weather": self.weather
                })
                
            except Exception as e:
                if self.running:
                    print(f"⚠️ Error broadcasting game state: {e}")

