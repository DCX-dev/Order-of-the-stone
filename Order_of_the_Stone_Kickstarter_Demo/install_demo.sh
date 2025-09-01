#!/bin/bash

# Order of the Stone - Demo Installation Script
# =============================================

echo "🎮 Order of the Stone - Demo Installation"
echo "=========================================="
echo ""

# Check if executable exists
if [ ! -f "Order_of_the_Stone_Demo" ]; then
    echo "❌ Error: Order_of_the_Stone_Demo not found!"
    echo "Please ensure you're running this script from the correct directory."
    exit 1
fi

# Make executable
chmod +x Order_of_the_Stone_Demo

echo "✅ Making executable..."
echo ""

# Create desktop shortcut (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Creating macOS application bundle..."
    
    # Create app bundle structure
    mkdir -p "Order of the Stone Demo.app/Contents/MacOS"
    mkdir -p "Order of the Stone Demo.app/Contents/Resources"
    
    # Copy executable
    cp Order_of_the_Stone_Demo "Order of the Stone Demo.app/Contents/MacOS/"
    
    # Create Info.plist
    cat > "Order of the Stone Demo.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Order_of_the_Stone_Demo</string>
    <key>CFBundleIdentifier</key>
    <string>com.dreamcrusherx.order-of-the-stone-demo</string>
    <key>CFBundleName</key>
    <string>Order of the Stone Demo</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
    
    echo "✅ macOS app bundle created: Order of the Stone Demo.app"
    echo "   You can now drag this to your Applications folder!"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Creating Linux desktop entry..."
    
    # Create desktop entry
    cat > "order-of-the-stone-demo.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Order of the Stone Demo
Comment=2D Sandbox Survival Game Demo
Exec=$(pwd)/Order_of_the_Stone_Demo
Icon=applications-games
Terminal=false
Categories=Game;
EOF
    
    chmod +x order-of-the-stone-demo.desktop
    echo "✅ Linux desktop entry created: order-of-the-stone-demo.desktop"
    echo "   You can copy this to ~/.local/share/applications/ to add to your applications menu"
    
else
    echo "🪟 Windows detected - no additional setup needed"
    echo "   Just double-click Order_of_the_Stone_Demo.exe to run!"
fi

echo ""
echo "🎮 Installation Complete!"
echo "========================"
echo ""
echo "To play the game:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  • Double-click 'Order of the Stone Demo.app'"
    echo "  • Or run: ./Order_of_the_Stone_Demo"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "  • Run: ./Order_of_the_Stone_Demo"
    echo "  • Or use the desktop entry if installed"
else
    echo "  • Double-click Order_of_the_Stone_Demo.exe"
fi
echo ""
echo "📖 Read KICKSTARTER_DEMO_README.md for detailed instructions"
echo ""
echo "🚀 Enjoy your adventure in Order of the Stone!"
echo "   Support our Kickstarter to help fund the full game!"
