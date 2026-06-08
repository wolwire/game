import pygame
import random
import math


class Particle:
    def __init__(self, x, y, color, vel_x=None, vel_y=None, size=4, life=30):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vel_x if vel_x is not None else random.uniform(-3, 3)
        self.vy = vel_y if vel_y is not None else random.uniform(-3, 3)
        self.size = size
        self.max_life = life
        self.life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.life -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        alpha = self.life / self.max_life
        r = max(1, int(self.size * alpha))
        sx = int(self.x - offset_x)
        sy = int(self.y - offset_y)
        c = tuple(int(ch * alpha) for ch in self.color[:3])
        pygame.draw.circle(surface, c, (sx, sy), r)

    @property
    def dead(self):
        return self.life <= 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_hit(self, x, y, color=(255, 200, 50), count=12):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 5)
            self.particles.append(Particle(
                x, y, color,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(3, 6),
                life=random.randint(15, 30)
            ))

    def emit_blood(self, x, y, count=8):
        for _ in range(count):
            angle = random.uniform(-math.pi, 0)
            speed = random.uniform(1, 4)
            self.particles.append(Particle(
                x, y, (180, 20, 20),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(2, 5),
                life=random.randint(20, 40)
            ))

    def emit_death(self, x, y, color=(200, 180, 50), count=30):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 6)
            self.particles.append(Particle(
                x, y, color,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(4, 10),
                life=random.randint(30, 70)
            ))

    def emit_parry(self, x, y):
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 8)
            self.particles.append(Particle(
                x, y, (255, 255, 180),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                size=random.randint(4, 8),
                life=random.randint(20, 35)
            ))

    def emit_grace(self, x, y):
        for _ in range(3):
            self.particles.append(Particle(
                x, y, (212, 175, 55),
                random.uniform(-0.5, 0.5),
                random.uniform(-3, -1),
                size=random.randint(2, 4),
                life=random.randint(30, 50)
            ))

    def update(self):
        self.particles = [p for p in self.particles if not p.dead]
        for p in self.particles:
            p.update()

    def draw(self, surface, cam_offset_x=0, cam_offset_y=0):
        for p in self.particles:
            p.draw(surface, cam_offset_x, cam_offset_y)
