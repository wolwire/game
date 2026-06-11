"""Regular enemies of the Stillness: husks, stalkers, riot husks,
feral dogs and security drones."""
import math
import random
from src.entity import move_with_collision, dist, norm, Projectile
from src.iso import facing_octant

ENEMY_STATS = {
    #          hp  speed dmg  windup recover sight range shards style
    'husk':    (46, 1.5, 14, 0.65, 0.7, 7.0, 1.15, 30, 'husk'),
    'stalker': (36, 3.2, 18, 0.34, 0.5, 9.0, 1.25, 48, 'stalker'),
    'riot':    (95, 1.3, 24, 0.8, 0.9, 7.0, 1.35, 70, 'riot'),
    'feral':   (30, 4.0, 12, 0.30, 0.8, 10.0, 1.1, 38, 'feral'),
    'drone':   (26, 2.4, 13, 0.9, 1.6, 11.0, 6.5, 44, 'drone'),
}


class Enemy:
    def __init__(self, kind, x, y, patrol_r=3.0):
        (self.max_hp, self.speed, self.dmg, self.windup, self.recover,
         self.sight, self.range, self.shards, self.style) = ENEMY_STATS[kind]
        self.kind = kind
        self.x, self.y = x, y
        self.home = (x, y)
        self.patrol_r = patrol_r
        self.hp = self.max_hp
        self.radius = 0.32
        self.state = 'idle'      # idle wander chase windup recover stagger
        self.timer = random.uniform(0.5, 2.0)
        self.fx, self.fy = 1.0, 0.0
        self.target = None
        self.wander_to = (x, y)
        self.anim_t = random.uniform(0, 10)
        self.hit_flash = 0.0
        self.alive = True
        self.aggro = False

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
            else:
                self._wander(dt, world)
                return

        # leash back home if the player escapes far away
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
                self._step_towards(dt, world, player.x, player.y, self.speed)
            else:
                self.state = 'windup'
                self.timer = self.windup
                self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
        elif self.state == 'windup':
            self.timer -= dt
            if self.kind == 'feral':   # dogs lunge through the windup
                self._step_towards(dt, world, player.x, player.y, self.speed * 1.4)
            if self.timer <= 0:
                if dist(self.x, self.y, player.x, player.y) < self.range + 0.25:
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
        elif self.state in ('recover', 'stagger'):
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'chase'

    def _drone_logic(self, dt, world, player, projectiles, d):
        # keep a band of distance, fire bolts
        if d > self.range:
            self._step_towards(dt, world, player.x, player.y, self.speed)
        elif d < self.range - 2.5:
            self._step_towards(dt, world, 2 * self.x - player.x, 2 * self.y - player.y, self.speed)
        self.timer -= dt
        if self.timer <= 0 and d < self.sight:
            vx, vy = norm(player.x - self.x, player.y - self.y)
            projectiles.append(Projectile(self.x, self.y, vx * 5.5, vy * 5.5,
                                          self.dmg, (255, 110, 90)))
            self.timer = self.windup + self.recover

    def _step_towards(self, dt, world, tx, ty, speed):
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
                self._step_towards(dt, world, *self.wander_to, self.speed * 0.45)
            else:
                self.state = 'idle'

    def take_damage(self, dmg, from_x, from_y, particles):
        if not self.alive:
            return 0
        # riot husks block most frontal damage unless mid-swing
        if self.kind == 'riot' and self.state not in ('windup', 'stagger'):
            ang = math.atan2(from_y - self.y, from_x - self.x)
            fang = math.atan2(self.fy, self.fx)
            diff = abs((ang - fang + math.pi) % (2 * math.pi) - math.pi)
            if diff < 1.2:
                dmg *= 0.25
                particles.block_spark(self.x, self.y)
        if self.state == 'stagger':
            dmg *= 2.2   # riposte
        self.hp -= dmg
        self.hit_flash = 0.15
        self.aggro = True
        particles.hit(self.x, self.y)
        if self.hp <= 0:
            self.alive = False
            particles.death_burst(self.x, self.y)
            return self.shards
        return 0

    def octant(self):
        return facing_octant(self.fx, self.fy)

    def anim_frame(self):
        if self.state == 'windup':
            return 3
        if self.state in ('chase', 'wander'):
            return 1 if int(self.anim_t * 6) % 2 == 0 else 2
        return 0
