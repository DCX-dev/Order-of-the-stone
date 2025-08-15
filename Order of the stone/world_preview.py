import pygame
import os
import time
from typing import Optional, Tuple

class WorldPreview:
    """Manages world preview screenshots and thumbnails"""
    
    def __init__(self, save_dir: str = "save_data"):
        self.save_dir = save_dir
        self.preview_dir = os.path.join(save_dir, "previews")
        self.screenshot_interval = 300  # 5 minutes in seconds
        self.last_screenshot_time = 0
        
        # Ensure preview directory exists
        if not os.path.exists(self.preview_dir):
            os.makedirs(self.preview_dir)
    
    def should_take_screenshot(self) -> bool:
        """Check if it's time to take a new screenshot"""
        current_time = time.time()
        return current_time - self.last_screenshot_time >= self.screenshot_interval
    
    def take_world_screenshot(self, world_name: str, screen: pygame.Surface) -> bool:
        """Take a screenshot of the current world and save it"""
        try:
            # Create a smaller thumbnail version
            thumbnail_size = (160, 120)  # 4:3 aspect ratio
            
            # Scale down the screen surface
            thumbnail = pygame.transform.scale(screen, thumbnail_size)
            
            # Save the preview directly with pygame
            preview_path = os.path.join(self.preview_dir, f"{world_name}_preview.png")
            pygame.image.save(thumbnail, preview_path)
            
            # Update last screenshot time
            self.last_screenshot_time = time.time()
            
            print(f"World preview saved for {world_name}")
            return True
            
        except Exception as e:
            print(f"Error taking world preview: {e}")
            return False
    

    
    def get_world_preview(self, world_name: str) -> Optional[pygame.Surface]:
        """Load and return a world preview thumbnail"""
        try:
            preview_path = os.path.join(self.preview_dir, f"{world_name}_preview.png")
            
            if os.path.exists(preview_path):
                # Load the preview image
                preview_surface = pygame.image.load(preview_path)
                return preview_surface
            else:
                # Return a default preview if none exists
                return self.create_default_preview()
                
        except Exception as e:
            print(f"Error loading world preview: {e}")
            return self.create_default_preview()
    
    def create_default_preview(self) -> pygame.Surface:
        """Create a default preview when none exists"""
        # Create a 160x120 surface with a default pattern
        surface = pygame.Surface((160, 120))
        surface.fill((50, 50, 50))  # Dark gray background
        
        # Add some default elements
        pygame.draw.rect(surface, (100, 100, 100), (20, 20, 120, 80))  # Main area
        pygame.draw.rect(surface, (150, 150, 150), (40, 40, 80, 40))   # Center area
        
        return surface
    
    def has_preview(self, world_name: str) -> bool:
        """Check if a world has a preview image"""
        preview_path = os.path.join(self.preview_dir, f"{world_name}_preview.png")
        return os.path.exists(preview_path)
    
    def delete_world_preview(self, world_name: str):
        """Delete a world's preview image"""
        try:
            preview_path = os.path.join(self.preview_dir, f"{world_name}_preview.png")
            if os.path.exists(preview_path):
                os.remove(preview_path)
                print(f"Deleted preview for {world_name}")
        except Exception as e:
            print(f"Error deleting preview for {world_name}: {e}")
    
    def cleanup_old_previews(self, valid_world_names: list):
        """Remove preview files for worlds that no longer exist"""
        try:
            for filename in os.listdir(self.preview_dir):
                if filename.endswith("_preview.png"):
                    world_name = filename[:-13]  # Remove "_preview.png"
                    if world_name not in valid_world_names:
                        self.delete_world_preview(world_name)
        except Exception as e:
            print(f"Error cleaning up old previews: {e}")
