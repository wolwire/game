import pygame
import math
from .constants import *


def get_font(size):
    return pygame.font.SysFont('monospace', size, bold=True)


def draw_bar(surface, x, y, w, h, value, max_val, color, bg_color=DARK_GREY):
    pygame.draw.rect(surface, bg_color, (x, y, w, h))
    if max_val > 0:
        fill = max(0, int(w * value / max_val))
        pygame.draw.rect(surface, color, (x, y, fill, h))
    pygame.draw.rect(surface, (10,10,10), (x, y, w, h), 1)


def draw_hud(surface, player):
    font_sm = get_font(14)
    font_md = get_font(17)

    px, py = 20, HEIGHT - 110

    # Backgrounds
    panel = pygame.Surface((280, 100), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 120))
    surface.blit(panel, (px-8, py-8))

    # HP bar
    draw_bar(surface, px, py, 240, BAR_HEIGHT, player.hp, player.max_hp, PLAYER_HP_COLOR)
    hp_txt = font_sm.render(f"HP  {player.hp}/{player.max_hp}", True, WHITE)
    surface.blit(hp_txt, (px+4, py+1))

    # Stamina bar
    sy2 = py + 26
    draw_bar(surface, px, sy2, 240, BAR_HEIGHT, player.stamina, player.max_stamina, PLAYER_STAMINA_COLOR)
    st_txt = font_sm.render(f"STA {int(player.stamina)}/{player.max_stamina}", True, WHITE)
    surface.blit(st_txt, (px+4, sy2+1))

    # Flasks
    fy = sy2 + 30
    flask_txt = font_sm.render("Flask:", True, GOLD)
    surface.blit(flask_txt, (px, fy))
    for i in range(player.max_flasks):
        fx2 = px + 60 + i * 26
        color = (60, 120, 200) if i < player.flasks else (50, 50, 50)
        pygame.draw.rect(surface, color, (fx2, fy, 18, 18), border_radius=3)
        pygame.draw.rect(surface, (100, 100, 100), (fx2, fy, 18, 18), border_radius=3, width=1)

    # Runes counter
    rune_txt = font_md.render(f"Runes: {player.runes}", True, (80, 220, 120))
    surface.blit(rune_txt, (px, py - 28))

    # Controls reminder (small)
    ctrl_y = HEIGHT - 28
    hints = [
        ("Z", "Light"), ("X", "Heavy"), ("Space", "Roll"),
        ("Q", "Parry"), ("Shift", "Block"), ("F", "Flask"),
    ]
    cx = 20
    font_tiny = get_font(11)
    for key, label in hints:
        k = font_tiny.render(f"[{key}]", True, GOLD)
        l = font_tiny.render(label, True, LIGHT_GREY)
        surface.blit(k, (cx, ctrl_y))
        surface.blit(l, (cx + k.get_width() + 2, ctrl_y))
        cx += k.get_width() + l.get_width() + 16


def draw_boss_bar(surface, boss):
    if not boss or boss.dead or not boss.aggro:
        return
    font = get_font(16)
    bar_w = 700
    bx = WIDTH // 2 - bar_w // 2
    by = 20

    # Background panel
    panel = pygame.Surface((bar_w + 20, 50), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 160))
    surface.blit(panel, (bx - 10, by - 8))

    # Name
    name_txt = font.render(boss.name, True, GOLD)
    surface.blit(name_txt, (WIDTH // 2 - name_txt.get_width() // 2, by - 6))

    # HP bar
    draw_bar(surface, bx, by + 20, bar_w, 16, boss.hp, boss.max_hp, BOSS_HP_COLOR)

    # Phase indicator
    if boss.enraged:
        enrage_txt = get_font(13).render("☩ PHASE 2 ☩", True, (255, 80, 40))
        surface.blit(enrage_txt, (WIDTH // 2 - enrage_txt.get_width() // 2, by + 38))


def draw_status_text(surface, text, alpha, y_offset=0):
    font = get_font(52)
    txt = font.render(text, True, WHITE)
    s = pygame.Surface((txt.get_width() + 20, txt.get_height() + 10), pygame.SRCALPHA)
    s.fill((0, 0, 0, int(alpha * 0.6)))
    s.blit(txt, (10, 5))
    x = WIDTH // 2 - s.get_width() // 2
    y = HEIGHT // 2 - s.get_height() // 2 + y_offset
    s.set_alpha(int(alpha))
    surface.blit(s, (x, y))


def draw_area_name(surface, name, alpha):
    font = get_font(28)
    txt = font.render(name, True, GOLD)
    s = pygame.Surface((txt.get_width() + 20, txt.get_height() + 8), pygame.SRCALPHA)
    s.blit(txt, (10, 4))
    s.set_alpha(int(alpha))
    surface.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT - 80))


def draw_text_screen(surface, lines, font_size=22, title_size=32, alpha=255):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    overlay.set_alpha(alpha)
    surface.blit(overlay, (0, 0))

    font_title = get_font(title_size)
    font_body = get_font(font_size)
    total_h = len(lines) * (font_size + 6)
    start_y = HEIGHT // 2 - total_h // 2

    for i, line in enumerate(lines):
        y = start_y + i * (font_size + 6)
        if i == 0 and line:
            txt = font_title.render(line, True, GOLD)
        elif not line:
            continue
        else:
            color = LIGHT_GREY if not line.startswith("—") else (120, 120, 100)
            txt = font_body.render(line, True, color)
        surface.blit(txt, (WIDTH // 2 - txt.get_width() // 2, y))


def draw_parry_success(surface, x, y, cam_ox, cam_oy):
    sx = x - cam_ox
    sy = y - cam_oy
    font = get_font(20)
    txt = font.render("PARRY!", True, (255, 240, 80))
    surface.blit(txt, (sx - txt.get_width() // 2, sy - 40))


def draw_pickup_text(surface, text, timer, max_timer=180):
    alpha = min(255, timer * 3) if timer > max_timer - 60 else 255
    alpha = min(alpha, max(0, int(255 * timer / 30))) if timer < 30 else alpha
    font = get_font(18)
    txt = font.render(text, True, GOLD)
    s = pygame.Surface((txt.get_width() + 16, txt.get_height() + 8), pygame.SRCALPHA)
    s.fill((0, 0, 0, 140))
    s.blit(txt, (8, 4))
    s.set_alpha(int(alpha))
    surface.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 60))
