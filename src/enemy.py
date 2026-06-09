import pygame
import math
import random
from .constants import *
from .particles import draw_glow


class Enemy:
    def __init__(self, x, y, etype='soldier'):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - 18, y - 18, 36, 36)
        self.etype = etype
        self.facing = pygame.math.Vector2(1, 0)
        self.dead = False
        self.death_timer = 50
        self.hurt_timer = 0
        self.stagger_timer = 0
        self.anim = random.randint(0, 60)

        cfg = {
            'soldier': dict(hp=60,  speed=1.6, dmg=18, atk_range=52,  atk_wind=30, atk_active=10, atk_cd=80,  aggro=240, runes=40,  poise=20, size=18),
            'knight':  dict(hp=140, speed=1.3, dmg=30, atk_range=58,  atk_wind=45, atk_active=12, atk_cd=90,  aggro=280, runes=120, poise=50, size=20),
            'archer':  dict(hp=50,  speed=1.4, dmg=16, atk_range=220, atk_wind=50, atk_active=8,  atk_cd=100, aggro=260, runes=60,  poise=10, size=16),
            'brute':   dict(hp=200, speed=1.0, dmg=45, atk_range=65,  atk_wind=55, atk_active=16, atk_cd=110, aggro=200, runes=200, poise=80, size=24),
        }
        c = cfg.get(etype, cfg['soldier'])
        self.max_hp = c['hp']
        self.hp     = self.max_hp
        self.speed  = c['speed']
        self.dmg    = c['dmg']
        self.atk_range    = c['atk_range']
        self.atk_wind     = c['atk_wind']
        self.atk_active   = c['atk_active']
        self.atk_cd       = c['atk_cd']
        self.aggro_range  = c['aggro']
        self.rune_reward  = c['runes']
        self.poise        = c['poise']
        self.max_poise    = c['poise']
        self.size         = c['size']

        self.attack_timer   = 0
        self.attack_cooldown = 0
        self.state = 'patrol'
        self.patrol_target  = pygame.math.Vector2(x + random.randint(-80,80), y + random.randint(-80,80))
        self.patrol_timer   = random.randint(60, 180)
        self.iframes = 0

    def take_damage(self, amount, stagger=False):
        if self.dead or self.iframes > 0: return False
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
        if self.attack_timer <= 0: return None
        elapsed = (self.atk_wind + self.atk_active + 10) - self.attack_timer
        if self.atk_wind <= elapsed <= self.atk_wind + self.atk_active:
            cx = self.pos.x + self.facing.x * (self.atk_range * 0.7)
            cy = self.pos.y + self.facing.y * (self.atk_range * 0.7)
            size = 40 if self.etype != 'brute' else 55
            return pygame.Rect(cx - size//2, cy - size//2, size, size)
        return None

    def is_winding_up(self):
        if self.attack_timer <= 0: return False
        elapsed = (self.atk_wind + self.atk_active + 10) - self.attack_timer
        return elapsed < self.atk_wind

    def update(self, player, walls):
        if self.dead:
            self.death_timer -= 1
            return
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.iframes > 0: self.iframes -= 1
        if self.stagger_timer > 0:
            self.stagger_timer -= 1
            return

        self.anim = (self.anim + 1) % 120
        diff = player.pos - self.pos
        dist = self.pos.distance_to(player.pos)

        if dist < self.aggro_range: self.state = 'chase'
        elif self.state == 'chase' and dist > self.aggro_range * 1.4: self.state = 'patrol'

        if self.attack_timer > 0:
            self.attack_timer -= 1
            if diff.length() > 0: self.facing = diff.normalize()
            return

        if self.attack_cooldown > 0: self.attack_cooldown -= 1

        if self.state == 'chase':
            if diff.length() > 0: self.facing = diff.normalize()
            if dist <= self.atk_range and self.attack_cooldown <= 0:
                self.attack_timer = self.atk_wind + self.atk_active + 10
                self.attack_cooldown = self.atk_cd
            elif dist > self.atk_range:
                self._move(self.facing * self.speed, walls)
        else:
            self.patrol_timer -= 1
            if self.patrol_timer <= 0 or self.pos.distance_to(self.patrol_target) < 10:
                self.patrol_target = self.pos + pygame.math.Vector2(random.randint(-80,80), random.randint(-80,80))
                self.patrol_timer = random.randint(60, 180)
            pt = self.patrol_target - self.pos
            if pt.length() > 2:
                self.facing = pt.normalize()
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
                a = self.death_timer / 50
                pygame.draw.ellipse(surface, (int(50*a), int(35*a), int(25*a)),
                                    (sx-int(self.size*a), sy-int(self.size*0.4*a),
                                     int(self.size*2*a), int(self.size*0.8*a)))
            return

        # Shadow
        shadow = pygame.Surface((self.size*3, self.size), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0,0,0,80), (0,0,self.size*3, self.size))
        surface.blit(shadow, (sx - self.size*3//2, sy + self.size - 2))

        wind_up = self.is_winding_up()
        wu_prog = 0.0
        if wind_up:
            total = self.atk_wind + self.atk_active + 10
            elapsed = total - self.attack_timer
            wu_prog = min(1.0, elapsed / self.atk_wind)

        if self.etype == 'soldier':
            self._draw_soldier(surface, sx, sy, wind_up, wu_prog)
        elif self.etype == 'knight':
            self._draw_knight(surface, sx, sy, wind_up, wu_prog)
        elif self.etype == 'archer':
            self._draw_archer(surface, sx, sy, wind_up, wu_prog)
        elif self.etype == 'brute':
            self._draw_brute(surface, sx, sy, wind_up, wu_prog)

        # HP bar
        if self.hp < self.max_hp:
            bar_w = self.size * 2 + 8
            bx = sx - bar_w//2
            by = sy - self.size - 16
            pygame.draw.rect(surface, (30,10,10), (bx, by, bar_w, 5))
            pygame.draw.rect(surface, (180,40,40), (bx, by, int(bar_w * self.hp / self.max_hp), 5))
            pygame.draw.rect(surface, (80,20,20), (bx, by, bar_w, 5), 1)

        # Wind-up warning bar
        if wind_up:
            bar_w = self.size * 2 + 8
            bx = sx - bar_w//2
            by = sy - self.size - 24
            pygame.draw.rect(surface, (60,20,0), (bx, by, bar_w, 5))
            pygame.draw.rect(surface, (255, int(180 - 140*wu_prog), 0),
                             (bx, by, int(bar_w * wu_prog), 5))

    def _draw_soldier(self, surface, sx, sy, wind_up, wu_prog):
        hurt = self.hurt_timer > 0
        # Rusty armor
        body_c = (160, 80, 60) if hurt else ((200, 140, 60) if wind_up else (110, 85, 55))
        pygame.draw.rect(surface, (40,30,20), (sx-15, sy-15, 30, 28), border_radius=3)
        pygame.draw.rect(surface, body_c, (sx-13, sy-13, 26, 24), border_radius=3)
        # Rust patches
        if not hurt:
            pygame.draw.rect(surface, (90,60,35), (sx-6, sy-8, 5, 7), border_radius=1)
            pygame.draw.rect(surface, (90,60,35), (sx+3, sy-2, 4, 5), border_radius=1)
        # Helmet
        helm = (150,120,80) if wind_up else (80,65,45)
        pygame.draw.circle(surface, (30,20,12), (sx, sy-16), 12)
        pygame.draw.circle(surface, helm, (sx, sy-17), 10)
        pygame.draw.rect(surface, helm, (sx-8, sy-17, 16, 6))
        # Eyes
        ec = (255,160,40) if wind_up else (200,80,40)
        pygame.draw.circle(surface, ec, (sx-3, sy-17), 2)
        pygame.draw.circle(surface, ec, (sx+3, sy-17), 2)
        # Sword
        wcolor = (180,160,130) if not wind_up else (240,180,60)
        wx = sx + int(self.facing.x * 24)
        wy = sy + int(self.facing.y * 24)
        if wind_up:
            draw_glow(surface, wx, wy, 12, (255,200,40), int(80*wu_prog))
        pygame.draw.line(surface, (50,40,30), (sx,sy), (wx,wy), 4)
        pygame.draw.line(surface, wcolor, (sx,sy), (wx,wy), 2)

    def _draw_knight(self, surface, sx, sy, wind_up, wu_prog):
        hurt = self.hurt_timer > 0
        body_c = (160,80,80) if hurt else ((180,180,220) if wind_up else (90,90,120))
        # Full plate
        pygame.draw.rect(surface, (20,18,25), (sx-17, sy-17, 34, 32), border_radius=4)
        pygame.draw.rect(surface, body_c, (sx-15, sy-15, 30, 28), border_radius=3)
        # Plate highlights
        hl = tuple(min(255,c+50) for c in body_c)
        pygame.draw.line(surface, hl, (sx-10,sy-12), (sx-10,sy+8), 2)
        pygame.draw.line(surface, hl, (sx+2,sy-12), (sx+2,sy+8), 2)
        # Great helm
        pygame.draw.rect(surface, (15,12,20), (sx-13, sy-26, 26, 18), border_radius=3)
        pygame.draw.rect(surface, body_c, (sx-11, sy-24, 22, 16), border_radius=2)
        # Visor slit
        pygame.draw.rect(surface, (10,10,15), (sx-9, sy-18, 18, 4))
        ec = (255,200,255) if wind_up else (100,80,140)
        pygame.draw.line(surface, ec, (sx-8,sy-16), (sx+8,sy-16), 2)
        if wind_up:
            draw_glow(surface, sx, sy-16, 14, (200,160,255), int(120*wu_prog))
        # Sword - heavier
        wcolor = (200,200,220) if not wind_up else (240,200,255)
        wx = sx + int(self.facing.x * 30)
        wy = sy + int(self.facing.y * 30)
        pygame.draw.line(surface, (30,28,40), (sx,sy), (wx,wy), 6)
        pygame.draw.line(surface, wcolor, (sx,sy), (wx,wy), 3)
        pygame.draw.circle(surface, wcolor, (wx,wy), 5)

    def _draw_archer(self, surface, sx, sy, wind_up, wu_prog):
        hurt = self.hurt_timer > 0
        body_c = (160,90,60) if hurt else ((200,160,60) if wind_up else (90,70,40))
        # Leather
        pygame.draw.rect(surface, (30,22,14), (sx-14, sy-14, 28, 26), border_radius=4)
        pygame.draw.rect(surface, body_c, (sx-12, sy-12, 24, 22), border_radius=3)
        # Hood
        pygame.draw.circle(surface, (40,30,18), (sx, sy-15), 11)
        pygame.draw.circle(surface, tuple(min(255,c+20) for c in body_c), (sx,sy-16), 9)
        # Eyes
        ec = (200,200,80) if wind_up else (160,160,60)
        pygame.draw.circle(surface, ec, (sx + int(self.facing.x*5)-2, sy-16), 2)
        pygame.draw.circle(surface, ec, (sx + int(self.facing.x*5)+2, sy-16), 2)
        # Bow
        bx = sx + int(self.facing.y * 14)
        by = sy - int(self.facing.x * 14)
        bx2 = sx + int(self.facing.y * -14)
        by2 = sy - int(self.facing.x * -14)
        pygame.draw.line(surface, (100,70,40), (bx,by),(bx2,by2), 3)
        # Arrow (nocked when winding up)
        if wind_up:
            ax = sx + int(self.facing.x * 30)
            ay = sy + int(self.facing.y * 30)
            pygame.draw.line(surface, (160,130,80), (sx,sy),(ax,ay), 2)
            draw_glow(surface, ax, ay, 10, (255,220,80), int(90*wu_prog))
            pygame.draw.circle(surface, (240,200,60), (ax,ay), 3)

    def _draw_brute(self, surface, sx, sy, wind_up, wu_prog):
        hurt = self.hurt_timer > 0
        body_c = (180,60,40) if hurt else ((220,120,40) if wind_up else (110,55,30))
        # Huge body
        pygame.draw.rect(surface, (35,15,8), (sx-22, sy-20, 44, 38), border_radius=5)
        pygame.draw.rect(surface, body_c, (sx-20, sy-18, 40, 34), border_radius=4)
        # Muscle lines
        hl = tuple(min(255,c+40) for c in body_c)
        pygame.draw.line(surface, hl, (sx-12,sy-14),(sx-12,sy+10), 2)
        pygame.draw.line(surface, hl, (sx,sy-14),(sx,sy+10), 2)
        pygame.draw.line(surface, hl, (sx+12,sy-14),(sx+12,sy+10), 2)
        # Massive head / bone mask
        pygame.draw.circle(surface, (30,14,6), (sx,sy-20), 17)
        pygame.draw.circle(surface, tuple(min(255,c+15) for c in body_c), (sx,sy-21), 15)
        # Bone horns
        pygame.draw.line(surface, (220,210,180), (sx-8,sy-30),(sx-14,sy-42), 3)
        pygame.draw.line(surface, (220,210,180), (sx+8,sy-30),(sx+14,sy-42), 3)
        # Sunken eyes
        ec = (255,80,20) if wind_up else (180,40,10)
        if wind_up:
            draw_glow(surface, sx-5, sy-21, 10, (255,80,20), int(150*wu_prog))
            draw_glow(surface, sx+5, sy-21, 10, (255,80,20), int(150*wu_prog))
        pygame.draw.circle(surface, ec, (sx-5, sy-21), 4)
        pygame.draw.circle(surface, ec, (sx+5, sy-21), 4)
        pygame.draw.circle(surface, (255,200,150), (sx-5,sy-21), 2)
        pygame.draw.circle(surface, (255,200,150), (sx+5,sy-21), 2)
        # Club/maul
        wx = sx + int(self.facing.x * 36)
        wy = sy + int(self.facing.y * 36)
        pygame.draw.line(surface, (60,40,20), (sx,sy),(wx,wy), 8)
        pygame.draw.circle(surface, (80,55,30), (wx,wy), 10)
        if wind_up:
            draw_glow(surface, wx, wy, 18, (255,120,20), int(100*wu_prog))
            pygame.draw.circle(surface, (200,120,40), (wx,wy), 10, 2)
