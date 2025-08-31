#!/usr/bin/env python3
"""
Block Breaker - A focused solution for ensuring blocks turn into air when broken
This script demonstrates the proper way to handle block breaking in the game.
"""

import pygame
import sys
import os

# Add the game directory to the path so we can import game modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'Order of the stone'))

# Initialize Pygame
pygame.init()

# Constants
TILE_SIZE = 32
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
BLUE = (0, 0, 255)

class BlockBreaker:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Block Breaker - Test Block Breaking")
        self.clock = pygame.time.Clock()
        
        # Simple world data structure (x,y coordinates as keys)
        self.world_data = {}
        self.player_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
        self.camera_x = 0
        self.camera_y = 0
        
        # Track which columns have been generated (to prevent regeneration)
        self.generated_columns = set()
        
        # Generate some test blocks
        self.generate_test_world()
        
    def generate_test_world(self):
        """Generate a simple test world with some blocks"""
        # Create a simple ground layer
        for x in range(-10, 30):
            for y in range(15, 20):
                # Grass surface
                if y == 15:
                    self.world_data[f"{x},{y}"] = "grass"
                # Dirt below
                elif y < 20:
                    self.world_data[f"{x},{y}"] = "dirt"
                # Stone deeper
                elif y < 25:
                    self.world_data[f"{x},{y}"] = "stone"
                    
            # Add some trees
            if x % 5 == 0 and x > 0:
                self.world_data[f"{x},{14}"] = "log"
                self.world_data[f"{x},{13}"] = "log"
                self.world_data[f"{x},{12}"] = "leaves"
                self.world_data[f"{x-1},{12}"] = "leaves"
                self.world_data[f"{x+1},{12}"] = "leaves"
                
            # Add some ores
            if x % 7 == 0 and x > 0:
                self.world_data[f"{x},{18}"] = "coal"
            if x % 11 == 0 and x > 0:
                self.world_data[f"{x},{19}"] = "iron"
                
        # Mark these columns as generated
        for x in range(-10, 30):
            self.generated_columns.add(x)
    
    def get_block(self, x, y):
        """Get block at coordinates - returns None for air"""
        return self.world_data.get(f"{x},{y}")
    
    def set_block(self, x, y, block_type):
        """Set block at coordinates"""
        if block_type == "air":
            # Remove the block completely (turn into air)
            self.world_data.pop(f"{x},{y}", None)
        else:
            self.world_data[f"{x},{y}"] = block_type
    
    def break_block(self, mouse_x, mouse_y):
        """Break a block at mouse position - turns it into air"""
        # Convert screen coordinates to world coordinates
        world_x = (mouse_x + self.camera_x) // TILE_SIZE
        world_y = (mouse_y + self.camera_y) // TILE_SIZE
        
        # Get the block at this position
        block = self.get_block(world_x, world_y)
        
        if block and block != "air":
            print(f"🔨 Breaking block: {block} at ({world_x}, {world_y})")
            
            # Remove the block completely - this turns it into air
            self.set_block(world_x, world_y, "air")
            
            print(f"✅ Block broken! Position ({world_x}, {world_y}) is now air")
            print(f"📊 World data keys: {len(self.world_data)} blocks remaining")
            
            return True
        else:
            print(f"💨 No block to break at ({world_x}, {world_y}) - already air")
            return False
    
    def place_block(self, mouse_x, mouse_y, block_type="stone"):
        """Place a block at mouse position - only on air"""
        # Convert screen coordinates to world coordinates
        world_x = (mouse_x + self.camera_x) // TILE_SIZE
        world_y = (mouse_y + self.camera_y) // TILE_SIZE
        
        # Check if the position is air (no block)
        current_block = self.get_block(world_x, world_y)
        
        if current_block is None:  # Air
            print(f"🏗️ Placing {block_type} at ({world_x}, {world_y})")
            self.set_block(world_x, world_y, block_type)
            return True
        else:
            print(f"❌ Can't place block at ({world_x}, {world_y}) - occupied by {current_block}")
            return False
    
    def draw_world(self):
        """Draw the world blocks"""
        self.screen.fill(BLUE)  # Sky background
        
        # Draw all blocks
        for key, block_type in self.world_data.items():
            try:
                x, y = map(int, key.split(','))
                screen_x = x * TILE_SIZE - self.camera_x
                screen_y = y * TILE_SIZE - self.camera_y
                
                # Only draw if on screen
                if -TILE_SIZE < screen_x < SCREEN_WIDTH and -TILE_SIZE < screen_y < SCREEN_HEIGHT:
                    # Draw block based on type
                    color = self.get_block_color(block_type)
                    rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, BLACK, rect, 1)  # Border
                    
                    # Draw block type text
                    font = pygame.font.Font(None, 16)
                    text = font.render(block_type, True, BLACK)
                    text_rect = text.get_rect(center=(screen_x + TILE_SIZE//2, screen_y + TILE_SIZE//2))
                    self.screen.blit(text, text_rect)
                    
            except (ValueError, AttributeError):
                continue
        
        # Draw player
        player_rect = pygame.Rect(self.player_pos[0] - 16, self.player_pos[1] - 16, 32, 32)
        pygame.draw.rect(self.screen, GREEN, player_rect)
        pygame.draw.rect(self.screen, BLACK, player_rect, 2)
        
        # Draw instructions
        font = pygame.font.Font(None, 24)
        instructions = [
            "Left Click: Break blocks (turn into air)",
            "Right Click: Place stone blocks",
            "Arrow Keys: Move camera",
            "R: Reset world",
            "ESC: Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, WHITE)
            self.screen.blit(text, (10, 10 + i * 25))
        
        # Draw block count
        block_count_text = font.render(f"Blocks in world: {len(self.world_data)}", True, WHITE)
        self.screen.blit(block_count_text, (10, SCREEN_HEIGHT - 30))
    
    def get_block_color(self, block_type):
        """Get color for different block types"""
        colors = {
            "grass": (34, 139, 34),    # Forest green
            "dirt": (139, 69, 19),     # Saddle brown
            "stone": (128, 128, 128),  # Gray
            "log": (101, 67, 33),      # Dark brown
            "leaves": (0, 100, 0),     # Dark green
            "coal": (47, 79, 79),      # Dark slate gray
            "iron": (192, 192, 192),   # Silver
        }
        return colors.get(block_type, GRAY)
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r:
                    print("🔄 Resetting world...")
                    self.world_data.clear()
                    self.generated_columns.clear()
                    self.generate_test_world()
                    print("✅ World reset complete!")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click - break blocks
                    self.break_block(event.pos[0], event.pos[1])
                elif event.button == 3:  # Right click - place blocks
                    self.place_block(event.pos[0], event.pos[1], "stone")
        
        # Handle camera movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.camera_x -= 5
        if keys[pygame.K_RIGHT]:
            self.camera_x += 5
        if keys[pygame.K_UP]:
            self.camera_y -= 5
        if keys[pygame.K_DOWN]:
            self.camera_y += 5
        
        return True
    
    def run(self):
        """Main game loop"""
        print("🚀 Block Breaker started!")
        print("💡 Left click to break blocks, Right click to place blocks")
        print("💡 Arrow keys to move camera, R to reset, ESC to quit")
        
        running = True
        while running:
            running = self.handle_events()
            
            # Draw everything
            self.draw_world()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        print("👋 Block Breaker closed!")

def main():
    """Main function"""
    try:
        game = BlockBreaker()
        game.run()
    except Exception as e:
        print(f"❌ Error running Block Breaker: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
