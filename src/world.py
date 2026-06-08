import pygame
import random
import math
from .constants import *


class Tile:
    def __init__(self, x, y, tile_type, passable=True):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.tile_type = tile_type
        self.passable = passable


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

        # Base
        pygame.draw.ellipse(surface, (60, 50, 30), (sx-18, sy+4, 36, 14))
        pygame.draw.polygon(surface, (80, 70, 40), [
            (sx, sy-28), (sx-8, sy+4), (sx+8, sy+4)
        ])

        if self.lit:
            # Glowing golden flame
            flicker = math.sin(self.anim * 0.15) * 4
            color = GOLD
            pygame.draw.polygon(surface, (200, 160, 40), [
                (sx, sy-40-flicker), (sx-8, sy-16), (sx+8, sy-16)
            ])
            pygame.draw.polygon(surface, (240, 210, 80), [
                (sx, sy-36-flicker), (sx-5, sy-18), (sx+5, sy-18)
            ])
            # Glow
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow, (212, 175, 55, 40), (30, 30), 28)
            surface.blit(glow, (sx-30, sy-48))
        else:
            pygame.draw.polygon(surface, (60, 60, 60), [
                (sx, sy-32), (sx-5, sy-16), (sx+5, sy-16)
            ])


class LoreFragment:
    def __init__(self, x, y, key):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x-12, y-12, 24, 24)
        self.key = key
        self.collected = False
        self.anim = random.randint(0, 60)

    def draw(self, surface, cam_ox, cam_oy):
        if self.collected:
            return
        sx = int(self.pos.x - cam_ox)
        sy = int(self.pos.y - cam_oy)
        self.anim = (self.anim + 1) % 120
        bob = math.sin(self.anim * 0.1) * 3
        # Book/scroll icon
        pygame.draw.rect(surface, (140, 110, 60), (sx-10, sy-12+bob, 20, 18), border_radius=2)
        pygame.draw.rect(surface, (180, 150, 90), (sx-8, sy-10+bob, 16, 14), border_radius=2)
        pygame.draw.line(surface, (140, 110, 60), (sx, sy-10+bob), (sx, sy+2+bob), 1)
        # Glow
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        a = int(60 + math.sin(self.anim * 0.08) * 30)
        pygame.draw.circle(glow, (212, 175, 55, a), (20, 20), 18)
        surface.blit(glow, (sx-20, sy-20+bob))


class RunePickup:
    def __init__(self, x, y, amount):
        self.pos = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x-16, y-16, 32, 32)
        self.amount = amount
        self.collected = False
        self.anim = 0

    def draw(self, surface, cam_ox, cam_oy):
        if self.collected:
            return
        sx = int(self.pos.x - cam_ox)
        sy = int(self.pos.y - cam_oy)
        self.anim = (self.anim + 1) % 120
        scale = 1 + math.sin(self.anim * 0.12) * 0.15
        r = int(14 * scale)
        glow = pygame.Surface((r*3, r*3), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 200, 100, 60), (r*3//2, r*3//2), r+4)
        surface.blit(glow, (sx-r*3//2, sy-r*3//2))
        pygame.draw.circle(surface, (40, 160, 80), (sx, sy), r)
        pygame.draw.circle(surface, (80, 220, 120), (sx, sy), r, 2)
        pygame.draw.circle(surface, (160, 255, 200), (sx-3, sy-3), r//3)


def _make_room(tiles, walls, rx, ry, rw, rh, floor_type='stone', wall_type='wall'):
    for ty in range(ry, ry + rh):
        for tx in range(rx, rx + rw):
            px = tx * TILE_SIZE
            py = ty * TILE_SIZE
            on_edge = (tx == rx or tx == rx+rw-1 or ty == ry or ty == ry+rh-1)
            t = Tile(px, py, wall_type if on_edge else floor_type, passable=not on_edge)
            tiles.append(t)
            if on_edge:
                walls.append(t.rect)


def _make_corridor(tiles, walls, x1, y1, x2, y2, floor_type='stone'):
    # L-shaped corridor
    cx = min(x1, x2)
    cxe = max(x1, x2)
    for tx in range(cx, cxe + 1):
        px = tx * TILE_SIZE
        py = y1 * TILE_SIZE
        tiles.append(Tile(px, py, floor_type, passable=True))
        # Remove from walls if exists
        wr = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        walls[:] = [w for w in walls if not w.colliderect(wr)]

    cy = min(y1, y2)
    cye = max(y1, y2)
    for ty in range(cy, cye + 1):
        px = x2 * TILE_SIZE
        py = ty * TILE_SIZE
        tiles.append(Tile(px, py, floor_type, passable=True))
        wr = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
        walls[:] = [w for w in walls if not w.colliderect(wr)]


FLOOR_COLORS = {
    'stone':   (55, 50, 45),
    'dirt':    (60, 50, 35),
    'grass':   (40, 65, 35),
    'rot':     (35, 55, 30),
    'marble':  (65, 60, 70),
    'water':   (30, 40, 70),
}
WALL_COLORS = {
    'wall':       (35, 30, 28),
    'dark_wall':  (22, 20, 25),
    'rot_wall':   (25, 35, 20),
    'castle_wall': (50, 45, 55),
}
DECOR_COLORS = {
    'stone':   (70, 65, 60),
    'grass':   (50, 80, 40),
    'rot':     (55, 80, 40),
    'marble':  (90, 85, 95),
}


def make_world_0():
    """Area 0 - The Ashen Crossing"""
    tiles = []
    walls = []
    entities_data = []
    graces = []
    lore = []

    map_w = 3200
    map_h = 2400

    # Starting room
    _make_room(tiles, walls, 2, 2, 18, 14, 'grass', 'wall')
    # Corridor north
    _make_corridor(tiles, walls, 5, 2, 5, -6, 'stone')
    # Mid room
    _make_room(tiles, walls, -2, -18, 24, 18, 'stone', 'wall')
    # Boss room
    _make_room(tiles, walls, 1, -38, 20, 18, 'stone', 'dark_wall')
    # Corridor to boss
    _make_corridor(tiles, walls, 10, -18, 10, -38, 'stone')

    # Side room 1
    _make_room(tiles, walls, 28, -4, 14, 12, 'stone', 'wall')
    _make_corridor(tiles, walls, 22, 6, 28, 6, 'stone')

    # Side room 2
    _make_room(tiles, walls, -18, -8, 14, 12, 'stone', 'wall')
    _make_corridor(tiles, walls, -2, 0, -4, 0, 'stone')

    # Sites of Grace
    graces.append(SiteOfGrace(10*TILE_SIZE, 8*TILE_SIZE))
    graces.append(SiteOfGrace(10*TILE_SIZE, -8*TILE_SIZE))

    # Enemies
    entities_data += [
        ('soldier', 14*TILE_SIZE, 6*TILE_SIZE),
        ('soldier', 6*TILE_SIZE, 3*TILE_SIZE),
        ('soldier', 8*TILE_SIZE, -6*TILE_SIZE),
        ('soldier', 12*TILE_SIZE, -10*TILE_SIZE),
        ('knight', 4*TILE_SIZE, -14*TILE_SIZE),
        ('knight', 16*TILE_SIZE, -14*TILE_SIZE),
        ('archer', 32*TILE_SIZE, 2*TILE_SIZE),
        ('archer', 34*TILE_SIZE, 6*TILE_SIZE),
        ('soldier', -8*TILE_SIZE, -2*TILE_SIZE),
        ('brute', -10*TILE_SIZE, -10*TILE_SIZE),
    ]

    # Lore fragments
    lore.append(LoreFragment(30*TILE_SIZE, 2*TILE_SIZE, 'scroll_1'))
    lore.append(LoreFragment(-12*TILE_SIZE, -6*TILE_SIZE, 'scroll_2'))

    return tiles, walls, entities_data, graces, lore, map_w, map_h


def make_world_1():
    """Area 1 - Rotwood"""
    tiles = []
    walls = []
    entities_data = []
    graces = []
    lore = []

    map_w = 3200
    map_h = 2800

    _make_room(tiles, walls, 2, 2, 20, 16, 'rot', 'rot_wall')
    _make_corridor(tiles, walls, 10, 2, 10, -6, 'rot')
    _make_room(tiles, walls, 0, -24, 26, 18, 'rot', 'rot_wall')
    _make_room(tiles, walls, 1, -44, 22, 18, 'rot', 'dark_wall')
    _make_corridor(tiles, walls, 11, -24, 11, -44, 'rot')

    _make_room(tiles, walls, 30, 0, 16, 14, 'rot', 'rot_wall')
    _make_corridor(tiles, walls, 22, 8, 30, 8, 'rot')
    _make_room(tiles, walls, -20, -4, 14, 14, 'rot', 'rot_wall')
    _make_corridor(tiles, walls, 0, 4, -6, 4, 'rot')

    graces.append(SiteOfGrace(10*TILE_SIZE, 8*TILE_SIZE))
    graces.append(SiteOfGrace(12*TILE_SIZE, -12*TILE_SIZE))

    entities_data += [
        ('soldier', 15*TILE_SIZE, 6*TILE_SIZE),
        ('soldier', 7*TILE_SIZE, 4*TILE_SIZE),
        ('knight', 10*TILE_SIZE, -8*TILE_SIZE),
        ('knight', 14*TILE_SIZE, -12*TILE_SIZE),
        ('archer', 12*TILE_SIZE, -16*TILE_SIZE),
        ('brute', 5*TILE_SIZE, -18*TILE_SIZE),
        ('brute', 18*TILE_SIZE, -18*TILE_SIZE),
        ('soldier', 34*TILE_SIZE, 4*TILE_SIZE),
        ('archer', 36*TILE_SIZE, 8*TILE_SIZE),
        ('knight', -8*TILE_SIZE, 0),
        ('brute', -12*TILE_SIZE, -8*TILE_SIZE),
    ]

    lore.append(LoreFragment(32*TILE_SIZE, 6*TILE_SIZE, 'scroll_3'))

    return tiles, walls, entities_data, graces, lore, map_w, map_h


def make_world_2():
    """Area 2 - The Sunken Throne"""
    tiles = []
    walls = []
    entities_data = []
    graces = []
    lore = []

    map_w = 3600
    map_h = 3000

    _make_room(tiles, walls, 2, 2, 22, 18, 'marble', 'castle_wall')
    _make_corridor(tiles, walls, 12, 2, 12, -6, 'marble')
    _make_room(tiles, walls, 2, -26, 28, 22, 'marble', 'castle_wall')
    _make_room(tiles, walls, 4, -52, 24, 24, 'marble', 'dark_wall')
    _make_corridor(tiles, walls, 15, -26, 15, -52, 'marble')

    _make_room(tiles, walls, 36, -2, 18, 16, 'marble', 'castle_wall')
    _make_corridor(tiles, walls, 24, 8, 36, 8, 'marble')
    _make_room(tiles, walls, -22, -2, 16, 16, 'marble', 'castle_wall')
    _make_corridor(tiles, walls, 2, 6, -6, 6, 'marble')

    graces.append(SiteOfGrace(12*TILE_SIZE, 10*TILE_SIZE))
    graces.append(SiteOfGrace(14*TILE_SIZE, -14*TILE_SIZE))

    entities_data += [
        ('knight', 16*TILE_SIZE, 6*TILE_SIZE),
        ('knight', 8*TILE_SIZE, 4*TILE_SIZE),
        ('brute', 12*TILE_SIZE, -8*TILE_SIZE),
        ('knight', 18*TILE_SIZE, -14*TILE_SIZE),
        ('archer', 8*TILE_SIZE, -16*TILE_SIZE),
        ('knight', 6*TILE_SIZE, -20*TILE_SIZE),
        ('knight', 20*TILE_SIZE, -20*TILE_SIZE),
        ('brute', 12*TILE_SIZE, -22*TILE_SIZE),
        ('archer', 40*TILE_SIZE, 2*TILE_SIZE),
        ('brute', 42*TILE_SIZE, 8*TILE_SIZE),
        ('knight', -8*TILE_SIZE, 2*TILE_SIZE),
        ('brute', -12*TILE_SIZE, 8*TILE_SIZE),
    ]

    lore.append(LoreFragment(38*TILE_SIZE, 4*TILE_SIZE, 'scroll_4'))

    return tiles, walls, entities_data, graces, lore, map_w, map_h


WORLD_MAKERS = [make_world_0, make_world_1, make_world_2]
BOSS_TYPES = ['erdwight', 'malvorn', 'nameless']
BOSS_SPAWN_OFFSETS = {
    0: (10*TILE_SIZE, -30*TILE_SIZE),
    1: (11*TILE_SIZE, -36*TILE_SIZE),
    2: (16*TILE_SIZE, -42*TILE_SIZE),
}


def draw_tiles(surface, tiles, cam_ox, cam_oy):
    for t in tiles:
        sr = pygame.Rect(t.rect.x - cam_ox, t.rect.y - cam_oy, TILE_SIZE, TILE_SIZE)
        if -TILE_SIZE <= sr.x <= WIDTH + TILE_SIZE and -TILE_SIZE <= sr.y <= HEIGHT + TILE_SIZE:
            fc = FLOOR_COLORS.get(t.tile_type) or WALL_COLORS.get(t.tile_type) or (50, 50, 50)
            pygame.draw.rect(surface, fc, sr)
            # Grid line
            pygame.draw.rect(surface, tuple(max(0,c-8) for c in fc), sr, 1)
