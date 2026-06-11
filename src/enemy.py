"""Regular enemies of the Stillness. Distances are in fine tiles."""
import math
import random
from src.entity import move_with_collision, dist, norm, Projectile

ENEMY_STATS = {
    #          hp  speed dmg  windup recover sight range shards style    weapon
    'husk':    (46, 3.0, 14, 0.62, 0.7, 14.0, 2.0, 30, 'husk', None),
    'stalker': (36, 6.4, 18, 0.32, 0.5, 18.0, 2.2, 48, 'stalker', 'machete'),
    'riot':    (95, 2.6, 24, 0.75, 0.9, 14.0, 2.4, 70, 'riot', 'baton'),
    'feral':   (30, 8.0, 12, 0.30, 0.8, 20.0, 2.0, 38, 'feral', None),
    'drone':   (26, 4.8, 13, 0.9, 1.6, 22.0, 13.0, 44, 'drone', None),
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
        self.radius = 0.6
        self.state = 'idle'      # idle wander chase windup recover stagger
        self.timer = random.uniform(0.5, 2.0)
        self.fx, self.fy = 1.0, 0.0
        self.wander_to = (x, y)
        self.anim_t = random.uniform(0, 10)
        self.hit_flash = 0.0
        self.alive = True
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
                if self.kind == 'stalker' and d < 7 and random.random() < 0.5:
                    px, py = norm(player.x - self.x, player.y - self.y)
                    sx_, sy_ = -py * self.strafe_dir, px * self.strafe_dir
                    self._step(dt, world, self.x + px * 2 + sx_ * 2,
                               self.y + py * 2 + sy_ * 2, self.speed)
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
                if dist(self.x, self.y, player.x, player.y) < self.range + 0.5:
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
        elif d < self.range - 5:
            self._step(dt, world, 2 * self.x - player.x, 2 * self.y - player.y, self.speed)
        else:
            # orbit
            px, py = norm(player.x - self.x, player.y - self.y)
            self._step(dt, world, self.x - py * self.strafe_dir * 3,
                       self.y + px * self.strafe_dir * 3, self.speed * 0.6)
        self.timer -= dt
        if self.timer <= 0 and d < self.sight:
            vx, vy = norm(player.x - self.x, player.y - self.y)
            projectiles.append(Projectile(self.x, self.y, vx * 11, vy * 11,
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
            if dist(self.x, self.y, *self.wander_to) > 0.6:
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
            particles.death_burst(self.x, self.y)
            particles.blood_decal(self.x, self.y)
            return self.shards
        return 0

    # ---- presentation ----
    def anim(self):
        if self.state == 'windup':
            return 'windup'
        if self.state == 'recover':
            return 'attack'
        if self.state == 'stagger':
            return 'stagger'
        if self.state in ('chase',):
            return 'run' if self.kind in ('stalker', 'feral') else 'walk'
        if self.state == 'wander':
            return 'walk'
        return 'idle'

    def attack_info(self):
        """Map windup/recover to a puppet attack phase."""
        kind = 'thrust' if self.kind == 'stalker' else 'swing'
        if self.state == 'windup':
            p = 0.32 * (1.0 - self.timer / max(0.01, self.windup))
            return (kind, p, 0)
        if self.state == 'recover':
            p = 0.32 + 0.68 * (1.0 - self.timer / max(0.01, self.recover))
            return (kind, min(1.0, p * 1.4), 0)
        return None
