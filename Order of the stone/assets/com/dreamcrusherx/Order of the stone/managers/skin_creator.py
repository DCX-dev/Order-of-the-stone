#!/usr/bin/env python3
"""
🎨 Skin Creator for Order of the Stone
A pixel art editor for creating custom character skins using Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
from PIL import Image, ImageTk, ImageDraw

# Constants
CANVAS_SIZE = 32  # 32x32 pixel skin
PIXEL_SIZE = 16   # Each pixel is 16x16 screen pixels
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
PINK = (255, 192, 203)
CYAN = (0, 255, 255)

# Color palette for skin creation
COLOR_PALETTE = [
    # Skin tones
    (255, 224, 189), (255, 205, 148), (234, 192, 134), (225, 184, 153),
    (255, 173, 96), (234, 137, 154), (255, 142, 69), (255, 106, 106),
    (255, 64, 64), (255, 0, 0), (139, 69, 19), (160, 82, 45),
    
    # Hair colors
    (139, 69, 19), (160, 82, 45), (210, 180, 140), (255, 248, 220),
    (255, 215, 0), (255, 165, 0), (255, 0, 0), (128, 0, 128),
    (0, 0, 255), (0, 255, 0), (255, 255, 255), (0, 0, 0),
    
    # Clothing colors
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 0, 128), (255, 165, 0),
    (255, 192, 203), (128, 128, 128), (255, 255, 255), (0, 0, 0),
    
    # Accent colors
    (255, 215, 0), (255, 140, 0), (255, 69, 0), (128, 0, 0),
    (0, 128, 0), (0, 0, 128), (75, 0, 130), (148, 0, 211)
]

class SkinCreator:
    def __init__(self):
        # Check if another instance is already running
        if hasattr(SkinCreator, '_instance') and SkinCreator._instance is not None:
            print("⚠️ Skin Creator is already running!")
            return
        
        # Set instance flag
        SkinCreator._instance = self
        
        self.root = tk.Tk()
        self.root.title("🎨 Skin Creator - Order of the Stone")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        
        # Canvas state
        self.canvas = [[WHITE for _ in range(CANVAS_SIZE)] for _ in range(CANVAS_SIZE)]
        self.selected_color = BLACK
        self.current_tool = "brush"
        self.drawing = False
        
        # Create UI
        self.create_widgets()
        
        # Load default skin template
        self.load_default_template()
        
        # Bind events
        self.bind_events()
        
    def create_widgets(self):
        """Create the main UI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎨 Skin Creator", font=("Arial", 24, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Tools frame
        tools_frame = ttk.LabelFrame(main_frame, text="Tools", padding=10)
        tools_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tool buttons
        tools = [
            ("🖌️ Brush", "brush"),
            ("🧽 Eraser", "eraser"),
            ("🪣 Fill", "fill"),
            ("🎯 Picker", "picker")
        ]
        
        for text, tool in tools:
            btn = ttk.Button(tools_frame, text=text, 
                           command=lambda t=tool: self.set_tool(t))
            btn.pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        actions_frame = ttk.Frame(tools_frame)
        actions_frame.pack(side=tk.RIGHT, padx=(20, 0))
        
        ttk.Button(actions_frame, text="💾 Save", command=self.save_skin).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="📂 Load", command=self.load_skin).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="🔄 Reset", command=self.load_default_template).pack(side=tk.LEFT, padx=5)
        
        # Main content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Canvas
        canvas_frame = ttk.LabelFrame(content_frame, text="Canvas (32x32 pixels)", padding=10)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Canvas
        self.canvas_widget = tk.Canvas(canvas_frame, 
                                      width=CANVAS_SIZE * PIXEL_SIZE,
                                      height=CANVAS_SIZE * PIXEL_SIZE,
                                      bg="white", relief=tk.RAISED, bd=2)
        self.canvas_widget.pack()
        
        # Right side - Color palette and info
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Color palette frame
        palette_frame = ttk.LabelFrame(right_frame, text="Color Palette (Click to Select)", padding=10)
        palette_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create color palette first (before search)
        self.create_color_palette(palette_frame)
        
        # Add color search/filter (after palette is created)
        search_frame = ttk.Frame(palette_frame)
        search_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(search_frame, text="🔍 Quick Find:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        # Don't trace until after palette is created
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(5, 5))
        search_entry.insert(0, "Type color name...")
        
        # Clear search button
        clear_btn = ttk.Button(search_frame, text="Clear", width=8,
                              command=self.clear_search)
        clear_btn.pack(side=tk.LEFT)
        
        # Bind focus events to clear placeholder text
        search_entry.bind("<FocusIn>", self.on_search_focus_in)
        search_entry.bind("<FocusOut>", self.on_search_focus_out)
        
        # Add search examples
        examples_frame = ttk.Frame(palette_frame)
        examples_frame.pack(fill=tk.X, pady=(5, 0))
        examples_label = ttk.Label(examples_frame, 
                                  text="Examples: 'red', 'skin', 'gold', 'blue'",
                                  font=("Arial", 8), foreground="gray")
        examples_label.pack(anchor=tk.W)
        
        # Now add the trace after palette is created
        self.search_var.trace("w", self.filter_colors)
        
        # Add color categories for better organization
        self.create_color_categories(palette_frame)
        
        # Selected color preview
        color_preview_frame = ttk.LabelFrame(right_frame, text="Selected Color", padding=10)
        color_preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.color_preview = tk.Canvas(color_preview_frame, width=60, height=60, bg="white", relief=tk.SUNKEN, bd=2)
        self.color_preview.pack()
        
        self.color_info = ttk.Label(color_preview_frame, text="RGB(0, 0, 0)")
        self.color_info.pack(pady=(5, 0))
        
        # Instructions frame
        instructions_frame = ttk.LabelFrame(right_frame, text="Instructions", padding=10)
        instructions_frame.pack(fill=tk.BOTH, expand=True)
        
        instructions = [
            "• Left click: Draw/Use tool",
            "• Right click: Pick color",
            "• Tools: Brush, Eraser, Fill, Picker",
            "• Save/Load your creations",
            "• Reset to start over"
        ]
        
        for instruction in instructions:
            ttk.Label(instructions_frame, text=instruction).pack(anchor=tk.W, pady=2)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def create_color_palette(self, parent):
        """Create the color palette grid"""
        # Create a frame for the palette grid
        self.palette_grid = ttk.Frame(parent)
        self.palette_grid.pack()
        
        # Store color buttons for filtering
        self.color_buttons = []
        
        # Create color buttons in a much larger grid
        for i, color in enumerate(COLOR_PALETTE):
            row = i // 8  # 8 colors per row instead of 12
            col = i % 8
            
            # Convert RGB to hex for tkinter
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            
            # Create much larger color buttons for better visibility
            color_btn = tk.Button(self.palette_grid, width=4, height=2, bg=hex_color,
                                command=lambda c=color: self.select_color(c))
            color_btn.grid(row=row, column=col, padx=2, pady=2)
            
            # Add better border and styling for visibility
            color_btn.configure(relief=tk.RAISED, bd=2, cursor="hand2")
            
            # Add hover effect
            color_btn.bind("<Enter>", lambda e, btn=color_btn: btn.configure(relief=tk.SUNKEN))
            color_btn.bind("<Leave>", lambda e, btn=color_btn: btn.configure(relief=tk.SUNKEN))
            
            # Store button reference for filtering
            self.color_buttons.append(color_btn)
    
    def create_color_categories(self, parent):
        """Create color category labels for better organization"""
        categories_frame = ttk.Frame(parent)
        categories_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Color categories with their ranges
        categories = [
            ("Skin Tones", 0, 11),
            ("Hair Colors", 12, 23),
            ("Clothing", 24, 35),
            ("Accents", 36, 47)
        ]
        
        for name, start, end in categories:
            # Create category label
            cat_label = ttk.Label(categories_frame, text=f"• {name}:", font=("Arial", 9, "bold"))
            cat_label.pack(anchor=tk.W, pady=(5, 2))
            
            # Show color range info
            range_label = ttk.Label(categories_frame, 
                                  text=f"  Colors {start+1}-{end+1} ({end-start+1} colors)",
                                  font=("Arial", 8))
            range_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Add helpful tip
        tip_label = ttk.Label(categories_frame, 
                             text="💡 Tip: Use the search box above to quickly find colors!",
                             font=("Arial", 8), foreground="blue")
        tip_label.pack(anchor=tk.W, pady=(10, 0))
    
    def filter_colors(self, *args):
        """Filter colors based on search text"""
        # Safety check - make sure color_buttons exists
        if not hasattr(self, 'color_buttons') or not self.color_buttons:
            return
            
        search_text = self.search_var.get().lower()
        
        # Color names for searching
        color_names = [
            "white", "black", "gray", "red", "green", "blue", "yellow", "purple", "orange", "brown", "pink", "cyan",
            "skin", "tone", "hair", "clothing", "accent", "gold", "silver", "copper", "bronze", "tan", "beige", "cream"
        ]
        
        for i, button in enumerate(self.color_buttons):
            color = COLOR_PALETTE[i]
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            
            # Check if color matches search
            matches = False
            if search_text in hex_color.lower():
                matches = True
            elif any(name in search_text for name in color_names if name in search_text):
                matches = True
            elif search_text == "" or search_text == "type color name...":
                matches = True
            
            # Show/hide button based on filter
            if matches:
                button.grid()
            else:
                button.grid_remove()
    
    def clear_search(self):
        """Clear the search and show all colors"""
        self.search_var.set("")
        self.filter_colors()
    
    def on_search_focus_in(self, event):
        """Clear placeholder text when search entry is focused"""
        if self.search_var.get() == "Type color name...":
            self.search_var.set("")
    
    def on_search_focus_out(self, event):
        """Restore placeholder text if search entry is empty"""
        if self.search_var.get() == "":
            self.search_var.set("Type color name...")
    
    def bind_events(self):
        """Bind mouse and keyboard events"""
        # Canvas events
        self.canvas_widget.bind("<Button-1>", self.on_canvas_click)
        self.canvas_widget.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas_widget.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas_widget.bind("<Button-3>", self.on_canvas_right_click)
        
        # Keyboard shortcuts
        self.root.bind("<Control-s>", lambda e: self.save_skin())
        self.root.bind("<Control-l>", lambda e: self.load_skin())
        self.root.bind("<Control-r>", lambda e: self.load_default_template())
        self.root.bind("<Escape>", lambda e: self.on_closing())
        
        # Window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def set_tool(self, tool):
        """Set the current drawing tool"""
        self.current_tool = tool
        self.status_var.set(f"Tool: {tool.title()}")
        
        # Update tool button states
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for grandchild in child.winfo_children():
                    if isinstance(grandchild, ttk.Frame):
                        for button in grandchild.winfo_children():
                            if isinstance(button, ttk.Button):
                                if button.cget("text").endswith(tool.title()):
                                    button.state(['pressed'])
                                else:
                                    button.state(['!pressed'])
    
    def select_color(self, color):
        """Select a color from the palette"""
        self.selected_color = color
        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        self.color_preview.configure(bg=hex_color)
        self.color_info.configure(text=f"RGB{color}")
        self.status_var.set(f"Color selected: RGB{color}")
        
        # Highlight the selected color in the palette
        self.highlight_selected_color(color)
    
    def highlight_selected_color(self, selected_color):
        """Highlight the currently selected color in the palette"""
        for i, button in enumerate(self.color_buttons):
            color = COLOR_PALETTE[i]
            if color == selected_color:
                # Highlight selected color with a thick border
                button.configure(bd=4, relief=tk.SUNKEN)
            else:
                # Reset other buttons to normal
                button.configure(bd=2, relief=tk.RAISED)
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        self.drawing = True
        self.draw_pixel(event.x, event.y)
    
    def on_canvas_drag(self, event):
        """Handle canvas drag (drawing)"""
        if self.drawing:
            self.draw_pixel(event.x, event.y)
    
    def on_canvas_release(self, event):
        """Handle canvas release"""
        self.drawing = False
    
    def on_canvas_right_click(self, event):
        """Handle right click (color picker)"""
        self.pick_color(event.x, event.y)
    
    def draw_pixel(self, x, y):
        """Draw a pixel at the given coordinates"""
        # Convert screen coordinates to canvas coordinates
        canvas_x = x // PIXEL_SIZE
        canvas_y = y // PIXEL_SIZE
        
        if 0 <= canvas_x < CANVAS_SIZE and 0 <= canvas_y < CANVAS_SIZE:
            if self.current_tool == "brush":
                self.canvas[canvas_y][canvas_x] = self.selected_color
            elif self.current_tool == "eraser":
                self.canvas[canvas_y][canvas_x] = WHITE
            elif self.current_tool == "fill":
                self.flood_fill(canvas_x, canvas_y, self.canvas[canvas_y][canvas_x], self.selected_color)
            
            # Redraw the canvas
            self.redraw_canvas()
    
    def pick_color(self, x, y):
        """Pick a color from the canvas"""
        canvas_x = x // PIXEL_SIZE
        canvas_y = y // PIXEL_SIZE
        
        if 0 <= canvas_x < CANVAS_SIZE and 0 <= canvas_y < CANVAS_SIZE:
            color = self.canvas[canvas_y][canvas_x]
            self.select_color(color)
            self.current_tool = "picker"
            self.status_var.set(f"Color picked: RGB{color}")
    
    def flood_fill(self, x, y, target_color, replacement_color):
        """Flood fill algorithm"""
        if target_color == replacement_color:
            return
        
        stack = [(x, y)]
        while stack:
            x, y = stack.pop()
            if not (0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE):
                continue
            if self.canvas[y][x] != target_color:
                continue
            
            self.canvas[y][x] = replacement_color
            
            # Add neighboring pixels to stack
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    
    def redraw_canvas(self):
        """Redraw the entire canvas"""
        self.canvas_widget.delete("all")
        
        # Draw pixels
        for y in range(CANVAS_SIZE):
            for x in range(CANVAS_SIZE):
                pixel_x = x * PIXEL_SIZE
                pixel_y = y * PIXEL_SIZE
                color = self.canvas[y][x]
                
                # Convert RGB to hex
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                
                # Draw pixel
                self.canvas_widget.create_rectangle(
                    pixel_x, pixel_y, 
                    pixel_x + PIXEL_SIZE, pixel_y + PIXEL_SIZE,
                    fill=hex_color, outline="gray", width=1
                )
    
    def load_default_template(self):
        """Load a basic humanoid skin template"""
        # Clear canvas
        self.canvas = [[WHITE for _ in range(CANVAS_SIZE)] for _ in range(CANVAS_SIZE)]
        
        # Draw basic humanoid outline
        # Head (8x8 pixels in center)
        head_start = CANVAS_SIZE // 2 - 4
        for y in range(head_start, head_start + 8):
            for x in range(head_start, head_start + 8):
                if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
                    self.canvas[y][x] = (255, 224, 189)  # Skin tone
        
        # Body (8x12 pixels below head)
        body_start_y = head_start + 8
        for y in range(body_start_y, body_start_y + 12):
            for x in range(head_start, head_start + 8):
                if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
                    self.canvas[y][x] = (255, 224, 189)  # Skin tone
        
        # Arms (4x8 pixels on sides)
        left_arm_x = head_start - 4
        right_arm_x = head_start + 8
        arm_y = body_start_y
        for y in range(arm_y, arm_y + 8):
            for x in range(left_arm_x, left_arm_x + 4):
                if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
                    self.canvas[y][x] = (255, 224, 189)  # Skin tone
            for x in range(right_arm_x, right_arm_x + 4):
                if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
                    self.canvas[y][x] = (255, 224, 189)  # Skin tone
        
        # Legs (4x8 pixels below body)
        leg_y = body_start_y + 12
        for y in range(leg_y, leg_y + 8):
            for x in range(head_start, head_start + 4):
                if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
                    self.canvas[y][x] = (255, 224, 189)  # Skin tone
            for x in range(head_start + 4, head_start + 8):
                if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
                    self.canvas[y][x] = (255, 224, 189)  # Skin tone
        
        # Redraw canvas
        self.redraw_canvas()
        self.status_var.set("Default template loaded")
    
    def save_skin(self):
        """Save the skin to a file"""
        try:
            # Create save_data directory if it doesn't exist
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../save_data", "skins")
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # Convert canvas to PIL Image
            img = Image.new('RGB', (CANVAS_SIZE, CANVAS_SIZE))
            pixels = img.load()
            
            for y in range(CANVAS_SIZE):
                for x in range(CANVAS_SIZE):
                    pixels[x, y] = self.canvas[y][x]
            
            # Save as PNG
            skin_path = os.path.join(save_dir, "custom_skin.png")
            img.save(skin_path)
            
            # Also save as JSON for easy loading
            json_path = os.path.join(save_dir, "custom_skin.json")
            skin_data = {
                "name": "Custom Skin",
                "pixels": self.canvas,
                "created": "now"
            }
            
            with open(json_path, 'w') as f:
                json.dump(skin_data, f, indent=2)
            
            self.status_var.set(f"Skin saved successfully!")
            messagebox.showinfo("Success", f"Skin saved to:\n{skin_path}")
            
        except Exception as e:
            self.status_var.set(f"Failed to save skin: {e}")
            messagebox.showerror("Error", f"Failed to save skin:\n{e}")
    
    def load_skin(self):
        """Load a skin from a file"""
        try:
            # Try to load from JSON first
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../save_data", "skins", "custom_skin.json")
            
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    skin_data = json.load(f)
                
                if "pixels" in skin_data:
                    self.canvas = skin_data["pixels"]
                    self.redraw_canvas()
                    self.status_var.set("Skin loaded successfully!")
                    messagebox.showinfo("Success", "Skin loaded successfully!")
                    return
            
            # Fallback: try to load from PNG
            png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../save_data", "skins", "custom_skin.png")
            
            if os.path.exists(png_path):
                img = Image.open(png_path)
                img = img.resize((CANVAS_SIZE, CANVAS_SIZE))
                pixels = img.load()
                
                for y in range(CANVAS_SIZE):
                    for x in range(CANVAS_SIZE):
                        if x < img.width and y < img.height:
                            self.canvas[y][x] = pixels[x, y]
                
                self.redraw_canvas()
                self.status_var.set("Skin loaded successfully!")
                messagebox.showinfo("Success", "Skin loaded successfully!")
                return
            
            messagebox.showinfo("Info", "No saved skin found!")
            
        except Exception as e:
            self.status_var.set(f"Failed to load skin: {e}")
            messagebox.showerror("Error", f"Failed to load skin:\n{e}")
    
    def on_closing(self):
        """Handle window closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit? Any unsaved changes will be lost."):
            # Clear instance flag
            SkinCreator._instance = None
            self.root.destroy()
            self.root.quit()
    
    def run(self):
        """Start the skin creator"""
        self.redraw_canvas()  # Initial draw
        self.root.mainloop()

def main():
    """Main function"""
    print("🎨 Starting Skin Creator...")
    try:
        creator = SkinCreator()
        # Check if creator was actually created (not blocked by instance check)
        if hasattr(creator, 'root'):
            creator.run()
        else:
            print("⚠️ Skin Creator instance blocked - another one is already running")
    except Exception as e:
        print(f"❌ Error in Skin Creator: {e}")
    finally:
        print("🎨 Skin Creator closed")

if __name__ == "__main__":
    main()
