"""Particles, damage numbers, persistent blood decals, ambient rain."""
import math
import random
import pygame
from src.constants import WIDTH, HEIGHT
from src.iso import world_to_screen

pygame.font.init()
_DMG_FONT = pygame.font.SysFont('dejavusansmono', 13, bold=True)


class P:
    __slots__ = ('x', 'y', 'z', 'vx', 'vy', 'vz', 'life', 'total', 'color', 'size', 'grav')

    def __init__(self, x, y, z, vx, vy, vz, life, color, size, grav=240.0):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = self.total = life
        self.color, self.size, self.grav = color, size, grav


class Particles:
    def __init__(self):
        self.parts = []
        self.rings = []     # [x, y, r, max_r, life]
        self.numbers = []   # [x, y, z, value_surf, life]
        self.decals = []    # [(x, y, surf)] persistent ground blood
        self.rain = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                      random.uniform(7, 14)] for _ in range(110)]

    def _burst(self, x, y, n, color, speed=4.0, life=0.5, size=3, z=20, vz=70):
        for _ in range(n):
            a = random.random() * 2 * math.pi
            s = speed * random.uniform(0.3, 1.0)
            self.parts.append(P(x, y, z + random.uniform(-4, 10),
                                math.cos(a) * s, math.sin(a) * s,
                                random.uniform(0, vz),
                                life * random.uniform(0.6, 1.3), color,
                                random.randint(max(1, size - 1), size + 1)))

    def hit(self, x, y):
        self._burst(x, y, 8, (255, 226, 140), 4.8, 0.35)

    def blood(self, x, y):
        self._burst(x, y, 10, (170, 40, 46), 4.0, 0.5)

    def blood_decal(self, x, y):
        if len(self.decals) > 160:
            self.decals.pop(0)
        surf = pygame.Surface((30, 16), pygame.SRCALPHA)
        rng = random.Random(int(x * 31 + y * 57))
        for _ in range(7):
            px, py = rng.randint(4, 24), rng.randint(3, 12)
            r = rng.randint(2, 5)
            pygame.draw.ellipse(surf, (96, 22, 26, 150), (px, py, r * 2, r))
        self.decals.append((x, y, surf))

    def block_spark(self, x, y):
        self._burst(x, y, 6, (200, 205, 220), 5.2, 0.3, size=2)

    def parry_spark(self, x, y):
        self._burst(x, y, 18, (140, 220, 255), 6.8, 0.5, size=3)
        self.rings.append([x, y, 0.4, 3.2, 0.35])

    def death_burst(self, x, y, big=False):
        n = 40 if big else 18
        self._burst(x, y, n, (150, 210, 255), 6.0 if big else 4.4, 0.9, size=3)
        self.rings.append([x, y, 0.4, 5.2 if big else 2.8, 0.5])

    def shard_sparkle(self, x, y):
        self._burst(x, y, 2, (170, 220, 255), 1.2, 0.7, size=2, vz=40)

    def static_burst(self, x, y):
        self._burst(x, y, 14, (130, 230, 255), 5.2, 0.4, size=2)

    def note(self, x, y):
        self._burst(x, y, 5, (210, 150, 255), 2.8, 0.7, size=2, z=42)

    def alert(self, x, y):
        self._burst(x, y, 3, (255, 90, 90), 1.0, 0.4, size=2, z=46, vz=30)

    def slam(self, x, y, r):
        self.rings.append([x, y, 0.4, r, 0.3])
        self._burst(x, y, 14, (220, 190, 120), 6.0, 0.4)

    def shockwave(self, x, y):
        self.rings.append([x, y, 0.6, 8.0, 0.6])
        self._burst(x, y, 30, (255, 200, 110), 8.0, 0.7)

    def beacon_idle(self, x, y):
        if random.random() < 0.3:
            self.parts.append(P(x + random.uniform(-0.6, 0.6), y + random.uniform(-0.6, 0.6),
                                10, 0, 0, 40, 1.4, (120, 215, 255), 2, grav=0))

    def damage_number(self, x, y, value):
        img = _DMG_FONT.render(str(value), True, (255, 232, 180))
        sh_ = _DMG_FONT.render(str(value), True, (20, 10, 5))
        comp = pygame.Surface((img.get_width() + 2, img.get_height() + 2), pygame.SRCALPHA)
        comp.blit(sh_, (1, 2))
        comp.blit(img, (0, 0))
        self.numbers.append([x + random.uniform(-0.4, 0.4), y, 34, comp, 0.8])

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
        for n in self.numbers[:]:
            n[4] -= dt
            n[2] += 30 * dt
            if n[4] <= 0:
                self.numbers.remove(n)
        for drop in self.rain:
            drop[0] -= drop[2] * 0.35
            drop[1] += drop[2]
            if drop[1] > HEIGHT or drop[0] < 0:
                drop[0] = random.uniform(0, WIDTH * 1.2)
                drop[1] = random.uniform(-30, -5)

    def draw_decals(self, screen, ox, oy):
        for (x, y, surf) in self.decals:
            sx, sy = world_to_screen(x, y)
            screen.blit(surf, (sx + ox - 15, sy + oy - 8))

    def draw_world(self, screen, ox, oy):
        for r in self.rings:
            sx, sy = world_to_screen(r[0], r[1])
            rad = r[2]
            pygame.draw.ellipse(screen, (200, 220, 255),
                                (sx + ox - rad * 16, sy + oy - rad * 8, rad * 32, rad * 16), 2)
        for p in self.parts:
            sx, sy = world_to_screen(p.x, p.y, p.z)
            a = max(0.0, min(1.0, p.life / p.total))
            c = (int(p.color[0] * a + 18 * (1 - a)), int(p.color[1] * a + 18 * (1 - a)),
                 int(p.color[2] * a + 22 * (1 - a)))
            pygame.draw.circle(screen, c, (int(sx + ox), int(sy + oy)), max(1, int(p.size * a + 0.5)))
        for n in self.numbers:
            sx, sy = world_to_screen(n[0], n[1], n[2])
            img = n[3]
            if n[4] < 0.3:
                img = img.copy()
                img.set_alpha(int(255 * n[4] / 0.3))
            screen.blit(img, (sx + ox - img.get_width() // 2, sy + oy))

    def draw_rain(self, screen):
        for x, y, s in self.rain:
            pygame.draw.line(screen, (80, 94, 116), (x, y), (x - s * 0.3, y + s), 1)
