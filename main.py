import pygame
import sys
import math
import random
import os

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

pygame.init()
pygame.display.set_mode((1280, 720))

from src.constants import *
from src.camera import Camera
from src.player import Player
from src.enemy import Enemy
from src.boss import Boss
from src.particles import ParticleSystem
from src.world import (draw_tiles, SiteOfGrace, LoreFragment, RunePickup,
                        WORLD_MAKERS, BOSS_TYPES, BOSS_SPAWN_OFFSETS)
from src.ui import (draw_hud, draw_boss_bar, draw_status_text, draw_area_name,
                     draw_text_screen, draw_parry_success, draw_pickup_text)
from data.lore import (INTRO, CONTROLS, AREA_NAMES, GRACE_MESSAGES,
                        BOSS_INTRO, VICTORY_TEXT, ENDING_RESTORE, ENDING_BURN,
                        LORE_FRAGMENTS, DEATH_MESSAGES)


class GameState:
    INTRO = 'intro'
    CONTROLS = 'controls'
    PLAYING = 'playing'
    BOSS_INTRO = 'boss_intro'
    DEAD = 'dead'
    GRACE = 'grace'
    LORE = 'lore'
    VICTORY = 'victory'
    ENDING = 'ending'


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("TARNISHED — A Lands Between Tale")
        self.clock = pygame.time.Clock()

        self.state = GameState.INTRO
        self.area_idx = 0
        self.load_area(0)
        self.particles = ParticleSystem()

        # Screen text state
        self.text_lines = INTRO
        self.text_alpha = 0
        self.fade_in = True

        # Notification
        self.pickup_text = ''
        self.pickup_timer = 0

        # Area name display
        self.area_name_alpha = 0
        self.area_name_timer = 0

        # Death state
        self.death_fade = 0
        self.respawn_delay = 0

        # Boss intro state
        self.boss_intro_lines = []
        self.boss_intro_timer = 0

        # Parry text
        self.parry_text_pos = None
        self.parry_text_timer = 0

        # Grace menu
        self.grace_choice = 0

        # Lore text
        self.lore_lines = []

        # Ending
        self.ending_lines = []
        self.ending_alpha = 0

        # Persistent rune drop
        self.rune_pickups = []

        # Frames elapsed
        self.frame = 0

    def load_area(self, idx):
        maker = WORLD_MAKERS[idx]
        self.tiles, self.walls, entities_data, graces_data, lore_data, mw, mh = maker()
        self.camera = Camera(mw, mh)

        spawn_x = 10 * TILE_SIZE
        spawn_y = 8 * TILE_SIZE
        self.player = Player(spawn_x, spawn_y)

        self.enemies = []
        for etype, ex, ey in entities_data:
            self.enemies.append(Enemy(ex, ey, etype))

        bx, by = BOSS_SPAWN_OFFSETS[idx]
        self.boss = Boss(bx, by, BOSS_TYPES[idx])

        self.graces = graces_data
        self.lore_fragments = lore_data
        self.rune_pickups = []

        self.camera.offset.x = spawn_x - WIDTH // 2
        self.camera.offset.y = spawn_y - HEIGHT // 2

    def handle_input_intro(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.state == GameState.INTRO:
                self.state = GameState.CONTROLS
                self.text_lines = CONTROLS
            elif self.state == GameState.CONTROLS:
                self.state = GameState.PLAYING
                self.show_area_name()
            elif self.state == GameState.LORE:
                self.state = GameState.PLAYING
            elif self.state == GameState.BOSS_INTRO:
                self.state = GameState.PLAYING

    def handle_input_game(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                if self.player.light_attack():
                    pass
            elif event.key == pygame.K_x:
                if self.player.heavy_attack():
                    pass
            elif event.key == pygame.K_SPACE:
                keys = pygame.key.get_pressed()
                move = pygame.math.Vector2(0, 0)
                if keys[pygame.K_w] or keys[pygame.K_UP]: move.y -= 1
                if keys[pygame.K_s] or keys[pygame.K_DOWN]: move.y += 1
                if keys[pygame.K_a] or keys[pygame.K_LEFT]: move.x -= 1
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move.x += 1
                self.player.roll(move)
            elif event.key == pygame.K_q:
                self.player.parry()
            elif event.key == pygame.K_f:
                self.player.use_flask()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    def handle_input_dead(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if self.respawn_delay <= 0:
                self.respawn()

    def handle_input_victory(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.start_ending('restore')
            elif event.key == pygame.K_b:
                self.start_ending('burn')

    def handle_input_ending(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            pygame.quit()
            sys.exit()

    def show_area_name(self):
        self.area_name_alpha = 255
        self.area_name_timer = 240

    def show_pickup(self, text, duration=180):
        self.pickup_text = text
        self.pickup_timer = duration

    def trigger_boss_intro(self):
        self.state = GameState.BOSS_INTRO
        self.boss_intro_lines = BOSS_INTRO.get(self.boss.boss_type, [self.boss.name])
        self.boss_intro_timer = 240

    def start_ending(self, choice):
        self.state = GameState.ENDING
        self.ending_lines = ENDING_RESTORE if choice == 'restore' else ENDING_BURN
        self.ending_alpha = 0

    def respawn(self):
        # Place rune pickup at death location
        if self.player.lost_runes > 0 and self.player.lost_rune_pos:
            self.rune_pickups.append(RunePickup(
                self.player.lost_rune_pos[0],
                self.player.lost_rune_pos[1],
                self.player.lost_runes
            ))

        self.player = Player(10 * TILE_SIZE, 8 * TILE_SIZE)
        self.death_fade = 0

        # Respawn enemies killed in this session
        self.enemies = [e for e in self.enemies if not e.dead]
        # Respawn all enemies at their original counts via reload?
        # For now keep survivors but reset boss if it died
        if self.boss.dead:
            bx, by = BOSS_SPAWN_OFFSETS[self.area_idx]
            self.boss = Boss(bx, by, BOSS_TYPES[self.area_idx])

        self.state = GameState.PLAYING
        self.show_area_name()

    def update_playing(self):
        keys = pygame.key.get_pressed()
        p = self.player

        if p.dead:
            self.state = GameState.DEAD
            self.death_fade = 0
            self.respawn_delay = 120
            return

        p.update(keys, self.walls)
        self.camera.update(p.rect)
        self.particles.update()

        # Update enemies
        for e in self.enemies:
            if not e.dead:
                e.update(p, self.walls)
            # Enemy attack hits player
            ehb = e.get_attack_hitbox()
            if ehb and p.rect.colliderect(ehb):
                diff = p.pos - e.pos
                if p.take_damage(e.dmg):
                    self.particles.emit_blood(p.pos.x, p.pos.y)

        # Update boss
        if self.boss and not self.boss.dead:
            self.boss.update(p, self.walls)
            # Check boss aggro range for intro
            dist = self.boss.pos.distance_to(p.pos)
            if dist < 350 and not self.boss.aggro and self.state == GameState.PLAYING:
                self.trigger_boss_intro()
                self.boss.aggro = True

            # Boss hitboxes hit player
            for hb in self.boss.active_hitboxes:
                if p.rect.colliderect(hb):
                    atk = getattr(self.boss, 'current_atk', None)
                    dmg = atk['dmg'] if atk else 20
                    if p.take_damage(dmg):
                        self.particles.emit_blood(p.pos.x, p.pos.y)

            # Boss projectiles
            for proj in self.boss.projectiles[:]:
                pr = pygame.Rect(proj['x']-10, proj['y']-10, 20, 20)
                if p.rect.colliderect(pr):
                    if p.take_damage(proj['dmg']):
                        self.particles.emit_blood(p.pos.x, p.pos.y)
                    self.boss.projectiles.remove(proj)

        # Player attack hits enemies
        p_hb = p.get_attack_hitbox()
        if p_hb:
            for e in self.enemies:
                if not e.dead and id(e) not in p.hit_enemies:
                    if p_hb.colliderect(e.rect):
                        # Check parry
                        if e.is_winding_up():
                            pass  # Could parry enemy wind-ups too
                        dmg = p.light_dmg if p.attack_type == 'light' else p.heavy_dmg
                        if e.take_damage(dmg):
                            p.hit_enemies.add(id(e))
                            self.particles.emit_hit(e.pos.x, e.pos.y)
                            if e.dead:
                                p.runes += e.rune_reward
                                self.particles.emit_death(e.pos.x, e.pos.y, (80, 200, 100))

            # Hit boss
            if self.boss and not self.boss.dead and id(self.boss) not in p.hit_enemies:
                if p_hb.colliderect(self.boss.rect):
                    # Check if player is parrying and boss is attacking
                    stagger = False
                    if p.get_parry_active() and self.boss.is_winding_up():
                        stagger = True
                        self.parry_text_pos = (p.pos.x, p.pos.y)
                        self.parry_text_timer = 60
                        self.particles.emit_parry(p.pos.x, p.pos.y)
                    dmg = p.light_dmg if p.attack_type == 'light' else p.heavy_dmg
                    if self.boss.take_damage(dmg, stagger):
                        p.hit_enemies.add(id(self.boss))
                        self.particles.emit_hit(self.boss.pos.x, self.boss.pos.y)
                        if self.boss.dead:
                            self.particles.emit_death(self.boss.pos.x, self.boss.pos.y, GOLD, )

        # Parry vs enemy wind-up
        if p.get_parry_active():
            for e in self.enemies:
                if not e.dead and e.is_winding_up():
                    if p.rect.inflate(60, 60).colliderect(e.rect):
                        e.take_damage(0, stagger=True)
                        e.attack_timer = 0
                        self.parry_text_pos = (p.pos.x, p.pos.y)
                        self.parry_text_timer = 60
                        self.particles.emit_parry(p.pos.x, p.pos.y)

        # Check grace interaction
        for g in self.graces:
            if p.rect.colliderect(g.rect.inflate(20, 20)):
                if not g.lit:
                    g.lit = True
                    p.flasks = p.max_flasks
                    p.hp = p.max_hp
                    msg = random.choice(GRACE_MESSAGES)
                    self.show_pickup(msg, 220)
                    self.particles.emit_death(g.pos.x, g.pos.y, GOLD, 20)
                self.particles.emit_grace(g.pos.x, g.pos.y)

        # Check lore fragments
        for lf in self.lore_fragments:
            if not lf.collected and p.rect.colliderect(lf.rect.inflate(20, 20)):
                lf.collected = True
                lines = LORE_FRAGMENTS.get(lf.key, ["A strange inscription..."])
                self.lore_lines = lines
                self.state = GameState.LORE

        # Check rune pickups
        for rp in self.rune_pickups[:]:
            if not rp.collected and p.rect.colliderect(rp.rect.inflate(10, 10)):
                rp.collected = True
                p.runes += rp.amount
                self.show_pickup(f"Recovered {rp.amount} Runes", 180)
                self.particles.emit_hit(rp.pos.x, rp.pos.y, (80, 220, 120))

        # Check boss death -> next area or victory
        if self.boss and self.boss.dead and self.boss.death_timer <= 0:
            if self.area_idx < 2:
                self.area_idx += 1
                saved_runes = p.runes
                self.load_area(self.area_idx)
                self.player.runes = saved_runes
                self.show_pickup(f"Entering {AREA_NAMES[self.area_idx]}...", 240)
                self.show_area_name()
            else:
                self.state = GameState.VICTORY

        # Area name fade
        if self.area_name_timer > 0:
            self.area_name_timer -= 1
            self.area_name_alpha = min(255, self.area_name_alpha)
            if self.area_name_timer < 60:
                self.area_name_alpha = int(255 * self.area_name_timer / 60)

        # Pickup text fade
        if self.pickup_timer > 0:
            self.pickup_timer -= 1

        # Parry text
        if self.parry_text_timer > 0:
            self.parry_text_timer -= 1

    def render_playing(self):
        cam_ox = int(self.camera.offset.x)
        cam_oy = int(self.camera.offset.y)

        # Background
        self.screen.fill((18, 16, 14))

        # Tiles
        draw_tiles(self.screen, self.tiles, cam_ox, cam_oy)

        # Graces
        for g in self.graces:
            g.draw(self.screen, cam_ox, cam_oy)

        # Lore fragments
        for lf in self.lore_fragments:
            lf.draw(self.screen, cam_ox, cam_oy)

        # Rune pickups
        for rp in self.rune_pickups:
            rp.draw(self.screen, cam_ox, cam_oy)

        # Enemies
        for e in self.enemies:
            e.draw(self.screen, cam_ox, cam_oy)

        # Boss
        if self.boss:
            self.boss.draw(self.screen, cam_ox, cam_oy)

        # Player
        self.player.draw(self.screen, cam_ox, cam_oy)

        # Particles
        self.particles.draw(self.screen, cam_ox, cam_oy)

        # Parry text
        if self.parry_text_timer > 0 and self.parry_text_pos:
            draw_parry_success(self.screen,
                               self.parry_text_pos[0], self.parry_text_pos[1],
                               cam_ox, cam_oy)

        # HUD
        draw_hud(self.screen, self.player)
        draw_boss_bar(self.screen, self.boss)

        # Area name
        if self.area_name_timer > 0:
            draw_area_name(self.screen, AREA_NAMES[self.area_idx], self.area_name_alpha)

        # Pickup text
        if self.pickup_timer > 0:
            draw_pickup_text(self.screen, self.pickup_text, self.pickup_timer)

    def run(self):
        running = True
        while running:
            self.frame += 1
            dt = self.clock.tick(FPS) / (1000 / FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif self.state in (GameState.INTRO, GameState.CONTROLS,
                                     GameState.LORE, GameState.BOSS_INTRO):
                    self.handle_input_intro(event)
                elif self.state == GameState.PLAYING:
                    self.handle_input_game(event)
                elif self.state == GameState.DEAD:
                    self.handle_input_dead(event)
                elif self.state == GameState.VICTORY:
                    self.handle_input_victory(event)
                elif self.state == GameState.ENDING:
                    self.handle_input_ending(event)

            # Update
            if self.state == GameState.PLAYING:
                self.update_playing()
            elif self.state == GameState.DEAD:
                self.respawn_delay = max(0, self.respawn_delay - 1)
                self.death_fade = min(255, self.death_fade + 4)
                self.particles.update()
            elif self.state == GameState.BOSS_INTRO:
                self.boss_intro_timer -= 1
                if self.boss_intro_timer <= 0:
                    self.state = GameState.PLAYING
            elif self.state == GameState.ENDING:
                self.ending_alpha = min(255, self.ending_alpha + 2)

            # Render
            self.screen.fill((8, 8, 10))

            if self.state == GameState.INTRO:
                self.text_alpha = min(255, self.text_alpha + 3)
                draw_text_screen(self.screen, self.text_lines, alpha=self.text_alpha)

            elif self.state == GameState.CONTROLS:
                draw_text_screen(self.screen, self.text_lines, alpha=255)

            elif self.state == GameState.PLAYING:
                self.render_playing()

            elif self.state == GameState.BOSS_INTRO:
                self.render_playing()
                a = min(255, int(255 * (1 - self.boss_intro_timer / 240)) * 2)
                draw_text_screen(self.screen, self.boss_intro_lines, font_size=20, title_size=36, alpha=min(255, a))

            elif self.state == GameState.DEAD:
                self.render_playing()
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((60, 0, 0, int(self.death_fade * 0.7)))
                self.screen.blit(overlay, (0, 0))
                if self.death_fade > 120:
                    draw_status_text(self.screen, "YOU DIED", min(255, (self.death_fade - 120) * 4))
                    if self.respawn_delay <= 0:
                        hint = pygame.font.SysFont('monospace', 18).render("Press ENTER to rise again", True, (180, 140, 140))
                        self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 50))

            elif self.state == GameState.GRACE:
                self.render_playing()

            elif self.state == GameState.LORE:
                self.render_playing()
                draw_text_screen(self.screen, self.lore_lines + ['', '— Press ENTER —'], alpha=230)

            elif self.state == GameState.VICTORY:
                self.render_playing()
                draw_text_screen(self.screen, VICTORY_TEXT, font_size=18, title_size=28, alpha=230)

            elif self.state == GameState.ENDING:
                draw_text_screen(self.screen, self.ending_lines + ['', '— Press ENTER to exit —'],
                                 font_size=20, title_size=30, alpha=int(self.ending_alpha))

            pygame.display.flip()

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
