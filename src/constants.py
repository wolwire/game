"""Global constants. World units are *fine* tiles: 32x16 px diamonds.
The player stands ~1.5 tiles wide — scenery is built from small tiles."""

WIDTH, HEIGHT = 1280, 720
FPS = 60

# Fine isometric tile metrics (2:1 diamond)
TILE_W = 32
TILE_H = 16
HALF_W = TILE_W // 2
HALF_H = TILE_H // 2

# World size in fine tiles
WORLD_W = 240
WORLD_H = 240

# Ground chunk pre-render (tiles per chunk side)
CHUNK = 16

# --- Player balance (distances in fine tiles: ~2x the old coarse units) ---
PLAYER_BASE_HP = 100
PLAYER_BASE_STAMINA = 100
PLAYER_SPEED = 7.0
PLAYER_SPRINT_MULT = 1.6
ROLL_SPEED = 15.0
ROLL_TIME = 0.40
ROLL_IFRAMES = 0.30
ROLL_COST = 20
SPRINT_DRAIN = 13
STAMINA_REGEN = 34
STAMINA_REGEN_DELAY = 0.5

COMBO_WINDOW = 0.45      # seconds after recover start to chain the next hit

PARRY_WINDOW = 0.22
PARRY_RECOVER = 0.55
RIPOSTE_MULT = 2.6

STIM_HEAL = 65
STIM_CHARGES = 3
STIM_TIME = 0.9

INVULN_AFTER_HIT = 0.55

def level_cost(level):
    return int(80 + (level ** 1.9) * 14)

VIGOR_HP = 14
ENDURANCE_STAM = 9
STRENGTH_DMG = 0.07

CAM_LERP = 6.5

# --- Palette ---
C_BG = (13, 14, 18)
C_TEXT = (224, 226, 230)
C_TEXT_DIM = (138, 142, 150)
C_ACCENT = (97, 203, 255)
C_ACCENT2 = (255, 176, 72)
C_HP = (198, 52, 58)
C_HP_BG = (52, 18, 20)
C_STAM = (104, 172, 84)
C_STAM_BG = (24, 40, 22)
C_SHARD = (152, 212, 255)
C_BOSS = (214, 170, 64)
C_DANGER = (255, 72, 72)
C_GRACE = (122, 222, 255)

# --- Lighting ---
LIGHT_SCALE = 3            # lightmap is screen/LIGHT_SCALE
AMBIENT = (158, 164, 184)    # moonlit overcast ambient (multiplied)
