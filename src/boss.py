import pygame
import math
import random
from .constants import *


class Boss:
    PHASES = {
        'erdwight': [
            {'name': 'Erdwight, First Knight', 'hp': 480, 'phase': 1},
            {'name': 'Erdwight, Fallen Blade', 'hp': 480, 'phase': 2},
        ],
        'malvorn': [
            {'name': 'Malvorn the Putrid', 'hp': 600, 'phase': 1},
            {'name': 'Malvorn, Rot Ascendant', 'hp': 600, 'phase': 2},
        ],
        'nameless': [
            {'name': 'The Nameless God', 'hp': 800, 'phase': 1},
            {'name': 'The Nameless God, Unshackled', 'hp': 800, 'phase': 2},
            {'name': 'The Nameless God, Oblivion', 'hp': 600, 'phase': 3},
        ],
    }

    def __init__(self, x, y, boss_type='erdwight'):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - 32, y - 32, 64, 64)
        self.boss_type = boss_type
        self.phase_idx = 0
        self.phases = self.PHASES[boss_type]
        self._init_phase()
        self.facing = pygame.math.Vector2(1, 0)
        self.dead = False
        self.death_timer = 120
        self.hurt_timer = 0
        self.stagger_timer = 0
        self.iframes = 0
        self.move_pattern = 0
        self.move_timer = 0
        self.phase_transition = False
        self.phase_transition_timer = 0
        self.enraged = False
        self.attacks = self._build_attacks()
        self.atk_idx = 0
        self.atk_timer = 0
        self.atk_cd = 0
        self.active_hitboxes = []
        self.projectiles = []
        self.aggro = False
        self.intro_timer = 90

    def _init_phase(self):
        pd = self.phases[self.phase_idx]
        self.max_hp = pd['hp']
        self.hp = self.max_hp
        self.name = pd['name']
        self.phase = pd['phase']

    def _build_attacks(self):
        if self.boss_type == 'erdwight':
            return [
                {'name': 'slash', 'wind': 35, 'active': 14, 'dmg': 28, 'range': 80, 'arc': 90, 'cd': 70},
                {'name': 'lunge', 'wind': 50, 'active': 18, 'dmg': 36, 'range': 140, 'arc': 40, 'cd': 90},
                {'name': 'spin',  'wind': 45, 'active': 24, 'dmg': 22, 'range': 90, 'arc': 360, 'cd': 100},
            ]
        elif self.boss_type == 'malvorn':
            return [
                {'name': 'rot_breath', 'wind': 55, 'active': 30, 'dmg': 20, 'range': 120, 'arc': 60, 'cd': 80, 'poison': True},
                {'name': 'slam',       'wind': 60, 'active': 20, 'dmg': 40, 'range': 100, 'arc': 120, 'cd': 90},
                {'name': 'spore_shot', 'wind': 40, 'active': 5,  'dmg': 15, 'range': 280, 'arc': 0, 'cd': 60, 'projectile': True},
            ]
        else:  # nameless
            return [
                {'name': 'void_slash',   'wind': 30, 'active': 12, 'dmg': 35, 'range': 90, 'arc': 70, 'cd': 60},
                {'name': 'star_rain',    'wind': 60, 'active': 8,  'dmg': 25, 'range': 260, 'arc': 0, 'cd': 80, 'projectile': True, 'multi': 5},
                {'name': 'annihilate',   'wind': 80, 'active': 40, 'dmg': 55, 'range': 200, 'arc': 360, 'cd': 120},
            ]

    def take_damage(self, amount, stagger=False):
        if self.dead or self.iframes > 0 or self.phase_transition:
            return False
        self.hp -= amount
        self.hurt_timer = 10
        self.iframes = 4
        if stagger:
            self.stagger_timer = 25
        if self.hp <= 0:
            self.hp = 0
            if self.phase_idx + 1 < len(self.phases):
                self._start_phase_transition()
            else:
                self.dead = True
        return True

    def _start_phase_transition(self):
        self.phase_transition = True
        self.phase_transition_timer = 120
        self.phase_idx += 1
        self.stagger_timer = 0
        self.iframes = 120

    def update(self, player, walls):
        if self.dead:
            self.death_timer -= 1
            return

        if self.intro_timer > 0:
            self.intro_timer -= 1
            return

        if self.phase_transition:
            self.phase_transition_timer -= 1
            if self.phase_transition_timer <= 0:
                self.phase_transition = False
                self._init_phase()
                self.iframes = 30
                self.enraged = self.phase_idx >= 1
            return

        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.iframes > 0: self.iframes -= 1
        if self.stagger_timer > 0:
            self.stagger_timer -= 1
            return

        diff = player.pos - self.pos
        dist = diff.length()
        self.aggro = True

        if diff.length() > 0:
            self.facing = diff.normalize()

        if self.atk_timer > 0:
            self.atk_timer -= 1
            self._update_hitboxes()
            return

        if self.atk_cd > 0:
            self.atk_cd -= 1
            spd = 1.5 + (0.5 if self.enraged else 0)
            if dist > 80:
                self._move(self.facing * spd, walls)
            return

        # Choose attack
        atk = self._choose_attack(dist)
        total = atk['wind'] + atk['active'] + 20
        self.current_atk = atk
        self.atk_timer = total
        self.atk_cd = atk['cd'] + random.randint(-10, 10)
        self.active_hitboxes = []

        if atk.get('projectile'):
            self._launch_projectiles(atk)

    def _choose_attack(self, dist):
        atks = self.attacks
        # Phase 2+ adds more aggression
        if self.enraged:
            # prefer faster attacks
            return random.choice(atks)
        # Weight towards range-appropriate attacks
        if dist > 150:
            ranged = [a for a in atks if a.get('projectile') or a['range'] > 100]
            if ranged:
                return random.choice(ranged)
        return random.choice(atks)

    def _update_hitboxes(self):
        atk = getattr(self, 'current_atk', None)
        if not atk:
            return
        total = atk['wind'] + atk['active'] + 20
        elapsed = total - self.atk_timer
        wind = atk['wind']
        active_end = wind + atk['active']

        if wind <= elapsed <= active_end:
            cx = self.pos.x + self.facing.x * atk['range'] * 0.5
            cy = self.pos.y + self.facing.y * atk['range'] * 0.5
            size = atk['range'] if atk['arc'] == 360 else int(atk['range'] * 0.8)
            self.active_hitboxes = [pygame.Rect(cx - size//2, cy - size//2, size, size)]
        else:
            self.active_hitboxes = []

        # Update projectiles
        for p in self.projectiles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] <= 0:
                self.projectiles.remove(p)

    def _launch_projectiles(self, atk):
        count = atk.get('multi', 1)
        for i in range(count):
            angle_offset = (i - count//2) * 0.3
            base_angle = math.atan2(self.facing.y, self.facing.x)
            angle = base_angle + angle_offset
            speed = 4.5
            self.projectiles.append({
                'x': self.pos.x, 'y': self.pos.y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'dmg': atk['dmg'],
                'life': 90,
                'poison': atk.get('poison', False),
            })

    def is_winding_up(self):
        atk = getattr(self, 'current_atk', None)
        if not atk or self.atk_timer <= 0:
            return False
        total = atk['wind'] + atk['active'] + 20
        elapsed = total - self.atk_timer
        return elapsed < atk['wind']

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

        # Draw projectiles
        for p in self.projectiles:
            px = int(p['x'] - cam_ox)
            py = int(p['y'] - cam_oy)
            pc = PURPLE if p.get('poison') else (200, 220, 255)
            pygame.draw.circle(surface, pc, (px, py), 8)
            pygame.draw.circle(surface, WHITE, (px, py), 8, 2)

        if self.dead and self.death_timer <= 0:
            return

        # Shadow
        pygame.draw.ellipse(surface, (15, 15, 15), (sx-28, sy+20, 56, 18))

        # Phase transition glow
        if self.phase_transition:
            prog = 1 - self.phase_transition_timer / 120
            r = int(60 * prog)
            glow_surf = pygame.Surface((r*2+1, r*2+1), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (200, 100, 50, 60), (r, r), r)
            surface.blit(glow_surf, (sx - r, sy - r))

        # Colors per type
        colors = {
            'erdwight': ((60, 70, 100), (120, 140, 180)),
            'malvorn':  ((40, 60, 30), (80, 120, 50)),
            'nameless': ((50, 30, 70), (130, 80, 180)),
        }
        outer, inner = colors.get(self.boss_type, ((60,60,60),(120,120,120)))

        if self.hurt_timer > 0:
            inner = (240, 100, 100)
        if self.is_winding_up():
            inner = (240, 180, 40)
        if self.enraged:
            outer = tuple(min(255, c+30) for c in outer)

        # Body
        pygame.draw.rect(surface, outer, (sx-32, sy-32, 64, 64), border_radius=8)
        pygame.draw.rect(surface, inner, (sx-28, sy-28, 56, 56), border_radius=6)

        # Head
        pygame.draw.circle(surface, tuple(min(255,c+20) for c in inner), (sx, sy-16), 18)

        # Eyes - glowing
        eye_color = (255, 60, 60) if not self.enraged else (255, 200, 0)
        ex = sx + int(self.facing.x * 8)
        ey = sy - 17 + int(self.facing.y * 5)
        pygame.draw.circle(surface, eye_color, (ex-5, ey), 4)
        pygame.draw.circle(surface, eye_color, (ex+5, ey), 4)
        pygame.draw.circle(surface, WHITE, (ex-5, ey), 2)
        pygame.draw.circle(surface, WHITE, (ex+5, ey), 2)

        # Attack hitbox visualization (subtle)
        atk = getattr(self, 'current_atk', None)
        if atk and self.active_hitboxes:
            for hb in self.active_hitboxes:
                s = pygame.Surface((hb.width, hb.height), pygame.SRCALPHA)
                s.fill((255, 80, 30, 50))
                surface.blit(s, (hb.x - cam_ox, hb.y - cam_oy))

        # Wind-up telegraph
        if self.is_winding_up() and atk:
            total = atk['wind'] + atk['active'] + 20
            elapsed = total - self.atk_timer
            prog = elapsed / atk['wind']
            # Draw warning arc
            warn_r = int(atk['range'] * prog * 0.7)
            if warn_r > 0:
                ws = pygame.Surface((warn_r*2+2, warn_r*2+2), pygame.SRCALPHA)
                pygame.draw.circle(ws, (255, 140, 0, 40), (warn_r+1, warn_r+1), warn_r)
                surface.blit(ws, (sx - warn_r - 1, sy - warn_r - 1))
