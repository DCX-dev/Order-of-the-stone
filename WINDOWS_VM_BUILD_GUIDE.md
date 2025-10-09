# 🖥️ Building Windows Executable in Virtual Machine

## Quick Setup for Windows VM

### Step 1: Copy Your Project to Windows VM
1. Start your Windows VM (Parallels, VMware, VirtualBox, etc.)
2. Copy the entire `Order-of-the-stone` folder to Windows
   - Use shared folders, or
   - Zip it and transfer via cloud/USB

### Step 2: Install Python on Windows VM
1. Download Python 3.12 for Windows:
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.12"
   
2. Run the installer:
   - ✅ **IMPORTANT**: Check "Add Python to PATH"
   - Click "Install Now"

### Step 3: Install Dependencies
Open Command Prompt (cmd) or PowerShell in Windows VM:

```cmd
cd path\to\Order-of-the-stone
pip install -r requirements.txt
pip install pyinstaller
```

### Step 4: Build Windows Executable
```cmd
python build_simple.py windows
```

### Step 5: Get Your Executable
The Windows .exe will be at:
```
releases\windows\Order_of_the_Stone.exe
```

Copy this file back to your Mac and share it with Windows users!

---

## ⚡ Quick Build Script for Windows VM

Create a file called `build_windows.bat`:

```batch
@echo off
echo Building Order of the Stone for Windows...
pip install pyinstaller pygame pillow
python build_simple.py windows
echo.
echo Done! Executable is in releases\windows\
pause
```

Then just double-click `build_windows.bat` in Windows!

---

## ✅ Verification

After building, check it's a real Windows executable:
```cmd
file releases\windows\Order_of_the_Stone.exe
```

Should say: **"PE32+ executable"** ✅

---

## 📦 File Transfer Tips

**From Windows VM to Mac:**
- Shared folder (easiest)
- Google Drive/Dropbox
- USB drive
- Email to yourself

Then you can upload the .exe to share with Windows users!

---

## 🎮 This Will Give You:

A TRUE Windows 10/11 executable that:
- ✅ Runs on any Windows PC
- ✅ Has all music and animations
- ✅ Works with all features
- ✅ Can be shared with YouTubers

Good luck! This will work perfectly! 🚀

