"""Procedural asset library.

Every sprite in the game is generated here at startup and cached, so the game
needs no external art files. All factories return (surface, (ax, ay)) where
(ax, ay) is the anchor: the pixel inside the surface that should be placed at
the object's projected screen position (its ground point).
"""
import math
import random
import pygame
from src.constants import TILE_W, TILE_H, HALF_W, HALF_H

_cache = {}


def _key(*parts):
    return parts


def _rand(seed):
    return random.Random(seed)


def _shade(color, f):
    return (max(0, min(255, int(color[0] * f))),
            max(0, min(255, int(color[1] * f))),
            max(0, min(255, int(color[2] * f))))


def diamond_points(ox, oy, w=TILE_W, h=TILE_H):
    return [(ox + w // 2, oy), (ox + w, oy + h // 2),
            (ox + w // 2, oy + h), (ox, oy + h // 2)]


# ---------------------------------------------------------------- ground ---

GROUND_COLORS = {
    'asphalt':   (52, 53, 58),
    'road':      (44, 45, 50),
    'sidewalk':  (108, 106, 102),
    'plaza':     (96, 92, 100),
    'grass':     (58, 78, 48),
    'dirt':      (84, 72, 56),
    'water':     (30, 48, 66),
    'sand':      (122, 110, 86),
    'rubble':    (70, 66, 62),
    'lot':       (60, 58, 56),
}


def ground_tile(kind, variant=0):
    k = _key('ground', kind, variant)
    if k in _cache:
        return _cache[k]
    rng = _rand(hash(k) & 0xffffffff)
    surf = pygame.Surface((TILE_W, TILE_H + 4), pygame.SRCALPHA)
    base = GROUND_COLORS.get(kind, (60, 60, 60))
    jitter = rng.randint(-4, 4)
    base = _shade(base, 1 + jitter / 100)
    pts = diamond_points(0, 0)
    pygame.draw.polygon(surf, base, pts)

    if kind in ('asphalt', 'road', 'lot'):
        for _ in range(7):
            x = rng.randint(10, TILE_W - 10)
            y = rng.randint(4, TILE_H - 4)
            c = _shade(base, rng.uniform(0.85, 1.15))
            surf.set_at((x, y), c)
        if rng.random() < 0.18:  # crack
            x, y = rng.randint(16, 48), rng.randint(8, 20)
            for _ in range(4):
                nx, ny = x + rng.randint(-6, 6), y + rng.randint(-3, 3)
                pygame.draw.line(surf, _shade(base, 0.7), (x, y), (nx, ny))
                x, y = nx, ny
    elif kind in ('sidewalk', 'plaza'):
        pygame.draw.line(surf, _shade(base, 0.82), pts[0], pts[2])
        pygame.draw.line(surf, _shade(base, 0.82), pts[3], pts[1])
    elif kind == 'grass':
        for _ in range(10):
            x = rng.randint(12, TILE_W - 12)
            y = rng.randint(5, TILE_H - 5)
            c = _shade((70, 95, 52), rng.uniform(0.8, 1.2))
            pygame.draw.line(surf, c, (x, y), (x + rng.randint(-1, 1), y - 2))
    elif kind == 'water':
        for i in range(3):
            y = 8 + i * 7 + rng.randint(-2, 2)
            pygame.draw.line(surf, _shade(base, 1.3), (14 + i * 4, y), (30 + i * 6, y))
    elif kind == 'rubble':
        for _ in range(6):
            x = rng.randint(10, TILE_W - 14)
            y = rng.randint(5, TILE_H - 8)
            c = _shade(base, rng.uniform(0.7, 1.25))
            pygame.draw.polygon(surf, c, [(x, y), (x + 4, y + 1), (x + 3, y + 3), (x - 1, y + 2)])
    # subtle edge shading so tiles read as a surface
    pygame.draw.lines(surf, _shade(base, 0.9), False, [pts[3], pts[2], pts[1]])
    _cache[k] = (surf, (HALF_W, HALF_H))
    return _cache[k]


def road_marking(kind):
    """Overlay decals for roads: lane dashes / crosswalks, in both axes."""
    k = _key('mark', kind)
    if k in _cache:
        return _cache[k]
    surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
    col = (188, 182, 150, 110)
    cx, cy = HALF_W, HALF_H
    if kind == 'dash_x':   # dashes running along world +x (screen down-right)
        pygame.draw.line(surf, col, (cx - 10, cy - 5), (cx + 10, cy + 5), 2)
    elif kind == 'dash_y':
        pygame.draw.line(surf, col, (cx + 10, cy - 5), (cx - 10, cy + 5), 2)
    elif kind == 'cross_x':
        for i in range(-2, 3):
            ox = i * 9
            pygame.draw.line(surf, (170, 168, 150, 130), (cx + ox - 7, cy + i * 0 - 4 + ox * 0.0 + 4 - 8), (cx + ox + 7, cy + 4 - 8 + 7), 3)
        surf.fill((0, 0, 0, 0))
        for i in range(-2, 3):
            x0, y0 = cx + i * 8 - 8, cy + i * 4 - 8
            pygame.draw.line(surf, (172, 170, 152, 120), (x0, y0 + 8), (x0 + 16, y0 + 16), 4)
    elif kind == 'manhole':
        pygame.draw.ellipse(surf, (38, 38, 40), (cx - 7, cy - 4, 14, 8))
        pygame.draw.ellipse(surf, (70, 70, 72), (cx - 7, cy - 4, 14, 8), 1)
    _cache[k] = (surf, (HALF_W, HALF_H))
    return _cache[k]


# -------------------------------------------------------------- buildings ---

BUILDING_STYLES = {
    'brick':    {'wall': (96, 62, 54),  'win': (28, 30, 40), 'lit': (210, 170, 90)},
    'concrete': {'wall': (110, 110, 116), 'win': (26, 30, 38), 'lit': (160, 200, 230)},
    'glass':    {'wall': (62, 76, 92),  'win': (40, 58, 76), 'lit': (120, 190, 235)},
    'shop':     {'wall': (88, 82, 96),  'win': (30, 32, 42), 'lit': (235, 160, 90)},
    'industrial': {'wall': (92, 84, 70), 'win': (24, 26, 30), 'lit': (200, 120, 70)},
    'tower':    {'wall': (40, 48, 64),  'win': (52, 70, 96), 'lit': (130, 220, 255)},
}


def building(seed, fw, fh, stories, style):
    """Iso box building over an fw x fh tile footprint, `stories` floors."""
    k = _key('bld', seed, fw, fh, stories, style)
    if k in _cache:
        return _cache[k]
    rng = _rand(seed)
    st = BUILDING_STYLES[style]
    story_px = 26
    zh = stories * story_px
    sw = (fw + fh) * HALF_W
    sh = (fw + fh) * HALF_H + zh
    surf = pygame.Surface((sw + 2, sh + 2), pygame.SRCALPHA)
    # origin: N corner of footprint at (fh*HALF_W, zh)
    nx, ny = fh * HALF_W, zh
    N = (nx, ny)
    E = (nx + fw * HALF_W, ny + fw * HALF_H)
    S = (nx + (fw - fh) * HALF_W, ny + (fw + fh) * HALF_H)
    W = (nx - fh * HALF_W, ny + fh * HALF_H)
    Nt, Et, St, Wt = [(p[0], p[1] - zh) for p in (N, E, S, W)]

    wall = _shade(st['wall'], rng.uniform(0.9, 1.08))
    left_c = _shade(wall, 0.72)    # SW face (darker)
    right_c = _shade(wall, 0.92)   # SE face
    top_c = _shade(wall, 1.12)

    pygame.draw.polygon(surf, left_c, [Wt, St, S, W])
    pygame.draw.polygon(surf, right_c, [St, Et, E, S])
    pygame.draw.polygon(surf, top_c, [Nt, Et, St, Wt])
    pygame.draw.lines(surf, _shade(wall, 0.5), True, [Nt, Et, St, Wt], 1)
    pygame.draw.line(surf, _shade(wall, 0.5), St, S, 1)
    pygame.draw.line(surf, _shade(wall, 0.55), Wt, W, 1)
    pygame.draw.line(surf, _shade(wall, 0.55), Et, E, 1)

    def face_windows(p_top_left, axis, n_cols, face_shade):
        ax_, ay_ = axis
        for s in range(stories):
            wy = p_top_left[1] + s * story_px + 7
            for c in range(n_cols):
                t = (c + 0.5) / n_cols
                wx = p_top_left[0] + ax_ * t
                yy = wy + ay_ * t
                lit = rng.random() < 0.13
                col = st['lit'] if lit else _shade(st['win'], face_shade)
                w_, h_ = 7, 11
                quad = [(wx - w_ / 2, yy), (wx + w_ / 2, yy + (ay_ / abs(ax_)) * w_ if ax_ else yy),
                        (wx + w_ / 2, yy + h_ + (ay_ / abs(ax_)) * w_ if ax_ else yy + h_),
                        (wx - w_ / 2, yy + h_)]
                pygame.draw.polygon(surf, col, quad)
                if lit:
                    pygame.draw.polygon(surf, _shade(col, 0.6), quad, 1)

    # SW face: from Wt to St, slope +0.5 ; SE face: from St to Et, slope -0.5
    face_windows(Wt, (St[0] - Wt[0], St[1] - Wt[1]), max(1, fw * 2 - 1), 0.85)
    face_windows(St, (Et[0] - St[0], Et[1] - St[1]), max(1, fh * 2 - 1), 1.0)

    # roof details
    if rng.random() < 0.6:
        bx = (Nt[0] + St[0]) / 2 + rng.randint(-8, 8)
        by = (Nt[1] + St[1]) / 2 + rng.randint(-4, 4)
        pygame.draw.polygon(surf, _shade(top_c, 0.8),
                            [(bx, by - 6), (bx + 10, by - 1), (bx, by + 4), (bx - 10, by - 1)])
    if style == 'tower':
        tipx, tipy = Nt[0] + (St[0] - Nt[0]) / 2, Nt[1] + (St[1] - Nt[1]) / 2
        pygame.draw.line(surf, (200, 60, 60), (tipx, tipy), (tipx, tipy - 26), 2)
        pygame.draw.circle(surf, (255, 90, 90), (int(tipx), int(tipy - 26)), 3)

    # ground-floor storefront for shop style
    if style == 'shop':
        pygame.draw.polygon(surf, (40, 36, 50),
                            [(W[0] + 4, W[1] - 14), (S[0] - 2, S[1] - 12 + 2), (S[0] - 2, S[1] - 2), (W[0] + 4, W[1] - 2)])
        pygame.draw.line(surf, (235, 170, 90), (W[0] + 4, W[1] - 15), (S[0] - 2, S[1] - 13), 2)

    # anchor: N corner of footprint should land on world_to_screen(gx, gy)
    _cache[k] = (surf, (nx, ny))
    return _cache[k]


# ------------------------------------------------------------------ props ---

CAR_COLORS = [(120, 40, 40), (50, 70, 110), (150, 140, 130), (60, 90, 60),
              (160, 120, 40), (90, 60, 100), (70, 70, 76)]


def car(seed, axis):
    """Wrecked car. axis 'x' = along world +x, 'y' = along world +y."""
    k = _key('car', seed, axis)
    if k in _cache:
        return _cache[k]
    rng = _rand(seed)
    col = _shade(rng.choice(CAR_COLORS), rng.uniform(0.8, 1.0))
    surf = pygame.Surface((92, 64), pygame.SRCALPHA)
    cx, cy = 46, 44

    def iso_quad(px, py, dx1, dy1, dx2, dy2, color):
        pygame.draw.polygon(surf, color, [(px, py), (px + dx1, py + dy1),
                                          (px + dx1 + dx2, py + dy1 + dy2), (px + dx2, py + dy2)])
    L, Wd, Hb = 60, 28, 14  # length, width, body height in px
    if axis == 'x':
        lx, ly = L * 0.55, L * 0.275      # long axis screen vector (down-right)
        wxp, wyp = -Wd * 0.55, Wd * 0.275  # width axis (down-left)
    else:
        lx, ly = -L * 0.55, L * 0.275
        wxp, wyp = Wd * 0.55, Wd * 0.275
    ox, oy = cx - (lx + wxp) / 2, cy - (ly + wyp) / 2 - Hb
    # body sides + top
    iso_quad(ox, oy + Hb, lx, ly, wxp, wyp, _shade(col, 0.55))          # shadow base
    iso_quad(ox, oy, lx, ly, 0, Hb, _shade(col, 0.8 if axis == 'x' else 0.65))
    iso_quad(ox + lx, oy + ly, wxp, wyp, 0, Hb, _shade(col, 0.65 if axis == 'x' else 0.8))
    iso_quad(ox, oy, lx, ly, wxp, wyp, col)
    # cabin
    cab_t = 0.28
    cox, coy = ox + lx * cab_t + wxp * 0.15, oy + ly * cab_t + wyp * 0.15 - 9
    iso_quad(cox, coy, lx * 0.42, ly * 0.42, wxp * 0.7, wyp * 0.7, _shade(col, 1.15))
    iso_quad(cox, coy, lx * 0.42, ly * 0.42, 0, 9, (30, 38, 48))
    iso_quad(cox + lx * 0.42, coy + ly * 0.42, wxp * 0.7, wyp * 0.7, 0, 9, (24, 30, 40))
    if rng.random() < 0.5:  # rust / damage
        for _ in range(4):
            px = ox + lx * rng.random() + wxp * rng.random()
            py = oy + ly * rng.random() + wyp * rng.random()
            pygame.draw.circle(surf, _shade(col, 0.5), (int(px), int(py)), rng.randint(2, 4))
    _cache[k] = (surf, (cx, cy + 6))
    return _cache[k]


def prop(kind, variant=0):
    k = _key('prop', kind, variant)
    if k in _cache:
        return _cache[k]
    rng = _rand(hash(k) & 0xffffffff)
    if kind == 'lamppost':
        surf = pygame.Surface((44, 92), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (12, 82, 20, 8))
        pygame.draw.line(surf, (70, 74, 80), (22, 86), (22, 14), 3)
        pygame.draw.line(surf, (70, 74, 80), (22, 14), (36, 18), 3)
        pygame.draw.circle(surf, (255, 196, 110), (37, 20), 4)
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 190, 100, 38), (20, 20), 18)
        surf.blit(glow, (17, 0))
        anchor = (22, 86)
    elif kind == 'traffic_light':
        surf = pygame.Surface((30, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (6, 72, 18, 7))
        pygame.draw.line(surf, (60, 62, 66), (15, 75), (15, 10), 3)
        pygame.draw.rect(surf, (40, 42, 46), (10, 6, 11, 26), border_radius=3)
        pygame.draw.circle(surf, (160, 50, 50), (15, 12), 3)
        pygame.draw.circle(surf, (150, 130, 40), (15, 19), 3)
        pygame.draw.circle(surf, (60, 110, 60), (15, 26), 3)
        anchor = (15, 75)
    elif kind == 'hydrant':
        surf = pygame.Surface((22, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (4, 23, 14, 6))
        pygame.draw.rect(surf, (150, 50, 44), (7, 8, 8, 17), border_radius=3)
        pygame.draw.circle(surf, (170, 60, 50), (11, 8), 5)
        pygame.draw.rect(surf, (120, 40, 36), (3, 13, 16, 4), border_radius=2)
        anchor = (11, 26)
    elif kind == 'dumpster':
        surf = pygame.Surface((56, 44), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (8, 34, 42, 9))
        pygame.draw.polygon(surf, (44, 84, 60), [(8, 38), (30, 27), (52, 38), (30, 49)])
        pygame.draw.polygon(surf, (38, 72, 52), [(8, 38), (8, 22), (30, 11), (30, 27)])
        pygame.draw.polygon(surf, (50, 96, 70), [(30, 27), (30, 11), (52, 22), (52, 38)])
        pygame.draw.polygon(surf, (60, 110, 80), [(8, 22), (30, 11), (52, 22), (30, 33)])
        anchor = (30, 42)
    elif kind == 'bench':
        surf = pygame.Surface((48, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (6, 22, 36, 7))
        pygame.draw.polygon(surf, (102, 74, 48), [(6, 22), (28, 11), (42, 18), (20, 29)])
        pygame.draw.polygon(surf, (84, 60, 40), [(6, 22), (6, 26), (20, 33), (20, 29)])
        pygame.draw.polygon(surf, (90, 66, 44), [(20, 29), (42, 18), (42, 22), (20, 33)])
        anchor = (24, 28)
    elif kind == 'barricade':
        surf = pygame.Surface((52, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (6, 27, 40, 8))
        pygame.draw.polygon(surf, (180, 120, 40), [(8, 26), (28, 16), (44, 24), (24, 34)])
        pygame.draw.polygon(surf, (150, 150, 150), [(8, 26), (28, 16), (28, 12), (8, 22)])
        for i in range(3):
            pygame.draw.line(surf, (220, 220, 220), (12 + i * 10, 24 - i * 3), (16 + i * 10, 30 - i * 3), 3)
        anchor = (26, 32)
    elif kind == 'tree':
        h = 58 + variant % 3 * 10
        surf = pygame.Surface((54, h + 14), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (15, h, 24, 10))
        pygame.draw.line(surf, (74, 56, 40), (27, h + 5), (27, h - 26), 4)
        for i, (r, yo) in enumerate([(17, -30), (14, -42), (10, -52)]):
            c = _shade((52, 84, 46), 0.9 + i * 0.12 + (variant % 5) * 0.02)
            pygame.draw.circle(surf, c, (27 + rng.randint(-3, 3), h + yo), r)
        anchor = (27, h + 5)
    elif kind == 'dead_tree':
        surf = pygame.Surface((44, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (12, 54, 20, 8))
        x, y = 22, 58
        pygame.draw.line(surf, (66, 56, 48), (x, y), (x - 2, y - 28), 4)
        pygame.draw.line(surf, (66, 56, 48), (x - 2, y - 28), (x - 12, y - 42), 2)
        pygame.draw.line(surf, (66, 56, 48), (x - 2, y - 28), (x + 8, y - 46), 2)
        pygame.draw.line(surf, (60, 52, 44), (x + 8, y - 46), (x + 14, y - 52), 1)
        anchor = (22, 58)
    elif kind == 'bus_stop':
        surf = pygame.Surface((70, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (10, 52, 50, 10))
        pygame.draw.polygon(surf, (50, 58, 70, 200), [(10, 24), (40, 9), (60, 19), (30, 34)])
        pygame.draw.line(surf, (90, 96, 104), (12, 25), (12, 54), 3)
        pygame.draw.line(surf, (90, 96, 104), (58, 20), (58, 49), 3)
        pygame.draw.polygon(surf, (70, 110, 140, 90), [(12, 28), (30, 37), (30, 52), (12, 43)])
        anchor = (35, 56)
    elif kind == 'debris':
        surf = pygame.Surface((40, 26), pygame.SRCALPHA)
        for _ in range(6):
            x, y = rng.randint(6, 32), rng.randint(8, 20)
            c = _shade((90, 84, 76), rng.uniform(0.6, 1.2))
            pygame.draw.polygon(surf, c, [(x, y), (x + 6, y + 2), (x + 4, y + 5), (x - 1, y + 3)])
        anchor = (20, 18)
    elif kind == 'crate':
        surf = pygame.Surface((40, 38), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (6, 28, 28, 9))
        pygame.draw.polygon(surf, (110, 88, 58), [(6, 30), (20, 23), (34, 30), (20, 37)])
        pygame.draw.polygon(surf, (94, 74, 48), [(6, 30), (6, 18), (20, 11), (20, 23)])
        pygame.draw.polygon(surf, (120, 96, 64), [(20, 23), (20, 11), (34, 18), (34, 30)])
        pygame.draw.polygon(surf, (130, 106, 72), [(6, 18), (20, 11), (34, 18), (20, 25)])
        anchor = (20, 34)
    elif kind == 'beacon':
        surf = pygame.Surface((70, 110), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (40, 70, 90, 90), (13, 92, 44, 16))
        pygame.draw.polygon(surf, (70, 78, 88), [(31, 100), (39, 100), (37, 30), (33, 30)])
        for yy, w in [(86, 14), (68, 11), (50, 8)]:
            pygame.draw.line(surf, (96, 104, 116), (35 - w, yy), (35 + w, yy), 2)
        pygame.draw.circle(surf, (140, 230, 255), (35, 24), 6)
        glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        for r, a in [(28, 28), (18, 48), (9, 90)]:
            pygame.draw.circle(glow, (110, 215, 255, a), (30, 30), r)
        surf.blit(glow, (5, -6))
        anchor = (35, 100)
    elif kind == 'shard_echo':   # dropped shards on death
        surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        for r, a in [(16, 36), (10, 70), (5, 130)]:
            pygame.draw.circle(surf, (150, 210, 255, a), (18, 22), r)
        pygame.draw.circle(surf, (220, 240, 255), (18, 22), 3)
        anchor = (18, 26)
    elif kind == 'lore':
        surf = pygame.Surface((26, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 60), (5, 23, 16, 6))
        pygame.draw.polygon(surf, (210, 200, 170), [(7, 24), (12, 9), (20, 12), (15, 27)])
        pygame.draw.line(surf, (120, 110, 90), (11, 14), (17, 16), 1)
        pygame.draw.line(surf, (120, 110, 90), (10, 18), (16, 20), 1)
        glow = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 230, 140, 40), (15, 15), 13)
        surf.blit(glow, (-2, 2))
        anchor = (13, 26)
    elif kind == 'fountain':
        surf = pygame.Surface((96, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (90, 88, 94), (8, 28, 80, 34))
        pygame.draw.ellipse(surf, (38, 60, 78), (16, 32, 64, 26))
        pygame.draw.ellipse(surf, (110, 108, 112), (36, 30, 24, 14))
        pygame.draw.line(surf, (140, 190, 220), (48, 34), (48, 14), 3)
        pygame.draw.circle(surf, (170, 210, 235), (48, 12), 4)
        anchor = (48, 50)
    else:
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surf, (200, 60, 200), (10, 10), 8)
        anchor = (10, 16)
    _cache[k] = (surf, anchor)
    return _cache[k]


# ------------------------------------------------------------- characters ---

CHAR_STYLES = {
    # body, jacket/torso, head/skin, accent
    'player':   {'body': (40, 46, 58),  'torso': (70, 90, 120), 'skin': (214, 178, 150), 'accent': (87, 199, 255)},
    'husk':     {'body': (62, 60, 58),  'torso': (84, 78, 70),  'skin': (170, 168, 150), 'accent': (120, 116, 104)},
    'riot':     {'body': (40, 42, 48),  'torso': (54, 58, 68),  'skin': (90, 94, 104),   'accent': (200, 170, 60)},
    'stalker':  {'body': (34, 34, 38),  'torso': (46, 44, 52),  'skin': (188, 160, 140), 'accent': (220, 70, 70)},
    'feral':    {'body': (70, 60, 50),  'torso': (88, 74, 58),  'skin': (88, 74, 58),    'accent': (230, 90, 60)},
    'drone':    {'body': (70, 74, 84),  'torso': (90, 96, 110), 'skin': (90, 96, 110),   'accent': (255, 90, 90)},
    'npc_maya': {'body': (52, 40, 58),  'torso': (140, 90, 60), 'skin': (190, 150, 124), 'accent': (255, 200, 110)},
    'npc_cart': {'body': (44, 50, 46),  'torso': (80, 100, 84), 'skin': (220, 190, 160), 'accent': (160, 230, 190)},
    'boss_warden':   {'body': (36, 38, 44), 'torso': (60, 64, 76), 'skin': (110, 116, 130), 'accent': (255, 170, 60), 'scale': 1.9},
    'boss_chorister': {'body': (60, 50, 70), 'torso': (96, 70, 110), 'skin': (200, 190, 210), 'accent': (190, 120, 255), 'scale': 1.55},
    'boss_archivist': {'body': (30, 40, 52), 'torso': (48, 70, 96), 'skin': (140, 200, 235), 'accent': (130, 230, 255), 'scale': 1.8},
}


def character(style_name, octant, frame=0):
    """Small 8-direction humanoid. frame 0 = idle, 1/2 = walk, 3 = attack."""
    k = _key('char', style_name, octant, frame)
    if k in _cache:
        return _cache[k]
    st = CHAR_STYLES[style_name]
    sc = st.get('scale', 1.0)
    w, h = int(40 * sc), int(58 * sc)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    foot = h - int(4 * sc)
    # shadow
    pygame.draw.ellipse(surf, (0, 0, 0, 80),
                        (cx - int(11 * sc), foot - int(4 * sc), int(22 * sc), int(8 * sc)))
    if style_name == 'feral':
        _draw_dog(surf, st, cx, foot, octant, frame, sc)
        _cache[k] = (surf, (cx, foot))
        return _cache[k]
    if style_name == 'drone':
        _draw_drone(surf, st, cx, foot, frame, sc)
        _cache[k] = (surf, (cx, foot))
        return _cache[k]

    ang = octant * math.pi / 4
    fx = math.cos(ang)            # screen-space facing
    lean = int(2 * sc) if frame == 3 else 0
    step = (1 if frame == 1 else -1 if frame == 2 else 0) * int(3 * sc)
    hipy = foot - int(18 * sc)
    # legs
    leg_c = st['body']
    pygame.draw.line(surf, leg_c, (cx - int(4 * sc), hipy), (cx - int(5 * sc) + step, foot), int(4 * sc))
    pygame.draw.line(surf, leg_c, (cx + int(4 * sc), hipy), (cx + int(5 * sc) - step, foot), int(4 * sc))
    # torso
    tw, th = int(17 * sc), int(20 * sc)
    torso_rect = pygame.Rect(cx - tw // 2 + lean, hipy - th, tw, th)
    pygame.draw.rect(surf, st['torso'], torso_rect, border_radius=int(5 * sc))
    pygame.draw.rect(surf, _shade(st['torso'], 0.7), torso_rect, 1, border_radius=int(5 * sc))
    # accent stripe
    pygame.draw.line(surf, st['accent'], (torso_rect.left + 3, torso_rect.top + 3),
                     (torso_rect.left + 3, torso_rect.bottom - 3), 2)
    # arms
    arm_c = _shade(st['torso'], 0.85)
    sh_y = hipy - th + int(4 * sc)
    if frame == 3:  # attack: leading arm extended toward facing
        ex = cx + int(fx * 16 * sc) + lean
        ey = sh_y + int(6 * sc)
        pygame.draw.line(surf, arm_c, (cx + lean, sh_y), (ex, ey), int(4 * sc))
        # weapon (pipe / machete)
        wx2 = cx + int(fx * 28 * sc) + lean
        pygame.draw.line(surf, (180, 184, 196), (ex, ey), (wx2, ey - int(3 * sc)), 3)
    else:
        sway = step // 2
        pygame.draw.line(surf, arm_c, (cx - tw // 2 + lean, sh_y), (cx - tw // 2 - int(2 * sc) + sway, hipy - int(2 * sc)), int(3 * sc))
        pygame.draw.line(surf, arm_c, (cx + tw // 2 + lean, sh_y), (cx + tw // 2 + int(2 * sc) - sway, hipy - int(2 * sc)), int(3 * sc))
        # sheathed weapon hint for player & stalker
        if style_name in ('player', 'stalker', 'boss_warden'):
            pygame.draw.line(surf, (150, 154, 166), (cx - tw // 2 + lean, sh_y + 2),
                             (cx - tw // 2 - int(6 * sc), sh_y - int(10 * sc)), 2)
    # head
    hr = int(6 * sc)
    hx = cx + int(fx * 2 * sc) + lean
    hy = hipy - th - hr + int(2 * sc)
    pygame.draw.circle(surf, st['skin'], (hx, hy), hr)
    # hair / helmet
    if style_name == 'riot' or style_name.startswith('boss_warden'):
        pygame.draw.circle(surf, _shade(st['torso'], 1.2), (hx, hy - 1), hr, 0,
                           draw_top_left=True, draw_top_right=True)
        pygame.draw.line(surf, st['accent'], (hx - hr + 2, hy), (hx + hr - 2, hy), 2)
    else:
        pygame.draw.circle(surf, _shade(st['body'], 1.3), (hx, hy - 2), hr - 1, 0,
                           draw_top_left=True, draw_top_right=True)
    # eye glint showing facing
    pygame.draw.circle(surf, st['accent'], (hx + int(fx * 3), hy), max(1, int(1.4 * sc)))
    _cache[k] = (surf, (cx, foot))
    return _cache[k]


def _draw_dog(surf, st, cx, foot, octant, frame, sc):
    ang = octant * math.pi / 4
    fx = math.cos(ang)
    bl = int(20 * sc)
    bx = cx - int(fx * bl / 2)
    by = foot - int(10 * sc)
    step = (2 if frame == 1 else -2 if frame == 2 else 0)
    pygame.draw.line(surf, st['body'], (bx - 5, by + 3), (bx - 6 + step, foot), 3)
    pygame.draw.line(surf, st['body'], (bx + 5, by + 3), (bx + 6 - step, foot), 3)
    pygame.draw.ellipse(surf, st['torso'], (bx - bl // 2, by - 6, bl, 12))
    hx = bx + int(fx * (bl // 2 + 4))
    hy = by - 4 if frame != 3 else by
    pygame.draw.circle(surf, st['torso'], (hx, hy), int(5 * sc))
    pygame.draw.circle(surf, st['accent'], (hx + int(fx * 3), hy), 2)
    # tail
    pygame.draw.line(surf, st['body'], (bx - int(fx * bl // 2), by - 4),
                     (bx - int(fx * (bl // 2 + 6)), by - 10), 2)


def _draw_drone(surf, st, cx, foot, frame, sc):
    hy = foot - int(34 * sc)
    pygame.draw.ellipse(surf, st['torso'], (cx - 11, hy - 6, 22, 13))
    pygame.draw.ellipse(surf, _shade(st['torso'], 0.7), (cx - 11, hy - 6, 22, 13), 1)
    rot = frame % 2
    for sx_ in (-13, 13):
        pygame.draw.line(surf, (140, 146, 158), (cx + sx_ - 6 + rot * 3, hy - 8),
                         (cx + sx_ + 6 - rot * 3, hy - 8), 2)
        pygame.draw.line(surf, (90, 96, 108), (cx + sx_, hy - 8), (cx + sx_, hy - 4), 2)
    pygame.draw.circle(surf, st['accent'], (cx, hy + 2), 3)


# ------------------------------------------------------------ misc visuals ---

def slash_arc(radius, color):
    k = _key('slash', radius, color)
    if k in _cache:
        return _cache[k]
    d = radius * 2
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    rect = surf.get_rect()
    for i, (w_, a) in enumerate([(6, 70), (3, 160)]):
        pygame.draw.arc(surf, (*color, a), rect.inflate(-i * 6, -i * 6), -0.7, 0.7, w_)
    _cache[k] = (surf, (radius, radius))
    return _cache[k]


def vignette():
    k = _key('vignette')
    if k in _cache:
        return _cache[k]
    from src.constants import WIDTH, HEIGHT
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(80):
        a = int(i * 1.1)
        pygame.draw.rect(surf, (0, 0, 5, a), (i * 4 - 320, i * 3 - 240, WIDTH - i * 8 + 640, HEIGHT - i * 6 + 480), 6)
    surf.fill((0, 0, 0, 0))
    # simpler: radial-ish darkening via corner rects
    import math as _m
    cx, cy = WIDTH / 2, HEIGHT / 2
    step = 16
    for x in range(0, WIDTH, step):
        for y in range(0, HEIGHT, step):
            d = _m.hypot(x - cx, y - cy) / _m.hypot(cx, cy)
            if d > 0.55:
                a = min(150, int((d - 0.55) * 260))
                pygame.draw.rect(surf, (4, 5, 10, a), (x, y, step, step))
    _cache[k] = surf
    return surf
