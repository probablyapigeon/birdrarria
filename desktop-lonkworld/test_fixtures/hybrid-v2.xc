application LonkWorld {
  "host_version": 1,
  "title": "LonkWorld",
  "starting_population": 5,
  "max_population": 20,
  "world": {
    "starting_population": 5,
    "max_population": 20,
    "initial_state": [
      0.5,
      0.5,
      0.2,
      0.3,
      0.1
    ],
    "initial_stats": [
      20,
      80
    ],
    "lifespan": [
      90,
      180
    ],
    "social_chance": 0.5,
    "rumor_mutation_chance": 0.2,
    "speech_chance": 0.25,
    "dream_chance": 0.12,
    "relationship_decay": 0.997,
    "rebirth_chance": 0.8,
    "arrival_chance": 0.05,
    "item_chance": 0.4,
    "inheritance_mutation": 8,
    "crush_chance": 0.1,
    "catchphrase_chance": 0.05,
    "recall_chance": 0.3
  },
  "bindings": {
    "energy": "state.0",
    "expectation": "state.1",
    "arousal": "state.2",
    "valence": "state.3",
    "error": "state.4",
    "power": "emotion.power",
    "courage": "emotion.courage",
    "wisdom": "emotion.wisdom",
    "masochism": "emotion.masochism",
    "joy": "emotion.joy",
    "anxiety": "emotion.anxiety",
    "aggression": "personality.aggression",
    "curiosity": "personality.curiosity",
    "worry": "personality.anxiety",
    "loyalty": "personality.loyalty",
    "trauma": "trauma",
    "dopamine": "dopamine"
  },
  "inputs": {
    "sensory": "uniform",
    "arousal_noise": "centered_uniform",
    "energy_noise": "centered_uniform",
    "attack_noise": "gumbel",
    "explore_noise": "gumbel",
    "think_noise": "gumbel",
    "ouch_noise": "gumbel",
    "idle_noise": "gumbel"
  },
  "title_for_player": "Momma Meat Wizard",
  "territories": {
    "The Big Rock": {
      "vibe": "immovable, judgmental, slightly warm",
      "bonus": {
        "courage": 3
      },
      "faction_bonus": "Bonk Battalion"
    },
    "The Loud Bush": {
      "vibe": "rustles aggressively for no reason",
      "bonus": {
        "curiosity": 4
      },
      "faction_bonus": "Chaos Choir"
    },
    "The Shiny Pit": {
      "vibe": "glimmers ominously, hums in F#",
      "bonus": {
        "loyalty": 3
      },
      "faction_bonus": "Shiny Seekers"
    },
    "The Moss Blanket": {
      "vibe": "soft, damp, emotionally supportive",
      "bonus": {
        "wisdom": 5
      },
      "faction_bonus": "Moss Goblins"
    },
    "The Unreasonable Clearing": {
      "vibe": "geometry makes no sense here",
      "bonus": {
        "masochism": 2
      },
      "faction_bonus": "The Unreasonable Ones"
    },
    "The Screaming Meadow": {
      "vibe": "the grass yells compliments",
      "bonus": {
        "power": 3
      },
      "faction_bonus": null
    }
  },
  "items": {
    "Cursed Spoon": {
      "effect": {
        "wisdom": -2,
        "curiosity": 4
      },
      "vibe": "it vibrates ominously"
    },
    "Shiny Pebble": {
      "effect": {
        "loyalty": 3
      },
      "vibe": "glimmers with suspicious enthusiasm"
    },
    "Angry Stick": {
      "effect": {
        "aggression": 4
      },
      "vibe": "seems upset about something"
    },
    "Moss Cube": {
      "effect": {
        "wisdom": 3,
        "anxiety": -2
      },
      "vibe": "soft, damp, cube-shaped"
    },
    "Goblin Tooth (Probably)": {
      "effect": {
        "courage": 2
      },
      "vibe": "warm… too warm"
    },
    "Forbidden Berry": {
      "effect": {
        "power": 3,
        "wisdom": -1
      },
      "vibe": "glows faintly"
    },
    "Screaming Pebble": {
      "effect": {
        "anxiety": 3
      },
      "vibe": "yells when touched"
    },
    "Pocket Void": {
      "effect": {
        "curiosity": 5,
        "loyalty": -2
      },
      "vibe": "a tiny portable nothingness"
    },
    "Bent Fork of Destiny": {
      "effect": {
        "power": 4
      },
      "vibe": "crooked but confident"
    },
    "Suspicious Egg": {
      "effect": {
        "masochism": 2
      },
      "vibe": "it wiggles occasionally"
    },
    "Haunted Leaf": {
      "effect": {
        "anxiety": 2,
        "wisdom": 1
      },
      "vibe": "rustles even indoors"
    },
    "Shiny Rock (Extra Shiny)": {
      "effect": {
        "loyalty": 5
      },
      "vibe": "blindingly fabulous"
    },
    "Goblin Coupon": {
      "effect": {
        "courage": 1
      },
      "vibe": "expired decades ago"
    },
    "Wiggly Stick": {
      "effect": {
        "curiosity": 2
      },
      "vibe": "wiggles on its own schedule"
    },
    "Bone of Unknown Origin": {
      "effect": {
        "power": 2,
        "anxiety": 1
      },
      "vibe": "mysterious and rude"
    },
    "Soggy Sock": {
      "effect": {
        "masochism": 3
      },
      "vibe": "wet. always wet."
    },
    "Miniature Door": {
      "effect": {
        "wisdom": 2
      },
      "vibe": "leads nowhere but feels important"
    },
    "Sparkling Dust": {
      "effect": {
        "loyalty": 1,
        "curiosity": 1
      },
      "vibe": "gets everywhere"
    },
    "Goblin Trading Card": {
      "effect": {
        "courage": 2
      },
      "vibe": "rare holographic edition"
    },
    "Suspicious Cube": {
      "effect": {
        "power": 1,
        "curiosity": 3
      },
      "vibe": "buzzes like it knows secrets"
    }
  },
  "name_start": [
    "Scr",
    "Blib",
    "Bonk",
    "Grub",
    "Snar",
    "Plib",
    "Krub",
    "Yib",
    "Trun",
    "Mog",
    "Wib",
    "Frub",
    "Glo",
    "Spro",
    "Nib",
    "Zag",
    "Dro",
    "Clum",
    "Bree",
    "Hog"
  ],
  "name_end": [
    "blo",
    "bble",
    "dunk",
    "glo",
    "fip",
    "wunk",
    "sprag",
    "mop",
    "doodle",
    "snip",
    "gunk",
    "wobble",
    "florp",
    "snorf",
    "tunk",
    "zibble",
    "crunk"
  ],
  "factions": [
    "Moss Goblins",
    "Shiny Seekers",
    "Chaos Choir",
    "Bonk Battalion",
    "Mushroom Union"
  ],
  "dialogue": {
    "fight": [
      "square up, leaf boy!",
      "I challenge thee to a BONK-OFF!",
      "prepare for maximum slapstick!",
      "violence but silly!",
      "I swing with the power of poor decisions!"
    ],
    "defeat": [
      "I have been bonked… emotionally.",
      "the air cheated!",
      "I fall with dramatic flair!",
      "I regret everything!",
      "ow. my pride. and my face."
    ],
    "victory": [
      "I am the bonk champion!",
      "witness my chaotic glory!",
      "I win! I win! I win!",
      "the prophecy foretold my triumph!",
      "SKREEEEE victory screech!"
    ],
    "rivalry": [
      "your face is symmetrical and I hate it!",
      "you smell like reasonable decisions!",
      "I bite you but gently!",
      "your vibes are uneven!",
      "you look like a mossless rock!"
    ],
    "general": [
      "wooOOOAAAHH buddy!!",
      "I did a bad thing on purpose.",
      "I found a shiny and now I'm emotionally attached.",
      "I am speed. But only emotionally.",
      "I have made a choice and it was wrong.",
      "the moon owes me rent.",
      "your shadow tastes like questions.",
      "time tripped over itself again.",
      "the sky blinked at me twice.",
      "I saw a dream fall out of a tree.",
      "SKREEEEEE.",
      "bonk bonk BONK.",
      "I crave chaos and soup.",
      "I ate a rock and now I know secrets.",
      "I am the chair now."
    ],
    "greeting": [
      "hi {title}!! I missed your vibes.",
      "{title}, the forest screamed your name again.",
      "behold! I have arrived to cause problems.",
      "{title}, I have concerns. Mostly about me.",
      "the moss whispered you were coming."
    ],
    "item": [
      "SHINY ACQUIRED: {item}!",
      "this {item} concerns me deeply.",
      "I licked the {item}. it is mine now.",
      "the {item} whispered at me."
    ],
    "think": [
      "thinks very hard about nothing."
    ],
    "ouch": [
      "pokes themselves experimentally."
    ],
    "idle": [
      "stands still, overwhelmed."
    ],
    "dream": [
      "drifts through soft colors.",
      "relives something confusing."
    ],
    "catchphrase": [
      "shiny time.",
      "I crave chaos and soup.",
      "bonk bonk BONK."
    ],
    "crush": [
      "your voice makes my brain do flips.",
      "I collected a shiny for you.",
      "I think you are sparkly.",
      "I wrote a poem about you but then I ate it."
    ],
    "hug": [
      "softness acquired.",
      "hugs you back with chaotic enthusiasm."
    ],
    "praise": [
      "I am a bean??",
      "wiggles proudly.",
      "beams with chaotic joy."
    ]
  },
  "keywords": {
    "positive": [
      "love",
      "good",
      "nice",
      "friend",
      "thanks",
      "happy"
    ],
    "negative": [
      "hate",
      "bad",
      "stupid",
      "ugly",
      "hurt",
      "angry"
    ],
    "friend": [
      "friend"
    ]
  },
  "release": "2.0",
  "compatible_v1_hashes": [
    "185a8912ae6181f0fa61068d967e1459edc63ffcb0248d1a473b010cdf56ed71"
  ],
  "culture": {
    "max_words": 256,
    "max_phrases": 64,
    "max_links": 768,
    "max_sentence_words": 14,
    "innovation_chance": 0.12,
    "learned_speech_chance": 0.85,
    "reflection_chance": 0.25,
    "conversation_chance": 0.9,
    "thought_history": 12
  },
  "society": {
    "apprentice_words": 1,
    "apprentice_conversations": 1,
    "storyteller_words": 3,
    "storyteller_conversations": 3,
    "graduate_words": 12,
    "graduate_conversations": 6,
    "partner_threshold": 18,
    "bond_chance": 0.35,
    "colony_min_members": 2,
    "colony_prefixes": [
      "Moss",
      "Shiny",
      "Moon",
      "Soup",
      "Dream",
      "Pebble"
    ],
    "colony_suffixes": [
      "Nest",
      "Grove",
      "Cuddle Commune",
      "Choir",
      "Garden"
    ],
    "colony_join_threshold": 4,
    "affection_gain": 3,
    "affection_decay": 0.999,
    "chronicle_limit": 256
  }
}

// LonkWorld XC application 1.0.
// Edit the application declaration above to change names, dialogue and world content.
// Edit this native xembra model to change emotional dynamics and behavior.
// Single-field updates below are lowered to ordered XC vector updates by the host.
// Host random inputs use the saved world's seeded RNG; the XC model is deterministic
// for those inputs. Gumbel noise + argmax produces stochastic action selection.

xembra LonkMind version 1.0 {
  seed = 2026
  state Psi {
    energy: real = 0.5
    expectation: real = 0.5
    arousal: real = 0.2
    valence: real = 0.3
    error: real = 0.1
    power: real = 50
    courage: real = 50
    wisdom: real = 50
    masochism: real = 0
    joy: real = 50
    anxiety: real = 50
    aggression: real = 50
    curiosity: real = 50
    worry: real = 50
    loyalty: real = 50
    trauma: real = 0
    dopamine: real = 50
    sensory: real = 0.5
    arousal_noise: real = 0
    energy_noise: real = 0
    attack_noise: real = 0
    explore_noise: real = 0
    think_noise: real = 0
    ouch_noise: real = 0
    idle_noise: real = 0
    trauma_enabled: real = 1
  }
  memory Episodes {
    capacity = 24
    decay = 0.06
    top_k = 4
    similarity_weight = 0.3
    salience_weight = 0.4
    recency_weight = 0.3
  }
  observation Moment {
    vector = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    salience = 0.4
  }
  observation Kindness {
    vector = [0,0,0,0.12,-0.05,0,0,0,0,3,-2,0,0,-1,2,0,2,0,0,0,0,0,0,0,0,0]
    salience = 0.75
  }
  observation Threat {
    vector = [0,0,0.15,-0.1,0.15,0,-1,0,0,-2,3,0,0,2,0,1,0,0,0,0,0,0,0,0,0,0]
    salience = 0.85
  }
  actions { ATTACK EXPLORE THINK OUCH IDLE }
  policy Instinct {
    score ATTACK = power / 100 + arousal + aggression / 100 + attack_noise
    score EXPLORE = courage / 100 + curiosity / 100 + joy / 200 + explore_noise
    score THINK = wisdom / 100 + (1 - error) + loyalty / 200 + think_noise
    score OUCH = masochism / 100 + error + worry / 100 + ouch_noise
    score IDLE = 0.3 + (1 - energy) + anxiety / 200 + idle_noise
    select argmax
  }
  cycle {
    error <- clamp(error * 0.95, 0, 1)
    arousal <- clamp(arousal + 0.1 * (sensory - arousal) + 0.2 * arousal_noise, 0, 1)
    valence <- clamp(valence + 0.1 * (1 - error) - 0.05 * arousal + 0.02 * recall_signal("Episodes", "Kindness") - 0.02 * recall_signal("Episodes", "Threat"), 0, 1)
    energy <- clamp(energy + 0.1 * (valence - energy) + 0.05 * energy_noise, 0, 1)
    expectation <- clamp(expectation + 0.05 * (energy - expectation), 0, 1)
    power <- 100 * energy
    courage <- 100 * (1 - norm([energy - expectation]))
    wisdom <- 100 * (1 - error)
    masochism <- 100 * arousal
    joy <- clamp(0.9 * joy + 10 * valence, 0, 100)
    anxiety <- clamp(0.9 * anxiety + 10 * error, 0, 100)
    action <- Instinct(Psi)
  }
  event Tick { observe Moment cycle 1 }
  event birth { observe Moment remember Episodes }
  event hear_player { observe Moment remember Episodes }
  event hear { observe Moment remember Episodes }
  event hear_positive {
    observe Kindness
    joy <- clamp(joy + 3, 0, 100)
    valence <- clamp(valence + 0.08, 0, 1)
    error <- clamp(error - 0.03, 0, 1)
    remember Episodes
  }
  event hear_negative {
    observe Threat
    anxiety <- clamp(anxiety + 3, 0, 100)
    error <- clamp(error + 0.08, 0, 1)
    worry <- clamp(worry + 1, 0, 100)
    remember Episodes
  }
  event hear_friend { observe Kindness loyalty <- clamp(loyalty + 2, 0, 100) remember Episodes }
  event attack { observe Moment aggression <- clamp(aggression + 2, 0, 100) dopamine <- clamp(dopamine + 5, 0, 100) }
  event explore { observe Moment curiosity <- clamp(curiosity + 2, 0, 100) }
  event think { observe Moment wisdom <- clamp(wisdom + 2, 0, 100) error <- clamp(error - 0.02, 0, 1) }
  event ouch {
    observe Threat
    error <- clamp(error + 0.1, 0, 1)
    arousal <- clamp(arousal + 0.03, 0, 1)
    trauma <- clamp(trauma + 2 * trauma_enabled, 0, 100)
    remember Episodes
  }
  event idle { observe Moment energy <- clamp(energy + 0.03, 0, 1) arousal <- clamp(arousal - 0.02, 0, 1) }
  event territory { observe Moment remember Episodes }
  event find_item { observe Moment dopamine <- clamp(dopamine + 3, 0, 100) remember Episodes }
  event win_duel { observe Moment aggression <- clamp(aggression + 2, 0, 100) power <- clamp(power + 3, 0, 100) }
  event lose_duel { observe Threat worry <- clamp(worry + 2, 0, 100) courage <- clamp(courage - 2, 0, 100) }
  event hurt {
    observe Threat
    error <- clamp(error + 0.15, 0, 1)
    arousal <- clamp(arousal + 0.045, 0, 1)
    trauma <- clamp(trauma + trauma_enabled, 0, 100)
    remember Episodes
  }
  event social { observe Kindness loyalty <- clamp(loyalty + 2, 0, 100) joy <- clamp(joy + 1, 0, 100) }
  event nightmare { observe Threat worry <- clamp(worry + 5, 0, 100) courage <- clamp(courage - 5, 0, 100) trauma <- clamp(trauma - 5, 0, 100) remember Episodes }
  event dream { observe Kindness dopamine <- clamp(dopamine + 10, 0, 100) loyalty <- clamp(loyalty + 3, 0, 100) trauma <- clamp(trauma - 5, 0, 100) remember Episodes }
}
