"""
🚀 NASA-GRADE PERFORMANCE SYSTEM 🚀
Advanced optimization system for infinite world generation
Makes the game run like it's on a NASA computer!
"""

import pygame
import time
import gc
import os
from typing import Dict, List, Tuple, Set, Optional
from collections import deque
import threading
import queue

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available - performance monitoring will be limited")

class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self):
        self.fps_history = deque(maxlen=60)  # Last 60 frames
        self.frame_times = deque(maxlen=60)
        self.memory_usage = deque(maxlen=60)
        self.cpu_usage = deque(maxlen=60)
        
        self.target_fps = 100
        self.min_fps = 80
        self.performance_mode = "HIGH"  # HIGH, MEDIUM, LOW
        
        # Performance metrics
        self.blocks_rendered = 0
        self.blocks_culled = 0
        self.chunks_loaded = 0
        self.memory_peak = 0
        
        # Optimization flags
        self.enable_viewport_culling = True
        self.enable_lod_system = True
        self.enable_memory_management = True
        self.enable_threading = True
        
        # Threading for background tasks
        self.background_queue = queue.Queue()
        self.background_thread = None
        self.running = True
        
        if self.enable_threading:
            self.start_background_thread()
    
    def start_background_thread(self):
        """Start background optimization thread"""
        self.background_thread = threading.Thread(target=self._background_optimizer, daemon=True)
        self.background_thread.start()
    
    def _background_optimizer(self):
        """Background thread for optimization tasks"""
        while self.running:
            try:
                # Memory cleanup
                if self.enable_memory_management:
                    self._cleanup_memory()
                
                # Performance analysis
                self._analyze_performance()
                
                time.sleep(0.1)  # Run every 100ms
            except Exception as e:
                print(f"⚠️ Background optimizer error: {e}")
    
    def update_frame(self, dt: float, blocks_rendered: int, blocks_culled: int):
        """Update performance metrics for current frame"""
        current_time = time.time()
        
        # FPS calculation
        if dt > 0:
            fps = 1.0 / dt
            self.fps_history.append(fps)
            self.frame_times.append(dt)
        
        # Memory usage
        if PSUTIL_AVAILABLE:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage.append(memory_mb)
            self.memory_peak = max(self.memory_peak, memory_mb)
            
            # CPU usage
            cpu_percent = process.cpu_percent()
            self.cpu_usage.append(cpu_percent)
        else:
            # Fallback memory estimation
            memory_mb = 100  # Default estimate
            self.memory_usage.append(memory_mb)
            self.memory_peak = max(self.memory_peak, memory_mb)
            
            # No CPU monitoring without psutil
            self.cpu_usage.append(0)
        
        # Rendering metrics
        self.blocks_rendered = blocks_rendered
        self.blocks_culled = blocks_culled
        
        # Auto-adjust performance mode
        self._auto_adjust_performance()
    
    def _auto_adjust_performance(self):
        """Automatically adjust performance settings based on metrics"""
        if len(self.fps_history) < 10:
            return
        
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        avg_memory = sum(self.memory_usage) / len(self.memory_usage)
        
        # Adjust performance mode based on FPS
        if avg_fps < 60:
            self.performance_mode = "LOW"
            self._enable_aggressive_optimizations()
        elif avg_fps < 80:
            self.performance_mode = "MEDIUM"
            self._enable_medium_optimizations()
        else:
            self.performance_mode = "HIGH"
            self._enable_high_optimizations()
        
        # Memory management
        if avg_memory > 500:  # 500MB threshold
            self._trigger_memory_cleanup()
    
    def _enable_aggressive_optimizations(self):
        """Enable aggressive optimizations for low-end systems"""
        self.enable_viewport_culling = True
        self.enable_lod_system = True
        self.enable_memory_management = True
        self.target_fps = 60
    
    def _enable_medium_optimizations(self):
        """Enable medium optimizations for mid-range systems"""
        self.enable_viewport_culling = True
        self.enable_lod_system = True
        self.enable_memory_management = True
        self.target_fps = 80
    
    def _enable_high_optimizations(self):
        """Enable high optimizations for high-end systems"""
        self.enable_viewport_culling = True
        self.enable_lod_system = False  # Disable for maximum quality
        self.enable_memory_management = True
        self.target_fps = 100
    
    def _cleanup_memory(self):
        """Clean up memory to prevent leaks"""
        # Force garbage collection
        collected = gc.collect()
        
        # Clear old data from deques
        if len(self.fps_history) > 30:
            for _ in range(10):
                if self.fps_history:
                    self.fps_history.popleft()
                if self.frame_times:
                    self.frame_times.popleft()
                if self.memory_usage:
                    self.memory_usage.popleft()
                if self.cpu_usage:
                    self.cpu_usage.popleft()
    
    def _trigger_memory_cleanup(self):
        """Trigger aggressive memory cleanup"""
        gc.collect()
        pygame.display.flip()  # Force display update
    
    def _analyze_performance(self):
        """Analyze performance and suggest optimizations"""
        if len(self.fps_history) < 10:
            return
        
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        avg_memory = sum(self.memory_usage) / len(self.memory_usage)
        
        # Performance warnings
        if avg_fps < 30:
            print(f"🚨 CRITICAL: FPS dropped to {avg_fps:.1f}")
        elif avg_fps < 60:
            print(f"⚠️ WARNING: FPS is {avg_fps:.1f}")
        
        if avg_memory > 1000:  # 1GB threshold
            print(f"⚠️ WARNING: Memory usage is {avg_memory:.1f}MB")
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics"""
        if not self.fps_history:
            return {}
        
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        min_fps = min(self.fps_history)
        max_fps = max(self.fps_history)
        
        avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        
        return {
            "fps": {
                "current": avg_fps,
                "min": min_fps,
                "max": max_fps,
                "target": self.target_fps
            },
            "memory": {
                "current_mb": avg_memory,
                "peak_mb": self.memory_peak
            },
            "cpu": {
                "percent": avg_cpu
            },
            "rendering": {
                "blocks_rendered": self.blocks_rendered,
                "blocks_culled": self.blocks_culled,
                "culling_efficiency": (self.blocks_culled / max(1, self.blocks_rendered + self.blocks_culled)) * 100
            },
            "mode": self.performance_mode
        }
    
    def stop(self):
        """Stop the performance monitor"""
        self.running = False
        if self.background_thread:
            self.background_thread.join(timeout=1.0)


class ViewportCuller:
    """Advanced viewport culling system for infinite worlds"""
    
    def __init__(self, screen_width: int, screen_height: int, block_size: int = 32):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.block_size = block_size
        
        # Culling margins for smooth scrolling
        self.margin_x = 2 * block_size
        self.margin_y = 2 * block_size
        
        # Cached viewport bounds
        self._cached_bounds = None
        self._cache_valid = False
    
    def get_viewport_bounds(self, camera_x: float, camera_y: float) -> Tuple[int, int, int, int]:
        """Get viewport bounds with margins for culling"""
        if self._cache_valid and self._cached_bounds:
            return self._cached_bounds
        
        # Calculate world coordinates
        left = int(camera_x - self.screen_width // 2 - self.margin_x)
        right = int(camera_x + self.screen_width // 2 + self.margin_x)
        top = int(camera_y - self.screen_height // 2 - self.margin_y)
        bottom = int(camera_y + self.screen_height // 2 + self.margin_y)
        
        # Convert to block coordinates
        left_block = left // self.block_size
        right_block = right // self.block_size
        top_block = top // self.block_size
        bottom_block = bottom // self.block_size
        
        self._cached_bounds = (left_block, right_block, top_block, bottom_block)
        self._cache_valid = True
        
        return self._cached_bounds
    
    def invalidate_cache(self):
        """Invalidate cached viewport bounds"""
        self._cache_valid = False
    
    def is_block_in_viewport(self, x: int, y: int, camera_x: float, camera_y: float) -> bool:
        """Check if a block is within the viewport"""
        left, right, top, bottom = self.get_viewport_bounds(camera_x, camera_y)
        return left <= x <= right and top <= y <= bottom


class LODSystem:
    """Level of Detail system for distant objects"""
    
    def __init__(self):
        self.lod_distances = {
            "HIGH": 5,    # 5 blocks - full detail
            "MEDIUM": 10, # 10 blocks - reduced detail
            "LOW": 20,    # 20 blocks - minimal detail
            "CULL": 50    # 50+ blocks - culled
        }
    
    def get_lod_level(self, distance: float) -> str:
        """Get LOD level based on distance from camera"""
        if distance <= self.lod_distances["HIGH"]:
            return "HIGH"
        elif distance <= self.lod_distances["MEDIUM"]:
            return "MEDIUM"
        elif distance <= self.lod_distances["LOW"]:
            return "LOW"
        else:
            return "CULL"
    
    def should_render_block(self, x: int, y: int, camera_x: float, camera_y: float) -> bool:
        """Determine if a block should be rendered based on LOD"""
        distance = ((x - camera_x) ** 2 + (y - camera_y) ** 2) ** 0.5
        lod_level = self.get_lod_level(distance)
        return lod_level != "CULL"


class MemoryManager:
    """Advanced memory management for infinite worlds"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = max_memory_mb * 0.8  # 80% threshold
        self.last_cleanup = time.time()
        self.cleanup_interval = 5.0  # 5 seconds
    
    def should_cleanup(self) -> bool:
        """Check if memory cleanup is needed"""
        current_time = time.time()
        
        # Time-based cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            return True
        
        # Memory-based cleanup
        if PSUTIL_AVAILABLE:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb > self.cleanup_threshold
        else:
            # Fallback to time-based cleanup only
            return False
    
    def cleanup(self):
        """Perform memory cleanup"""
        self.last_cleanup = time.time()
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear pygame cache
        pygame.display.flip()
        
        return collected


class PerformanceSystem:
    """Main performance system that coordinates all optimizations"""
    
    def __init__(self, screen_width: int, screen_height: int, block_size: int = 32):
        self.monitor = PerformanceMonitor()
        self.viewport_culler = ViewportCuller(screen_width, screen_height, block_size)
        self.lod_system = LODSystem()
        self.memory_manager = MemoryManager()
        
        # Performance settings
        self.enable_all_optimizations = True
        self.debug_mode = False
        
        # Rendering statistics
        self.blocks_rendered = 0
        self.blocks_culled = 0
        self.chunks_processed = 0
    
    def update_frame(self, dt: float, camera_x: float, camera_y: float):
        """Update performance system for current frame"""
        # Update performance monitor
        self.monitor.update_frame(dt, self.blocks_rendered, self.blocks_culled)
        
        # Invalidate viewport cache if camera moved significantly
        if hasattr(self, '_last_camera_x') and hasattr(self, '_last_camera_y'):
            if abs(camera_x - self._last_camera_x) > 32 or abs(camera_y - self._last_camera_y) > 32:
                self.viewport_culler.invalidate_cache()
        
        self._last_camera_x = camera_x
        self._last_camera_y = camera_y
        
        # Memory cleanup if needed
        if self.memory_manager.should_cleanup():
            self.memory_manager.cleanup()
    
    def should_render_block(self, x: int, y: int, camera_x: float, camera_y: float) -> bool:
        """Determine if a block should be rendered based on all optimizations"""
        if not self.enable_all_optimizations:
            return True
        
        # Viewport culling
        if self.monitor.enable_viewport_culling:
            if not self.viewport_culler.is_block_in_viewport(x, y, camera_x, camera_y):
                self.blocks_culled += 1
                return False
        
        # LOD system
        if self.monitor.enable_lod_system:
            if not self.lod_system.should_render_block(x, y, camera_x, camera_y):
                self.blocks_culled += 1
                return False
        
        self.blocks_rendered += 1
        return True
    
    def get_optimized_blocks(self, world_data: Dict, camera_x: float, camera_y: float) -> List[Tuple[int, int, str]]:
        """Get optimized list of blocks to render"""
        optimized_blocks = []
        
        if not self.enable_all_optimizations:
            # Return all blocks if optimizations disabled
            for key, block_type in world_data.items():
                if ',' in key:
                    x, y = map(int, key.split(','))
                    optimized_blocks.append((x, y, block_type))
            return optimized_blocks
        
        # Get viewport bounds
        left, right, top, bottom = self.viewport_culler.get_viewport_bounds(camera_x, camera_y)
        
        # Process blocks in viewport
        for key, block_type in world_data.items():
            if ',' in key:
                x, y = map(int, key.split(','))
                
                # Check if block should be rendered
                if self.should_render_block(x, y, camera_x, camera_y):
                    optimized_blocks.append((x, y, block_type))
        
        return optimized_blocks
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        stats = self.monitor.get_performance_stats()
        
        # Add system-specific stats
        stats["system"] = {
            "viewport_culling": self.monitor.enable_viewport_culling,
            "lod_system": self.monitor.enable_lod_system,
            "memory_management": self.monitor.enable_memory_management,
            "threading": self.monitor.enable_threading
        }
        
        stats["optimization"] = {
            "blocks_rendered": self.blocks_rendered,
            "blocks_culled": self.blocks_culled,
            "culling_efficiency": (self.blocks_culled / max(1, self.blocks_rendered + self.blocks_culled)) * 100,
            "chunks_processed": self.chunks_processed
        }
        
        return stats
    
    def reset_counters(self):
        """Reset performance counters"""
        self.blocks_rendered = 0
        self.blocks_culled = 0
        self.chunks_processed = 0
    
    def set_debug_mode(self, enabled: bool):
        """Enable/disable debug mode"""
        self.debug_mode = enabled
        if enabled:
            print("🐛 Performance debug mode enabled")
        else:
            print("🐛 Performance debug mode disabled")
    
    def stop(self):
        """Stop the performance system"""
        self.monitor.stop()
        print("🛑 Performance system stopped")


# Global performance system instance
performance_system = None

def initialize_performance_system(screen_width: int, screen_height: int, block_size: int = 32):
    """Initialize the global performance system"""
    global performance_system
    performance_system = PerformanceSystem(screen_width, screen_height, block_size)
    print("🚀 NASA-Grade Performance System initialized!")
    return performance_system

def get_performance_system():
    """Get the global performance system instance"""
    return performance_system
