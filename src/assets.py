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
            pygame.draw.line(surf, sh(base, 0.94), pts[0], pts[2])
        else:
            pygame.draw.line(surf, sh(base, 0.96), pts[3], pts[1])
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
    # wall plaster/stone, window glass, trim stone, roof tiles, timber/detail
    'brick':      {'wall': (172, 116, 88),  'win': (96, 120, 148),  'trim': (212, 196, 168),
                   'roof': (164, 82, 56),  'timber': (118, 78, 58), 'masonry': 'brick'},
    'concrete':   {'wall': (190, 184, 170), 'win': (104, 130, 158), 'trim': (216, 210, 196),
                   'roof': (142, 130, 118), 'timber': (140, 132, 118), 'masonry': 'stone'},
    'glass':      {'wall': (132, 152, 172), 'win': (138, 170, 200), 'trim': (170, 186, 202),
                   'roof': (110, 124, 140), 'timber': (96, 110, 126), 'masonry': 'panel'},
    'shop':       {'wall': (204, 176, 142), 'win': (98, 124, 152),  'trim': (228, 212, 184),
                   'roof': (152, 74, 52),  'timber': (122, 86, 60), 'masonry': 'plaster'},
    'industrial': {'wall': (176, 158, 124), 'win': (92, 112, 134),  'trim': (204, 190, 158),
                   'roof': (124, 128, 134), 'timber': (110, 96, 72), 'masonry': 'stone'},
    'house':      {'wall': (214, 192, 156), 'win': (100, 126, 154), 'trim': (230, 216, 188),
                   'roof': (170, 88, 60),  'timber': (112, 82, 58), 'masonry': 'plaster'},
    'tower':      {'wall': (124, 142, 164), 'win': (146, 178, 208), 'trim': (168, 184, 202),
                   'roof': (96, 110, 128), 'timber': (90, 104, 122), 'masonry': 'panel'},
}
STORY_PX = 26
ROOF_H = 22

BANNER_COLORS = [(64, 96, 170), (170, 64, 64), (74, 130, 74), (160, 120, 50), (110, 70, 140)]
AWNING_COLORS = [(168, 60, 60), (60, 104, 150), (150, 118, 56), (84, 128, 84)]
NEON_COLORS = [(255, 90, 120), (90, 220, 255), (255, 180, 70), (140, 255, 160), (200, 120, 255)]


def _w2px(wx, wy, z=0.0):
    """Local world offset (tiles) -> local pixel offset."""
    return (wx - wy) * HALF_W, (wx + wy) * HALF_H - z


def _wall_face(surf, p0, p1, h, color, st, rng, stories, face_shade, win=True,
               arcade=False):
    """One wall face: top edge runs p0->p1 (both at wall-top height); the wall
    extends down by h px. Painted with masonry, plinth, windows."""
    axx, axy = p1[0] - p0[0], p1[1] - p0[1]
    g0 = (p0[0], p0[1] + h)
    g1 = (p1[0], p1[1] + h)
    col = sh(color, face_shade)
    pygame.draw.polygon(surf, col, [p0, p1, g1, g0])

    # masonry coursing
    kind = st['masonry']
    course = 6 if kind == 'brick' else 8
    line_c = sh(col, 0.88)
    for cy in range(course, h - 3, course):
        pygame.draw.line(surf, line_c, (p0[0], p0[1] + cy), (p1[0], p1[1] + cy), 1)
        if kind in ('brick', 'stone'):
            # staggered vertical joints
            n = max(2, int(abs(axx) / 9))
            off = (cy // course) % 2 * 0.5
            for j in range(n):
                t = (j + 0.5 + off) / n
                if t >= 1:
                    continue
                jx = p0[0] + axx * t
                jy = p0[1] + axy * t + cy
                pygame.draw.line(surf, line_c, (jx, jy - course + 2), (jx, jy - 1), 1)
    if kind == 'plaster':
        # timber frame: corner posts + diagonal brace
        tc = st['timber']
        pygame.draw.line(surf, tc, (p0[0] + 1, p0[1]), (g0[0] + 1, g0[1]), 2)
        pygame.draw.line(surf, tc, (p1[0] - 1, p1[1]), (g1[0] - 1, g1[1]), 2)
        for s in range(stories):
            yy = s * STORY_PX
            pygame.draw.line(surf, tc, (p0[0], p0[1] + yy + STORY_PX - 1),
                             (p1[0], p1[1] + yy + STORY_PX - 1), 2)
    if kind == 'panel':
        n = max(2, int(abs(axx) / 10))
        for j in range(1, n):
            t = j / n
            jx, jy = p0[0] + axx * t, p0[1] + axy * t
            pygame.draw.line(surf, sh(col, 0.92), (jx, jy), (jx, jy + h), 1)

    # plinth (stone base)
    pygame.draw.polygon(surf, sh(st['trim'], face_shade * 0.78),
                        [(g0[0], g0[1] - 6), (g1[0], g1[1] - 6), g1, g0])
    pygame.draw.line(surf, sh(st['trim'], face_shade * 0.95),
                     (g0[0], g0[1] - 6), (g1[0], g1[1] - 6), 1)

    # speckle weathering
    for _ in range(int(abs(axx) * h / 260)):
        t = rng.random()
        sx_ = p0[0] + axx * t
        sy_ = p0[1] + axy * t + rng.uniform(2, h - 7)
        surf.set_at((int(sx_), int(sy_)), sh(col, rng.uniform(0.82, 1.14)))

    if not win:
        return

    # arched windows per story/column
    ncols = max(1, int(abs(axx) / 22))
    for s in range(stories):
        for c in range(ncols):
            t0 = (c + 0.30) / ncols
            t1 = (c + 0.70) / ncols
            x0 = p0[0] + axx * t0
            x1 = p0[0] + axx * t1
            ymid0 = p0[1] + axy * t0 + s * STORY_PX + 8
            ymid1 = p0[1] + axy * t1 + s * STORY_PX + 8
            wgt = 11
            if arcade and s == stories - 1:   # ground floor arcade arch
                ay0 = p0[1] + axy * t0 + s * STORY_PX + 5
                ay1 = p0[1] + axy * t1 + s * STORY_PX + 5
                ah = h - (s * STORY_PX) - 11
                pygame.draw.polygon(surf, (52, 50, 56),
                                    [(x0, ay0 + 4), (x1, ay1 + 4), (x1, ay1 + ah), (x0, ay0 + ah)])
                pygame.draw.circle(surf, (52, 50, 56),
                                   (int((x0 + x1) / 2), int((ay0 + ay1) / 2 + 5)), int((x1 - x0) / 2))
                pygame.draw.arc(surf, sh(st['trim'], face_shade),
                                (x0 - 1, ay0 - 1, (x1 - x0) + 2, (x1 - x0) + 2), 0, 3.3, 2)
                continue
            wcol = sh(st['win'], face_shade * rng.uniform(0.9, 1.1))
            quad = [(x0, ymid0), (x1, ymid1), (x1, ymid1 + wgt), (x0, ymid0 + wgt)]
            # arch top
            pygame.draw.circle(surf, wcol, (int((x0 + x1) / 2), int((ymid0 + ymid1) / 2 + 1)),
                               max(2, int((x1 - x0) / 2)))
            pygame.draw.polygon(surf, wcol, quad)
            # stone trim + sill
            trim = sh(st['trim'], face_shade)
            pygame.draw.arc(surf, trim, (x0 - 1, ymid0 - (x1 - x0) / 2,
                                         (x1 - x0) + 2, (x1 - x0) + 2), 0, 3.4, 1)
            pygame.draw.line(surf, trim, (x0 - 1, ymid0 + wgt + 1), (x1 + 1, ymid1 + wgt + 1), 2)
            pygame.draw.line(surf, sh(wcol, 1.3), (x0 + 1, ymid0 + wgt - 3), (x1 - 1, ymid1 + 1), 1)
            if rng.random() < 0.18:  # shutter / dark pane
                pygame.draw.polygon(surf, (60, 62, 70), quad)


def _roof_hipped(surf, Nt, Et, St, Wt, fw, fh, st, rng, gabled=False):
    """Tiled sloped roof over wall-top diamond Nt/Et/St/Wt."""
    roof = st['roof']
    rh = ROOF_H + min(fw, fh)
    # eave overhang
    Nt = (Nt[0], Nt[1] - 2)
    Et = (Et[0] + 5, Et[1] + 1)
    St = (St[0], St[1] + 4)
    Wt = (Wt[0] - 5, Wt[1] + 1)
    if gabled or fw == fh:
        inset = 0 if gabled else None
    # ridge endpoints
    if fw >= fh:
        a0, a1 = (0 if gabled else fh / 2), (fw if gabled else fw - fh / 2)
        RA = _w2px(a0, fh / 2, 0)
        RB = _w2px(a1, fh / 2, 0)
    else:
        a0, a1 = (0 if gabled else fw / 2), (fh if gabled else fh - fw / 2)
        RA = _w2px(fw / 2, a0, 0)
        RB = _w2px(fw / 2, a1, 0)
    base = _w2px(0, 0, 0)
    RA = (Nt[0] + RA[0] - base[0] + 0, Nt[1] + RA[1] - base[1] - rh + 2)
    RB = (Nt[0] + RB[0] - base[0] + 0, Nt[1] + RB[1] - base[1] - rh + 2)
    if RB[0] < RA[0]:
        RA, RB = RB, RA

    def tiled_face(eave0, eave1, r0, r1, shade):
        pygame.draw.polygon(surf, sh(roof, shade), [eave0, eave1, r1, r0])
        rows = 5
        for i in range(1, rows):
            t = i / rows
            q0 = (eave0[0] + (r0[0] - eave0[0]) * t, eave0[1] + (r0[1] - eave0[1]) * t)
            q1 = (eave1[0] + (r1[0] - eave1[0]) * t, eave1[1] + (r1[1] - eave1[1]) * t)
            pygame.draw.line(surf, sh(roof, shade * (0.82 + 0.07 * (i % 2))), q0, q1, 1)
        # scalloped eave edge
        seg = max(3, int(math.hypot(eave1[0] - eave0[0], eave1[1] - eave0[1]) / 7))
        for i in range(seg):
            t = (i + 0.5) / seg
            ex = eave0[0] + (eave1[0] - eave0[0]) * t
            ey = eave0[1] + (eave1[1] - eave0[1]) * t
            pygame.draw.circle(surf, sh(roof, shade * 0.75), (int(ex), int(ey)), 2, 1)
        pygame.draw.line(surf, sh(roof, shade * 1.25), eave0, eave1, 1)

    if fw >= fh:
        # SW slope (Wt->St eave) is in shadow side w/ our NE sun
        tiled_face(Wt, St, RA, RB, 0.84)
        if gabled:
            # gable wall triangle on the E end
            apexE = (RB[0], RB[1])
            pygame.draw.polygon(surf, sh(st['wall'], 1.02), [St, Et, apexE])
            pygame.draw.polygon(surf, sh(st['timber'], 1.0), [St, Et, apexE], 1)
            pygame.draw.circle(surf, sh(st['win'], 0.9),
                               (int((St[0] + Et[0] + apexE[0]) / 3), int((St[1] + Et[1] + apexE[1]) / 3)), 2)
        else:
            tiled_face(St, Et, RB, RB, 1.04)   # SE hip triangle
    else:
        tiled_face(St, Et, RA, RB, 1.04)
        if gabled:
            apexS = (RB[0], RB[1]) if RB[1] > RA[1] else (RA[0], RA[1])
            pygame.draw.polygon(surf, sh(st['wall'], 0.82), [Wt, St, apexS])
            pygame.draw.polygon(surf, sh(st['timber'], 0.9), [Wt, St, apexS], 1)
        else:
            tiled_face(Wt, St, RA, RA, 0.84)
    # ridge cap
    pygame.draw.line(surf, sh(roof, 1.35), RA, RB, 2)
    pygame.draw.line(surf, sh(roof, 0.6), (RA[0], RA[1] + 1), (RB[0], RB[1] + 1), 1)
    return RA, RB


def _roof_flat(surf, Nt, Et, St, Wt, st, rng, crenellate=False):
    top_c = sh(st['wall'], 1.18)
    pygame.draw.polygon(surf, top_c, [Nt, Et, St, Wt])
    pygame.draw.lines(surf, sh(st['trim'], 1.05), True, [Nt, Et, St, Wt], 2)
    inner = [(Nt[0], Nt[1] + 3), (Et[0] - 5, Et[1]), (St[0], St[1] - 3), (Wt[0] + 5, Wt[1])]
    pygame.draw.polygon(surf, sh(top_c, 0.92), inner)
    # gravel speckle
    for _ in range(14):
        u, v = rng.random(), rng.random()
        gx = Nt[0] + (Et[0] - Nt[0]) * u + (Wt[0] - Nt[0]) * v
        gy = Nt[1] + (Et[1] - Nt[1]) * u + (Wt[1] - Nt[1]) * v
        surf.set_at((int(gx), int(gy)), sh(top_c, rng.uniform(0.85, 1.1)))
    if crenellate:
        for edge in ((Wt, St), (St, Et)):
            e0, e1 = edge
            seg = max(2, int(math.hypot(e1[0] - e0[0], e1[1] - e0[1]) / 10))
            for i in range(seg):
                t = (i + 0.25) / seg
                mx = e0[0] + (e1[0] - e0[0]) * t
                my = e0[1] + (e1[1] - e0[1]) * t
                pygame.draw.rect(surf, sh(st['trim'], 0.95), (mx - 2, my - 4, 5, 5))


def _roof_furniture(surf, Nt, Et, St, Wt, st, rng, n):
    def roof_pt(u, v):
        return (Nt[0] + (Et[0] - Nt[0]) * u + (Wt[0] - Nt[0]) * v,
                Nt[1] + (Et[1] - Nt[1]) * u + (Wt[1] - Nt[1]) * v)
    wall = st['wall']
    for _ in range(n):
        u, v = rng.uniform(0.25, 0.75), rng.uniform(0.25, 0.75)
        bx, by = roof_pt(u, v)
        kind = rng.random()
        if kind < 0.5:  # AC unit
            pygame.draw.polygon(surf, sh(wall, 0.8), [(bx - 6, by - 1), (bx, by - 4), (bx + 6, by - 1), (bx, by + 2)])
            pygame.draw.polygon(surf, sh(wall, 0.6), [(bx - 6, by - 1), (bx, by + 2), (bx, by + 7), (bx - 6, by + 4)])
            pygame.draw.polygon(surf, sh(wall, 0.7), [(bx, by + 2), (bx + 6, by - 1), (bx + 6, by + 4), (bx, by + 7)])
            pygame.draw.ellipse(surf, sh(wall, 0.5), (bx - 4, by - 2, 8, 4))
        elif kind < 0.8:  # vent pipe
            pygame.draw.line(surf, sh(wall, 0.6), (bx, by), (bx, by - 8), 3)
            pygame.draw.line(surf, sh(wall, 0.8), (bx - 3, by - 8), (bx + 3, by - 8), 3)
        else:  # antenna
            pygame.draw.line(surf, (150, 154, 162), (bx, by), (bx, by - 16), 1)
            pygame.draw.line(surf, (150, 154, 162), (bx - 4, by - 10), (bx + 4, by - 13), 1)


def _banner(surf, x, y, color, length=20):
    pygame.draw.line(surf, (90, 76, 56), (x - 5, y - 2), (x + 5, y + 2), 2)
    pts = [(x - 4, y), (x + 4, y + 3), (x + 4, y + 3 + length), (x, y + length - 1), (x - 4, y + length + 1)]
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, sh(color, 0.6), pts, 1)
    pygame.draw.circle(surf, sh(color, 1.6), (x, y + 7), 2, 1)


def _ivy(surf, x, y, h, rng):
    for i in range(int(h / 5)):
        yy = y - i * 5 - rng.randint(0, 3)
        xx = x + rng.randint(-3, 3) + int(math.sin(i * 1.3) * 3)
        c = sh((74, 110, 56), rng.uniform(0.75, 1.2))
        pygame.draw.circle(surf, c, (xx, yy), rng.randint(2, 3))


def _volume(surf, nx, ny, vx, vy, fw, fh, stories, st, rng, roof, accent=None,
            arcade=False, win=True):
    """Draw one building volume whose footprint origin is at world offset
    (vx,vy) from the sprite's footprint anchor at pixel (nx,ny)."""
    zh = stories * STORY_PX
    bx, by = _w2px(vx, vy)
    N = (nx + bx, ny + by)
    E = (nx + bx + fw * HALF_W, ny + by + fw * HALF_H)
    S = (nx + bx + (fw - fh) * HALF_W, ny + by + (fw + fh) * HALF_H)
    W = (nx + bx - fh * HALF_W, ny + by + fh * HALF_H)
    Nt, Et, St, Wt = [(p[0], p[1] - zh) for p in (N, E, S, W)]

    _wall_face(surf, Wt, St, zh, st['wall'], st, rng, stories, 0.78, win=win, arcade=arcade)
    _wall_face(surf, St, Et, zh, st['wall'], st, rng, stories, 1.0, win=win, arcade=arcade)
    # corner quoins on the S vertical edge
    if st['masonry'] in ('stone', 'brick'):
        for q in range(0, zh - 4, 7):
            w_ = 3 if (q // 7) % 2 == 0 else 2
            pygame.draw.rect(surf, sh(st['trim'], 0.92), (S[0] - w_, S[1] - zh + q, w_ * 2, 4))
    # eave shadow under roofline
    pygame.draw.line(surf, sh(st['wall'], 0.55), Wt, St, 1)
    pygame.draw.line(surf, sh(st['wall'], 0.6), St, Et, 1)

    if roof == 'hip':
        _roof_hipped(surf, Nt, Et, St, Wt, fw, fh, st, rng)
    elif roof == 'gable':
        RA, RB = _roof_hipped(surf, Nt, Et, St, Wt, fw, fh, st, rng, gabled=True)
        # chimney
        cx_ = RA[0] + (RB[0] - RA[0]) * 0.75
        cy_ = RA[1] + (RB[1] - RA[1]) * 0.75
        pygame.draw.rect(surf, sh(st['wall'], 0.9), (cx_ - 2, cy_ - 8, 5, 9))
        pygame.draw.rect(surf, sh(st['trim'], 0.85), (cx_ - 3, cy_ - 9, 7, 3))
    elif roof == 'pyramid':
        _roof_hipped(surf, Nt, Et, St, Wt, min(fw, fh), min(fw, fh), st, rng)
    else:
        _roof_flat(surf, Nt, Et, St, Wt, st, rng, crenellate=(roof == 'flat_cren'))
        _roof_furniture(surf, Nt, Et, St, Wt, st, rng, 1 + stories // 3)
    return N, E, S, W, Nt, Et, St, Wt


def building(seed, fw, fh, stories, style):
    """AoE-style composed building: main volume + optional annex wing and
    corner tower, masonry walls, arched windows, tiled roofs, banners, ivy."""
    k = ('bld', seed, fw, fh, stories, style)
    if k in _cache:
        return _cache[k]
    rng = _rand(seed)
    st = BUILDING_STYLES[style]

    sloped = style in ('house', 'shop', 'brick', 'industrial')
    if sloped:
        stories = min(stories, 3)
    roof_main = ('gable' if style in ('house', 'industrial') else 'hip') if sloped \
        else ('flat_cren' if style == 'concrete' and rng.random() < 0.4 else 'flat')

    has_annex = sloped and fw >= 6 and fh >= 5 and rng.random() < 0.6
    has_tower = sloped and fw >= 6 and fh >= 5 and rng.random() < 0.45 and style != 'house'

    zh_main = stories * STORY_PX
    extra_top = ROOF_H + min(fw, fh) + (STORY_PX + 14 if has_tower else 0) + 26
    sw = (fw + fh) * HALF_W
    shh = (fw + fh) * HALF_H
    surf = pygame.Surface((sw + 12, shh + zh_main + extra_top), pygame.SRCALPHA)
    nx, ny = fh * HALF_W + 6, zh_main + extra_top - 8

    annex_h = max(2, fh // 2)
    annex_w = max(3, fw // 2)
    tower_sz = 3

    # main volume sits at the back if there's an annex
    main_fh = fh - (annex_h if has_annex else 0)
    _volume(surf, nx, ny, 0, 0, fw, max(2, main_fh), stories, st, rng, roof_main,
            arcade=(style == 'concrete' and stories >= 3))

    if has_annex:
        ast = min(stories, 1 + rng.randint(0, 1))
        _volume(surf, nx, ny, 0, fh - annex_h, annex_w, annex_h, ast, st, rng,
                'hip' if rng.random() < 0.7 else 'gable')
    if has_tower:
        tst = stories + 1
        _volume(surf, nx, ny, fw - tower_sz, fh - tower_sz, tower_sz, tower_sz,
                tst, st, rng, 'pyramid', win=True)

    # ---- dressing on the front (SW face of the front-most volume) ----
    fr_fh = annex_h if has_annex else fh
    fr_fw = annex_w if has_annex else fw
    Wf = (nx - fr_fh * HALF_W + _w2px(0, fh - fr_fh)[0],
          ny + fr_fh * HALF_H + _w2px(0, fh - fr_fh)[1])
    Sf = (Wf[0] + fr_fw * HALF_W, Wf[1] + fr_fw * HALF_H)

    # doorway with step
    dx0 = Wf[0] + (Sf[0] - Wf[0]) * 0.62
    dy0 = Wf[1] + (Sf[1] - Wf[1]) * 0.62
    pygame.draw.polygon(surf, (62, 46, 36),
                        [(dx0, dy0 - 16), (dx0 + 7, dy0 - 12.5), (dx0 + 7, dy0 + 1), (dx0, dy0 - 2)])
    pygame.draw.circle(surf, (62, 46, 36), (int(dx0 + 3.5), int(dy0 - 15)), 4)
    pygame.draw.arc(surf, sh(st['trim'], 0.9), (dx0 - 1, dy0 - 20, 10, 10), 0, 3.4, 2)
    pygame.draw.line(surf, sh(st['trim'], 0.8), (dx0 - 1, dy0 + 2), (dx0 + 8, dy0 + 5), 2)
    pygame.draw.circle(surf, (200, 180, 120), (int(dx0 + 6), int(dy0 - 7)), 1)

    if style == 'shop':
        aw = rng.choice(AWNING_COLORS)
        ax0, ay0 = Wf[0] + 2, Wf[1] - 20
        ax1 = Wf[0] + (Sf[0] - Wf[0]) * 0.55
        ay1 = Wf[1] + (Sf[1] - Wf[1]) * 0.55 - 20
        pygame.draw.polygon(surf, aw, [(ax0, ay0), (ax1, ay1), (ax1 + 5, ay1 + 6), (ax0 + 5, ay0 + 6)])
        seg = max(3, int((ax1 - ax0) / 7))
        for i in range(seg):
            t = i / seg
            if i % 2 == 0:
                continue
            x0_ = ax0 + (ax1 - ax0) * t
            y0_ = ay0 + (ay1 - ay0) * t
            x1_ = ax0 + (ax1 - ax0) * (t + 1 / seg)
            y1_ = ay0 + (ay1 - ay0) * (t + 1 / seg)
            pygame.draw.polygon(surf, (226, 222, 210),
                                [(x0_, y0_), (x1_, y1_), (x1_ + 5, y1_ + 6), (x0_ + 5, y0_ + 6)])
        pygame.draw.line(surf, sh(aw, 0.55), (ax0 + 5, ay0 + 7), (ax1 + 5, ay1 + 7), 2)
        # painted sign above
        neon = rng.choice(NEON_COLORS)
        pygame.draw.polygon(surf, sh(neon, 0.5),
                            [(ax0 + 2, ay0 - 9), (ax1 - 4, ay1 - 9), (ax1 - 4, ay1 - 1), (ax0 + 2, ay0 - 1)])
        for i in range(3):
            pygame.draw.rect(surf, sh(neon, 1.3), (ax0 + 5 + i * 7, ay0 - 7 + i * 3, 4, 5), 1)

    # banner on the SE face
    if rng.random() < 0.5 and stories >= 2:
        S_ = (nx + (fw - fh) * HALF_W, ny + (fw + fh) * HALF_H)
        E_ = (nx + fw * HALF_W, ny + fw * HALF_H)
        bx_ = S_[0] + (E_[0] - S_[0]) * rng.uniform(0.3, 0.7)
        by_ = S_[1] + (E_[1] - S_[1]) * rng.uniform(0.3, 0.7) - zh_main + 8
        _banner(surf, int(bx_), int(by_), rng.choice(BANNER_COLORS))

    # ivy on the W corner
    if rng.random() < 0.45 and style != 'glass':
        W_ = (nx - fh * HALF_W, ny + fh * HALF_H)
        _ivy(surf, int(W_[0] + 3), int(W_[1] - 2), zh_main * 0.8, rng)

    # fire escape stays for tall flat-roofed city blocks
    if not sloped and stories >= 4 and rng.random() < 0.5:
        S_ = (nx + (fw - fh) * HALF_W, ny + (fw + fh) * HALF_H)
        E_ = (nx + fw * HALF_W, ny + fw * HALF_H)
        fx = (S_[0] + E_[0]) / 2
        fy = (S_[1] + E_[1]) / 2
        rail = sh(st['wall'], 0.5)
        for s in range(1, stories):
            y = fy - s * STORY_PX
            pygame.draw.line(surf, rail, (fx - 9, y), (fx + 9, y + 4), 2)
            pygame.draw.line(surf, rail, (fx - 9, y - 6), (fx - 9, y), 1)
            pygame.draw.line(surf, rail, (fx + 9, y - 2), (fx + 9, y + 4), 1)
            pygame.draw.line(surf, rail, (fx - 7, y), (fx + 5, y - STORY_PX + 2), 1)

    if style == 'tower':
        # glass spire crown + aviation light
        Nt = (nx, ny - zh_main)
        St = (nx + (fw - fh) * HALF_W, ny + (fw + fh) * HALF_H - zh_main)
        tipx = (Nt[0] + St[0]) / 2
        tipy = (Nt[1] + St[1]) / 2
        pygame.draw.polygon(surf, sh(st['wall'], 1.15),
                            [(tipx - 14, tipy + 2), (tipx, tipy - 16), (tipx + 14, tipy + 2)])
        pygame.draw.line(surf, (170, 182, 200), (tipx, tipy - 16), (tipx, tipy - 34), 2)
        pygame.draw.circle(surf, (255, 90, 90), (int(tipx), int(tipy - 34)), 3)

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
