# 🎬 Custom Animation Tutorial - Create Your Own Character Animations!

## 🎯 **What You Need to Create**

Your game now has a **custom animation system** that loads your own animation files! Here's exactly what you need to create:

### **📁 File Structure**
```
assets/player/
├── idle_1.png      # Standing still, frame 1
├── idle_2.png      # Standing still, frame 2
├── idle_3.png      # Standing still, frame 3
├── idle_4.png      # Standing still, frame 4
├── idle_5.png      # Standing still, frame 5
├── idle_6.png      # Standing still, frame 6
├── walk_1.png      # Walking, frame 1
├── walk_2.png      # Walking, frame 2
├── walk_3.png      # Walking, frame 3
├── walk_4.png      # Walking, frame 4
├── jump_1.png      # Jumping, frame 1
├── jump_2.png      # Jumping, frame 2
├── jump_3.png      # Jumping, frame 3
├── jump_4.png      # Jumping, frame 4
├── fall_1.png      # Falling, frame 1
├── fall_2.png      # Falling, frame 2
├── fall_3.png      # Falling, frame 3
├── attack_1.png    # Attacking, frame 1
├── attack_2.png    # Attacking, frame 2
├── attack_3.png    # Attacking, frame 3
└── attack_4.png    # Attacking, frame 4
```

## 🎨 **How to Create Your Animation Files**

### **Method 1: Digital Art Software (Recommended)**
1. **Use software like:**
   - **GIMP** (Free) - https://www.gimp.org/
   - **Krita** (Free) - https://krita.org/
   - **Aseprite** (Paid, but excellent for pixel art) - https://www.aseprite.org/
   - **Piskel** (Free, web-based) - https://www.piskelapp.com/

2. **Create a 32x32 pixel canvas**
3. **Draw your character in different poses**
4. **Export each frame as PNG**

### **Method 2: Pixel Art Creation**
1. **Start with a 32x32 grid**
2. **Design your character:**
   - **Head**: 6x6 pixels (around position 16,12)
   - **Body**: 16x20 pixels (around position 8,4)
   - **Arms**: 4x8 pixels
   - **Legs**: 4x6 pixels

3. **Create variations for each animation**

### **Method 3: Convert Existing Art**
1. **Find character sprites online** (make sure they're free to use!)
2. **Resize to 32x32 pixels**
3. **Split into individual frames**
4. **Save as PNG files**

## 🎭 **Animation Types & What to Create**

### **1. Idle Animation (6 frames)**
- **Purpose**: Character standing still
- **Variations**: Breathing, slight movement, blinking
- **Example**: 
  - Frame 1: Normal stance
  - Frame 2: Slight up movement
  - Frame 3: Peak of movement
  - Frame 4: Slight down movement
  - Frame 5: Back to normal
  - Frame 6: Blink or small gesture

### **2. Walking Animation (4 frames)**
- **Purpose**: Character moving left/right
- **Variations**: Leg movement, arm swing, body bounce
- **Example**:
  - Frame 1: Left leg forward, right leg back
  - Frame 2: Both legs together
  - Frame 3: Right leg forward, left leg back
  - Frame 4: Both legs together

### **3. Jumping Animation (4 frames)**
- **Purpose**: Character jumping up
- **Variations**: Squat, launch, peak, landing prep
- **Example**:
  - Frame 1: Crouch down
  - Frame 2: Launch upward
  - Frame 3: Peak of jump
  - Frame 4: Start of fall

### **4. Falling Animation (3 frames)**
- **Purpose**: Character falling down
- **Variations**: Arms up, compressed body, landing
- **Example**:
  - Frame 1: Arms up, body stretched
  - Frame 2: Body compressed
  - Frame 3: Landing pose

### **5. Attack Animation (4 frames)**
- **Purpose**: Character attacking/mining
- **Variations**: Weapon swing, arm movement, body lean
- **Example**:
  - Frame 1: Wind up
  - Frame 2: Swing weapon
  - Frame 3: Follow through
  - Frame 4: Return to stance

## 🎨 **Art Style Guidelines**

### **Size Requirements**
- **Canvas**: Exactly 32x32 pixels
- **Character**: Should fill most of the canvas
- **Transparency**: Use transparent background (PNG)

### **Color Guidelines**
- **Limited palette**: 8-16 colors for pixel art look
- **Contrast**: Make sure character is visible
- **Consistency**: Keep colors consistent across frames

### **Animation Principles**
- **Smooth transitions**: Each frame should flow to the next
- **Exaggeration**: Make movements clear and visible
- **Timing**: Consider how fast each animation plays

## 🛠️ **Step-by-Step Creation Process**

### **Step 1: Plan Your Character**
1. **Decide on character design**
2. **Sketch basic poses**
3. **Plan frame transitions**

### **Step 2: Create Base Character**
1. **Draw your character in neutral pose**
2. **Establish color palette**
3. **Save as template**

### **Step 3: Create Animation Frames**
1. **Start with idle animation**
2. **Copy base character to new frames**
3. **Modify each frame slightly**
4. **Test animation flow**

### **Step 4: Export and Test**
1. **Save each frame as PNG**
2. **Use correct naming convention**
3. **Test in the game**
4. **Adjust timing if needed**

## 📱 **Using Piskel (Free Web Tool)**

### **Quick Start with Piskel**
1. **Go to**: https://www.piskelapp.com/
2. **Create new sprite**: 32x32 pixels
3. **Draw your character**
4. **Add frames**: Click the + button
5. **Modify each frame**
6. **Export**: File → Export → PNG Files

### **Piskel Features**
- **Onion skinning**: See previous frame while drawing
- **Animation preview**: Test your animation
- **Layer support**: Organize your artwork
- **Free to use**: No registration required

## 🎮 **Testing Your Animations**

### **In-Game Testing**
1. **Place your PNG files in `assets/player/` folder**
2. **Run the game**
3. **Watch console for loading messages**
4. **Move around to see animations**

### **Debug Information**
The game will show:
- ✅ **"Custom animations loaded successfully!"** - Your files worked!
- ⚠️ **"Could not load [file].png"** - File missing or corrupted
- 🎬 **"Setting up procedural fallback animations"** - Using backup system

### **Common Issues & Fixes**
- **File not found**: Check file path and naming
- **Wrong size**: Ensure 32x32 pixels
- **Corrupted file**: Re-export from your art software
- **Wrong format**: Use PNG, not JPG

## 🎨 **Advanced Animation Tips**

### **Smooth Movement**
- **Ease in/out**: Start slow, speed up, slow down
- **Anticipation**: Prepare for major movements
- **Follow through**: Don't stop abruptly

### **Character Personality**
- **Idle quirks**: Small movements while standing
- **Movement style**: How does your character move?
- **Weapon handling**: How do they hold tools?

### **Performance Optimization**
- **Keep file sizes small**: Under 5KB per frame
- **Use indexed colors**: Reduces file size
- **Optimize transparency**: Only where needed

## 🔧 **Troubleshooting**

### **Animation Not Working?**
1. **Check file names**: Must be exactly `idle_1.png`, `walk_1.png`, etc.
2. **Check file location**: Must be in `assets/player/` folder
3. **Check file format**: Must be PNG
4. **Check file size**: Must be 32x32 pixels

### **Animation Looks Wrong?**
1. **Frame order**: Make sure frames are numbered correctly
2. **Timing**: Adjust animation speed in the code
3. **Transparency**: Ensure background is transparent
4. **Consistency**: Keep character size consistent across frames

### **Game Crashes?**
1. **File corruption**: Re-export from your art software
2. **Wrong file type**: Use PNG, not other formats
3. **File size**: Keep files under 10KB each
4. **Special characters**: Avoid spaces or special characters in filenames

## 🎯 **Example Animation Sequence**

### **Walking Animation Example**
```
Frame 1: Character with left leg forward
Frame 2: Character with both legs together  
Frame 3: Character with right leg forward
Frame 4: Character with both legs together
```

### **Jumping Animation Example**
```
Frame 1: Character crouching down
Frame 2: Character launching upward
Frame 3: Character at peak of jump
Frame 4: Character starting to fall
```

## 🏆 **Your Mission**

1. **Create your character design**
2. **Draw 6 idle frames**
3. **Draw 4 walking frames**
4. **Draw 4 jumping frames**
5. **Draw 3 falling frames**
6. **Draw 4 attack frames**
7. **Save as PNG files with correct names**
8. **Place in `assets/player/` folder**
9. **Test in the game!**

## 🎬 **Animation Resources**

### **Free Tools**
- **Piskel**: https://www.piskelapp.com/
- **GIMP**: https://www.gimp.org/
- **Krita**: https://krita.org/

### **Learning Resources**
- **Pixel Art Tutorials**: YouTube search "pixel art animation"
- **Game Art Guides**: Many free resources online
- **Animation Principles**: Study basic animation concepts

---

## 🎮 **Ready to Animate?**

Your game is now set up to use **your custom animations**! The system will:

1. **Try to load your custom files first**
2. **Fall back to procedural animations if needed**
3. **Show helpful debug messages**
4. **Automatically scale and format your images**

**Start creating your character animations today! 🎨✨**

---

**Need help? Check the console messages when you run the game - they'll tell you exactly what's happening with your animation files! 🎬**

