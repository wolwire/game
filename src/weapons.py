"""Weapon definitions.

Each weapon has a light-attack combo (list of steps) and a heavy attack.
Step format: (kind, windup, active, recover). `sheet` names the flare avatar
overlay drawn in the player's hands.
"""

WEAPONS = {
    'wrench': dict(
        name="Founder's Hammer", sheet='smith_hammer', desc="You cast half the city's bells with it.",
        dmg=21, reach=1.35, arc=2.1, stamina=15, stagger=1.0,
        combo=[('swing', 0.16, 0.14, 0.30), ('swing', 0.12, 0.14, 0.34)],
        heavy=('smash', 0.46, 0.16, 0.52, 2.2),
        wlen=0.62, color=(186, 190, 200), grip=(110, 80, 50), shape='blunt',
        trail=(255, 214, 150)),
    'machete': dict(
        name="Butcher's Shortsword", sheet='shortsword', desc="From the night market's knife row.",
        dmg=15, reach=1.4, arc=2.2, stamina=11, stagger=0.7,
        combo=[('swing', 0.11, 0.12, 0.22), ('swing', 0.09, 0.12, 0.22),
               ('swing', 0.10, 0.12, 0.30)],
        heavy=('swing', 0.34, 0.16, 0.44, 1.9),
        wlen=0.72, color=(200, 206, 214), grip=(40, 40, 44), shape='blade',
        trail=(190, 230, 255)),
    'spear': dict(
        name="Pilgrim's Quarterstaff", sheet='staff', desc="Cut from the Unfinished Mile's scaffolds.",
        dmg=24, reach=1.9, arc=0.9, stamina=17, stagger=1.0,
        combo=[('thrust', 0.18, 0.12, 0.34), ('thrust', 0.14, 0.12, 0.38)],
        heavy=('swing', 0.42, 0.18, 0.50, 1.8),
        wlen=1.25, color=(150, 144, 138), grip=(96, 86, 70), shape='spear',
        trail=(255, 180, 130)),
    'sledge': dict(
        name="Mason's Maul", sheet='maul', desc="Asks one question, loudly.",
        dmg=42, reach=1.5, arc=2.4, stamina=30, stagger=2.4,
        combo=[('smash', 0.34, 0.16, 0.50)],
        heavy=('smash', 0.62, 0.18, 0.66, 1.9),
        wlen=0.85, color=(120, 116, 112), grip=(120, 92, 56), shape='hammer',
        trail=(255, 160, 90)),
    'baton': dict(
        name="Warden's Cudgel", sheet='club', desc="Still humming with the order it kept.",
        dmg=20, reach=1.4, arc=2.0, stamina=12, stagger=1.7, shock=True,
        combo=[('swing', 0.12, 0.12, 0.24), ('swing', 0.10, 0.12, 0.24),
               ('thrust', 0.12, 0.12, 0.30)],
        heavy=('thrust', 0.36, 0.14, 0.46, 2.0),
        wlen=0.66, color=(70, 76, 90), grip=(36, 38, 44), shape='baton',
        trail=(150, 220, 255)),
    'choirblade': dict(
        name="Choir Blade", sheet='greatsword', desc="It rings one pure note when it cuts.",
        dmg=26, reach=1.65, arc=2.2, stamina=14, stagger=1.0,
        combo=[('swing', 0.10, 0.12, 0.20), ('swing', 0.08, 0.12, 0.20),
               ('thrust', 0.10, 0.12, 0.20), ('swing', 0.10, 0.14, 0.34)],
        heavy=('swing', 0.38, 0.18, 0.42, 2.1),
        wlen=0.95, color=(220, 210, 240), grip=(90, 70, 110), shape='blade',
        trail=(216, 160, 255)),
}


def step_time(step):
    return step[1] + step[2] + step[3]
