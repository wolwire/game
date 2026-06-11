"""Procedural asset library, production pass.

Ground is painted tile-by-tile into pre-rendered chunk surfaces (rich texture
is free at runtime). Props/buildings return (surface, (ax, ay)) where the
anchor is the pixel placed at the object's projected ground point.
"""
import math
import random
import pygame
from src.constants import TILE_W, TILE_H, HALF_W, HALF_H, CHUNK

_cache = {}


def _rand(seed):
    return random.Random(seed)


def sh(color, f):
    return (max(0, min(255, int(color[0] * f))),
            max(0, min(255, int(color[1] * f))),
            max(0, min(255, int(color[2] * f))))


def diamond(ox, oy, w=TILE_W, h=TILE_H):
    return [(ox + w // 2, oy), (ox + w, oy + h // 2),
            (ox + w // 2, oy + h), (ox, oy + h // 2)]


# =================================================================== ground
GROUND_COLORS = {
    'asphalt':  (94, 94, 100),
    'road':     (86, 87, 94),
    'sidewalk': (168, 162, 148),
    'plaza':    (162, 154, 158),
    'grass':    (84, 118, 54),
    'dirt':     (132, 108, 76),
    'water':    (48, 94, 140),
    'sand':     (192, 174, 136),
    'lot':      (114, 110, 106),
    'alley':    (96, 94, 98),
}

# darker / lighter mottling targets per terrain (AoE-style painterly ground)
GROUND_VAR = {
    'grass':    ((56, 92, 42), (122, 142, 62)),
    'asphalt':  ((80, 80, 87), (108, 108, 113)),
    'road':     ((72, 73, 80), (100, 101, 108)),
    'sidewalk': ((148, 142, 130), (186, 180, 164)),
    'plaza':    ((142, 134, 140), (180, 172, 174)),
    'dirt':     ((108, 86, 60), (156, 132, 94)),
    'water':    ((36, 78, 122), (66, 116, 162)),
    'sand':     ((170, 152, 116), (212, 196, 156)),
    'lot':      ((98, 94, 92), (130, 126, 120)),
    'alley':    ((82, 80, 86), (110, 108, 110)),
}


def _hashv(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 1446453) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return ((h ^ (h >> 16)) & 0xffff) / 65535.0


def vnoise(x, y, seed=0):
    """Smooth value noise — continuous across tiles, kills the grid look."""
    ix, iy = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = _hashv(ix, iy, seed)
    b = _hashv(ix + 1, iy, seed)
    c = _hashv(ix, iy + 1, seed)
    d = _hashv(ix + 1, iy + 1, seed)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def _mix(c0, c1, t):
    return (int(c0[0] + (c1[0] - c0[0]) * t),
            int(c0[1] + (c1[1] - c0[1]) * t),
            int(c0[2] + (c1[2] - c0[2]) * t))


def _noise_dots(surf, rng, pts, n, lo, hi, base):
    minx = min(p[0] for p in pts) + 4
    maxx = max(p[0] for p in pts) - 4
    cy = (pts[0][1] + pts[2][1]) // 2
    for _ in range(n):
        x = rng.randint(minx, maxx)
        y = cy + rng.randint(-5, 5)
        surf.set_at((x, y), sh(base, rng.uniform(lo, hi)))


def paint_tile(surf, ox, oy, kind, wx, wy, world=None):
    """Paint one ground tile: noise-blended sub-diamonds give organic,
    grid-free terrain in full daylight."""
    rng = _rand((wx * 73856093) ^ (wy * 19349663))
    base = GROUND_COLORS.get(kind, (60, 60, 60))
    dark, light = GROUND_VAR.get(kind, (sh(base, 0.85), sh(base, 1.15)))
    pts = diamond(ox, oy)
    pygame.draw.polygon(surf, base, pts)

    # 2x2 sub-diamonds colored by two octaves of continuous noise
    for a, b in ((0, 0), (0.5, 0), (0, 0.5), (0.5, 0.5)):
        n = vnoise((wx + a) * 0.55, (wy + b) * 0.55, 7) * 0.65 \
            + vnoise((wx + a) * 1.7, (wy + b) * 1.7, 23) * 0.35
        col = _mix(dark, light, max(0.0, min(1.0, n)))
        x0 = ox + 16 + (a - b) * 16 - 8
        y0 = oy + (a + b) * 8
        pygame.draw.polygon(surf, col, diamond(x0, y0, 16, 8))

    if kind == 'grass':
        for _ in range(7):
            x = ox + rng.randint(6, TILE_W - 8)
            y = oy + rng.randint(3, TILE_H - 3)
            c = sh((96, 130, 58), rng.uniform(0.7, 1.25))
            pygame.draw.line(surf, c, (x, y), (x + rng.randint(-1, 1), y - rng.randint(1, 3)))
        if rng.random() < 0.05:
            for _ in range(3):
                surf.set_at((ox + rng.randint(8, 24), oy + rng.randint(4, 12)),
                            rng.choice([(228, 216, 130), (216, 160, 180), (236, 236, 230)]))
    elif kind in ('asphalt', 'road', 'lot', 'alley'):
        if rng.random() < 0.10:  # crack
            x, y = ox + rng.randint(8, 24), oy + rng.randint(4, 12)
            for _ in range(3):
                nx, ny = x + rng.randint(-5, 5), y + rng.randint(-2, 2)
                pygame.draw.line(surf, sh(base, 0.7), (x, y), (nx, ny))
                x, y = nx, ny
        if kind in ('road', 'asphalt') and rng.random() < 0.04:  # oil stain
            pygame.draw.ellipse(surf, sh(base, 0.8),
                                (ox + rng.randint(6, 16), oy + rng.randint(3, 8),
                                 rng.randint(8, 14), rng.randint(4, 7)))
        if rng.random() < 0.03:  # puddle mirrors the sky
            px, py = ox + rng.randint(7, 15), oy + rng.randint(3, 8)
            pw, ph = rng.randint(9, 15), rng.randint(4, 7)
            pygame.draw.ellipse(surf, (124, 152, 184), (px, py, pw, ph))
            pygame.draw.ellipse(surf, (172, 196, 220), (px + 2, py + 1, pw - 4, 2))
    elif kind in ('sidewalk', 'plaza'):
        if (wx + wy) % 2 == 0:
            pygame.draw.line(surf, sh(base, 0.88), pts[0], pts[2])
        else:
            pygame.draw.line(surf, sh(base, 0.91), pts[3], pts[1])
        if rng.random() < 0.05:
            pygame.draw.line(surf, sh(base, 0.7), (ox + 10, oy + 6),
                             (ox + 10 + rng.randint(4, 9), oy + 6 + rng.randint(-2, 3)))
    elif kind == 'water':
        if rng.random() < 0.5:
            y = oy + rng.randint(4, 11)
            x = ox + rng.randint(6, 12)
            pygame.draw.line(surf, (150, 190, 220), (x, y), (x + rng.randint(5, 11), y))
    elif kind in ('dirt', 'sand'):
        _noise_dots(surf, rng, pts, 6, 0.85, 1.15, base)

    # neighbor-aware edges: curbs & shorelines
    if world is not None:
        def g(x, y):
            if 0 <= x < world.w and 0 <= y < world.h:
                return world.ground[y][x]
            return kind
        if kind == 'sidewalk':
            curb = sh(base, 1.22)
            curb_d = sh(base, 0.72)
            if g(wx + 1, wy) in ('road', 'asphalt'):   # SE edge
                pygame.draw.line(surf, curb, pts[0], pts[1], 2)
                pygame.draw.line(surf, curb_d, (pts[0][0] + 1, pts[0][1] + 2), (pts[1][0] - 1, pts[1][1] + 2), 1)
            if g(wx, wy + 1) in ('road', 'asphalt'):   # SW edge
                pygame.draw.line(surf, curb, pts[1], pts[2], 2)
            if g(wx - 1, wy) in ('road', 'asphalt'):
                pygame.draw.line(surf, curb, pts[2], pts[3], 2)
            if g(wx, wy - 1) in ('road', 'asphalt'):
                pygame.draw.line(surf, curb, pts[3], pts[0], 2)
        elif kind == 'water':
            foam = (196, 216, 230)
            if g(wx - 1, wy) not in ('water',):
                pygame.draw.line(surf, foam, pts[2], pts[3], 1)
            if g(wx, wy - 1) not in ('water',):
                pygame.draw.line(surf, foam, pts[3], pts[0], 1)
        elif kind == 'grass' and g(wx + 1, wy) in ('sidewalk', 'plaza', 'asphalt', 'road'):
            pygame.draw.line(surf, sh(base, 0.75), pts[0], pts[1], 1)


def paint_decal(surf, ox, oy, kind, wx, wy):
    rng = _rand((wx * 31 + wy * 57) & 0xffffff)
    cx, cy = ox + HALF_W, oy + HALF_H
    if kind == 'dash_x':
        pygame.draw.line(surf, (224, 218, 178), (cx - 7, cy - 3), (cx + 7, cy + 3), 2)
    elif kind == 'dash_y':
        pygame.draw.line(surf, (224, 218, 178), (cx + 7, cy - 3), (cx - 7, cy + 3), 2)
    elif kind == 'cross_x':   # crosswalk stripes for a road running along x
        pygame.draw.line(surf, (226, 224, 212), (cx - 8, cy - 4), (cx - 1, cy - 1), 3)
        pygame.draw.line(surf, (226, 224, 212), (cx + 1, cy + 1), (cx + 8, cy + 4), 3)
    elif kind == 'cross_y':
        pygame.draw.line(surf, (226, 224, 212), (cx + 8, cy - 4), (cx + 1, cy - 1), 3)
        pygame.draw.line(surf, (226, 224, 212), (cx - 1, cy + 1), (cx - 8, cy + 4), 3)
    elif kind == 'manhole':
        pygame.draw.ellipse(surf, (64, 64, 68), (cx - 6, cy - 3, 12, 6))
        pygame.draw.ellipse(surf, (110, 110, 114), (cx - 6, cy - 3, 12, 6), 1)
        pygame.draw.line(surf, (66, 66, 70), (cx - 3, cy), (cx + 3, cy), 1)
    elif kind == 'grime':
        for _ in range(5):
            surf.set_at((cx + rng.randint(-8, 8), cy + rng.randint(-4, 4)), (70, 70, 74))
    elif kind == 'leaf':
        for _ in range(4):
            surf.set_at((cx + rng.randint(-9, 9), cy + rng.randint(-4, 4)),
                        rng.choice([(96, 84, 40), (110, 70, 36)]))


def render_chunk(world, ccx, ccy):
    """Pre-render a CHUNK x CHUNK ground chunk. Returns (surf, blit_anchor)."""
    w = CHUNK * TILE_W
    h = CHUNK * TILE_H + 8
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    x0, y0 = ccx * CHUNK, ccy * CHUNK
    for j in range(CHUNK):
        for i in range(CHUNK):
            wx, wy = x0 + i, y0 + j
            if wx >= world.w or wy >= world.h:
                continue
            ox = (i - j) * HALF_W + (CHUNK - 1) * HALF_W
            oy = (i + j) * HALF_H
            kind = world.ground[wy][wx]
            paint_tile(surf, ox, oy, kind, wx, wy, world)
            dec = world.decals.get((wx, wy))
            # decals only belong on pavement — districts repaint terrain
            # over old roads, so stale markings must not bleed through
            if dec:
                if dec in ('dash_x', 'dash_y', 'cross_x', 'cross_y', 'manhole'):
                    ok = kind in ('road', 'asphalt')
                else:
                    ok = kind in ('road', 'asphalt', 'sidewalk', 'plaza', 'lot', 'alley')
                if ok:
                    paint_decal(surf, ox, oy, dec, wx, wy)
    # anchor: tile (x0,y0) top corner sits at local ((CHUNK-1)*HALF_W + HALF_W, 0)
    return surf, (CHUNK * HALF_W, 0)


# ================================================================ buildings
BUILDING_STYLES = {
    'brick':      {'wall': (164, 102, 82),  'win': (104, 128, 156), 'lit': (146, 174, 198), 'trim': (120, 76, 62)},
    'concrete':   {'wall': (178, 176, 178), 'win': (108, 132, 160), 'lit': (150, 178, 202), 'trim': (140, 138, 142)},
    'glass':      {'wall': (118, 140, 162), 'win': (130, 162, 192), 'lit': (170, 200, 224), 'trim': (90, 108, 128)},
    'shop':       {'wall': (172, 150, 158), 'win': (104, 128, 156), 'lit': (150, 176, 200), 'trim': (130, 110, 120)},
    'industrial': {'wall': (160, 144, 116), 'win': (96, 116, 138), 'lit': (140, 162, 184), 'trim': (118, 106, 86)},
    'house':      {'wall': (186, 152, 118), 'win': (106, 130, 158), 'lit': (152, 178, 202), 'trim': (140, 112, 88)},
    'tower':      {'wall': (108, 126, 152), 'win': (140, 172, 204), 'lit': (184, 212, 234), 'trim': (84, 98, 120)},
}
STORY_PX = 30

NEON_COLORS = [(255, 90, 120), (90, 220, 255), (255, 180, 70), (140, 255, 160), (200, 120, 255)]
NEON_WORDS = [4, 5, 3, 6]


def building(seed, fw, fh, stories, style):
    k = ('bld', seed, fw, fh, stories, style)
    if k in _cache:
        return _cache[k]
    rng = _rand(seed)
    st = BUILDING_STYLES[style]
    zh = stories * STORY_PX
    sw = (fw + fh) * HALF_W
    shh = (fw + fh) * HALF_H
    surf = pygame.Surface((sw + 4, shh + zh + 30), pygame.SRCALPHA)
    nx, ny = fh * HALF_W + 2, zh + 24
    N = (nx, ny)
    E = (nx + fw * HALF_W, ny + fw * HALF_H)
    S = (nx + (fw - fh) * HALF_W, ny + (fw + fh) * HALF_H)
    W = (nx - fh * HALF_W, ny + fh * HALF_H)
    Nt, Et, St, Wt = [(p[0], p[1] - zh) for p in (N, E, S, W)]

    wall = sh(st['wall'], rng.uniform(0.92, 1.06))
    left_c, right_c, top_c = sh(wall, 0.72), sh(wall, 0.96), sh(wall, 1.22)

    pygame.draw.polygon(surf, left_c, [Wt, St, S, W])
    pygame.draw.polygon(surf, right_c, [St, Et, E, S])

    # --- facade detailing helper -------------------------------------
    def face(p0, p1, ncols, fshade, face_id):
        """Detail the face whose top edge runs p0->p1 (ground edge below)."""
        axx, axy = p1[0] - p0[0], p1[1] - p0[1]
        col_w = abs(axx) / max(1, ncols)
        for s in range(stories):
            ytop = p0[1] + s * STORY_PX
            # floor band
            band = sh(wall, fshade * 0.92)
            pygame.draw.line(surf, band, (p0[0], ytop + axy * 0 + 1 + (axy / abs(axx)) * 0 if axx else ytop),
                             (p0[0], ytop), 1)
            for c in range(ncols):
                t0 = (c + 0.18) / ncols
                t1 = (c + 0.82) / ncols
                x0 = p0[0] + axx * t0
                x1 = p0[0] + axx * t1
                yb0 = p0[1] + axy * t0
                yb1 = p0[1] + axy * t1
                wy0 = yb0 + s * STORY_PX + 8
                wy1 = yb1 + s * STORY_PX + 8
                hgt = 13
                r = rng.random()
                if r < 0.18:
                    wcol = sh(st['lit'], fshade * 1.05)     # bright sky glint
                elif r < 0.24:
                    wcol = (52, 56, 66)                     # broken / dark interior
                else:
                    wcol = sh(st['win'], fshade)
                quad = [(x0, wy0), (x1, wy1), (x1, wy1 + hgt), (x0, wy0 + hgt)]
                pygame.draw.polygon(surf, wcol, quad)
                # frame + sill
                pygame.draw.polygon(surf, sh(wall, fshade * 0.7), quad, 1)
                pygame.draw.line(surf, sh(wall, fshade * 1.18),
                                 (x0, wy0 + hgt + 1), (x1, wy1 + hgt + 1), 1)
                if r < 0.18:  # diagonal sky glint across the pane
                    pygame.draw.line(surf, sh(wcol, 1.25), (x0 + 1, wy0 + hgt - 3), (x1 - 1, wy1 + 2), 1)
                if rng.random() < 0.06:  # cracked pane
                    pygame.draw.line(surf, (236, 240, 244), (x0 + 1, wy0 + 2), (x1 - 1, wy1 + hgt - 3), 1)
        # dirt streaks
        for _ in range(fw + fh):
            t = rng.random()
            x = p0[0] + axx * t
            y0_ = p0[1] + axy * t + rng.randint(0, zh // 2)
            streak = pygame.Surface((2, rng.randint(10, max(11, zh // 2))), pygame.SRCALPHA)
            streak.fill((40, 38, 36, 30))
            surf.blit(streak, (x, y0_))

    face(Wt, St, max(1, fw), 0.62, 0)
    face(St, Et, max(1, fh), 0.86, 1)

    # --- ground floor -------------------------------------------------
    if style in ('shop', 'brick') and stories >= 1:
        # storefront on SW face: big window, door, awning, neon sign
        gx0, gy0 = W[0] + 3, W[1] - 1
        gx1, gy1 = S[0] - 2, S[1] - 1
        mid = 0.55
        pygame.draw.polygon(surf, (26, 30, 40),
                            [(gx0, gy0 - 16), (gx0 + (gx1 - gx0) * mid, gy0 + (gy1 - gy0) * mid - 16),
                             (gx0 + (gx1 - gx0) * mid, gy0 + (gy1 - gy0) * mid - 2), (gx0, gy0 - 2)])
        pane = (64, 84, 104) if rng.random() < 0.5 else (40, 44, 56)
        pygame.draw.polygon(surf, pane,
                            [(gx0 + 2, gy0 - 14),
                             (gx0 + (gx1 - gx0) * mid - 2, gy0 + (gy1 - gy0) * mid - 14),
                             (gx0 + (gx1 - gx0) * mid - 2, gy0 + (gy1 - gy0) * mid - 4),
                             (gx0 + 2, gy0 - 4)])
        pygame.draw.line(surf, (130, 160, 190), (gx0 + 3, gy0 - 13),
                         (gx0 + (gx1 - gx0) * mid - 4, gy0 + (gy1 - gy0) * mid - 13), 1)
        # door
        dx0 = gx0 + (gx1 - gx0) * 0.7
        dy0 = gy0 + (gy1 - gy0) * 0.7
        pygame.draw.polygon(surf, (34, 30, 28),
                            [(dx0, dy0 - 15), (dx0 + 7, dy0 - 11.5), (dx0 + 7, dy0 + 1), (dx0, dy0 - 2)])
        # awning
        aw = rng.choice([(168, 60, 60), (60, 110, 150), (150, 120, 60), (80, 130, 80)])
        pygame.draw.polygon(surf, aw, [(gx0 - 1, gy0 - 17), (gx1, gy1 - 17),
                                       (gx1 + 4, gy1 - 12), (gx0 + 3, gy0 - 12)])
        for i in range(4):
            t0 = i / 4
            pygame.draw.line(surf, sh(aw, 0.7),
                             (gx0 - 1 + (gx1 - gx0 + 1) * t0 + 2, gy0 - 14 + (gy1 - gy0) * t0),
                             (gx0 + 3 + (gx1 - gx0 + 1) * t0, gy0 - 12 + (gy1 - gy0) * t0), 2)
        # neon sign above awning
        if style == 'shop':
            neon = rng.choice(NEON_COLORS)
            sx0 = gx0 + 3
            sy0 = gy0 - 27
            nchars = rng.choice(NEON_WORDS)
            bw = nchars * 7 + 6
            board = [(sx0, sy0), (sx0 + bw, sy0 + bw * 0.5), (sx0 + bw, sy0 + bw * 0.5 + 10), (sx0, sy0 + 10)]
            pygame.draw.polygon(surf, sh(neon, 0.55), board)
            pygame.draw.polygon(surf, sh(neon, 0.35), board, 1)
            for i in range(nchars):
                ch_x = sx0 + 4 + i * 7
                ch_y = sy0 + 2 + (4 + i * 7) * 0.5
                pygame.draw.rect(surf, sh(neon, 1.4), (ch_x, ch_y, 4, 6), 1)

    # fire escape on some brick/concrete buildings (SE face)
    if style in ('brick', 'concrete') and stories >= 3 and rng.random() < 0.6:
        fx = (St[0] + Et[0]) / 2
        fy = (St[1] + Et[1]) / 2
        rail = sh(wall, 0.45)
        for s in range(1, stories):
            y = fy + s * STORY_PX - STORY_PX // 2
            pygame.draw.line(surf, rail, (fx - 9, y), (fx + 9, y + 4), 2)
            pygame.draw.line(surf, rail, (fx - 9, y - 6), (fx + 9, y - 2), 1)
            pygame.draw.line(surf, rail, (fx - 9, y - 6), (fx - 9, y), 1)
            pygame.draw.line(surf, rail, (fx + 9, y - 2), (fx + 9, y + 4), 1)
            pygame.draw.line(surf, rail, (fx - 7, y), (fx + 5, y - STORY_PX + 2), 1)

    # --- roof ----------------------------------------------------------
    pygame.draw.polygon(surf, top_c, [Nt, Et, St, Wt])
    # parapet
    pygame.draw.lines(surf, sh(wall, 1.25), True, [Nt, Et, St, Wt], 2)
    pygame.draw.lines(surf, sh(wall, 0.4), False, [Wt, St, Et], 1)
    inner = [(Nt[0], Nt[1] + 3), (Et[0] - 5, Et[1]), (St[0], St[1] - 3), (Wt[0] + 5, Wt[1])]
    pygame.draw.polygon(surf, sh(top_c, 0.93), inner)
    # roof furniture
    def roof_pt(u, v):
        return (Nt[0] + (Et[0] - Nt[0]) * u + (Wt[0] - Nt[0]) * v,
                Nt[1] + (Et[1] - Nt[1]) * u + (Wt[1] - Nt[1]) * v)
    for _ in range(min(3, 1 + stories // 3)):
        u, v = rng.uniform(0.25, 0.75), rng.uniform(0.25, 0.75)
        bx, by = roof_pt(u, v)
        kind = rng.random()
        if kind < 0.5:  # AC unit
            pygame.draw.polygon(surf, sh(wall, 0.75), [(bx - 6, by - 1), (bx, by - 4), (bx + 6, by - 1), (bx, by + 2)])
            pygame.draw.polygon(surf, sh(wall, 0.55), [(bx - 6, by - 1), (bx, by + 2), (bx, by + 7), (bx - 6, by + 4)])
            pygame.draw.polygon(surf, sh(wall, 0.65), [(bx, by + 2), (bx + 6, by - 1), (bx + 6, by + 4), (bx, by + 7)])
            pygame.draw.ellipse(surf, sh(wall, 0.4), (bx - 4, by - 2, 8, 4))
        elif kind < 0.8:  # vent pipe
            pygame.draw.line(surf, sh(wall, 0.5), (bx, by), (bx, by - 8), 3)
            pygame.draw.line(surf, sh(wall, 0.7), (bx - 3, by - 8), (bx + 3, by - 8), 3)
        else:  # antenna
            pygame.draw.line(surf, (140, 144, 152), (bx, by), (bx, by - 16), 1)
            pygame.draw.line(surf, (140, 144, 152), (bx - 4, by - 10), (bx + 4, by - 13), 1)
    if style == 'brick' and stories >= 4 and rng.random() < 0.5:  # water tank
        bx, by = roof_pt(0.7, 0.3)
        pygame.draw.ellipse(surf, (60, 48, 40), (bx - 7, by - 18, 14, 6))
        pygame.draw.rect(surf, (74, 58, 48), (bx - 7, by - 15, 14, 12))
        pygame.draw.rect(surf, (60, 48, 40), (bx - 7, by - 15, 14, 12), 1)
        pygame.draw.polygon(surf, (86, 68, 56), [(bx - 8, by - 15), (bx, by - 22), (bx + 8, by - 15)])
    if style == 'tower':
        tipx, tipy = roof_pt(0.5, 0.5)
        pygame.draw.line(surf, (160, 170, 190), (tipx, tipy), (tipx, tipy - 34), 2)
        pygame.draw.circle(surf, (255, 90, 90), (int(tipx), int(tipy - 34)), 3)
        # helix logo on SE face top
        lx, ly = (St[0] + Et[0]) / 2, (St[1] + Et[1]) / 2 - zh + STORY_PX * 1.2
        for i in range(8):
            yy = ly + i * 3
            xx = math.sin(i * 0.9) * 5
            pygame.draw.circle(surf, (120, 220, 255), (int(lx + xx), int(yy)), 1)
            pygame.draw.circle(surf, (120, 220, 255), (int(lx - xx), int(yy)), 1)

    _cache[k] = (surf, (nx, ny))
    return _cache[k]


# ===================================================================== cars
CAR_COLORS = [(126, 44, 44), (52, 72, 112), (148, 140, 132), (58, 92, 62),
              (164, 122, 44), (88, 60, 100), (66, 68, 74), (140, 88, 40)]


def car(seed, axis):
    k = ('car', seed, axis)
    if k in _cache:
        return _cache[k]
    rng = _rand(seed)
    col = sh(rng.choice(CAR_COLORS), rng.uniform(0.75, 1.0))
    surf = pygame.Surface((96, 64), pygame.SRCALPHA)
    cx, cy = 48, 46
    L, Wd, Hb = 66, 26, 13
    if axis == 'x':
        lx, ly = L * 0.55, L * 0.275
        wxp, wyp = -Wd * 0.55, Wd * 0.275
    else:
        lx, ly = -L * 0.55, L * 0.275
        wxp, wyp = Wd * 0.55, Wd * 0.275
    ox, oy = cx - (lx + wxp) / 2, cy - (ly + wyp) / 2 - Hb

    def quad(px, py, dx1, dy1, dx2, dy2, color, width=0):
        pygame.draw.polygon(surf, color, [(px, py), (px + dx1, py + dy1),
                                          (px + dx1 + dx2, py + dy1 + dy2), (px + dx2, py + dy2)], width)
    # shadow
    spts = [(ox - 2, oy + Hb + 2), (ox + lx - 2, oy + ly + Hb + 2),
            (ox + lx + wxp - 2, oy + ly + wyp + Hb + 2), (ox + wxp - 2, oy + wyp + Hb + 2)]
    sh_s = pygame.Surface((96, 64), pygame.SRCALPHA)
    pygame.draw.polygon(sh_s, (0, 0, 0, 90), spts)
    surf.blit(sh_s, (0, 0))
    # wheels
    for t in (0.18, 0.82):
        for sgn in (0.1, 0.9):
            wx_ = ox + lx * t + wxp * sgn
            wy_ = oy + ly * t + wyp * sgn + Hb
            pygame.draw.ellipse(surf, (18, 18, 20), (wx_ - 4, wy_ - 2, 8, 6))
    # body
    quad(ox, oy, lx, ly, 0, Hb, sh(col, 0.78 if axis == 'x' else 0.6))
    quad(ox + lx, oy + ly, wxp, wyp, 0, Hb, sh(col, 0.6 if axis == 'x' else 0.78))
    quad(ox, oy, lx, ly, wxp, wyp, col)
    quad(ox, oy, lx, ly, wxp, wyp, sh(col, 0.5), 1)
    # hood/trunk shading
    quad(ox + lx * 0.78, oy + ly * 0.78, lx * 0.2, ly * 0.2, wxp, wyp, sh(col, 1.12))
    # cabin
    cab_t = 0.30
    cox, coy = ox + lx * cab_t + wxp * 0.12, oy + ly * cab_t + wyp * 0.12 - 9
    quad(cox, coy, lx * 0.40, ly * 0.40, 0, 9, (28, 36, 48))
    quad(cox + lx * 0.40, coy + ly * 0.40, wxp * 0.76, wyp * 0.76, 0, 9, (22, 28, 38))
    quad(cox, coy, lx * 0.40, ly * 0.40, wxp * 0.76, wyp * 0.76, sh(col, 1.2))
    # windshield glint
    pygame.draw.line(surf, (120, 150, 180),
                     (cox + lx * 0.4 + wxp * 0.1, coy + ly * 0.4 + wyp * 0.1 + 2),
                     (cox + lx * 0.4 + wxp * 0.6, coy + ly * 0.4 + wyp * 0.6 + 2), 2)
    # lights
    pygame.draw.circle(surf, (220, 210, 170), (int(ox + lx + wxp * 0.18), int(oy + ly + wyp * 0.18 + 4)), 2)
    pygame.draw.circle(surf, (220, 210, 170), (int(ox + lx + wxp * 0.82), int(oy + ly + wyp * 0.82 + 4)), 2)
    pygame.draw.circle(surf, (160, 50, 50), (int(ox + wxp * 0.2), int(oy + wyp * 0.2 + 5)), 2)
    # damage
    if rng.random() < 0.6:
        for _ in range(rng.randint(2, 5)):
            px = ox + lx * rng.random() + wxp * rng.random()
            py = oy + ly * rng.random() + wyp * rng.random()
            pygame.draw.circle(surf, sh(col, 0.45), (int(px), int(py)), rng.randint(1, 3))
    if rng.random() < 0.3:  # broken windshield
        pygame.draw.line(surf, (200, 210, 220), (cox + 4, coy + 4), (cox + 12, coy + 9), 1)
    _cache[k] = (surf, (cx, cy + 8))
    return _cache[k]


# ==================================================================== props
def prop(kind, variant=0):
    k = ('prop', kind, variant)
    if k in _cache:
        return _cache[k]
    rng = _rand(hash(k) & 0xffffffff)
    if kind == 'lamppost':
        surf = pygame.Surface((46, 96), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (14, 86, 18, 7))
        pygame.draw.line(surf, (52, 56, 62), (23, 89), (23, 16), 3)
        pygame.draw.line(surf, (74, 78, 86), (22, 89), (22, 16), 1)
        pygame.draw.line(surf, (52, 56, 62), (23, 16), (38, 21), 3)
        pygame.draw.rect(surf, (40, 42, 48), (35, 18, 8, 5), border_radius=2)
        pygame.draw.ellipse(surf, (255, 214, 140), (36, 21, 6, 4))
        anchor = (23, 89)
    elif kind == 'traffic_light':
        surf = pygame.Surface((30, 84), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (8, 76, 16, 6))
        pygame.draw.line(surf, (48, 50, 56), (15, 79), (15, 10), 3)
        pygame.draw.rect(surf, (34, 36, 40), (9, 5, 12, 28), border_radius=3)
        pygame.draw.rect(surf, (20, 22, 26), (9, 5, 12, 28), 1, border_radius=3)
        pygame.draw.circle(surf, (170, 56, 56), (15, 11), 3)
        pygame.draw.circle(surf, (70, 62, 30), (15, 19), 3)
        pygame.draw.circle(surf, (40, 80, 46), (15, 27), 3)
        anchor = (15, 79)
    elif kind == 'hydrant':
        surf = pygame.Surface((20, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (4, 20, 12, 5))
        pygame.draw.rect(surf, (152, 50, 44), (7, 7, 7, 15), border_radius=3)
        pygame.draw.rect(surf, (108, 36, 32), (7, 7, 7, 15), 1, border_radius=3)
        pygame.draw.circle(surf, (172, 64, 54), (10, 7), 4)
        pygame.draw.rect(surf, (120, 40, 36), (3, 11, 14, 4), border_radius=2)
        pygame.draw.line(surf, (210, 120, 110), (8, 9), (8, 18), 1)
        anchor = (10, 23)
    elif kind == 'dumpster':
        surf = pygame.Surface((52, 42), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (6, 32, 42, 9))
        pygame.draw.polygon(surf, (36, 70, 50), [(6, 36), (28, 25), (48, 35), (26, 46)])
        pygame.draw.polygon(surf, (30, 58, 42), [(6, 36), (6, 22), (28, 11), (28, 25)])
        pygame.draw.polygon(surf, (44, 84, 60), [(28, 25), (28, 11), (48, 21), (48, 35)])
        pygame.draw.polygon(surf, (56, 102, 74), [(6, 22), (28, 11), (48, 21), (26, 32)])
        pygame.draw.line(surf, (24, 46, 34), (6, 29), (28, 18), 1)
        pygame.draw.line(surf, (70, 120, 90), (10, 21), (24, 14), 2)  # lid line
        anchor = (27, 40)
    elif kind == 'bench':
        surf = pygame.Surface((44, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (5, 21, 34, 6))
        pygame.draw.polygon(surf, (104, 76, 50), [(5, 20), (26, 10), (39, 16), (18, 26)])
        pygame.draw.line(surf, (124, 92, 62), (7, 20), (27, 11), 2)
        pygame.draw.polygon(surf, (80, 58, 38), [(5, 20), (5, 24), (18, 30), (18, 26)])
        pygame.draw.polygon(surf, (88, 64, 42), [(18, 26), (39, 16), (39, 20), (18, 30)])
        pygame.draw.line(surf, (60, 44, 30), (9, 24), (9, 28), 2)
        pygame.draw.line(surf, (60, 44, 30), (34, 19), (34, 23), 2)
        anchor = (22, 26)
    elif kind == 'barricade':
        surf = pygame.Surface((46, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (5, 24, 36, 7))
        pygame.draw.polygon(surf, (172, 116, 44), [(7, 23), (25, 14), (39, 21), (21, 30)])
        pygame.draw.polygon(surf, (140, 92, 34), [(7, 23), (7, 19), (25, 10), (25, 14)])
        for i in range(3):
            pygame.draw.line(surf, (224, 224, 228), (11 + i * 9, 21 - i * 3), (15 + i * 9, 26 - i * 3), 3)
        pygame.draw.line(surf, (110, 110, 116), (9, 23), (9, 29), 2)
        pygame.draw.line(surf, (110, 110, 116), (37, 20), (37, 26), 2)
        anchor = (23, 28)
    elif kind == 'tree':
        h = 64 + variant % 3 * 10
        surf = pygame.Surface((56, h + 14), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (16, h, 24, 9))
        pygame.draw.line(surf, (66, 50, 36), (28, h + 4), (28, h - 24), 4)
        pygame.draw.line(surf, (82, 62, 44), (27, h + 4), (27, h - 24), 1)
        pygame.draw.line(surf, (66, 50, 36), (28, h - 18), (20, h - 28), 2)
        pygame.draw.line(surf, (66, 50, 36), (28, h - 22), (36, h - 32), 2)
        base_c = (46, 76, 42) if variant % 2 == 0 else (54, 82, 40)
        for i, (r, yo, xo) in enumerate([(16, -34, -4), (14, -44, 6), (13, -52, -3), (9, -60, 2)]):
            c = sh(base_c, 0.85 + i * 0.13)
            pygame.draw.circle(surf, c, (28 + xo + rng.randint(-2, 2), h + yo), r)
        # highlight clumps
        pygame.draw.circle(surf, sh(base_c, 1.45), (34, h - 52), 5)
        pygame.draw.circle(surf, sh(base_c, 1.45), (22, h - 40), 4)
        anchor = (28, h + 4)
    elif kind == 'dead_tree':
        surf = pygame.Surface((44, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (12, 54, 20, 8))
        x, y = 22, 58
        pygame.draw.line(surf, (62, 52, 44), (x, y), (x - 2, y - 28), 4)
        pygame.draw.line(surf, (74, 62, 52), (x - 1, y), (x - 3, y - 28), 1)
        pygame.draw.line(surf, (62, 52, 44), (x - 2, y - 28), (x - 12, y - 42), 2)
        pygame.draw.line(surf, (62, 52, 44), (x - 2, y - 28), (x + 8, y - 46), 2)
        pygame.draw.line(surf, (56, 48, 40), (x + 8, y - 46), (x + 14, y - 52), 1)
        pygame.draw.line(surf, (56, 48, 40), (x - 12, y - 42), (x - 16, y - 50), 1)
        anchor = (22, 58)
    elif kind == 'bus_stop':
        surf = pygame.Surface((66, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (8, 50, 50, 9))
        pygame.draw.polygon(surf, (46, 54, 66), [(8, 22), (38, 7), (58, 17), (28, 32)])
        pygame.draw.polygon(surf, (60, 70, 84), [(8, 22), (38, 7), (58, 17), (28, 32)], 1)
        pygame.draw.line(surf, (84, 90, 100), (10, 23), (10, 52), 3)
        pygame.draw.line(surf, (84, 90, 100), (56, 18), (56, 47), 3)
        pygame.draw.polygon(surf, (66, 104, 134, 84), [(11, 26), (28, 35), (28, 50), (11, 41)])
        pygame.draw.line(surf, (110, 150, 180), (12, 27), (27, 35), 1)
        # bench inside
        pygame.draw.line(surf, (96, 76, 52), (32, 40), (50, 31), 3)
        anchor = (33, 54)
    elif kind == 'container':
        # cargo container, 2 tiles long
        cols = [(120, 60, 50), (54, 86, 110), (110, 96, 44), (70, 100, 70)]
        col = cols[variant % len(cols)]
        surf = pygame.Surface((76, 52), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), (6, 38, 64, 12))
        L, Wd, Hb = 56, 22, 20
        ox, oy = 12, 36 - Hb
        lx, ly = L * 0.55, L * 0.275
        wxp, wyp = -Wd * 0.55, Wd * 0.275
        ox -= wxp
        pygame.draw.polygon(surf, sh(col, 0.7), [(ox, oy), (ox + lx, oy + ly), (ox + lx, oy + ly + Hb), (ox, oy + Hb)])
        pygame.draw.polygon(surf, sh(col, 0.5), [(ox + lx, oy + ly), (ox + lx + wxp, oy + ly + wyp),
                                                 (ox + lx + wxp, oy + ly + wyp + Hb), (ox + lx, oy + ly + Hb)])
        pygame.draw.polygon(surf, col, [(ox, oy), (ox + lx, oy + ly), (ox + lx + wxp, oy + ly + wyp), (ox + wxp, oy + wyp)])
        for i in range(5):  # corrugation
            t = (i + 0.5) / 5
            pygame.draw.line(surf, sh(col, 0.58), (ox + lx * t, oy + ly * t + 1), (ox + lx * t, oy + ly * t + Hb - 1), 1)
        pygame.draw.polygon(surf, sh(col, 0.4), [(ox, oy), (ox + lx, oy + ly), (ox + lx + wxp, oy + ly + wyp), (ox + wxp, oy + wyp)], 1)
        anchor = (38, 44)
    elif kind == 'crate':
        surf = pygame.Surface((36, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (5, 25, 26, 8))
        pygame.draw.polygon(surf, (104, 84, 56), [(5, 27), (18, 21), (31, 27), (18, 33)])
        pygame.draw.polygon(surf, (88, 70, 46), [(5, 27), (5, 16), (18, 10), (18, 21)])
        pygame.draw.polygon(surf, (116, 92, 62), [(18, 21), (18, 10), (31, 16), (31, 27)])
        pygame.draw.polygon(surf, (126, 102, 70), [(5, 16), (18, 10), (31, 16), (18, 22)])
        pygame.draw.line(surf, (70, 56, 38), (5, 16), (18, 22), 1)
        pygame.draw.line(surf, (70, 56, 38), (31, 16), (18, 22), 1)
        anchor = (18, 30)
    elif kind == 'debris':
        surf = pygame.Surface((36, 22), pygame.SRCALPHA)
        for _ in range(6):
            x, y = rng.randint(5, 28), rng.randint(7, 17)
            c = sh((86, 80, 72), rng.uniform(0.6, 1.2))
            pygame.draw.polygon(surf, c, [(x, y), (x + 5, y + 2), (x + 3, y + 4), (x - 1, y + 2)])
        if rng.random() < 0.5:
            pygame.draw.line(surf, (100, 70, 40), (8, 12), (20, 16), 2)
        anchor = (18, 15)
    elif kind == 'beacon':
        surf = pygame.Surface((84, 130), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (30, 60, 80, 100), (18, 110, 48, 16))
        # lattice tower
        bx = 42
        for i, (w0, w1, y0, y1) in enumerate([(16, 12, 118, 92), (12, 9, 92, 66), (9, 6, 66, 42)]):
            pygame.draw.line(surf, (84, 92, 104), (bx - w0, y0), (bx - w1, y1), 2)
            pygame.draw.line(surf, (64, 72, 84), (bx + w0, y0), (bx + w1, y1), 2)
            pygame.draw.line(surf, (74, 82, 94), (bx - w0, y0), (bx + w1, y1), 1)
            pygame.draw.line(surf, (74, 82, 94), (bx + w0, y0), (bx - w1, y1), 1)
            pygame.draw.line(surf, (90, 98, 110), (bx - w0, y0), (bx + w0, y0), 2)
        pygame.draw.line(surf, (90, 98, 110), (bx - 6, 42), (bx + 6, 42), 2)
        pygame.draw.line(surf, (100, 108, 120), (bx, 42), (bx, 22), 3)
        # dish
        pygame.draw.ellipse(surf, (110, 118, 130), (bx + 2, 50, 12, 8))
        pygame.draw.ellipse(surf, (140, 148, 160), (bx + 4, 51, 8, 5))
        # beacon lamp + glow
        pygame.draw.circle(surf, (160, 235, 255), (bx, 20), 5)
        pygame.draw.circle(surf, (235, 250, 255), (bx, 20), 2)
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        for r, a in [(34, 22), (22, 40), (11, 80)]:
            pygame.draw.circle(glow, (110, 215, 255, a), (35, 35), r)
        surf.blit(glow, (bx - 35, -14))
        anchor = (42, 118)
    elif kind == 'shard_echo':
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        for r, a in [(18, 30), (11, 64), (6, 120)]:
            pygame.draw.circle(surf, (150, 210, 255, a), (20, 24), r)
        pygame.draw.circle(surf, (225, 242, 255), (20, 24), 3)
        for i in range(5):
            a = i * 1.25664
            pygame.draw.line(surf, (190, 225, 255),
                             (20 + math.cos(a) * 6, 24 + math.sin(a) * 3),
                             (20 + math.cos(a) * 11, 24 + math.sin(a) * 5.5), 1)
        anchor = (20, 28)
    elif kind == 'lore':
        surf = pygame.Surface((28, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (6, 25, 16, 6))
        glow = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 230, 140, 46), (16, 16), 14)
        surf.blit(glow, (-2, 4))
        pygame.draw.polygon(surf, (214, 204, 174), [(8, 26), (13, 11), (21, 14), (16, 29)])
        pygame.draw.polygon(surf, (160, 150, 120), [(8, 26), (13, 11), (21, 14), (16, 29)], 1)
        for i in range(3):
            pygame.draw.line(surf, (124, 114, 94), (12 - i, 15 + i * 3.4), (18 - i, 17 + i * 3.4), 1)
        anchor = (14, 28)
    elif kind == 'cache':
        # supply duffel on a pallet, glowing faintly amber
        surf = pygame.Surface((44, 36), pygame.SRCALPHA)
        glow = pygame.Surface((44, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 190, 90, 36), glow.get_rect())
        surf.blit(glow, (0, 8))
        pygame.draw.polygon(surf, (96, 76, 50), [(6, 28), (22, 20), (38, 28), (22, 36)])
        pygame.draw.ellipse(surf, (84, 96, 70), (10, 13, 24, 13))
        pygame.draw.ellipse(surf, (64, 74, 54), (10, 13, 24, 13), 1)
        pygame.draw.line(surf, (160, 150, 110), (14, 19), (30, 19), 2)
        pygame.draw.circle(surf, (255, 200, 110), (22, 14), 2)
        anchor = (22, 33)
    elif kind == 'weapon_pickup':
        surf = pygame.Surface((40, 36), pygame.SRCALPHA)
        glow = pygame.Surface((40, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (120, 215, 255, 44), glow.get_rect())
        surf.blit(glow, (0, 10))
        # weapon on a tarp
        pygame.draw.polygon(surf, (52, 58, 70), [(6, 26), (20, 19), (34, 26), (20, 33)])
        pygame.draw.line(surf, (190, 196, 208), (12, 27), (28, 19), 3)
        pygame.draw.line(surf, (120, 124, 136), (13, 28), (29, 20), 1)
        pygame.draw.line(surf, (110, 80, 50), (12, 27), (16, 25), 4)
        anchor = (20, 31)
    elif kind == 'fountain':
        surf = pygame.Surface((110, 72), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (74, 72, 80), (8, 30, 94, 40))
        pygame.draw.ellipse(surf, (96, 94, 100), (8, 26, 94, 40))
        pygame.draw.ellipse(surf, (30, 52, 72), (18, 31, 74, 30))
        pygame.draw.ellipse(surf, (58, 86, 110), (24, 34, 62, 22), 1)
        pygame.draw.ellipse(surf, (104, 102, 108), (42, 28, 26, 14))
        pygame.draw.ellipse(surf, (84, 82, 88), (42, 32, 26, 12))
        pygame.draw.line(surf, (140, 186, 216), (55, 32), (55, 10), 3)
        pygame.draw.circle(surf, (180, 215, 240), (55, 8), 4)
        for a in range(5):
            t = a / 4.0
            pygame.draw.line(surf, (120, 170, 200), (55, 12),
                             (45 + t * 20, 28), 1)
        anchor = (55, 54)
    elif kind == 'phonebooth':
        surf = pygame.Surface((30, 58), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (6, 50, 18, 7))
        pygame.draw.rect(surf, (40, 60, 90), (8, 12, 14, 41), border_radius=2)
        pygame.draw.rect(surf, (28, 42, 64), (8, 12, 14, 41), 2, border_radius=2)
        pygame.draw.rect(surf, (130, 170, 210, 110), (11, 17, 8, 22))
        pygame.draw.rect(surf, (60, 86, 120), (8, 8, 14, 6), border_radius=2)
        anchor = (15, 54)
    elif kind == 'trash':
        surf = pygame.Surface((20, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 70), (3, 20, 14, 5))
        pygame.draw.rect(surf, (64, 68, 74), (5, 7, 10, 15), border_radius=2)
        pygame.draw.rect(surf, (44, 48, 54), (5, 7, 10, 15), 1, border_radius=2)
        pygame.draw.line(surf, (84, 88, 94), (5, 10), (15, 10), 1)
        pygame.draw.ellipse(surf, (38, 40, 44), (5, 5, 10, 5))
        anchor = (10, 23)
    else:
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surf, (200, 60, 200), (10, 10), 8)
        anchor = (10, 16)
    _cache[k] = (surf, anchor)
    return _cache[k]


# ================================================================= lighting
def light_sprite(radius, color):
    """Radial gradient for additive blending onto the lightmap (RGB only —
    intensity is baked into the color, alpha is ignored by BLEND_RGB_ADD)."""
    k = ('light', radius, color)
    if k in _cache:
        return _cache[k]
    d = radius * 2
    surf = pygame.Surface((d, d))
    steps = 12
    for i in range(steps, 0, -1):
        f = i / steps                       # 1 at rim, 1/steps at core
        inten = ((steps - i + 1) / steps) ** 1.8
        c = (min(255, int(color[0] * inten)), min(255, int(color[1] * inten)),
             min(255, int(color[2] * inten)))
        pygame.draw.circle(surf, c, (radius, radius), int(radius * f))
    _cache[k] = surf
    return surf


def vignette():
    k = ('vignette',)
    if k in _cache:
        return _cache[k]
    from src.constants import WIDTH, HEIGHT
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    cx, cy = WIDTH / 2, HEIGHT / 2
    step = 8
    maxd = math.hypot(cx, cy)
    for x in range(0, WIDTH, step):
        for y in range(0, HEIGHT, step):
            d = math.hypot(x - cx, y - cy) / maxd
            if d > 0.55:
                a = min(120, int((d - 0.55) * 230))
                pygame.draw.rect(surf, (3, 4, 9, a), (x, y, step, step))
    _cache[k] = surf
    return surf
