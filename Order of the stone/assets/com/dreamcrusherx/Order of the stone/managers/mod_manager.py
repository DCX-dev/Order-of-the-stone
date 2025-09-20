"""
Mod Manager for Order of the Stone
Handles loading, managing, and executing mods
"""

import os
import sys
import importlib.util
import traceback
from typing import Dict, List, Any, Optional

class ModManager:
    def __init__(self, game_instance=None):
        self.game_instance = game_instance
        self.loaded_mods = {}
        self.mod_paths = []
        self.mods_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "assets", "mods")
        
    def load_all_mods(self):
        """Load all mods from the mods directory"""
        print("🔧 Loading mods...")
        
        try:
            if not os.path.exists(self.mods_dir):
                print("📁 Mods directory not found, creating...")
                os.makedirs(self.mods_dir, exist_ok=True)
                print("✅ Mods directory created")
                return
            
            # Find all mod files and folders
            mod_items = []
            for item in os.listdir(self.mods_dir):
                item_path = os.path.join(self.mods_dir, item)
                if os.path.isfile(item_path) and item.endswith('.py'):
                    mod_items.append(('file', item, item_path))
                elif os.path.isdir(item_path) and not item.startswith('.'):
                    # Check if folder has __init__.py
                    init_path = os.path.join(item_path, '__init__.py')
                    if os.path.exists(init_path):
                        mod_items.append(('folder', item, item_path))
            
            if not mod_items:
                print("📁 No mods found in mods directory")
                return
            
            print(f"📁 Found {len(mod_items)} mod(s) to load")
            
            # Load each mod
            loaded_count = 0
            for mod_type, mod_name, mod_path in mod_items:
                try:
                    print(f"🔧 Loading mod: {mod_name}")
                    self.load_mod(mod_name, mod_path, mod_type)
                    loaded_count += 1
                except Exception as e:
                    print(f"❌ Failed to load mod '{mod_name}': {e}")
                    traceback.print_exc()
                    # Continue loading other mods even if one fails
            
            print(f"✅ Successfully loaded {loaded_count}/{len(mod_items)} mods")
            
        except Exception as e:
            print(f"❌ Critical error in mod loading system: {e}")
            traceback.print_exc()
            print("🎮 Game will continue without mods")
    
    def load_mod(self, mod_name: str, mod_path: str, mod_type: str):
        """Load a single mod"""
        try:
            if mod_type == 'file':
                # Load single Python file
                spec = importlib.util.spec_from_file_location(mod_name, mod_path)
                if not spec or not spec.loader:
                    raise ImportError(f"Could not load spec for {mod_name}")
                mod_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod_module)
            else:
                # Load mod folder
                sys.path.insert(0, mod_path)
                try:
                    # Import the __init__.py file from the mod folder
                    mod_module = importlib.import_module('__init__')
                finally:
                    sys.path.pop(0)
            
            # Initialize mod
            mod_info = {
                'name': mod_name,
                'module': mod_module,
                'path': mod_path,
                'type': mod_type,
                'enabled': True
            }
            
            # Call mod_init if it exists
            if hasattr(mod_module, 'mod_init'):
                try:
                    mod_module.mod_init(self.game_instance)
                    print(f"✅ Loaded mod: {mod_name}")
                except Exception as e:
                    print(f"⚠️ Mod '{mod_name}' init failed: {e}")
                    # Still add the mod but mark it as disabled
                    mod_info['enabled'] = False
            else:
                print(f"⚠️ Mod '{mod_name}' has no mod_init() function")
            
            self.loaded_mods[mod_name] = mod_info
            
        except Exception as e:
            print(f"❌ Error loading mod '{mod_name}': {e}")
            # Don't re-raise the exception, just log it and continue
            traceback.print_exc()
    
    def update_mods(self):
        """Update all loaded mods"""
        if not self.loaded_mods:
            return
            
        for mod_name, mod_info in self.loaded_mods.items():
            if not mod_info['enabled']:
                continue
                
            try:
                if hasattr(mod_info['module'], 'mod_update'):
                    mod_info['module'].mod_update(self.game_instance)
            except Exception as e:
                print(f"❌ Error updating mod '{mod_name}': {e}")
                # Disable the mod if it keeps crashing
                mod_info['enabled'] = False
                traceback.print_exc()
    
    def call_mod_event(self, event_name: str, *args, **kwargs):
        """Call a specific event on all mods"""
        if not self.loaded_mods:
            return
            
        for mod_name, mod_info in self.loaded_mods.items():
            if not mod_info['enabled']:
                continue
                
            try:
                if hasattr(mod_info['module'], event_name):
                    func = getattr(mod_info['module'], event_name)
                    func(*args, **kwargs)
            except Exception as e:
                print(f"❌ Error calling {event_name} on mod '{mod_name}': {e}")
                # Don't disable mods for event errors, just log them
                traceback.print_exc()
    
    def unload_mod(self, mod_name: str):
        """Unload a specific mod"""
        if mod_name in self.loaded_mods:
            mod_info = self.loaded_mods[mod_name]
            try:
                if hasattr(mod_info['module'], 'mod_cleanup'):
                    mod_info['module'].mod_cleanup()
            except Exception as e:
                print(f"❌ Error cleaning up mod '{mod_name}': {e}")
            
            del self.loaded_mods[mod_name]
            print(f"✅ Unloaded mod: {mod_name}")
    
    def unload_all_mods(self):
        """Unload all mods"""
        for mod_name in list(self.loaded_mods.keys()):
            self.unload_mod(mod_name)
    
    def get_mod(self, mod_name: str) -> Optional[Dict]:
        """Get mod information"""
        return self.loaded_mods.get(mod_name)
    
    def list_mods(self) -> List[str]:
        """Get list of loaded mod names"""
        return list(self.loaded_mods.keys())
    
    def enable_mod(self, mod_name: str):
        """Enable a mod"""
        if mod_name in self.loaded_mods:
            self.loaded_mods[mod_name]['enabled'] = True
            print(f"✅ Enabled mod: {mod_name}")
    
    def disable_mod(self, mod_name: str):
        """Disable a mod"""
        if mod_name in self.loaded_mods:
            self.loaded_mods[mod_name]['enabled'] = False
            print(f"✅ Disabled mod: {mod_name}")

# Global mod manager instance
mod_manager = None

def init_mod_system(game_instance):
    """Initialize the mod system"""
    global mod_manager
    print("🔧 Creating mod manager...")
    mod_manager = ModManager(game_instance)
    print("🔧 Loading all mods...")
    mod_manager.load_all_mods()
    print("🔧 Mod system initialization complete")
    return mod_manager

def get_mod_manager():
    """Get the global mod manager instance"""
    return mod_manager
