"""Open-world map generation for Meridian City — fine-tile scale.

The world is 240x240 small tiles (the player spans ~1.5 tiles). Roads are six
tiles wide with two-tile sidewalks, blocks hold buildings with alley gaps and
lootable courtyards. Generated deterministically from a fixed seed.
"""
import random
from src.constants import WORLD_W, WORLD_H

SEED = 20261009


class Prop:
    __slots__ = ('kind', 'x', 'y', 'variant', 'solid', 'axis', 'seed')

    def __init__(self, kind, x, y, variant=0, solid=True, axis='x', seed=0):
        self.kind, self.x, self.y = kind, x, y
        self.variant, self.solid, self.axis, self.seed = variant, solid, axis, seed


class Building:
    __slots__ = ('x', 'y', 'fw', 'fh', 'stories', 'style', 'seed')

    def __init__(self, x, y, fw, fh, stories, style, seed):
        self.x, self.y, self.fw, self.fh = x, y, fw, fh
        self.stories, self.style, self.seed = stories, style, seed


DISTRICTS = {
    'tower':    (152, 4, 236, 68),
    'plaza':    (84, 4, 148, 56),
    'market':   (8, 32, 72, 92),
    'downtown': (56, 60, 152, 144),
    'park':     (156, 76, 228, 160),
    'hub':      (16, 100, 52, 144),
    'overpass': (4, 4, 28, 96),
    'suburbs':  (8, 152, 84, 208),
    'docks':    (92, 156, 232, 216),
}


def district_at(x, y):
    for name in ('hub', 'overpass', 'plaza', 'tower', 'market', 'park',
                 'suburbs', 'docks', 'downtown'):
        x0, y0, x1, y1 = DISTRICTS[name]
        if x0 <= x <= x1 and y0 <= y <= y1:
            return name
    return 'downtown'


class World:
    def __init__(self):
        self.w, self.h = WORLD_W, WORLD_H
        self.ground = [['grass'] * self.w for _ in range(self.h)]
        self.solid = [[False] * self.w for _ in range(self.h)]
        self.decals = {}
        self.buildings = []
        self.props = []
        self.beacons = []          # (x, y, name)
        self.lore = []             # (x, y, index)
        self.npcs = []             # (x, y, key, style)
        self.enemy_spawns = []     # (kind, x, y, radius)
        self.bosses = {}           # key -> dict(center, radius, kind)
        self.gate_tiles = []
        self.lights = []           # (x, y, z_px, radius_px, color)
        self.weapons = []          # (x, y, weapon_key)  world pickups
        self.caches = []           # (x, y, kind, amount) kind: shards|stim|hp
        self.spawn = (35.0, 123.0)
        rng = random.Random(SEED)
        self._generate(rng)

    # ---- helpers -----------------------------------------------------
    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def fill(self, x0, y0, x1, y1, kind):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.ground[y][x] = kind

    def set_solid(self, x0, y0, x1, y1, val=True):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.solid[y][x] = val

    def add_building(self, x, y, fw, fh, stories, style, seed):
        self.buildings.append(Building(x, y, fw, fh, stories, style, seed))
        self.set_solid(x, y, x + fw - 1, y + fh - 1)
        self.fill(x, y, x + fw - 1, y + fh - 1, 'lot')
        if style == 'shop':
            rng = random.Random(seed)
            neon = rng.choice([(255, 90, 120), (90, 220, 255), (255, 180, 70),
                               (140, 255, 160), (200, 120, 255)])
            self.lights.append((x + fw * 0.2, y + fh + 0.6, 18, 64, tuple(c // 2 for c in neon)))

    def add_prop(self, kind, x, y, variant=0, solid=True, axis='x', seed=0, big=False):
        self.props.append(Prop(kind, x, y, variant, solid, axis, seed))
        if solid:
            self.solid[int(y)][int(x)] = True
            if big:
                if axis == 'x':
                    for dx in (-1, 1):
                        if self.in_bounds(int(x) + dx, int(y)):
                            self.solid[int(y)][int(x) + dx] = True
                else:
                    for dy in (-1, 1):
                        if self.in_bounds(int(x), int(y) + dy):
                            self.solid[int(y) + dy][int(x)] = True

    def add_lamppost(self, x, y):
        self.add_prop('lamppost', x, y)
        self.lights.append((x + 0.9, y + 0.3, 20, 190, (112, 88, 48)))

    def is_clear(self, x0, y0, x1, y1, kinds=('asphalt', 'lot', 'grass', 'plaza', 'sidewalk')):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if not self.in_bounds(x, y) or self.solid[y][x] or self.ground[y][x] not in kinds:
                    return False
        return True

    def clear_rect(self, x0, y0, x1, y1):
        self.set_solid(x0, y0, x1, y1, False)
        self.props = [p for p in self.props if not (x0 <= p.x <= x1 + 1 and y0 <= p.y <= y1 + 1)]
        self.buildings = [b for b in self.buildings
                          if not (x0 - b.fw <= b.x <= x1 and y0 - b.fh <= b.y <= y1)]

    # ---- generation --------------------------------------------------
    def _generate(self, rng):
        self._terrain_base(rng)
        self._roads(rng)
        self._district_downtown(rng)
        self._district_market(rng)
        self._district_plaza(rng)
        self._district_tower(rng)
        self._district_park(rng)
        self._district_suburbs(rng)
        self._district_docks(rng)
        self._district_overpass(rng)
        self._district_hub(rng)
        self._streetlife(rng)
        self._population(rng)
        self._pickups_and_npcs(rng)

    def _terrain_base(self, rng):
        self.fill(0, 0, self.w - 1, self.h - 1, 'grass')
        self.fill(4, 4, self.w - 5, 190, 'asphalt')
        self.fill(0, 218, self.w - 1, self.h - 1, 'water')
        self.set_solid(0, 218, self.w - 1, self.h - 1)
        self.fill(0, 210, self.w - 1, 217, 'sand')
        self.set_solid(0, 0, self.w - 1, 1)
        self.set_solid(0, 0, 1, self.h - 1)
        self.set_solid(self.w - 2, 0, self.w - 1, self.h - 1)
        self.set_solid(0, self.h - 2, self.w - 1, self.h - 1)

    V_ROADS = (28, 56, 84, 116, 148, 180, 212)
    H_ROADS = (28, 60, 92, 124, 156, 188)

    def _road_v(self, x, y0, y1, width=6):
        self.fill(x, y0, x + width - 1, y1, 'road')
        self.fill(x - 2, y0, x - 1, y1, 'sidewalk')
        self.fill(x + width, y0, x + width + 1, y1, 'sidewalk')
        mid = x + width // 2
        for y in range(y0, y1 + 1):
            if y % 3 != 0:
                self.decals[(mid, y)] = 'dash_y'

    def _road_h(self, y, x0, x1, width=6):
        self.fill(x0, y, x1, y + width - 1, 'road')
        self.fill(x0, y - 2, x1, y - 1, 'sidewalk')
        self.fill(x0, y + width, x1, y + width + 1, 'sidewalk')
        mid = y + width // 2
        for x in range(x0, x1 + 1):
            if x % 3 != 0:
                self.decals[(x, mid)] = 'dash_x'

    def _roads(self, rng):
        for x in self.V_ROADS:
            self._road_v(x, 6, 208)
        for y in self.H_ROADS:
            self._road_h(y, 5, 234)
        # crosswalks + manholes at intersections
        for vx in self.V_ROADS:
            for hy in self.H_ROADS:
                for dy in range(6):
                    self.decals[(vx - 4, hy + dy)] = 'cross_y'
                    self.decals[(vx + 9, hy + dy)] = 'cross_y'
                for dx in range(6):
                    self.decals[(vx + dx, hy - 4)] = 'cross_x'
                    self.decals[(vx + dx, hy + 9)] = 'cross_x'
                if rng.random() < 0.5:
                    self.decals[(vx + 2, hy + 2)] = 'manhole'

    # ---- blocks --------------------------------------------------------
    def _block(self, rng, x0, y0, x1, y1, styles, min_st, max_st, courtyard=0.35):
        """Fill a city block: buildings around the rim with alley gaps,
        sometimes a lootable interior courtyard."""
        placed = []
        attempts = 22
        for _ in range(attempts):
            fw, fh = rng.randint(4, 8), rng.randint(4, 7)
            # bias to the rim
            side = rng.randint(0, 3)
            if side == 0:
                bx, by = rng.randint(x0, max(x0, x1 - fw)), y0
            elif side == 1:
                bx, by = rng.randint(x0, max(x0, x1 - fw)), max(y0, y1 - fh)
            elif side == 2:
                bx, by = x0, rng.randint(y0, max(y0, y1 - fh))
            else:
                bx, by = max(x0, x1 - fw), rng.randint(y0, max(y0, y1 - fh))
            if self.is_clear(bx - 1, by - 1, bx + fw, by + fh, ('asphalt', 'lot', 'grass')):
                self.add_building(bx, by, fw, fh, rng.randint(min_st, max_st),
                                  rng.choice(styles), rng.randint(0, 10 ** 9))
                placed.append((bx, by, fw, fh))
        # courtyard loot in the interior
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        if placed and rng.random() < courtyard and not self.solid[cy][cx]:
            self.fill(cx - 2, cy - 2, cx + 2, cy + 2, 'alley')
            r = rng.random()
            if r < 0.6:
                self.caches.append((cx + 0.5, cy + 0.5, 'shards', rng.randint(60, 160)))
            elif r < 0.85:
                self.caches.append((cx + 0.5, cy + 0.5, 'hp', 20))
            else:
                self.caches.append((cx + 0.5, cy + 0.5, 'stim', 1))
            if rng.random() < 0.6:
                self.add_prop('dumpster', cx - 1.5, cy - 1.5)
            if rng.random() < 0.5:
                self.add_prop('debris', cx + 1.5, cy - 1.0, solid=False)

    def _blocks_between(self, rng, xa, xb, ya, yb, styles, mn, mx, courtyard=0.35):
        """Build on the block bounded by roads at xa/xb and ya/yb."""
        self._block(rng, xa + 9, ya + 9, xb - 4, yb - 4, styles, mn, mx, courtyard)

    def _district_downtown(self, rng):
        vs, hs = self.V_ROADS, self.H_ROADS
        for xa, xb in [(56, 84), (84, 116), (116, 148)]:
            for ya, yb in [(60, 92), (92, 124), (124, 156)]:
                if (xa, ya) == (84, 92):
                    continue   # central plaza block kept open
                self._blocks_between(rng, xa, xb, ya, yb,
                                     ('concrete', 'glass', 'shop'), 3, 7)
        # central open plaza with the downtown beacon
        self.fill(95, 102, 112, 117, 'plaza')
        for x, y in [(96, 103), (110, 103), (96, 115), (110, 115)]:
            self.add_lamppost(x + 0.5, y + 0.5)

    def _district_market(self, rng):
        for xa, xb in [(8, 28), (28, 56)]:
            for ya, yb in [(32, 60), (60, 92)]:
                self._blocks_between(rng, xa, xb, ya, yb, ('shop', 'brick'), 2, 4, 0.5)
        # pedestrian market lane
        self.fill(34, 40, 52, 54, 'plaza')
        self.clear_rect(35, 41, 51, 53)
        for i in range(10):
            x = 36 + (i % 5) * 3.4
            y = 42.5 + (i // 5) * 7
            self.add_prop('crate', x, y, variant=i)
            if i % 2 == 0:
                self.add_prop('crate', x + 0.9, y + 0.4, variant=i + 20)
        for x, y in [(36, 47), (44, 47), (50, 47)]:
            self.add_lamppost(x + 0.5, y + 0.5)
        self.weapons.append((47.5, 50.5, 'machete'))

    def _district_plaza(self, rng):
        self.fill(92, 12, 140, 52, 'plaza')
        self.clear_rect(92, 12, 140, 52)
        self.add_building(92, 8, 10, 5, 6, 'concrete', 101)
        self.add_building(128, 8, 10, 5, 6, 'concrete', 102)
        self.add_prop('fountain', 116.0, 32.0, solid=True)
        self.set_solid(114, 31, 117, 33)
        for x, y in [(100, 18), (132, 18), (100, 46), (132, 46)]:
            self.add_lamppost(x + 0.5, y + 0.5)
        for x, y in [(106, 24), (126, 24), (106, 40), (126, 40)]:
            self.add_prop('bench', x + 0.5, y + 0.5)
        self.bosses['chorister'] = dict(center=(116.0, 37.0), radius=17.0, kind='chorister')

    def _district_tower(self, rng):
        self.fill(160, 8, 228, 64, 'plaza')
        self.clear_rect(160, 8, 228, 64)
        self.add_building(184, 12, 20, 16, 14, 'tower', 777)
        self.add_building(164, 12, 8, 10, 8, 'glass', 778)
        self.add_building(216, 12, 8, 10, 8, 'glass', 779)
        self.bosses['archivist'] = dict(center=(194.0, 42.0), radius=15.0, kind='archivist')
        for x in range(176, 214):
            self.gate_tiles.append((x, 66))
            self.gate_tiles.append((x, 67))
        for x, y in [(172, 36), (216, 36), (180, 56), (208, 56)]:
            self.add_lamppost(x + 0.5, y + 0.5)
        # helix tower floods its own plaza with signal-blue light
        self.lights.append((194, 30, 60, 300, (36, 66, 88)))

    def _district_park(self, rng):
        x0, y0, x1, y1 = DISTRICTS['park']
        self.fill(x0, y0, x1, y1, 'grass')
        self.clear_rect(x0, y0, x1, y1)
        self.fill(x0 + 4, 116, x1 - 4, 118, 'dirt')
        self.fill(188, y0 + 4, 190, y1 - 4, 'dirt')
        for _ in range(110):
            x, y = rng.randint(x0 + 2, x1 - 2), rng.randint(y0 + 2, y1 - 2)
            if not self.solid[y][x] and self.ground[y][x] == 'grass':
                kind = 'tree' if rng.random() < 0.82 else 'dead_tree'
                self.add_prop(kind, x + 0.5, y + 0.5, variant=rng.randint(0, 4))
        for x, y in [(168, 116), (208, 116), (188, 96), (188, 140)]:
            if not self.solid[y][x]:
                self.add_prop('bench', x + 0.5, y + 0.5)
        for (x, y) in [(170, 117), (206, 117)]:
            self.add_lamppost(x + 0.5, y - 1.5)
        # Patient Zero's clearing
        self.clear_rect(192, 124, 216, 142)
        self.fill(195, 126, 213, 140, 'dirt')
        self.bosses['hound'] = dict(center=(203.0, 132.0), radius=12.0, kind='hound')
        self.caches.append((212.5, 138.5, 'shards', 140))

    def _district_suburbs(self, rng):
        x0, y0, x1, y1 = DISTRICTS['suburbs']
        self.fill(x0, y0, x1, y1, 'grass')
        self._road_h(176, x0, x1, width=4)
        self._road_v(44, y0 + 2, y1 - 4, width=4)
        for bx in range(x0 + 4, x1 - 7, 11):
            for by in (160, 166, 184, 196):
                if rng.random() < 0.8 and self.is_clear(bx - 1, by - 1, bx + 6, by + 5,
                                                        ('grass', 'asphalt', 'lot')):
                    self.add_building(bx, by, rng.randint(4, 6), 4,
                                      rng.randint(1, 2), 'house', rng.randint(0, 10 ** 9))
        for _ in range(30):
            x, y = rng.randint(x0, x1), rng.randint(y0, y1)
            if not self.solid[y][x] and self.ground[y][x] == 'grass':
                self.add_prop('tree', x + 0.5, y + 0.5, variant=rng.randint(0, 4))
        self.caches.append((14.5, 199.5, 'stim', 1))
        self.caches.append((76.5, 160.5, 'shards', 90))

    def _district_docks(self, rng):
        x0, y0, x1, y1 = DISTRICTS['docks']
        self.fill(x0, y0, x1, min(y1, 208), 'lot')
        for bx0 in (100, 140, 184):
            self._block(rng, bx0, 160, bx0 + 22, 176, ('industrial',), 2, 3, 0.4)
        # container yard
        for _ in range(40):
            x, y = rng.randint(x0 + 4, x1 - 4), rng.randint(182, 204)
            if self.is_clear(x - 1, y, x + 2, y + 1, ('lot',)):
                self.add_prop('container', x + 0.5, y + 0.5, variant=rng.randint(0, 7),
                              axis='x', big=True)
        for x in range(100, 226, 24):
            if not self.solid[196][x]:
                self.add_lamppost(x + 0.5, 196.5)
        self.weapons.append((205.5, 200.5, 'sledge'))
        self.caches.append((118.5, 203.5, 'shards', 120))
        self.caches.append((226.5, 186.5, 'hp', 20))

    def _district_overpass(self, rng):
        x0, y0, x1, y1 = DISTRICTS['overpass']
        self.fill(x0 + 2, y0 + 2, x1 - 2, y1, 'road')
        self.fill(x0, y0 + 2, x0 + 1, y1, 'sidewalk')
        self.fill(x1 - 1, y0 + 2, x1, y1, 'sidewalk')
        for y in range(y0 + 2, y1, 3):
            self.decals[(16, y)] = 'dash_y'
        for y in range(10, 90, 13):
            self.add_prop('barricade', 10.5, y + 0.5)
            self.add_prop('barricade', 22.5, y + 4.5)
        for y in range(14, 92, 16):
            self.add_prop('car', 16.5, y + 0.5, axis='y', seed=rng.randint(0, 10 ** 9), big=True)
        for y in range(12, 92, 22):
            self.add_lamppost(5.5, y + 0.5)
        # Warden arena
        self.clear_rect(7, 40, 26, 64)
        self.bosses['warden'] = dict(center=(17.0, 52.0), radius=11.0, kind='warden')
        self.weapons.append((18.5, 80.5, 'spear'))
        self.caches.append((9.5, 8.5, 'shards', 100))

    def _district_hub(self, rng):
        x0, y0, x1, y1 = DISTRICTS['hub']
        self.fill(x0, y0, x1, y1, 'lot')
        self.add_building(20, 104, 8, 6, 2, 'industrial', 31)
        self.add_building(40, 104, 6, 6, 2, 'industrial', 32)
        self.add_prop('crate', 25.5, 117.5)
        self.add_prop('crate', 26.6, 118.1)
        self.add_prop('dumpster', 43.5, 133.5)
        self.add_prop('trash', 31.5, 120.5)
        self.beacons.append((35.0, 127.0, 'hub'))
        self.add_lamppost(30.5, 124.5)

    def _streetlife(self, rng):
        # regular lampposts along arterials — the city was planned, once
        for vx in self.V_ROADS:
            for y in range(10, 206, 16):
                if self.ground[y][vx - 2] == 'sidewalk' and not self.solid[y][vx - 2]:
                    self.add_lamppost(vx - 1.5, y + 0.5)
                y2 = y + 8
                if y2 < 206 and self.ground[y2][vx + 7] == 'sidewalk' and not self.solid[y2][vx + 7]:
                    self.add_lamppost(vx + 7.5, y2 + 0.5)
        for hy in self.H_ROADS:
            for x in range(12, 230, 18):
                if self.ground[hy - 2][x] == 'sidewalk' and not self.solid[hy - 2][x]:
                    if rng.random() < 0.5:
                        self.add_lamppost(x + 0.5, hy - 1.5)
        # traffic lights at intersections
        for vx in self.V_ROADS:
            for hy in self.H_ROADS:
                if rng.random() < 0.75:
                    x, y = vx - 2, hy - 2
                    if not self.solid[y][x]:
                        self.add_prop('traffic_light', x + 0.5, y + 0.5)
                if rng.random() < 0.75:
                    x, y = vx + 7, hy + 7
                    if self.in_bounds(x, y) and not self.solid[y][x]:
                        self.add_prop('traffic_light', x + 0.5, y + 0.5)
        # wrecked cars in lanes
        for _ in range(110):
            x, y = rng.randint(8, self.w - 9), rng.randint(8, 206)
            if self.ground[y][x] == 'road' and not self.solid[y][x] and rng.random() < 0.7:
                if any(abs(x - b['center'][0]) < 16 and abs(y - b['center'][1]) < 16
                       for b in self.bosses.values()):
                    continue
                axis = 'y' if any(abs(x - vx - 3) < 4 for vx in self.V_ROADS) else 'x'
                if not self.is_clear(x - 1, y - 1, x + 1, y + 1, ('road',)):
                    continue
                self.add_prop('car', x + 0.5, y + 0.5, axis=axis,
                              seed=rng.randint(0, 10 ** 9), big=True)
        # sidewalk clutter
        for _ in range(240):
            x, y = rng.randint(6, self.w - 7), rng.randint(8, 206)
            if self.ground[y][x] == 'sidewalk' and not self.solid[y][x]:
                r = rng.random()
                if r < 0.10:
                    self.add_prop('hydrant', x + 0.5, y + 0.5)
                elif r < 0.18:
                    self.add_prop('trash', x + 0.5, y + 0.5)
                elif r < 0.24:
                    self.add_prop('bus_stop', x + 0.5, y + 0.5)
                elif r < 0.28:
                    self.add_prop('phonebooth', x + 0.5, y + 0.5)
                elif r < 0.42:
                    self.add_prop('debris', x + 0.5, y + 0.5, solid=False)
                elif r < 0.52:
                    self.decals[(x, y)] = rng.choice(('grime', 'leaf'))
        # leaves and grime drift everywhere
        for _ in range(500):
            x, y = rng.randint(4, self.w - 5), rng.randint(6, 208)
            if (x, y) not in self.decals and self.ground[y][x] in ('asphalt', 'sidewalk', 'plaza', 'lot'):
                self.decals[(x, y)] = rng.choice(('grime', 'leaf', 'leaf'))

    def _population(self, rng):
        def spawn_in(name, kind, count):
            x0, y0, x1, y1 = DISTRICTS[name]
            placed = tries = 0
            while placed < count and tries < count * 50:
                tries += 1
                x = rng.uniform(x0 + 2, x1 - 2)
                y = rng.uniform(y0 + 2, y1 - 2)
                if self.solid[int(y)][int(x)] or self.ground[int(y)][int(x)] == 'water':
                    continue
                if any(abs(x - bx) < 14 and abs(y - by) < 14 for bx, by, _ in self.beacons):
                    continue
                if any(abs(x - b['center'][0]) < b['radius'] + 4 and
                       abs(y - b['center'][1]) < b['radius'] + 4 for b in self.bosses.values()):
                    continue
                sx, sy = self.spawn
                if abs(x - sx) < 14 and abs(y - sy) < 14:
                    continue
                self.enemy_spawns.append((kind, x, y, rng.uniform(5, 9)))
                placed += 1

        spawn_in('downtown', 'husk', 16)
        spawn_in('downtown', 'stalker', 5)
        spawn_in('market', 'husk', 9)
        spawn_in('market', 'stalker', 3)
        spawn_in('hub', 'husk', 2)
        spawn_in('park', 'feral', 8)
        spawn_in('park', 'husk', 4)
        spawn_in('suburbs', 'husk', 10)
        spawn_in('suburbs', 'feral', 4)
        spawn_in('docks', 'riot', 7)
        spawn_in('docks', 'drone', 6)
        spawn_in('docks', 'husk', 5)
        spawn_in('plaza', 'husk', 6)
        spawn_in('overpass', 'riot', 4)
        spawn_in('tower', 'riot', 4)
        spawn_in('tower', 'drone', 5)
        spawn_in('tower', 'stalker', 3)

    def _pickups_and_npcs(self, rng):
        for bx, by, name in [(101.0, 109.0, 'downtown'), (43.0, 61.0, 'market'),
                             (99.0, 55.0, 'plaza'), (171.0, 99.0, 'park'),
                             (41.0, 171.0, 'suburbs'), (121.0, 185.0, 'docks'),
                             (169.0, 61.0, 'tower')]:
            self.clear_rect(int(bx) - 1, int(by) - 1, int(bx) + 1, int(by) + 1)
            self.beacons.append((bx, by, name))
        spots = [(27.5, 111.5), (99.5, 21.5), (49.5, 183.5), (105.5, 101.5),
                 (45.5, 49.5), (197.5, 65.5), (171.5, 117.5), (61.5, 161.5),
                 (177.5, 53.5), (17.5, 73.5)]
        for i, (x, y) in enumerate(spots):
            self.solid[int(y)][int(x)] = False
            self.lore.append((x, y, i))
        self.npcs.append((39.0, 129.0, 'maya', 'maya'))
        self.npcs.append((47.0, 65.0, 'cartographer', 'cart'))
        for x, y, kind in [(35, 121, None)]:
            pass
        # make sure pickup tiles are walkable
        for (x, y, _) in self.weapons:
            self.solid[int(y)][int(x)] = False
        for (x, y, _, _) in self.caches:
            self.solid[int(y)][int(x)] = False
