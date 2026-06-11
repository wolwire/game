"""STILLWAKE — a 2.5D isometric open-world souls-like set in Meridian City.

Run:  python3 main.py
"""
import math
import random
import sys

import pygame

pygame.init()

from src.constants import *
from src.iso import world_to_screen, screen_to_world
from src import assets
from src.worldgen import World, district_at
from src.player import Player
from src.enemy import Enemy
from src.boss import Boss
from src.camera import Camera
from src.particles import Particles
from src import ui
from src.entity import dist, Projectile
from data import story


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("STILLWAKE — a tale of the Stillness")
        self.clock = pygame.time.Clock()
        self.state = 'title'
        self.t = 0.0
        self.state_t = 0.0

        self.world = World()
        self.player = Player(*self.world.spawn)
        self.camera = Camera(self.player.x, self.player.y)
        self.particles = Particles()
        self.vignette = assets.vignette()
        ui.build_minimap(self.world)

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

        self.echo = None              # (x, y, shards) dropped on death
        self.area = district_at(int(self.player.x), int(self.player.y))
        self.banner = (story.AREA_NAMES.get(self.area, ''), story.AREA_DESC.get(self.area, ''))
        self.banner_t = 0.0
        self.flash_msg = None
        self.flash_t = 0.0

        # state payloads
        self.text_lines = []
        self.text_title = None
        self.text_next = 'playing'
        self.dialogue = None          # (name, pages, page_idx)
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
                    self.text_lines, self.text_title = story.INTRO, "OCTOBER 9TH, 3:14 AM"
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
                if k == pygame.K_ESCAPE:
                    self.set_state('playing')
                elif k == pygame.K_RETURN:
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
        best, best_d = None, 1.5
        for bx, by, name in self.world.beacons:
            d = dist(px, py, bx, by)
            if d < best_d:
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
            self.spawn_enemies()      # resting revives the city
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
        if key == 'archivist':
            self.text_lines = story.VICTORY_ARCHIVIST + [""] + story.ENDING_CHOICE
            self.text_title = "THE TOP FLOOR"
            self.text_next = 'ending_choice'
            self.set_state('text')
        elif not self.gate_open and {'warden', 'chorister'} <= self.bosses_defeated:
            self.set_gate(True)
            self.flash("Far north, the Helix Tower gate shudders open.", 5.0)

    # ------------------------------------------------------------ update ---
    def update(self, dt):
        self.t += dt
        self.state_t += dt
        self.particles.update(dt)
        self.flash_t = max(0, self.flash_t - dt)
        if self.state != 'playing':
            return
        p = self.player

        keys = pygame.key.get_pressed()
        mx = (keys[pygame.K_d] - keys[pygame.K_a])
        my = (keys[pygame.K_s] - keys[pygame.K_w])
        p.update(dt, self.world, (mx, my), keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        # area banner
        area = district_at(int(p.x), int(p.y))
        if area != self.area:
            self.area = area
            self.banner = (story.AREA_NAMES.get(area, ''), story.AREA_DESC.get(area, ''))
            self.banner_t = 0.0
        self.banner_t = min(1.0, self.banner_t + dt / 4.5)

        # gate bump message
        if not self.gate_open:
            for (gx, gy) in self.world.gate_tiles[::4]:
                if dist(p.x, p.y, gx + 0.5, gy + 0.5) < 2.2 and self.flash_t <= 0:
                    need = [k for k in ('warden', 'chorister') if k not in self.bosses_defeated]
                    names = ' and '.join(story.BOSS_DATA[k]['name'] for k in need)
                    self.flash(f"The Lattice denies you. It still grieves: {names}.", 3.5)

        # enemies
        for e in self.enemies:
            if e.alive and dist(p.x, p.y, e.x, e.y) < 30:
                e.update(dt, self.world, p, self.projectiles, self.particles)

        # bosses
        self.check_boss_triggers()
        if self.active_boss:
            boss = self.active_boss
            boss.update(dt, self.world, p, self.projectiles, self.particles, self.enemies)
            # confine player to arena during the fight
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

        # player attacks
        if p.attack_active():
            p.attack_hit_done = True
            hit_any = False
            for e in self.enemies:
                if e.alive and p.in_arc(e.x, e.y, e.radius):
                    gained = e.take_damage(p.attack_damage(), p.x, p.y, self.particles)
                    hit_any = True
                    if gained:
                        p.shards += gained
                        p.kills += 1
                        self.flash(f"+{gained} shards", 1.2)
            b = self.active_boss
            if b and b.alive and p.in_arc(b.x, b.y, b.radius):
                b.take_damage(p.attack_damage(), p.x, p.y, self.particles)
                hit_any = True
            if hit_any:
                self.camera.shake(3, 0.1)

        # projectiles
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

        # shard echo proximity sparkle
        if self.echo:
            self.particles.shard_sparkle(self.echo[0], self.echo[1])
        for bx, by, _ in self.world.beacons:
            if dist(p.x, p.y, bx, by) < 14:
                self.particles.beacon_idle(bx, by)

        self.camera.follow(p.x, p.y, dt)

        # death
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
        self.particles.draw_rain(s)
        s.blit(self.vignette, (0, 0))

        # HUD layer
        p = self.player
        if self.state in ('playing', 'dialogue', 'boss_intro', 'beacon', 'dead'):
            ui.draw_hud(s, p, story.AREA_NAMES.get(self.area, ''))
            if self.banner_t < 1.0:
                ui.draw_banner(s, *self.banner, self.banner_t)
            if self.active_boss and self.active_boss.alive:
                ui.draw_boss_bar(s, self.active_boss,
                                 story.BOSS_DATA[self.pending_boss]['name'])
            if p.lock_target is not None and getattr(p.lock_target, 'alive', False):
                tx, ty = world_to_screen(p.lock_target.x, p.lock_target.y, 30)
                ui.draw_lock_marker(s, tx + ox, ty + oy, self.t)
            if p.parry_success_t > 0:
                ui.draw_center_flash(s, "PARRY!", C_ACCENT)
            if self.flash_t > 0 and self.flash_msg:
                ui.text(s, self.flash_msg, WIDTH // 2, HEIGHT - 40, ui.F_MED,
                        C_ACCENT2, center=True)
            if self.state == 'playing':
                it = self.nearest_interactable()
                if it:
                    labels = {'beacon': "E — rest at the relay beacon",
                              'npc': "E — talk",
                              'lore': "E — read",
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
            ui.text(s, "PAUSED", WIDTH // 2, 240, ui.F_BIG, C_TEXT, center=True)
            for i, line in enumerate(story.CONTROLS):
                ui.text(s, line, WIDTH // 2, 300 + i * 24, ui.F_SMALL, C_TEXT_DIM, center=True)
            ui.text(s, "ESC — resume    Q — quit", WIDTH // 2, HEIGHT - 80,
                    ui.F_MED, C_ACCENT, center=True)
        elif self.state == 'ending_choice':
            ui.draw_ending_choice(s, story.ENDING_CHOICE, self.ending_sel)

        pygame.display.flip()

    def draw_world(self, s, ox, oy):
        w = self.world
        # visible world-rect from screen corners
        corners = [screen_to_world(-ox + cx, -oy + cy)
                   for cx, cy in ((0, 0), (WIDTH, 0), (0, HEIGHT), (WIDTH, HEIGHT))]
        x0 = max(0, int(min(c[0] for c in corners)) - 2)
        x1 = min(w.w, int(max(c[0] for c in corners)) + 3)
        y0 = max(0, int(min(c[1] for c in corners)) - 2)
        y1 = min(w.h, int(max(c[1] for c in corners)) + 9)

        # ground pass
        wave = self.t * 1.5
        for ty in range(y0, y1):
            row = w.ground[ty]
            for tx in range(x0, x1):
                sx, sy = world_to_screen(tx, ty)
                sx += ox
                sy += oy
                if sx < -TILE_W or sx > WIDTH or sy < -TILE_H or sy > HEIGHT + TILE_H:
                    continue
                kind = row[tx]
                variant = (tx * 7 + ty * 13) % 4
                if kind == 'water':
                    variant = int(wave + (tx + ty) * 0.5) % 4
                img, (ax, ay) = assets.ground_tile(kind, variant)
                s.blit(img, (sx, sy))
                dec = w.decals.get((tx, ty))
                if dec:
                    dimg, _ = assets.road_marking(dec)
                    s.blit(dimg, (sx, sy))

        # boss telegraphs (flat on ground)
        if self.active_boss:
            for tg in self.active_boss.telegraphs:
                sx, sy = world_to_screen(tg.x, tg.y)
                frac = 1.0 - tg.t / tg.total
                rw, rh = tg.r * TILE_W, tg.r * TILE_H
                rect = pygame.Rect(sx + ox - rw, sy + oy - rh, rw * 2, rh * 2)
                surf_tg = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(surf_tg, (255, 60, 50, 40 + int(60 * frac)),
                                    surf_tg.get_rect())
                pygame.draw.ellipse(surf_tg, (255, 80, 60, 180), surf_tg.get_rect(), 2)
                s.blit(surf_tg, rect.topleft)

        # depth-sorted entity pass
        drawables = []   # (depth, surf, x, y)

        def add(img_anchor, wx, wy, z=0.0, depth_bias=0.0):
            img, (ax, ay) = img_anchor
            sx, sy = world_to_screen(wx, wy, z)
            drawables.append((wx + wy + depth_bias, img, sx + ox - ax, sy + oy - ay))

        px, py = self.player.x, self.player.y
        view_r = 26
        for b in w.buildings:
            if abs(b.x - px) < view_r + b.fw and abs(b.y - py) < view_r + b.fh:
                add(assets.building(b.seed, b.fw, b.fh, b.stories, b.style),
                    b.x, b.y, depth_bias=b.fw + b.fh - 1)
        for pr in w.props:
            if abs(pr.x - px) < view_r and abs(pr.y - py) < view_r:
                if pr.kind == 'car':
                    add(assets.car(pr.seed, pr.axis), pr.x, pr.y)
                else:
                    add(assets.prop(pr.kind, pr.variant), pr.x, pr.y)
        for bx, by, name in w.beacons:
            if abs(bx - px) < view_r and abs(by - py) < view_r:
                add(assets.prop('beacon'), bx, by)
        for (x, y, idx) in w.lore:
            if idx not in self.lore_found and abs(x - px) < view_r and abs(y - py) < view_r:
                add(assets.prop('lore'), x, y)
        if self.echo and abs(self.echo[0] - px) < view_r and abs(self.echo[1] - py) < view_r:
            add(assets.prop('shard_echo'), self.echo[0], self.echo[1])
        for (x, y, key, style) in w.npcs:
            if abs(x - px) < view_r and abs(y - py) < view_r:
                add(assets.character(style, 2, 0), x, y)
        for e in self.enemies:
            if e.alive and abs(e.x - px) < view_r and abs(e.y - py) < view_r:
                img, anchor = assets.character(e.style, e.octant(), e.anim_frame())
                if e.hit_flash > 0:
                    img = img.copy()
                    img.fill((90, 30, 30, 0), special_flags=pygame.BLEND_RGBA_ADD)
                add((img, anchor), e.x, e.y)
        for key, boss in self.bosses.items():
            if boss.alive and abs(boss.x - px) < view_r and abs(boss.y - py) < view_r:
                img, anchor = assets.character(boss.style, boss.octant(), boss.anim_frame())
                if boss.hit_flash > 0:
                    img = img.copy()
                    img.fill((90, 30, 30, 0), special_flags=pygame.BLEND_RGBA_ADD)
                add((img, anchor), boss.x, boss.y)

        # player (with roll tilt + attack slash)
        p = self.player
        if p.alive or self.state == 'dead':
            img, anchor = assets.character('player', p.octant(), p.anim_frame())
            if p.state == 'roll':
                img = pygame.transform.rotate(img, 28 if p.roll_dx - p.roll_dy > 0 else -28)
                anchor = (img.get_width() // 2, img.get_height() - 6)
            if p.state == 'stim':
                img = img.copy()
                img.fill((20, 60, 20, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if p.hit_iframes > 0 and int(self.t * 20) % 2 == 0:
                img = img.copy()
                img.set_alpha(120)
            add((img, anchor), p.x, p.y)

        # projectiles
        for pr in self.projectiles:
            sx, sy = world_to_screen(pr.x, pr.y, 22)
            drawables.append((pr.x + pr.y, None, sx + ox, sy + oy, pr.color))

        drawables.sort(key=lambda d: d[0])
        for d in drawables:
            if d[1] is None:
                _, _, sx, sy, color = d
                pygame.draw.circle(s, color, (int(sx), int(sy)), 5)
                pygame.draw.circle(s, (255, 255, 255), (int(sx), int(sy)), 2)
            else:
                s.blit(d[1], (d[2], d[3]))

        # attack slash arc on top
        if p.attack_active() or (p.state in ('attack', 'heavy') and p.attack_hit_done
                                 and p.timer > (LIGHT_RECOVER if p.state == 'attack'
                                                else HEAVY_RECOVER) - 0.12):
            sx, sy = world_to_screen(p.x + p.fx * 0.9, p.y + p.fy * 0.9, 24)
            ang = math.atan2(-(p.fx + p.fy) * 0.5, (p.fx - p.fy))
            color = C_ACCENT if p.state == 'attack' else C_ACCENT2
            img, (ax, ay) = assets.slash_arc(34, color)
            img = pygame.transform.rotate(img, math.degrees(ang))
            r = img.get_rect(center=(sx + ox, sy + oy))
            s.blit(img, r)

        # parry shimmer
        if p.parry_active > 0:
            sx, sy = world_to_screen(p.x + p.fx * 0.5, p.y + p.fy * 0.5, 26)
            pygame.draw.circle(s, C_ACCENT, (int(sx + ox), int(sy + oy)), 14, 2)

        # fog gate
        if not self.gate_open:
            for (gx, gy) in w.gate_tiles:
                sx, sy = world_to_screen(gx, gy)
                sx += ox
                sy += oy
                if -TILE_W < sx < WIDTH and -100 < sy < HEIGHT + 60:
                    hgt = 70
                    fog = pygame.Surface((TILE_W, TILE_H + hgt), pygame.SRCALPHA)
                    pulse = 30 + int(20 * math.sin(self.t * 2 + gx))
                    pts = assets.diamond_points(0, hgt)
                    pygame.draw.polygon(fog, (90, 200, 255, pulse),
                                        [(pts[3][0], pts[3][1] - hgt), (pts[1][0], pts[1][1] - hgt),
                                         pts[1], pts[3]])
                    pygame.draw.line(fog, (140, 230, 255, 90),
                                     (pts[3][0], pts[3][1] - hgt), (pts[1][0], pts[1][1] - hgt), 2)
                    s.blit(fog, (sx, sy - hgt + 0))

    # -------------------------------------------------------------- run ---
    def run(self):
        while True:
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            self.handle_events()
            self.update(dt)
            self.render()


if __name__ == '__main__':
    Game().run()
