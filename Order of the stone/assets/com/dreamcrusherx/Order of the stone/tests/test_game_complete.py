#!/usr/bin/env python3
"""
Complete test of the game systems
"""
import sys
sys.path.append('../../../../../..')

# Import the main game module
try:
    import order_of_the_stone as game
except ImportError:
    print("❌ Could not import order_of_the_stone")
    print("   Make sure you're running this from the correct directory")
    sys.exit(1)

print("🎮 Complete Game Systems Test")
print("=" * 50)

# Test 1: Load game
print("\n1. Testing load_game()...")
try:
    result = game.load_game()
    print(f"✅ load_game() returned: {result}")
    if result:
        print(f"   - World data: {len(game.world_data)} blocks")
        print(f"   - Player: ({game.player['x']}, {game.player['y']})")
        print(f"   - Entities: {len(game.entities)}")
    else:
        print("❌ load_game() failed")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error in load_game(): {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check coordinate conversion
print("\n2. Testing coordinate conversion...")
TILE_SIZE = game.TILE_SIZE
camera_x, camera_y = game.camera_x, game.camera_y
print(f"   - TILE_SIZE: {TILE_SIZE}")
print(f"   - Camera: ({camera_x}, {camera_y})")

# Test mouse position (400, 300) -> world coordinates
mx, my = 400, 300
bx, by = (mx + camera_x) // TILE_SIZE, (my + camera_y) // TILE_SIZE
print(f"   - Mouse ({mx}, {my}) -> World ({bx}, {by})")

# Test 3: Check block access
print("\n3. Testing block access...")
test_positions = [(0, 64), (1, 64), (2, 64), (0, 63), (0, 65)]
for x, y in test_positions:
    block = game.get_block(x, y)
    print(f"   - Block at ({x}, {y}): {block}")

# Test 4: Check chest system
print("\n4. Testing chest system...")
try:
    chest_system = game.chest_system
    print(f"✅ Chest system initialized: {chest_system}")
    print(f"   - CHEST_ROWS: {chest_system.CHEST_ROWS}")
    print(f"   - CHEST_COLS: {chest_system.CHEST_COLS}")
    
    # Generate test chest loot
    test_loot = chest_system.generate_chest_loot("fortress")
    print(f"   - Test fortress loot: {test_loot}")
except Exception as e:
    print(f"❌ Error with chest system: {e}")

# Test 5: Check if there are chests in the world
print("\n5. Checking for chests in world...")
chest_count = 0
chest_positions = []
for pos, block_type in game.world_data.items():
    if block_type == "chest":
        chest_count += 1
        if len(chest_positions) < 3:  # Show first 3 chest positions
            chest_positions.append(pos)

print(f"   - Total chests in world: {chest_count}")
print(f"   - Sample chest positions: {chest_positions}")

# Test 6: Test range check
print("\n6. Testing range check...")
px, py = int(game.player["x"]), int(game.player["y"])
print(f"   - Player position: ({px}, {py})")

# Check blocks within range
nearby_blocks = []
for dx in range(-3, 4):
    for dy in range(-3, 4):
        x, y = px + dx, py + dy
        block = game.get_block(x, y)
        if block and block != "air":
            distance = abs(dx) + abs(dy)  # Manhattan distance
            nearby_blocks.append((x, y, block, distance))

print(f"   - Nearby blocks (within 3): {len(nearby_blocks)}")
for x, y, block, dist in nearby_blocks[:5]:  # Show first 5
    print(f"     ({x}, {y}): {block} (distance: {dist})")

print("\n" + "=" * 50)
print("🎮 Test completed!")

if chest_count > 0:
    print("✅ Chests found in world - chest opening should work")
else:
    print("❌ No chests found in world - this might be the issue")

if len(nearby_blocks) > 0:
    print("✅ Blocks found near player - breaking should work")
else:
    print("❌ No blocks found near player - this might be the issue")
