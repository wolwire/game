"""Global constants: screen, isometric grid, balance numbers, palette."""

WIDTH, HEIGHT = 1280, 720
FPS = 60

# Isometric tile metrics (2:1 diamond)
TILE_W = 64
TILE_H = 32
HALF_W = TILE_W // 2
HALF_H = TILE_H // 2

# World size in tiles (open world)
WORLD_W = 120
WORLD_H = 120

# --- Player balance ---
PLAYER_BASE_HP = 100
PLAYER_BASE_STAMINA = 100
PLAYER_SPEED = 3.4          # tiles / second
PLAYER_SPRINT_MULT = 1.6
ROLL_SPEED = 7.5
ROLL_TIME = 0.38
ROLL_IFRAMES = 0.28
ROLL_COST = 22
SPRINT_DRAIN = 14           # stamina / second
STAMINA_REGEN = 32          # stamina / second
STAMINA_REGEN_DELAY = 0.55

LIGHT_DMG = 22
LIGHT_COST = 16
LIGHT_RECOVER = 0.34
HEAVY_DMG = 48
HEAVY_COST = 30
HEAVY_WINDUP = 0.42
HEAVY_RECOVER = 0.55
ATTACK_RANGE = 1.45         # tiles
ATTACK_ARC = 1.9            # radians

PARRY_WINDOW = 0.22
PARRY_RECOVER = 0.6
RIPOSTE_MULT = 2.6

STIM_HEAL = 65
STIM_CHARGES = 3
STIM_TIME = 0.85

INVULN_AFTER_HIT = 0.5

# Leveling (souls-like): cost grows per level
def level_cost(level):
    return int(80 + (level ** 1.9) * 14)

VIGOR_HP = 14               # hp per point
ENDURANCE_STAM = 9          # stamina per point
STRENGTH_DMG = 0.07         # +7% damage per point

# --- Camera ---
CAM_LERP = 6.0

# --- Palette (modern, overcast, desaturated with neon accents) ---
C_BG = (14, 15, 19)
C_UI_BG = (10, 11, 14, 200)
C_TEXT = (222, 224, 228)
C_TEXT_DIM = (140, 144, 152)
C_ACCENT = (87, 199, 255)       # signal blue
C_ACCENT2 = (255, 170, 64)      # sodium-lamp amber
C_HP = (196, 50, 56)
C_HP_BG = (52, 18, 20)
C_STAM = (96, 168, 80)
C_STAM_BG = (24, 40, 22)
C_SHARD = (150, 210, 255)
C_BOSS = (212, 168, 60)
C_DANGER = (255, 70, 70)
C_GRACE = (120, 220, 255)
