"""All HUD and screen-level UI: bars, banners, dialogue, beacon menu,
minimap, text screens."""
import math
import pygame
from src.constants import *

pygame.font.init()
F_SMALL = pygame.font.SysFont('dejavusansmono', 14)
F_MED = pygame.font.SysFont('dejavusansmono', 18)
F_BIG = pygame.font.SysFont('dejavusansmono', 30, bold=True)
F_TITLE = pygame.font.SysFont('dejavusansmono', 56, bold=True)


def text(surf, s, x, y, font=F_MED, color=C_TEXT, center=False, shadow=True):
    img = font.render(s, True, color)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    if shadow:
        sh = font.render(s, True, (0, 0, 0))
        surf.blit(sh, (r.x + 1, r.y + 2))
    surf.blit(img, r)
    return r


def bar(surf, x, y, w, h, frac, color, bg, border=(20, 22, 26)):
    pygame.draw.rect(surf, bg, (x, y, w, h))
    if frac > 0:
        pygame.draw.rect(surf, color, (x, y, int(w * max(0.0, min(1.0, frac))), h))
    pygame.draw.rect(surf, border, (x, y, w, h), 2)


def draw_hud(surf, player, area_name):
    bar(surf, 24, 22, 280 * (player.max_hp / 240), 16, player.hp / player.max_hp, C_HP, C_HP_BG)
    bar(surf, 24, 44, 240 * (player.max_stamina / 200), 12,
        player.stamina / player.max_stamina, C_STAM, C_STAM_BG)
    # stims
    for i in range(player.stim_max):
        col = C_ACCENT2 if i < player.stims else (50, 48, 44)
        pygame.draw.rect(surf, col, (24 + i * 22, 64, 16, 20), border_radius=4)
        pygame.draw.rect(surf, (20, 20, 22), (24 + i * 22, 64, 16, 20), 2, border_radius=4)
    text(surf, 'Q', 24 + player.stim_max * 22 + 6, 66, F_SMALL, C_TEXT_DIM)
    # shards
    pygame.draw.circle(surf, C_SHARD, (38, 106), 7)
    pygame.draw.circle(surf, (230, 245, 255), (38, 106), 3)
    text(surf, f"{player.shards}", 52, 96, F_MED, C_SHARD)
    text(surf, f"LV {player.level}", 52, 116, F_SMALL, C_TEXT_DIM)
    # weapon slot
    w = player.weapon
    pygame.draw.rect(surf, (16, 18, 24, 200), (24, HEIGHT - 64, 230, 40), border_radius=6)
    pygame.draw.rect(surf, (60, 68, 84), (24, HEIGHT - 64, 230, 40), 2, border_radius=6)
    text(surf, w['name'], 38, HEIGHT - 58, F_MED, C_TEXT)
    if len(player.inventory) > 1:
        text(surf, f"[{player.weapon_idx + 1}/{len(player.inventory)}]  R — switch",
             38, HEIGHT - 38, F_SMALL, C_TEXT_DIM)
    else:
        text(surf, w['desc'], 38, HEIGHT - 38, F_SMALL, C_TEXT_DIM)
    # area
    img = F_MED.render(area_name, True, C_TEXT_DIM)
    surf.blit(img, (WIDTH - img.get_width() - 24, 20))


def draw_boss_bar(surf, boss, name):
    w = 640
    x = (WIDTH - w) // 2
    y = HEIGHT - 86
    text(surf, name, WIDTH // 2, y - 14, F_MED, C_BOSS, center=True)
    bar(surf, x, y, w, 14, boss.hp / boss.max_hp, C_BOSS, (50, 40, 18))


def draw_prompt(surf, s):
    text(surf, s, WIDTH // 2, HEIGHT - 140, F_MED, C_ACCENT, center=True)


def draw_banner(surf, title, sub, t):
    """Area-name banner, fades with t in [0,1]."""
    a = min(1.0, t * 4) if t < 0.75 else max(0.0, (1.0 - t) * 4)
    if a <= 0:
        return
    img = F_BIG.render(title, True, C_TEXT)
    img.set_alpha(int(255 * a))
    surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))
    if sub:
        img2 = F_SMALL.render(sub, True, C_TEXT_DIM)
        img2.set_alpha(int(255 * a))
        surf.blit(img2, img2.get_rect(center=(WIDTH // 2, 184)))


def draw_center_flash(surf, s, color=C_ACCENT):
    text(surf, s, WIDTH // 2, HEIGHT // 2 - 120, F_BIG, color, center=True)


def overlay(surf, alpha=180, color=(8, 9, 12)):
    o = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    o.fill((*color, alpha))
    surf.blit(o, (0, 0))


def draw_text_screen(surf, lines, title=None, footer="E / ENTER — continue", t=1.0):
    overlay(surf, 215)
    y = 130
    if title:
        text(surf, title, WIDTH // 2, 80, F_BIG, C_ACCENT2, center=True)
    shown = int(len(lines) * min(1.0, t))
    for i, line in enumerate(lines[:shown]):
        text(surf, line, WIDTH // 2, y + i * 26, F_MED, C_TEXT, center=True)
    if footer and t >= 0.99:
        text(surf, footer, WIDTH // 2, HEIGHT - 60, F_SMALL, C_TEXT_DIM, center=True)


def draw_dialogue(surf, name, lines, page_done):
    h = 170
    pygame.draw.rect(surf, (12, 13, 17), (80, HEIGHT - h - 30, WIDTH - 160, h), border_radius=8)
    pygame.draw.rect(surf, (60, 70, 86), (80, HEIGHT - h - 30, WIDTH - 160, h), 2, border_radius=8)
    text(surf, name, 104, HEIGHT - h - 18, F_MED, C_ACCENT2)
    for i, line in enumerate(lines):
        text(surf, line, 104, HEIGHT - h + 12 + i * 24, F_MED, C_TEXT)
    if page_done:
        text(surf, "E — continue", WIDTH - 240, HEIGHT - 56, F_SMALL, C_TEXT_DIM)


def draw_beacon_menu(surf, player, sel, message):
    overlay(surf, 170)
    text(surf, "RELAY BEACON", WIDTH // 2, 110, F_BIG, C_GRACE, center=True)
    text(surf, message, WIDTH // 2, 152, F_SMALL, C_TEXT_DIM, center=True)
    cost = level_cost(player.level)
    rows = [
        (f"VIGOR      {player.vigor:>3}   (+{VIGOR_HP} max HP)", True),
        (f"ENDURANCE  {player.endurance:>3}   (+{ENDURANCE_STAM} max stamina)", True),
        (f"STRENGTH   {player.strength:>3}   (+{int(STRENGTH_DMG*100)}% damage)", True),
        ("LEAVE", True),
    ]
    y0 = 240
    text(surf, f"Shards: {player.shards}    Next level: {cost}", WIDTH // 2, 200,
         F_MED, C_SHARD, center=True)
    for i, (label, _) in enumerate(rows):
        col = C_ACCENT if i == sel else C_TEXT
        if i < 3 and player.shards < cost:
            col = C_TEXT_DIM if i != sel else (140, 170, 190)
        text(surf, ("> " if i == sel else "  ") + label, WIDTH // 2 - 220, y0 + i * 44, F_MED, col)
    text(surf, "W/S — select   E/ENTER — confirm", WIDTH // 2, HEIGHT - 80,
         F_SMALL, C_TEXT_DIM, center=True)


MINIMAP_COLORS = {
    'grass': (58, 84, 46), 'meadow': (70, 92, 48), 'dirt': (104, 84, 58),
    'flag': (108, 106, 110), 'flag2': (92, 92, 96), 'mosaic': (96, 110, 116),
    'reddirt': (120, 70, 52), 'rubblef': (84, 78, 72), 'water': (38, 64, 96),
}

_minimap_base = None
MAP_SCALE = 3


def build_minimap(world):
    global _minimap_base
    scale = MAP_SCALE
    surf = pygame.Surface((world.w * scale, world.h * scale))
    for y in range(world.h):
        for x in range(world.w):
            c = MINIMAP_COLORS.get(world.kind[y][x], (60, 60, 60))
            if world.solid[y][x] and world.kind[y][x] != 'water':
                c = (max(0, c[0] - 22), max(0, c[1] - 22), max(0, c[2] - 22))
            surf.fill(c, (x * scale, y * scale, scale, scale))
    _minimap_base = surf
    return surf


def draw_map(surf, world, player, bosses_defeated):
    overlay(surf, 200)
    base = _minimap_base if _minimap_base is not None else build_minimap(world)
    scale = MAP_SCALE
    mw, mh = base.get_size()
    mx, my = (WIDTH - mw) // 2, (HEIGHT - mh) // 2
    surf.blit(base, (mx, my))
    pygame.draw.rect(surf, (80, 90, 104), (mx, my, mw, mh), 2)
    for bx, by, name in world.beacons:
        pygame.draw.circle(surf, C_GRACE, (mx + int(bx * scale), my + int(by * scale)), 4)
    for key, b in world.bosses.items():
        if key not in bosses_defeated:
            cx, cy = b['center']
            pygame.draw.circle(surf, C_DANGER, (mx + int(cx * scale), my + int(cy * scale)), 4)
    px, py = mx + int(player.x * scale), my + int(player.y * scale)
    pygame.draw.circle(surf, (255, 255, 255), (px, py), 5, 2)
    pygame.draw.circle(surf, C_ACCENT, (px, py), 2)
    text(surf, "MERIDIAN CITY — M to close", WIDTH // 2, my - 24, F_MED, C_TEXT, center=True)
    text(surf, "blue: beacons   red: something old and angry   white: you",
         WIDTH // 2, my + mh + 20, F_SMALL, C_TEXT_DIM, center=True)


def draw_death(surf, msg, t):
    overlay(surf, min(220, int(t * 300)))
    img = F_TITLE.render(msg, True, (170, 30, 36))
    img.set_alpha(min(255, int(t * 300)))
    surf.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
    if t > 1.2:
        text(surf, "the beacon prints you again — E / ENTER", WIDTH // 2, HEIGHT // 2 + 40,
             F_SMALL, C_TEXT_DIM, center=True)


def draw_title(surf, t):
    surf.fill((10, 11, 15))
    # skyline silhouette
    import random as _r
    rng = _r.Random(7)
    for i in range(40):
        bw = rng.randint(30, 80)
        bh = rng.randint(60, 280)
        x = i * 34 - 40
        pygame.draw.rect(surf, (16, 18, 24), (x, HEIGHT - bh - 120, bw, bh + 200))
        for _ in range(bh // 40):
            wx = x + rng.randint(4, bw - 8)
            wy = HEIGHT - bh - 110 + rng.randint(0, bh - 10)
            if rng.random() < 0.5:
                pygame.draw.rect(surf, (150, 130, 70), (wx, wy, 3, 5))
    pulse = 0.5 + 0.5 * math.sin(t * 2)
    text(surf, "S T I L L W A K E", WIDTH // 2, 240, F_TITLE, C_ACCENT, center=True)
    text(surf, "a tale of the Stillness — the city of Meridian, three years in",
         WIDTH // 2, 300, F_MED, C_TEXT_DIM, center=True)
    col = (int(120 + 100 * pulse),) * 3
    text(surf, "PRESS ENTER", WIDTH // 2, 480, F_MED, col, center=True)
    text(surf, "a 2.5D isometric souls-like — WASD move / J K attack / SPACE roll", WIDTH // 2, HEIGHT - 50, F_SMALL,
         (70, 74, 84), center=True)


def draw_ending_choice(surf, lines, sel):
    overlay(surf, 225)
    y = 110
    for i, line in enumerate(lines):
        text(surf, line, WIDTH // 2, y + i * 26, F_MED, C_TEXT, center=True)
    opts = ["SEVER THE LATTICE — wake the city", "INHERIT THE LATTICE — keep the dream"]
    for i, o in enumerate(opts):
        col = C_ACCENT if sel == i else C_TEXT_DIM
        text(surf, ("> " if sel == i else "  ") + o, WIDTH // 2, 480 + i * 40, F_MED, col, center=True)
    text(surf, "W/S — choose    E/ENTER — decide", WIDTH // 2, HEIGHT - 60,
         F_SMALL, C_TEXT_DIM, center=True)


def draw_lock_marker(surf, sx, sy, t):
    r = 14 + math.sin(t * 6) * 2
    pygame.draw.circle(surf, C_ACCENT2, (int(sx), int(sy)), int(r), 2)
    pygame.draw.line(surf, C_ACCENT2, (sx - r - 5, sy), (sx - r + 3, sy), 2)
    pygame.draw.line(surf, C_ACCENT2, (sx + r - 3, sy), (sx + r + 5, sy), 2)
