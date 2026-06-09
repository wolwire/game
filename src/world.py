import pygame
import random
import math
from .constants import *
from .particles import draw_glow


class Tile:
    def __init__(self, x, y, tile_type, passable=True, seed=None):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.tile_type = tile_type
        self.passable = passable
        self.seed = seed if seed is not None else random.randint(0, 9999)


class SiteOfGrace:
    def __init__(self, x, y):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x - 20, y - 20, 40, 40)
        self.lit = False
        self.anim = 0

    def draw(self, surface, cam_ox, cam_oy):
        sx = int(self.pos.x - cam_ox)
        sy = int(self.pos.y - cam_oy)
        self.anim = (self.anim + 1) % 120
        flicker = math.sin(self.anim * 0.18) * 3

        # Stone base platform
        pygame.draw.ellipse(surface, (50, 44, 36), (sx-22, sy+8, 44, 16))
        pygame.draw.ellipse(surface, (72, 63, 50), (sx-20, sy+6, 40, 14))

        # Central obelisk
        obelisk_pts = [(sx-7,sy+8),(sx+7,sy+8),(sx+5,sy-22),(sx,sy-28),(sx-5,sy-22)]
        pygame.draw.polygon(surface, (45, 40, 32), [(x+1,y+1) for x,y in obelisk_pts])
        pygame.draw.polygon(surface, (90, 80, 60), obelisk_pts)
        # Rune lines on obelisk
        pygame.draw.line(surface, GOLD, (sx-3,sy-8),(sx+3,sy-8), 1)
        pygame.draw.line(surface, GOLD, (sx-2,sy-2),(sx+2,sy-2), 1)
        pygame.draw.line(surface, GOLD, (sx-4,sy+2),(sx+4,sy+2), 1)

        if self.lit:
            # Bright flame layers
            flame_h = 18 + flicker
            # Outer flame
            pts_out = [(sx-7,sy-22),(sx+7,sy-22),(sx+4,sy-22-flame_h*0.6),(sx,sy-22-flame_h),(sx-4,sy-22-flame_h*0.6)]
            pygame.draw.polygon(surface, (200, 100, 20), pts_out)
            # Mid flame
            pts_mid = [(sx-4,sy-22),(sx+4,sy-22),(sx+2,sy-22-flame_h*0.7),(sx,sy-22-flame_h*1.1),(sx-2,sy-22-flame_h*0.7)]
            pygame.draw.polygon(surface, (240, 180, 40), pts_mid)
            # Inner bright
            pts_in = [(sx-2,sy-22),(sx+2,sy-22),(sx,sy-22-flame_h*0.9)]
            pygame.draw.polygon(surface, (255, 240, 180), pts_in)
            # Glow
            draw_glow(surface, sx, sy-26, 28, (212,175,55), 80)
            draw_glow(surface, sx, sy-26, 14, (255,240,180), 120)
            # Light ring on ground
            ring = pygame.Surface((80,30), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (212,175,55,30), (0,0,80,30))
            surface.blit(ring, (sx-40, sy))
        else:
            # Unlit — faint ember
            pygame.draw.polygon(surface, (50,42,30), [(sx-3,sy-22),(sx+3,sy-22),(sx,sy-30)])
            draw_glow(surface, sx, sy-26, 8, (80,60,30), 40)


class LoreFragment:
    def __init__(self, x, y, key):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x-12, y-12, 24, 24)
        self.key = key
        self.collected = False
        self.anim = random.randint(0, 60)

    def draw(self, surface, cam_ox, cam_oy):
        if self.collected: return
        sx = int(self.pos.x - cam_ox)
        sy = int(self.pos.y - cam_oy)
        self.anim = (self.anim + 1) % 120
        bob = math.sin(self.anim * 0.1) * 3
        spin = self.anim * 3

        # Gold glow
        draw_glow(surface, sx, int(sy+bob), 22, GOLD, int(60+math.sin(self.anim*0.08)*30))

        # Rotating outer rune ring
        for i in range(8):
            angle = math.radians(spin + i*45)
            rx = sx + int(math.cos(angle)*14)
            ry = int(sy+bob) + int(math.sin(angle)*14)
            pygame.draw.circle(surface, GOLD, (rx,ry), 2)

        # Scroll body
        scroll_y = int(sy - 10 + bob)
        pygame.draw.rect(surface, (100,80,45), (sx-9,scroll_y,18,16), border_radius=2)
        pygame.draw.rect(surface, (160,130,80), (sx-8,scroll_y+1,16,14), border_radius=2)
        # End caps
        pygame.draw.rect(surface, (120,95,55), (sx-10,scroll_y,20,4), border_radius=2)
        pygame.draw.rect(surface, (120,95,55), (sx-10,scroll_y+12,20,4), border_radius=2)
        # Text lines on scroll
        for li in range(3):
            pygame.draw.line(surface, (80,60,30), (sx-5, scroll_y+4+li*3), (sx+5, scroll_y+4+li*3), 1)


class RunePickup:
    def __init__(self, x, y, amount):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x-16, y-16, 32, 32)
        self.amount = amount
        self.collected = False
        self.anim = 0

    def draw(self, surface, cam_ox, cam_oy):
        if self.collected: return
        sx = int(self.pos.x - cam_ox)
        sy = int(self.pos.y - cam_oy)
        self.anim = (self.anim + 1) % 120
        pulse = 1 + math.sin(self.anim * 0.12) * 0.2
        spin = self.anim * 2

        # Ground glow
        draw_glow(surface, sx, sy, int(28*pulse), (60,180,80), 60)

        # Orbiting sparks
        for i in range(4):
            angle = math.radians(spin + i*90)
            ox2 = sx + int(math.cos(angle)*16)
            oy2 = sy + int(math.sin(angle)*10)
            pygame.draw.circle(surface, (100,240,140), (ox2,oy2), 2)

        # Central gem
        r = int(12 * pulse)
        pygame.draw.circle(surface, (20,100,40), (sx,sy), r+2)
        pygame.draw.circle(surface, (50,180,80), (sx,sy), r)
        # Facets
        for i in range(6):
            angle = math.radians(spin*0.5 + i*60)
            fx = sx + int(math.cos(angle)*r*0.7)
            fy = sy + int(math.sin(angle)*r*0.7)
            pygame.draw.line(surface, (100,240,140), (sx,sy), (fx,fy), 1)
        # Highlight
        pygame.draw.circle(surface, (180,255,200), (sx-3,sy-3), r//3)


# ---- Tile palette ----
FLOOR_BASE = {
    'stone':   [(52,48,44),(58,53,48),(48,44,40)],
    'dirt':    [(58,48,34),(64,54,38),(52,42,28)],
    'grass':   [(38,62,32),(44,70,36),(32,56,28)],
    'rot':     [(34,52,28),(40,62,32),(28,44,22)],
    'marble':  [(62,58,68),(70,66,76),(54,50,60)],
}
WALL_BASE = {
    'wall':        [(32,28,26),(38,34,30),(26,22,20)],
    'dark_wall':   [(20,18,24),(26,22,28),(16,14,20)],
    'rot_wall':    [(22,34,18),(28,42,22),(18,28,14)],
    'castle_wall': [(46,42,52),(54,50,60),(40,36,46)],
}
ALL_TILE_COLORS = {**FLOOR_BASE, **WALL_BASE}


def _tile_color(tile_type, seed):
    variants = ALL_TILE_COLORS.get(tile_type)
    if not variants:
        return (50,50,50)
    return variants[seed % len(variants)]


def _draw_floor_detail(surface, rect, tile_type, seed, cam_ox, cam_oy):
    sx = rect.x - cam_ox
    sy = rect.y - cam_oy
    S = TILE_SIZE
    rng = random.Random(seed)

    base = _tile_color(tile_type, seed)
    pygame.draw.rect(surface, base, (sx, sy, S, S))

    # Subtle edge shading
    edge = tuple(max(0,c-10) for c in base)
    pygame.draw.line(surface, edge, (sx,sy+S-1),(sx+S,sy+S-1), 1)
    pygame.draw.line(surface, edge, (sx+S-1,sy),(sx+S-1,sy+S), 1)
    lighter = tuple(min(255,c+8) for c in base)
    pygame.draw.line(surface, lighter, (sx,sy),(sx+S,sy), 1)
    pygame.draw.line(surface, lighter, (sx,sy),(sx,sy+S), 1)

    # Type-specific details
    if tile_type in ('stone','marble','castle_wall','wall','dark_wall') and rng.random() < 0.12:
        # Crack
        cx = sx + rng.randint(4, S-8)
        cy = sy + rng.randint(4, S-8)
        ce = (max(0,base[0]-18), max(0,base[1]-18), max(0,base[2]-18))
        dx = rng.randint(-8, 8)
        dy = rng.randint(-8, 8)
        pygame.draw.line(surface, ce, (cx,cy),(cx+dx,cy+dy), 1)

    elif tile_type in ('grass','rot') and rng.random() < 0.14:
        # Tuft of grass/rot weed
        gx = sx + rng.randint(4, S-8)
        gy = sy + S - rng.randint(4,10)
        gc = (60,100,40) if tile_type=='grass' else (60,100,30)
        for b in range(3):
            bx = gx + rng.randint(-4,4)
            pygame.draw.line(surface, gc, (bx,gy),(bx+rng.randint(-2,2),gy-rng.randint(4,9)), 1)

    elif tile_type == 'dirt' and rng.random() < 0.08:
        # Pebble
        px = sx + rng.randint(5, S-9)
        py = sy + rng.randint(5, S-9)
        pygame.draw.circle(surface, (70,58,40), (px,py), rng.randint(2,4))

    if tile_type in ('wall','dark_wall','castle_wall','rot_wall') and rng.random() < 0.06:
        # Moss / lichen
        mx = sx + rng.randint(3, S-8)
        my = sy + rng.randint(3, S-8)
        mc = (40,70,30) if tile_type!='rot_wall' else (50,80,30)
        pygame.draw.ellipse(surface, mc, (mx,my,rng.randint(4,10),rng.randint(3,7)))


def _make_room(tiles, walls, rx, ry, rw, rh, floor_type='stone', wall_type='wall'):
    for ty in range(ry, ry + rh):
        for tx in range(rx, tx + rw if False else rx + rw):
            px = tx * TILE_SIZE
            py = ty * TILE_SIZE
            on_edge = (tx == rx or tx == rx+rw-1 or ty == ry or ty == ry+rh-1)
            seed = (tx * 73 + ty * 31) & 0xFFFF
            t = Tile(px, py, wall_type if on_edge else floor_type,
                     passable=not on_edge, seed=seed)
            tiles.append(t)
            if on_edge:
                walls.append(t.rect.copy())


def _make_corridor(tiles, walls, x1, y1, x2, y2, floor_type='stone'):
    cx = min(x1, x2)
    cxe = max(x1, x2)
    for tx in range(cx, cxe + 1):
        px = tx * TILE_SIZE
        py = y1 * TILE_SIZE
        seed = (tx * 73 + y1 * 31) & 0xFFFF
        tiles.append(Tile(px, py, floor_type, passable=True, seed=seed))
        wr = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        walls[:] = [w for w in walls if not w.colliderect(wr)]
    cy = min(y1, y2)
    cye = max(y1, y2)
    for ty in range(cy, cye + 1):
        px = x2 * TILE_SIZE
        py = ty * TILE_SIZE
        seed = (x2 * 73 + ty * 31) & 0xFFFF
        tiles.append(Tile(px, py, floor_type, passable=True, seed=seed))
        wr = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        walls[:] = [w for w in walls if not w.colliderect(wr)]


class Decoration:
    """Non-blocking environment prop."""
    def __init__(self, x, y, dtype, area=0):
        self.x = x
        self.y = y
        self.dtype = dtype
        self.area = area
        self.anim = random.randint(0,120)

    def draw(self, surface, cam_ox, cam_oy):
        sx = int(self.x - cam_ox)
        sy = int(self.y - cam_oy)
        self.anim = (self.anim + 1) % 240

        if self.dtype == 'torch':
            # Wall torch
            pygame.draw.rect(surface, (80,60,30), (sx-3,sy-6,6,14), border_radius=1)
            flicker = math.sin(self.anim*0.2) * 3
            # Flame
            pygame.draw.polygon(surface, (200,80,20), [(sx-4,sy-6),(sx+4,sy-6),(sx,sy-16-flicker)])
            pygame.draw.polygon(surface, (240,160,30), [(sx-2,sy-6),(sx+2,sy-6),(sx,sy-14-flicker)])
            pygame.draw.polygon(surface, (255,230,180), [(sx-1,sy-6),(sx+1,sy-6),(sx,sy-12-flicker)])
            draw_glow(surface, sx, sy-10, 24, (220,140,40), int(70+flicker*8))

        elif self.dtype == 'pillar':
            shadow = pygame.Surface((20,12), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0,0,0,80), (0,0,20,12))
            surface.blit(shadow, (sx-10,sy+12))
            # Pillar body
            pygame.draw.rect(surface, (35,30,28), (sx-8,sy-28,16,40), border_radius=2)
            pygame.draw.rect(surface, (65,58,50), (sx-7,sy-27,14,38), border_radius=2)
            # Capital
            pygame.draw.rect(surface, (72,65,55), (sx-10,sy-28,20,6))
            pygame.draw.rect(surface, (72,65,55), (sx-10,sy+10,20,4))
            # Highlight
            pygame.draw.line(surface, (90,80,65), (sx-5,sy-22),(sx-5,sy+8), 2)

        elif self.dtype == 'bones':
            pygame.draw.line(surface, (200,195,175), (sx-8,sy),(sx+8,sy), 2)
            pygame.draw.line(surface, (200,195,175), (sx-6,sy-4),(sx+6,sy+4), 2)
            pygame.draw.circle(surface, (210,205,185), (sx,sy-6), 5)
            pygame.draw.circle(surface, (180,175,155), (sx,sy-6), 5, 1)

        elif self.dtype == 'mushroom':
            stalk_c = (140,120,80)
            cap_c = (180,80,50) if self.area < 2 else (80,160,50)
            cap_size = 10 + int(math.sin(self.anim*0.03)*2)
            pygame.draw.line(surface, stalk_c, (sx,sy),(sx,sy-12), 2)
            pygame.draw.ellipse(surface, (40,20,12), (sx-cap_size//2-1,sy-16,cap_size+2,cap_size//2+2))
            pygame.draw.ellipse(surface, cap_c, (sx-cap_size//2,sy-15,cap_size,cap_size//2))
            pygame.draw.ellipse(surface, tuple(min(255,c+40) for c in cap_c),
                                (sx-cap_size//2+2,sy-14,cap_size-4,cap_size//4))

        elif self.dtype == 'web':
            wc = (160,155,145)
            for i in range(6):
                angle = i * math.pi/3
                ex2 = sx + int(math.cos(angle)*14)
                ey2 = sy + int(math.sin(angle)*14)
                pygame.draw.line(surface, wc, (sx,sy),(ex2,ey2), 1)
            for r in [5,10,14]:
                for i in range(6):
                    a1 = i*math.pi/3
                    a2 = (i+1)*math.pi/3
                    p1 = (sx+int(math.cos(a1)*r), sy+int(math.sin(a1)*r))
                    p2 = (sx+int(math.cos(a2)*r), sy+int(math.sin(a2)*r))
                    pygame.draw.line(surface, wc, p1, p2, 1)

        elif self.dtype == 'chest':
            pygame.draw.rect(surface, (60,45,25), (sx-12,sy-8,24,16), border_radius=2)
            pygame.draw.rect(surface, (90,68,35), (sx-11,sy-7,22,14), border_radius=2)
            pygame.draw.rect(surface, (70,55,28), (sx-11,sy-8,22,8), border_radius=2)
            pygame.draw.line(surface, (120,90,40), (sx-11,sy-1),(sx+11,sy-1), 2)
            pygame.draw.circle(surface, GOLD, (sx,sy-1), 3)
            draw_glow(surface, sx, sy, 14, GOLD, 40)

        elif self.dtype == 'rot_spore':
            r = 8 + int(math.sin(self.anim*0.05)*3)
            draw_glow(surface, sx, sy, r+6, (100,200,50), 40)
            pygame.draw.circle(surface, (50,90,25), (sx,sy), r)
            pygame.draw.circle(surface, (80,140,40), (sx,sy), r-2)
            pygame.draw.circle(surface, (120,200,60), (sx,sy), r-4)

        elif self.dtype == 'void_crystal':
            r = 10 + int(math.sin(self.anim*0.06)*3)
            draw_glow(surface, sx, sy, r+8, (120,60,200), 60)
            pts = [(sx,sy-r),(sx+r//2,sy),(sx,sy+r//2),(sx-r//2,sy)]
            pygame.draw.polygon(surface, (60,20,100), pts)
            pts2 = [(sx+2,sy-r+4),(sx+r//2-2,sy+2),(sx,sy+r//2-4),(sx-r//2+2,sy)]
            pygame.draw.polygon(surface, (160,80,255), pts2)
            pygame.draw.circle(surface, (220,180,255), (sx,sy-r//2), 3)


def make_world_0():
    tiles, walls = [], []
    entities_data, graces, lore, decorations = [], [], [], []
    map_w, map_h = 3200, 2400

    _make_room(tiles, walls, 2, 2, 18, 14, 'grass', 'wall')
    _make_corridor(tiles, walls, 5, 2, 5, -6, 'stone')
    _make_room(tiles, walls, -2, -18, 24, 18, 'stone', 'wall')
    _make_room(tiles, walls, 1, -38, 20, 18, 'stone', 'dark_wall')
    _make_corridor(tiles, walls, 10, -18, 10, -38, 'stone')
    _make_room(tiles, walls, 28, -4, 14, 12, 'stone', 'wall')
    _make_corridor(tiles, walls, 22, 6, 28, 6, 'stone')
    _make_room(tiles, walls, -18, -8, 14, 12, 'stone', 'wall')
    _make_corridor(tiles, walls, -2, 0, -4, 0, 'stone')

    from src.world import SiteOfGrace, LoreFragment
    graces = [SiteOfGrace(10*TILE_SIZE, 8*TILE_SIZE), SiteOfGrace(10*TILE_SIZE, -8*TILE_SIZE)]

    entities_data = [
        ('soldier',14*T,6*T),('soldier',6*T,3*T),
        ('soldier',8*T,-6*T),('soldier',12*T,-10*T),
        ('knight',4*T,-14*T),('knight',16*T,-14*T),
        ('archer',32*T,2*T),('archer',34*T,6*T),
        ('soldier',-8*T,-2*T),('brute',-10*T,-10*T),
    ]

    lore = [LoreFragment(30*T,2*T,'scroll_1'), LoreFragment(-12*T,-6*T,'scroll_2')]

    # Decorations
    for _ in range(8):
        decorations.append(Decoration(random.randint(3,16)*T, random.randint(3,14)*T, 'torch', 0))
    for _ in range(6):
        decorations.append(Decoration(random.randint(3,20)*T, random.randint(-16,-4)*T, 'pillar', 0))
    for _ in range(10):
        decorations.append(Decoration(random.randint(3,16)*T, random.randint(3,14)*T, 'bones', 0))
    for _ in range(6):
        decorations.append(Decoration(random.randint(28,40)*T, random.randint(-3,6)*T, 'bones', 0))
    decorations.append(Decoration(30*T, 4*T, 'chest', 0))

    return tiles, walls, entities_data, graces, lore, decorations, map_w, map_h

T = TILE_SIZE

def make_world_1():
    tiles, walls = [], []
    entities_data, graces, lore, decorations = [], [], [], []
    map_w, map_h = 3200, 2800

    _make_room(tiles, walls, 2, 2, 20, 16, 'rot', 'rot_wall')
    _make_corridor(tiles, walls, 10, 2, 10, -6, 'rot')
    _make_room(tiles, walls, 0, -24, 26, 18, 'rot', 'rot_wall')
    _make_room(tiles, walls, 1, -44, 22, 18, 'rot', 'dark_wall')
    _make_corridor(tiles, walls, 11, -24, 11, -44, 'rot')
    _make_room(tiles, walls, 30, 0, 16, 14, 'rot', 'rot_wall')
    _make_corridor(tiles, walls, 22, 8, 30, 8, 'rot')
    _make_room(tiles, walls, -20, -4, 14, 14, 'rot', 'rot_wall')
    _make_corridor(tiles, walls, 0, 4, -6, 4, 'rot')

    graces = [SiteOfGrace(10*T,8*T), SiteOfGrace(12*T,-12*T)]

    entities_data = [
        ('soldier',15*T,6*T),('soldier',7*T,4*T),
        ('knight',10*T,-8*T),('knight',14*T,-12*T),
        ('archer',12*T,-16*T),('brute',5*T,-18*T),('brute',18*T,-18*T),
        ('soldier',34*T,4*T),('archer',36*T,8*T),
        ('knight',-8*T,0),('brute',-12*T,-8*T),
    ]

    lore = [LoreFragment(32*T,6*T,'scroll_3')]

    for _ in range(12):
        decorations.append(Decoration(random.randint(3,20)*T, random.randint(3,16)*T, 'mushroom', 1))
    for _ in range(8):
        decorations.append(Decoration(random.randint(3,24)*T, random.randint(-22,-4)*T, 'rot_spore', 1))
    for _ in range(6):
        decorations.append(Decoration(random.randint(3,20)*T, random.randint(3,16)*T, 'torch', 1))
    for _ in range(5):
        decorations.append(Decoration(random.randint(3,24)*T, random.randint(-22,-4)*T, 'bones', 1))
    for _ in range(3):
        decorations.append(Decoration(random.randint(3,20)*T, random.randint(3,16)*T, 'web', 1))

    return tiles, walls, entities_data, graces, lore, decorations, map_w, map_h


def make_world_2():
    tiles, walls = [], []
    entities_data, graces, lore, decorations = [], [], [], []
    map_w, map_h = 3600, 3000

    _make_room(tiles, walls, 2, 2, 22, 18, 'marble', 'castle_wall')
    _make_corridor(tiles, walls, 12, 2, 12, -6, 'marble')
    _make_room(tiles, walls, 2, -26, 28, 22, 'marble', 'castle_wall')
    _make_room(tiles, walls, 4, -52, 24, 24, 'marble', 'dark_wall')
    _make_corridor(tiles, walls, 15, -26, 15, -52, 'marble')
    _make_room(tiles, walls, 36, -2, 18, 16, 'marble', 'castle_wall')
    _make_corridor(tiles, walls, 24, 8, 36, 8, 'marble')
    _make_room(tiles, walls, -22, -2, 16, 16, 'marble', 'castle_wall')
    _make_corridor(tiles, walls, 2, 6, -6, 6, 'marble')

    graces = [SiteOfGrace(12*T,10*T), SiteOfGrace(14*T,-14*T)]

    entities_data = [
        ('knight',16*T,6*T),('knight',8*T,4*T),
        ('brute',12*T,-8*T),('knight',18*T,-14*T),
        ('archer',8*T,-16*T),('knight',6*T,-20*T),
        ('knight',20*T,-20*T),('brute',12*T,-22*T),
        ('archer',40*T,2*T),('brute',42*T,8*T),
        ('knight',-8*T,2*T),('brute',-12*T,8*T),
    ]

    lore = [LoreFragment(38*T,4*T,'scroll_4')]

    for _ in range(10):
        decorations.append(Decoration(random.randint(3,22)*T, random.randint(3,18)*T, 'pillar', 2))
    for _ in range(8):
        decorations.append(Decoration(random.randint(3,28)*T, random.randint(-24,-4)*T, 'void_crystal', 2))
    for _ in range(6):
        decorations.append(Decoration(random.randint(3,22)*T, random.randint(3,18)*T, 'torch', 2))
    for _ in range(4):
        decorations.append(Decoration(random.randint(36,52)*T, random.randint(-1,12)*T, 'bones', 2))

    return tiles, walls, entities_data, graces, lore, decorations, map_w, map_h


WORLD_MAKERS = [make_world_0, make_world_1, make_world_2]
BOSS_TYPES = ['erdwight', 'malvorn', 'nameless']
BOSS_SPAWN_OFFSETS = {
    0: (10*T, -30*T),
    1: (11*T, -36*T),
    2: (16*T, -42*T),
}


def draw_tiles(surface, tiles, cam_ox, cam_oy):
    for t in tiles:
        sr = t.rect.move(-cam_ox, -cam_oy)
        if -TILE_SIZE <= sr.x <= WIDTH + TILE_SIZE and -TILE_SIZE <= sr.y <= HEIGHT + TILE_SIZE:
            _draw_floor_detail(surface, t.rect, t.tile_type, t.seed, cam_ox, cam_oy)
