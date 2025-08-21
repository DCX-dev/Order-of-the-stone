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
        
    def start_server(self, world_name: str):
        """Start the multiplayer server"""
        self.world_name = world_name
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)
            self.running = True
            
            print(f"🌐 Multiplayer server started on {self.host}:{self.port}")
            print(f"🌍 Hosting world: {self.world_name}")
            
            # Start accepting clients in a separate thread
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
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
            self.client_data[client_id].update(message.get("data", {}))
            # Broadcast to other clients
            self.broadcast_to_clients({
                "type": "player_update",
                "client_id": client_id,
                "data": self.client_data[client_id]
            }, exclude_client=client_id)
            
        elif msg_type == "chat_message":
            # Broadcast chat message to all clients
            self.broadcast_to_clients({
                "type": "chat_message",
                "client_id": client_id,
                "username": self.client_data[client_id].get("username", f"Player{client_id}"),
                "message": message.get("message", "")
            })
            
        elif msg_type == "world_update":
            # Handle world modifications
            self.world_data.update(message.get("world_data", {}))
            self.broadcast_to_clients({
                "type": "world_update",
                "world_data": message.get("world_data", {})
            })
    
    def broadcast_to_clients(self, message: dict, exclude_client: Optional[int] = None):
        """Send message to all connected clients"""
        message_bytes = pickle.dumps(message)
        disconnected_clients = []
        
        for client_id, (client_socket, address) in self.clients.items():
            if client_id != exclude_client:
                try:
                    client_socket.send(message_bytes)
                except Exception as e:
                    print(f"⚠️ Failed to send to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Remove disconnected clients
        for client_id in disconnected_clients:
            self.disconnect_client(client_id)
    
    def disconnect_client(self, client_id: int):
        """Disconnect a specific client"""
        if client_id in self.clients:
            client_socket, address = self.clients[client_id]
            try:
                client_socket.close()
            except:
                pass
            del self.clients[client_id]
            if client_id in self.client_data:
                del self.client_data[client_id]
            print(f"👤 Client {client_id} disconnected")
    
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
            "name": self.world_name,
            "host": self.host,
            "port": self.port,
            "players": len(self.clients),
            "max_players": self.max_players,
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

class ServerDiscovery:
    def __init__(self):
        self.discovery_port = 5556
        self.discovery_socket = None
        self.servers = {}
        
    def start_discovery(self):
        """Start listening for server broadcasts"""
        try:
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.bind(('', self.discovery_port))
            self.discovery_socket.settimeout(1.0)
            print(f"🔍 Server discovery started on port {self.discovery_port}")
            return True
        except Exception as e:
            print(f"❌ Failed to start discovery: {e}")
            return False
    
    def discover_servers(self) -> dict:
        """Discover available servers on the network"""
        servers = {}
        
        # Send broadcast to discover servers
        try:
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send discovery packet
            discovery_packet = pickle.dumps({"type": "discovery_request"})
            broadcast_socket.sendto(discovery_packet, ('<broadcast>', self.discovery_port))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < 2.0:  # Listen for 2 seconds
                try:
                    data, addr = self.discovery_socket.recvfrom(1024)
                    try:
                        response = pickle.loads(data)
                        if response.get("type") == "discovery_response":
                            server_info = response.get("server_info", {})
                            server_key = f"{addr[0]}:{server_info.get('port', 5555)}"
                            servers[server_key] = server_info
                    except Exception as e:
                        print(f"⚠️ Error parsing discovery response: {e}")
                except socket.timeout:
                    continue
                    
            broadcast_socket.close()
            
        except Exception as e:
            print(f"⚠️ Error during server discovery: {e}")
        
        return servers
    
    def stop_discovery(self):
        """Stop server discovery"""
        if self.discovery_socket:
            try:
                self.discovery_socket.close()
            except:
                pass
