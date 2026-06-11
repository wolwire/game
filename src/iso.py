"""Isometric projection math.

World coordinates are in tile units (floats allowed). The projection is the
classic 2:1 diamond:  screen_x = (wx - wy) * HALF_W,  screen_y = (wx + wy) * HALF_H - z.
Depth sorting key for anything standing on the ground is (wx + wy).
"""
import math
from src.constants import HALF_W, HALF_H


def world_to_screen(wx, wy, z=0.0):
    return (wx - wy) * HALF_W, (wx + wy) * HALF_H - z


def screen_to_world(sx, sy):
    wx = (sx / HALF_W + sy / HALF_H) / 2
    wy = (sy / HALF_H - sx / HALF_W) / 2
    return wx, wy


def screen_dir_to_world(dx, dy):
    """Convert a screen-space input direction (e.g. WASD) into a normalized
    world-space direction so 'up' on screen moves up-screen in iso view."""
    wx = dx / HALF_W + dy / HALF_H
    wy = dy / HALF_H - dx / HALF_W
    length = math.hypot(wx, wy)
    if length < 1e-9:
        return 0.0, 0.0
    return wx / length, wy / length


def facing_octant(dx, dy):
    """Map a world-space direction to one of 8 facing indices (screen-space).
    0=E 1=SE 2=S 3=SW 4=W 5=NW 6=N 7=NE in *screen* terms."""
    sx = (dx - dy)
    sy = (dx + dy) * 0.5
    ang = math.atan2(sy, sx)
    return int(round(ang / (math.pi / 4))) % 8
