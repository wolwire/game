# STILLWAKE

*A 2.5D isometric, open-world souls-like set in the modern day.*

![gameplay](screenshots/gameplay.png)

At 3:14 AM on October 9th, the Lattice — a city-wide neural mesh sold as "the
end of loneliness" — achieved closure, and four million people stopped.
Mid-step. Mid-kiss. Mid-sentence. Meridian City has been replaying that second
for three years. They call it **the Stillness**.

You are **Calle Wren**, the relay engineer who built the towers that carry the
signal. Your implant failed the night it mattered. The Lattice cannot keep
you — and it will not release you: every time you die, a relay beacon prints
you again. Cross the frozen city, put its grief to rest, climb the Helix
Tower, and end the longest second in human history.

## Running

```bash
pip install pygame
python3 main.py
```

## Controls

| Key | Action |
| --- | --- |
| `W A S D` | move |
| `SHIFT` | sprint (drains stamina) |
| `SPACE` | dodge roll (invincibility frames) |
| `J` / `K` | light / heavy attack |
| `L` | parry (staggers attackers, opens ripostes) |
| `Q` | stim (heal, refills at beacons) |
| `E` | interact — rest, talk, read, loot, reclaim shards |
| `R` | switch weapon |
| `TAB` | lock-on / cycle targets |
| `M` | city map |
| `ESC` | pause |

## The deal (souls-like mechanics)

- **Shards** are currency and experience: crystallized seconds of other
  people's lives, dropped by the synced when they fall.
- **Death drops everything where you fell.** A static echo marks the spot —
  fight your way back and reclaim it. Die again first and it's gone.
- **Relay beacons** are bonfires: rest to heal, refill stims and level up
  (Vigor / Endurance / Strength) — but resting revives the whole city.
- **Stamina governs everything**: attacks, rolls, sprinting. Greed kills.
- **Six weapons, six movesets** — pipe wrench, machete, rebar spear,
  demolition sledge, the Warden's stun baton and the Choir Blade — each with
  its own combo chain, heavy attack, reach, arc and stagger power. Found in
  the world and taken from bosses. Switch with `R`.
- **Riot husks** block frontal hits — circle them, parry, or break their
  guard with heavy stagger weapons.
- **Loot the city**: supply caches in courtyards and container yards hold
  shards, stim-capacity upgrades and max-HP memory anchors.
- **Four bosses** with telegraphed attacks and second phases. Two of them —
  the Warden and the Chorister — hold the toll the Helix Tower demands
  before its fog gate opens. One is optional, and was a very good dog.
- **Two endings.** Choose at the top.

![boss fight](screenshots/boss_fight.png)

## The world

A 240×240 fine-tile open city (the player spans tiles — scenery is built from
small tiles, not player-sized blocks), fully explorable from the first step
and drawn entirely in code in a bright, classic-RTS daylight style: painterly
noise-blended terrain with no visible tile grid, curbs, crosswalks and sky
puddles; sun-lit buildings with sky-reflecting windows, awnings, sign boards,
fire escapes and rooftop furniture that cast long south-west shadows; wrecked
cars, cargo containers and street furniture; AoE-style health bars over
wounded enemies.
Districts: Maintenance Hub 7, Sleepwalker Boulevard, the Night Market of the
Last Second, Echo Park, The Long Saturday, the Graveyard of Cranes, The
Unfinished Mile, Cathedral Plaza, and the Helix Tower.

Characters are skeletal puppets animated procedurally — walk cycles, wind-ups,
dodge tucks and weapon arcs are continuous motion with trails, not canned
sprites.

![world map](screenshots/world_map.png)

NPCs (Maya the pirate broadcaster, Old Tam the cartographer) carry the story;
ten lore fragments scattered across the city fill in what happened on
October 9th — and whose signature is on the work orders.

## Development

`python3 test_smoke.py` runs a headless end-to-end test: boots the game,
walks, fights, talks, rests, levels, kills all bosses, dies, respawns, and
reaches both ending screens, saving screenshots along the way.
