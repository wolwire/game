import pygame
import math
import random
from .constants import *
from .particles import draw_glow


class Player:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - 16, y - 16, 32, 32)

        self.max_hp = 120
        self.hp = self.max_hp
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_regen = 0.6
        self.stamina_regen_delay = 0
        self.speed = 3.2
        self.runes = 0
        self.level = 1

        self.max_flasks = 4
        self.flasks = self.max_flasks

        self.facing = pygame.math.Vector2(1, 0)

        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_hitbox = None
        self.attack_type = None
        self.light_dmg = 22
        self.heavy_dmg = 48
        self.hit_enemies = set()

        self.rolling = False
        self.roll_timer = 0
        self.roll_dir = pygame.math.Vector2(0, 0)
        self.roll_vel = pygame.math.Vector2(0, 0)
        self.iframes = 0

        self.parrying = False
        self.parry_timer = 0
        self.parry_cooldown = 0

        self.blocking = False

        self.hurt_timer = 0
        self.dead = False
        self.death_timer = 0

        self.lost_runes = 0
        self.lost_rune_pos = None

        self.anim_timer = 0
        self.walk_frame = 0
        self.bob = 0.0

        self.poise = 40
        self.max_poise = 40
        self.poise_damage = 0
        self.stagger_timer = 0

        # Sword trail
        self.trail = []

    def get_stamina_cost(self, action):
        return {'light': 18, 'heavy': 35, 'roll': 28, 'parry': 20, 'block': 6}.get(action, 0)

    def use_stamina(self, amount):
        self.stamina = max(0, self.stamina - amount)
        self.stamina_regen_delay = 60

    def can_act(self):
        return (not self.rolling and self.attack_timer <= 0 and
                self.stagger_timer <= 0 and not self.dead and
                self.hurt_timer <= 10)

    def light_attack(self):
        if self.attack_cooldown > 0 or not self.can_act(): return False
        if self.stamina < self.get_stamina_cost('light'): return False
        self.attack_type = 'light'
        self.attack_timer = 16
        self.attack_cooldown = 28
        self.hit_enemies = set()
        self.use_stamina(self.get_stamina_cost('light'))
        self.trail = []
        return True

    def heavy_attack(self):
        if self.attack_cooldown > 0 or not self.can_act(): return False
        if self.stamina < self.get_stamina_cost('heavy'): return False
        self.attack_type = 'heavy'
        self.attack_timer = 24
        self.attack_cooldown = 45
        self.hit_enemies = set()
        self.use_stamina(self.get_stamina_cost('heavy'))
        self.trail = []
        return True

    def roll(self, move_dir):
        if not self.can_act(): return False
        if self.stamina < self.get_stamina_cost('roll'): return False
        self.rolling = True
        self.roll_timer = ROLL_DURATION
        self.roll_dir = move_dir.normalize() if move_dir.length() > 0 else self.facing.copy()
        self.iframes = IFRAMES_ON_ROLL
        self.use_stamina(self.get_stamina_cost('roll'))
        return True

    def parry(self):
        if self.parry_cooldown > 0 or not self.can_act(): return False
        if self.stamina < self.get_stamina_cost('parry'): return False
        self.parrying = True
        self.parry_timer = PARRY_WINDOW + 8
        self.parry_cooldown = PARRY_COOLDOWN
        self.use_stamina(self.get_stamina_cost('parry'))
        return True

    def use_flask(self):
        if self.flasks <= 0 or self.hp >= self.max_hp or not self.can_act(): return False
        self.flasks -= 1
        self.hp = min(self.max_hp, self.hp + 60)
        return True

    def take_damage(self, amount, knockback_dir=None):
        if self.iframes > 0 or self.dead: return False
        if self.blocking:
            amount = int(amount * 0.3)
            self.use_stamina(amount * 0.5)
        self.hp -= amount
        self.hurt_timer = 20
        self.poise_damage += amount
        if self.poise_damage >= self.poise:
            self.stagger_timer = STAGGER_DURATION
            self.poise_damage = 0
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
            self.lost_runes = self.runes
            self.lost_rune_pos = (self.pos.x, self.pos.y)
            self.runes = 0
        return True

    def get_attack_hitbox(self):
        if self.attack_timer <= 0: return None
        active_start = 6 if self.attack_type == 'light' else 12
        active_end = active_start + (8 if self.attack_type == 'light' else 12)
        elapsed = (16 if self.attack_type == 'light' else 24) - self.attack_timer
        if active_start <= elapsed <= active_end:
            reach = 48 if self.attack_type == 'light' else 60
            cx = self.pos.x + self.facing.x * reach
            cy = self.pos.y + self.facing.y * reach
            size = 44 if self.attack_type == 'light' else 56
            return pygame.Rect(cx - size//2, cy - size//2, size, size)
        return None

    def get_parry_active(self):
        elapsed = (PARRY_WINDOW + 8) - self.parry_timer
        return self.parrying and 2 <= elapsed <= PARRY_WINDOW

    def update(self, keys, walls, dt=1.0):
        if self.dead: return
        if self.stagger_timer > 0:
            self.stagger_timer -= 1
            return

        def k(key):
            try: return bool(keys[key])
            except (KeyError, IndexError): return False

        move = pygame.math.Vector2(0, 0)
        if k(pygame.K_w) or k(pygame.K_UP):    move.y -= 1
        if k(pygame.K_s) or k(pygame.K_DOWN):  move.y += 1
        if k(pygame.K_a) or k(pygame.K_LEFT):  move.x -= 1
        if k(pygame.K_d) or k(pygame.K_RIGHT): move.x += 1

        self.blocking = (k(pygame.K_LSHIFT) and not self.rolling and
                         self.attack_timer <= 0 and self.stamina > 0)

        if self.attack_timer > 0: self.attack_timer -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        if self.parry_timer > 0: self.parry_timer -= 1
        else: self.parrying = False
        if self.parry_cooldown > 0: self.parry_cooldown -= 1
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.iframes > 0: self.iframes -= 1

        if self.stamina_regen_delay > 0:
            self.stamina_regen_delay -= 1
        elif self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen)

        if self.rolling:
            self.roll_timer -= 1
            progress = self.roll_timer / ROLL_DURATION
            speed = 7 * progress + 1
            self._move(self.roll_dir * speed, walls)
            if self.roll_timer <= 0:
                self.rolling = False
            return

        if move.length() > 0 and not self.blocking:
            move = move.normalize()
            self.facing = move.copy()
            spd = self.speed * (0.6 if self.attack_timer > 0 else 1.0)
            self._move(move * spd, walls)
            self.anim_timer += 1
            self.bob = math.sin(self.anim_timer * 0.4) * 2.5
            if self.anim_timer % 8 == 0:
                self.walk_frame = (self.walk_frame + 1) % 4
        else:
            self.bob *= 0.7

        # Sword trail
        if self.attack_timer > 0:
            reach = 48 if self.attack_type == 'light' else 64
            tip = (self.pos.x + self.facing.x * reach,
                   self.pos.y + self.facing.y * reach)
            self.trail.append(tip)
            if len(self.trail) > 10:
                self.trail.pop(0)
        else:
            if self.trail:
                self.trail.pop(0)

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
        sy = int(self.pos.y - cam_oy + self.bob)

        # Shadow
        shadow = pygame.Surface((36, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, 36, 14))
        surface.blit(shadow, (sx - 18, sy + 12))

        # I-frame aura
        if self.iframes > 0:
            draw_glow(surface, sx, sy, 28, (80, 180, 255),
                      int(120 * self.iframes / IFRAMES_ON_ROLL))

        # Sword trail
        if len(self.trail) >= 2:
            for i in range(1, len(self.trail)):
                alpha = int(180 * i / len(self.trail))
                p1 = (int(self.trail[i-1][0] - cam_ox), int(self.trail[i-1][1] - cam_oy))
                p2 = (int(self.trail[i][0] - cam_ox), int(self.trail[i][1] - cam_oy))
                tc = (220, 200, 255) if self.attack_type == 'light' else (255, 160, 40)
                ts = pygame.Surface((abs(p2[0]-p1[0])+12, abs(p2[1]-p1[1])+12), pygame.SRCALPHA)
                ox2 = min(p1[0],p2[0])-6
                oy2 = min(p1[1],p2[1])-6
                pygame.draw.line(ts, (*tc, alpha),
                                 (p1[0]-ox2, p1[1]-oy2), (p2[0]-ox2, p2[1]-oy2), 4)
                surface.blit(ts, (ox2, oy2))

        if self.dead:
            # Fallen figure
            pygame.draw.ellipse(surface, (60, 50, 45), (sx-18, sy-6, 36, 18))
            pygame.draw.ellipse(surface, (80, 65, 55), (sx-16, sy-4, 32, 14))
            return

        # Cloak base (dark outer)
        cloak_color = (35, 30, 25)
        if self.hurt_timer > 0:
            cloak_color = (120, 30, 30)
        pygame.draw.rect(surface, cloak_color, (sx-15, sy-14, 30, 30), border_radius=5)

        # Armor inner
        if self.rolling:
            armor = (80, 160, 210)
        elif self.blocking:
            armor = (120, 120, 160)
        elif self.parrying:
            armor = (240, 220, 60)
            draw_glow(surface, sx, sy, 24, (255, 240, 80), 100)
        elif self.attack_timer > 0:
            t = self.attack_timer / (16 if self.attack_type == 'light' else 24)
            armor = (int(180 + 60*t), int(160 + 40*t), int(80 + 20*t))
        else:
            armor = (130, 118, 95)

        pygame.draw.rect(surface, armor, (sx-13, sy-12, 26, 26), border_radius=4)

        # Chest plate highlight
        pygame.draw.rect(surface, tuple(min(255,c+40) for c in armor),
                         (sx-8, sy-10, 16, 10), border_radius=2)

        # Belt
        pygame.draw.rect(surface, (60, 50, 35), (sx-13, sy+2, 26, 5))
        pygame.draw.rect(surface, (90, 75, 45), (sx-2, sy+3, 4, 3))

        # Hood/helm
        hood = (55, 48, 38)
        pygame.draw.circle(surface, hood, (sx, sy-14), 13)
        pygame.draw.circle(surface, (80, 68, 52), (sx, sy-15), 11)

        # Visor slit
        vx = sx + int(self.facing.x * 5)
        vy = sy - 15 + int(self.facing.y * 3)

        # Eyes glow
        eye_color = (255, 200, 60)
        if self.parrying:
            eye_color = (255, 255, 100)
            draw_glow(surface, vx-3, vy, 8, eye_color, 160)
            draw_glow(surface, vx+3, vy, 8, eye_color, 160)
        elif self.attack_timer > 0:
            eye_color = (255, 140, 40)
        elif self.hurt_timer > 0:
            eye_color = (255, 80, 80)

        pygame.draw.circle(surface, eye_color, (vx-3, vy), 2)
        pygame.draw.circle(surface, eye_color, (vx+3, vy), 2)
        draw_glow(surface, vx-3, vy, 6, eye_color, 80)
        draw_glow(surface, vx+3, vy, 6, eye_color, 80)

        # Pauldrons (shoulder guards)
        pygame.draw.ellipse(surface, (100, 90, 70), (sx-16, sy-12, 10, 8))
        pygame.draw.ellipse(surface, (100, 90, 70), (sx+6, sy-12, 10, 8))

        # Sword
        if self.attack_timer > 0:
            progress = self.attack_timer / (16 if self.attack_type == 'light' else 24)
            swing = math.sin(progress * math.pi)
            ang = math.atan2(self.facing.y, self.facing.x)
            arc = math.pi * 0.7 if self.attack_type == 'light' else math.pi
            a = ang - arc * 0.5 + arc * (1 - progress)
            blade_len = 40 if self.attack_type == 'light' else 52
            wx = int(sx + math.cos(a) * blade_len)
            wy = int(sy + math.sin(a) * blade_len)
            blade_color = (200, 215, 240) if self.attack_type == 'light' else (240, 160, 40)
            # Blade glow
            draw_glow(surface, (sx+wx)//2, (sy+wy)//2, 14, blade_color, int(100*swing))
            pygame.draw.line(surface, (80, 80, 100), (sx, sy), (wx, wy), 5)
            pygame.draw.line(surface, blade_color, (sx, sy), (wx, wy), 3)
            pygame.draw.circle(surface, (255, 240, 200), (wx, wy), 4)
        else:
            # Resting sword on back
            bx = sx - int(self.facing.y * 8)
            by = sy + int(self.facing.x * 8)
            ex2 = bx + int(self.facing.y * 22)
            ey2 = by - int(self.facing.x * 22)
            pygame.draw.line(surface, (80, 80, 95), (bx, by), (ex2, ey2), 3)
            pygame.draw.line(surface, (160, 170, 190), (bx, by), (ex2, ey2), 2)

        # Shield (blocking/parrying)
        if self.blocking or self.parrying:
            sx2 = sx - int(self.facing.x * 18) + int(self.facing.y * 16)
            sy2b = sy - int(self.facing.y * 18) - int(self.facing.x * 16)
            sc_outer = (60, 60, 90)
            sc_inner = (140, 150, 200) if self.parrying else (100, 110, 150)
            pygame.draw.circle(surface, sc_outer, (sx2, sy2b), 13)
            pygame.draw.circle(surface, sc_inner, (sx2, sy2b), 11)
            pygame.draw.circle(surface, (200, 210, 255), (sx2, sy2b), 11, 2)
            pygame.draw.circle(surface, (220, 230, 255), (sx2-2, sy2b-2), 4)
            if self.parrying:
                draw_glow(surface, sx2, sy2b, 20, (255, 240, 80), 150)
