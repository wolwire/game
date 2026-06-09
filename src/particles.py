import pygame
import math
import random


# --- Glow helper ---
def draw_glow(surface, cx, cy, radius, color, alpha=80):
    s = pygame.Surface((radius*2+2, radius*2+2), pygame.SRCALPHA)
    for r in range(radius, 0, -max(1, radius//6)):
        a = int(alpha * (1 - r/radius) ** 1.4)
        pygame.draw.circle(s, (*color[:3], a), (radius+1, radius+1), r)
    surface.blit(s, (cx - radius - 1, cy - radius - 1))


def draw_glow_line(surface, p1, p2, color, width=3, alpha=120):
    s = pygame.Surface((abs(p2[0]-p1[0])+width*4+2, abs(p2[1]-p1[1])+width*4+2), pygame.SRCALPHA)
    ox = min(p1[0], p2[0]) - width*2
    oy = min(p1[1], p2[1]) - width*2
    for w in range(width+4, 0, -1):
        a = int(alpha * (1 - w/(width+4))**1.5)
        pygame.draw.line(s, (*color[:3], a),
                         (p1[0]-ox, p1[1]-oy), (p2[0]-ox, p2[1]-oy), w)
    surface.blit(s, (ox, oy))


class Particle:
    def __init__(self, x, y, color, vel_x=None, vel_y=None, size=4, life=30, glow=False):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vel_x if vel_x is not None else random.uniform(-3, 3)
        self.vy = vel_y if vel_y is not None else random.uniform(-3, 3)
        self.size = size
        self.max_life = life
        self.life = life
        self.glow = glow

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.90
        self.vy *= 0.90
        self.vy += 0.04  # slight gravity
        self.life -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        alpha = self.life / self.max_life
        r = max(1, int(self.size * alpha))
        sx = int(self.x - offset_x)
        sy = int(self.y - offset_y)
        c = tuple(int(ch * alpha) for ch in self.color[:3])
        if self.glow and r > 1:
            draw_glow(surface, sx, sy, r*3, self.color[:3], int(100*alpha))
        pygame.draw.circle(surface, c, (sx, sy), r)

    @property
    def dead(self):
        return self.life <= 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_hit(self, x, y, color=(255, 200, 50), count=14):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 6)
            self.particles.append(Particle(
                x, y, color,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(3, 7),
                life=random.randint(18, 35),
                glow=True
            ))
        # Sparks
        for _ in range(6):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(4, 10)
            self.particles.append(Particle(
                x, y, (255, 255, 220),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=2, life=random.randint(8, 16), glow=False
            ))

    def emit_blood(self, x, y, count=10):
        for _ in range(count):
            angle = random.uniform(-math.pi*0.8, -math.pi*0.2) + random.uniform(-0.5, 0.5)
            speed = random.uniform(1, 5)
            self.particles.append(Particle(
                x, y, random.choice([(180,20,20),(200,40,30),(160,10,10)]),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(2, 6),
                life=random.randint(22, 45)
            ))

    def emit_death(self, x, y, color=(200, 180, 50), count=35):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 7)
            self.particles.append(Particle(
                x, y, color,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(4, 12),
                life=random.randint(35, 80),
                glow=True
            ))

    def emit_parry(self, x, y):
        for _ in range(28):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(4, 10)
            self.particles.append(Particle(
                x, y, random.choice([(255,255,180),(255,230,80),(255,255,255)]),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(3, 9),
                life=random.randint(20, 40),
                glow=True
            ))

    def emit_grace(self, x, y):
        for _ in range(4):
            self.particles.append(Particle(
                x + random.uniform(-8, 8),
                y + random.uniform(-5, 5),
                random.choice([(212,175,55),(240,210,80),(255,230,120)]),
                random.uniform(-0.6, 0.6),
                random.uniform(-3.5, -1.5),
                size=random.randint(2, 5),
                life=random.randint(30, 55),
                glow=True
            ))

    def emit_roll_dust(self, x, y):
        for _ in range(4):
            self.particles.append(Particle(
                x, y, (140, 130, 110),
                random.uniform(-2, 2), random.uniform(-1, 0.5),
                size=random.randint(3, 6), life=random.randint(12, 22)
            ))

    def update(self):
        self.particles = [p for p in self.particles if not p.dead]
        for p in self.particles:
            p.update()

    def draw(self, surface, cam_offset_x=0, cam_offset_y=0):
        for p in self.particles:
            p.draw(surface, cam_offset_x, cam_offset_y)
