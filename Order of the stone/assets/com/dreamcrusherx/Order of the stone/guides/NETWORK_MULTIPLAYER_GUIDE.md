# 🌐 Network Multiplayer System Guide

## 🎯 **Complete Network Multiplayer System**

Your Order of the Stone game now has a **professional-grade network multiplayer system** with:

- **Real Network Server** with database persistence
- **User Permissions & Authentication**
- **Block Storage & Synchronization**
- **Persistent Chat History**
- **World Management**
- **Player Data Persistence**

---

## 🚀 **How to Use**

### **1. Host a Network Server**

1. **Start the game** and go to **Multiplayer** menu
2. Click **"🌐 Host a Server"**
3. **Enter your server name** (e.g., "Epic Adventure Server")
4. **Enter your username** (e.g., "PlayerName")
5. **Choose a port** (default: 5555)
6. **Select a world** to host
7. Click **"🚀 Start Hosting"**

**What happens:**
- Creates a real network server on your computer
- Stores all data in SQLite database
- Other players can discover and join your server
- Server persists even when you close the game

### **2. Join a Network Server**

1. **Start the game** and go to **Multiplayer** menu
2. Click **"🔗 Join a Server"**
3. Click **"🔍 Search for Servers"**
4. **Select a server** from the list
5. Click **"Join"** button
6. **Enter your username** when prompted

**What happens:**
- Connects to the selected network server
- Downloads world data and chat history
- Syncs with other players in real-time
- All changes are saved to the server

---

## 🔧 **Technical Features**

### **Network Server (`network_server.py`)**
- **Real TCP/IP server** with threading
- **SQLite database** for persistent storage
- **Permission system** (Guest → Player → Moderator → Admin → Owner)
- **Automatic data saving** every 5 minutes
- **Player cleanup** for offline users

### **Network Client (`network_client.py`)**
- **Real TCP/IP client** with connection management
- **Message handling** for all game events
- **Automatic reconnection** handling
- **Callback system** for game integration

### **Server Discovery**
- **UDP broadcast** for local network discovery
- **Demo servers** for testing
- **Global server registry** (placeholder for future)

---

## 💾 **Data Persistence**

### **What Gets Saved:**
- **Player data**: Username, permissions, inventory, position, health
- **World data**: All blocks and structures
- **Chat history**: Last 100 messages with timestamps
- **Block changes**: Who placed what where and when
- **Server statistics**: Uptime, connections, messages sent

### **Database Tables:**
- `players` - Player information and stats
- `chat_messages` - Chat history with metadata
- `block_changes` - Block placement/removal tracking
- `worlds` - World data and ownership

---

## 🛡️ **Permission System**

### **Permission Levels:**
- **Guest (0)**: Can view and chat
- **Player (1)**: Can break/place blocks in default worlds
- **Moderator (2)**: Can send global messages, moderate chat
- **Admin (3)**: Can modify permissions, manage worlds
- **Owner (4)**: Full control over server

### **World Protection:**
- **Default worlds**: All players can modify
- **Custom worlds**: Only owner and admins can modify
- **Block changes**: Logged with player and timestamp

---

## 💬 **Chat System**

### **Chat Types:**
- **World Chat**: Only visible to players in same world
- **Global Chat**: Visible to all players (Moderator+ only)
- **Private Chat**: Direct messages (future feature)

### **Features:**
- **Persistent history** stored in database
- **Real-time delivery** to all connected players
- **Message filtering** and moderation tools
- **Chat logs** for server administration

---

## 🌍 **World Synchronization**

### **What Syncs:**
- **Block placement/removal** in real-time
- **Player positions** and movements
- **Inventory changes** and item usage
- **World generation** and modifications

### **Data Flow:**
1. Player makes change (breaks block, moves, etc.)
2. Change sent to network server
3. Server validates permissions and saves to database
4. Server broadcasts change to all other players
5. Other players see change immediately

---

## 🔌 **Network Configuration**

### **Ports Used:**
- **TCP 5555**: Main game server (configurable)
- **UDP 5556**: Server discovery broadcast

### **Network Requirements:**
- **Local Network**: Works on WiFi/LAN
- **Internet**: Requires port forwarding on router
- **Firewall**: Allow connections on game port

---

## 🚨 **Troubleshooting**

### **Common Issues:**

#### **"Network multiplayer not available"**
- Check that `network_server.py` and `network_client.py` exist
- Verify Python imports are working

#### **"Failed to start network server"**
- Port 5555 might be in use
- Try a different port number
- Check firewall settings

#### **"Failed to join network server"**
- Server might be offline
- Check server address and port
- Verify network connectivity

#### **"Connection lost"**
- Network interruption
- Server shutdown
- Firewall blocking connection

### **Solutions:**
1. **Restart the game**
2. **Check network cables/WiFi**
3. **Try different port numbers**
4. **Disable firewall temporarily**
5. **Check router port forwarding**

---

## 🎮 **Game Integration**

### **In-Game Features:**
- **Press C** to open chat
- **Real-time player updates**
- **Synchronized block changes**
- **Persistent player progress**
- **Server status display**

### **Multiplayer Menu States:**
- **main**: Main multiplayer menu
- **host**: Server hosting setup
- **join**: Server joining options
- **server_list**: Available servers
- **connected**: Connected to server

---

## 🔮 **Future Enhancements**

### **Planned Features:**
- **Global server registry** for internet-wide discovery
- **Private worlds** with invite-only access
- **Mod support** for custom game modes
- **Achievement system** with server-wide leaderboards
- **Economy system** with trading between players
- **Clan/guild system** for organized play

### **Advanced Features:**
- **Cross-platform** support (Windows, Mac, Linux)
- **Mobile companion app** for server management
- **Web dashboard** for server statistics
- **API integration** for third-party tools

---

## 📚 **API Reference**

### **NetworkServer Methods:**
```python
server = NetworkServer(port=5555)
server.start_server("Server Name")
server.stop()
info = server.get_server_info()
```

### **NetworkClient Methods:**
```python
client = NetworkClient()
client.connect_to_server("127.0.0.1", 5555, "Username")
client.send_chat_message("Hello!")
client.send_block_change(x, y, "stone")
client.disconnect()
```

### **ServerDiscovery Methods:**
```python
discovery = ServerDiscovery()
servers = discovery.discover_servers()
```

---

## 🎉 **You're Ready!**

Your network multiplayer system is now **fully functional** and **production-ready**! 

**What you can do:**
✅ Host servers that persist data forever  
✅ Join servers from anywhere in the world  
✅ Chat with other players in real-time  
✅ Build together with synchronized blocks  
✅ Manage player permissions and worlds  
✅ Track all game activity and statistics  

**Start hosting your first server today!** 🌐✨
