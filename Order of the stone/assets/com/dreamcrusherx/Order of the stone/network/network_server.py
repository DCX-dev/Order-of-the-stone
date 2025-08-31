#!/usr/bin/env python3
"""
Network Server for Order of the Stone
=====================================

A comprehensive multiplayer server with:
- User permissions and authentication
- Block storage and synchronization
- Persistent chat history
- World management
- Player data persistence
"""

import socket
import threading
import json
import time
import pickle
import hashlib
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Permission(Enum):
    """Player permission levels"""
    GUEST = 0
    PLAYER = 1
    MODERATOR = 2
    ADMIN = 3
    OWNER = 4

@dataclass
class Player:
    """Player data structure"""
    username: str
    permission: Permission
    last_seen: float
    is_online: bool
    world_data: Dict[str, Any]
    inventory: List[str]
    position: Tuple[float, float]
    health: int
    hunger: int
    stamina: int

@dataclass
class ChatMessage:
    """Chat message structure"""
    id: int
    username: str
    message: str
    timestamp: float
    world: str
    message_type: str  # "global", "world", "private"

@dataclass
class BlockChange:
    """Block change structure"""
    x: int
    y: int
    block_type: str
    timestamp: float
    player: str
    world: str

class NetworkServer:
    """Main network server class"""
    
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {client_id: (connection, address)}
        self.players = {}  # {username: Player}
        self.worlds = {}   # {world_name: world_data}
        self.running = False
        self.max_players = 20
        self.server_name = "Order of the Stone Network"
        self.version = "1.0.0"
        
        # Database
        self.db_path = "network_server.db"
        self.init_database()
        
        # Load existing data
        self.load_players()
        self.load_worlds()
        self.load_chat_history()
        
        # Server stats
        self.stats = {
            "start_time": time.time(),
            "total_connections": 0,
            "messages_sent": 0,
            "blocks_changed": 0
        }
    
    def init_database(self):
        """Initialize SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create tables
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    username TEXT PRIMARY KEY,
                    permission INTEGER,
                    last_seen REAL,
                    world_data TEXT,
                    inventory TEXT,
                    position TEXT,
                    health INTEGER,
                    hunger INTEGER,
                    stamina INTEGER
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    message TEXT,
                    timestamp REAL,
                    world TEXT,
                    message_type TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS block_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    x INTEGER,
                    y INTEGER,
                    block_type TEXT,
                    timestamp REAL,
                    player TEXT,
                    world TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS worlds (
                    name TEXT PRIMARY KEY,
                    data TEXT,
                    last_modified REAL,
                    owner TEXT
                )
            ''')
            
            self.conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def load_players(self):
        """Load existing players from database"""
        try:
            self.cursor.execute("SELECT * FROM players")
            rows = self.cursor.fetchall()
            
            for row in rows:
                username, permission, last_seen, world_data, inventory, position, health, hunger, stamina = row
                
                player = Player(
                    username=username,
                    permission=Permission(permission),
                    last_seen=last_seen,
                    is_online=False,
                    world_data=json.loads(world_data) if world_data else {},
                    inventory=json.loads(inventory) if inventory else [],
                    position=tuple(json.loads(position)) if position else (0, 0),
                    health=health,
                    hunger=hunger,
                    stamina=stamina
                )
                
                self.players[username] = player
                
            logger.info(f"Loaded {len(self.players)} players from database")
            
        except Exception as e:
            logger.error(f"Failed to load players: {e}")
    
    def load_worlds(self):
        """Load existing worlds from database"""
        try:
            self.cursor.execute("SELECT * FROM worlds")
            rows = self.cursor.fetchall()
            
            for row in rows:
                name, data, last_modified, owner = row
                self.worlds[name] = {
                    "data": json.loads(data) if data else {},
                    "last_modified": last_modified,
                    "owner": owner
                }
                
            logger.info(f"Loaded {len(self.worlds)} worlds from database")
            
        except Exception as e:
            logger.error(f"Failed to load worlds: {e}")
    
    def load_chat_history(self):
        """Load recent chat history"""
        try:
            self.cursor.execute("""
                SELECT * FROM chat_messages 
                ORDER BY timestamp DESC 
                LIMIT 100
            """)
            rows = self.cursor.fetchall()
            
            # Store recent messages in memory
            self.recent_chat = []
            for row in rows:
                msg_id, username, message, timestamp, world, msg_type = row
                chat_msg = ChatMessage(
                    id=msg_id,
                    username=username,
                    message=message,
                    timestamp=timestamp,
                    world=world,
                    message_type=msg_type
                )
                self.recent_chat.append(chat_msg)
                
            logger.info(f"Loaded {len(self.recent_chat)} recent chat messages")
            
        except Exception as e:
            logger.error(f"Failed to load chat history: {e}")
    
    def save_player(self, player: Player):
        """Save player data to database"""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO players 
                (username, permission, last_seen, world_data, inventory, position, health, hunger, stamina)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player.username,
                player.permission.value,
                player.last_seen,
                json.dumps(player.world_data),
                json.dumps(player.inventory),
                json.dumps(player.position),
                player.health,
                player.hunger,
                player.stamina
            ))
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save player {player.username}: {e}")
    
    def save_chat_message(self, message: ChatMessage):
        """Save chat message to database"""
        try:
            self.cursor.execute("""
                INSERT INTO chat_messages (username, message, timestamp, world, message_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                message.username,
                message.message,
                message.timestamp,
                message.world,
                message.message_type
            ))
            self.conn.commit()
            
            # Add to recent chat
            self.recent_chat.append(message)
            if len(self.recent_chat) > 100:
                self.recent_chat.pop(0)
                
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")
    
    def save_block_change(self, block_change: BlockChange):
        """Save block change to database"""
        try:
            self.cursor.execute("""
                INSERT INTO block_changes (x, y, block_type, timestamp, player, world)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                block_change.x,
                block_change.y,
                block_change.block_type,
                block_change.timestamp,
                block_change.player,
                block_change.world
            ))
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save block change: {e}")
    
    def save_world(self, world_name: str, world_data: Dict, owner: str):
        """Save world data to database"""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO worlds (name, data, last_modified, owner)
                VALUES (?, ?, ?, ?)
            """, (
                world_name,
                json.dumps(world_data),
                time.time(),
                owner
            ))
            self.conn.commit()
            
            # Update in-memory worlds
            self.worlds[world_name] = {
                "data": world_data,
                "last_modified": time.time(),
                "owner": owner
            }
            
        except Exception as e:
            logger.error(f"Failed to save world {world_name}: {e}")
    
    def start_server(self, server_name: str = None):
        """Start the network server"""
        if server_name:
            self.server_name = server_name
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_players)
            self.running = True
            
            logger.info(f"🌐 Network server started on {self.host}:{self.port}")
            logger.info(f"🏷️ Server name: {self.server_name}")
            logger.info(f"🔌 Max players: {self.max_players}")
            
            # Start accepting clients in a separate thread
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Start periodic tasks
            self.start_periodic_tasks()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start server: {e}")
            return False
    
    def start_periodic_tasks(self):
        """Start periodic server maintenance tasks"""
        def periodic_save():
            while self.running:
                time.sleep(300)  # Save every 5 minutes
                self.save_all_data()
                
        def periodic_cleanup():
            while self.running:
                time.sleep(60)  # Cleanup every minute
                self.cleanup_offline_players()
        
        # Start periodic tasks
        threading.Thread(target=periodic_save, daemon=True).start()
        threading.Thread(target=periodic_cleanup, daemon=True).start()
    
    def accept_clients(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_id = self.stats["total_connections"]
                self.stats["total_connections"] += 1
                
                logger.info(f"🔌 New connection from {address[0]}:{address[1]} (ID: {client_id})")
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_id, client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting client: {e}")
    
    def handle_client(self, client_id: int, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle individual client connection"""
        try:
            while self.running:
                # Receive message
                data = client_socket.recv(4096)
                if not data:
                    break
                
                # Parse message
                try:
                    message = pickle.loads(data)
                    self.process_client_message(client_id, message, client_socket)
                except pickle.UnpicklingError:
                    logger.warning(f"Invalid message format from client {client_id}")
                    
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.disconnect_client(client_id)
    
    def process_client_message(self, client_id: int, message: Dict, client_socket: socket.socket):
        """Process messages from clients"""
        msg_type = message.get("type")
        
        if msg_type == "login":
            self.handle_login(client_id, message, client_socket)
        elif msg_type == "player_update":
            self.handle_player_update(client_id, message)
        elif msg_type == "chat":
            self.handle_chat(client_id, message)
        elif msg_type == "block_change":
            self.handle_block_change(client_id, message)
        elif msg_type == "world_request":
            self.handle_world_request(client_id, message, client_socket)
        elif msg_type == "world_save":
            self.handle_world_save(client_id, message)
        elif msg_type == "permission_request":
            self.handle_permission_request(client_id, message, client_socket)
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    def handle_login(self, client_id: int, message: Dict, client_socket: socket.socket):
        """Handle player login"""
        username = message.get("username", f"Player{client_id}")
        world_name = message.get("world", "Default World")
        
        # Check if player exists
        if username in self.players:
            player = self.players[username]
            player.is_online = True
            player.last_seen = time.time()
        else:
            # Create new player
            player = Player(
                username=username,
                permission=Permission.PLAYER,
                last_seen=time.time(),
                is_online=True,
                world_data={},
                inventory=["sword", "pickaxe"],
                position=(0, 0),
                health=10,
                hunger=100,
                stamina=100
            )
            self.players[username] = player
        
        # Store client connection
        self.clients[client_id] = (client_socket, username)
        
        # Send login response
        response = {
            "type": "login_response",
            "success": True,
            "player_data": asdict(player),
            "world_data": self.worlds.get(world_name, {}).get("data", {}),
            "recent_chat": [asdict(msg) for msg in self.recent_chat[-20:]]  # Last 20 messages
        }
        
        self.send_to_client(client_id, response)
        
        # Notify other players
        self.broadcast_to_world(world_name, {
            "type": "player_joined",
            "username": username,
            "player_data": asdict(player)
        }, exclude_client=client_id)
        
        logger.info(f"👤 Player {username} logged in to world {world_name}")
    
    def handle_player_update(self, client_id: int, message: Dict):
        """Handle player position/state updates"""
        if client_id not in self.clients:
            return
            
        username = self.clients[client_id][1]
        if username not in self.players:
            return
            
        player = self.players[username]
        player_data = message.get("data", {})
        
        # Update player data
        if "position" in player_data:
            player.position = tuple(player_data["position"])
        if "health" in player_data:
            player.health = player_data["health"]
        if "hunger" in player_data:
            player.hunger = player_data["hunger"]
        if "stamina" in player_data:
            player.stamina = player_data["stamina"]
        if "inventory" in player_data:
            player.inventory = player_data["inventory"]
        
        player.last_seen = time.time()
        
        # Broadcast to other players in the same world
        world_name = message.get("world", "Default World")
        self.broadcast_to_world(world_name, {
            "type": "player_update",
            "username": username,
            "data": asdict(player)
        }, exclude_client=client_id)
    
    def handle_chat(self, client_id: int, message: Dict):
        """Handle chat messages"""
        if client_id not in self.clients:
            return
            
        username = self.clients[client_id][1]
        chat_text = message.get("message", "")
        world_name = message.get("world", "Default World")
        msg_type = message.get("message_type", "world")
        
        # Check permissions for global messages
        if msg_type == "global" and not self.has_permission(username, Permission.MODERATOR):
            msg_type = "world"  # Demote to world-only
        
        # Create chat message
        chat_msg = ChatMessage(
            id=0,  # Will be set by database
            username=username,
            message=chat_text,
            timestamp=time.time(),
            world=world_name,
            message_type=msg_type
        )
        
        # Save to database
        self.save_chat_message(chat_msg)
        
        # Broadcast message
        if msg_type == "global":
            self.broadcast_to_all({
                "type": "chat",
                "username": username,
                "message": chat_text,
                "timestamp": chat_msg.timestamp,
                "message_type": msg_type
            })
        else:
            self.broadcast_to_world(world_name, {
                "type": "chat",
                "username": username,
                "message": chat_text,
                "timestamp": chat_msg.timestamp,
                "message_type": msg_type
            })
        
        logger.info(f"💬 {username}: {chat_text} ({msg_type})")
        self.stats["messages_sent"] += 1
    
    def handle_block_change(self, client_id: int, message: Dict):
        """Handle block placement/removal"""
        if client_id not in self.clients:
            return
            
        username = self.clients[client_id][1]
        world_name = message.get("world", "Default World")
        
        # Check if player has permission to modify this world
        if not self.can_modify_world(username, world_name):
            logger.warning(f"Player {username} attempted unauthorized block change in {world_name}")
            return
        
        # Create block change record
        block_change = BlockChange(
            x=message.get("x", 0),
            y=message.get("y", 0),
            block_type=message.get("block_type", "air"),
            timestamp=time.time(),
            player=username,
            world=world_name
        )
        
        # Save to database
        self.save_block_change(block_change)
        
        # Broadcast to other players in the same world
        self.broadcast_to_world(world_name, {
            "type": "block_change",
            "x": block_change.x,
            "y": block_change.y,
            "block_type": block_change.block_type,
            "player": username
        }, exclude_client=client_id)
        
        self.stats["blocks_changed"] += 1
    
    def handle_world_request(self, client_id: int, message: Dict, client_socket: socket.socket):
        """Handle world data requests"""
        world_name = message.get("world", "Default World")
        world_data = self.worlds.get(world_name, {}).get("data", {})
        
        response = {
            "type": "world_data",
            "world": world_name,
            "data": world_data
        }
        
        self.send_to_client(client_id, response)
    
    def handle_world_save(self, client_id: int, message: Dict):
        """Handle world save requests"""
        if client_id not in self.clients:
            return
            
        username = self.clients[client_id][1]
        world_name = message.get("world", "Default World")
        world_data = message.get("data", {})
        
        # Check if player can save this world
        if not self.can_modify_world(username, world_name):
            logger.warning(f"Player {username} attempted unauthorized world save for {world_name}")
            return
        
        # Save world
        self.save_world(world_name, world_data, username)
        
        # Notify other players
        self.broadcast_to_world(world_name, {
            "type": "world_updated",
            "world": world_name,
            "last_modified": time.time()
        })
        
        logger.info(f"💾 World {world_name} saved by {username}")
    
    def handle_permission_request(self, client_id: int, message: Dict, client_socket: socket.socket):
        """Handle permission level requests"""
        if client_id not in self.clients:
            return
            
        username = self.clients[client_id][1]
        requested_permission = message.get("permission")
        
        # Check if player can grant this permission
        if not self.has_permission(username, Permission.ADMIN):
            response = {
                "type": "permission_response",
                "success": False,
                "message": "Insufficient permissions"
            }
            self.send_to_client(client_id, response)
            return
        
        # Grant permission (simplified - in real implementation, this would be more complex)
        target_username = message.get("target_username")
        if target_username in self.players:
            self.players[target_username].permission = Permission(requested_permission)
            self.save_player(self.players[target_username])
            
            response = {
                "type": "permission_response",
                "success": True,
                "message": f"Permission granted to {target_username}"
            }
        else:
            response = {
                "type": "permission_response",
                "success": False,
                "message": "Player not found"
            }
        
        self.send_to_client(client_id, response)
    
    def has_permission(self, username: str, required_permission: Permission) -> bool:
        """Check if player has required permission"""
        if username not in self.players:
            return False
        return self.players[username].permission.value >= required_permission.value
    
    def can_modify_world(self, username: str, world_name: str) -> bool:
        """Check if player can modify world"""
        if username not in self.players:
            return False
            
        player = self.players[username]
        
        # Owner can always modify
        if world_name in self.worlds and self.worlds[world_name]["owner"] == username:
            return True
        
        # Admins and moderators can modify
        if player.permission.value >= Permission.MODERATOR.value:
            return True
        
        # Regular players can modify default worlds
        if world_name in ["Default World", "World 1", "World 2"]:
            return True
        
        return False
    
    def broadcast_to_world(self, world_name: str, message: Dict, exclude_client: int = None):
        """Send message to all players in a specific world"""
        message_bytes = pickle.dumps(message)
        
        for client_id, (client_socket, username) in self.clients.items():
            if client_id == exclude_client:
                continue
                
            # Check if player is in the specified world
            if username in self.players:
                player = self.players[username]
                # For now, assume all players are in the same world
                # In a real implementation, you'd track which world each player is in
                
                try:
                    client_socket.send(message_bytes)
                except Exception as e:
                    logger.error(f"Failed to send to client {client_id}: {e}")
                    self.disconnect_client(client_id)
    
    def broadcast_to_all(self, message: Dict, exclude_client: int = None):
        """Send message to all connected clients"""
        message_bytes = pickle.dumps(message)
        
        for client_id, (client_socket, address) in self.clients.items():
            if client_id == exclude_client:
                continue
                
            try:
                client_socket.send(message_bytes)
            except Exception as e:
                logger.error(f"Failed to send to client {client_id}: {e}")
                self.disconnect_client(client_id)
    
    def send_to_client(self, client_id: int, message: Dict):
        """Send message to specific client"""
        if client_id not in self.clients:
            return
            
        client_socket, address = self.clients[client_id]
        try:
            message_bytes = pickle.dumps(message)
            client_socket.send(message_bytes)
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            self.disconnect_client(client_id)
    
    def disconnect_client(self, client_id: int):
        """Disconnect a client and clean up"""
        if client_id not in self.clients:
            return
            
        client_socket, username = self.clients[client_id]
        
        try:
            client_socket.close()
        except:
            pass
        
        # Mark player as offline
        if username in self.players:
            self.players[username].is_online = False
            self.players[username].last_seen = time.time()
            self.save_player(self.players[username])
        
        # Remove from client list
        del self.clients[client_id]
        
        # Notify other players
        self.broadcast_to_all({
            "type": "player_left",
            "username": username
        })
        
        logger.info(f"🔌 Client {client_id} ({username}) disconnected")
    
    def save_all_data(self):
        """Save all data to database"""
        try:
            for player in self.players.values():
                self.save_player(player)
            self.conn.commit()
            logger.info("💾 All data saved to database")
        except Exception as e:
            logger.error(f"Failed to save all data: {e}")
    
    def cleanup_offline_players(self):
        """Clean up old offline player data"""
        try:
            current_time = time.time()
            offline_threshold = 86400  # 24 hours
            
            for username, player in list(self.players.items()):
                if not player.is_online and (current_time - player.last_seen) > offline_threshold:
                    # Remove very old offline players
                    del self.players[username]
                    logger.info(f"🧹 Cleaned up old offline player: {username}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup offline players: {e}")
    
    def get_server_info(self) -> Dict:
        """Get server information"""
        return {
            "name": self.server_name,
            "version": self.version,
            "host": self.host,
            "port": self.port,
            "players": len([p for p in self.players.values() if p.is_online]),
            "max_players": self.max_players,
            "worlds": list(self.worlds.keys()),
            "uptime": time.time() - self.stats["start_time"],
            "total_connections": self.stats["total_connections"],
            "messages_sent": self.stats["messages_sent"],
            "blocks_changed": self.stats["blocks_changed"]
        }
    
    def stop(self):
        """Stop the server"""
        self.running = False
        
        # Save all data
        self.save_all_data()
        
        # Close all client connections
        for client_id in list(self.clients.keys()):
            self.disconnect_client(client_id)
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        # Close database connection
        if hasattr(self, 'conn'):
            self.conn.close()
        
        logger.info("🛑 Network server stopped")

if __name__ == "__main__":
    # Test the server
    server = NetworkServer(port=5555)
    if server.start_server("Test Network Server"):
        try:
            print("🌐 Network server running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            server.stop()
            print("✅ Server stopped")
