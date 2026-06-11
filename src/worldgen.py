"""Meridian-under-the-Stillness: a ruined walled city built from flare-game
tiles. 120x120 tile open world: grass commons, dirt roads, a flagstone city
core of ruined compounds, a market of stalls, a cathedral plaza, gardens,
a drowned dockside and the Carillon Spire."""
import random
from src.constants import WORLD_W, WORLD_H

SEED = 20261009

G = 'tileset_grassland.txt'
R = 'tileset_ruins.txt'

FLOOR_POOLS = {
    'grass':   (G, [16, 17, 18, 19, 20, 21, 22, 23]),
    'meadow':  (G, [24, 25, 26, 27, 28, 29, 30, 31]),
    'dirt':    (G, [36, 37, 38, 39, 40, 41, 42, 43]),
    'flag':    (R, [24, 25, 26, 28, 29, 31, 37, 38]),
    'flag2':   (R, [32, 34, 35, 36, 44, 45, 46, 47]),
    'mosaic':  (R, [152, 153, 154, 155, 156, 157]),
    'reddirt': (R, [96, 97, 98, 99, 100, 101, 102, 103]),
    'rubblef': (R, [56, 57, 58, 59, 60, 61, 62, 63]),
    'water':   (G, [176, 177, 178, 179, 180, 181, 182, 183]),
}

# object id pools
TREES = (G, [240, 241, 242, 243, 246, 247, 248, 249, 250, 251])
PLANTS = (G, [112, 113, 114, 115, 116, 117, 118, 119])
BUSHES = (G, [120, 121, 122, 123, 124, 125])
FERNS = (R, [312, 313, 317])
GOLD_BUSH = (R, [314, 315, 316])
GRAVES = (G, [136, 137, 138, 139])
ROCKS = (G, [128, 129, 130, 131])
STUMPS = (G, [132, 133])
TENTS = (G, [64, 65])
CRATES = (G, [72, 73, 74, 75])
BUCKETS = (G, [76, 77])
LOGS = (G, [92, 93, 94, 95])
CAMPFIRE = (G, [96])
ANVIL = (G, [97])
FENCES = (G, [98, 99, 100, 101, 102, 103])
STALLS = (G, [192, 193, 196, 197, 198, 199])
BOATS = (G, [178, 179])
COLUMNS = (R, [122, 123, 124, 140, 144])
COLUMNS_BROKEN = (R, [136, 137])
STATUES = (R, [236, 237, 238, 239, 240, 241])
FURNITURE = (R, [265, 266, 267, 268, 269, 273, 274, 275, 276, 277])
TABLES = (R, [284, 285, 286])
RUBBLE = (R, [188, 189, 190, 191, 192, 193, 194])
ALTARS = (R, [384, 385, 386])
IRONFENCE = (R, [360, 361, 362, 363])
POOL_TILE = (R, [380])
CRYSTAL = (R, [296])

WALL_X = (R, [200, 201, 205])     # front face visible, runs +x
WALL_Y = (R, [199])                    # front face visible, runs +y
WALL_XB = (R, [198])                        # dark back face, runs +x
WALL_YB = (R, [197])                        # dark back face, runs +y
WALL_END = (R, [232, 233, 202])

DISTRICTS = {
    'tower':    (76, 2, 118, 34),
    'plaza':    (42, 2, 74, 28),
    'market':   (4, 16, 36, 46),
    'downtown': (28, 30, 76, 72),
    'park':     (78, 38, 114, 80),
    'hub':      (8, 50, 26, 72),
    'overpass': (2, 2, 14, 48),
    'suburbs':  (4, 76, 42, 104),
    'docks':    (46, 78, 116, 108),
}


def district_at(x, y):
    for name in ('hub', 'overpass', 'plaza', 'tower', 'market', 'park',
                 'suburbs', 'docks', 'downtown'):
        x0, y0, x1, y1 = DISTRICTS[name]
        if x0 <= x <= x1 and y0 <= y <= y1:
            return name
    return 'downtown'


class Obj:
    __slots__ = ('ts', 'tid', 'x', 'y', 'solid')

    def __init__(self, ts, tid, x, y, solid=True):
        self.ts, self.tid, self.x, self.y, self.solid = ts, tid, x, y, solid


class World:
    def __init__(self):
        self.w, self.h = WORLD_W, WORLD_H
        self.kind = [['grass'] * self.w for _ in range(self.h)]
        self.floor = [[None] * self.w for _ in range(self.h)]
        self.solid = [[False] * self.w for _ in range(self.h)]
        self.objects = []
        self.obj_at = {}
        self.beacons = []        # (x, y, name)
        self.lore = []           # (x, y, index)
        self.npcs = []           # (x, y, key, style)
        self.enemy_spawns = []
        self.bosses = {}
        self.gate_tiles = []
        self.weapons = []        # (x, y, weapon_key)
        self.caches = []         # (x, y, kind, amount)
        self.spawn = (17.5, 61.5)
        rng = random.Random(SEED)
        self._generate(rng)
        self._bake_floor(rng)

    # ---- helpers -----------------------------------------------------
    def in_bounds(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def fill(self, x0, y0, x1, y1, kind):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.kind[y][x] = kind

    def set_solid(self, x0, y0, x1, y1, val=True):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.solid[y][x] = val

    def add(self, pool, x, y, rng=None, solid=True):
        ts, ids = pool
        tid = ids[0] if rng is None else rng.choice(ids)
        if not self.in_bounds(x, y) or (x, y) in self.obj_at:
            return None
        o = Obj(ts, tid, x, y, solid)
        self.objects.append(o)
        self.obj_at[(x, y)] = o
        if solid:
            self.solid[y][x] = True
        return o

    def clear_rect(self, x0, y0, x1, y1):
        self.set_solid(x0, y0, x1, y1, False)
        self.objects = [o for o in self.objects
                        if not (x0 <= o.x <= x1 and y0 <= o.y <= y1)]
        self.obj_at = {(o.x, o.y): o for o in self.objects}

    def is_free(self, x, y, kinds=None):
        return (self.in_bounds(x, y) and not self.solid[y][x]
                and (x, y) not in self.obj_at
                and (kinds is None or self.kind[y][x] in kinds))

    def _bake_floor(self, rng):
        for y in range(self.h):
            for x in range(self.w):
                ts, ids = FLOOR_POOLS[self.kind[y][x]]
                self.floor[y][x] = (ts, ids[(x * 73856093 ^ y * 19349663) % len(ids)])

    # ---- structure: ruined walled compound ---------------------------
    def compound(self, rng, x0, y0, x1, y1, ruin=0.35, interior='flag2',
                 furnish=True):
        self.fill(x0, y0, x1, y1, interior)
        # gap for the entrance on the south-west wall
        door = rng.randint(x0 + 1, x1 - 1)
        # decide wall presence first so exposed run-ends get capped pieces
        top = {x: rng.random() > ruin for x in range(x0, x1 + 1)}
        bot = {x: (x != door) and rng.random() > ruin for x in range(x0, x1 + 1)}
        left = {y: rng.random() > ruin for y in range(y0 + 1, y1)}
        right = {y: rng.random() > ruin for y in range(y0 + 1, y1)}

        def place(x, y, present, prev_present, next_present, pool):
            if present:
                whole = prev_present and next_present
                self.add(pool if whole else WALL_END, x, y, rng)
            elif rng.random() < 0.5:
                self.add(RUBBLE, x, y, rng)

        for x in range(x0, x1 + 1):
            place(x, y0, top.get(x, False), top.get(x - 1, False),
                  top.get(x + 1, False), WALL_X)
            place(x, y1, bot.get(x, False), bot.get(x - 1, False),
                  bot.get(x + 1, False), WALL_X)
        for y in range(y0 + 1, y1):
            place(x0, y, left.get(y, False), left.get(y - 1, False),
                  left.get(y + 1, False), WALL_Y)
            place(x1, y, right.get(y, False), right.get(y - 1, False),
                  right.get(y + 1, False), WALL_Y)
        if furnish:
            for _ in range((x1 - x0) * (y1 - y0) // 5):
                x = rng.randint(x0 + 1, x1 - 1)
                y = rng.randint(y0 + 1, y1 - 1)
                if self.is_free(x, y):
                    r = rng.random()
                    if r < 0.4:
                        self.add(FURNITURE, x, y, rng)
                    elif r < 0.55:
                        self.add(TABLES, x, y, rng)
                    elif r < 0.75:
                        self.add(COLUMNS_BROKEN, x, y, rng)
                    else:
                        self.add(RUBBLE, x, y, rng)
        return door

    # ---- generation ---------------------------------------------------
    def _generate(self, rng):
        self.fill(0, 0, self.w - 1, self.h - 1, 'grass')
        # meadow patches
        for _ in range(60):
            cx, cy = rng.randint(0, self.w - 1), rng.randint(0, self.h - 1)
            r = rng.randint(2, 5)
            self.fill(cx - r, cy - r, cx + r, cy + r, 'meadow')
        # waterfront
        self.fill(0, 109, self.w - 1, self.h - 1, 'water')
        self.set_solid(0, 109, self.w - 1, self.h - 1)
        self.fill(0, 105, self.w - 1, 108, 'dirt')
        # world border
        self.set_solid(0, 0, self.w - 1, 0)
        self.set_solid(0, 0, 0, self.h - 1)
        self.set_solid(self.w - 1, 0, self.w - 1, self.h - 1)
        self.set_solid(0, self.h - 1, self.w - 1, self.h - 1)

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
        self._wilds(rng)
        self._population(rng)
        self._pickups_and_npcs(rng)

    V_ROADS = (14, 28, 42, 58, 74, 90, 106)
    H_ROADS = (14, 30, 46, 62, 78, 94)

    def _roads(self, rng):
        for x in self.V_ROADS:
            self.fill(x, 3, x + 1, 104, 'dirt')
        for y in self.H_ROADS:
            self.fill(3, y, 116, y + 1, 'dirt')
        # the city core is paved
        for x in self.V_ROADS:
            if 42 <= x <= 90:
                self.fill(x, 3, x + 1, 78, 'flag')
        for y in self.H_ROADS:
            if y <= 62:
                self.fill(28, y, 106, y + 1, 'flag')

    def _district_downtown(self, rng):
        # ruined compounds in each block of the old city
        for bx0, by0 in [(31, 33), (45, 33), (61, 33), (31, 49), (61, 49),
                         (45, 65), (61, 65), (31, 65)]:
            w = rng.randint(6, 9)
            h = rng.randint(6, 9)
            x0 = bx0 + rng.randint(0, 2)
            y0 = by0 + rng.randint(0, 2)
            self.compound(rng, x0, y0, min(x0 + w, bx0 + 11), min(y0 + h, by0 + 11),
                          ruin=rng.uniform(0.25, 0.5))
        # central court kept open with the downtown beacon
        self.clear_rect(46, 50, 55, 58)
        self.fill(46, 50, 55, 58, 'flag')
        for x, y in [(47, 51), (54, 51), (47, 57), (54, 57)]:
            self.add(COLUMNS, x, y, rng)

    def _district_market(self, rng):
        x0, y0, x1, y1 = DISTRICTS['market']
        # stall rows on a packed-dirt square
        self.fill(16, 19, 27, 29, 'dirt')
        for i in range(5):
            self.add(STALLS, 17 + i * 2, 21, rng)
            self.add(STALLS, 18 + i * 2, 26, rng)
        for _ in range(14):
            x, y = rng.randint(16, 27), rng.randint(19, 29)
            if self.is_free(x, y):
                self.add(rng.choice([CRATES, BUCKETS, LOGS]), x, y, rng)
        # fenced yards south of the square
        for fx0, fy0 in [(8, 34), (20, 36), (30, 34)]:
            for x in range(fx0, fx0 + 5):
                self.add(FENCES, x, fy0, rng, solid=False)
            for _ in range(3):
                x, y = rng.randint(fx0, fx0 + 4), rng.randint(fy0 + 1, fy0 + 3)
                if self.is_free(x, y):
                    self.add(rng.choice([CRATES, LOGS, BUCKETS]), x, y, rng)
        self.weapons.append((23.5, 25.5, 'machete'))

    def _district_plaza(self, rng):
        self.fill(46, 6, 70, 26, 'flag')
        self.clear_rect(46, 6, 70, 26)
        self.fill(54, 12, 62, 20, 'mosaic')
        self.add(POOL_TILE, 58, 16, solid=False)
        # ring of columns + statues
        for x in range(48, 69, 4):
            self.add(COLUMNS if rng.random() < 0.7 else COLUMNS_BROKEN, x, 8, rng)
            self.add(COLUMNS if rng.random() < 0.7 else COLUMNS_BROKEN, x, 24, rng)
        for y in range(10, 23, 4):
            self.add(COLUMNS if rng.random() < 0.7 else COLUMNS_BROKEN, 47, y, rng)
        for x, y in [(50, 12), (66, 12), (50, 20), (66, 20)]:
            self.add(STATUES, x, y, rng)
        self.bosses['chorister'] = dict(center=(58.0, 17.0), radius=8.5, kind='chorister')

    def _district_tower(self, rng):
        self.fill(80, 4, 114, 32, 'flag')
        self.clear_rect(80, 4, 114, 32)
        self.fill(90, 8, 104, 18, 'mosaic')
        # colonnade leading north to the sanctum
        for y in range(20, 31, 2):
            self.add(COLUMNS, 90, y, rng)
            self.add(COLUMNS, 104, y, rng)
        # inner sanctum walls
        for x in range(90, 105):
            if x != 97:
                self.add(WALL_END if x in (96, 104) else WALL_X, x, 7, rng)
        for y in range(8, 14):
            self.add(WALL_END if y == 13 else WALL_Y, 90, y, rng)
            self.add(WALL_END if y == 13 else WALL_Y, 104, y, rng)
        for x, y in [(92, 9), (102, 9), (92, 13), (102, 13)]:
            self.add(STATUES, x, y, rng)
        for x, y in [(94, 8), (100, 8)]:
            self.add(ALTARS, x, y, rng)
        self.bosses['archivist'] = dict(center=(97.0, 21.0), radius=8.0, kind='archivist')
        for x in range(88, 107):
            self.gate_tiles.append((x, 33))

    def _district_park(self, rng):
        x0, y0, x1, y1 = DISTRICTS['park']
        self.fill(x0 + 2, 58, x1 - 2, 59, 'dirt')
        self.fill(94, y0 + 2, 95, y1 - 2, 'dirt')
        for _ in range(70):
            x, y = rng.randint(x0 + 1, x1 - 1), rng.randint(y0 + 1, y1 - 1)
            if self.is_free(x, y, ('grass', 'meadow')):
                r = rng.random()
                if r < 0.55:
                    self.add(TREES, x, y, rng)
                elif r < 0.75:
                    self.add(rng.choice([PLANTS, BUSHES, FERNS]), x, y, rng, solid=False)
                elif r < 0.85:
                    self.add(GRAVES, x, y, rng)
                else:
                    self.add(ROCKS, x, y, rng)
        # the beast's clearing
        self.clear_rect(95, 61, 108, 71)
        self.fill(96, 62, 107, 70, 'reddirt')
        for x, y in [(96, 62), (107, 62), (96, 70)]:
            self.add(RUBBLE, x, y, rng)
        self.bosses['hound'] = dict(center=(101.5, 66.0), radius=6.0, kind='hound')
        self.caches.append((106.5, 69.5, 'shards', 140))

    def _district_suburbs(self, rng):
        x0, y0, x1, y1 = DISTRICTS['suburbs']
        # the Long Saturday: a hamlet of tents, yards and too many graves
        for hx, hy in [(8, 80), (18, 82), (30, 80), (10, 92), (24, 94), (34, 90)]:
            self.add(TENTS, hx, hy, rng)
            self.add(CAMPFIRE, hx + 2, hy + 1, rng, solid=False)
            for x in range(hx - 1, hx + 4):
                if rng.random() < 0.6:
                    self.add(FENCES, x, hy + 3, rng, solid=False)
        # graveyard rows
        for gy in (98, 100, 102):
            for gx in range(8, 38, 3):
                if rng.random() < 0.6 and self.is_free(gx, gy, ('grass', 'meadow')):
                    self.add(GRAVES, gx, gy, rng)
        for _ in range(20):
            x, y = rng.randint(x0, x1), rng.randint(y0, y1)
            if self.is_free(x, y, ('grass', 'meadow')):
                self.add(TREES if rng.random() < 0.6 else BUSHES, x, y, rng)
        self.caches.append((7.5, 99.5, 'stim', 1))
        self.caches.append((38.5, 80.5, 'shards', 90))

    def _district_docks(self, rng):
        x0, y0, x1, y1 = DISTRICTS['docks']
        self.fill(x0, 96, x1, 104, 'dirt')
        for bx in range(50, 114, 9):
            self.add(BOATS, bx, rng.randint(106, 107), rng)
        for _ in range(30):
            x, y = rng.randint(x0 + 2, x1 - 2), rng.randint(88, 103)
            if self.is_free(x, y):
                self.add(rng.choice([CRATES, LOGS, BUCKETS, STALLS]), x, y, rng)
        self.weapons.append((102.5, 100.5, 'sledge'))
        self.caches.append((59.5, 103.5, 'shards', 120))
        self.caches.append((113.5, 93.5, 'hp', 20))

    def _district_overpass(self, rng):
        # The Unfinished Mile: an abandoned processional way
        x0, y0, x1, y1 = DISTRICTS['overpass']
        self.fill(x0 + 2, y0 + 2, x1 - 2, y1, 'flag2')
        for y in range(6, 46, 4):
            self.add(COLUMNS if rng.random() < 0.5 else COLUMNS_BROKEN, 4, y, rng)
            self.add(COLUMNS if rng.random() < 0.5 else COLUMNS_BROKEN, 12, y, rng)
        for _ in range(16):
            x, y = rng.randint(5, 11), rng.randint(4, 46)
            if self.is_free(x, y):
                self.add(RUBBLE, x, y, rng)
        self.clear_rect(5, 20, 12, 32)
        self.bosses['warden'] = dict(center=(8.5, 26.0), radius=5.5, kind='warden')
        self.weapons.append((9.5, 40.5, 'spear'))
        self.caches.append((4.5, 5.5, 'shards', 100))

    def _district_hub(self, rng):
        # the Foundry Yard — where you woke
        self.fill(12, 54, 24, 68, 'dirt')
        self.add(TENTS, 13, 56, rng)
        self.add(TENTS, 21, 55, rng)
        self.add(CAMPFIRE, 16, 60, rng, solid=False)
        self.add(ANVIL, 14, 62, rng)
        self.add(CRATES, 12, 59, rng)
        self.add(LOGS, 22, 66, rng)
        for x in range(11, 17):
            self.add(FENCES, x, 53, rng, solid=False)
        self.beacons.append((17.5, 63.5, 'hub'))

    def _wilds(self, rng):
        # scatter trees/rocks/plants across the commons
        for _ in range(420):
            x, y = rng.randint(2, self.w - 3), rng.randint(2, 103)
            if not self.is_free(x, y, ('grass', 'meadow')):
                continue
            if any(abs(x - b['center'][0]) < b['radius'] + 3 and
                   abs(y - b['center'][1]) < b['radius'] + 3 for b in self.bosses.values()):
                continue
            r = rng.random()
            if r < 0.5:
                self.add(TREES, x, y, rng)
            elif r < 0.7:
                self.add(rng.choice([PLANTS, BUSHES, FERNS, GOLD_BUSH]), x, y, rng, solid=False)
            elif r < 0.8:
                self.add(ROCKS, x, y, rng)
            elif r < 0.86:
                self.add(STUMPS, x, y, rng)
            elif r < 0.92:
                self.add(RUBBLE, x, y, rng)
        # broken columns along the paved core roads
        for x in self.V_ROADS:
            if 42 <= x <= 90:
                for y in range(6, 76, 7):
                    if rng.random() < 0.4 and self.is_free(x - 1, y):
                        self.add(COLUMNS_BROKEN, x - 1, y, rng)

    def _population(self, rng):
        def spawn_in(name, kind, count):
            x0, y0, x1, y1 = DISTRICTS[name]
            placed = tries = 0
            while placed < count and tries < count * 50:
                tries += 1
                x = rng.uniform(x0 + 1, x1 - 1)
                y = rng.uniform(y0 + 1, y1 - 1)
                if self.solid[int(y)][int(x)] or self.kind[int(y)][int(x)] == 'water':
                    continue
                if any(abs(x - bx) < 8 and abs(y - by) < 8 for bx, by, _ in self.beacons):
                    continue
                if any(abs(x - b['center'][0]) < b['radius'] + 2 and
                       abs(y - b['center'][1]) < b['radius'] + 2 for b in self.bosses.values()):
                    continue
                sx, sy = self.spawn
                if abs(x - sx) < 7 and abs(y - sy) < 7:
                    continue
                self.enemy_spawns.append((kind, x, y, rng.uniform(2.5, 4.5)))
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
        for bx, by, name in [(50.5, 54.5, 'downtown'), (21.5, 30.5, 'market'),
                             (49.5, 27.5, 'plaza'), (85.5, 49.5, 'park'),
                             (20.5, 85.5, 'suburbs'), (60.5, 92.5, 'docks'),
                             (84.5, 30.5, 'tower')]:
            self.clear_rect(int(bx) - 1, int(by) - 1, int(bx) + 1, int(by) + 1)
            self.beacons.append((bx, by, name))
        spots = [(13.5, 55.8), (49.5, 10.5), (24.5, 91.5), (52.5, 50.5),
                 (22.5, 24.5), (98.5, 30.5), (85.5, 58.5), (30.5, 80.5),
                 (88.5, 26.5), (8.5, 36.5)]
        for i, (x, y) in enumerate(spots):
            if self.solid[int(y)][int(x)]:
                self.clear_rect(int(x), int(y), int(x), int(y))
            self.lore.append((x, y, i))
        self.npcs.append((19.5, 64.5, 'maya', 'npc_maya'))
        self.npcs.append((23.5, 32.5, 'cartographer', 'npc_cart'))
        for (x, y, _) in self.weapons:
            self.clear_rect(int(x), int(y), int(x), int(y))
        for item in self.caches:
            self.clear_rect(int(item[0]), int(item[1]), int(item[0]), int(item[1]))
