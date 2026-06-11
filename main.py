"""STILLWAKE — a 2.5D isometric open-world souls-like.

Meridian under the Stillness, drawn with flare-game's pre-rendered art.
Run:  python3 main.py
"""
import math
import random
import sys

import pygame

pygame.init()

from src.constants import *
from src.iso import world_to_screen, screen_to_world
from src import flare, sprites
from src.worldgen import World, district_at, CRYSTAL, ALTARS, CRATES, FURNITURE, IRONFENCE
from src.player import Player
from src.enemy import Enemy
from src.boss import Boss
from src.camera import Camera
from src.particles import Particles
from src import ui
from src.weapons import WEAPONS
from src.entity import dist
from data import story


def glow_surf(radius, color):
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r, a in ((radius, 26), (int(radius * 0.62), 48), (int(radius * 0.3), 80)):
        pygame.draw.circle(s, (*color, a), (radius, radius), r)
    return s


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("STILLWAKE — a tale of the Stillness")
        self.clock = pygame.time.Clock()
        self.state = 'title'
        self.t = 0.0
        self.state_t = 0.0
        self.freeze_t = 0.0

        self.world = World()
        self.player = Player(*self.world.spawn)
        self.camera = Camera(self.player.x, self.player.y)
        self.particles = Particles()
        self.chunks = {}
        sprites.warm_up()
        ui.build_minimap(self.world)
        self.glow_beacon = glow_surf(90, (150, 110, 255))
        self.glow_amber = glow_surf(46, (255, 190, 90))
        self.glow_blue = glow_surf(46, (110, 200, 255))

        self.enemies = []
        self.spawn_enemies()
        self.projectiles = []

        self.bosses = {}
        for key, b in self.world.bosses.items():
            self.bosses[key] = Boss(b['kind'], b['center'][0], b['center'][1],
                                    b['center'], b['radius'])
        self.bosses_defeated = set()
        self.active_boss = None

        self.last_beacon = self.world.beacons[0][:2]
        self.gate_open = False
        self.set_gate(False)

        self.echo = None
        self.area = district_at(int(self.player.x), int(self.player.y))
        self.banner = (story.AREA_NAMES.get(self.area, ''), story.AREA_DESC.get(self.area, ''))
        self.banner_t = 0.0
        self.flash_msg = None
        self.flash_t = 0.0

        self.text_lines = []
        self.text_title = None
        self.text_next = 'playing'
        self.dialogue = None
        self.npc_progress = {}
        self.beacon_sel = 0
        self.beacon_msg = ''
        self.death_msg = ''
        self.ending_sel = 0
        self.lore_found = set()
        self.pending_boss = None

    # ------------------------------------------------------------ setup ---
    def spawn_enemies(self):
        self.enemies = [Enemy(kind, x, y, r) for kind, x, y, r in self.world.enemy_spawns]

    def set_gate(self, opened):
        self.gate_open = opened
        for (x, y) in self.world.gate_tiles:
            self.world.solid[y][x] = not opened

    def flash(self, msg, t=2.5):
        self.flash_msg = msg
        self.flash_t = t

    def set_state(self, s):
        self.state = s
        self.state_t = 0.0

    def hitstop(self, t=0.05):
        self.freeze_t = max(self.freeze_t, t)

    # ------------------------------------------------------------ events ---
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type != pygame.KEYDOWN:
                continue
            k = ev.key
            confirm = k in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE)
            if self.state == 'title':
                if k == pygame.K_RETURN:
                    self.text_lines, self.text_title = story.INTRO, story.INTRO_TITLE
                    self.text_next = 'controls_screen'
                    self.set_state('text')
            elif self.state == 'text':
                if confirm and self.state_t > 0.6:
                    if self.text_next == 'controls_screen':
                        self.text_lines, self.text_title = story.CONTROLS, "SURVIVING THE STILLNESS"
                        self.text_next = 'playing'
                        self.set_state('text')
                        self.banner_t = 0.0
                    elif self.text_next == 'ending_choice':
                        self.set_state('ending_choice')
                    elif self.text_next == 'quit':
                        pygame.quit()
                        sys.exit()
                    else:
                        self.set_state('playing')
            elif self.state == 'playing':
                if k == pygame.K_SPACE:
                    self.player.try_roll()
                elif k == pygame.K_j:
                    self.player.try_attack(False)
                elif k == pygame.K_k:
                    self.player.try_attack(True)
                elif k == pygame.K_l:
                    self.player.try_parry()
                elif k == pygame.K_q:
                    self.player.try_stim()
                elif k == pygame.K_r:
                    self.player.cycle_weapon()
                elif k == pygame.K_TAB:
                    self.cycle_lock()
                elif k == pygame.K_m:
                    self.set_state('map')
                elif k == pygame.K_ESCAPE:
                    self.set_state('pause')
                elif k == pygame.K_e:
                    self.interact()
            elif self.state == 'map':
                if k in (pygame.K_m, pygame.K_ESCAPE):
                    self.set_state('playing')
            elif self.state == 'pause':
                if k in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.set_state('playing')
                elif k == pygame.K_q:
                    pygame.quit()
                    sys.exit()
            elif self.state == 'dialogue':
                if confirm:
                    name, pages, idx = self.dialogue
                    if idx + 1 < len(pages):
                        self.dialogue = (name, pages, idx + 1)
                    else:
                        self.set_state('playing')
            elif self.state == 'beacon':
                if k in (pygame.K_w, pygame.K_UP):
                    self.beacon_sel = (self.beacon_sel - 1) % 4
                elif k in (pygame.K_s, pygame.K_DOWN):
                    self.beacon_sel = (self.beacon_sel + 1) % 4
                elif confirm:
                    self.beacon_choose()
                elif k == pygame.K_ESCAPE:
                    self.set_state('playing')
            elif self.state == 'boss_intro':
                if confirm and self.state_t > 0.8 and self.player.alive:
                    self.start_boss_fight()
            elif self.state == 'dead':
                if confirm and self.state_t > 1.2:
                    self.respawn()
            elif self.state == 'ending_choice':
                if k in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN):
                    self.ending_sel = 1 - self.ending_sel
                elif confirm:
                    self.text_lines = (story.ENDING_SEVER if self.ending_sel == 0
                                       else story.ENDING_INHERIT)
                    self.text_title = "THE LONGEST SECOND ENDS" if self.ending_sel == 0 \
                        else "THE DREAM CONTINUES"
                    self.text_next = 'quit'
                    self.set_state('text')

    # ------------------------------------------------------- interactions ---
    def nearest_interactable(self):
        px, py = self.player.x, self.player.y
        best, best_d = None, 1.6
        for bx, by, name in self.world.beacons:
            d = dist(px, py, bx, by)
            if d < best_d + 0.4:
                best, best_d = ('beacon', (bx, by, name)), d
        for (x, y, key, style) in self.world.npcs:
            d = dist(px, py, x, y)
            if d < best_d:
                best, best_d = ('npc', (x, y, key, style)), d
        for item in self.world.lore:
            x, y, idx = item
            if idx in self.lore_found:
                continue
            d = dist(px, py, x, y)
            if d < best_d:
                best, best_d = ('lore', item), d
        for item in self.world.weapons:
            d = dist(px, py, item[0], item[1])
            if d < best_d:
                best, best_d = ('weapon', item), d
        for item in self.world.caches:
            d = dist(px, py, item[0], item[1])
            if d < best_d:
                best, best_d = ('cache', item), d
        if self.echo:
            d = dist(px, py, self.echo[0], self.echo[1])
            if d < best_d:
                best, best_d = ('echo', self.echo), d
        return best

    def interact(self):
        it = self.nearest_interactable()
        if not it:
            return
        kind, data = it
        if kind == 'beacon':
            bx, by, name = data
            self.last_beacon = (bx, by)
            self.player.rest()
            self.spawn_enemies()
            self.projectiles.clear()
            self.reset_bosses()
            self.beacon_sel = 0
            self.beacon_msg = random.choice(story.GRACE_MESSAGES)
            self.set_state('beacon')
        elif kind == 'npc':
            x, y, key, style = data
            d = story.NPC_DIALOGUE[key]
            prog = self.npc_progress.get(key, 0)
            lines = d['lines'][min(prog, len(d['lines']) - 1)]
            self.npc_progress[key] = prog + 1
            pages = [lines[i:i + 3] for i in range(0, len(lines), 3)]
            self.dialogue = (d['name'], pages, 0)
            self.set_state('dialogue')
        elif kind == 'lore':
            x, y, idx = data
            self.lore_found.add(idx)
            title, lines = story.LORE_FRAGMENTS[idx]
            self.text_lines, self.text_title = lines, title
            self.text_next = 'playing'
            self.set_state('text')
            self.player.shards += 25
        elif kind == 'weapon':
            x, y, wkey = data
            self.world.weapons.remove(data)
            self.player.give_weapon(wkey)
            w = WEAPONS[wkey]
            self.flash(f"{w['name']} acquired — {w['desc']}", 4.0)
            self.particles.parry_spark(x, y)
        elif kind == 'cache':
            x, y, ckind, amount = data
            self.world.caches.remove(data)
            if ckind == 'shards':
                self.player.shards += amount
                self.flash(f"Supply cache: +{amount} shards")
            elif ckind == 'stim':
                self.player.stim_max += 1
                self.player.stims = self.player.stim_max
                self.flash("Healer's satchel: +1 stim capacity, refilled")
            else:
                self.player.bonus_hp += amount
                self.player.hp += amount
                self.flash(f"Memory anchor: +{amount} max HP")
            self.particles.death_burst(x, y)
        elif kind == 'echo':
            self.player.shards += self.echo[2]
            self.particles.death_burst(self.echo[0], self.echo[1])
            self.flash(f"{self.echo[2]} shards reclaimed")
            self.echo = None

    def beacon_choose(self):
        cost = level_cost(self.player.level)
        p = self.player
        if self.beacon_sel == 3:
            self.set_state('playing')
            return
        if p.shards < cost:
            return
        p.shards -= cost
        p.level += 1
        if self.beacon_sel == 0:
            p.vigor += 1
        elif self.beacon_sel == 1:
            p.endurance += 1
        else:
            p.strength += 1
        p.rest()

    def cycle_lock(self):
        p = self.player
        targets = [e for e in self.enemies if e.alive and dist(p.x, p.y, e.x, e.y) < 11]
        if self.active_boss and self.active_boss.alive:
            targets.append(self.active_boss)
        targets.sort(key=lambda e: dist(p.x, p.y, e.x, e.y))
        if not targets:
            p.lock_target = None
            return
        if p.lock_target in targets:
            i = targets.index(p.lock_target)
            p.lock_target = targets[(i + 1) % len(targets)]
        else:
            p.lock_target = targets[0]

    # ------------------------------------------------------------ bosses ---
    def reset_bosses(self):
        for key, boss in self.bosses.items():
            if key not in self.bosses_defeated:
                c = self.world.bosses[key]['center']
                boss.hp = boss.max_hp
                boss.x, boss.y = c
                boss.active = False
                boss.alive = True
                boss.phase2 = False
                boss.state = 'idle'
                boss.telegraphs.clear()
        self.active_boss = None
        self.enemies = [e for e in self.enemies if not getattr(e, 'summoned', False)]

    def check_boss_triggers(self):
        if self.active_boss is not None or not self.player.alive:
            return
        p = self.player
        for key, boss in self.bosses.items():
            if key in self.bosses_defeated or not boss.alive:
                continue
            bd = self.world.bosses[key]
            if dist(p.x, p.y, *bd['center']) < bd['radius'] - 1.0:
                self.pending_boss = key
                self.set_state('boss_intro')
                return

    def start_boss_fight(self):
        key = self.pending_boss
        self.bosses[key].active = True
        self.active_boss = self.bosses[key]
        self.set_state('playing')

    def on_boss_death(self, key):
        boss = self.bosses[key]
        boss.active = False
        self.bosses_defeated.add(key)
        self.player.shards += boss.shards
        self.player.kills += 1
        data = story.BOSS_DATA[key]
        self.flash(data['defeat'], 5.0)
        self.camera.shake(10, 0.5)
        self.active_boss = None
        if key == 'warden' and self.player.give_weapon('baton'):
            self.flash(data['defeat'] + "  [Warden's Cudgel acquired]", 6.0)
        if key == 'chorister' and self.player.give_weapon('choirblade'):
            self.flash(data['defeat'] + "  [Choir Blade acquired]", 6.0)
        if key == 'archivist':
            self.text_lines = story.VICTORY_ARCHIVIST + [""] + story.ENDING_CHOICE
            self.text_title = "THE HIGH CHAMBER"
            self.text_next = 'ending_choice'
            self.set_state('text')
        elif not self.gate_open and {'warden', 'chorister'} <= self.bosses_defeated:
            self.set_gate(True)
            self.flash("Far north, the Carillon gate grinds open.", 5.0)

    # ------------------------------------------------------------ update ---
    def update(self, dt):
        self.t += dt
        self.state_t += dt
        self.flash_t = max(0, self.flash_t - dt)
        if self.freeze_t > 0:
            self.freeze_t -= dt
            return
        self.particles.update(dt)
        if self.state != 'playing':
            return
        p = self.player

        keys = pygame.key.get_pressed()
        mx = (keys[pygame.K_d] - keys[pygame.K_a])
        my = (keys[pygame.K_s] - keys[pygame.K_w])
        p.update(dt, self.world, (mx, my), keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        area = district_at(int(p.x), int(p.y))
        if area != self.area:
            self.area = area
            self.banner = (story.AREA_NAMES.get(area, ''), story.AREA_DESC.get(area, ''))
            self.banner_t = 0.0
        self.banner_t = min(1.0, self.banner_t + dt / 4.5)

        if not self.gate_open:
            for (gx, gy) in self.world.gate_tiles[::4]:
                if dist(p.x, p.y, gx + 0.5, gy + 0.5) < 2.2 and self.flash_t <= 0:
                    need = [k for k in ('warden', 'chorister') if k not in self.bosses_defeated]
                    names = ' and '.join(story.BOSS_DATA[k]['name'] for k in need)
                    self.flash(f"The Carillon denies you. It still grieves: {names}.", 3.5)

        for e in self.enemies:
            if e.alive and dist(p.x, p.y, e.x, e.y) < 28:
                e.update(dt, self.world, p, self.projectiles, self.particles)
            elif not e.alive and e.death_clock is not None and e.death_clock < 10:
                e.death_clock += dt

        self.check_boss_triggers()
        if self.active_boss:
            boss = self.active_boss
            boss.update(dt, self.world, p, self.projectiles, self.particles, self.enemies)
            key = self.pending_boss
            bd = self.world.bosses[key]
            d = dist(p.x, p.y, *bd['center'])
            if d > bd['radius']:
                nx = (bd['center'][0] - p.x) / d
                ny = (bd['center'][1] - p.y) / d
                p.x += nx * (d - bd['radius'])
                p.y += ny * (d - bd['radius'])
            if not boss.alive:
                self.on_boss_death(key)
        for key, boss in self.bosses.items():
            if not boss.alive and boss.death_clock is not None and boss.death_clock < 10:
                boss.death_clock += dt

        if p.attack_active():
            w = p.weapon
            hit_any = False
            for e in self.enemies:
                if e.alive and p.in_arc(e.x, e.y, e.radius):
                    gained = e.take_damage(p.attack_damage(), p.x, p.y,
                                           self.particles, w['stagger'])
                    hit_any = True
                    if gained:
                        p.shards += gained
                        p.kills += 1
                        self.flash(f"+{gained} shards", 1.2)
            b = self.active_boss
            if b and b.alive and p.in_arc(b.x, b.y, b.radius):
                b.take_damage(p.attack_damage(), p.x, p.y, self.particles, w['stagger'])
                hit_any = True
            if hit_any:
                p.atk_hit_done = True
                self.camera.shake(3 if not p.atk_heavy else 6, 0.12)
                self.hitstop(0.045 if not p.atk_heavy else 0.075)

        for pr in self.projectiles[:]:
            if not pr.update(dt, self.world):
                self.projectiles.remove(pr)
                continue
            if pr.hostile and dist(pr.x, pr.y, p.x, p.y) < pr.r + p.radius:
                res = p.take_damage(pr.dmg)
                if res in ('hit', 'dead', 'parried'):
                    self.projectiles.remove(pr)
                    if res == 'hit':
                        self.particles.blood(p.x, p.y)

        if self.echo:
            self.particles.shard_sparkle(self.echo[0], self.echo[1])
        for bx, by, _ in self.world.beacons:
            if dist(p.x, p.y, bx, by) < 14:
                self.particles.beacon_idle(bx, by)

        self.camera.follow(p.x, p.y, dt)

        if not p.alive and self.state == 'playing':
            self.echo = (p.x, p.y, p.shards) if p.shards > 0 else self.echo
            p.shards = 0
            self.death_msg = random.choice(story.DEATH_MESSAGES)
            self.set_state('dead')

    def respawn(self):
        self.player.respawn(*self.last_beacon)
        self.spawn_enemies()
        self.projectiles.clear()
        self.reset_bosses()
        self.camera = Camera(self.player.x, self.player.y)
        self.set_state('playing')

    # ------------------------------------------------------------ render ---
    def render(self):
        s = self.screen
        if self.state == 'title':
            ui.draw_title(s, self.t)
            pygame.display.flip()
            return
        s.fill(C_BG)
        ox, oy = self.camera.offset()
        self.draw_world(s, ox, oy)
        self.particles.draw_world(s, ox, oy)

        p = self.player
        if self.state in ('playing', 'dialogue', 'boss_intro', 'beacon', 'dead'):
            ui.draw_hud(s, p, story.AREA_NAMES.get(self.area, ''))
            if self.banner_t < 1.0:
                ui.draw_banner(s, *self.banner, self.banner_t)
            if self.active_boss and self.active_boss.alive:
                ui.draw_boss_bar(s, self.active_boss,
                                 story.BOSS_DATA[self.pending_boss]['name'])
            if p.lock_target is not None and getattr(p.lock_target, 'alive', False):
                tx, ty = world_to_screen(p.lock_target.x, p.lock_target.y, 150)
                ui.draw_lock_marker(s, tx + ox, ty + oy, self.t)
            if p.parry_success_t > 0:
                ui.draw_center_flash(s, "PARRY!", C_ACCENT)
            if self.flash_t > 0 and self.flash_msg:
                ui.text(s, self.flash_msg, WIDTH // 2, HEIGHT - 40, ui.F_MED,
                        C_ACCENT2, center=True)
            if self.state == 'playing':
                it = self.nearest_interactable()
                if it:
                    labels = {'beacon': "E — rest at the resonance shard",
                              'npc': "E — talk",
                              'lore': "E — read",
                              'weapon': "E — take the weapon",
                              'cache': "E — open the cache",
                              'echo': "E — reclaim your shards"}
                    ui.draw_prompt(s, labels[it[0]])

        if self.state == 'text':
            ui.draw_text_screen(s, self.text_lines, self.text_title,
                                t=min(1.0, self.state_t / 1.2))
        elif self.state == 'dialogue':
            name, pages, idx = self.dialogue
            ui.draw_dialogue(s, name, pages[idx], True)
        elif self.state == 'beacon':
            ui.draw_beacon_menu(s, p, self.beacon_sel, self.beacon_msg)
        elif self.state == 'map':
            ui.draw_map(s, self.world, p, self.bosses_defeated)
        elif self.state == 'boss_intro':
            bd = story.BOSS_DATA[self.pending_boss]
            ui.overlay(s, 170)
            ui.text(s, bd['name'], WIDTH // 2, 200, ui.F_BIG, C_BOSS, center=True)
            ui.text(s, bd['sub'], WIDTH // 2, 244, ui.F_MED, C_TEXT_DIM, center=True)
            for i, line in enumerate(bd['intro']):
                ui.text(s, line, WIDTH // 2, 320 + i * 28, ui.F_MED, C_TEXT, center=True)
            if self.state_t > 0.8:
                ui.text(s, "E — face them", WIDTH // 2, HEIGHT - 90, ui.F_MED,
                        C_DANGER, center=True)
        elif self.state == 'dead':
            ui.draw_death(s, self.death_msg, self.state_t)
        elif self.state == 'pause':
            ui.overlay(s, 170)
            ui.text(s, "PAUSED", WIDTH // 2, 200, ui.F_BIG, C_TEXT, center=True)
            for i, line in enumerate(story.CONTROLS):
                ui.text(s, line, WIDTH // 2, 260 + i * 24, ui.F_SMALL, C_TEXT_DIM, center=True)
            ui.text(s, "ESC — resume    Q — quit", WIDTH // 2, HEIGHT - 80,
                    ui.F_MED, C_ACCENT, center=True)
        elif self.state == 'ending_choice':
            ui.draw_ending_choice(s, story.ENDING_CHOICE, self.ending_sel)

        pygame.display.flip()

    # ---------------------------------------------------------- world draw ---
    def get_chunk(self, ccx, ccy):
        ch = self.chunks.get((ccx, ccy))
        if ch is None:
            w = CHUNK * TILE_W
            h = CHUNK * TILE_H + 96
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            x0, y0 = ccx * CHUNK, ccy * CHUNK
            for j in range(CHUNK):
                for i in range(CHUNK):
                    wx, wy = x0 + i, y0 + j
                    if wx >= self.world.w or wy >= self.world.h:
                        continue
                    ts, tid = self.world.floor[wy][wx]
                    lx = (i - j) * HALF_W + (CHUNK - 1) * HALF_W + HALF_W
                    ly = (i + j) * HALF_H
                    sprites.draw_tile(surf, ts, tid, lx, ly)
            ch = (surf, (CHUNK * HALF_W, 0))
            self.chunks[(ccx, ccy)] = ch
        return ch

    def draw_world(self, s, ox, oy):
        w = self.world
        corners = [screen_to_world(-ox + cx, -oy + cy)
                   for cx, cy in ((0, 0), (WIDTH, 0), (0, HEIGHT), (WIDTH, HEIGHT))]
        x0 = max(0, int(min(c[0] for c in corners)) - 2)
        x1 = min(w.w, int(max(c[0] for c in corners)) + 3)
        y0 = max(0, int(min(c[1] for c in corners)) - 2)
        y1 = min(w.h, int(max(c[1] for c in corners)) + 6)

        for ccy in range(y0 // CHUNK, (y1 - 1) // CHUNK + 1):
            for ccx in range(x0 // CHUNK, (x1 - 1) // CHUNK + 1):
                surf, (ax, ay) = self.get_chunk(ccx, ccy)
                sx, sy = world_to_screen(ccx * CHUNK, ccy * CHUNK)
                s.blit(surf, (sx + ox - ax, sy + oy - ay))

        self.particles.draw_decals(s, ox, oy)

        # boss telegraphs flat on the ground
        if self.active_boss:
            for tg in self.active_boss.telegraphs:
                sx, sy = world_to_screen(tg.x, tg.y)
                frac = 1.0 - tg.t / tg.total
                rw, rh = tg.r * HALF_W, tg.r * HALF_H
                rect = pygame.Rect(sx + ox - rw, sy + oy - rh, rw * 2, rh * 2)
                surf_tg = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(surf_tg, (255, 60, 50, 36 + int(56 * frac)),
                                    surf_tg.get_rect())
                pygame.draw.ellipse(surf_tg, (255, 80, 60, 180), surf_tg.get_rect(), 2)
                inner = surf_tg.get_rect().inflate(-rect.w * (1 - frac), -rect.h * (1 - frac))
                pygame.draw.ellipse(surf_tg, (255, 120, 80, 90), inner, 2)
                s.blit(surf_tg, rect.topleft)

        # beacon glows on the ground, pre-entity
        for bx, by, name in w.beacons:
            if x0 - 2 < bx < x1 + 2 and y0 - 2 < by < y1 + 2:
                gx, gy = world_to_screen(bx, by)
                g = self.glow_beacon
                s.blit(g, (gx + ox - g.get_width() // 2,
                           gy + oy - g.get_height() // 2 - 30),
                       special_flags=pygame.BLEND_RGBA_ADD)

        # ---- depth-sorted draw list ----
        drawables = []
        p = self.player

        def vis(x, y):
            return x0 - 3 < x < x1 + 3 and y0 - 6 < y < y1 + 6

        for o in w.objects:
            if vis(o.x, o.y):
                drawables.append((o.x + o.y + 1.0, 'tile', (o.ts, o.tid, o.x, o.y)))
        ts_c, ids_c = CRYSTAL
        for bx, by, name in w.beacons:
            if vis(bx, by):
                drawables.append((bx + by, 'tile_f', (ts_c, ids_c[0], bx, by)))
        ts_a, ids_a = ALTARS
        for (x, y, idx) in w.lore:
            if idx not in self.lore_found and vis(x, y):
                drawables.append((x + y, 'marker', (ts_a, ids_a[0], x, y, self.glow_amber)))
        ts_an, ids_an = FURNITURE
        for item in w.weapons:
            x, y, wkey = item
            if vis(x, y):
                drawables.append((x + y, 'marker', (ts_an, ids_an[8], x, y, self.glow_blue)))
        ts_cr, ids_cr = CRATES
        for item in w.caches:
            x, y = item[0], item[1]
            if vis(x, y):
                drawables.append((x + y, 'marker', (ts_cr, ids_cr[0], x, y, self.glow_amber)))
        if self.echo and vis(self.echo[0], self.echo[1]):
            drawables.append((self.echo[0] + self.echo[1], 'echo', self.echo))

        for (x, y, key, style) in w.npcs:
            if vis(x, y):
                drawables.append((x + y, 'npc', (x, y, style)))
        for e in self.enemies:
            if (e.alive or e.death_clock is not None) and vis(e.x, e.y):
                drawables.append((e.x + e.y, 'enemy', e))
        for key, boss in self.bosses.items():
            if (boss.alive or boss.death_clock is not None) and vis(boss.x, boss.y):
                drawables.append((boss.x + boss.y, 'boss', boss))
        if p.alive or self.state == 'dead':
            drawables.append((p.x + p.y, 'player', p))
        for pr in self.projectiles:
            drawables.append((pr.x + pr.y, 'proj', pr))
        if not self.gate_open:
            ts_i, ids_i = IRONFENCE
            for n, (gx, gy) in enumerate(w.gate_tiles):
                if vis(gx, gy):
                    drawables.append((gx + gy + 1.0, 'tile', (ts_i, ids_i[n % 2], gx, gy)))

        drawables.sort(key=lambda d: d[0])
        for depth, kind, payload in drawables:
            if kind in ('tile', 'tile_f'):
                ts, tid, x, y = payload
                if kind == 'tile_f':
                    sx, sy = world_to_screen(x - 0.5, y - 0.5)
                else:
                    sx, sy = world_to_screen(x, y)
                sprites.draw_tile(s, ts, tid, sx + ox, sy + oy)
            elif kind == 'marker':
                ts, tid, x, y, glow = payload
                sx, sy = world_to_screen(x - 0.5, y - 0.5)
                sprites.draw_tile(s, ts, tid, sx + ox, sy + oy)
                gx, gy = world_to_screen(x, y)
                s.blit(glow, (gx + ox - glow.get_width() // 2,
                              gy + oy - glow.get_height() // 2 - 16),
                       special_flags=pygame.BLEND_RGBA_ADD)
            elif kind == 'echo':
                x, y, amt = payload
                gx, gy = world_to_screen(x, y)
                pulse = 6 + int(3 * math.sin(self.t * 4))
                pygame.draw.circle(s, (170, 215, 255), (int(gx + ox), int(gy + oy - 18)), pulse, 2)
                pygame.draw.circle(s, (225, 242, 255), (int(gx + ox), int(gy + oy - 18)), 3)
            elif kind == 'npc':
                x, y, style = payload
                sprites.draw_enemy(s, ox, oy, style, x, y, 0.5, 0.5,
                                   ('stance', self.t, 'time'), self.t)
            elif kind == 'enemy':
                e = payload
                sprites.draw_enemy(s, ox, oy, e.style, e.x, e.y, e.fx, e.fy,
                                   e.anim_state(), e.anim_t, flash=e.hit_flash * 3)
                if e.alive and e.hp < e.max_hp:
                    self.draw_healthbar(s, ox, oy, e.x, e.y, 130, e.hp / e.max_hp)
            elif kind == 'boss':
                b = payload
                sprites.draw_enemy(s, ox, oy, b.style, b.x, b.y, b.fx, b.fy,
                                   b.anim_state(), b.anim_t, flash=b.hit_flash * 3,
                                   scale=1.3)
            elif kind == 'player':
                self.draw_player(s, ox, oy)
            elif kind == 'proj':
                pr = payload
                sx, sy = world_to_screen(pr.x, pr.y, 60)
                pygame.draw.circle(s, pr.color, (int(sx + ox), int(sy + oy)), 7)
                pygame.draw.circle(s, (255, 255, 255), (int(sx + ox), int(sy + oy)), 3)

        # parry shimmer
        if p.parry_active > 0:
            sx, sy = world_to_screen(p.x + p.fx * 0.5, p.y + p.fy * 0.5, 70)
            pygame.draw.circle(s, C_ACCENT, (int(sx + ox), int(sy + oy)), 16, 2)

        # fog over the closed gate
        if not self.gate_open:
            for (gx, gy) in w.gate_tiles[::2]:
                sx, sy = world_to_screen(gx + 0.5, gy + 0.5)
                sx += ox
                sy += oy
                if -TILE_W < sx < WIDTH + TILE_W and -200 < sy < HEIGHT + 100:
                    pulse = 22 + int(14 * math.sin(self.t * 2 + gx * 0.4))
                    fog = pygame.Surface((TILE_W, 150), pygame.SRCALPHA)
                    pygame.draw.polygon(fog, (150, 110, 255, pulse),
                                        [(0, 150), (TILE_W, 150), (TILE_W, 30), (0, 30)])
                    s.blit(fog, (sx - HALF_W, sy - 150))

    def draw_healthbar(self, s, ox, oy, x, y, z, frac):
        sx, sy = world_to_screen(x, y, z)
        sx += ox
        sy += oy
        pygame.draw.rect(s, (30, 30, 30), (sx - 16, sy, 32, 5))
        pygame.draw.rect(s, (80, 205, 70), (sx - 15, sy + 1, int(30 * max(0, frac)), 3))

    def draw_player(self, s, ox, oy):
        p = self.player
        if p.hit_iframes > 0 and int(self.t * 20) % 2 == 0 and p.alive:
            return
        alpha = 170 if p.state == 'roll' else 255
        sheet = p.weapon.get('sheet')
        sprites.draw_player(s, ox, oy, p.x, p.y, p.fx, p.fy, p.anim_state(),
                            p.anim_t, sheet, alpha=alpha)

    # -------------------------------------------------------------- run ---
    def run(self):
        while True:
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            self.handle_events()
            self.update(dt)
            self.render()


if __name__ == '__main__':
    Game().run()
