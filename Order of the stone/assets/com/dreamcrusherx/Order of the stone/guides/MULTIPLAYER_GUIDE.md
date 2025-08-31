# 🌐 Multiplayer Guide

Your Order of the Stone game now has **fully functional multiplayer**! Here's how to use it:

## 🚀 Getting Started

### 1. **Start the Game**
- Run `python3 order_of_the_stone.py`
- The game will load with all your animations and textures

### 2. **Access Multiplayer Menu**
- From the main title screen, click **"Multiplayer"**
- You'll see three options:
  - 🏠 **Host a Server** - Start your own multiplayer world
  - 🔗 **Join a Server** - Connect to someone else's server
  - ⬅️ **Back to Title** - Return to main menu

### 3. **Enhanced Features**
- **Custom Server Names** - Create servers with unique names
- **Custom Ports** - Choose any port (default: 5555)
- **Global Discovery** - Find servers from around the world
- **One-Click Join** - Join servers with dedicated buttons
- **C Key Chat** - Press C to open chat (instead of T)

## 🏠 Hosting a Server

### **Step 1: Choose Host Option**
- Click **"Host a Server"** from the multiplayer menu
- **Type your custom server name** (e.g., "Epic Adventure Server")
- **Choose a custom port** (default: 5555)
- Select which world you want to host (World 1, World 2, etc.)
- Click **"Start Hosting"**

**💡 Tips:**
- Server names can be up to 30 characters
- Ports can be any number from 1-65535
- Use Tab to switch between input fields
- Press Backspace to edit your input

### **Step 2: Server is Running**
- Your server will start on port **5555**
- Other players can join using your IP address
- You'll see a message: "🌐 Server started! Players can now join!"

### **Step 3: Play Together**
- Other players can join your world
- You can chat with them using the **T** key
- Build, explore, and fight together!

## 🔗 Joining a Server

### **Step 1: Choose Join Option**
- Click **"Join a Server"** from the multiplayer menu
- Click **"Search for Servers"**

### **Step 2: Select a Server**
- You'll see a list of available servers from around the world
- Each server shows:
  - Server name
  - World name
  - Player count (current/max)
  - Description
  - **Join button**
- Click the **"Join"** button on any server to connect

**🌐 Discovery Sources:**
- **Global Service** - Central server registry (when available)
- **Local Network** - Servers on your WiFi network
- **Demo Servers** - Always available for testing

### **Step 3: Connected!**
- You'll join the selected world
- You can see other players
- Use **T** key to chat with everyone

## 💬 Chat System

### **Opening Chat**
- Press **C** key to open chat input
- Type your message
- Press **Enter** to send
- Press **Escape** to cancel

### **Chat Features**
- Messages show username and timestamp
- Your messages appear in green
- Other players' messages in white
- Chat history is preserved during the session

## 🌐 Network Information

### **Ports Used**
- **Server Port**: 5555 (default)
- **Discovery Port**: 5556 (for finding servers)

### **Connection Types**
- **Local Network**: Players on same WiFi can join directly
- **Internet**: Requires port forwarding on your router
- **Localhost**: For testing (127.0.0.1)

## 🔧 Troubleshooting

### **Can't Start Server?**
- Check if port 5555 is available
- Make sure no other game is using the port
- Try restarting the game

### **Can't Join Server?**
- Verify the server IP address
- Check if the server is running
- Ensure firewall allows the connection
- Try the server discovery feature

### **Chat Not Working?**
- Make sure you're connected to a server
- Check if the T key is working
- Verify the server is still running

## 🎯 Multiplayer Features

### **What Works**
✅ **Player Movement** - See other players move in real-time
✅ **World Synchronization** - Shared world state
✅ **Chat System** - Real-time communication with C key
✅ **Server Discovery** - Find servers worldwide automatically
✅ **Custom Server Names** - Create servers with your own names
✅ **Custom Ports** - Choose any port for your server
✅ **Multiple Players** - Up to 20 players per server
✅ **Global Network** - Discover servers from around the world

### **Coming Soon**
🔄 **Block Breaking/Placing** - Shared world building
🔄 **Item Sharing** - Trade items with other players
🔄 **Combat** - Fight monsters together
🔄 **Achievements** - Shared goals and rewards

## 🚀 Advanced Setup

### **Hosting for Internet Players**
1. **Port Forwarding**: Forward port 5555 on your router
2. **Public IP**: Share your public IP address
3. **Firewall**: Allow the game through your firewall

### **Custom Server Settings**
- Edit `multiplayer_server.py` to change:
  - Maximum players (default: 20)
  - Server port (default: 5555)
  - World selection options

## 🎮 Have Fun!

Your multiplayer system is now fully functional! You can:
- Host epic adventures for your friends
- Join other players' worlds
- Build amazing creations together
- Chat and coordinate strategies
- Experience the game in a whole new way

**Happy Multiplaying!** 🎉
