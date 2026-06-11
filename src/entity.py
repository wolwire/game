"""Shared entity helpers: grid collision and the projectile class."""
import math


def move_with_collision(world, x, y, dx, dy, radius=0.3):
    """Move a circle through the tile grid, sliding along walls."""
    nx = x + dx
    if not _blocked(world, nx, y, radius):
        x = nx
    ny = y + dy
    if not _blocked(world, x, ny, radius):
        y = ny
    return x, y


def _blocked(world, x, y, r):
    for ty in range(int(y - r), int(y + r) + 1):
        for tx in range(int(x - r), int(x + r) + 1):
            if not world.in_bounds(tx, ty) or world.solid[ty][tx]:
                # circle vs tile AABB
                cx = max(tx, min(x, tx + 1))
                cy = max(ty, min(y, ty + 1))
                if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                    return True
    return False


def dist(ax, ay, bx, by):
    return math.hypot(bx - ax, by - ay)


def norm(dx, dy):
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, 0.0
    return dx / d, dy / d


class Projectile:
    __slots__ = ('x', 'y', 'vx', 'vy', 'dmg', 'ttl', 'color', 'r', 'hostile')

    def __init__(self, x, y, vx, vy, dmg, color, ttl=3.0, r=0.22, hostile=True):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.dmg, self.color, self.ttl, self.r = dmg, color, ttl, r
        self.hostile = hostile

    def update(self, dt, world):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.ttl -= dt
        tx, ty = int(self.x), int(self.y)
        if not world.in_bounds(tx, ty) or world.solid[ty][tx]:
            self.ttl = 0
        return self.ttl > 0
