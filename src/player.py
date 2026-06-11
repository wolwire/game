"""The player: Calle Wren. Souls-like state machine — movement, sprint,
dodge rolls with i-frames, light/heavy attacks, parry, stims, stats."""
import math
from src.constants import *
from src.entity import move_with_collision, dist, norm
from src.iso import screen_dir_to_world, facing_octant


class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 0.3
        # stats
        self.level = 1
        self.vigor = 5
        self.endurance = 5
        self.strength = 5
        self.shards = 0
        self.hp = self.max_hp
        self.stamina = self.max_stamina
        self.stims = STIM_CHARGES
        # state
        self.state = 'idle'        # idle walk roll attack heavy parry stim dead
        self.timer = 0.0
        self.fx, self.fy = 1.0, 0.0   # facing (world space)
        self.move_dx, self.move_dy = 0.0, 0.0
        self.roll_dx, self.roll_dy = 0.0, 0.0
        self.iframes = 0.0
        self.hit_iframes = 0.0
        self.stam_delay = 0.0
        self.attack_hit_done = False
        self.parry_active = 0.0
        self.parry_success_t = 0.0
        self.lock_target = None
        self.anim_t = 0.0
        self.walking = False
        self.kills = 0
        self.deaths = 0

    # ---- derived stats ----
    @property
    def max_hp(self):
        return PLAYER_BASE_HP + self.vigor * VIGOR_HP

    @property
    def max_stamina(self):
        return PLAYER_BASE_STAMINA + self.endurance * ENDURANCE_STAM

    @property
    def dmg_mult(self):
        return 1.0 + self.strength * STRENGTH_DMG

    @property
    def alive(self):
        return self.state != 'dead'

    def busy(self):
        return self.state in ('roll', 'attack', 'heavy', 'parry', 'stim')

    # ---- inputs ----
    def try_roll(self):
        if self.busy() or self.stamina < ROLL_COST or not self.alive:
            return
        dx, dy = self.move_dx, self.move_dy
        if abs(dx) < 0.01 and abs(dy) < 0.01:
            dx, dy = self.fx, self.fy
        self.roll_dx, self.roll_dy = norm(dx, dy)
        self.state = 'roll'
        self.timer = ROLL_TIME
        self.iframes = ROLL_IFRAMES
        self._spend(ROLL_COST)

    def try_attack(self, heavy=False):
        if self.busy() or not self.alive:
            return
        cost = HEAVY_COST if heavy else LIGHT_COST
        if self.stamina < cost:
            return
        if self.lock_target is not None and getattr(self.lock_target, 'alive', False):
            self.fx, self.fy = norm(self.lock_target.x - self.x, self.lock_target.y - self.y)
        elif abs(self.move_dx) > 0.01 or abs(self.move_dy) > 0.01:
            self.fx, self.fy = self.move_dx, self.move_dy
        self.state = 'heavy' if heavy else 'attack'
        self.timer = (HEAVY_WINDUP + HEAVY_RECOVER) if heavy else (0.12 + LIGHT_RECOVER)
        self.attack_hit_done = False
        self._spend(cost)

    def try_parry(self):
        if self.busy() or not self.alive or self.stamina < 10:
            return
        self.state = 'parry'
        self.timer = PARRY_WINDOW + PARRY_RECOVER
        self.parry_active = PARRY_WINDOW
        self._spend(10)

    def try_stim(self):
        if self.busy() or not self.alive or self.stims <= 0 or self.hp >= self.max_hp:
            return
        self.state = 'stim'
        self.timer = STIM_TIME

    def _spend(self, amt):
        self.stamina = max(0, self.stamina - amt)
        self.stam_delay = STAMINA_REGEN_DELAY

    # ---- per-frame ----
    def update(self, dt, world, move_screen, sprinting):
        self.anim_t += dt
        self.iframes = max(0, self.iframes - dt)
        self.hit_iframes = max(0, self.hit_iframes - dt)
        self.parry_active = max(0, self.parry_active - dt)
        self.parry_success_t = max(0, self.parry_success_t - dt)
        if not self.alive:
            return

        mdx, mdy = screen_dir_to_world(*move_screen) if any(move_screen) else (0.0, 0.0)
        self.move_dx, self.move_dy = mdx, mdy
        self.walking = False

        if self.state in ('idle', 'walk'):
            speed = PLAYER_SPEED
            if sprinting and (mdx or mdy) and self.stamina > 1:
                speed *= PLAYER_SPRINT_MULT
                self.stamina = max(0, self.stamina - SPRINT_DRAIN * dt)
                self.stam_delay = max(self.stam_delay, 0.2)
            if mdx or mdy:
                self.x, self.y = move_with_collision(world, self.x, self.y,
                                                     mdx * speed * dt, mdy * speed * dt, self.radius)
                if self.lock_target is None:
                    self.fx, self.fy = mdx, mdy
                self.walking = True
            self.state = 'walk' if self.walking else 'idle'
        elif self.state == 'roll':
            self.timer -= dt
            sp = ROLL_SPEED * (0.55 + 0.45 * (self.timer / ROLL_TIME))
            self.x, self.y = move_with_collision(world, self.x, self.y,
                                                 self.roll_dx * sp * dt, self.roll_dy * sp * dt, self.radius)
            if self.timer <= 0:
                self.state = 'idle'
        elif self.state in ('attack', 'heavy', 'parry', 'stim'):
            self.timer -= dt
            if self.state == 'stim' and self.timer <= 0:
                self.stims -= 1
                self.hp = min(self.max_hp, self.hp + STIM_HEAL)
            if self.timer <= 0:
                self.state = 'idle'

        # lock-on facing
        if self.lock_target is not None:
            t = self.lock_target
            if not getattr(t, 'alive', False) or dist(self.x, self.y, t.x, t.y) > 13:
                self.lock_target = None
            elif self.state in ('idle', 'walk'):
                self.fx, self.fy = norm(t.x - self.x, t.y - self.y)

        # stamina regen
        self.stam_delay = max(0, self.stam_delay - dt)
        if self.stam_delay <= 0 and self.state not in ('roll',):
            self.stamina = min(self.max_stamina, self.stamina + STAMINA_REGEN * dt)

    def attack_active(self):
        """True on the active damage frame of the current swing."""
        if self.state == 'attack':
            return not self.attack_hit_done and self.timer <= LIGHT_RECOVER
        if self.state == 'heavy':
            return not self.attack_hit_done and self.timer <= HEAVY_RECOVER
        return False

    def attack_damage(self):
        base = HEAVY_DMG if self.state == 'heavy' else LIGHT_DMG
        return base * self.dmg_mult

    def in_arc(self, ex, ey, extra=0.0):
        d = dist(self.x, self.y, ex, ey)
        if d > ATTACK_RANGE + extra:
            return False
        if d < 0.4:
            return True
        ang = math.atan2(ey - self.y, ex - self.x)
        fang = math.atan2(self.fy, self.fx)
        diff = (ang - fang + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) < ATTACK_ARC / 2

    def take_damage(self, dmg, sx=0.0, sy=0.0):
        """Returns 'parried' | 'dodged' | 'hit' | 'dead'."""
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
            self.deaths += 1
            return 'dead'
        return 'hit'

    def rest(self):
        self.hp = self.max_hp
        self.stamina = self.max_stamina
        self.stims = STIM_CHARGES

    def respawn(self, x, y):
        self.x, self.y = x, y
        self.state = 'idle'
        self.lock_target = None
        self.rest()

    def octant(self):
        return facing_octant(self.fx, self.fy)

    def anim_frame(self):
        if self.state in ('attack', 'heavy'):
            return 3
        if self.walking or self.state == 'roll':
            return 1 if int(self.anim_t * 7) % 2 == 0 else 2
        return 0
