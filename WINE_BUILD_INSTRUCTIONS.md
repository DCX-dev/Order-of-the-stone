# 🍷 Building Windows Executable with Wine

## When Your Mom Gets Back - Install Wine

### Step 1: Install Homebrew (if not already installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Wine
```bash
brew install --cask wine-stable
```

### Step 3: Download Windows Python
```bash
# Download Python for Windows
curl -o python-installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe

# Install Python in Wine
wine python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
```

### Step 4: Install PyInstaller in Wine
```bash
wine python -m pip install pyinstaller pygame pillow
```

### Step 5: Build Windows Executable
```bash
# Create a simple Wine build script
wine python build_simple.py windows
```

---

## ⚠️ Warning

Wine is **complex** and **unreliable** for building Windows executables. It often:
- Fails with weird errors
- Creates broken executables
- Takes hours to debug

**GitHub Actions is still the better option** (it's free, no installation, works perfectly).

---

## 🎯 Alternative: Just Release Mac Version First

You can:
1. Release the Mac executable NOW (you already have it!)
2. Tell Windows users "Windows version coming soon!"
3. Build Windows version later when you have access

This is what many indie developers do! 🎮

---

## For Now - You Have:

✅ **releases/mac/Order_of_the_Stone** - Works perfectly on Mac
- Has all music, animations, everything
- Ready to share with Mac users

When you can use Wine or GitHub Actions, you'll get the Windows version! 🚀

