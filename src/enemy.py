import pygame
import math
import random
from .constants import *


class Enemy:
    def __init__(self, x, y, etype='soldier'):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - 18, y - 18, 36, 36)
        self.etype = etype
        self.facing = pygame.math.Vector2(1, 0)
        self.dead = False
        self.death_timer = 40
        self.hurt_timer = 0
        self.stagger_timer = 0

        cfg = {
            'soldier': dict(hp=60, speed=1.6, dmg=18, atk_range=52, atk_wind=30, atk_active=10, atk_cd=80, aggro=240, runes=40, poise=20, color=(100,120,80)),
            'knight':  dict(hp=140, speed=1.3, dmg=30, atk_range=58, atk_wind=45, atk_active=12, atk_cd=90, aggro=280, runes=120, poise=50, color=(80,80,110)),
            'archer':  dict(hp=50, speed=1.4, dmg=16, atk_range=220, atk_wind=50, atk_active=8, atk_cd=100, aggro=260, runes=60, poise=10, color=(90,80,60)),
            'brute':   dict(hp=200, speed=1.0, dmg=45, atk_range=65, atk_wind=55, atk_active=16, atk_cd=110, aggro=200, runes=200, poise=80, color=(110,60,50)),
        }
        c = cfg.get(etype, cfg['soldier'])
        self.max_hp = c['hp']
        self.hp = self.max_hp
        self.speed = c['speed']
        self.dmg = c['dmg']
        self.atk_range = c['atk_range']
        self.atk_wind = c['atk_wind']
        self.atk_active = c['atk_active']
        self.atk_cd = c['atk_cd']
        self.aggro_range = c['aggro']
        self.rune_reward = c['runes']
        self.poise = c['poise']
        self.max_poise = c['poise']
        self.color = c['color']

        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_hitbox = None
        self.state = 'patrol'
        self.patrol_target = pygame.math.Vector2(x + random.randint(-80,80), y + random.randint(-80,80))
        self.patrol_timer = random.randint(60, 180)

        self.iframes = 0

    def take_damage(self, amount, stagger=False):
        if self.dead or self.iframes > 0:
            return False
        self.hp -= amount
        self.hurt_timer = 14
        self.iframes = 6
        if stagger or amount >= self.max_poise * 0.4:
            self.stagger_timer = STAGGER_DURATION
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
        return True

    def get_attack_hitbox(self):
        if self.attack_timer <= 0:
            return None
        wind_done = self.atk_wind
        active_end = wind_done + self.atk_active
        elapsed = (self.atk_wind + self.atk_active + 10) - self.attack_timer
        if wind_done <= elapsed <= active_end:
            cx = self.pos.x + self.facing.x * (self.atk_range * 0.7)
            cy = self.pos.y + self.facing.y * (self.atk_range * 0.7)
            size = 40 if self.etype != 'brute' else 55
            return pygame.Rect(cx - size//2, cy - size//2, size, size)
        return None

    def is_winding_up(self):
        if self.attack_timer <= 0:
            return False
        elapsed = (self.atk_wind + self.atk_active + 10) - self.attack_timer
        return elapsed < self.atk_wind

    def update(self, player, walls):
        if self.dead:
            self.death_timer -= 1
            return
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
        if self.iframes > 0:
            self.iframes -= 1
        if self.stagger_timer > 0:
            self.stagger_timer -= 1
            return

        dist = self.pos.distance_to(player.pos)
        diff = player.pos - self.pos

        # State machine
        if dist < self.aggro_range:
            self.state = 'chase'
        elif self.state == 'chase' and dist > self.aggro_range * 1.4:
            self.state = 'patrol'

        if self.attack_timer > 0:
            self.attack_timer -= 1
            # Face player during wind-up
            if diff.length() > 0:
                self.facing = diff.normalize()
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == 'chase':
            if diff.length() > 0:
                self.facing = diff.normalize()

            if dist <= self.atk_range and self.attack_cooldown <= 0:
                self.attack_timer = self.atk_wind + self.atk_active + 10
                self.attack_cooldown = self.atk_cd
            elif dist > self.atk_range:
                self._move(self.facing * self.speed, walls)
        else:
            # Patrol
            self.patrol_timer -= 1
            if self.patrol_timer <= 0 or self.pos.distance_to(self.patrol_target) < 10:
                self.patrol_target = self.pos + pygame.math.Vector2(
                    random.randint(-80, 80), random.randint(-80, 80))
                self.patrol_timer = random.randint(60, 180)
            pt_diff = self.patrol_target - self.pos
            if pt_diff.length() > 2:
                self.facing = pt_diff.normalize()
                self._move(self.facing * self.speed * 0.4, walls)

    def _move(self, delta, walls):
        self.pos.x += delta.x
        self.rect.centerx = int(self.pos.x)
        for w in walls:
            if self.rect.colliderect(w):
                if delta.x > 0: self.rect.right = w.left
                else: self.rect.left = w.right
                self.pos.x = self.rect.centerx
        self.pos.y += delta.y
        self.rect.centery = int(self.pos.y)
        for w in walls:
            if self.rect.colliderect(w):
                if delta.y > 0: self.rect.bottom = w.top
                else: self.rect.top = w.bottom
            self.pos.y = self.rect.centery

    def draw(self, surface, cam_ox, cam_oy):
        sx = int(self.pos.x - cam_ox)
        sy = int(self.pos.y - cam_oy)

        if self.dead:
            if self.death_timer > 0:
                alpha = self.death_timer / 40
                c = tuple(int(ch * alpha * 0.4) for ch in self.color)
                pygame.draw.ellipse(surface, c, (sx-14, sy-6, 28, 14))
            return

        # Shadow
        pygame.draw.ellipse(surface, (20, 20, 20), (sx-16, sy+10, 32, 10))

        color = (220, 80, 80) if self.hurt_timer > 0 else self.color
        if self.is_winding_up():
            # Flash orange during wind-up (telegraph)
            flash = (220, 160, 40)
            color = flash

        # Body
        if self.etype == 'brute':
            pygame.draw.rect(surface, (50, 30, 20), (sx-20, sy-20, 40, 40), border_radius=3)
            pygame.draw.rect(surface, color, (sx-18, sy-18, 36, 36), border_radius=3)
        elif self.etype == 'knight':
            pygame.draw.rect(surface, (30, 30, 50), (sx-16, sy-16, 32, 32), border_radius=2)
            pygame.draw.rect(surface, color, (sx-14, sy-14, 28, 28), border_radius=2)
        else:
            pygame.draw.rect(surface, (30, 40, 20), (sx-14, sy-14, 28, 28), border_radius=4)
            pygame.draw.rect(surface, color, (sx-12, sy-12, 24, 24), border_radius=4)

        # Head
        pygame.draw.circle(surface, tuple(min(255,c+30) for c in color), (sx, sy-6), 9)

        # Eyes
        pygame.draw.circle(surface, RED, (sx + int(self.facing.x*4)-2, sy-7), 2)
        pygame.draw.circle(surface, RED, (sx + int(self.facing.x*4)+2, sy-7), 2)

        # Wind-up indicator bar
        if self.is_winding_up():
            elapsed = (self.atk_wind + self.atk_active + 10) - self.attack_timer
            prog = elapsed / self.atk_wind
            bar_w = 36
            bar_x = sx - bar_w // 2
            bar_y = sy - 30
            pygame.draw.rect(surface, (60, 20, 20), (bar_x, bar_y, bar_w, 6))
            pygame.draw.rect(surface, ORANGE, (bar_x, bar_y, int(bar_w * prog), 6))

        # HP bar above enemy
        bar_w = 36
        bar_x = sx - bar_w // 2
        bar_y = sy - 40
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_w, 5))
        pygame.draw.rect(surface, (180, 50, 50), (bar_x, bar_y, int(bar_w * self.hp / self.max_hp), 5))
