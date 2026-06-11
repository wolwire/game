"""Open-world map generation for Meridian City.

The world is a 120x120 tile city split into districts, generated
deterministically from a fixed seed so the layout is hand-tunable:

      [plaza: Cathedral Plaza]      [tower: Helix Tower]
  [market]      [downtown core grid]      [park: Echo Park]
  [hub: start]  [overpass: Unfinished Mile (Warden)]
  [suburbs: The Long Saturday]      [docks: Graveyard of Cranes]
                       [water]
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
    # name: (x0, y0, x1, y1)
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
    # later entries win; check in priority order (small zones first)
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
        self.beacons = []        # (x, y, name)
        self.lore = []           # (x, y, index) — index into LORE_FRAGMENTS
        self.npcs = []           # (x, y, key, style)
        self.enemy_spawns = []   # (kind, x, y, radius)
        self.bosses = {}         # key -> dict(center, radius, kind)
        self.gate_tiles = []     # tower fog gate
        self.spawn = (17.5, 61.5)
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

    def add_prop(self, kind, x, y, variant=0, solid=True, axis='x', seed=0):
        self.props.append(Prop(kind, x, y, variant, solid, axis, seed))
        if solid:
            self.solid[int(y)][int(x)] = True

    def is_clear(self, x0, y0, x1, y1, kinds=('asphalt', 'lot', 'grass', 'plaza', 'sidewalk')):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if not self.in_bounds(x, y) or self.solid[y][x] or self.ground[y][x] not in kinds:
                    return False
        return True

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
        self._scatter_streetlife(rng)
        self._population(rng)
        self._pickups_and_npcs(rng)

    def _terrain_base(self, rng):
        self.fill(0, 0, self.w - 1, self.h - 1, 'grass')
        # urban core gets pavement base
        self.fill(2, 2, self.w - 3, 94, 'asphalt')
        # southern waterfront
        self.fill(0, 109, self.w - 1, self.h - 1, 'water')
        self.set_solid(0, 109, self.w - 1, self.h - 1)
        self.fill(0, 105, self.w - 1, 108, 'sand')
        # hard world border
        self.set_solid(0, 0, self.w - 1, 0)
        self.set_solid(0, 0, 0, self.h - 1)
        self.set_solid(self.w - 1, 0, self.w - 1, self.h - 1)
        self.set_solid(0, self.h - 1, self.w - 1, self.h - 1)

    def _road_v(self, x, y0, y1, width=3):
        self.fill(x, y0, x + width - 1, y1, 'road')
        self.fill(x - 1, y0, x - 1, y1, 'sidewalk')
        self.fill(x + width, y0, x + width, y1, 'sidewalk')
        mid = x + width // 2
        for y in range(y0, y1 + 1):
            if y % 2 == 0:
                self.decals[(mid, y)] = 'dash_y'

    def _road_h(self, y, x0, x1, width=3):
        self.fill(x0, y, x1, y + width - 1, 'road')
        self.fill(x0, y - 1, x1, y - 1, 'sidewalk')
        self.fill(x0, y + width, x1, y + width, 'sidewalk')
        mid = y + width // 2
        for x in range(x0, x1 + 1):
            if x % 2 == 0:
                self.decals[(x, mid)] = 'dash_x'

    def _roads(self, rng):
        # arterial grid
        for x in (14, 28, 42, 58, 74, 90, 106):
            self._road_v(x, 4, 104)
        for y in (14, 30, 46, 62, 78, 94):
            self._road_h(y, 3, 116)
        # manholes at some intersections
        for x in (15, 43, 75, 91):
            for y in (31, 63):
                if rng.random() < 0.7:
                    self.decals[(x + 1, y + 1)] = 'manhole'

    def _block_buildings(self, rng, x0, y0, x1, y1, styles, min_st, max_st, density=0.8):
        """Place buildings around the rim of a city block."""
        attempts = 14
        for _ in range(attempts):
            if rng.random() > density:
                continue
            fw, fh = rng.randint(2, 4), rng.randint(2, 4)
            bx = rng.randint(x0, max(x0, x1 - fw))
            by = rng.randint(y0, max(y0, y1 - fh))
            if self.is_clear(bx - 1, by - 1, bx + fw, by + fh, ('asphalt', 'lot', 'grass')):
                self.add_building(bx, by, fw, fh, rng.randint(min_st, max_st),
                                  rng.choice(styles), rng.randint(0, 10 ** 9))

    def _district_downtown(self, rng):
        for bx0, by0 in [(31, 33), (45, 33), (61, 33), (31, 49), (61, 49),
                         (45, 65), (61, 65), (31, 65)]:
            self._block_buildings(rng, bx0, by0, bx0 + 9, by0 + 9,
                                  ('concrete', 'glass', 'shop'), 3, 7)
        # central downtown beacon block kept open (45,49)-(54,58)
        self.fill(46, 50, 55, 58, 'plaza')

    def _district_market(self, rng):
        x0, y0, x1, y1 = DISTRICTS['market']
        for bx0, by0 in [(6, 18), (20, 18), (6, 34), (22, 34)]:
            self._block_buildings(rng, bx0, by0, bx0 + 7, by0 + 8,
                                  ('shop', 'brick'), 2, 4, density=0.7)
        # market lane: stalls (crates) along a pedestrian street
        self.fill(17, 20, 25, 27, 'plaza')
        for i in range(7):
            x = 18 + (i % 4) * 2
            y = 21 + (i // 4) * 4
            if not self.solid[y][x]:
                self.add_prop('crate', x + 0.5, y + 0.5, variant=i)

    def _district_plaza(self, rng):
        # Cathedral Plaza: large open square for the Chorister fight
        self.fill(46, 6, 70, 26, 'plaza')
        self.set_solid(46, 6, 70, 26, False)
        self.buildings = [b for b in self.buildings
                          if not (44 <= b.x <= 72 and 4 <= b.y <= 28)]
        self.add_building(46, 4, 5, 3, 6, 'concrete', 101)
        self.add_building(64, 4, 5, 3, 6, 'concrete', 102)
        self.add_prop('fountain', 58.0, 16.0, solid=True)
        self.solid[16][58] = True
        for x, y in [(50, 9), (66, 9), (50, 23), (66, 23)]:
            self.add_prop('lamppost', x + 0.5, y + 0.5)
        self.bosses['chorister'] = dict(center=(58.0, 18.5), radius=9.5, kind='chorister')

    def _district_tower(self, rng):
        # Helix Tower at the top: huge tower + approach plaza + fog gate
        self.fill(80, 4, 114, 32, 'plaza')
        self.add_building(92, 6, 10, 8, 14, 'tower', 777)
        self.add_building(82, 6, 4, 5, 8, 'glass', 778)
        self.add_building(108, 6, 4, 5, 8, 'glass', 779)
        # arena in front of tower
        self.bosses['archivist'] = dict(center=(97.0, 21.0), radius=8.0, kind='archivist')
        # fog gate across the approach road (south entrance of tower district)
        for x in range(88, 107):
            self.gate_tiles.append((x, 33))
        for x, y in [(86, 18), (108, 18), (90, 28), (104, 28)]:
            self.add_prop('lamppost', x + 0.5, y + 0.5)

    def _district_park(self, rng):
        x0, y0, x1, y1 = DISTRICTS['park']
        self.fill(x0, y0, x1, y1, 'grass')
        self.set_solid(x0, y0, x1, y1, False)
        self.buildings = [b for b in self.buildings
                          if not (x0 - 2 <= b.x <= x1 and y0 - 2 <= b.y <= y1)]
        # paths
        self.fill(x0 + 2, 58, x1 - 2, 59, 'dirt')
        self.fill(94, y0 + 2, 95, y1 - 2, 'dirt')
        for _ in range(46):
            x, y = rng.randint(x0 + 1, x1 - 1), rng.randint(y0 + 1, y1 - 1)
            if not self.solid[y][x] and self.ground[y][x] == 'grass':
                kind = 'tree' if rng.random() < 0.8 else 'dead_tree'
                self.add_prop(kind, x + 0.5, y + 0.5, variant=rng.randint(0, 4))
        for x, y in [(84, 58), (104, 58), (94, 48), (94, 70)]:
            if not self.solid[y][x]:
                self.add_prop('bench', x + 0.5, y + 0.5)
        # Patient Zero's clearing
        for yy in range(62, 71):
            for xx in range(96, 107):
                self.solid[yy][xx] = False
        self.props = [p for p in self.props if not (96 <= p.x <= 107 and 62 <= p.y <= 71)]
        self.fill(98, 63, 105, 69, 'dirt')
        self.bosses['hound'] = dict(center=(101.5, 66.0), radius=6.5, kind='hound')

    def _district_suburbs(self, rng):
        x0, y0, x1, y1 = DISTRICTS['suburbs']
        self.fill(x0, y0, x1, y1, 'grass')
        self._road_h(88, x0, x1)
        self._road_v(22, y0, y1 - 2)
        for bx in range(x0 + 2, x1 - 3, 6):
            for by in (y0 + 3, 92):
                if rng.random() < 0.85 and self.is_clear(bx - 1, by - 1, bx + 3, by + 3, ('grass', 'asphalt', 'lot')):
                    self.add_building(bx, by, rng.randint(2, 3), 2,
                                      rng.randint(1, 2), 'brick', rng.randint(0, 10 ** 9))
        for _ in range(14):
            x, y = rng.randint(x0, x1), rng.randint(y0, y1)
            if not self.solid[y][x] and self.ground[y][x] == 'grass':
                self.add_prop('tree', x + 0.5, y + 0.5, variant=rng.randint(0, 4))

    def _district_docks(self, rng):
        x0, y0, x1, y1 = DISTRICTS['docks']
        self.fill(x0, y0, x1, min(y1, 104), 'lot')
        for bx0 in (50, 70, 92):
            self._block_buildings(rng, bx0, 80, bx0 + 12, 88,
                                  ('industrial',), 2, 3, density=0.6)
        # container stacks
        for _ in range(26):
            x, y = rng.randint(x0 + 2, x1 - 2), rng.randint(90, 102)
            if self.is_clear(x, y, x + 1, y, ('lot',)):
                self.add_prop('crate', x + 0.5, y + 0.5, variant=rng.randint(0, 9))
        for x in range(50, 110, 14):
            if not self.solid[97][x]:
                self.add_prop('lamppost', x + 0.5, 97.5)

    def _district_overpass(self, rng):
        # The Unfinished Mile: a dead highway strip — the Warden's domain
        x0, y0, x1, y1 = DISTRICTS['overpass']
        self.fill(x0 + 2, y0 + 2, x1 - 2, y1, 'road')
        for y in range(y0 + 2, y1, 2):
            self.decals[(8, y)] = 'dash_y'
        for y in range(6, 40, 7):
            self.add_prop('barricade', 5.5, y + 0.5)
            self.add_prop('barricade', 11.5, y + 2.5)
        for y in range(8, 44, 9):
            self.add_prop('car', 8.5, y + 0.5, axis='y', seed=rng.randint(0, 10 ** 9))
        # Warden arena: cleared stretch
        for yy in range(20, 32):
            for xx in range(4, 13):
                self.solid[yy][xx] = False
        self.props = [p for p in self.props if not (4 <= p.x <= 13 and 19 <= p.y <= 32)]
        self.bosses['warden'] = dict(center=(8.5, 26.0), radius=6.0, kind='warden')

    def _district_hub(self, rng):
        # Maintenance Hub 7 — safe start zone
        x0, y0, x1, y1 = DISTRICTS['hub']
        self.fill(x0, y0, x1, y1, 'lot')
        self.add_building(10, 52, 4, 3, 2, 'industrial', 31)
        self.add_building(20, 52, 3, 3, 2, 'industrial', 32)
        self.add_prop('crate', 12.5, 58.5)
        self.add_prop('crate', 13.5, 59.0)
        self.add_prop('dumpster', 21.5, 66.5)
        self.beacons.append((17.5, 63.5, 'hub'))

    def _scatter_streetlife(self, rng):
        # wrecked cars on roads, lampposts and hydrants on sidewalks, debris
        for _ in range(70):
            x, y = rng.randint(4, self.w - 5), rng.randint(5, 102)
            if self.ground[y][x] == 'road' and not self.solid[y][x] and rng.random() < 0.6:
                near_boss = any(abs(x - b['center'][0]) < 9 and abs(y - b['center'][1]) < 9
                                for b in self.bosses.values())
                if not near_boss:
                    self.add_prop('car', x + 0.5, y + 0.5,
                                  axis=rng.choice('xy'), seed=rng.randint(0, 10 ** 9))
        for _ in range(120):
            x, y = rng.randint(3, self.w - 4), rng.randint(4, 103)
            if self.ground[y][x] == 'sidewalk' and not self.solid[y][x]:
                r = rng.random()
                if r < 0.35:
                    self.add_prop('lamppost', x + 0.5, y + 0.5)
                elif r < 0.45:
                    self.add_prop('hydrant', x + 0.5, y + 0.5)
                elif r < 0.52:
                    self.add_prop('traffic_light', x + 0.5, y + 0.5)
                elif r < 0.60:
                    self.add_prop('bus_stop', x + 0.5, y + 0.5)
                elif r < 0.72:
                    self.add_prop('debris', x + 0.5, y + 0.5, solid=False)
        for _ in range(60):
            x, y = rng.randint(3, self.w - 4), rng.randint(4, 103)
            if self.ground[y][x] in ('asphalt', 'lot') and not self.solid[y][x] and rng.random() < 0.4:
                self.add_prop('debris', x + 0.5, y + 0.5, solid=False)

    def _population(self, rng):
        """Enemy spawn points per district."""
        def spawn_in(name, kind, count, keep_out=3.0):
            x0, y0, x1, y1 = DISTRICTS[name]
            placed = 0
            tries = 0
            while placed < count and tries < count * 40:
                tries += 1
                x = rng.uniform(x0 + 1, x1 - 1)
                y = rng.uniform(y0 + 1, y1 - 1)
                if self.solid[int(y)][int(x)] or self.ground[int(y)][int(x)] == 'water':
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
        # beacons (bonfires) — hub beacon added in _district_hub
        for bx, by, name in [(50.5, 54.5, 'downtown'), (21.5, 30.5, 'market'),
                             (49.5, 27.5, 'plaza'), (85.5, 49.5, 'park'),
                             (20.5, 85.5, 'suburbs'), (60.5, 92.5, 'docks'),
                             (84.5, 30.5, 'tower')]:
            x, y = int(bx), int(by)
            self.solid[y][x] = False
            self.props = [p for p in self.props
                          if not (abs(p.x - bx) < 1.6 and abs(p.y - by) < 1.6)]
            self.beacons.append((bx, by, name))
        # lore fragments — placed at story-relevant spots
        spots = [(13.5, 55.5), (49.5, 10.5), (24.5, 91.5), (52.5, 50.5),
                 (22.5, 24.5), (98.5, 8.5 + 24), (85.5, 58.5), (30.5, 80.5),
                 (88.5, 26.5), (8.5, 36.5)]
        for i, (x, y) in enumerate(spots):
            self.solid[int(y)][int(x)] = False
            self.lore.append((x, y, i))
        # NPCs
        self.npcs.append((19.5, 64.5, 'maya', 'npc_maya'))
        self.npcs.append((23.5, 32.5, 'cartographer', 'npc_cart'))
