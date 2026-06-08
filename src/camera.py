import pygame
from .constants import WIDTH, HEIGHT


class Camera:
    def __init__(self, map_width, map_height):
        self.offset = pygame.math.Vector2(0, 0)
        self.map_w = map_width
        self.map_h = map_height

    def update(self, target_rect):
        x = target_rect.centerx - WIDTH // 2
        y = target_rect.centery - HEIGHT // 2
        x = max(0, min(x, self.map_w - WIDTH))
        y = max(0, min(y, self.map_h - HEIGHT))
        self.offset.x += (x - self.offset.x) * 0.12
        self.offset.y += (y - self.offset.y) * 0.12

    def apply(self, rect):
        return pygame.Rect(rect.x - self.offset.x, rect.y - self.offset.y, rect.width, rect.height)

    def apply_pos(self, x, y):
        return x - self.offset.x, y - self.offset.y
