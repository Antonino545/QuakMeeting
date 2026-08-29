"""
Common Particle Physics Simulation for QuakMeeting Banners.
Handles turbo afterburner flames, smoke puffs, and sparkle trails.
"""
import math
import random
from typing import List, Dict, Any

class BannerParticleEngine:
    def __init__(self):
        self.flame_particles: List[Dict[str, Any]] = []
        self.smoke_particles: List[Dict[str, Any]] = []
        self.sparkle_particles: List[Dict[str, Any]] = []

    def reset(self):
        self.flame_particles.clear()
        self.smoke_particles.clear()
        self.sparkle_particles.clear()

    def emit_and_update(
        self,
        plane_x: float,
        plane_y: float,
        tick: int,
        is_late: bool,
        is_paused: bool,
        pilot_type: str
    ):
        """Simulates particle emission and frame steps."""
        if not is_paused:
            # 1. Turbo Flame Emitter (When Late / Emergency Mode)
            if is_late:
                for dy_eng in [-10, 10]:
                    self.flame_particles.append({
                        "x": plane_x - 30.0,
                        "y": plane_y + dy_eng + (random.random() - 0.5) * 4.0,
                        "r": 5.5 + random.random() * 3.0,
                        "alpha": 0.95,
                        "vx": -4.2 - random.random() * 2.0,
                        "vy": (random.random() - 0.5) * 1.5,
                        "color_stage": 0.0 # 0=gold/yellow, 1=orange, 2=red
                    })

            # 2. Standard Smoke / Sparkles (Active during flight)
            elif tick % 4 == 0:
                if pilot_type == "captain":
                    self.smoke_particles.append({"x": plane_x - 22, "y": plane_y - 12, "r": 4.0, "alpha": 0.75, "drift": -0.2})
                    self.smoke_particles.append({"x": plane_x - 22, "y": plane_y + 12, "r": 4.0, "alpha": 0.75, "drift": 0.2})
                elif pilot_type == "zen_duck":
                    self.smoke_particles.append({"x": plane_x - 28, "y": plane_y + 4, "r": 4.5, "alpha": 0.65, "drift": 0.0})
                    if tick % 8 == 0:
                        self.sparkle_particles.append({"x": plane_x - 24, "y": plane_y + 8, "r": 3.0, "alpha": 0.9, "vy": 0.4})
                elif pilot_type == "owl":
                    self.smoke_particles.append({"x": plane_x - 26, "y": plane_y + 6, "r": 4.2, "alpha": 0.6, "drift": 0.0})
                    if tick % 10 == 0:
                        self.sparkle_particles.append({"x": plane_x - 22, "y": plane_y + 10, "r": 3.2, "alpha": 0.95, "vy": 0.3})
                else:
                    self.smoke_particles.append({
                        "x": plane_x - 28,
                        "y": plane_y + 6,
                        "r": 4.8,
                        "alpha": 0.75,
                        "drift": math.sin(tick * 0.1) * 0.4
                    })

        # Update flames
        new_flames = []
        for f in self.flame_particles:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            f["r"] += 0.4
            f["alpha"] -= 0.05
            f["color_stage"] = min(2.0, f["color_stage"] + 0.1)
            if f["alpha"] > 0 and f["r"] < 28:
                new_flames.append(f)
        self.flame_particles = new_flames

        # Update smoke
        new_particles = []
        for p in self.smoke_particles:
            p["x"] -= 2.4
            p["y"] += p.get("drift", 0.0) + math.sin(p["x"] * 0.04) * 0.3
            p["r"] += 0.35
            p["alpha"] -= 0.022
            if p["alpha"] > 0 and p["r"] < 24:
                new_particles.append(p)
        self.smoke_particles = new_particles

        # Update sparkles
        new_sparkles = []
        for s in self.sparkle_particles:
            s["x"] -= 1.8
            s["y"] += s["vy"]
            s["alpha"] -= 0.028
            s["r"] = max(0.5, s["r"] - 0.04)
            if s["alpha"] > 0:
                new_sparkles.append(s)
        self.sparkle_particles = new_sparkles
