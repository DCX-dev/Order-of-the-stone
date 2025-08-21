import pygame
import os
import json

class CharacterManager:
    def __init__(self, player_dir, tile_size):
        self.player_dir = player_dir
        self.tile_size = tile_size
        self.character_textures = {}
        self.selected_character = "default"
        self.available_characters = [
            {"name": "default", "price": 0, "description": "Basic character", "unlocked": True},
            {"name": "warrior", "price": 100, "description": "Strong fighter", "unlocked": False},
            {"name": "miner", "price": 200, "description": "Expert digger", "unlocked": False},
            {"name": "explorer", "price": 300, "description": "Adventure seeker", "unlocked": False},
            {"name": "mage", "price": 500, "description": "Magic user", "unlocked": False},
            {"name": "ninja", "price": 750, "description": "Stealth master", "unlocked": False},
            {"name": "knight", "price": 1000, "description": "Noble warrior", "unlocked": False},
            {"name": "hacker", "price": 1000000, "description": "ULTIMATE CHARACTER - Requires special achievement", "unlocked": False}
        ]
        
        # Load character textures
        self.load_character_textures()
    
    def load_character_textures(self):
        """Load all character textures from the player folder"""
        print("🎭 Loading character textures...")
        
        # Start with default player texture from existing player.gif
        try:
            self.character_textures["default"] = pygame.transform.scale(
                pygame.image.load(os.path.join(self.player_dir, "player.gif")).convert_alpha(), 
                (self.tile_size, self.tile_size)
            )
            print("✅ Loaded default character texture from player.gif")
        except Exception as e:
            print(f"❌ Could not load player.gif: {e}")
            # Create fallback default texture
            fallback = pygame.Surface((self.tile_size, self.tile_size))
            fallback.fill((100, 150, 200))
            # Draw simple character shape
            pygame.draw.rect(fallback, (255, 200, 150), (10, 8, 12, 10))  # Head
            pygame.draw.rect(fallback, (100, 150, 200), (8, 16, 16, 16))  # Body
            pygame.draw.rect(fallback, (50, 100, 150), (8, 16, 16, 16), 1)  # Outline
            self.character_textures["default"] = fallback
            print("⚠️ Created fallback default character texture")
        
        # Load other character textures (you'll create these)
        for char in self.available_characters:
            if char["name"] != "default":
                try:
                    texture_path = os.path.join(self.player_dir, f"{char['name']}.png")
                    if os.path.exists(texture_path):
                        self.character_textures[char["name"]] = pygame.transform.scale(
                            pygame.image.load(texture_path).convert_alpha(), 
                            (self.tile_size, self.tile_size)
                        )
                        print(f"✅ Loaded character texture: {char['name']}")
                    else:
                        # Create placeholder texture if file doesn't exist
                        placeholder = pygame.Surface((self.tile_size, self.tile_size))
                        placeholder.fill((100, 100, 100))
                        # Draw placeholder text
                        font_small = pygame.font.SysFont("Arial", 16)
                        placeholder_text = font_small.render(char['name'][:3].upper(), True, (255, 255, 255))
                        text_x = (self.tile_size - placeholder_text.get_width()) // 2
                        text_y = (self.tile_size - placeholder_text.get_height()) // 2
                        placeholder.blit(placeholder_text, (text_x, text_y))
                        self.character_textures[char["name"]] = placeholder
                        print(f"⏳ Waiting for {char['name']} texture (you'll create this)")
                except Exception as e:
                    print(f"❌ Error loading texture for {char['name']}: {e}")
                    # Create error texture
                    error_texture = pygame.Surface((self.tile_size, self.tile_size))
                    error_texture.fill((255, 0, 0))
                    # Draw error symbol
                    font_small = pygame.font.SysFont("Arial", 16)
                    error_text = font_small.render("!", True, (255, 255, 255))
                    text_x = (self.tile_size - error_text.get_width()) // 2
                    text_y = (self.tile_size - error_text.get_height()) // 2
                    error_texture.blit(error_text, (text_x, text_y))
                    self.character_textures[char["name"]] = error_texture
        
        print(f"🎭 Character textures loaded: {list(self.character_textures.keys())}")
    
    def select_character(self, character_name):
        """Select a character to use"""
        if character_name != self.selected_character:
            self.selected_character = character_name
            print(f"🎭 Character changed to: {character_name}")
            
            # Debug: Check if texture exists
            if character_name in self.character_textures:
                print(f"✅ Texture found for {character_name}")
            else:
                print(f"❌ No texture found for {character_name}")
                print(f"Available textures: {list(self.character_textures.keys())}")
            
            return True
        return False
    
    def unlock_character(self, character_name, player_coins):
        """Unlock a character by spending coins"""
        # Find the character
        for char in self.available_characters:
            if char["name"] == character_name:
                if player_coins >= char["price"]:
                    char["unlocked"] = True
                    print(f"🎭 Character unlocked: {character_name}")
                    return True, char["price"]  # Return success and cost
                else:
                    print(f"❌ Not enough coins to unlock {character_name}")
                    return False, 0
        return False, 0
    
    def get_character_texture(self, character_name=None):
        """Get the texture for a character, or current selected character if none specified"""
        if character_name is None:
            character_name = self.selected_character
        
        if character_name in self.character_textures:
            return self.character_textures[character_name]
        else:
            # Fallback to default
            return self.character_textures.get("default", None)
    
    def is_character_unlocked(self, character_name):
        """Check if a character is unlocked"""
        for char in self.available_characters:
            if char["name"] == character_name:
                return char["unlocked"]
        return False
    
    def get_character_info(self, character_name):
        """Get character information"""
        for char in self.available_characters:
            if char["name"] == character_name:
                return char
        return None
    
    def get_current_character_name(self):
        """Get the currently selected character name"""
        return self.selected_character
    
    def save_data(self):
        """Get character data for saving"""
        return {
            "selected_character": self.selected_character,
            "available_characters": self.available_characters
        }
    
    def load_data(self, data):
        """Load character data from save"""
        if "selected_character" in data:
            self.selected_character = data["selected_character"]
            print(f"🎭 Loaded selected character: {self.selected_character}")
        
        if "available_characters" in data:
            # Update unlock status for existing characters
            for i, char in enumerate(self.available_characters):
                if char["name"] in [c["name"] for c in data["available_characters"]]:
                    # Find the matching character in saved data
                    for saved_char in data["available_characters"]:
                        if saved_char["name"] == char["name"]:
                            self.available_characters[i]["unlocked"] = saved_char["unlocked"]
                            print(f"🎭 Loaded unlock status for {char['name']}: {saved_char['unlocked']}")
                            break
