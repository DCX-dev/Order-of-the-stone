# Order of the Stone - Build Instructions

## 🎮 How to Build Executables

### Option 1: GitHub Actions (Recommended - True Windows Executable)

**This creates a REAL Windows 10/11 compatible `.exe` file!**

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Update game"
   git push
   ```

2. **GitHub Actions will automatically build**:
   - ✅ **Windows executable** (built on Windows server - works on Windows 10/11)
   - ✅ **Mac executable** (built on Mac server - works on macOS)

3. **Download the executables**:
   - Go to your GitHub repository
   - Click "Actions" tab
   - Click on the latest workflow run
   - Scroll down to "Artifacts"
   - Download:
     - `Order_of_the_Stone-Windows` (for Windows 10/11)
     - `Order_of_the_Stone-Mac` (for macOS)

### Option 2: Build Locally on Mac (Mac executable only)

This only creates Mac executables, NOT real Windows executables:

```bash
# Build both (but Windows version won't work on real Windows)
python3 build_simple.py

# Build Mac only
python3 build_simple.py mac
```

**⚠️ Important**: The "Windows" executable built on Mac is actually a Mac executable with a `.exe` extension. It **WILL NOT** work on real Windows 10/11 computers!

### Option 3: Build on Windows Computer

If you have access to a Windows PC:

1. Copy your project to Windows
2. Install Python 3.12
3. Install dependencies: `pip install -r requirements.txt`
4. Install PyInstaller: `pip install pyinstaller`
5. Run: `python build_simple.py windows`

## 📁 Output Locations

After building, executables will be in:
- **Mac**: `releases/mac/Order_of_the_Stone`
- **Windows**: `releases/windows/Order_of_the_Stone.exe`

## 🎯 For YouTubers and Players

### Windows Users (Windows 10/11)
- Download the executable from GitHub Actions artifacts
- Extract `Order_of_the_Stone.exe`
- Double-click to run!

### Mac Users
- Download the Mac executable from GitHub Actions artifacts
- Extract `Order_of_the_Stone`
- Right-click → Open (first time only, to bypass Gatekeeper)
- Or run: `chmod +x Order_of_the_Stone && ./Order_of_the_Stone`

## ✨ Features Included in Executables

- ✅ All game assets (textures, sprites, tiles)
- ✅ Player animations (walking, standing, falling)
- ✅ Background music
- ✅ Damage sounds
- ✅ Village generation without floating trees
- ✅ World creation and loading
- ✅ All UI systems

## 🔧 Troubleshooting

**If Windows executable doesn't work**:
1. Make sure it was built using GitHub Actions (not on Mac)
2. Windows might need Visual C++ Redistributable installed
3. Check Windows Defender didn't block it

**If Mac executable doesn't work**:
1. Right-click → Open (don't double-click)
2. System Preferences → Security → Allow app to run
3. Or run from terminal: `./Order_of_the_Stone`

## 📝 Notes

- The `.exe` extension doesn't make it a Windows executable - it must be built on Windows
- GitHub Actions is FREE and builds real platform-specific executables
- Executables are stored as artifacts for 90 days

