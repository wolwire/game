"""Game-side sprite layer over the Flare assets: entity rendering with
layered avatar equipment, enemy sheets, and world-object tiles."""
import math
import pygame
from src import flare
from src.iso import world_to_screen, facing_octant

# my screen octant (0=E 1=SE 2=S 3=SW 4=W 5=NW 6=N 7=NE) -> flare direction
# flare: 0=SW 1=W 2=NW 3=N 4=NE 5=E 6=SE 7=S
OCT_TO_FLARE = {0: 5, 1: 6, 2: 7, 3: 0, 4: 1, 5: 2, 6: 3, 7: 4}

# flare hero layer order per flare direction (main = weapon)
LAYER_ORDER = {
    0: ('main', 'feet', 'legs', 'hands', 'chest', 'head'),   # SW
    1: ('main', 'feet', 'legs', 'hands', 'chest', 'head'),   # W
    2: ('main', 'feet', 'legs', 'hands', 'chest', 'head'),   # NW
    3: ('feet', 'legs', 'hands', 'chest', 'head', 'main'),   # N
    4: ('feet', 'legs', 'hands', 'chest', 'head', 'main'),   # NE
    5: ('feet', 'legs', 'hands', 'chest', 'head', 'main'),   # E
    6: ('feet', 'legs', 'hands', 'main', 'chest', 'head'),   # SE
    7: ('main', 'feet', 'legs', 'hands', 'chest', 'head'),   # S
}

AVATAR_DIR = 'animations/avatar/male/'
PLAYER_LAYERS = {
    'feet': 'leather_boots',
    'legs': 'leather_pants',
    'chest': 'leather_chest',
    'hands': 'default_hands',
    'head': 'head_short',
}

ENEMY_SHEETS = {
    'husk':      'animations/enemies/zombie.txt',
    'stalker':   'animations/enemies/skeleton.txt',
    'riot':      'animations/enemies/hobgoblin.txt',
    'feral':     'animations/enemies/goblin.txt',
    'drone':     'animations/enemies/skeleton_archer.txt',
    'warden':    'animations/enemies/minotaur.txt',
    'chorister': 'animations/enemies/skeleton_mage_high_boss.txt',
    'hound':     'animations/enemies/antlion.txt',
    'archivist': 'animations/enemies/skeleton_knight_boss.txt',
    'npc_maya':  'animations/npcs/peasant_woman1.txt',
    'npc_cart':  'animations/npcs/guild_man.txt',
}


def warm_up():
    """Pre-load all animation sets (decodes the big sheets once)."""
    for p in ENEMY_SHEETS.values():
        flare.animset(p)
    for s in PLAYER_LAYERS.values():
        flare.animset(AVATAR_DIR + s + '.txt')


def flare_dir(fx, fy):
    return OCT_TO_FLARE[facing_octant(fx, fy)]


def _blit_frame(surf, fr, sx, sy, alpha=255, flash=0.0):
    if fr is None:
        return
    img, (ox, oy) = fr
    if flash > 0:
        img = img.copy()
        img.fill((int(110 * flash),) * 3 + (0,), special_flags=pygame.BLEND_RGB_ADD)
    if alpha < 255:
        img = img.copy()
        img.set_alpha(alpha)
    surf.blit(img, (sx - ox, sy - oy))


def draw_shadow(surf, sx, sy, scale=1.0):
    w, h = int(56 * scale), int(22 * scale)
    sh = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
    surf.blit(sh, (sx - w // 2, sy - h // 2))


def draw_enemy(surf, ox, oy, style, x, y, fx, fy, anim, t, flash=0.0, scale=1.0):
    """anim: (name, t_or_progress, mode) where mode 'loop' uses time directly,
    'once' maps progress 0..1 onto the anim duration."""
    aset = flare.animset(ENEMY_SHEETS[style])
    name, tt, mode = anim
    if not aset.has(name):
        name = 'stance'
    if mode == 'once':
        tt = max(0.0, min(0.999, tt)) * aset.duration(name)
    d = flare_dir(fx, fy)
    sx, sy = world_to_screen(x, y)
    sx += ox
    sy += oy
    if name not in ('die', 'critdie'):
        draw_shadow(surf, sx, sy, scale)
    fr = aset.frame(name, d, tt)
    _blit_frame(surf, fr, sx, sy, flash=flash)


def draw_player(surf, ox, oy, x, y, fx, fy, anim, t, weapon_sheet, alpha=255,
                roll=False):
    d = flare_dir(fx, fy)
    name, tt, mode = anim
    sx, sy = world_to_screen(x, y)
    sx += ox
    sy += oy
    draw_shadow(surf, sx, sy)
    layers = []
    for kind in LAYER_ORDER[d]:
        if kind == 'main':
            if weapon_sheet:
                layers.append(flare.animset(AVATAR_DIR + weapon_sheet + '.txt'))
        else:
            layers.append(flare.animset(AVATAR_DIR + PLAYER_LAYERS[kind] + '.txt'))
    for aset in layers:
        nm = name if aset.has(name) else 'stance'
        ftt = tt
        if mode == 'once':
            ftt = max(0.0, min(0.999, tt)) * aset.duration(nm)
        fr = aset.frame(nm, d, ftt)
        _blit_frame(surf, fr, sx, sy, alpha=alpha)


# ----------------------------------------------------------- world objects
GRASS = 'tileset_grassland.txt'
RUINS = 'tileset_ruins.txt'


def draw_tile(surf, ts_name, tid, sx, sy):
    """Blit a flare tile whose grid cell top-corner projects to (sx, sy)."""
    img, (tox, toy) = flare.tileset(ts_name).get(tid)
    surf.blit(img, (sx - tox, sy + 48 - toy))


def tile_img(ts_name, tid):
    return flare.tileset(ts_name).get(tid)
