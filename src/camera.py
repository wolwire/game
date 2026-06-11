"""Smooth-follow camera with screen shake, in screen-space pixels."""
import random
from src.constants import WIDTH, HEIGHT, CAM_LERP
from src.iso import world_to_screen


class Camera:
    def __init__(self, wx, wy):
        sx, sy = world_to_screen(wx, wy)
        self.x, self.y = sx, sy
        self.shake_t = 0.0
        self.shake_amp = 0.0

    def follow(self, wx, wy, dt):
        tx, ty = world_to_screen(wx, wy)
        f = min(1.0, CAM_LERP * dt)
        self.x += (tx - self.x) * f
        self.y += (ty - self.y) * f
        self.shake_t = max(0.0, self.shake_t - dt)

    def shake(self, amp=6, t=0.25):
        self.shake_amp = amp
        self.shake_t = t

    def offset(self):
        ox = WIDTH / 2 - self.x
        oy = HEIGHT / 2 - self.y + 40
        if self.shake_t > 0:
            ox += random.uniform(-self.shake_amp, self.shake_amp)
            oy += random.uniform(-self.shake_amp, self.shake_amp)
        return ox, oy
