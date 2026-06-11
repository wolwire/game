"""Weapon definitions and rendering.

Each weapon has a light-attack combo (list of steps) and a heavy attack.
Step format: (kind, windup, active, recover) — kind drives the animation
(swing / thrust / smash), the timings drive both gameplay and the puppet.
`wlen` is the blade length in world units used by the puppet renderer.
"""
import math
import pygame
from src.assets import sh

WEAPONS = {
    'wrench': dict(
        name="Pipe Wrench", desc="You installed half this city with it.",
        dmg=21, reach=2.3, arc=2.1, stamina=15, stagger=1.0,
        combo=[('swing', 0.16, 0.14, 0.30), ('swing', 0.12, 0.14, 0.34)],
        heavy=('smash', 0.46, 0.16, 0.52, 2.2),
        wlen=0.62, color=(186, 190, 200), grip=(110, 80, 50), shape='blunt',
        trail=(255, 214, 150)),
    'machete': dict(
        name="Machete", desc="From the night market's kitchen row.",
        dmg=15, reach=2.4, arc=2.2, stamina=11, stagger=0.7,
        combo=[('swing', 0.11, 0.12, 0.22), ('swing', 0.09, 0.12, 0.22),
               ('swing', 0.10, 0.12, 0.30)],
        heavy=('swing', 0.34, 0.16, 0.44, 1.9),
        wlen=0.72, color=(200, 206, 214), grip=(40, 40, 44), shape='blade',
        trail=(190, 230, 255)),
    'spear': dict(
        name="Rebar Spear", desc="The Unfinished Mile, sharpened.",
        dmg=24, reach=3.6, arc=0.9, stamina=17, stagger=1.0,
        combo=[('thrust', 0.18, 0.12, 0.34), ('thrust', 0.14, 0.12, 0.38)],
        heavy=('swing', 0.42, 0.18, 0.50, 1.8),
        wlen=1.25, color=(150, 144, 138), grip=(96, 86, 70), shape='spear',
        trail=(255, 180, 130)),
    'sledge': dict(
        name="Demolition Sledge", desc="Asks one question, loudly.",
        dmg=42, reach=2.6, arc=2.4, stamina=30, stagger=2.4,
        combo=[('smash', 0.34, 0.16, 0.50)],
        heavy=('smash', 0.62, 0.18, 0.66, 1.9),
        wlen=0.85, color=(120, 116, 112), grip=(120, 92, 56), shape='hammer',
        trail=(255, 160, 90)),
    'baton': dict(
        name="Warden's Baton", desc="Still humming with crowd-control current.",
        dmg=20, reach=2.4, arc=2.0, stamina=12, stagger=1.7, shock=True,
        combo=[('swing', 0.12, 0.12, 0.24), ('swing', 0.10, 0.12, 0.24),
               ('thrust', 0.12, 0.12, 0.30)],
        heavy=('thrust', 0.36, 0.14, 0.46, 2.0),
        wlen=0.66, color=(70, 76, 90), grip=(36, 38, 44), shape='baton',
        trail=(150, 220, 255)),
    'choirblade': dict(
        name="Choir Blade", desc="It rings one pure note when it cuts.",
        dmg=26, reach=2.9, arc=2.2, stamina=14, stagger=1.0,
        combo=[('swing', 0.10, 0.12, 0.20), ('swing', 0.08, 0.12, 0.20),
               ('thrust', 0.10, 0.12, 0.20), ('swing', 0.10, 0.14, 0.34)],
        heavy=('swing', 0.38, 0.18, 0.42, 2.1),
        wlen=0.95, color=(220, 210, 240), grip=(90, 70, 110), shape='blade',
        trail=(216, 160, 255)),
}


def step_time(step):
    return step[1] + step[2] + step[3]


def draw_weapon(surf, hand, tip, w, flash=0.0):
    """Draw a weapon from hand (screen pt) to tip (screen pt)."""
    dx, dy = tip[0] - hand[0], tip[1] - hand[1]
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    col = sh(w['color'], 1 + flash)
    dark = sh(w['color'], 0.55)
    shape = w['shape']
    out = (14, 14, 18)
    if shape == 'blade':
        # grip
        g = (hand[0] - ux * 4, hand[1] - uy * 4)
        pygame.draw.line(surf, out, g, hand, 5)
        pygame.draw.line(surf, w['grip'], g, hand, 3)
        # blade: tapering polygon with edge highlight
        b0 = (hand[0] + px * 1.6, hand[1] + py * 1.6)
        b1 = (hand[0] - px * 1.6, hand[1] - py * 1.6)
        pygame.draw.polygon(surf, out, [b0, b1, tip])
        pygame.draw.polygon(surf, col, [(b0[0], b0[1]), (b1[0], b1[1]),
                                        (tip[0] - ux, tip[1] - uy)])
        pygame.draw.line(surf, sh(col, 1.35), b0, tip, 1)
        # guard
        pygame.draw.line(surf, dark, (hand[0] + px * 3, hand[1] + py * 3),
                         (hand[0] - px * 3, hand[1] - py * 3), 2)
    elif shape == 'spear':
        pygame.draw.line(surf, out, hand, tip, 4)
        pygame.draw.line(surf, w['grip'], hand, (hand[0] + dx * 0.8, hand[1] + dy * 0.8), 2)
        pygame.draw.line(surf, col, (hand[0] + dx * 0.8, hand[1] + dy * 0.8), tip, 2)
        # head
        h0 = (tip[0] - ux * 6 + px * 2.5, tip[1] - uy * 6 + py * 2.5)
        h1 = (tip[0] - ux * 6 - px * 2.5, tip[1] - uy * 6 - py * 2.5)
        pygame.draw.polygon(surf, out, [h0, h1, tip])
        pygame.draw.polygon(surf, col, [h0, h1, tip])
        # rebar ridges
        for i in range(3):
            t = 0.2 + i * 0.22
            rx_, ry_ = hand[0] + dx * t, hand[1] + dy * t
            pygame.draw.line(surf, sh(w['grip'], 0.7), (rx_ + px * 2, ry_ + py * 2),
                             (rx_ - px * 2, ry_ - py * 2), 1)
    elif shape == 'hammer':
        pygame.draw.line(surf, out, hand, tip, 5)
        pygame.draw.line(surf, w['grip'], hand, (tip[0] - ux * 8, tip[1] - uy * 8), 3)
        head0 = (tip[0] - ux * 6 + px * 6, tip[1] - uy * 6 + py * 6)
        head1 = (tip[0] - ux * 6 - px * 6, tip[1] - uy * 6 - py * 6)
        pygame.draw.line(surf, out, head0, head1, 11)
        pygame.draw.line(surf, col, head0, head1, 8)
        pygame.draw.line(surf, sh(col, 1.3), (head0[0], head0[1] - 2), (head1[0], head1[1] - 2), 2)
    elif shape == 'baton':
        pygame.draw.line(surf, out, hand, tip, 5)
        pygame.draw.line(surf, w['grip'], hand, (hand[0] + dx * 0.3, hand[1] + dy * 0.3), 4)
        pygame.draw.line(surf, col, (hand[0] + dx * 0.3, hand[1] + dy * 0.3), tip, 3)
        if w.get('shock'):
            # crackle at the tip
            pygame.draw.line(surf, (170, 225, 255), (tip[0] - 2, tip[1] - 2), (tip[0] + 2, tip[1] + 1), 1)
            pygame.draw.circle(surf, (200, 240, 255), (int(tip[0]), int(tip[1])), 1)
    else:  # blunt: pipe wrench
        pygame.draw.line(surf, out, hand, tip, 5)
        pygame.draw.line(surf, col, hand, tip, 3)
        # wrench jaw
        jx, jy = tip[0] - ux * 2, tip[1] - uy * 2
        pygame.draw.line(surf, out, (jx + px * 4, jy + py * 4), (jx - px * 2, jy - py * 2), 6)
        pygame.draw.line(surf, sh(col, 1.15), (jx + px * 4, jy + py * 4), (jx - px * 2, jy - py * 2), 4)
        pygame.draw.line(surf, dark, (tip[0] + px * 3, tip[1] + py * 3), tip, 2)
        pygame.draw.line(surf, w['grip'], hand, (hand[0] + dx * 0.25, hand[1] + dy * 0.25), 3)


def draw_trail(surf, trail, color):
    """trail: list of [x, y, ttl] tip samples; draws a fading ribbon."""
    if len(trail) < 2:
        return
    pts = [(t[0], t[1]) for t in trail]
    n = len(pts)
    for i in range(n - 1):
        a = int(160 * (i + 1) / n)
        w = 1 + int(3 * (i + 1) / n)
        seg = pygame.Surface((1, 1))  # avoid per-pixel alpha cost; use draw with alpha via aaline fallback
        pygame.draw.line(surf, (min(255, color[0] + (255 - color[0]) * (i + 1) // n),
                                min(255, color[1] + (255 - color[1]) * (i + 1) // n),
                                min(255, color[2])), pts[i], pts[i + 1], w)
