"""Cheap 2D lighting: a low-res lightmap filled with the ambient color,
light blobs added on top, multiplied over the framebuffer. Turns flat
daylight rendering into a moody night city for ~1.5 ms a frame."""
import pygame
from src.constants import WIDTH, HEIGHT, LIGHT_SCALE, AMBIENT
from src.assets import light_sprite
from src.iso import world_to_screen

LW, LH = WIDTH // LIGHT_SCALE, HEIGHT // LIGHT_SCALE


class Lighting:
    def __init__(self):
        self.lmap = pygame.Surface((LW, LH))
        self.lights = []   # transient per-frame: (sx, sy, radius_px, color)

    def add(self, sx, sy, radius, color):
        if -radius < sx < WIDTH + radius and -radius < sy < HEIGHT + radius:
            self.lights.append((sx, sy, radius, color))

    def add_world(self, ox, oy, wx, wy, z, radius, color):
        sx, sy = world_to_screen(wx, wy, z)
        self.add(sx + ox, sy + oy, radius, color)

    def apply(self, screen):
        self.lmap.fill(AMBIENT)
        s = LIGHT_SCALE
        for (sx, sy, radius, color) in self.lights:
            spr = light_sprite(max(8, int(radius / s)), color)
            r = spr.get_rect(center=(int(sx / s), int(sy / s)))
            self.lmap.blit(spr, r, special_flags=pygame.BLEND_RGB_ADD)
        self.lights.clear()
        big = pygame.transform.smoothscale(self.lmap, (WIDTH, HEIGHT))
        screen.blit(big, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
