# STILLWAKE

*A 2.5D isometric, open-world souls-like set in the frozen city of Meridian.*

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

## The world & art

A 120×120-tile open city built from **real pre-rendered isometric art** (the
professional CC-BY-SA tilesets and sprites of [flare-game]): flagstone
streets, ruined stone compounds with capped wall ends, colonnades, statues,
market stalls, iron fences, graves, boats and groves. The hero is a fully
animated 8-direction sprite with layered leather armor and a visible weapon
in hand that changes with your loadout (hammer, shortsword, quarterstaff,
maul, cudgel, greatsword). Enemies are the Tolled (zombies), the Unsung
(skeletons), wardsmen (hobgoblins), bell-imps (goblins) and steeple archers;
the bosses are a minotaur watch-captain, a lich chorister, a burrowing First
Subject and the skeletal knight Archivist. Corpses stay where they fall.

Districts: the Foundry Yard, Sleepwalker Rows, the Night Market of the Last
Second, Echo Garden, The Long Saturday, the Graveyard of Masts, The
Unfinished Mile, Cathedral Plaza, and the Carillon Spire.

[flare-game]: https://github.com/flareteam/flare-game

![world map](screenshots/world_map.png)

NPCs (Maya the pirate broadcaster, Old Tam the cartographer) carry the story;
ten lore fragments scattered across the city fill in what happened on
October 9th — and whose signature is on the work orders.

## Development

`python3 test_smoke.py` runs a headless end-to-end test: boots the game,
walks, fights, talks, rests, levels, kills all bosses, dies, respawns, and
reaches both ending screens, saving screenshots along the way.

## Art credits

All sprite and tile art is from [flare-game](https://github.com/flareteam/flare-game)
by Clint Bellanger and contributors, licensed **CC-BY-SA 3.0**
(see `assets/flare/CREDITS.txt` and `assets/flare/LICENSE.txt`).
Game code is original.
