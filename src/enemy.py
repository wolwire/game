"""Regular enemies of the Stillness. Distances are in fine tiles."""
import math
import random
from src.entity import move_with_collision, dist, norm, Projectile

ENEMY_STATS = {
    #          hp  speed dmg  windup recover sight range shards style    weapon
    'husk':    (46, 1.5, 14, 0.62, 0.7, 7.0, 1.15, 30, 'husk', None),
    'stalker': (36, 3.2, 18, 0.32, 0.5, 9.0, 1.25, 48, 'stalker', 'machete'),
    'riot':    (95, 1.3, 24, 0.75, 0.9, 7.0, 1.35, 70, 'riot', 'baton'),
    'feral':   (30, 4.0, 12, 0.30, 0.8, 10.0, 1.15, 38, 'feral', None),
    'drone':   (26, 2.4, 13, 0.9, 1.6, 11.0, 6.5, 44, 'drone', None),
}


class Enemy:
    def __init__(self, kind, x, y, patrol_r=6.0):
        (self.max_hp, self.speed, self.dmg, self.windup, self.recover,
         self.sight, self.range, self.shards, self.style, self.weapon_key) = ENEMY_STATS[kind]
        self.kind = kind
        self.x, self.y = x, y
        self.home = (x, y)
        self.patrol_r = patrol_r
        self.hp = self.max_hp
        self.radius = 0.32
        self.state = 'idle'      # idle wander chase windup recover stagger
        self.timer = random.uniform(0.5, 2.0)
        self.fx, self.fy = 1.0, 0.0
        self.wander_to = (x, y)
        self.anim_t = random.uniform(0, 10)
        self.hit_flash = 0.0
        self.alive = True
        self.death_clock = None
        self.aggro = False
        self.strafe_dir = random.choice((-1, 1))

    def update(self, dt, world, player, projectiles, particles):
        if not self.alive:
            return
        self.anim_t += dt
        self.hit_flash = max(0, self.hit_flash - dt)
        d = dist(self.x, self.y, player.x, player.y)

        if not self.aggro:
            if d < self.sight and player.alive:
                self.aggro = True
                self.state = 'chase'
                particles.alert(self.x, self.y)
            else:
                self._wander(dt, world)
                return

        if d > self.sight * 2.4 or not player.alive:
            self.aggro = False
            self.state = 'idle'
            self.timer = 1.0
            return

        if self.state == 'chase':
            if self.kind == 'drone':
                self._drone_logic(dt, world, player, projectiles, d)
                return
            if d > self.range * 0.85:
                # stalkers strafe in, others walk straight
                if self.kind == 'stalker' and d < 3.5 and random.random() < 0.5:
                    px, py = norm(player.x - self.x, player.y - self.y)
                    sx_, sy_ = -py * self.strafe_dir, px * self.strafe_dir
                    self._step(dt, world, self.x + px + sx_,
                               self.y + py + sy_, self.speed)
                else:
                    self._step(dt, world, player.x, player.y, self.speed)
            else:
                self.state = 'windup'
                self.timer = self.windup
                self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
        elif self.state == 'windup':
            self.timer -= dt
            if self.kind == 'feral':
                self._step(dt, world, player.x, player.y, self.speed * 1.5)
            if self.timer <= 0:
                if dist(self.x, self.y, player.x, player.y) < self.range + 0.3:
                    res = player.take_damage(self.dmg, player.x - self.x, player.y - self.y)
                    if res == 'parried':
                        self.state = 'stagger'
                        self.timer = 1.6
                        particles.parry_spark(self.x, self.y)
                        return
                    elif res == 'hit':
                        particles.blood(player.x, player.y)
                self.state = 'recover'
                self.timer = self.recover
                if self.kind == 'stalker':
                    self.strafe_dir = -self.strafe_dir
        elif self.state in ('recover', 'stagger'):
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'chase'

    def _drone_logic(self, dt, world, player, projectiles, d):
        if d > self.range:
            self._step(dt, world, player.x, player.y, self.speed)
        elif d < self.range - 2.5:
            self._step(dt, world, 2 * self.x - player.x, 2 * self.y - player.y, self.speed)
        else:
            # orbit
            px, py = norm(player.x - self.x, player.y - self.y)
            self._step(dt, world, self.x - py * self.strafe_dir * 1.5,
                       self.y + px * self.strafe_dir * 1.5, self.speed * 0.6)
        self.timer -= dt
        if self.timer <= 0 and d < self.sight:
            vx, vy = norm(player.x - self.x, player.y - self.y)
            projectiles.append(Projectile(self.x, self.y, vx * 5.5, vy * 5.5,
                                          self.dmg, (255, 110, 90)))
            self.timer = self.windup + self.recover
            self.state = 'windup'   # purely for the firing flash

    def _step(self, dt, world, tx, ty, speed):
        dx, dy = norm(tx - self.x, ty - self.y)
        self.fx, self.fy = dx, dy
        self.x, self.y = move_with_collision(world, self.x, self.y,
                                             dx * speed * dt, dy * speed * dt, self.radius)

    def _wander(self, dt, world):
        self.timer -= dt
        if self.timer <= 0:
            hx, hy = self.home
            self.wander_to = (hx + random.uniform(-self.patrol_r, self.patrol_r),
                              hy + random.uniform(-self.patrol_r, self.patrol_r))
            self.timer = random.uniform(2.0, 5.0)
            self.state = 'wander'
        if self.state == 'wander':
            if dist(self.x, self.y, *self.wander_to) > 0.3:
                self._step(dt, world, *self.wander_to, self.speed * 0.35)
            else:
                self.state = 'idle'

    def take_damage(self, dmg, from_x, from_y, particles, stagger=1.0):
        if not self.alive:
            return 0
        if self.kind == 'riot' and self.state not in ('windup', 'stagger'):
            ang = math.atan2(from_y - self.y, from_x - self.x)
            fang = math.atan2(self.fy, self.fx)
            diff = abs((ang - fang + math.pi) % (2 * math.pi) - math.pi)
            if diff < 1.2 and stagger < 2.0:
                dmg *= 0.25
                particles.block_spark(self.x, self.y)
        if self.state == 'stagger':
            dmg *= 2.2
        self.hp -= dmg
        self.hit_flash = 0.18
        self.aggro = True
        particles.hit(self.x, self.y)
        particles.damage_number(self.x, self.y, int(dmg))
        if stagger >= 1.7 and self.alive and self.state != 'stagger':
            self.state = 'stagger'
            self.timer = max(self.timer, 0.9)
        if self.hp <= 0:
            self.alive = False
            self.death_clock = 0.0
            particles.death_burst(self.x, self.y)
            particles.blood_decal(self.x, self.y)
            return self.shards
        return 0

    # ---- presentation: (anim_name, t_or_progress, mode) for sprites ----
    def anim_state(self):
        if not self.alive:
            return ('die', self.death_clock or 0.0, 'time')
        if self.state == 'windup':
            nm = 'shoot' if self.kind == 'drone' else 'swing'
            return (nm, 0.45 * (1.0 - self.timer / max(0.01, self.windup)), 'once')
        if self.state == 'recover':
            return ('swing', 0.5 + 0.5 * (1.0 - self.timer / max(0.01, self.recover)), 'once')
        if self.state == 'stagger':
            return ('hit', min(1.0, (1.6 - self.timer) * 2), 'once')
        if self.state in ('chase', 'wander'):
            return ('run', self.anim_t, 'time')
        return ('stance', self.anim_t, 'time')
