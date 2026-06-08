import pygame
import math
from .constants import *


class Player:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - 16, y - 16, 32, 32)

        # Stats
        self.max_hp = 120
        self.hp = self.max_hp
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_regen = 0.6
        self.stamina_regen_delay = 0
        self.speed = 3.2
        self.runes = 0
        self.level = 1

        # Flasks
        self.max_flasks = 4
        self.flasks = self.max_flasks

        # Facing
        self.facing = pygame.math.Vector2(1, 0)

        # Attack state
        self.attack_timer = 0
        self.attack_cooldown = 0
        self.attack_hitbox = None
        self.attack_type = None  # 'light' or 'heavy'
        self.light_dmg = 22
        self.heavy_dmg = 48
        self.hit_enemies = set()

        # Roll state
        self.rolling = False
        self.roll_timer = 0
        self.roll_dir = pygame.math.Vector2(0, 0)
        self.roll_vel = pygame.math.Vector2(0, 0)
        self.iframes = 0

        # Parry state
        self.parrying = False
        self.parry_timer = 0
        self.parry_cooldown = 0

        # Block
        self.blocking = False

        # Damage state
        self.hurt_timer = 0
        self.dead = False
        self.death_timer = 0

        # Rune drop (on death)
        self.lost_runes = 0
        self.lost_rune_pos = None

        # Visual
        self.anim_timer = 0
        self.walk_frame = 0

        # Poise
        self.poise = 40
        self.max_poise = 40
        self.poise_damage = 0
        self.stagger_timer = 0

    def get_stamina_cost(self, action):
        costs = {'light': 18, 'heavy': 35, 'roll': 28, 'parry': 20, 'block': 6}
        return costs.get(action, 0)

    def use_stamina(self, amount):
        self.stamina = max(0, self.stamina - amount)
        self.stamina_regen_delay = 60

    def can_act(self):
        return (not self.rolling and self.attack_timer <= 0 and
                self.stagger_timer <= 0 and not self.dead and
                self.hurt_timer <= 10)

    def light_attack(self):
        if self.attack_cooldown > 0 or not self.can_act():
            return False
        if self.stamina < self.get_stamina_cost('light'):
            return False
        self.attack_type = 'light'
        self.attack_timer = 16
        self.attack_cooldown = 28
        self.hit_enemies = set()
        self.use_stamina(self.get_stamina_cost('light'))
        return True

    def heavy_attack(self):
        if self.attack_cooldown > 0 or not self.can_act():
            return False
        if self.stamina < self.get_stamina_cost('heavy'):
            return False
        self.attack_type = 'heavy'
        self.attack_timer = 24
        self.attack_cooldown = 45
        self.hit_enemies = set()
        self.use_stamina(self.get_stamina_cost('heavy'))
        return True

    def roll(self, move_dir):
        if not self.can_act():
            return False
        if self.stamina < self.get_stamina_cost('roll'):
            return False
        self.rolling = True
        self.roll_timer = ROLL_DURATION
        if move_dir.length() > 0:
            self.roll_dir = move_dir.normalize()
        else:
            self.roll_dir = self.facing.copy()
        self.iframes = IFRAMES_ON_ROLL
        self.use_stamina(self.get_stamina_cost('roll'))
        return True

    def parry(self):
        if self.parry_cooldown > 0 or not self.can_act():
            return False
        if self.stamina < self.get_stamina_cost('parry'):
            return False
        self.parrying = True
        self.parry_timer = PARRY_WINDOW + 8
        self.parry_cooldown = PARRY_COOLDOWN
        self.use_stamina(self.get_stamina_cost('parry'))
        return True

    def use_flask(self):
        if self.flasks <= 0 or self.hp >= self.max_hp or not self.can_act():
            return False
        self.flasks -= 1
        self.hp = min(self.max_hp, self.hp + 60)
        return True

    def take_damage(self, amount, knockback_dir=None):
        if self.iframes > 0 or self.dead:
            return False
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
        if self.attack_timer <= 0:
            return None
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
        if self.dead:
            return

        if self.stagger_timer > 0:
            self.stagger_timer -= 1
            return

        def k(key):
            try:
                return bool(keys[key])
            except (KeyError, IndexError):
                return False

        move = pygame.math.Vector2(0, 0)
        if k(pygame.K_w) or k(pygame.K_UP):
            move.y -= 1
        if k(pygame.K_s) or k(pygame.K_DOWN):
            move.y += 1
        if k(pygame.K_a) or k(pygame.K_LEFT):
            move.x -= 1
        if k(pygame.K_d) or k(pygame.K_RIGHT):
            move.x += 1

        self.blocking = (k(pygame.K_LSHIFT) and not self.rolling and
                         self.attack_timer <= 0 and self.stamina > 0)

        # Update timers
        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.parry_timer > 0:
            self.parry_timer -= 1
        else:
            self.parrying = False
        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
        if self.iframes > 0:
            self.iframes -= 1

        # Stamina regen
        if self.stamina_regen_delay > 0:
            self.stamina_regen_delay -= 1
        elif self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen)

        # Rolling movement
        if self.rolling:
            self.roll_timer -= 1
            progress = self.roll_timer / ROLL_DURATION
            speed = 7 * progress + 1
            self._move(self.roll_dir * speed, walls)
            if self.roll_timer <= 0:
                self.rolling = False
            return

        # Normal movement
        if move.length() > 0 and not self.blocking:
            move = move.normalize()
            self.facing = move.copy()
            spd = self.speed * (0.6 if self.attack_timer > 0 else 1.0)
            self._move(move * spd, walls)
            self.anim_timer += 1
            if self.anim_timer % 8 == 0:
                self.walk_frame = (self.walk_frame + 1) % 4

    def _move(self, delta, walls):
        self.pos.x += delta.x
        self.rect.centerx = int(self.pos.x)
        for w in walls:
            if self.rect.colliderect(w):
                if delta.x > 0:
                    self.rect.right = w.left
                elif delta.x < 0:
                    self.rect.left = w.right
                self.pos.x = self.rect.centerx

        self.pos.y += delta.y
        self.rect.centery = int(self.pos.y)
        for w in walls:
            if self.rect.colliderect(w):
                if delta.y > 0:
                    self.rect.bottom = w.top
                elif delta.y < 0:
                    self.rect.top = w.bottom
                self.pos.y = self.rect.centery

    def draw(self, surface, cam_ox, cam_oy):
        sx = int(self.pos.x - cam_ox)
        sy = int(self.pos.y - cam_oy)

        # Shadow
        pygame.draw.ellipse(surface, (20, 20, 20), (sx-14, sy+10, 28, 10))

        # Body color based on state
        if self.dead:
            color = (80, 60, 60)
        elif self.hurt_timer > 0:
            color = (240, 80, 80)
        elif self.rolling:
            color = (100, 180, 220)
        elif self.blocking:
            color = (160, 160, 200)
        elif self.parrying:
            color = (240, 220, 80)
        elif self.attack_timer > 0:
            color = (220, 180, 80)
        else:
            color = (180, 160, 120)

        # Cloak/body
        pygame.draw.rect(surface, (40, 35, 30), (sx-14, sy-14, 28, 28), border_radius=4)
        pygame.draw.rect(surface, color, (sx-12, sy-12, 24, 24), border_radius=4)

        # Hood
        pygame.draw.circle(surface, (60, 50, 40), (sx, sy-8), 11)
        pygame.draw.circle(surface, (100, 85, 70), (sx, sy-9), 9)

        # Eyes
        ex = sx + int(self.facing.x * 4)
        ey = sy - 9 + int(self.facing.y * 3)
        pygame.draw.circle(surface, (240, 200, 80), (ex-3, ey), 2)
        pygame.draw.circle(surface, (240, 200, 80), (ex+3, ey), 2)

        # Sword (show when attacking)
        if self.attack_timer > 0:
            progress = self.attack_timer / (16 if self.attack_type == 'light' else 24)
            swing = math.sin(progress * math.pi) * 20
            wx = sx + int(self.facing.x * 30 - self.facing.y * swing)
            wy = sy + int(self.facing.y * 30 + self.facing.x * swing)
            sword_color = (220, 220, 240) if self.attack_type == 'light' else (240, 160, 40)
            pygame.draw.line(surface, sword_color, (sx, sy), (wx, wy), 4)
            pygame.draw.circle(surface, sword_color, (wx, wy), 5)

        # Shield (show when blocking or parrying)
        if self.blocking or self.parrying:
            shield_x = sx - int(self.facing.x * 20) + int(self.facing.y * 18)
            shield_y = sy - int(self.facing.y * 20) - int(self.facing.x * 18)
            sc = (200, 200, 240) if self.parrying else (140, 140, 180)
            pygame.draw.circle(surface, sc, (shield_x, shield_y), 10)
            pygame.draw.circle(surface, WHITE, (shield_x, shield_y), 10, 2)

        # I-frame indicator
        if self.iframes > 0:
            alpha_val = int(128 * self.iframes / IFRAMES_ON_ROLL)
            pygame.draw.circle(surface, (100, 200, 255), (sx, sy), 20, 2)
