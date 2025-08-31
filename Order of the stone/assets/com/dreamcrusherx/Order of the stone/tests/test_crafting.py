#!/usr/bin/env python3
"""
Test script for the new crafting system
This demonstrates the improved crafting interface with tabs and working slots
"""

import pygame
import sys

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (150, 150, 150)
GREEN = (0, 150, 0)
RED = (200, 0, 0)

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Crafting System Test")
clock = pygame.time.Clock()

# Font
font = pygame.font.Font(None, 24)

# Crafting system variables
crafting_materials = [None] * 9  # 3x3 grid
material_counts = {}
current_crafting_tab = "crafting"  # "crafting" or "recipes"
show_crafting = True

# Sample crafting recipes
CRAFTING_RECIPES = {
    "pickaxe": {
        "name": "Wooden Pickaxe",
        "materials": {"oak_planks": 2, "stone": 1},
        "description": "Basic mining tool"
    },
    "sword": {
        "name": "Wooden Sword",
        "materials": {"oak_planks": 2},
        "description": "Basic combat weapon"
    },
    "stone_sword": {
        "name": "Stone Sword",
        "materials": {"stone": 2, "oak_planks": 1},
        "description": "Stronger combat weapon"
    }
}

def add_to_crafting(material, slot_index=None):
    """Add material to crafting grid"""
    if slot_index is not None and 0 <= slot_index < 9:
        # Add to specific slot
        old_material = crafting_materials[slot_index]
        if old_material:
            # Remove old material count
            if old_material in material_counts:
                material_counts[old_material] = max(0, material_counts[old_material] - 1)
                if material_counts[old_material] == 0:
                    del material_counts[old_material]
        
        crafting_materials[slot_index] = material
        material_counts[material] = material_counts.get(material, 0) + 1
        print(f"⚒️ Added {material} to crafting slot {slot_index}")
    else:
        # Add to next available slot
        for i, slot in enumerate(crafting_materials):
            if slot is None:
                crafting_materials[i] = material
                material_counts[material] = material_counts.get(material, 0) + 1
                print(f"⚒️ Added {material} to crafting slot {i}")
                return
        print("⚒️ Crafting grid is full!")

def remove_from_crafting(slot_index):
    """Remove item from specific crafting slot"""
    if 0 <= slot_index < len(crafting_materials):
        material = crafting_materials[slot_index]
        if material:
            # Remove from crafting
            crafting_materials[slot_index] = None
            # Update material counts
            if material in material_counts:
                material_counts[material] = max(0, material_counts[material] - 1)
                if material_counts[material] == 0:
                    del material_counts[material]
            print(f"⚒️ Removed {material} from crafting slot {slot_index}")

def clear_crafting():
    """Clear crafting grid"""
    global crafting_materials, material_counts
    crafting_materials = [None] * 9
    material_counts.clear()
    print("⚒️ Cleared crafting grid")

def check_crafting_recipe(materials):
    """Check if materials match any crafting recipe"""
    for recipe_name, recipe in CRAFTING_RECIPES.items():
        if materials == recipe["materials"]:
            return recipe_name
    return None

def draw_crafting_interface():
    """Draw the crafting interface with tabs"""
    if not show_crafting:
        return
    
    # Crafting background
    crafting_x = SCREEN_WIDTH // 2 - 250
    crafting_y = SCREEN_HEIGHT // 2 - 200
    crafting_width = 500
    crafting_height = 400
    
    pygame.draw.rect(screen, DARK_GRAY, (crafting_x, crafting_y, crafting_width, crafting_height))
    pygame.draw.rect(screen, LIGHT_GRAY, (crafting_x, crafting_y, crafting_width, crafting_height), 3)
    
    # Tab buttons
    tab_y = crafting_y + 10
    tab_width = 120
    tab_height = 30
    
    # Crafting tab
    crafting_tab_rect = pygame.Rect(crafting_x + 10, tab_y, tab_width, tab_height)
    crafting_tab_color = GRAY if current_crafting_tab == "crafting" else DARK_GRAY
    pygame.draw.rect(screen, crafting_tab_color, crafting_tab_rect)
    pygame.draw.rect(screen, LIGHT_GRAY, crafting_tab_rect, 2)
    crafting_tab_text = font.render("⚒️ Crafting", True, WHITE)
    screen.blit(crafting_tab_text, (crafting_tab_rect.x + 10, crafting_tab_rect.y + 5))
    
    # Recipes tab
    recipes_tab_rect = pygame.Rect(crafting_x + 140, tab_y, tab_width, tab_height)
    recipes_tab_color = GRAY if current_crafting_tab == "recipes" else DARK_GRAY
    pygame.draw.rect(screen, recipes_tab_color, recipes_tab_rect)
    pygame.draw.rect(screen, LIGHT_GRAY, recipes_tab_rect, 2)
    recipes_tab_text = font.render("📖 Recipes", True, WHITE)
    screen.blit(recipes_tab_text, (recipes_tab_rect.x + 10, recipes_tab_rect.y + 5))
    
    # Close button
    close_btn = pygame.Rect(crafting_x + crafting_width - 30, crafting_y + 10, 20, 20)
    pygame.draw.rect(screen, RED, close_btn)
    pygame.draw.rect(screen, WHITE, close_btn, 2)
    close_text = font.render("X", True, WHITE)
    screen.blit(close_text, (close_btn.x + 5, close_btn.y + 2))
    
    # Draw content based on current tab
    if current_crafting_tab == "crafting":
        draw_crafting_tab(crafting_x, crafting_y, crafting_width, crafting_height)
    else:
        draw_recipes_tab(crafting_x, crafting_y, crafting_width, crafting_height)

def draw_crafting_tab(crafting_x, crafting_y, crafting_width, crafting_height):
    """Draw the crafting tab with 3x3 grid and output"""
    # Title
    title_text = font.render("⚒️ CRAFTING GRID", True, WHITE)
    screen.blit(title_text, (crafting_x + 20, crafting_y + 50))
    
    # Material input slots (3x3 grid)
    slot_size = 40
    start_x = crafting_x + 50
    start_y = crafting_y + 80
    
    for i in range(9):
        row = i // 3
        col = i % 3
        slot_x = start_x + col * (slot_size + 10)
        slot_y = start_y + row * (slot_size + 10)
        
        # Draw slot with 3D effect
        pygame.draw.rect(screen, GRAY, (slot_x, slot_y, slot_size, slot_size))
        pygame.draw.line(screen, LIGHT_GRAY, (slot_x, slot_y), (slot_x + slot_size, slot_y), 2)
        pygame.draw.line(screen, LIGHT_GRAY, (slot_x, slot_y), (slot_x, slot_y + slot_size), 2)
        pygame.draw.line(screen, BLACK, (slot_x, slot_y + slot_size), (slot_x + slot_size, slot_y + slot_size), 2)
        pygame.draw.line(screen, BLACK, (slot_x + slot_size, slot_y), (slot_x + slot_size, slot_y + slot_size), 2)
        
        # Draw item if exists
        if crafting_materials[i]:
            material = crafting_materials[i]
            # Draw material name
            material_text = font.render(material, True, WHITE)
            screen.blit(material_text, (slot_x + 2, slot_y + 10))
            # Draw count
            count_text = font.render(str(material_counts.get(material, 1)), True, (255, 255, 0))
            screen.blit(count_text, (slot_x + 25, slot_y + 25))
        else:
            # Draw empty slot indicator
            empty_text = font.render("+", True, (120, 120, 120))
            screen.blit(empty_text, (slot_x + 15, slot_y + 10))
    
    # Output slot
    output_x = crafting_x + 350
    output_y = crafting_y + 120
    pygame.draw.rect(screen, LIGHT_GRAY, (output_x, output_y, slot_size, slot_size))
    pygame.draw.rect(screen, WHITE, (output_x, output_y, slot_size, slot_size), 3)
    
    # Check recipe and show output
    recipe_name = check_crafting_recipe(material_counts)
    if recipe_name:
        recipe = CRAFTING_RECIPES[recipe_name]
        # Show recipe name
        recipe_text = font.render(recipe["name"], True, (255, 255, 0))
        screen.blit(recipe_text, (output_x - 200, output_y + 50))
        
        # Show description
        desc_text = font.render(recipe["description"], True, (200, 200, 200))
        screen.blit(desc_text, (output_x - 200, output_y + 70))
        
        # Craft button
        craft_btn = pygame.Rect(output_x - 200, output_y + 100, 120, 30)
        pygame.draw.rect(screen, GREEN, craft_btn)
        pygame.draw.rect(screen, WHITE, craft_btn, 2)
        
        craft_text = font.render("CRAFT", True, WHITE)
        screen.blit(craft_text, (craft_btn.x + 10, craft_btn.y + 5))
    
    # Instructions
    instruction_text = font.render("Click on slots to add materials from inventory", True, (200, 200, 200))
    screen.blit(instruction_text, (crafting_x + 20, crafting_y + 320))
    
    # Clear button
    clear_btn = pygame.Rect(crafting_x + 20, crafting_y + 350, 100, 30)
    pygame.draw.rect(screen, (150, 100, 100), clear_btn)
    pygame.draw.rect(screen, WHITE, clear_btn, 2)
    clear_text = font.render("Clear All", True, WHITE)
    screen.blit(clear_text, (clear_btn.x + 10, clear_btn.y + 5))

def draw_recipes_tab(crafting_x, crafting_y, crafting_width, crafting_height):
    """Draw the recipes tab with clickable recipe buttons"""
    # Title
    title_text = font.render("📖 CRAFTING RECIPES", True, WHITE)
    screen.blit(title_text, (crafting_x + 20, crafting_y + 50))
    
    # Recipe buttons
    button_width = 200
    button_height = 60
    start_x = crafting_x + 20
    start_y = crafting_y + 80
    buttons_per_row = 2
    
    for i, (recipe_name, recipe) in enumerate(CRAFTING_RECIPES.items()):
        row = i // buttons_per_row
        col = i % buttons_per_row
        button_x = start_x + col * (button_width + 20)
        button_y = start_y + row * (button_height + 15)
        
        # Button color (always green for demo)
        button_color = (100, 150, 100)
        pygame.draw.rect(screen, button_color, (button_x, button_y, button_width, button_height))
        pygame.draw.rect(screen, WHITE, (button_x, button_y, button_width, button_height), 2)
        
        # Recipe name
        name_text = font.render(recipe["name"], True, WHITE)
        screen.blit(name_text, (button_x + 10, button_y + 5))
        
        # Materials needed
        materials_text = font.render(f"Materials: {', '.join([f'{count}x {mat}' for mat, count in recipe['materials'].items()])}", True, (200, 200, 200))
        screen.blit(materials_text, (button_x + 10, button_y + 25))
        
        # Status text
        status_text = font.render("✅ Can Craft", True, (0, 255, 0))
        screen.blit(status_text, (button_x + 10, button_y + 40))
    
    # Instructions
    instruction_text = font.render("Click on recipes to auto-fill crafting grid", True, (200, 200, 200))
    screen.blit(instruction_text, (crafting_x + 20, crafting_y + 320))

def handle_crafting_clicks(mouse_pos):
    """Handle clicks in the crafting interface"""
    global show_crafting, current_crafting_tab
    
    # Crafting background coordinates
    crafting_x = SCREEN_WIDTH // 2 - 250
    crafting_y = SCREEN_HEIGHT // 2 - 200
    crafting_width = 500
    crafting_height = 400
    
    # Check if click is within crafting area
    if not (crafting_x <= mouse_pos[0] <= crafting_x + crafting_width and 
            crafting_y <= mouse_pos[1] <= crafting_y + crafting_height):
        return False
    
    # Check tab clicks
    tab_y = crafting_y + 10
    tab_width = 120
    tab_height = 30
    
    # Crafting tab
    crafting_tab_rect = pygame.Rect(crafting_x + 10, tab_y, tab_width, tab_height)
    if crafting_tab_rect.collidepoint(mouse_pos):
        current_crafting_tab = "crafting"
        return True
    
    # Recipes tab
    recipes_tab_rect = pygame.Rect(crafting_x + 140, tab_y, tab_width, tab_height)
    if recipes_tab_rect.collidepoint(mouse_pos):
        current_crafting_tab = "recipes"
        return True
    
    # Close button
    close_btn = pygame.Rect(crafting_x + crafting_width - 30, crafting_y + 10, 20, 20)
    if close_btn.collidepoint(mouse_pos):
        show_crafting = False
        return True
    
    # Handle tab-specific clicks
    if current_crafting_tab == "crafting":
        return handle_crafting_tab_clicks(mouse_pos, crafting_x, crafting_y)
    else:
        return handle_recipes_tab_clicks(mouse_pos, crafting_x, crafting_y)

def handle_crafting_tab_clicks(mouse_pos, crafting_x, crafting_y):
    """Handle clicks in the crafting tab"""
    # Material input slots (3x3 grid)
    slot_size = 40
    start_x = crafting_x + 50
    start_y = crafting_y + 80
    
    for i in range(9):
        row = i // 3
        col = i % 3
        slot_x = start_x + col * (slot_size + 10)
        slot_y = start_y + row * (slot_size + 10)
        slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
        
        if slot_rect.collidepoint(mouse_pos):
            if crafting_materials[i]:
                # Remove item from slot
                remove_from_crafting(i)
            else:
                # Add a sample material for testing
                add_to_crafting("stone", i)
            return True
    
    # Clear button
    clear_btn = pygame.Rect(crafting_x + 20, crafting_y + 350, 100, 30)
    if clear_btn.collidepoint(mouse_pos):
        clear_crafting()
        return True
    
    return False

def handle_recipes_tab_clicks(mouse_pos, crafting_x, crafting_y):
    """Handle clicks in the recipes tab"""
    global current_crafting_tab
    
    # Recipe buttons
    button_width = 200
    button_height = 60
    start_x = crafting_x + 20
    start_y = crafting_y + 80
    buttons_per_row = 2
    
    for i, (recipe_name, recipe) in enumerate(CRAFTING_RECIPES.items()):
        row = i // buttons_per_row
        col = i % buttons_per_row
        button_x = start_x + col * (button_width + 20)
        button_y = start_y + row * (button_height + 15)
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        if button_rect.collidepoint(mouse_pos):
            # Auto-fill crafting grid with this recipe
            auto_fill_crafting_grid(recipe_name)
            # Switch to crafting tab
            current_crafting_tab = "crafting"
            return True
    
    return False

def auto_fill_crafting_grid(recipe_name):
    """Auto-fill the crafting grid with recipe materials"""
    if recipe_name not in CRAFTING_RECIPES:
        return False
    
    recipe = CRAFTING_RECIPES[recipe_name]
    materials_needed = recipe["materials"]
    
    # Clear current crafting grid
    clear_crafting()
    
    # Auto-fill the grid based on recipe pattern
    slot_index = 0
    for material, count in materials_needed.items():
        if slot_index < 9:
            add_to_crafting(material, slot_index)
            slot_index += 1
    
    print(f"⚒️ Auto-filled crafting grid with {recipe['name']} recipe")
    return True

def main():
    """Main game loop"""
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    handle_crafting_clicks(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_c:
                    # Toggle crafting interface
                    global show_crafting
                    show_crafting = not show_crafting
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw crafting interface
        if show_crafting:
            draw_crafting_interface()
        
        # Draw instructions
        if not show_crafting:
            instruction_text = font.render("Press C to open crafting interface", True, WHITE)
            screen.blit(instruction_text, (20, 20))
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
