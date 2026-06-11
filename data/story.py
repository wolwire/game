"""STILLWAKE — story, lore, dialogue.

THE WORLD
---------
The free city of Meridian, in the year of its fourth bell. Three years ago the
Carillon Guild finished THE CARILLON: a crown of brass resonance bells hung
through every tower of the city, tuned so finely that every mind in earshot
would ring in sympathy — grief shared until it dissolved, memory held in
bronze forever. "The end of loneliness," the criers called it.

At three hours past midnight on the ninth of October, the Carillon struck
once — and never finished the stroke. Every soul in earshot locked into a
single recurring instant. The city stopped: not dead, but *paused*, living
its last second over and over. Survivors call it THE STILLNESS.

The belled citizens — the TOLLED — walk their final loops, hostile to anything
that moves out of step, because to them, you are the wrong note. The few who
were deaf to the bell — the WAKEFUL — cannot be held by it, and cannot be
released: when a Wakeful dies, the bronze remembers them, and a resonance
shard rings them back at the nearest crystal — minus what they carried.
Memory has become coin. The Wakeful trade in SHARDS: crystallized seconds of
other people's lives, shed by the Tolled when they fall.

You are CALLE WREN, the bell-founder's engineer. You cast the bells. You
signed the tuning orders. You woke on the floor of the Foundry Yard with a
cracked ear, a founder's hammer, and three years of ringing where the guilt
should be. Somewhere above the city, in the Carillon Spire, the ARCHIVIST —
the one mind the bell chose to stay awake and keep the ledger of everyone's
forever — is still writing. You are going to climb up there and make a choice
nobody elected you to make. Again.
"""

TITLE = "STILLWAKE"
SUBTITLE = "a tale of the Stillness"
INTRO_TITLE = "THE NINTH OF OCTOBER, THREE HOURS PAST MIDNIGHT"

INTRO = [
    "MERIDIAN — three years into the Stillness.",
    "",
    "The Carillon struck once and never finished the",
    "stroke. Forty thousand people stopped. Mid-step.",
    "Mid-kiss. Mid-sentence. The city has been living",
    "that second ever since.",
    "",
    "You are Calle Wren. You cast the bells that carry",
    "the note. Your ear cracked the night it mattered,",
    "and the Carillon has been trying to correct that",
    "clerical error ever since.",
    "",
    "It cannot keep you. It will not release you.",
    "Every time you die, a resonance shard rings you back.",
    "",
    "Climb to the Carillon Spire. Find the Archivist.",
    "End the longest second in the city's history.",
]

CONTROLS = [
    "W A S D — move        SHIFT — sprint",
    "SPACE — dodge roll (invincibility frames)",
    "J — light attack      K — heavy attack",
    "L — parry             Q — stim (heal)",
    "E — interact          R — switch weapon",
    "TAB — lock-on         M — map      ESC — pause",
    "",
    "Rest at the violet RESONANCE SHARDS to heal,",
    "refill stims and level up — resting revives",
    "the dead. Death drops your shards where you",
    "fell. Return to the echo to reclaim them.",
]

AREA_NAMES = {
    'hub':      "The Foundry Yard",
    'downtown': "Sleepwalker Rows",
    'market':   "Night Market of the Last Second",
    'park':     "Echo Garden",
    'suburbs':  "The Long Saturday",
    'docks':    "Graveyard of Masts",
    'overpass': "The Unfinished Mile",
    'plaza':    "Cathedral Plaza",
    'tower':    "The Carillon Spire",
}

AREA_DESC = {
    'hub':      "Where you woke. The forge in the yard is still warm. It is always still warm.",
    'downtown': "Burgher crowds walk their last errand on a loop. Do not break their stride.",
    'market':   "The stalls still smell of ginger and rain. The vendors still smile. Keep moving.",
    'park':     "The strollers never tire. The kept beasts remember being loved, and it has made them cruel.",
    'suburbs':  "Lawns scythed to the second. Wells mid-draw. Four hundred families, one shared dream of Saturday.",
    'docks':    "The ships froze mid-unlading. Cargo hangs in the rigging like held breath.",
    'overpass': "They were still raising it when the city stopped. It leads nowhere, beautifully.",
    'plaza':    "Where the faithful gathered to be belled first. The Chorister sings their gratitude.",
    'tower':    "The Guild's high seat. The note is so dense here that the rain falls in loops.",
}

GRACE_MESSAGES = [
    "The shard hums your frequency. You are, briefly, expected.",
    "Resonance restored. The Carillon notes your survival with mild disappointment.",
    "You rest. Somewhere in bronze, a copy of you is updated and filed.",
    "The ringing recedes. The dead get back up. That is the deal.",
    "Three years of warmth left in this crystal. You tuned it to last.",
]

DEATH_MESSAGES = [
    "THE NOTE TAKES YOU",
    "RUNG BACK...",
    "THE BRONZE REMEMBERS YOU",
    "OUT OF TUNE",
    "RESTORED FROM BRONZE — LOSSY",
]

# --------------------------------------------------------------- bosses ---

BOSS_DATA = {
    'warden': {
        'name': "The Warden of the Last Gate",
        'sub': "Captain Anya Volkov, who would not abandon her post",
        'intro': ["She was watch-captain on the night of the bell.",
                  "Ten thousand pilgrims froze on her mile, and she",
                  "decided, forever, that they were her charge.",
                  "The note kept the order. It discarded the rest.",
                  "What stands at the gate now wears her horns of office."],
        'defeat': "The Warden kneels. Somewhere in the ringing, a captain finally goes off watch.",
    },
    'chorister': {
        'name': "The Chorister",
        'sub': "First of the willing, voice of the choir",
        'intro': ["They queued for days to be belled first.",
                  "She sang at the consecration as the Carillon closed.",
                  "She is singing still. The note has not ended.",
                  "She will not let you interrupt the hymn."],
        'defeat': "The note ends. Four thousand voices in the plaza exhale, three years late.",
    },
    'hound': {
        'name': "The First Subject",
        'sub': "The beast they belled, to see if it was safe",
        'intro': ["Before the city, before the volunteers,",
                  "the Guild hung a bell on a burrowing beast",
                  "and rang it once, to see what would remain.",
                  "It has been digging for the way out for three years.",
                  "It keeps finding Echo Garden. It keeps beginning again."],
        'defeat': "It stops digging at last. Down, now. Rest. Good.",
    },
    'archivist': {
        'name': "The Archivist",
        'sub': "Brother Elias Mura, keeper of the eternal second",
        'intro': ["He designed the Carillon to end grief.",
                  "When it closed, it needed one waking mind",
                  "to keep the ledger of the dream — and he volunteered.",
                  "He has read every life in this city. He likes yours.",
                  "He would like you to stop ruining the ending."],
        'defeat': "",
    },
}

# ---------------------------------------------------------------- NPCs ---

NPC_DIALOGUE = {
    'maya': {
        'name': "Maya Reyes, the Crier",
        'lines': [
            ["Another Wakeful! Sit, the ringing's quiet near the shard.",
             "I walk the walls at night and call the hours.",
             "Nobody hears me. I call them anyway. If even one",
             "of the Tolled stirs for one second at a human voice...",
             "that's a crack in the Stillness. Cracks spread."],
            ["You're the founder's engineer, aren't you? Wren.",
             "Don't make that face. Nobody blames the hammer.",
             "...Okay, some of us blame the hammer a little.",
             "Prove us wrong. Climb the Spire."],
            ["The Tolled aren't gone, you know. I've watched them.",
             "Every loop, the flower girl offers the same tulip —",
             "but last month she held it out two seconds longer.",
             "That's not in the bell. They're still in there."],
        ],
    },
    'cartographer': {
        'name': "Old Tam, the Cartographer",
        'lines': [
            ["Maps! Real vellum. The bell can't ring vellum.",
             "I walk the city and I write down what's TRUE.",
             "The Rows loop left at the burnt cart. The market",
             "smells of ginger. The Warden owns the Mile.",
             "Cross her and you'd best know how to roll, child."],
            ["I had a wife. She's on a bench in Echo Garden,",
             "reading page 212 of a romance, forever.",
             "I sit with her sometimes. I don't read ahead.",
             "It'd be rude, finishing a book before her."],
            ["The Spire wants a toll. The Warden's watch, the",
             "Chorister's last note. Quiet the city's grief",
             "before the gate will open to you.",
             "That's not superstition. That's *acoustics*."],
        ],
    },
}

# ------------------------------------------------------------- lore items ---

LORE_FRAGMENTS = [
    ("GUILD CONSECRATION PAMPHLET",
     ["\"Welcome to the Carillon! Effects may include:",
      "shared dreams, the end of loneliness, a lightness",
      "where the grief was. The Guild is not liable for",
      "feelings of completion.\" Someone burned the corners."]),
    ("TUNING ORDER #7741 — SIGNED: C. WREN",
     ["Bell twelve, Cathedral Plaza. Raise the gain a",
      "fourth. Note from engineer: 'Pitch exceeds the safe",
      "interval. Flagged twice. Overruled twice. Casting",
      "anyway.' Your handwriting. Your signature. Your bell."]),
    ("CHILD'S DRAWING, WAXED AGAINST RAIN",
     ["A charcoal family under a charcoal sun.",
      "On the back, adult handwriting:",
      "'If you wake before me, water the garden.'",
      "The kitchen it was taken from is three streets away."]),
    ("WATCH TRANSCRIPT — NINTH OF OCTOBER",
     ["'...not an attack. Repeat: this is not an attack.",
      "Citizens are unharmed. Citizens are... smiling.",
      "If you can hear this crier, you are unbelled. Do not",
      "approach the smiling. Do not break their round.'"]),
    ("OBSERVATIONS — MAYA'S HANDWRITING",
     ["Day 800: The flower girl's loop is 41 seconds.",
      "Day 801: 41 seconds. Day 802: 43 seconds.",
      "She held the tulip out to the empty air two",
      "seconds longer. Like she was waiting for a buyer."]),
    ("GUILD MEMORANDUM — THE CARILLON",
     ["'The closure is not a flaw in the casting. The bell",
      "did exactly what forty thousand people asked it",
      "nightly: make it stop hurting. We built a wishing",
      "bell and the city wished. — E. Mura. Do not copy.'"]),
    ("A RAIN-SOAKED MAP, OLD TAM'S WORK",
     ["The city in pencil, annotated and re-annotated.",
      "A bench in Echo Garden circled in red, marked 'HER'.",
      "The Carillon Spire drawn over and over, darker each",
      "pass, until the vellum tore through."]),
    ("LETTER, NEVER SENT",
     ["'It's me. I know you're working the bells tonight.",
      "Great consecration, end of loneliness, whatever.",
      "Come home after. I'll leave the lamp in the window.'",
      "Dated: the ninth of October."]),
    ("THE ARCHIVIST'S MARGINALIA",
     ["Found tucked in a library return-slot:",
      "'Ledgered life #38,114. A cruel man, by the record.",
      "In the dream I gave him a kinder Tuesday.",
      "Who, exactly, is harmed?' The hand is steady."]),
    ("CAPTAIN VOLKOV'S FINAL REPORT",
     ["'Crowd of ten thousand on the pilgrim mile. All",
      "still. Requesting relief. Requesting relief. Requ—'",
      "The rest is the same word, written nine hundred",
      "times, getting neater and neater."]),
]

# --------------------------------------------------------------- endings ---

ENDING_CHOICE = [
    "The Archivist is on his knees. The great bell above",
    "you holds forty thousand sleeping heartbeats in bronze.",
    "",
    "\"Last clerical error in the city,\" he says. \"Choose.\"",
    "",
    "CRACK the bell — wake them into grief, and rubble,",
    "and rain that finally falls forward. Let time resume.",
    "",
    "or INHERIT it — take his ledger, keep the dream kindly,",
    "and let forty thousand people stay loved, and stopped.",
]

ENDING_SEVER = [
    "You swing the hammer you signed for into the bell",
    "you cast.",
    "",
    "The second ends.",
    "",
    "Forty thousand people stumble out of the ninth of",
    "October and into the rain. Some scream. Some hold each",
    "other. The flower girl sells the tulip, and the coin is",
    "hers this time. On a bench in Echo Garden, a woman",
    "turns to page 213, and an old man with vellum maps",
    "begins, at last, to cry.",
    "",
    "The city will grieve everything at once now. It will be",
    "ugly, and slow, and real. At dawn Maya climbs the wall",
    "and calls the hour to a city that can finally hear her:",
    "'Good morning, Meridian. It's been three years.'",
    "",
    "STILLWAKE — you chose the morning.",
]

ENDING_INHERIT = [
    "You sit down at the ledger. The chair fits. It always",
    "would have — you cast half of this machine before you",
    "ever held a hammer like a weapon.",
    "",
    "The dream takes you gently. You ledger a wedding, a",
    "recovery, ten thousand ordinary kitchens at supper.",
    "You give the flower girl a buyer. You let the captain",
    "go off watch. You water the garden.",
    "",
    "Outside, a city of forty thousand sleeps without pain,",
    "kept now by someone who knows what the note cost.",
    "Each night Maya calls the hours to the Stillness.",
    "You make sure that one flower girl, mid-loop, hums along.",
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
