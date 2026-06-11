"""Bosses of Meridian City — telegraphed attacks, second phases.
Distances in fine tiles (2x the old coarse scale)."""
import math
import random
from src.entity import move_with_collision, dist, norm, Projectile

BOSS_STATS = {
    #            hp   speed contact_dmg shards style
    'warden':    (640, 2.1, 30, 900, 'warden'),
    'chorister': (520, 1.4, 22, 850, 'chorister'),
    'hound':     (400, 4.6, 18, 600, 'hound'),
    'archivist': (860, 2.2, 26, 0, 'archivist'),
}


class Telegraph:
    __slots__ = ('x', 'y', 'r', 't', 'dmg', 'total')

    def __init__(self, x, y, r, t, dmg):
        self.x, self.y, self.r, self.t, self.dmg = x, y, r, t, dmg
        self.total = t


class Boss:
    def __init__(self, kind, x, y, arena_center, arena_r):
        self.kind = kind
        self.max_hp, self.speed, self.dmg, self.shards, self.style = BOSS_STATS[kind]
        self.hp = self.max_hp
        self.x, self.y = x, y
        self.cx, self.cy = arena_center
        self.arena_r = arena_r
        self.radius = 0.55 if kind != 'hound' else 0.45
        self.fx, self.fy = 0.0, 1.0
        self.alive = True
        self.active = False
        self.state = 'idle'
        self.timer = 0.0
        self.combo = 0
        self.anim_t = 0.0
        self.atk_t = 0.0       # progress clock for the current swing
        self.atk_total = 1.0
        self.hit_flash = 0.0
        self.phase2 = False
        self.telegraphs = []
        self.charge_dir = (0.0, 0.0)
        self.weapon_key = 'sledge' if kind == 'warden' else None
        self.death_clock = None

    # ------------------------------------------------------------------
    def update(self, dt, world, player, projectiles, particles, enemies):
        if not self.alive:
            return
        self.anim_t += dt
        self.atk_t += dt
        self.hit_flash = max(0, self.hit_flash - dt)
        if not self.active:
            return
        if not self.phase2 and self.hp < self.max_hp * 0.5:
            self.phase2 = True
            particles.shockwave(self.x, self.y)
            self.state = 'recover'
            self.timer = 0.8

        for tg in self.telegraphs[:]:
            tg.t -= dt
            if tg.t <= 0:
                self.telegraphs.remove(tg)
                particles.slam(tg.x, tg.y, tg.r)
                if dist(player.x, player.y, tg.x, tg.y) < tg.r + 0.2:
                    if player.take_damage(tg.dmg, player.x - tg.x, player.y - tg.y) == 'hit':
                        particles.blood(player.x, player.y)

        getattr(self, '_ai_' + self.kind)(dt, world, player, projectiles, particles, enemies)

        d = dist(self.x, self.y, self.cx, self.cy)
        if d > self.arena_r:
            nx, ny = norm(self.cx - self.x, self.cy - self.y)
            self.x += nx * (d - self.arena_r)
            self.y += ny * (d - self.arena_r)

    def _begin(self, state, t):
        self.state = state
        self.timer = t
        self.atk_t = 0.0
        self.atk_total = t

    def _step(self, dt, world, tx, ty, speed):
        dx, dy = norm(tx - self.x, ty - self.y)
        self.fx, self.fy = dx, dy
        self.x, self.y = move_with_collision(world, self.x, self.y,
                                             dx * speed * dt, dy * speed * dt, self.radius)

    def _melee(self, player, particles, dmg, reach):
        if dist(self.x, self.y, player.x, player.y) < reach:
            res = player.take_damage(dmg, player.x - self.x, player.y - self.y)
            if res == 'parried':
                self._begin('stagger', 2.0)
                particles.parry_spark(self.x, self.y)
                return True
            if res == 'hit':
                particles.blood(player.x, player.y)
        return False

    # ----------------------------------------------------------- warden ---
    def _ai_warden(self, dt, world, player, projectiles, particles, enemies):
        sp = self.speed * (1.35 if self.phase2 else 1.0)
        if self.state == 'idle':
            self.state = 'chase'
        elif self.state == 'chase':
            d = dist(self.x, self.y, player.x, player.y)
            if d > 1.7:
                self._step(dt, world, player.x, player.y, sp)
                if d > 5 and random.random() < (0.012 if not self.phase2 else 0.02):
                    self._begin('charge_wind', 0.55)
                    self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
            else:
                if random.random() < 0.5:
                    self._begin('windup', 0.55 if not self.phase2 else 0.42)
                    self.combo = 0
                else:
                    self._begin('slam_wind', 0.8)
                    r = 2.6 if not self.phase2 else 3.2
                    self.telegraphs.append(Telegraph(player.x, player.y, r, 1.0, 34))
        elif self.state == 'windup':
            self.timer -= dt
            self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
            if self.timer <= 0:
                if self._melee(player, particles, self.dmg, 2.0):
                    return
                self.combo += 1
                if self.combo < (3 if self.phase2 else 2):
                    self._begin('windup', 0.38)
                else:
                    self._begin('recover', 1.0)
        elif self.state == 'charge_wind':
            self.timer -= dt
            if self.timer <= 0:
                self.charge_dir = norm(player.x - self.x, player.y - self.y)
                self._begin('charge', 0.85)
        elif self.state == 'charge':
            self.timer -= dt
            self.x, self.y = move_with_collision(world, self.x, self.y,
                                                 self.charge_dir[0] * 9 * dt,
                                                 self.charge_dir[1] * 9 * dt, self.radius)
            if dist(self.x, self.y, player.x, player.y) < 1.2:
                self._melee(player, particles, self.dmg + 8, 1.4)
                self.timer = 0
            if self.timer <= 0:
                self._begin('recover', 0.9)
        elif self.state == 'slam_wind':
            self.timer -= dt
            if self.timer <= 0:
                self._begin('recover', 1.1)
                if self.phase2:
                    for i in range(8):
                        a = i * math.pi / 4
                        projectiles.append(Projectile(self.x, self.y,
                                                      math.cos(a) * 4.5, math.sin(a) * 4.5,
                                                      16, (255, 170, 60), ttl=1.4))
        elif self.state in ('recover', 'stagger'):
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'chase'

    # -------------------------------------------------------- chorister ---
    def _ai_chorister(self, dt, world, player, projectiles, particles, enemies):
        d = dist(self.x, self.y, player.x, player.y)
        if self.state == 'idle':
            self.state = 'chase'
        elif self.state == 'chase':
            if d < 3.0:
                self._step(dt, world, 2 * self.x - player.x, 2 * self.y - player.y, self.speed)
            elif d > 6.0:
                self._step(dt, world, player.x, player.y, self.speed)
            else:
                self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
            self.timer -= dt
            if self.timer <= 0:
                r = random.random()
                if d < 3.2:
                    self._begin('scream_wind', 0.7)
                    self.telegraphs.append(Telegraph(self.x, self.y, 3.4, 0.7, 30))
                elif r < 0.55:
                    self._begin('burst', 0.5)
                    self.combo = 3 if not self.phase2 else 5
                else:
                    self._begin('summon', 1.0)
        elif self.state == 'burst':
            self.timer -= dt
            if self.timer <= 0 and self.combo > 0:
                self.combo -= 1
                n = 10 if self.phase2 else 7
                off = random.random() * math.pi
                for i in range(n):
                    a = off + i * 2 * math.pi / n
                    projectiles.append(Projectile(self.x, self.y,
                                                  math.cos(a) * 3.6, math.sin(a) * 3.6,
                                                  15, (200, 130, 255), ttl=2.6))
                particles.note(self.x, self.y)
                self.timer = 0.55
                if self.combo == 0:
                    self._begin('recover', 1.4)
        elif self.state == 'scream_wind':
            self.timer -= dt
            if self.timer <= 0:
                self._begin('recover', 1.0)
        elif self.state == 'summon':
            self.timer -= dt
            if self.timer <= 0:
                from src.enemy import Enemy
                living = sum(1 for e in enemies if e.alive and getattr(e, 'summoned', False))
                if living < 3:
                    for _ in range(2):
                        a = random.random() * 2 * math.pi
                        e = Enemy('husk', self.cx + math.cos(a) * 4, self.cy + math.sin(a) * 4)
                        e.aggro = True
                        e.summoned = True
                        enemies.append(e)
                        particles.note(e.x, e.y)
                self._begin('recover', 1.2)
        elif self.state in ('recover', 'stagger'):
            self.timer -= dt
            if self.timer <= 0:
                self.state = 'chase'
                self.timer = random.uniform(0.8, 1.6)

    # ------------------------------------------------------------ hound ---
    def _ai_hound(self, dt, world, player, projectiles, particles, enemies):
        d = dist(self.x, self.y, player.x, player.y)
        sp = self.speed * (1.2 if self.phase2 else 1.0)
        if self.state == 'idle':
            self._begin('circle', random.uniform(0.8, 1.6))
        elif self.state == 'circle':
            ang = math.atan2(self.y - player.y, self.x - player.x) + 1.5 * dt
            tx = player.x + math.cos(ang) * 3.2
            ty = player.y + math.sin(ang) * 3.2
            self._step(dt, world, tx, ty, sp * 0.8)
            self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
            self.timer -= dt
            if self.timer <= 0:
                self._begin('lunge_wind', 0.3)
                self.combo = 3 if self.phase2 else 1
        elif self.state == 'lunge_wind':
            self.timer -= dt
            self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
            if self.timer <= 0:
                self.charge_dir = (self.fx, self.fy)
                self._begin('lunge', 0.42)
        elif self.state == 'lunge':
            self.timer -= dt
            self.x, self.y = move_with_collision(world, self.x, self.y,
                                                 self.charge_dir[0] * 10 * dt,
                                                 self.charge_dir[1] * 10 * dt, self.radius)
            if dist(self.x, self.y, player.x, player.y) < 1.0:
                self._melee(player, particles, self.dmg, 1.2)
                self.timer = 0
            if self.timer <= 0:
                self.combo -= 1
                if self.combo > 0:
                    self._begin('lunge_wind', 0.28)
                else:
                    self._begin('recover', 1.1)
        elif self.state in ('recover', 'stagger'):
            self.timer -= dt
            if self.timer <= 0:
                self._begin('circle', random.uniform(0.9, 1.8))

    # -------------------------------------------------------- archivist ---
    def _ai_archivist(self, dt, world, player, projectiles, particles, enemies):
        d = dist(self.x, self.y, player.x, player.y)
        if self.state == 'idle':
            self.state = 'chase'
        elif self.state == 'chase':
            if d > 2.0:
                self._step(dt, world, player.x, player.y, self.speed)
            else:
                self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
            self.timer -= dt
            if self.timer <= 0:
                r = random.random()
                if d < 2.4:
                    self._begin('windup', 0.4)
                    self.combo = 0
                elif r < 0.3:
                    self._begin('teleport', 0.5)
                elif r < 0.62:
                    self._begin('fan', 0.45)
                    self.combo = 3
                else:
                    n = 4 if self.phase2 else 3
                    for i in range(n):
                        self.telegraphs.append(Telegraph(
                            player.x + random.uniform(-1.5, 1.5) * i,
                            player.y + random.uniform(-1.5, 1.5) * i,
                            1.7, 0.9 + i * 0.35, 26))
                    self._begin('recover', 1.2)
        elif self.state == 'windup':
            self.timer -= dt
            self.fx, self.fy = norm(player.x - self.x, player.y - self.y)
            if self.timer <= 0:
                if self._melee(player, particles, self.dmg, 2.0):
                    return
                self.combo += 1
                if self.combo < 2:
                    self._begin('windup', 0.34)
                else:
                    self._begin('recover', 0.9)
        elif self.state == 'teleport':
            self.timer -= dt
            if self.timer <= 0:
                particles.static_burst(self.x, self.y)
                a = random.random() * 2 * math.pi
                r = random.uniform(2.0, 3.4)
                self.x = max(self.cx - self.arena_r, min(self.cx + self.arena_r, player.x + math.cos(a) * r))
                self.y = max(self.cy - self.arena_r, min(self.cy + self.arena_r, player.y + math.sin(a) * r))
                particles.static_burst(self.x, self.y)
                self._begin('fan', 0.3)
                self.combo = 2
        elif self.state == 'fan':
            self.timer -= dt
            if self.timer <= 0 and self.combo > 0:
                self.combo -= 1
                base = math.atan2(player.y - self.y, player.x - self.x)
                spread = 5 if not self.phase2 else 7
                for i in range(spread):
                    a = base + (i - spread // 2) * 0.22
                    projectiles.append(Projectile(self.x, self.y,
                                                  math.cos(a) * 5.0, math.sin(a) * 5.0,
                                                  17, (120, 220, 255), ttl=2.2))
                self.timer = 0.5
                if self.combo == 0:
                    self._begin('recover', 1.0)
        elif self.state in ('recover', 'stagger'):
            self.timer -= dt
            if self.timer <= 0:
                if self.phase2 and random.random() < 0.3:
                    from src.enemy import Enemy
                    living = sum(1 for e in enemies if e.alive and getattr(e, 'summoned', False))
                    if living < 2:
                        e = Enemy('drone', self.x + 1, self.y + 1)
                        e.aggro = True
                        e.summoned = True
                        enemies.append(e)
                self.state = 'chase'
                self.timer = random.uniform(0.5, 1.1)

    # ------------------------------------------------------------------
    def take_damage(self, dmg, from_x, from_y, particles, stagger=1.0):
        if not self.alive or not self.active:
            return 0
        if self.state == 'stagger':
            dmg *= 2.0
        self.hp -= dmg
        self.hit_flash = 0.18
        particles.hit(self.x, self.y)
        particles.damage_number(self.x, self.y, int(dmg))
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.death_clock = 0.0
            particles.death_burst(self.x, self.y, big=True)
            particles.blood_decal(self.x, self.y)
            return self.shards
        return 0

    # ---- presentation: (anim_name, t_or_progress, mode) ----
    def anim_state(self):
        if not self.alive:
            return ('die', self.death_clock or 0.0, 'time')
        prog = min(1.0, self.atk_t / max(0.01, self.atk_total))
        if self.state in ('windup', 'slam_wind', 'lunge_wind', 'charge_wind'):
            return ('swing', 0.45 * prog, 'once')
        if self.state in ('charge', 'lunge'):
            return ('swing', 0.5 + 0.35 * prog, 'once')
        if self.state in ('burst', 'fan', 'summon', 'scream_wind', 'teleport'):
            return ('cast', prog, 'once')
        if self.state == 'stagger':
            return ('hit', min(1.0, prog * 2), 'once')
        if self.state in ('chase', 'circle'):
            return ('run', self.anim_t, 'time')
        return ('stance', self.anim_t, 'time')
