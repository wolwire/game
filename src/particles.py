"""Particles + ambient rain. Particles live in world space (tile units)
with a z height in pixels; rain is screen-space."""
import math
import random
import pygame
from src.constants import WIDTH, HEIGHT
from src.iso import world_to_screen


class P:
    __slots__ = ('x', 'y', 'z', 'vx', 'vy', 'vz', 'life', 'total', 'color', 'size', 'grav')

    def __init__(self, x, y, z, vx, vy, vz, life, color, size, grav=120.0):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = self.total = life
        self.color, self.size, self.grav = color, size, grav


class Particles:
    def __init__(self):
        self.parts = []
        self.rings = []   # (x, y, r, max_r, life)
        self.rain = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                      random.uniform(6, 13)] for _ in range(90)]

    # ---- emitters ----
    def _burst(self, x, y, n, color, speed=2.0, life=0.5, size=3, z=20, vz=60):
        for _ in range(n):
            a = random.random() * 2 * math.pi
            s = speed * random.uniform(0.3, 1.0)
            self.parts.append(P(x, y, z + random.uniform(-4, 10),
                                math.cos(a) * s, math.sin(a) * s,
                                random.uniform(0, vz),
                                life * random.uniform(0.6, 1.3), color,
                                random.randint(max(1, size - 1), size + 1)))

    def hit(self, x, y):
        self._burst(x, y, 8, (255, 226, 140), 2.4, 0.35)

    def blood(self, x, y):
        self._burst(x, y, 10, (190, 50, 56), 2.0, 0.5)

    def block_spark(self, x, y):
        self._burst(x, y, 6, (200, 205, 220), 2.6, 0.3, size=2)

    def parry_spark(self, x, y):
        self._burst(x, y, 18, (140, 220, 255), 3.4, 0.5, size=3)
        self.rings.append([x, y, 0.2, 1.6, 0.35])

    def death_burst(self, x, y, big=False):
        n = 40 if big else 18
        self._burst(x, y, n, (150, 210, 255), 3.0 if big else 2.2, 0.9, size=3)
        self.rings.append([x, y, 0.2, 2.6 if big else 1.4, 0.5])

    def shard_sparkle(self, x, y):
        self._burst(x, y, 2, (170, 220, 255), 0.6, 0.7, size=2, vz=40)

    def static_burst(self, x, y):
        self._burst(x, y, 14, (130, 230, 255), 2.6, 0.4, size=2)

    def note(self, x, y):
        self._burst(x, y, 5, (210, 150, 255), 1.4, 0.7, size=2, z=42)

    def slam(self, x, y, r):
        self.rings.append([x, y, 0.2, r, 0.3])
        self._burst(x, y, 14, (220, 190, 120), 3.0, 0.4)

    def shockwave(self, x, y):
        self.rings.append([x, y, 0.3, 4.0, 0.6])
        self._burst(x, y, 30, (255, 200, 110), 4.0, 0.7)

    def beacon_idle(self, x, y):
        if random.random() < 0.25:
            self.parts.append(P(x + random.uniform(-0.3, 0.3), y + random.uniform(-0.3, 0.3),
                                10, 0, 0, 36, 1.2, (120, 215, 255), 2, grav=0))

    # ---- update / draw ----
    def update(self, dt):
        for p in self.parts[:]:
            p.life -= dt
            if p.life <= 0:
                self.parts.remove(p)
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.z += p.vz * dt
            p.vz -= p.grav * dt
            if p.z < 0:
                p.z = 0
                p.vz *= -0.4
        for r in self.rings[:]:
            r[4] -= dt
            r[2] += (r[3] - r[2]) * 10 * dt
            if r[4] <= 0:
                self.rings.remove(r)
        for drop in self.rain:
            drop[0] -= drop[2] * 0.35
            drop[1] += drop[2]
            if drop[1] > HEIGHT or drop[0] < 0:
                drop[0] = random.uniform(0, WIDTH * 1.2)
                drop[1] = random.uniform(-30, -5)

    def draw_world(self, screen, ox, oy):
        for r in self.rings:
            sx, sy = world_to_screen(r[0], r[1])
            rad = r[2]
            pygame.draw.ellipse(screen, (200, 220, 255),
                                (sx + ox - rad * 32, sy + oy - rad * 16, rad * 64, rad * 32), 2)
        for p in self.parts:
            sx, sy = world_to_screen(p.x, p.y, p.z)
            a = max(0.0, min(1.0, p.life / p.total))
            c = (int(p.color[0] * a + 20 * (1 - a)), int(p.color[1] * a + 20 * (1 - a)),
                 int(p.color[2] * a + 24 * (1 - a)))
            pygame.draw.circle(screen, c, (int(sx + ox), int(sy + oy)), max(1, int(p.size * a + 0.5)))

    def draw_rain(self, screen):
        for x, y, s in self.rain:
            pygame.draw.line(screen, (96, 110, 130), (x, y), (x - s * 0.3, y + s), 1)
