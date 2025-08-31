import socket
import threading
import json
import time
import pickle
from typing import Dict, List, Tuple, Optional
import pygame

class MultiplayerServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {client_id: (connection, address)}
        self.client_data = {}  # {client_id: player_data}
        self.world_data = {}
        self.entities = []
        self.running = False
        self.max_players = 8
        self.world_name = "Default World"
        self.server_name = "My Server"
        self.description = "Join for epic adventures!"
        self.version = "1.0.0"
        
    def start_server(self, server_name: str, world_name: str, port: int = 5555):
        """Start the multiplayer server with custom settings"""
        self.server_name = server_name
        self.world_name = world_name
        self.port = port
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)
            self.running = True
            
            print(f"🌐 Multiplayer server started on {self.host}:{self.port}")
            print(f"🌍 Hosting world: {self.world_name}")
            print(f"🏷️ Server name: {self.server_name}")
            
            # Start accepting clients in a separate thread
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Register server with global discovery service
            self.register_with_discovery()
            
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def register_with_discovery(self):
        """Register server with global discovery service"""
        try:
            server_info = {
                "name": self.server_name,
                "world": self.world_name,
                "port": self.port,
                "host": self.host,
                "players": len(self.clients),
                "max_players": self.max_players,
                "description": self.description,
                "version": self.version,
                "status": "running"
            }
            
            # In a real implementation, this would send to a central server registry
            print(f"🌐 Server registered with global discovery service")
            print(f"   Name: {self.server_name}")
            print(f"   World: {self.world_name}")
            print(f"   Port: {self.port}")
            
        except Exception as e:
            print(f"⚠️ Failed to register with discovery service: {e}")
    
    def accept_clients(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                if len(self.clients) < self.max_players:
                    client_id = len(self.clients) + 1
                    self.clients[client_id] = (client_socket, address)
                    self.client_data[client_id] = {
                        "username": f"Player{client_id}",
                        "x": 0,
                        "y": 0,
                        "health": 10,
                        "hunger": 10
                    }
                    
                    print(f"👤 Client {client_id} connected from {address}")
                    
                    # Start client handler thread
                    client_thread = threading.Thread(target=self.handle_client, args=(client_id,))
                    client_thread.daemon = True
                    client_thread.start()
                else:
                    client_socket.close()
                    print("❌ Server full, rejecting connection")
            except Exception as e:
                if self.running:
                    print(f"⚠️ Error accepting client: {e}")
    
    def handle_client(self, client_id: int):
        """Handle communication with a specific client"""
        client_socket, address = self.clients[client_id]
        
        try:
            while self.running and client_id in self.clients:
                # Receive data from client
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = pickle.loads(data)
                    self.process_client_message(client_id, message)
                except Exception as e:
                    print(f"⚠️ Error processing message from client {client_id}: {e}")
                    
        except Exception as e:
            print(f"⚠️ Client {client_id} error: {e}")
        finally:
            self.disconnect_client(client_id)
    
    def process_client_message(self, client_id: int, message: dict):
        """Process messages from clients"""
        msg_type = message.get("type")
        
        if msg_type == "player_update":
            # Update player position and state
            if client_id in self.client_data:
                self.client_data[client_id].update(message.get("data", {}))
                
                # Broadcast to other clients
                self.broadcast_to_clients({
                    "type": "player_update",
                    "client_id": client_id,
                    "data": self.client_data[client_id]
                }, exclude_client=client_id)
                
        elif msg_type == "chat":
            # Broadcast chat message to all clients
            chat_data = {
                "type": "chat",
                "username": message.get("username", f"Player{client_id}"),
                "message": message.get("message", ""),
                "timestamp": time.time()
            }
            self.broadcast_to_clients(chat_data)
            print(f"💬 {chat_data['username']}: {chat_data['message']}")
            
        elif msg_type == "player_join":
            # New player joined
            username = message.get("username", f"Player{client_id}")
            if client_id in self.client_data:
                self.client_data[client_id]["username"] = username
            
            # Notify other clients
            self.broadcast_to_clients({
                "type": "player_joined",
                "username": username,
                "client_id": client_id
            }, exclude_client=client_id)
            
            # Send current world state to new player
            self.send_to_client(client_id, {
                "type": "world_state",
                "world_data": self.world_data,
                "entities": self.entities,
                "players": self.client_data
            })
    
    def broadcast_to_clients(self, message: dict, exclude_client: int = None):
        """Send message to all connected clients"""
        message_bytes = pickle.dumps(message)
        for client_id, (client_socket, address) in self.clients.items():
            if client_id != exclude_client:
                try:
                    client_socket.send(message_bytes)
                except Exception as e:
                    print(f"⚠️ Failed to send to client {client_id}: {e}")
                    self.disconnect_client(client_id)
    
    def send_to_client(self, client_id: int, message: dict):
        """Send message to specific client"""
        if client_id in self.clients:
            client_socket, address = self.clients[client_id]
            try:
                message_bytes = pickle.dumps(message)
                client_socket.send(message_bytes)
            except Exception as e:
                print(f"⚠️ Failed to send to client {client_id}: {e}")
                self.disconnect_client(client_id)
    
    def disconnect_client(self, client_id: int):
        """Disconnect a specific client"""
        if client_id in self.clients:
            client_socket, address = self.clients[client_id]
            try:
                client_socket.close()
            except:
                pass
            
            # Remove from client lists
            del self.clients[client_id]
            if client_id in self.client_data:
                del self.client_data[client_id]
            
            print(f"🔌 Client {client_id} disconnected")
            
            # Notify other clients
            self.broadcast_to_clients({
                "type": "player_left",
                "client_id": client_id
            })
    
    def stop_server(self):
        """Stop the multiplayer server"""
        self.running = False
        
        # Disconnect all clients
        for client_id in list(self.clients.keys()):
            self.disconnect_client(client_id)
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("🛑 Multiplayer server stopped")
    
    def get_server_info(self) -> dict:
        """Get server information for discovery"""
        return {
            "name": self.server_name,
            "world": self.world_name,
            "host": self.host,
            "port": self.port,
            "players": len(self.clients),
            "max_players": self.max_players,
            "description": self.description,
            "version": self.version,
            "status": "running" if self.running else "stopped"
        }

class MultiplayerClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.server_info = {}
        self.other_players = {}
        self.chat_messages = []
        self.username = "Player"
        
    def connect_to_server(self, host: str, port: int, username: str) -> bool:
        """Connect to a multiplayer server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.username = username
            self.connected = True
            
            # Send initial player data
            self.send_message({
                "type": "player_join",
                "username": username
            })
            
            print(f"✅ Connected to server {host}:{port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to server: {e}")
            return False
    
    def send_message(self, message: dict):
        """Send a message to the server"""
        if self.connected and self.socket:
            try:
                message_bytes = pickle.dumps(message)
                self.socket.send(message_bytes)
            except Exception as e:
                print(f"⚠️ Failed to send message: {e}")
                self.disconnect()
    
    def receive_messages(self):
        """Receive and process messages from the server"""
        if not self.connected or not self.socket:
            return []
        
        messages = []
        try:
            # Set non-blocking mode
            self.socket.setblocking(False)
            
            while True:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    
                    message = pickle.loads(data)
                    messages.append(message)
                    
                except BlockingIOError:
                    break
                except Exception as e:
                    print(f"⚠️ Error receiving message: {e}")
                    break
                    
        except Exception as e:
            print(f"⚠️ Error in receive loop: {e}")
            self.disconnect()
        
        return messages
    
    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.other_players.clear()
        print("🔌 Disconnected from server")

class GlobalServerDiscovery:
    """Global server discovery service"""
    
    def __init__(self):
        self.discovery_url = "https://api.example.com/servers"  # Placeholder URL
        self.local_discovery_port = 5556
        self.servers = {}
        
    def discover_servers(self) -> List[dict]:
        """Discover servers from multiple sources"""
        discovered_servers = []
        
        # 1. Try global discovery service
        try:
            global_servers = self.discover_from_global_service()
            discovered_servers.extend(global_servers)
            print(f"🌐 Found {len(global_servers)} servers from global service")
        except Exception as e:
            print(f"⚠️ Global discovery failed: {e}")
        
        # 2. Try local network discovery
        try:
            local_servers = self.discover_from_local_network()
            discovered_servers.extend(local_servers)
            print(f"🏠 Found {len(local_servers)} servers from local network")
        except Exception as e:
            print(f"⚠️ Local discovery failed: {e}")
        
        # 3. Add some demo servers for testing
        demo_servers = self.get_demo_servers()
        discovered_servers.extend(demo_servers)
        print(f"🎮 Added {len(demo_servers)} demo servers")
        
        # Remove duplicates and sort by player count
        unique_servers = self.remove_duplicates(discovered_servers)
        unique_servers.sort(key=lambda x: x.get("players", 0), reverse=True)
        
        self.servers = {server["name"]: server for server in unique_servers}
        return unique_servers
    
    def discover_from_global_service(self) -> List[dict]:
        """Discover servers from global service (placeholder)"""
        # In a real implementation, this would query a central server registry
        # For now, return empty list
        return []
    
    def discover_from_local_network(self) -> List[dict]:
        """Discover servers on local network using UDP broadcast"""
        local_servers = []
        
        try:
            # Create UDP socket for discovery
            discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            discovery_socket.settimeout(2.0)
            discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send discovery broadcast
            discovery_message = pickle.dumps({"type": "server_discovery"})
            discovery_socket.sendto(discovery_message, ('<broadcast>', self.local_discovery_port))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < 3.0:  # Listen for 3 seconds
                try:
                    data, addr = discovery_socket.recvfrom(1024)
                    server_info = pickle.loads(data)
                    if server_info.get("type") == "server_info":
                        server_info["address"] = addr[0]
                        local_servers.append(server_info)
                except socket.timeout:
                    break
                except Exception as e:
                    continue
            
            discovery_socket.close()
            
        except Exception as e:
            print(f"⚠️ Local network discovery error: {e}")
        
        return local_servers
    
    def get_demo_servers(self) -> List[dict]:
        """Get demo servers for testing"""
        return [
            {
                "name": "Epic Adventure Server",
                "world": "Epic World",
                "players": 3,
                "max_players": 20,
                "version": "1.0.0",
                "description": "Join us for epic adventures!",
                "address": "127.0.0.1",
                "port": 5555
            },
            {
                "name": "Creative Building Server", 
                "world": "Creative World",
                "players": 8,
                "max_players": 20,
                "version": "1.0.0",
                "description": "Build amazing creations together!",
                "address": "127.0.0.2",
                "port": 5555
            },
            {
                "name": "Survival Challenge",
                "world": "Hardcore World",
                "players": 12,
                "max_players": 15,
                "version": "1.0.0",
                "description": "Survive the ultimate challenge!",
                "address": "127.0.0.3",
                "port": 5555
            }
        ]
    
    def remove_duplicates(self, servers: List[dict]) -> List[dict]:
        """Remove duplicate servers based on name and address"""
        seen = set()
        unique_servers = []
        
        for server in servers:
            key = (server.get("name"), server.get("address"), server.get("port"))
            if key not in seen:
                seen.add(key)
                unique_servers.append(server)
        
        return unique_servers

class ServerDiscovery:
    def __init__(self):
        self.discovery_port = 5556
        self.discovery_socket = None
        self.servers = {}
        self.global_discovery = GlobalServerDiscovery()
        
    def start_discovery(self):
        """Start listening for server broadcasts"""
        try:
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.bind(('', self.discovery_port))
            self.discovery_socket.settimeout(1.0)
            print(f"🔍 Server discovery started on port {self.discovery_port}")
        except Exception as e:
            print(f"⚠️ Failed to start discovery: {e}")
    
    def discover_servers(self) -> List[dict]:
        """Discover available servers"""
        return self.global_discovery.discover_servers()
