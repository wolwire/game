import pygame
import math
import random
from .constants import *
from .particles import draw_glow


class Boss:
    PHASES = {
        'erdwight': [
            {'name': 'Erdwight, First Knight',   'hp': 480, 'phase': 1},
            {'name': 'Erdwight, Fallen Blade',   'hp': 480, 'phase': 2},
        ],
        'malvorn': [
            {'name': 'Malvorn the Putrid',        'hp': 600, 'phase': 1},
            {'name': 'Malvorn, Rot Ascendant',    'hp': 600, 'phase': 2},
        ],
        'nameless': [
            {'name': 'The Nameless God',           'hp': 800, 'phase': 1},
            {'name': 'The Nameless God, Unshackled','hp': 800, 'phase': 2},
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
        self.phase_transition = False
        self.phase_transition_timer = 0
        self.enraged = False
        self.attacks = self._build_attacks()
        self.current_atk = None
        self.atk_timer = 0
        self.atk_cd = 0
        self.active_hitboxes = []
        self.projectiles = []
        self.aggro = False
        self.intro_timer = 90
        self.anim = 0
        self.float_offset = 0.0

    def _init_phase(self):
        pd = self.phases[self.phase_idx]
        self.max_hp = pd['hp']
        self.hp = self.max_hp
        self.name = pd['name']
        self.phase = pd['phase']

    def _build_attacks(self):
        if self.boss_type == 'erdwight':
            return [
                {'name':'slash',  'wind':35,'active':14,'dmg':28,'range':80, 'arc':90,  'cd':70},
                {'name':'lunge',  'wind':50,'active':18,'dmg':36,'range':140,'arc':40,  'cd':90},
                {'name':'spin',   'wind':45,'active':24,'dmg':22,'range':90, 'arc':360, 'cd':100},
            ]
        elif self.boss_type == 'malvorn':
            return [
                {'name':'rot_breath','wind':55,'active':30,'dmg':20,'range':120,'arc':60, 'cd':80,'poison':True},
                {'name':'slam',      'wind':60,'active':20,'dmg':40,'range':100,'arc':120,'cd':90},
                {'name':'spore_shot','wind':40,'active':5, 'dmg':15,'range':280,'arc':0,  'cd':60,'projectile':True},
            ]
        else:
            return [
                {'name':'void_slash', 'wind':30,'active':12,'dmg':35,'range':90, 'arc':70, 'cd':60},
                {'name':'star_rain',  'wind':60,'active':8, 'dmg':25,'range':260,'arc':0,  'cd':80,'projectile':True,'multi':5},
                {'name':'annihilate', 'wind':80,'active':40,'dmg':55,'range':200,'arc':360,'cd':120},
            ]

    def take_damage(self, amount, stagger=False):
        if self.dead or self.iframes > 0 or self.phase_transition: return False
        self.hp -= amount
        self.hurt_timer = 10
        self.iframes = 4
        if stagger: self.stagger_timer = 25
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

        self.anim = (self.anim + 1) % 240
        self.float_offset = math.sin(self.anim * 0.06) * 4

        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.iframes > 0: self.iframes -= 1
        if self.stagger_timer > 0:
            self.stagger_timer -= 1
            return

        diff = player.pos - self.pos
        dist = diff.length()
        self.aggro = True
        if diff.length() > 0: self.facing = diff.normalize()

        if self.atk_timer > 0:
            self.atk_timer -= 1
            self._update_hitboxes()
            return

        if self.atk_cd > 0:
            self.atk_cd -= 1
            spd = 1.5 + (0.5 if self.enraged else 0)
            if dist > 80: self._move(self.facing * spd, walls)
            return

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
        if dist > 150:
            ranged = [a for a in atks if a.get('projectile') or a['range'] > 100]
            if ranged: return random.choice(ranged)
        return random.choice(atks)

    def _update_hitboxes(self):
        atk = self.current_atk
        if not atk: return
        total = atk['wind'] + atk['active'] + 20
        elapsed = total - self.atk_timer
        if atk['wind'] <= elapsed <= atk['wind'] + atk['active']:
            cx = self.pos.x + self.facing.x * atk['range'] * 0.5
            cy = self.pos.y + self.facing.y * atk['range'] * 0.5
            size = atk['range'] if atk['arc'] == 360 else int(atk['range'] * 0.8)
            self.active_hitboxes = [pygame.Rect(cx-size//2, cy-size//2, size, size)]
        else:
            self.active_hitboxes = []
        for p in self.projectiles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] <= 0:
                self.projectiles.remove(p)

    def _launch_projectiles(self, atk):
        count = atk.get('multi', 1)
        for i in range(count):
            angle = math.atan2(self.facing.y, self.facing.x) + (i - count//2) * 0.3
            speed = 4.5
            self.projectiles.append({
                'x': self.pos.x, 'y': self.pos.y,
                'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed,
                'dmg': atk['dmg'], 'life': 90,
                'poison': atk.get('poison', False),
                'color': (80,200,80) if atk.get('poison') else (160,100,255),
            })

    def is_winding_up(self):
        if not self.current_atk or self.atk_timer <= 0: return False
        total = self.current_atk['wind'] + self.current_atk['active'] + 20
        elapsed = total - self.atk_timer
        return elapsed < self.current_atk['wind']

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
        sy = int(self.pos.y - cam_oy + self.float_offset)

        # Draw projectiles
        for p in self.projectiles:
            px = int(p['x'] - cam_ox)
            py = int(p['y'] - cam_oy)
            pc = p.get('color', (160,100,255))
            draw_glow(surface, px, py, 20, pc, 80)
            pygame.draw.circle(surface, pc, (px, py), 8)
            core = tuple(min(255,c+80) for c in pc)
            pygame.draw.circle(surface, core, (px, py), 4)

        if self.dead and self.death_timer <= 0: return

        if self.boss_type == 'erdwight':
            self._draw_erdwight(surface, sx, sy)
        elif self.boss_type == 'malvorn':
            self._draw_malvorn(surface, sx, sy)
        else:
            self._draw_nameless(surface, sx, sy)

        # Hitbox visual
        for hb in self.active_hitboxes:
            s = pygame.Surface((hb.width, hb.height), pygame.SRCALPHA)
            s.fill((255, 80, 30, 35))
            pygame.draw.rect(s, (255,120,40,80), (0,0,hb.width,hb.height), 2)
            surface.blit(s, (hb.x - cam_ox, hb.y - cam_oy))

    def _draw_erdwight(self, surface, sx, sy):
        wind_up = self.is_winding_up()
        hurt = self.hurt_timer > 0
        phase2 = self.enraged

        # Aura
        aura_c = (255,60,20) if phase2 else (80,100,180)
        intensity = 60 + int(math.sin(self.anim * 0.12) * 20)
        draw_glow(surface, sx, sy, 55, aura_c, intensity)

        # Shadow
        shadow = pygame.Surface((80,24), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0,0,0,100), (0,0,80,24))
        surface.blit(shadow, (sx-40, sy+28))

        # Cape
        cape_c = (20,15,30) if not phase2 else (40,8,8)
        for i in range(8):
            angle = math.pi * 0.5 + i * math.pi / 7
            cx = sx + int(math.cos(angle) * 28)
            cy = sy + int(math.sin(angle) * 18) + 10
            pygame.draw.ellipse(surface, cape_c, (cx-6,cy-14,12,20))

        # Body — full plate armor
        body_c = (160,160,200) if hurt else ((220,180,100) if wind_up else (120,125,160))
        if phase2: body_c = (180,80,60) if not wind_up else (240,140,40)
        pygame.draw.rect(surface, (25,22,35), (sx-30, sy-30, 60, 58), border_radius=8)
        pygame.draw.rect(surface, body_c, (sx-27, sy-27, 54, 52), border_radius=6)

        # Armor detailing
        hl = tuple(min(255,c+50) for c in body_c)
        for lx in [sx-18, sx-6, sx+6, sx+18]:
            pygame.draw.line(surface, hl, (lx, sy-22), (lx, sy+18), 2)
        pygame.draw.line(surface, hl, (sx-22, sy-5), (sx+22, sy-5), 2)

        # Pauldrons (big)
        pc = tuple(min(255,c+20) for c in body_c)
        pygame.draw.ellipse(surface, (20,18,28), (sx-40,sy-25,22,18))
        pygame.draw.ellipse(surface, pc, (sx-38,sy-24,18,14))
        pygame.draw.ellipse(surface, (20,18,28), (sx+18,sy-25,22,18))
        pygame.draw.ellipse(surface, pc, (sx+20,sy-24,18,14))

        # Great helm
        pygame.draw.rect(surface, (20,18,30), (sx-22,sy-46,44,26), border_radius=6)
        pygame.draw.rect(surface, body_c, (sx-20,sy-44,40,22), border_radius=5)
        # Crest / crown
        for i in range(5):
            cx2 = sx - 16 + i*8
            pygame.draw.line(surface, GOLD, (cx2,sy-44), (cx2,sy-56), 3)
            pygame.draw.circle(surface, GOLD, (cx2,sy-56), 3)

        # Visor
        pygame.draw.rect(surface, (8,6,14), (sx-16,sy-38,32,8), border_radius=2)
        ec = (255,200,60) if wind_up else (180,160,255)
        if phase2: ec = (255,80,40)
        pygame.draw.line(surface, ec, (sx-14,sy-34),(sx+14,sy-34), 3)
        if wind_up or phase2:
            draw_glow(surface, sx, sy-34, 20, ec, 120 if wind_up else 80)

        # Greatsword
        sw_color = (200,210,240) if not phase2 else (240,120,60)
        ang = math.atan2(self.facing.y, self.facing.x)
        if wind_up:
            wu_prog = min(1.0, (self.current_atk['wind'] + self.current_atk['active'] + 20 - self.atk_timer) / self.current_atk['wind'])
            ang += math.sin(wu_prog * math.pi) * 0.8
            draw_glow(surface, sx + int(math.cos(ang)*50), sy + int(math.sin(ang)*50), 22, sw_color, 120)
        wx = sx + int(math.cos(ang) * 65)
        wy = sy + int(math.sin(ang) * 65)
        pygame.draw.line(surface, (30,28,40), (sx,sy-5),(wx,wy), 9)
        pygame.draw.line(surface, sw_color, (sx,sy-5),(wx,wy), 5)
        # Crossguard
        perp = (-math.sin(ang), math.cos(ang))
        pygame.draw.line(surface, GOLD,
                         (sx+int(perp[0]*14), sy+int(perp[1]*14)-5),
                         (sx-int(perp[0]*14), sy-int(perp[1]*14)-5), 4)
        pygame.draw.circle(surface, (255,240,180), (wx,wy), 5)

    def _draw_malvorn(self, surface, sx, sy):
        wind_up = self.is_winding_up()
        hurt = self.hurt_timer > 0
        phase2 = self.enraged

        # Rot aura
        rot_c = (120,200,60) if not phase2 else (180,240,80)
        aura_a = 50 + int(math.sin(self.anim*0.08)*20)
        draw_glow(surface, sx, sy, 65, rot_c, aura_a)
        # Spore particles around body
        for i in range(6):
            angle = self.anim * 0.05 + i * math.pi / 3
            px2 = sx + int(math.cos(angle) * 38)
            py2 = sy + int(math.sin(angle) * 28)
            r = 3 + int(math.sin(angle + self.anim*0.1) * 2)
            pygame.draw.circle(surface, (*rot_c, 180), (px2, py2), r)

        # Shadow
        shadow = pygame.Surface((90,30), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0,0,0,90), (0,0,90,30))
        surface.blit(shadow, (sx-45, sy+30))

        # Body — bloated fungal mass
        body_c = (200,100,80) if hurt else ((200,200,80) if wind_up else (70,100,45))
        if phase2: body_c = (100,160,50) if not wind_up else (180,240,60)
        pygame.draw.ellipse(surface, (20,30,12), (sx-32,sy-28,64,60))
        pygame.draw.ellipse(surface, body_c, (sx-29,sy-25,58,54))

        # Mushroom growths
        mc = (180,160,60) if not phase2 else (220,200,80)
        for i, (ox,oy,mw,mh) in enumerate([(-24,-30,18,12),(-8,-36,16,14),(10,-32,20,12),(20,-26,14,10)]):
            pygame.draw.ellipse(surface, (30,50,20), (sx+ox-1,sy+oy-1,mw+2,mh+2))
            pygame.draw.ellipse(surface, mc, (sx+ox,sy+oy,mw,mh))

        # Head — rotted skull face
        pygame.draw.circle(surface, (25,35,15), (sx,sy-26), 22)
        pygame.draw.circle(surface, tuple(min(255,c+20) for c in body_c), (sx,sy-27), 19)
        # Skull cracks
        pygame.draw.line(surface, (20,30,10), (sx-5,sy-38),(sx-8,sy-22), 2)
        pygame.draw.line(surface, (20,30,10), (sx+6,sy-36),(sx+4,sy-20), 2)
        # Eyes — glowing rot
        ec = (180,255,80) if wind_up else (100,200,40)
        if wind_up: draw_glow(surface, sx-7,sy-28,12,ec,160)
        if wind_up: draw_glow(surface, sx+7,sy-28,12,ec,160)
        pygame.draw.circle(surface, ec, (sx-7,sy-28), 5)
        pygame.draw.circle(surface, ec, (sx+7,sy-28), 5)
        pygame.draw.circle(surface, (220,255,180), (sx-7,sy-28), 2)
        pygame.draw.circle(surface, (220,255,180), (sx+7,sy-28), 2)
        # Maw / teeth
        pygame.draw.arc(surface, (40,60,20), (sx-12,sy-20,24,12), math.pi, 2*math.pi, 3)
        for tx in range(-2,3):
            pygame.draw.line(surface, (220,210,180), (sx+tx*5,sy-14),(sx+tx*5-1,sy-9), 2)

        # Claws
        ang = math.atan2(self.facing.y, self.facing.x)
        for side in [-1,1]:
            perp_angle = ang + side * math.pi/2.2
            cx2 = sx + int(math.cos(perp_angle)*36)
            cy2 = sy + int(math.sin(perp_angle)*28)
            claw_c = (160,220,60) if wind_up else (80,120,40)
            pygame.draw.line(surface, (25,40,15),(sx,sy),(cx2,cy2),7)
            pygame.draw.line(surface, claw_c,(sx,sy),(cx2,cy2),4)
            # Claw tips
            for ci in range(3):
                tip_a = perp_angle + (ci-1)*0.25
                tx2 = cx2 + int(math.cos(tip_a)*14)
                ty2 = cy2 + int(math.sin(tip_a)*14)
                pygame.draw.line(surface, claw_c,(cx2,cy2),(tx2,ty2),3)

        if wind_up:
            draw_glow(surface, sx, sy, 40, rot_c, 80)

    def _draw_nameless(self, surface, sx, sy):
        wind_up = self.is_winding_up()
        hurt = self.hurt_timer > 0
        phase = self.phase_idx

        # Void aura — big
        aura_c = [(80,40,160),(120,60,200),(200,80,255)][min(phase,2)]
        aura_r = 70 + phase*15
        draw_glow(surface, sx, sy, aura_r, aura_c, 60 + phase*10)

        # Orbiting void fragments
        for i in range(4 + phase*2):
            angle = self.anim * 0.04 + i * math.pi*2/(4+phase*2)
            orb_r = 50 + phase*10
            ox2 = sx + int(math.cos(angle)*orb_r)
            oy2 = sy + int(math.sin(angle)*orb_r)
            fc = (160,80,255) if phase < 2 else (255,200,80)
            draw_glow(surface, ox2, oy2, 12, fc, 100)
            pygame.draw.circle(surface, fc, (ox2,oy2), 6)
            pygame.draw.circle(surface, WHITE, (ox2,oy2), 3)

        # Shadow
        shadow = pygame.Surface((100,30), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0,0,0,80), (0,0,100,30))
        surface.blit(shadow, (sx-50, sy+32))

        # Robes — flowing dark
        robe_c = (180,80,80) if hurt else ((240,180,80) if wind_up else (45,25,65))
        if phase >= 1: robe_c = (220,100,80) if wind_up else (60,30,80)
        if phase >= 2: robe_c = (255,200,40) if wind_up else (80,40,100)

        # Robe folds
        for i in range(7):
            angle = math.pi * i / 6
            rx = sx + int(math.cos(angle)*28)
            ry = sy + 10 + int(math.sin(angle)*12)
            pygame.draw.ellipse(surface, robe_c, (rx-5,ry-18,10,32))
        pygame.draw.ellipse(surface, robe_c, (sx-28,sy-12,56,50))

        # Upper body — void core
        core_c = (20,10,35) if phase < 2 else (40,20,10)
        pygame.draw.ellipse(surface, core_c, (sx-26,sy-26,52,46))
        pygame.draw.ellipse(surface, tuple(min(255,c+30) for c in robe_c), (sx-22,sy-22,44,38))

        # Crown of void shards
        for i in range(7):
            angle = -math.pi/2 + i * math.pi*2/7
            cr = 20 + i%2*5
            cx2 = sx + int(math.cos(angle)*18)
            cy2 = sy - 35 + int(math.sin(angle)*10)
            sc = (200,150,255) if phase < 2 else (255,230,80)
            pygame.draw.line(surface, sc, (sx,sy-26),(cx2,cy2), 3)
            pygame.draw.circle(surface, sc, (cx2,cy2), 4)

        # Face — ancient and terrible
        pygame.draw.circle(surface, (8,4,18), (sx,sy-22), 24)
        pygame.draw.circle(surface, tuple(min(255,c+25) for c in robe_c), (sx,sy-23), 20)

        # Multiple eyes
        eye_positions = [(-9,-28),(9,-28),(0,-22),(-14,-20),(14,-20)]
        for i,(ex2,ey2) in enumerate(eye_positions):
            ec = (255,100,255) if phase < 2 else (255,220,40)
            if wind_up: ec = (255,255,100)
            er = 3 if i < 2 else 2
            if wind_up or i < 2:
                draw_glow(surface, sx+ex2, sy+ey2, 10, ec, 130 if i<2 else 80)
            pygame.draw.circle(surface, ec, (sx+ex2,sy+ey2), er)
            pygame.draw.circle(surface, WHITE, (sx+ex2,sy+ey2), max(1,er-1))

        # Void hands / tendrils
        ang = math.atan2(self.facing.y, self.facing.x)
        for side in [-1,1]:
            pa = ang + side * math.pi/2.5
            hx = sx + int(math.cos(pa)*42)
            hy = sy + int(math.sin(pa)*32)
            tc = (140,60,220) if not wind_up else (220,160,255)
            if phase >= 2: tc = (255,180,40) if wind_up else (180,80,20)
            # Tendril
            for j in range(1,5):
                mix = j/4
                tx2 = int(sx + (hx-sx)*mix + math.sin(self.anim*0.1+j)*4)
                ty2 = int(sy + (hy-sy)*mix + math.cos(self.anim*0.1+j)*4)
                nx = int(sx + (hx-sx)*(mix+0.25) + math.sin(self.anim*0.1+j+1)*4)
                ny = int(sy + (hy-sy)*(mix+0.25) + math.cos(self.anim*0.1+j+1)*4)
                pygame.draw.line(surface, tc, (tx2,ty2),(nx,ny), max(1,5-j))
            # Hand
            draw_glow(surface, hx, hy, 15, tc, 80 if not wind_up else 140)
            pygame.draw.circle(surface, tc, (hx,hy), 8)
            pygame.draw.circle(surface, WHITE, (hx,hy), 3)
            # Fingers
            for fi in range(4):
                fa = pa + (fi-1.5)*0.3
                fx2 = hx + int(math.cos(fa)*18)
                fy2 = hy + int(math.sin(fa)*18)
                pygame.draw.line(surface, tc, (hx,hy),(fx2,fy2), 2)

        if wind_up:
            wu_prog = min(1.0, (self.current_atk['wind'] + self.current_atk['active'] + 20 - self.atk_timer) / self.current_atk['wind'])
            draw_glow(surface, sx, sy, int(50+50*wu_prog), (200,120,255), int(80*wu_prog))
