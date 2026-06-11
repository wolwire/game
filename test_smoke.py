"""Headless smoke test: boots the game, drives it through title -> intro ->
controls -> gameplay, simulates movement/combat, and saves screenshots."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import main as game_main


def press(g, key):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    g.handle_events()


def frames(g, n, dt=1 / 60):
    for _ in range(n):
        g.handle_events()
        g.update(dt)
        g.render()


def shot(g, name):
    pygame.image.save(g.screen, name)
    print('saved', name)


g = game_main.Game()
print('world generated:', len(g.world.buildings), 'buildings,',
      len(g.world.props), 'props,', len(g.enemies), 'enemies,',
      len(g.world.beacons), 'beacons,', len(g.bosses), 'bosses')

frames(g, 5)
shot(g, 'ss_title.png')
press(g, pygame.K_RETURN)          # title -> intro text
frames(g, 90)
shot(g, 'ss_intro.png')
press(g, pygame.K_e)               # -> controls
frames(g, 90)
press(g, pygame.K_e)               # -> playing
frames(g, 30)
shot(g, 'ss_start.png')
assert g.state == 'playing', g.state

# walk around
kd = pygame.key.get_pressed()


class FakeKeys(dict):
    def __getitem__(self, k):
        return self.get(k, 0)


held = FakeKeys()
real_get = pygame.key.get_pressed
pygame.key.get_pressed = lambda: held

held[pygame.K_d] = 1
frames(g, 120)
held[pygame.K_d] = 0
held[pygame.K_s] = 1
frames(g, 60)
held[pygame.K_s] = 0
shot(g, 'ss_walk.png')
print('player at', round(g.player.x, 1), round(g.player.y, 1), 'state', g.state)

# attack & roll
press(g, pygame.K_j)
frames(g, 20)
press(g, pygame.K_SPACE)
frames(g, 30)
press(g, pygame.K_k)
frames(g, 40)
print('after combat inputs, hp', g.player.hp, 'stam', round(g.player.stamina))

# map
press(g, pygame.K_m)
frames(g, 3)
shot(g, 'ss_map.png')
press(g, pygame.K_m)

# talk to Maya (teleport near)
g.player.x, g.player.y = 19.0, 64.0
frames(g, 3)
press(g, pygame.K_e)
frames(g, 3)
print('dialogue state:', g.state)
shot(g, 'ss_dialogue.png')
while g.state == 'dialogue':
    press(g, pygame.K_e)
    frames(g, 2)

# rest at beacon
g.player.x, g.player.y = 17.6, 63.6
frames(g, 3)
press(g, pygame.K_e)
frames(g, 3)
print('beacon state:', g.state)
shot(g, 'ss_beacon.png')
g.player.shards = 500
press(g, pygame.K_e)   # buy vigor
frames(g, 2)
print('level', g.player.level, 'vigor', g.player.vigor, 'shards', g.player.shards)
press(g, pygame.K_s)
press(g, pygame.K_s)
press(g, pygame.K_s)
press(g, pygame.K_e)   # leave
frames(g, 2)
assert g.state == 'playing', g.state

def fight_boss(g, key, arena_xy):
    g.player.x, g.player.y = arena_xy
    g.player.hp = g.player.max_hp
    g.player.state = 'idle'
    frames(g, 10)
    assert g.state == 'boss_intro', (key, g.state)
    g.state_t = 2.0
    press(g, pygame.K_e)
    frames(g, 90)
    assert g.active_boss is not None and g.active_boss.hp < g.active_boss.max_hp + 1
    # finish it: stand next to it and land a light attack
    g.bosses[key].hp = 1
    g.player.x = g.bosses[key].x + 1.0
    g.player.y = g.bosses[key].y
    g.player.stamina = 100
    g.player.state = 'idle'
    press(g, pygame.K_TAB)
    press(g, pygame.K_j)
    frames(g, 60)


# go fight the Warden
g.player.x, g.player.y = 8.5, 30.5
frames(g, 10)
print('boss state:', g.state)
shot(g, 'ss_boss_intro.png')
assert g.state == 'boss_intro'
g.state_t = 2.0
press(g, pygame.K_e)
frames(g, 90)
shot(g, 'ss_boss_fight.png')
print('active boss:', g.pending_boss, 'boss hp', g.active_boss.hp if g.active_boss else None)
g.bosses['warden'].hp = 1
g.player.x = g.bosses['warden'].x + 1.0
g.player.y = g.bosses['warden'].y
g.player.stamina = 100
g.player.state = 'idle'
press(g, pygame.K_TAB)
press(g, pygame.K_j)
frames(g, 60)
print('warden defeated?', 'warden' in g.bosses_defeated, 'shards', g.player.shards)
assert 'warden' in g.bosses_defeated

# die on purpose, away from boss arenas
g.player.x, g.player.y = 50.0, 50.0
g.player.hp = 1
g.player.hit_iframes = 0
g.player.iframes = 0
g.player.take_damage(50)
frames(g, 30)
print('death state:', g.state, 'echo:', g.echo)
shot(g, 'ss_death.png')
assert g.state == 'dead'
g.state_t = 2.0
press(g, pygame.K_e)
frames(g, 30)
print('respawned at', round(g.player.x, 1), round(g.player.y, 1), 'state', g.state)
assert g.state == 'playing'

# warden stays dead after respawn
assert not g.bosses['warden'].active and 'warden' in g.bosses_defeated

# chorister, then gate should open
fight_boss(g, 'chorister', (58.0, 18.5))
print('chorister defeated?', 'chorister' in g.bosses_defeated, '| gate open?', g.gate_open)
assert g.gate_open

# archivist + ending flow
fight_boss(g, 'archivist', (97.0, 21.0))
print('post-archivist state:', g.state)
shot(g, 'ss_victory.png')
assert g.state == 'text'
g.state_t = 2.0
press(g, pygame.K_e)
frames(g, 5)
print('ending state:', g.state)
shot(g, 'ss_ending_choice.png')
assert g.state == 'ending_choice'
press(g, pygame.K_e)
frames(g, 60)
shot(g, 'ss_ending.png')
assert g.state == 'text'
print('SMOKE TEST OK')
