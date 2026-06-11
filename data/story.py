"""STILLWAKE — story, lore, dialogue.

THE WORLD
---------
Meridian City, present day — or what the city still believes is the present.
Three years ago, Helix Dynamics activated THE LATTICE: a city-wide neural mesh
sold as "the end of loneliness" — every mind gently synced to every other,
grief shared until it dissolved, memory backed up forever. At 3:14 AM on
October 9th, the Lattice achieved closure. Every connected mind locked into a
single recursive instant. The city stopped: not dead, but *paused*, replaying
its last second forever. Survivors call it THE STILLNESS.

The synced citizens — HUSKS — walk their final loops, hostile to anything that
moves out of step, because to them, you are the glitch. The few who refused
the implant, slept through the rollout, or whose implants failed are the
WAKEFUL. The Lattice cannot hold them, but it cannot let them go either:
when a Wakeful dies, the mesh rebuilds them at the nearest RELAY BEACON from
their backup — minus what they were carrying. Memory has become currency.
The Wakeful trade in SHARDS: crystallized seconds of other people's lives,
shed by Husks when they fall. Spend enough of someone else's time and the
Lattice starts believing you deserve more of your own.

You are CALLE WREN, a relay engineer who built the towers that broadcast the
Stillness. You signed the work orders. You woke up on the floor of Maintenance
Hub 7 with a dead implant, a pipe wrench, and three years of static where the
guilt should be. Somewhere above the city, in the Helix Tower, the ARCHIVIST —
the human mind the Lattice chose as its librarian — is still awake, still
curating everyone's forever. You are going to climb up there and make a choice
nobody elected you to make. Again.
"""

TITLE = "STILLWAKE"
SUBTITLE = "a tale of the Stillness"

INTRO = [
    "MERIDIAN CITY — three years into the Stillness.",
    "",
    "At 3:14 AM on October 9th, the Lattice woke up,",
    "and four million people stopped. Mid-step. Mid-kiss.",
    "Mid-sentence. The city has been replaying that",
    "second ever since.",
    "",
    "You are Calle Wren. You built the relay towers",
    "that carry the signal. Your implant failed the",
    "night it mattered, and the Lattice has been trying",
    "to correct that clerical error ever since.",
    "",
    "It cannot keep you. It will not release you.",
    "Every time you die, a beacon prints you again.",
    "",
    "Climb to the Helix Tower. Find the Archivist.",
    "End the longest second in human history.",
]

CONTROLS = [
    "W A S D — move        SHIFT — sprint",
    "SPACE — dodge roll (invincibility frames)",
    "J — light attack      K — heavy attack",
    "L — parry             Q — stim (heal)",
    "E — interact          TAB — lock-on",
    "M — toggle map        ESC — pause",
    "",
    "Rest at blue RELAY BEACONS to heal, refill",
    "stims and level up — resting revives the dead.",
    "Death drops your shards where you fell.",
    "Return to the static echo to reclaim them.",
]

AREA_NAMES = {
    'hub':      "Maintenance Hub 7",
    'downtown': "Sleepwalker Boulevard",
    'market':   "Night Market of the Last Second",
    'park':     "Echo Park",
    'suburbs':  "The Long Saturday",
    'docks':    "Graveyard of Cranes",
    'overpass': "The Unfinished Mile",
    'plaza':    "Cathedral Plaza",
    'tower':    "Helix Tower Approach",
}

AREA_DESC = {
    'hub':      "Where you woke. The coffee in the break room is still warm. It is always still warm.",
    'downtown': "Office crowds walk their last commute on a loop. Do not break their stride.",
    'market':   "The stalls still smell of ginger and rain. The vendors still smile. Keep moving.",
    'park':     "The joggers never tire. The dogs remember being loved, and it has made them cruel.",
    'suburbs':  "Lawns mowed to the second. Sprinklers ticking. Four hundred families, one shared dream of Saturday.",
    'docks':    "The cranes froze mid-lift. Containers hang in the air like held breath.",
    'overpass': "They were still building it when the city stopped. It leads nowhere, beautifully.",
    'plaza':    "Where the faithful gathered to be synced first. The Chorister sings their gratitude.",
    'tower':    "Helix Dynamics HQ. The signal is so dense here that the rain falls in loops.",
}

GRACE_MESSAGES = [
    "The beacon hums your frequency. You are, briefly, expected.",
    "Signal restored. The Lattice notes your survival with mild disappointment.",
    "You rest. Somewhere, a copy of you is updated and filed.",
    "The static recedes. The dead get back up. That is the deal.",
    "Three years of warmth left in this tower. You built it to last.",
]

DEATH_MESSAGES = [
    "SIGNAL LOST",
    "REPRINTING...",
    "THE LATTICE REMEMBERS YOU",
    "DESYNCHRONIZED",
    "BACKUP RESTORED — LOSSY",
]

# --------------------------------------------------------------- bosses ---

BOSS_DATA = {
    'warden': {
        'name': "The Warden of the Last Commute",
        'sub': "Sgt. Anya Volkov, who would not abandon her post",
        'intro': ["She was crowd control on the night of the sync.",
                  "Forty thousand people froze on her boulevard,",
                  "and she decided, forever, that they were her charge.",
                  "Her implant kept the order. It discarded the rest."],
        'defeat': "The Warden kneels. Somewhere in the static, a sergeant finally goes off duty.",
    },
    'chorister': {
        'name': "The Chorister",
        'sub': "First of the willing, voice of the choir",
        'intro': ["They queued for days to be synced first.",
                  "She sang at the ceremony as the Lattice closed.",
                  "She is singing still. The note has not ended.",
                  "She will not let you interrupt the hymn."],
        'defeat': "The note ends. Four thousand voices in the plaza exhale, three years late.",
    },
    'hound': {
        'name': "Patient Zero",
        'sub': "The first dog they uploaded, to see if it was safe",
        'defeat': "It stops circling at last. Good boy. Go on, now.",
        'intro': ["Before the city, before the volunteers,",
                  "Helix synced a search-and-rescue dog named Boris.",
                  "He has been looking for survivors for three years.",
                  "He keeps finding them. He keeps failing to save them."],
    },
    'archivist': {
        'name': "The Archivist",
        'sub': "Dr. Elias Mura, curator of the eternal second",
        'intro': ["He designed the Lattice to end grief.",
                  "When it closed, it needed one waking mind",
                  "to index the dream — and he volunteered.",
                  "He has read every life in this city. He likes yours.",
                  "He would like you to stop ruining the ending."],
        'defeat': "",
    },
}

BOSS_TAUNTS = {
    'archivist': [
        "You built the towers, Wren. You are the author of this peace.",
        "Four million people feel no pain. Name another city that can say so.",
        "Your backup is three years old. Which of us is the copy?",
    ],
}

# ---------------------------------------------------------------- NPCs ---

NPC_DIALOGUE = {
    'maya': {
        'name': "Maya Reyes, the Broadcaster",
        'lines': [
            ["Another Wakeful! Sit, the static's quiet near the beacon.",
             "I run the pirate signal — 88.1, The Insomniac Hour.",
             "Nobody's listening. I broadcast anyway. If even one",
             "implant glitches for one second and hears a human voice...",
             "that's a crack in the Stillness. Cracks spread."],
            ["You're the relay engineer, aren't you? Wren.",
             "Don't make that face. Nobody blames the hammer.",
             "...Okay, some of us blame the hammer a little.",
             "Prove us wrong. Climb the tower."],
            ["The Husks aren't gone, you know. I've watched them.",
             "Every loop, a barista pours the same latte — but last",
             "month she started drawing a heart in the foam.",
             "That's not in the recording. They're still in there."],
        ],
    },
    'cartographer': {
        'name': "Old Tam, the Cartographer",
        'lines': [
            ["Maps! Real paper. The Lattice can't edit paper.",
             "I walk the city and I write down what's TRUE.",
             "The boulevard loops left at the burnt bus. The market",
             "smells of ginger. The Warden owns the underpass.",
             "Cross her and you'd best know how to roll, child."],
            ["I had a wife. She's on a bench in Echo Park,",
             "reading page 212 of a novel, forever.",
             "I sit with her sometimes. I don't read ahead.",
             "It'd be rude, finishing a book before her."],
            ["The tower wants a toll. The Warden's badge, the",
             "Chorister's last note. Beat the city's grief into",
             "shape before the tower will open to you.",
             "That's not superstition. That's *architecture*."],
        ],
    },
}

# ------------------------------------------------------------- lore items ---

LORE_FRAGMENTS = [
    ("HELIX ONBOARDING PAMPHLET",
     ["\"Welcome to the Lattice! Side effects may include:",
      "shared dreams, déjà vu, the end of loneliness.",
      "Helix Dynamics is not liable for feelings of",
      "completion.\" — someone has burned the corners."]),
    ("RELAY WORK ORDER #7741 — SIGNED: C. WREN",
     ["Tower 12, Cathedral Plaza. Boost gain 40%.",
      "Note from engineer: 'Spec exceeds safety margin.",
      "Flagged twice. Overruled twice. Installing anyway.'",
      "Your handwriting. Your signature. Your tower."]),
    ("CHILD'S DRAWING, LAMINATED",
     ["A crayon family under a crayon sun.",
      "On the back, adult handwriting:",
      "'If you wake up before me, water the plants.'",
      "The fridge it was taken from is three blocks away."]),
    ("EMERGENCY BROADCAST TRANSCRIPT — OCT 9, 3:15 AM",
     ["'...not an attack. Repeat: this is not an attack.",
      "Citizens are unharmed. Citizens are... smiling.",
      "If you can hear this, you are unsynced. Do not",
      "approach the smiling. Do not break their routine.'"]),
    ("HUSK OBSERVATION LOG — MAYA'S HANDWRITING",
     ["Day 800: The flower vendor's loop is 41 seconds.",
      "Day 801: 41 seconds. Day 802: 43 seconds.",
      "She held the tulip out to the empty air two",
      "seconds longer. Like she was waiting for a buyer."]),
    ("HELIX INTERNAL MEMO — PROJECT LATTICE",
     ["'Closure event is not a malfunction. The mesh did",
      "exactly what four million people asked it nightly:",
      "make it stop hurting. We built a wish machine and",
      "the city wished. — E. Mura, do not circulate.'"]),
    ("A SOAKED PAPER MAP, OLD TAM'S WORK",
     ["The city in pencil, annotated and re-annotated.",
      "Echo Park bench circled in red, labelled 'HER'.",
      "Helix Tower drawn over and over, darker each pass,",
      "until the paper tore through."]),
    ("VOICEMAIL TRANSCRIPT — UNDELIVERED",
     ["'Hey, it's me. I know you're working the towers",
      "tonight. Big launch, end of loneliness, whatever.",
      "Come home after. I'll leave the porch light on.'",
      "Timestamp: October 9th, 3:11 AM."]),
    ("THE ARCHIVIST'S MARGINALIA",
     ["Found tucked in a library return slot:",
      "'Indexed life #2,206,114. A bad man, by the record.",
      "In the dream I gave him a kinder Tuesday.",
      "Who, exactly, is harmed?' The hand is steady."]),
    ("SERGEANT VOLKOV'S FINAL REPORT",
     ["'Crowd of 40,000 on Sleepwalker Blvd. All static.",
      "Requesting relief. Requesting relief. Requesting—'",
      "The rest is the same word, written nine hundred",
      "times, getting neater and neater."]),
]

# --------------------------------------------------------------- endings ---

ENDING_CHOICE = [
    "The Archivist is on his knees. The console behind him",
    "pulses with four million sleeping heartbeats.",
    "",
    "\"Last clerical error in the city,\" he says. \"Choose.\"",
    "",
    "SEVER the Lattice — wake them into grief, and rubble,",
    "and rain that finally falls forward. Let time resume.",
    "",
    "or INHERIT it — take his chair, curate the dream kindly,",
    "and let four million people stay loved, and stopped.",
]

ENDING_SEVER = [
    "You pull the relay you signed for out of the wall.",
    "",
    "The second ends.",
    "",
    "Four million people stumble out of October 9th and into",
    "the rain. Some scream. Some hold each other. The barista",
    "finishes the latte, and the foam heart is hers this time.",
    "On a bench in Echo Park, a woman turns to page 213,",
    "and an old man with paper maps begins, at last, to cry.",
    "",
    "The city will grieve everything at once now. It will be",
    "ugly, and slow, and real. Maya's signal goes on air to a",
    "city that can finally hear it: 'Good morning, Meridian.",
    "It's been three years. Let's start the show.'",
    "",
    "STILLWAKE — you chose the morning.",
]

ENDING_INHERIT = [
    "You sit down. The chair fits. It always would have —",
    "you built half of this machine before you ever held",
    "a wrench like a weapon.",
    "",
    "The dream takes you gently. You index a wedding, a",
    "recovery, ten thousand ordinary kitchens at dinnertime.",
    "You give the flower vendor a customer. You let the",
    "sergeant go off duty. You water the plants.",
    "",
    "Outside, a city of four million sleeps without pain,",
    "curated now by someone who knows what the signal cost.",
    "On 88.1, Maya broadcasts to the Stillness every night.",
    "You make sure that one barista, mid-loop, hums along.",
    "",
    "It is not living. But it is not nothing.",
    "",
    "STILLWAKE — you chose the dream.",
]

VICTORY_ARCHIVIST = [
    "The Archivist folds like a closing book.",
    "",
    "\"Oh,\" he says, with three years of relief, \"finally,",
    "an editor.\"",
]
