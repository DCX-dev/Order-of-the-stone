# loader.py
import importlib.util, os, traceback
from api.mod_api import ModAPI

_LISTENERS = {}  # event_name -> [functions]

def on(event_name: str, fn):
    _LISTENERS.setdefault(event_name, []).append(fn)

def emit(event_name: str, payload: dict):
    for fn in _LISTENERS.get(event_name, []):
        try:
            fn(payload)
        except Exception as e:
            print(f"[Mod Event Error] {event_name}: {e}")

def load_all_mods(mods_root: str = "mods"):
    """Each mod is a folder containing main.py (entry)."""
    if not os.path.isdir(mods_root):
        print("[Mods] No mods/ folder; skipping.")
        return

    for name in sorted(os.listdir(mods_root)):
        mod_dir = os.path.join(mods_root, name)
        entry = os.path.join(mod_dir, "main.py")
        if not os.path.isdir(mod_dir) or not os.path.isfile(entry):
            continue

        mod_id = name
        try:
            spec = importlib.util.spec_from_file_location(f"oots_mod_{mod_id}", entry)
            module = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(module)  # executes mod code

            api = ModAPI(mod_id=mod_id, mod_dir=mod_dir)
            # Optional metadata
            meta = getattr(module, "MOD_INFO", {"id": mod_id, "version": "1.0"})
            print(f"[Mods] Loaded {meta.get('id', mod_id)} v{meta.get('version','1.0')}")

            # Required entry hook: register(api)
            if hasattr(module, "register"):
                module.register(api)

            # Optional lifecycles
            for hook in ("on_enable", "on_ready"):
                if hasattr(module, hook):
                    try:
                        getattr(module, hook)(api)
                    except Exception:
                        traceback.print_exc()

        except Exception:
            print(f"[Mods] FAILED to load {mod_id}:\n{traceback.format_exc()}")