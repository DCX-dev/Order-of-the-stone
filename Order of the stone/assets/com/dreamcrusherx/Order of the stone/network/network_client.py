#!/usr/bin/env python3
"""
Network Client for Order of the Stone
=====================================

A comprehensive multiplayer client that connects to the network server.
"""

import socket
import threading
import json
import time
import pickle
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ServerInfo:
    """Server information"""
    name: str
    host: str
    port: int
    players: int
    max_players: int
    version: str
    uptime: float

class NetworkClient:
    """Network client for connecting to multiplayer servers"""
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.server_info = None
        self.username = "Player"
        self.current_world = "Default World"
        
        # Message handlers
        self.message_handlers = {
            "login_response": self.handle_login_response,
            "player_joined": self.handle_player_joined,
            "player_left": self.handle_player_left,
            "player_update": self.handle_player_update,
            "chat": self.handle_chat,
            "block_change": self.handle_block_change,
            "world_data": self.handle_world_data,
            "world_updated": self.handle_world_updated,
            "permission_response": self.handle_permission_response
        }
        
        # Callbacks for game integration
        self.on_player_joined = None
        self.on_player_left = None
        self.on_player_update = None
        self.on_chat_message = None
        self.on_block_change = None
        self.on_world_update = None
        
        # Message queue
        self.message_queue = []
        self.message_lock = threading.Lock()
        
        # Connection thread
        self.receive_thread = None
        self.running = False
    
    def connect_to_server(self, host: str, port: int, username: str, world: str = "Default World") -> bool:
        """Connect to a multiplayer server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # 10 second timeout
            self.socket.connect((host, port))
            
            self.username = username
            self.current_world = world
            self.connected = True
            self.running = True
            
            logger.info(f"🔗 Connected to server {host}:{port}")
            
            # Start receiving messages
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Send login message
            self.send_message({
                "type": "login",
                "username": username,
                "world": world
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to server: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        logger.info("🔌 Disconnected from server")
    
    def send_message(self, message: Dict):
        """Send a message to the server"""
        if not self.connected or not self.socket:
            return False
        
        try:
            message_bytes = pickle.dumps(message)
            self.socket.send(message_bytes)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.connected = False
            return False
    
    def receive_messages(self):
        """Receive messages from the server"""
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                
                # Parse message
                try:
                    message = pickle.loads(data)
                    self.handle_message(message)
                except pickle.UnpicklingError:
                    logger.warning("Invalid message format received")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error receiving message: {e}")
                break
        
        # Connection lost
        self.connected = False
        logger.warning("Connection to server lost")
    
    def handle_message(self, message: Dict):
        """Handle incoming messages from the server"""
        msg_type = message.get("type")
        
        if msg_type in self.message_handlers:
            self.message_handlers[msg_type](message)
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    def handle_login_response(self, message: Dict):
        """Handle login response from server"""
        success = message.get("success", False)
        
        if success:
            logger.info("✅ Login successful")
            player_data = message.get("player_data", {})
            world_data = message.get("world_data", {})
            recent_chat = message.get("recent_chat", [])
            
            # Process received data
            logger.info(f"👤 Player data received: {len(player_data)} fields")
            logger.info(f"🌍 World data received: {len(world_data)} blocks")
            logger.info(f"💬 Recent chat: {len(recent_chat)} messages")
            
        else:
            logger.error("❌ Login failed")
            self.disconnect()
    
    def handle_player_joined(self, message: Dict):
        """Handle player joined notification"""
        username = message.get("username")
        player_data = message.get("player_data", {})
        
        logger.info(f"👋 Player joined: {username}")
        
        # Call callback if set
        if self.on_player_joined:
            self.on_player_joined(username, player_data)
    
    def handle_player_left(self, message: Dict):
        """Handle player left notification"""
        username = message.get("username")
        
        logger.info(f"👋 Player left: {username}")
        
        # Call callback if set
        if self.on_player_left:
            self.on_player_left(username)
    
    def handle_player_update(self, message: Dict):
        """Handle player update notification"""
        username = message.get("username")
        data = message.get("data", {})
        
        # Call callback if set
        if self.on_player_update:
            self.on_player_update(username, data)
    
    def handle_chat(self, message: Dict):
        """Handle chat message"""
        username = message.get("username")
        chat_text = message.get("message")
        timestamp = message.get("timestamp")
        msg_type = message.get("message_type", "world")
        
        logger.info(f"💬 {username}: {chat_text} ({msg_type})")
        
        # Call callback if set
        if self.on_chat_message:
            self.on_chat_message(username, chat_text, timestamp, msg_type)
    
    def handle_block_change(self, message: Dict):
        """Handle block change notification"""
        x = message.get("x")
        y = message.get("y")
        block_type = message.get("block_type")
        player = message.get("player")
        
        logger.info(f"🔨 Block change: {player} placed {block_type} at ({x}, {y})")
        
        # Call callback if set
        if self.on_block_change:
            self.on_block_change(x, y, block_type, player)
    
    def handle_world_data(self, message: Dict):
        """Handle world data response"""
        world = message.get("world")
        data = message.get("data", {})
        
        logger.info(f"🌍 World data received for {world}: {len(data)} blocks")
        
        # Call callback if set
        if self.on_world_update:
            self.on_world_update(world, data)
    
    def handle_world_updated(self, message: Dict):
        """Handle world update notification"""
        world = message.get("world")
        last_modified = message.get("last_modified")
        
        logger.info(f"🌍 World {world} updated at {time.ctime(last_modified)}")
    
    def handle_permission_response(self, message: Dict):
        """Handle permission response"""
        success = message.get("success", False)
        message_text = message.get("message", "")
        
        if success:
            logger.info(f"✅ Permission request successful: {message_text}")
        else:
            logger.warning(f"❌ Permission request failed: {message_text}")
    
    # Convenience methods for game integration
    
    def send_player_update(self, position: Tuple[float, float], health: int, hunger: int, stamina: int, inventory: List[str]):
        """Send player update to server"""
        self.send_message({
            "type": "player_update",
            "data": {
                "position": position,
                "health": health,
                "hunger": hunger,
                "stamina": stamina,
                "inventory": inventory
            },
            "world": self.current_world
        })
    
    def send_chat_message(self, message: str, message_type: str = "world"):
        """Send chat message to server"""
        self.send_message({
            "type": "chat",
            "message": message,
            "world": self.current_world,
            "message_type": message_type
        })
    
    def send_block_change(self, x: int, y: int, block_type: str):
        """Send block change to server"""
        self.send_message({
            "type": "block_change",
            "x": x,
            "y": y,
            "block_type": block_type,
            "world": self.current_world
        })
    
    def request_world_data(self, world_name: str = None):
        """Request world data from server"""
        if world_name is None:
            world_name = self.current_world
            
        self.send_message({
            "type": "world_request",
            "world": world_name
        })
    
    def save_world(self, world_data: Dict):
        """Save world data to server"""
        self.send_message({
            "type": "world_save",
            "world": self.current_world,
            "data": world_data
        })
    
    def request_permission(self, target_username: str, permission_level: int):
        """Request permission change for another player"""
        self.send_message({
            "type": "permission_request",
            "target_username": target_username,
            "permission": permission_level
        })
    
    def is_connected(self) -> bool:
        """Check if client is connected to server"""
        return self.connected and self.socket is not None
    
    def get_connection_info(self) -> Optional[Dict]:
        """Get current connection information"""
        if not self.is_connected():
            return None
            
        return {
            "username": self.username,
            "world": self.current_world,
            "connected": self.connected
        }

class ServerDiscovery:
    """Server discovery service"""
    
    def __init__(self):
        self.discovery_port = 5556
        self.servers = []
    
    def discover_servers(self, timeout: float = 5.0) -> List[ServerInfo]:
        """Discover available servers on the network"""
        discovered_servers = []
        
        try:
            # Create UDP socket for discovery
            discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            discovery_socket.settimeout(timeout)
            discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send discovery broadcast
            discovery_message = pickle.dumps({"type": "server_discovery"})
            discovery_socket.sendto(discovery_message, ('<broadcast>', self.discovery_port))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = discovery_socket.recvfrom(1024)
                    server_info = pickle.loads(data)
                    
                    if server_info.get("type") == "server_info":
                        server = ServerInfo(
                            name=server_info.get("name", "Unknown Server"),
                            host=addr[0],
                            port=server_info.get("port", 5555),
                            players=server_info.get("players", 0),
                            max_players=server_info.get("max_players", 20),
                            version=server_info.get("version", "1.0.0"),
                            uptime=server_info.get("uptime", 0)
                        )
                        discovered_servers.append(server)
                        
                except socket.timeout:
                    break
                except Exception as e:
                    logger.warning(f"Error processing discovery response: {e}")
                    continue
            
            discovery_socket.close()
            
        except Exception as e:
            logger.error(f"Server discovery failed: {e}")
        
        # Add some demo servers for testing
        demo_servers = [
            ServerInfo("Epic Adventure Server", "127.0.0.1", 5555, 3, 20, "1.0.0", 3600),
            ServerInfo("Creative Building Server", "127.0.0.2", 5555, 8, 20, "1.0.0", 7200),
            ServerInfo("Survival Challenge", "127.0.0.3", 5555, 12, 15, "1.0.0", 1800)
        ]
        
        discovered_servers.extend(demo_servers)
        
        logger.info(f"🔍 Discovered {len(discovered_servers)} servers")
        return discovered_servers

if __name__ == "__main__":
    # Test the client
    client = NetworkClient()
    
    # Set up callbacks
    def on_player_joined(username, data):
        print(f"👋 {username} joined the game!")
    
    def on_chat_message(username, message, timestamp, msg_type):
        print(f"💬 {username}: {message}")
    
    client.on_player_joined = on_player_joined
    client.on_chat_message = on_chat_message
    
    # Try to connect to local server
    if client.connect_to_server("127.0.0.1", 5555, "TestPlayer"):
        print("✅ Connected to server!")
        
        # Send a test message
        client.send_chat_message("Hello, server!")
        
        # Keep connection alive for a bit
        time.sleep(5)
        
        client.disconnect()
    else:
        print("❌ Failed to connect to server")
    
    # Test server discovery
    discovery = ServerDiscovery()
    servers = discovery.discover_servers()
    
    print(f"\n🔍 Found {len(servers)} servers:")
    for server in servers:
        print(f"  - {server.name} ({server.host}:{server.port}) - {server.players}/{server.max_players} players")
