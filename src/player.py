"""Calle Wren — souls-like state machine with a real weapon system:
per-weapon combo chains, queued inputs, dodge i-frames, parry, stims."""
import math
from src.constants import *
from src.entity import move_with_collision, dist, norm
from src.iso import screen_dir_to_world
from src.weapons import WEAPONS, step_time


class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 0.55
        # stats
        self.level = 1
        self.vigor = 5
        self.endurance = 5
        self.strength = 5
        self.shards = 0
        self.bonus_hp = 0
        self.stim_max = STIM_CHARGES
        self.hp = self.max_hp
        self.stamina = self.max_stamina
        self.stims = self.stim_max
        # gear
        self.inventory = ['wrench']
        self.weapon_idx = 0
        # state
        self.state = 'idle'        # idle walk run roll attack parry stim dead
        self.timer = 0.0
        self.fx, self.fy = 1.0, 0.0
        self.move_dx, self.move_dy = 0.0, 0.0
        self.roll_dx, self.roll_dy = 0.0, 0.0
        self.iframes = 0.0
        self.hit_iframes = 0.0
        self.stam_delay = 0.0
        # attack bookkeeping
        self.atk_heavy = False
        self.atk_step = 0
        self.atk_elapsed = 0.0
        self.atk_hit_done = False
        self.atk_queued = False
        self.trail = []
        self.parry_active = 0.0
        self.parry_success_t = 0.0
        self.lock_target = None
        self.anim_t = 0.0
        self.sprinting = False
        self.walking = False
        self.kills = 0
        self.deaths = 0
        self.state_t = 0.0

    # ---- derived ----
    @property
    def max_hp(self):
        return PLAYER_BASE_HP + self.vigor * VIGOR_HP + self.bonus_hp

    @property
    def max_stamina(self):
        return PLAYER_BASE_STAMINA + self.endurance * ENDURANCE_STAM

    @property
    def dmg_mult(self):
        return 1.0 + self.strength * STRENGTH_DMG

    @property
    def weapon(self):
        return WEAPONS[self.inventory[self.weapon_idx]]

    @property
    def alive(self):
        return self.state != 'dead'

    def busy(self):
        return self.state in ('roll', 'attack', 'parry', 'stim')

    def give_weapon(self, key):
        if key not in self.inventory:
            self.inventory.append(key)
            self.weapon_idx = len(self.inventory) - 1
            return True
        return False

    def cycle_weapon(self, d=1):
        if not self.busy():
            self.weapon_idx = (self.weapon_idx + d) % len(self.inventory)

    # ---- current attack step info ----
    def _step_def(self):
        w = self.weapon
        if self.atk_heavy:
            k, wu, act, rec, mult = w['heavy']
            return (k, wu, act, rec)
        return w['combo'][self.atk_step]

    def attack_progress(self):
        return min(1.0, self.atk_elapsed / max(0.01, step_time(self._step_def())))

    def attack_kind(self):
        return self._step_def()[0]

    # ---- inputs ----
    def try_roll(self):
        if self.busy() or self.stamina < ROLL_COST or not self.alive:
            return
        dx, dy = self.move_dx, self.move_dy
        if abs(dx) < 0.01 and abs(dy) < 0.01:
            dx, dy = self.fx, self.fy
        self.roll_dx, self.roll_dy = norm(dx, dy)
        self.state = 'roll'
        self.state_t = 0.0
        self.timer = ROLL_TIME
        self.iframes = ROLL_IFRAMES
        self._spend(ROLL_COST)

    def try_attack(self, heavy=False):
        if not self.alive:
            return
        w = self.weapon
        # chain: queue the next light during recover
        if self.state == 'attack' and not heavy and not self.atk_heavy:
            k, wu, act, rec = self._step_def()
            if self.atk_elapsed > wu + act and self.atk_step + 1 < len(w['combo']):
                self.atk_queued = True
            return
        if self.busy():
            return
        cost = w['stamina'] * (2.0 if heavy else 1.0)
        if self.stamina < cost:
            return
        self._face_target()
        self.state = 'attack'
        self.state_t = 0.0
        self.atk_heavy = heavy
        self.atk_step = 0
        self.atk_elapsed = 0.0
        self.atk_hit_done = False
        self.atk_queued = False
        self.trail.clear()
        self._spend(cost)

    def _face_target(self):
        if self.lock_target is not None and getattr(self.lock_target, 'alive', False):
            self.fx, self.fy = norm(self.lock_target.x - self.x, self.lock_target.y - self.y)
        elif abs(self.move_dx) > 0.01 or abs(self.move_dy) > 0.01:
            self.fx, self.fy = self.move_dx, self.move_dy

    def try_parry(self):
        if self.busy() or not self.alive or self.stamina < 10:
            return
        self.state = 'parry'
        self.state_t = 0.0
        self.timer = PARRY_WINDOW + PARRY_RECOVER
        self.parry_active = PARRY_WINDOW
        self._spend(10)

    def try_stim(self):
        if self.busy() or not self.alive or self.stims <= 0 or self.hp >= self.max_hp:
            return
        self.state = 'stim'
        self.state_t = 0.0
        self.timer = STIM_TIME

    def _spend(self, amt):
        self.stamina = max(0, self.stamina - amt)
        self.stam_delay = STAMINA_REGEN_DELAY

    # ---- per-frame ----
    def update(self, dt, world, move_screen, sprinting):
        self.anim_t += dt
        self.state_t += dt
        self.iframes = max(0, self.iframes - dt)
        self.hit_iframes = max(0, self.hit_iframes - dt)
        self.parry_active = max(0, self.parry_active - dt)
        self.parry_success_t = max(0, self.parry_success_t - dt)
        for t in self.trail:
            t[2] -= dt
        self.trail[:] = [t for t in self.trail if t[2] > 0]
        if not self.alive:
            return

        mdx, mdy = screen_dir_to_world(*move_screen) if any(move_screen) else (0.0, 0.0)
        self.move_dx, self.move_dy = mdx, mdy
        self.walking = False
        self.sprinting = False

        if self.state in ('idle', 'walk', 'run'):
            speed = PLAYER_SPEED
            if sprinting and (mdx or mdy) and self.stamina > 1:
                speed *= PLAYER_SPRINT_MULT
                self.sprinting = True
                self.stamina = max(0, self.stamina - SPRINT_DRAIN * dt)
                self.stam_delay = max(self.stam_delay, 0.2)
            if mdx or mdy:
                self.x, self.y = move_with_collision(world, self.x, self.y,
                                                     mdx * speed * dt, mdy * speed * dt, self.radius)
                if self.lock_target is None:
                    self.fx, self.fy = mdx, mdy
                self.walking = True
            self.state = ('run' if self.sprinting else 'walk') if self.walking else 'idle'
        elif self.state == 'roll':
            self.timer -= dt
            sp = ROLL_SPEED * (0.5 + 0.5 * (self.timer / ROLL_TIME))
            self.x, self.y = move_with_collision(world, self.x, self.y,
                                                 self.roll_dx * sp * dt, self.roll_dy * sp * dt, self.radius)
            if self.timer <= 0:
                self.state = 'idle'
        elif self.state == 'attack':
            self.atk_elapsed += dt
            k, wu, act, rec = self._step_def()
            # small forward drift during the strike
            if wu < self.atk_elapsed < wu + act:
                self.x, self.y = move_with_collision(world, self.x, self.y,
                                                     self.fx * 2.2 * dt, self.fy * 2.2 * dt, self.radius)
            if self.atk_elapsed >= wu + act + rec:
                if self.atk_queued and not self.atk_heavy and self.atk_step + 1 < len(self.weapon['combo']):
                    cost = self.weapon['stamina'] * 0.8
                    if self.stamina >= cost:
                        self.atk_step += 1
                        self.atk_elapsed = 0.0
                        self.atk_hit_done = False
                        self.atk_queued = False
                        self._face_target()
                        self._spend(cost)
                    else:
                        self.state = 'idle'
                else:
                    self.state = 'idle'
        elif self.state in ('parry', 'stim'):
            self.timer -= dt
            if self.state == 'stim' and self.timer <= 0:
                self.stims -= 1
                self.hp = min(self.max_hp, self.hp + STIM_HEAL)
            if self.timer <= 0:
                self.state = 'idle'

        if self.lock_target is not None:
            t = self.lock_target
            if not getattr(t, 'alive', False) or dist(self.x, self.y, t.x, t.y) > 26:
                self.lock_target = None
            elif self.state in ('idle', 'walk', 'run'):
                self.fx, self.fy = norm(t.x - self.x, t.y - self.y)

        self.stam_delay = max(0, self.stam_delay - dt)
        if self.stam_delay <= 0 and self.state != 'roll':
            self.stamina = min(self.max_stamina, self.stamina + STAMINA_REGEN * dt)

    # ---- combat ----
    def attack_active(self):
        if self.state != 'attack' or self.atk_hit_done:
            return False
        k, wu, act, rec = self._step_def()
        return wu <= self.atk_elapsed <= wu + act

    def attack_damage(self):
        w = self.weapon
        base = w['dmg']
        if self.atk_heavy:
            base *= w['heavy'][4]
        return base * self.dmg_mult

    def in_arc(self, ex, ey, extra=0.0):
        w = self.weapon
        d = dist(self.x, self.y, ex, ey)
        if d > w['reach'] + extra:
            return False
        if d < 0.8:
            return True
        ang = math.atan2(ey - self.y, ex - self.x)
        fang = math.atan2(self.fy, self.fx)
        diff = (ang - fang + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) < w['arc'] / 2

    def take_damage(self, dmg, sx=0.0, sy=0.0):
        if not self.alive:
            return 'dead'
        if self.parry_active > 0:
            self.parry_success_t = 0.9
            self.parry_active = 0
            self.state = 'idle'
            self.stamina = min(self.max_stamina, self.stamina + 25)
            return 'parried'
        if self.iframes > 0 or self.hit_iframes > 0:
            return 'dodged'
        self.hp -= dmg
        self.hit_iframes = INVULN_AFTER_HIT
        if self.hp <= 0:
            self.hp = 0
            self.state = 'dead'
            self.state_t = 0.0
            self.deaths += 1
            return 'dead'
        return 'hit'

    def rest(self):
        self.hp = self.max_hp
        self.stamina = self.max_stamina
        self.stims = self.stim_max

    def respawn(self, x, y):
        self.x, self.y = x, y
        self.state = 'idle'
        self.lock_target = None
        self.trail.clear()
        self.rest()

    # ---- presentation ----
    def anim(self):
        if self.state == 'attack':
            return 'attack'
        if self.state == 'run':
            return 'run'
        if self.state == 'walk':
            return 'walk'
        if self.state == 'roll':
            return 'roll'
        if self.state == 'parry':
            return 'parry'
        if self.state == 'stim':
            return 'drink'
        if self.state == 'dead':
            return 'dead'
        return 'idle'

    def anim_time(self):
        if self.state in ('roll', 'parry', 'stim', 'dead'):
            if self.state == 'roll':
                return 1.0 - self.timer / ROLL_TIME
            if self.state == 'dead':
                return self.state_t
            total = (PARRY_WINDOW + PARRY_RECOVER) if self.state == 'parry' else STIM_TIME
            return 1.0 - self.timer / total
        return self.anim_t

    def attack_info(self):
        if self.state == 'attack':
            return (self.attack_kind(), self.attack_progress(), self.atk_step)
        return None
