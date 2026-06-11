"""Skeletal character renderer.

Characters are drawn as articulated puppets — joints are computed in world
space (forward/side in tile units, height in pixels) from continuous pose
functions, then projected to the screen. This gives smooth walk cycles,
readable wind-ups, and real weapon arcs instead of canned sprites.
"""
import math
import pygame
from src.iso import world_to_screen
from src.assets import sh

STYLES = {
    'player':    dict(skin=(216, 180, 152), hair=(52, 42, 36), top=(70, 94, 124), top2=(52, 70, 94),
                      pants=(44, 48, 58), boots=(32, 34, 40), accent=(97, 203, 255), scale=1.0),
    'husk':      dict(skin=(172, 168, 152), hair=(74, 70, 64), top=(124, 122, 116), top2=(104, 102, 96),
                      pants=(70, 70, 74), boots=(40, 40, 44), accent=(140, 46, 46), scale=1.0, tie=True,
                      eyes=(200, 200, 190)),
    'stalker':   dict(skin=(188, 160, 140), hair=(38, 38, 44), top=(46, 46, 54), top2=(36, 36, 42),
                      pants=(38, 40, 46), boots=(28, 28, 32), accent=(225, 70, 70), scale=1.0, hood=True,
                      eyes=(255, 80, 80)),
    'riot':      dict(skin=(120, 124, 134), hair=(50, 54, 62), top=(58, 62, 74), top2=(44, 48, 58),
                      pants=(48, 52, 62), boots=(32, 34, 40), accent=(255, 186, 80), scale=1.08,
                      helmet=True, shield=True, armor=True),
    'maya':      dict(skin=(192, 152, 126), hair=(30, 26, 30), top=(150, 96, 62), top2=(122, 76, 50),
                      pants=(54, 50, 62), boots=(36, 32, 40), accent=(255, 204, 120), scale=0.98,
                      headset=True),
    'cart':      dict(skin=(222, 192, 162), hair=(176, 176, 176), top=(84, 104, 86), top2=(66, 84, 70),
                      pants=(60, 58, 50), boots=(40, 38, 34), accent=(170, 230, 195), scale=0.95, hat=True),
    'warden':    dict(skin=(126, 130, 142), hair=(50, 54, 62), top=(62, 66, 80), top2=(46, 50, 62),
                      pants=(50, 54, 64), boots=(34, 36, 42), accent=(255, 176, 64), scale=1.75,
                      helmet=True, shield=True, armor=True),
    'chorister': dict(skin=(206, 196, 216), hair=(228, 224, 234), top=(104, 76, 122), top2=(82, 58, 98),
                      pants=(70, 54, 86), boots=(50, 40, 62), accent=(196, 126, 255), scale=1.4,
                      robe=True, eyes=(216, 150, 255)),
    'archivist': dict(skin=(150, 200, 230), hair=(220, 230, 240), top=(50, 72, 100), top2=(38, 56, 80),
                      pants=(40, 56, 76), boots=(30, 40, 54), accent=(134, 230, 255), scale=1.6,
                      coat=True, eyes=(160, 240, 255)),
}

OUT = (14, 14, 18)   # outline


def _lerp(a, b, t):
    return a + (b - a) * t


def _ease(t):
    return t * t * (3 - 2 * t)


class Pose:
    """Joint targets produced by the pose functions, all in local units."""
    __slots__ = ('lf', 'rf', 'lh', 'rh', 'hip_z', 'chest_z', 'head_f', 'lean',
                 'head_z', 'crouch')

    def __init__(self):
        self.lf = (0.05, -0.22, 0)    # (fwd, side, z) feet
        self.rf = (0.05, 0.22, 0)
        self.lh = (0.02, -0.34, 20)   # hands
        self.rh = (0.02, 0.34, 20)
        self.hip_z = 17
        self.chest_z = 28
        self.head_z = 38
        self.head_f = 0.04
        self.lean = 0.0               # forward lean of upper body (units)
        self.crouch = 0.0


def pose_idle(t):
    p = Pose()
    b = math.sin(t * 2.2) * 0.8
    p.chest_z += b
    p.head_z += b * 1.3
    p.lh = (0.04, -0.33, 19 + b * 0.5)
    p.rh = (0.04, 0.33, 19 + b * 0.5)
    return p


def pose_walk(t, run=False):
    p = Pose()
    rate = 11.0 if run else 8.0
    amp = 0.42 if run else 0.3
    ph = t * rate
    s = math.sin(ph)
    p.lf = (s * amp, -0.2, max(0, math.cos(ph)) * (4 if run else 2.5))
    p.rf = (-s * amp, 0.2, max(0, -math.cos(ph)) * (4 if run else 2.5))
    bob = abs(math.cos(ph)) * (2.2 if run else 1.4)
    p.hip_z += bob * 0.5
    p.chest_z += bob
    p.head_z += bob
    p.lean = 0.10 if run else 0.04
    arm = (0.30 if run else 0.18)
    p.lh = (-s * arm, -0.32, 19 + bob * 0.5)
    p.rh = (s * arm, 0.32, 19 + bob * 0.5)
    return p


def pose_roll(t01):
    p = Pose()
    c = math.sin(t01 * math.pi)
    p.crouch = c * 9
    p.hip_z -= c * 7
    p.chest_z -= c * 9
    p.head_z -= c * 11
    p.lean = 0.5 * c
    p.head_f = 0.18
    tuck = c * 0.2
    p.lf = (0.16 - tuck, -0.18, c * 3)
    p.rf = (-0.05 + tuck, 0.18, c * 5)
    p.lh = (0.25, -0.2, 14)
    p.rh = (0.25, 0.2, 14)
    return p


def pose_stagger(t01):
    p = Pose()
    k = math.sin(min(1, t01 * 2) * math.pi)
    p.lean = -0.22 * k
    p.head_f = -0.06 * k
    p.chest_z -= 2 * k
    p.lh = (-0.15 * k, -0.4, 22)
    p.rh = (-0.15 * k, 0.4, 22)
    return p


def pose_drink(t01):
    p = Pose()
    k = _ease(min(1, t01 * 1.6))
    p.rh = (_lerp(0.04, 0.16, k), _lerp(0.33, 0.10, k), _lerp(19, 34, k))
    p.head_f = 0.02
    return p


def pose_parry(t01):
    p = Pose()
    k = _ease(min(1, t01 * 4))
    p.rh = (_lerp(0.04, 0.5, k), _lerp(0.33, 0.05, k), _lerp(19, 30, k))
    p.lh = (0.2 * k, -0.25, 24)
    p.lean = 0.06
    return p


def pose_dead(t01):
    p = Pose()
    k = _ease(min(1, t01 * 1.4))
    p.crouch = 13 * k
    p.hip_z -= 12 * k
    p.chest_z -= 16 * k
    p.head_z -= 20 * k
    p.lean = 0.55 * k
    return p


def attack_hand(kind, p01, step=0):
    """Returns (fwd, side, z, weapon_angle_offset) of the weapon hand through
    an attack. weapon_angle_offset is radians around the character, 0=facing."""
    flip = -1 if step % 2 else 1
    if kind == 'swing':
        a0, a1 = -1.9 * flip, 1.7 * flip
        if p01 < 0.32:                     # wind-up: pull back
            k = _ease(p01 / 0.32)
            ang = _lerp(0.6 * flip, a0, k)
            r = _lerp(0.5, 0.62, k)
            z = _lerp(20, 27, k)
        elif p01 < 0.60:                   # strike: fast sweep
            k = _ease((p01 - 0.32) / 0.28)
            ang = _lerp(a0, a1, k)
            r = 0.85
            z = _lerp(27, 18, k)
        else:                              # recover
            k = _ease((p01 - 0.60) / 0.40)
            ang = _lerp(a1, 0.5 * flip, k)
            r = _lerp(0.85, 0.5, k)
            z = _lerp(18, 20, k)
        return (math.cos(ang) * r, math.sin(ang) * r, z, ang)
    if kind == 'thrust':
        if p01 < 0.36:
            k = _ease(p01 / 0.36)
            f = _lerp(0.3, -0.25, k)
            z = _lerp(20, 24, k)
        elif p01 < 0.58:
            k = _ease((p01 - 0.36) / 0.22)
            f = _lerp(-0.25, 1.05, k)
            z = 22
        else:
            k = _ease((p01 - 0.58) / 0.42)
            f = _lerp(1.05, 0.3, k)
            z = _lerp(22, 20, k)
        return (f, 0.12, z, 0.0)
    # smash: overhead slam
    if p01 < 0.42:
        k = _ease(p01 / 0.42)
        f = _lerp(0.3, -0.35, k)
        z = _lerp(20, 46, k)
    elif p01 < 0.62:
        k = _ease((p01 - 0.42) / 0.20)
        f = _lerp(-0.35, 0.95, k)
        z = _lerp(46, 8, k)
    else:
        k = _ease((p01 - 0.62) / 0.38)
        f = _lerp(0.95, 0.4, k)
        z = _lerp(8, 20, k)
    return (f, 0.1, z, 0.0)


def pose_attack(kind, p01, step=0):
    p = Pose()
    hf, hs, hz, _ = attack_hand(kind, p01, step)
    p.rh = (hf, hs, hz)
    # body follows the strike
    if p01 < 0.35:
        p.lean = -0.08
    elif p01 < 0.62:
        p.lean = 0.22
        p.crouch = 2
    else:
        p.lean = 0.06
    p.lh = (-hf * 0.3, -0.3, 18 + (hz - 20) * 0.2)
    p.lf = (0.22, -0.2, 0)
    p.rf = (-0.14, 0.22, 0)
    return p


# ----------------------------------------------------------------- drawing
def draw(surf, ox, oy, x, y, fx, fy, style_name, anim, t,
         weapon=None, attack=None, trail=None, flash=0.0, alpha=255):
    """Draw a humanoid puppet. attack = (kind, p01, step) when attacking."""
    st = STYLES[style_name]
    sc = st['scale']
    rx, ry = -fy, fx

    if anim == 'idle':
        pose = pose_idle(t)
    elif anim == 'walk':
        pose = pose_walk(t)
    elif anim == 'run':
        pose = pose_walk(t, run=True)
    elif anim == 'roll':
        pose = pose_roll(t)
    elif anim == 'attack' and attack:
        pose = pose_attack(attack[0], attack[1], attack[2])
    elif anim == 'windup' and attack:
        pose = pose_attack(attack[0], attack[1], attack[2])
    elif anim == 'stagger':
        pose = pose_stagger(t)
    elif anim == 'drink':
        pose = pose_drink(t)
    elif anim == 'parry':
        pose = pose_parry(t)
    elif anim == 'dead':
        pose = pose_dead(t)
    else:
        pose = pose_idle(t)

    def P(f, s, z):
        f = f * sc
        s = s * sc
        wx = x + fx * (f + pose.lean * (z / 30)) + rx * s
        wy = y + fy * (f + pose.lean * (z / 30)) + ry * s
        sx, sy = world_to_screen(wx, wy, (z - pose.crouch) * sc)
        return (sx + ox, sy + oy)

    lw = max(2, int(3 * sc))     # limb width

    skin = st['skin']
    top, top2 = st['top'], st['top2']
    if flash > 0:
        top = sh(top, 1 + flash * 2)
        top2 = sh(top2, 1 + flash * 2)
        skin = sh(skin, 1 + flash * 1.5)

    # shadow
    sxc, syc = P(0, 0, 0)
    shadow = pygame.Surface((int(26 * sc), int(10 * sc)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    surf.blit(shadow, (sxc - 13 * sc, syc - 5 * sc))

    hip_l = P(pose.lf[0] * 0.1, -0.13, pose.hip_z)
    hip_r = P(pose.rf[0] * 0.1, 0.13, pose.hip_z)
    sho_l = P(0, -0.26, pose.chest_z)
    sho_r = P(0, 0.26, pose.chest_z)
    foot_l = P(*pose.lf)
    foot_r = P(*pose.rf)
    hand_l = P(*pose.lh)
    hand_r = P(*pose.rh)
    head = P(pose.head_f, 0, pose.head_z)

    # near/far ordering by screen y of the side offset
    left_near = P(0, -0.3, 20)[1] > P(0, 0.3, 20)[1]

    def limb(a, b, color, width):
        pygame.draw.line(surf, OUT, a, b, width + 2)
        pygame.draw.line(surf, color, a, b, width)

    def leg(hip, foot, near):
        c = st['pants'] if near else sh(st['pants'], 0.75)
        # knee bend: midpoint pushed slightly forward
        mid = ((hip[0] + foot[0]) / 2 + fx * 1.5, (hip[1] + foot[1]) / 2 - 1)
        pygame.draw.lines(surf, OUT, False, [hip, mid, foot], lw + 2)
        pygame.draw.lines(surf, c, False, [hip, mid, foot], lw)
        bc = st['boots'] if near else sh(st['boots'], 0.75)
        pygame.draw.line(surf, bc, (foot[0] - 1, foot[1] - 1), (foot[0] + 2, foot[1]), lw + 1)

    def arm(sho, hand, near):
        c = top if near else sh(top, 0.7)
        mid = ((sho[0] + hand[0]) / 2, (sho[1] + hand[1]) / 2 + 2)
        pygame.draw.lines(surf, OUT, False, [sho, mid, hand], lw + 2)
        pygame.draw.lines(surf, c, False, [sho, mid, hand], lw)
        pygame.draw.circle(surf, skin if near else sh(skin, 0.8), hand, max(2, int(2 * sc)))

    # ---- draw order: far limbs, torso, near limbs, head, weapon ----
    if left_near:
        leg(hip_r, foot_r, False)
        arm(sho_r, hand_r, False)
    else:
        leg(hip_l, foot_l, False)
        arm(sho_l, hand_l, False)

    # torso
    if st.get('robe'):
        hem_l = P(0.05, -0.42, 2)
        hem_r = P(0.05, 0.42, 2)
        sway = math.sin(t * 3) * 2
        pygame.draw.polygon(surf, OUT, [sho_l, sho_r, (hem_r[0] + sway, hem_r[1]),
                                        (hem_l[0] + sway, hem_l[1])], 0)
        pygame.draw.polygon(surf, top, [(sho_l[0] + 1, sho_l[1] + 1), (sho_r[0] - 1, sho_r[1] + 1),
                                        (hem_r[0] + sway - 2, hem_r[1] - 1), (hem_l[0] + sway + 2, hem_l[1] - 1)])
        pygame.draw.line(surf, top2, ((sho_l[0] + sho_r[0]) / 2, (sho_l[1] + sho_r[1]) / 2),
                         ((hem_l[0] + hem_r[0]) / 2 + sway, (hem_l[1] + hem_r[1]) / 2), 2)
    else:
        quad = [sho_l, sho_r, hip_r, hip_l]
        pygame.draw.polygon(surf, OUT, quad, 0)
        inner = [(sho_l[0] + 1, sho_l[1] + 1), (sho_r[0] - 1, sho_r[1] + 1),
                 (hip_r[0] - 1, hip_r[1] - 1), (hip_l[0] + 1, hip_l[1] - 1)]
        pygame.draw.polygon(surf, top, inner)
        # shaded half (away from light/facing)
        midt = ((sho_l[0] + sho_r[0]) / 2, (sho_l[1] + sho_r[1]) / 2)
        midb = ((hip_l[0] + hip_r[0]) / 2, (hip_l[1] + hip_r[1]) / 2)
        shade_side = [midt, sho_l, hip_l, midb] if not left_near else [midt, sho_r, hip_r, midb]
        pygame.draw.polygon(surf, top2, shade_side)
        if st.get('armor'):  # chest plate
            pygame.draw.line(surf, sh(top, 1.3), (midt[0], midt[1] + 2), (midb[0], midb[1] - 2), 2)
            pygame.draw.line(surf, st['accent'], (sho_l[0] + 2, sho_l[1] + 3), (sho_r[0] - 2, sho_r[1] + 3), 1)
        elif st.get('tie'):
            pygame.draw.line(surf, st['accent'], (midt[0], midt[1] + 1), (midb[0], midb[1] - 2), 2)
        elif st.get('coat'):
            pygame.draw.line(surf, sh(top, 1.25), midt, midb, 1)
        else:  # zipper / jacket accent
            pygame.draw.line(surf, st['accent'], (midt[0], midt[1] + 1), (midb[0], midb[1]), 1)

    if st.get('coat'):  # coat tails
        tail_l = P(-0.18, -0.3, 4)
        tail_r = P(-0.18, 0.3, 4)
        pygame.draw.polygon(surf, top2, [hip_l, hip_r, tail_r, tail_l])

    if left_near:
        leg(hip_l, foot_l, True)
        arm(sho_l, hand_l, True)
    else:
        leg(hip_r, foot_r, True)
        arm(sho_r, hand_r, True)

    # head
    hr = max(3, int(5.5 * sc))
    pygame.draw.circle(surf, OUT, head, hr + 1)
    pygame.draw.circle(surf, skin, head, hr)
    face_sx = (fx - fy)  # facing in screen-x
    facing_cam = (fx + fy) > -0.2
    if st.get('helmet'):
        pygame.draw.circle(surf, top, head, hr, draw_top_left=True, draw_top_right=True)
        pygame.draw.circle(surf, sh(top, 1.3), (head[0] - 1, head[1] - 2), hr - 2,
                           draw_top_left=True)
        if facing_cam:
            vx = head[0] + (1 if face_sx > 0 else -1) * 1
            pygame.draw.line(surf, st['accent'], (vx - hr + 2, head[1]), (vx + hr - 2, head[1]), 2)
    elif st.get('hood'):
        pygame.draw.circle(surf, top, head, hr + 1, draw_top_left=True, draw_top_right=True)
        pygame.draw.line(surf, top, (head[0] - hr, head[1]), (head[0] + hr, head[1]), 2)
    elif st.get('hat'):
        pygame.draw.line(surf, st['hair'], (head[0] - hr, head[1] + 2), (head[0] + hr, head[1] + 2), 1)
        pygame.draw.line(surf, sh(st['top'], 0.7), (head[0] - hr + 1, head[1] - 3),
                         (head[0] + hr - 1, head[1] - 3), 3)
        pygame.draw.line(surf, sh(st['top'], 0.85), (head[0] - hr - 2, head[1] - 1),
                         (head[0] + hr + 2, head[1] - 1), 2)
    else:
        pygame.draw.circle(surf, st['hair'], (head[0], head[1] - 1), hr,
                           draw_top_left=True, draw_top_right=True)
        if abs(face_sx) > 0.3:  # hair swept opposite facing
            hx = head[0] - (1 if face_sx > 0 else -1) * (hr - 1)
            pygame.draw.line(surf, st['hair'], (hx, head[1] - 1), (hx, head[1] + 2), 2)
    if st.get('headset'):
        pygame.draw.arc(surf, (220, 220, 230), (head[0] - hr, head[1] - hr - 2, hr * 2, hr * 2),
                        0.4, 2.7, 2)
    # eyes
    if facing_cam and not st.get('helmet'):
        ec = st.get('eyes', (30, 26, 26))
        exo = 1 if face_sx >= 0 else -1
        pygame.draw.circle(surf, ec, (int(head[0] + exo * 2), head[1]), 1)
        if abs(face_sx) < 0.85:
            pygame.draw.circle(surf, ec, (int(head[0] - exo * 1), head[1]), 1)

    # shield (off-hand)
    if st.get('shield'):
        sb = P(0.30, -0.30, 22)
        st_ = P(0.30, -0.30, 8)
        wvec = (fx - fy, (fx + fy) * 0.5)
        wlen = math.hypot(*wvec) or 1
        nx_, ny_ = wvec[0] / wlen * 7 * sc, wvec[1] / wlen * 7 * sc
        pts = [(sb[0] - nx_, sb[1] - ny_), (sb[0] + nx_, sb[1] + ny_),
               (st_[0] + nx_, st_[1] + ny_), (st_[0] - nx_, st_[1] - ny_)]
        pygame.draw.polygon(surf, OUT, pts)
        pygame.draw.polygon(surf, sh((70, 76, 90), 1 + flash), [(p[0] + (1 if i in (0, 3) else -1), p[1]) for i, p in enumerate(pts)])
        pygame.draw.line(surf, (160, 170, 190), pts[0], pts[3], 1)
        pygame.draw.line(surf, st['accent'], ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2 + 3),
                         ((pts[3][0] + pts[2][0]) / 2, (pts[3][1] + pts[2][1]) / 2 - 3), 1)

    # weapon in main hand
    if weapon is not None:
        from src.weapons import draw_weapon
        if attack:
            hf, hsd, hz, ang = attack_hand(attack[0], attack[1], attack[2])
            wf = (math.cos(ang), math.sin(ang)) if attack[0] == 'swing' else (1.0, 0.0)
            if attack[0] == 'smash':
                # blade pitches with the slam
                tip_z = hz + (30 if attack[1] < 0.42 else -6)
            else:
                tip_z = hz + weapon.get('tip_rise', 4)
            tip = P(hf + wf[0] * weapon['wlen'], hsd + wf[1] * weapon['wlen'], tip_z)
        else:
            # held at rest, angled across the body
            tip = P(pose.rh[0] + 0.55, pose.rh[1] + 0.25, pose.rh[2] + 16)
        draw_weapon(surf, hand_r, tip, weapon, flash)
        if trail is not None and attack and 0.30 < attack[1] < 0.75:
            trail.append([tip[0], tip[1], 0.14])


def draw_dog(surf, ox, oy, x, y, fx, fy, anim, t, flash=0.0, scale=1.0, accent=(230, 90, 60)):
    body = (92, 78, 60)
    belly = (70, 58, 46)
    rx, ry = -fy, fx
    sc = scale

    def P(f, s, z):
        wx = x + fx * f * sc + rx * s * sc
        wy = y + fy * f * sc + ry * s * sc
        sx, sy = world_to_screen(wx, wy, z * sc)
        return (sx + ox, sy + oy)

    sxc, syc = P(0, 0, 0)
    shadow = pygame.Surface((int(30 * sc), int(10 * sc)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    surf.blit(shadow, (sxc - 15 * sc, syc - 5 * sc))

    run = anim in ('walk', 'run')
    ph = t * 12
    lunge = anim in ('attack', 'windup')
    crouch = 3 if lunge else 0
    front = P(0.45, 0, 12 - crouch)
    rear = P(-0.45, 0, 14 - crouch)
    bc = sh(body, 1 + flash * 2)
    # legs (trot gait)
    for i, (f, s) in enumerate([(0.4, -0.16), (0.4, 0.16), (-0.4, -0.16), (-0.4, 0.16)]):
        sw = math.sin(ph + (i % 2) * math.pi + (i // 2) * math.pi * 0.5) * (0.18 if run else 0.0)
        hip = P(f, s, 12 - crouch)
        foot = P(f + sw, s, 0)
        pygame.draw.line(surf, OUT, hip, foot, 4)
        pygame.draw.line(surf, sh(bc, 0.8 if i % 2 == 0 else 1.0), hip, foot, 2)
    # body capsule
    pygame.draw.line(surf, OUT, front, rear, int(11 * sc))
    pygame.draw.line(surf, bc, front, rear, int(9 * sc))
    pygame.draw.line(surf, belly, (front[0], front[1] + 3), (rear[0], rear[1] + 3), 3)
    # ribs showing (it has been three years)
    for i in range(3):
        t_ = 0.25 + i * 0.2
        rxp = front[0] + (rear[0] - front[0]) * t_
        ryp = front[1] + (rear[1] - front[1]) * t_
        pygame.draw.line(surf, sh(bc, 0.75), (rxp, ryp - 2), (rxp, ryp + 3), 1)
    # tail
    tail = P(-0.7, 0.05, 18)
    pygame.draw.line(surf, OUT, rear, tail, 4)
    pygame.draw.line(surf, sh(bc, 0.9), rear, tail, 2)
    # head
    head = P(0.72, 0, (10 if lunge else 17) - crouch)
    snout = P(0.95, 0, (8 if lunge else 15) - crouch)
    pygame.draw.line(surf, OUT, front, head, int(9 * sc))
    pygame.draw.line(surf, bc, front, head, int(7 * sc))
    pygame.draw.line(surf, OUT, head, snout, 6)
    pygame.draw.line(surf, sh(bc, 1.05), head, snout, 4)
    if lunge:  # open jaw
        jaw = P(0.93, 0, (4 - crouch))
        pygame.draw.line(surf, (60, 30, 30), head, jaw, 3)
        pygame.draw.line(surf, (220, 215, 200), (snout[0] - 1, snout[1]), (snout[0] + 1, snout[1]), 2)
    # ears + eye
    pygame.draw.line(surf, OUT, (head[0] - 2, head[1] - 4), (head[0] - 4, head[1] - 8), 3)
    pygame.draw.line(surf, OUT, (head[0] + 2, head[1] - 4), (head[0] + 3, head[1] - 8), 3)
    pygame.draw.circle(surf, accent, (int(head[0] + (1 if (fx - fy) > 0 else -1) * 2), int(head[1] - 1)), 1)


def draw_drone(surf, ox, oy, x, y, t, flash=0.0, firing=False):
    sx, sy = world_to_screen(x, y, 0)
    sx += ox
    sy += oy
    shadow = pygame.Surface((22, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 60), shadow.get_rect())
    surf.blit(shadow, (sx - 11, sy - 4))
    bob = math.sin(t * 3.1) * 2.5
    hy = sy - 46 + bob
    body = sh((96, 102, 116), 1 + flash * 2)
    # rotor arms + blur disks
    spin = (t * 40) % 1
    for side in (-15, 15):
        pygame.draw.line(surf, (60, 64, 74), (sx, hy - 2), (sx + side, hy - 7), 2)
        blur = pygame.Surface((22, 7), pygame.SRCALPHA)
        pygame.draw.ellipse(blur, (180, 190, 205, 70 + int(spin * 40)), blur.get_rect())
        surf.blit(blur, (sx + side - 11, hy - 11))
    pygame.draw.ellipse(surf, OUT, (sx - 12, hy - 7, 24, 15))
    pygame.draw.ellipse(surf, body, (sx - 11, hy - 6, 22, 13))
    pygame.draw.ellipse(surf, sh(body, 0.7), (sx - 11, hy, 22, 7))
    pygame.draw.ellipse(surf, sh(body, 1.3), (sx - 8, hy - 5, 10, 4))
    # camera eye
    eye = (255, 110, 90) if not firing else (255, 220, 200)
    pygame.draw.circle(surf, OUT, (sx, int(hy + 5)), 4)
    pygame.draw.circle(surf, eye, (sx, int(hy + 5)), 3 if firing else 2)
    # landing skids
    pygame.draw.line(surf, (60, 64, 74), (sx - 7, hy + 6), (sx - 7, hy + 11), 1)
    pygame.draw.line(surf, (60, 64, 74), (sx + 7, hy + 6), (sx + 7, hy + 11), 1)
