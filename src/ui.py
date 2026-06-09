import pygame
import math
from .constants import *
from .particles import draw_glow


_font_cache = {}
def get_font(size, bold=True):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont('monospace', size, bold=bold)
    return _font_cache[key]


def draw_bar(surface, x, y, w, h, value, max_val, color, bg=(20,16,14)):
    # Background
    pygame.draw.rect(surface, bg, (x-1, y-1, w+2, h+2), border_radius=3)
    pygame.draw.rect(surface, tuple(max(0,c-6) for c in bg), (x, y, w, h), border_radius=2)
    if max_val > 0 and value > 0:
        fill = max(1, int(w * value / max_val))
        # Main fill
        pygame.draw.rect(surface, color, (x, y, fill, h), border_radius=2)
        # Shimmer highlight on top
        hl = tuple(min(255,c+50) for c in color)
        pygame.draw.rect(surface, hl, (x, y, fill, max(1,h//3)), border_radius=2)
    # Tick marks
    for pct in [0.25, 0.5, 0.75]:
        tx = x + int(w * pct)
        pygame.draw.line(surface, (0,0,0), (tx, y), (tx, y+h), 1)
    # Border
    pygame.draw.rect(surface, (60,55,50), (x-1, y-1, w+2, h+2), border_radius=3, width=1)


def draw_hud(surface, player):
    # Vignette
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for r in range(min(WIDTH,HEIGHT)//2, 0, -20):
        a = max(0, int(80 * (1 - r / (min(WIDTH,HEIGHT)//2))**2))
        pygame.draw.circle(vignette, (0,0,0,a), (WIDTH//2, HEIGHT//2), r+20)
    surface.blit(vignette, (0,0))

    # HUD panel background
    panel_w, panel_h = 300, 108
    px, py = 18, HEIGHT - panel_h - 14
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((0,0,0,0))
    pygame.draw.rect(panel, (0,0,0,160), (0,0,panel_w,panel_h), border_radius=6)
    # Gold border
    pygame.draw.rect(panel, (212,175,55,100), (0,0,panel_w,panel_h), border_radius=6, width=1)
    surface.blit(panel, (px-4, py-4))

    # HP bar
    font_sm = get_font(14)
    draw_bar(surface, px, py+2, 260, 18, player.hp, player.max_hp,
             (200,35,35), bg=(40,10,10))
    hp_txt = font_sm.render(f"HP  {player.hp}/{player.max_hp}", True, (240,220,210))
    surface.blit(hp_txt, (px+6, py+3))

    # Stamina bar
    draw_bar(surface, px, py+28, 260, 14, player.stamina, player.max_stamina,
             (45,185,80), bg=(10,30,15))
    st_txt = get_font(13).render(f"STA {int(player.stamina)}/{player.max_stamina}", True, (200,240,200))
    surface.blit(st_txt, (px+6, py+29))

    # Flask icons
    fy = py + 52
    fl_label = get_font(13).render("Flask", True, GOLD)
    surface.blit(fl_label, (px, fy))
    for i in range(player.max_flasks):
        fx2 = px + 56 + i*30
        if i < player.flasks:
            draw_glow(surface, fx2+10, fy+10, 14, (60,140,220), 50)
            pygame.draw.rect(surface, (20,50,90), (fx2, fy, 20, 20), border_radius=4)
            pygame.draw.rect(surface, (60,140,220), (fx2, fy, 20, 20), border_radius=4)
            # Flask shape
            pygame.draw.rect(surface, (40,110,180), (fx2+3, fy+3, 14, 14), border_radius=3)
            pygame.draw.circle(surface, (120,200,255), (fx2+10, fy+8), 4)
            pygame.draw.rect(surface, (80,160,220), (fx2+1, fy+1, 18, 18), border_radius=4, width=1)
        else:
            pygame.draw.rect(surface, (30,30,35), (fx2, fy, 20, 20), border_radius=4)
            pygame.draw.rect(surface, (50,50,60), (fx2, fy, 20, 20), border_radius=4, width=1)
            pygame.draw.line(surface, (60,60,70), (fx2+4,fy+10),(fx2+16,fy+10), 2)

    # Rune counter (top left, styled)
    rune_panel = pygame.Surface((180, 32), pygame.SRCALPHA)
    pygame.draw.rect(rune_panel, (0,0,0,150), (0,0,180,32), border_radius=4)
    pygame.draw.rect(rune_panel, (80,200,100,80), (0,0,180,32), border_radius=4, width=1)
    surface.blit(rune_panel, (px-4, py-42))
    draw_glow(surface, px+12, py-28, 10, (80,200,100), 60)
    pygame.draw.circle(surface, (50,180,80), (px+12, py-28), 8)
    pygame.draw.circle(surface, (120,240,150), (px+12, py-28), 4)
    rune_font = get_font(18)
    rune_txt = rune_font.render(f"{player.runes:,}", True, (120,240,150))
    surface.blit(rune_txt, (px+26, py-38))

    # Stagger/hurt indicator
    if player.stagger_timer > 0:
        stag = get_font(16).render("STAGGERED", True, (255,80,80))
        surface.blit(stag, (px, py-62))

    # Controls bar (bottom center)
    hints = [("Z","Light"),("X","Heavy"),("Space","Roll"),("Q","Parry"),("Shift","Block"),("F","Flask")]
    ctrl_panel_w = 620
    ctrl_panel = pygame.Surface((ctrl_panel_w, 26), pygame.SRCALPHA)
    pygame.draw.rect(ctrl_panel, (0,0,0,130), (0,0,ctrl_panel_w,26), border_radius=4)
    surface.blit(ctrl_panel, (WIDTH//2 - ctrl_panel_w//2, HEIGHT-28))
    cx = WIDTH//2 - ctrl_panel_w//2 + 8
    font_k = get_font(12)
    font_l = get_font(11, bold=False)
    for key, label in hints:
        k = font_k.render(f"[{key}]", True, GOLD)
        l = font_l.render(label, True, (160,155,145))
        surface.blit(k, (cx, HEIGHT-24))
        surface.blit(l, (cx + k.get_width()+2, HEIGHT-24))
        cx += k.get_width() + l.get_width() + 14


def draw_boss_bar(surface, boss):
    if not boss or boss.dead or not boss.aggro:
        return

    bar_w = 720
    bx = WIDTH//2 - bar_w//2
    by = 18

    # Panel
    panel = pygame.Surface((bar_w+28, 58), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0,0,0,180), (0,0,bar_w+28,58), border_radius=5)
    pygame.draw.rect(panel, (180,20,20,80), (0,0,bar_w+28,58), border_radius=5, width=1)
    surface.blit(panel, (bx-14,by-8))

    # Boss name
    font = get_font(18)
    name_txt = font.render(boss.name, True, GOLD)
    surface.blit(name_txt, (WIDTH//2 - name_txt.get_width()//2, by-4))

    # HP bar
    draw_bar(surface, bx, by+22, bar_w, 14, boss.hp, boss.max_hp,
             (200,45,20), bg=(50,10,10))
    # Segment lines (10% increments)
    for pct in [i*0.1 for i in range(1,10)]:
        tx = bx + int(bar_w * pct)
        pygame.draw.line(surface, (0,0,0), (tx,by+22),(tx,by+36), 2)

    # HP text
    hp_pct = int(boss.hp / boss.max_hp * 100)
    hp_f = get_font(12).render(f"{boss.hp}/{boss.max_hp}", True, (200,180,160))
    surface.blit(hp_f, (WIDTH//2 - hp_f.get_width()//2, by+24))

    if boss.enraged:
        txt = get_font(13).render("☩ ENRAGED ☩", True, (255,70,30))
        surface.blit(txt, (WIDTH//2 - txt.get_width()//2, by+40))
        draw_glow(surface, WIDTH//2, by+46, 60, (255,60,20), 40)

    if boss.phase_transition:
        prog = 1 - boss.phase_transition_timer/120
        flash_a = int(math.sin(prog*math.pi*3)*80+80)
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((200,80,20,flash_a))
        surface.blit(flash, (0,0))
        txt = get_font(28).render("PHASE TRANSITION", True, GOLD)
        s2 = pygame.Surface((txt.get_width()+20,txt.get_height()+10), pygame.SRCALPHA)
        s2.fill((0,0,0,160))
        s2.blit(txt,(10,5))
        s2.set_alpha(flash_a*2)
        surface.blit(s2, (WIDTH//2-s2.get_width()//2, HEIGHT//2-s2.get_height()//2))


def draw_status_text(surface, text, alpha, y_offset=0):
    font = get_font(60)
    txt = font.render(text, True, (220,60,60))
    shadow = font.render(text, True, (60,10,10))
    x = WIDTH//2 - txt.get_width()//2
    y = HEIGHT//2 - txt.get_height()//2 + y_offset
    s = pygame.Surface((txt.get_width()+40,txt.get_height()+20), pygame.SRCALPHA)
    s.fill((0,0,0,0))
    # Drop shadow
    s.blit(shadow, (22,12))
    s.blit(txt, (20,10))
    s.set_alpha(int(alpha))
    surface.blit(s, (x-20, y-10))


def draw_area_name(surface, name, alpha):
    font = get_font(30)
    txt = font.render(name, True, GOLD)
    shadow = font.render(name, True, (80,60,20))
    panel = pygame.Surface((txt.get_width()+40, txt.get_height()+14), pygame.SRCALPHA)
    panel.fill((0,0,0,140))
    panel.blit(shadow, (22,8))
    panel.blit(txt, (20,6))
    pygame.draw.rect(panel, (212,175,55,80), (0,0,panel.get_width(),panel.get_height()), width=1, border_radius=4)
    panel.set_alpha(int(alpha))
    surface.blit(panel, (WIDTH//2 - panel.get_width()//2, HEIGHT - 90))


def draw_text_screen(surface, lines, font_size=22, title_size=32, alpha=255):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,210))
    overlay.set_alpha(alpha)
    surface.blit(overlay, (0,0))

    # Decorative top/bottom borders
    border_s = pygame.Surface((WIDTH, 4), pygame.SRCALPHA)
    border_s.fill((212,175,55,int(alpha*0.6)))
    surface.blit(border_s, (0, 60))
    surface.blit(border_s, (0, HEIGHT-64))

    total_h = 0
    for i, line in enumerate(lines):
        sz = title_size if i==0 and line else font_size
        total_h += sz + 8
    start_y = max(80, HEIGHT//2 - total_h//2)
    cy = start_y

    for i, line in enumerate(lines):
        if not line:
            cy += font_size//2
            continue
        if i == 0:
            font = get_font(title_size)
            col = GOLD
        elif line.startswith('—') or line.startswith('['):
            font = get_font(font_size)
            col = (180,170,130)
        elif line.startswith('RESTORE') or line.startswith('BURN'):
            font = get_font(font_size)
            col = (200,220,255) if line.startswith('RESTORE') else (255,140,60)
        else:
            font = get_font(font_size, bold=False)
            col = (180,175,165)
        txt = font.render(line, True, col)
        x = WIDTH//2 - txt.get_width()//2
        # Shadow
        shadow_s = font.render(line, True, (0,0,0))
        surface.blit(shadow_s, (x+2, cy+2))
        surface.blit(txt, (x, cy))
        cy += font.get_height() + 6


def draw_parry_success(surface, x, y, cam_ox, cam_oy):
    sx = int(x - cam_ox)
    sy = int(y - cam_oy)
    font = get_font(22)
    txt = font.render("PARRY!", True, (255,240,60))
    draw_glow(surface, sx, sy-40, 30, (255,230,50), 100)
    shadow = font.render("PARRY!", True, (100,80,0))
    surface.blit(shadow, (sx - txt.get_width()//2+2, sy-44))
    surface.blit(txt, (sx - txt.get_width()//2, sy-46))


def draw_pickup_text(surface, text, timer, max_timer=180):
    fade = min(1.0, timer/30) * min(1.0, (timer)/max_timer*6)
    alpha = int(255 * fade)
    font = get_font(18)
    txt = font.render(text, True, GOLD)
    panel = pygame.Surface((txt.get_width()+24, txt.get_height()+12), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0,0,0,160), (0,0,panel.get_width(),panel.get_height()), border_radius=4)
    pygame.draw.rect(panel, (212,175,55,100), (0,0,panel.get_width(),panel.get_height()), border_radius=4, width=1)
    panel.blit(txt, (12,6))
    panel.set_alpha(alpha)
    surface.blit(panel, (WIDTH//2 - panel.get_width()//2, HEIGHT//2 + 65))
