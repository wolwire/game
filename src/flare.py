"""Loader for Flare-engine assets (CC-BY-SA art from flare-game).

Parses Flare's tilesetdefs (tile=id,x,y,w,h,ox,oy) and animation defs
([name] sections with frame=idx,dir,x,y,w,h,ox,oy). Anchors follow Flare's
convention: blit at (screen_pos - offset).
"""
import os
import pygame

ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'flare')

_images = {}


def _img(rel):
    s = _images.get(rel)
    if s is None:
        s = pygame.image.load(os.path.join(ROOT, rel)).convert_alpha()
        _images[rel] = s
    return s


class Tileset:
    def __init__(self, def_name):
        self.tiles = {}          # id -> (img_rel, x, y, w, h, ox, oy)
        self._cache = {}
        img = None
        with open(os.path.join(ROOT, 'tilesetdefs', def_name)) as f:
            for line in f:
                line = line.strip()
                if line.startswith('img='):
                    img = line[4:]
                elif line.startswith('tile='):
                    parts = line[5:].split(',')
                    tid, x, y, w, h, ox, oy = (int(p) for p in parts[:7])
                    self.tiles[tid] = (img, x, y, w, h, ox, oy)

    def get(self, tid):
        """Returns (surface, (ox, oy)) — blit at screen_pos - offset."""
        got = self._cache.get(tid)
        if got is None:
            rel, x, y, w, h, ox, oy = self.tiles[tid]
            surf = _img(rel).subsurface((x, y, w, h))
            got = (surf, (ox, oy))
            self._cache[tid] = got
        return got

    def ids(self):
        return sorted(self.tiles.keys())


class AnimSet:
    """One Flare animation definition (an enemy, or one avatar layer)."""

    def __init__(self, def_path):
        self.images = {}         # anim_name or '' -> img rel path
        self.anims = {}          # name -> dict(frames, duration_s, type, data)
        self._cache = {}
        cur = None
        with open(os.path.join(ROOT, def_path)) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('image='):
                    val = line[6:]
                    if ',' in val:
                        rel, name = val.split(',', 1)
                        self.images[name] = rel
                    else:
                        self.images[''] = val
                elif line.startswith('[') and line.endswith(']'):
                    cur = line[1:-1]
                    self.anims[cur] = {'frames': 1, 'duration': 1.0,
                                       'type': 'looped', 'data': {}}
                elif cur and '=' in line:
                    k, v = line.split('=', 1)
                    a = self.anims[cur]
                    if k == 'frames':
                        a['frames'] = int(v)
                    elif k == 'duration':
                        ms = v.replace('ms', '')
                        a['duration'] = max(0.05, int(ms) / 1000.0)
                    elif k == 'type':
                        a['type'] = v
                    elif k == 'frame':
                        toks = v.split(',')
                        p = [int(t) for t in toks[:8]]
                        imgkey = toks[8] if len(toks) > 8 else None
                        idx, d = p[0], p[1]
                        a['data'].setdefault(d, {})[idx] = tuple(p[2:8]) + (imgkey,)

    def has(self, name):
        return name in self.anims

    def frame(self, name, direction, t, freeze_last=False):
        """Sample animation `name` at time t (seconds since anim start).
        Returns (surface, (ox, oy)) or None."""
        a = self.anims.get(name)
        if a is None:
            return None
        n = a['frames']
        ft = a['duration'] / n
        i = int(t / ft)
        if a['type'] == 'play_once':
            i = min(i, n - 1) if freeze_last or True else i
            i = min(i, n - 1)
        elif a['type'] == 'back_forth':
            cyc = i % (2 * n - 2) if n > 1 else 0
            i = cyc if cyc < n else 2 * n - 2 - cyc
        else:
            i = i % n
        data = a['data'].get(direction)
        if not data:
            return None
        fr = data.get(i) or data.get(min(data.keys()))
        key = (name, direction, i)
        got = self._cache.get(key)
        if got is None:
            x, y, w, h, ox, oy, imgkey = fr
            rel = self.images.get(imgkey or name, self.images.get('', None))
            surf = _img(rel).subsurface((x, y, w, h))
            got = (surf, (ox, oy))
            self._cache[key] = got
        return got

    def duration(self, name):
        a = self.anims.get(name)
        return a['duration'] if a else 0.5


_tilesets = {}
_animsets = {}


def tileset(name):
    t = _tilesets.get(name)
    if t is None:
        t = Tileset(name)
        _tilesets[name] = t
    return t


def animset(path):
    a = _animsets.get(path)
    if a is None:
        a = AnimSet(path)
        _animsets[path] = a
    return a
