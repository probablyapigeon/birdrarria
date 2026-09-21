"""Finite social development, mutual affection and persistent little communities."""

import math


DEFAULTS = {
    'apprentice_words': 1, 'storyteller_words': 3,
    'apprentice_conversations': 1, 'storyteller_conversations': 3,
    'graduate_words': 12, 'graduate_conversations': 6,
    'partner_threshold': 18, 'bond_chance': .35, 'colony_min_members': 2,
    'colony_prefixes': ['Moss', 'Shiny', 'Moon'],
    'colony_suffixes': ['Nest', 'Grove', 'Cuddle Commune'],
    'colony_join_threshold': 4, 'affection_gain': 3,
    'affection_decay': .999, 'chronicle_limit': 256, 'familiar_friend_chance': .7,
}


def _number(world, key, low=0, high=1000000):
    value = world.config.get('society', {}).get(key, DEFAULTS[key])
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        value = DEFAULTS[key]
    return max(low, min(high, value))


def init_world(world):
    world.colonies = {}
    world.chronicle = []
    world.next_colony_id = 1


def init_lonk(lonk):
    lonk.social = {
        'stage': 'hatchling', 'graduated_at': None, 'colony_id': None,
        'partners': [], 'affection': {}, 'conversations': 0, 'thoughts': [],
        'player_affection': 0, 'parents': [],
    }


def _record(world, text, kind, lonks=()):
    world.chronicle.append({'tick': world.tick, 'kind': kind,
                            'text': text[:500], 'lonks': [x.uid for x in lonks]})
    del world.chronicle[:-int(_number(world, 'chronicle_limit', 1, 1024))]
    for lonk in lonks:
        lonk.remember(text)
    print(text)


def on_hear(lonk, speaker=None, player=False):
    if not lonk.alive:
        return
    social = lonk.social
    social['conversations'] = min(1000000, social['conversations'] + 1)
    gain = _number(lonk.world, 'affection_gain', 0, 100)
    if player:
        social['player_affection'] = min(100, social['player_affection'] + gain)
    if speaker is not None and speaker is not lonk and speaker.alive:
        affinity = social['affection']
        affinity[speaker.uid] = min(100, affinity.get(speaker.uid, 0) + gain)
        maybe_bond(lonk, speaker)


def maybe_bond(a, b):
    if a is b or not a.alive or not b.alive or a.world is not b.world:
        return False
    if b.uid in a.social['partners']:
        return False
    threshold = _number(a.world, 'partner_threshold', 0, 100)
    if min(a.social['affection'].get(b.uid, 0), b.social['affection'].get(a.uid, 0)) < threshold:
        return False
    if a.world.rng.random() >= _number(a.world, 'bond_chance', 0, 1):
        return False
    a.social['partners'].append(b.uid)
    if a.uid not in b.social['partners']:
        b.social['partners'].append(a.uid)
    _record(a.world, f'{a.name} and {b.name} become sweethearts and share a happy cuddle.',
            'partnership', (a, b))
    return True


def develop(lonk):
    if not lonk.alive:
        return
    social, world = lonk.social, lonk.world
    if social['graduated_at'] is not None:
        social['stage'] = 'graduate'
        return
    words = len(getattr(lonk, 'linguistics', {}).get('tokens', lonk.vocabulary))
    if (words >= _number(world, 'graduate_words') and
            social['conversations'] >= _number(world, 'graduate_conversations')):
        social['stage'] = 'graduate'
        social['graduated_at'] = world.tick
        _record(world, f'{lonk.name} graduates! A little storyteller is ready to help a colony grow.',
                'graduation', (lonk,))
    elif (words >= _number(world, 'storyteller_words') and
          social['conversations'] >= _number(world, 'storyteller_conversations')):
        social['stage'] = 'storyteller'
    elif (words >= _number(world, 'apprentice_words') and
          social['conversations'] >= _number(world, 'apprentice_conversations')):
        social['stage'] = 'apprentice'


def _compatible(a, b):
    return min(a.social['affection'].get(b.uid, 0),
               b.social['affection'].get(a.uid, 0)) >= _number(a.world, 'colony_join_threshold', 0, 100)


def _name(world, key):
    options = world.config.get('society', {}).get(key, DEFAULTS[key])
    if not isinstance(options, list):
        options = DEFAULTS[key]
    options = [x[:80] for x in options if isinstance(x, str) and x.strip()]
    return world.rng.choice(options or DEFAULTS[key])


def society_tick(world):
    """One reciprocal conversation per community; all loops are population bounded."""
    living = [x for x in world.lonks if x.alive]
    by_uid = {x.uid: x for x in living}
    decay = _number(world, 'affection_decay', 0, 1)
    for lonk in living:
        lonk.social['affection'] = {uid: score * decay for uid, score in lonk.social['affection'].items()
                                   if uid in by_uid and uid != lonk.uid}
        lonk.social['partners'] = [uid for uid in lonk.social['partners'] if uid in by_uid]
    for cid, colony in world.colonies.items():
        colony['members'] = [x.uid for x in living if x.social['colony_id'] == cid]
        if not colony['members'] and colony['archived_at'] is None:
            colony['archived_at'] = world.tick
    groups = {}
    for lonk in living:
        cid = lonk.social['colony_id']
        if cid not in world.colonies or world.colonies[cid]['archived_at'] is not None:
            lonk.social['colony_id'] = cid = None
        groups.setdefault(cid, []).append(lonk)
    for members in groups.values():
        if len(members) < 2:
            continue
        chance = world.config.get('culture', {}).get('conversation_chance', .9)
        if type(chance) not in (int, float) or not math.isfinite(chance):
            chance = .9
        if world.rng.random() >= max(0, min(1, chance)):
            continue
        a = world.rng.choice(members)
        others = [x for x in members if x is not a]
        # Familiar friends reconnect, while new friendships remain possible.
        b = (max(others, key=lambda x: a.social['affection'].get(x.uid, 0))
             if world.rng.random() < _number(world, 'familiar_friend_chance', 0, 1)
             else world.rng.choice(others))
        if a.territory != b.territory:
            print(f'{a.name} visits {b.name} for a little conversation.')
        a.speak(target=b)
        b.speak(target=a)
    for lonk in living:
        develop(lonk)
    for lonk in living:
        if lonk.social['colony_id'] is not None or lonk.social['graduated_at'] is None:
            continue
        colony = next((c for c in world.colonies.values() if c['archived_at'] is None and
                       any(_compatible(lonk, by_uid[uid]) for uid in c['members'] if uid in by_uid)), None)
        if colony is not None:
            lonk.social['colony_id'] = colony['id']
            colony['members'].append(lonk.uid)
            _record(world, f'{lonk.name} joins {colony["name"]}.', 'colony_join', (lonk,))
            continue
        friends = [x for x in living if x is not lonk and x.social['colony_id'] is None
                   and x.social['graduated_at'] is not None and _compatible(lonk, x)]
        minimum = int(_number(world, 'colony_min_members', 2, 1000))
        if len(friends) + 1 < minimum:
            continue
        founders = [lonk] + friends[:minimum - 1]
        cid = f'colony-{world.next_colony_id}'
        world.next_colony_id += 1
        name = f'{_name(world, "colony_prefixes")} {_name(world, "colony_suffixes")}'
        world.colonies[cid] = {'id': cid, 'name': name, 'founded_at': world.tick,
                               'founders': [x.uid for x in founders],
                               'members': [x.uid for x in founders], 'archived_at': None}
        for member in founders:
            member.social['colony_id'] = cid
        _record(world, f'{" and ".join(x.name for x in founders)} found {name}!', 'colony_founded', founders)
    archived = [cid for cid, c in world.colonies.items() if c['archived_at'] is not None]
    for cid in archived[:-64]:
        del world.colonies[cid]


def inherit(parent, baby):
    init_lonk(baby)
    baby.social['parents'] = [parent.uid]
    baby.social['colony_id'] = parent.social['colony_id']
    colony = baby.world.colonies.get(baby.social['colony_id'])
    if colony is not None and baby.uid not in colony['members']:
        colony['members'].append(baby.uid)


def on_departure(world, lonk):
    for other in world.lonks:
        if other is not lonk and lonk.uid in other.social['partners']:
            other.social['partners'].remove(lonk.uid)
            other.remember(f'I remember the happy cuddles I shared with {lonk.name}.')
    lonk.social['partners'] = []
    colony = world.colonies.get(lonk.social['colony_id'])
    if colony is not None and lonk.uid in colony['members']:
        colony['members'].remove(lonk.uid)
        if not colony['members']:
            colony['archived_at'] = world.tick


def validate_world(world):
    """Read-only persistence validation; historic founder/parent IDs may be absent."""
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(isinstance(world.colonies, dict) and isinstance(world.chronicle, list), 'Invalid society history')
    require(type(world.next_colony_id) is int and world.next_colony_id >= 1, 'Invalid colony sequence')
    for entry in world.chronicle:
        require(isinstance(entry, dict) and isinstance(entry.get('text'), str)
                and isinstance(entry.get('kind'), str) and isinstance(entry.get('lonks'), list)
                and type(entry.get('tick')) is int and 0 <= entry['tick'] <= world.tick,
                'Invalid chronicle entry')
    by_uid = {x.uid: x for x in world.lonks}
    for lonk in world.lonks:
        social = lonk.social
        require(isinstance(social, dict) and set(init_keys()).issubset(social), 'Invalid social schema')
        require(social['stage'] in ('hatchling', 'apprentice', 'storyteller', 'graduate'), 'Invalid learning stage')
        require(type(social['conversations']) is int and social['conversations'] >= 0, 'Invalid conversation count')
        require(isinstance(social['affection'], dict), 'Invalid affection map')
        for score in list(social['affection'].values()) + [social['player_affection']]:
            require(type(score) in (int, float) and math.isfinite(score) and 0 <= score <= 100, 'Invalid affection')
        for key in ('partners', 'parents', 'thoughts'):
            require(isinstance(social[key], list), f'Invalid {key}')
        require(all(isinstance(uid, str) for uid in social['partners'] + social['parents']), 'Invalid social ID')
        require(len(set(social['partners'])) == len(social['partners']), 'Duplicate partnership')
        for uid in social['partners']:
            require(uid != lonk.uid and uid in by_uid and by_uid[uid].alive and lonk.alive,
                    'Invalid active partnership')
            require(lonk.uid in by_uid[uid].social['partners'], 'Nonreciprocal partnership')
        cid = social['colony_id']
        require(cid is None or isinstance(cid, str) and cid in world.colonies, 'Unknown colony')
        if cid is not None:
            require(lonk.uid in world.colonies[cid]['members'], 'Missing colony membership')
        graduation = social['graduated_at']
        require(graduation is None or type(graduation) is int and 0 <= graduation <= world.tick, 'Invalid graduation')
    for cid, colony in world.colonies.items():
        require(isinstance(cid, str) and cid.startswith('colony-') and cid[7:].isdigit()
                and 0 < int(cid[7:]) < world.next_colony_id, 'Invalid colony sequence reference')
        require(isinstance(colony, dict) and colony.get('id') == cid, 'Invalid colony identity')
        require(isinstance(colony.get('name'), str) and isinstance(colony.get('members'), list)
                and isinstance(colony.get('founders'), list), 'Invalid colony schema')
        require(all(isinstance(uid, str) for uid in colony['members'] + colony['founders']), 'Invalid colony ID')
        require(len(set(colony['members'])) == len(colony['members']), 'Duplicate colony member')
        for uid in colony['members']:
            require(uid in by_uid and by_uid[uid].social['colony_id'] == cid, 'Invalid colony member')
        require(not colony['members'] or colony.get('archived_at') is None, 'Archived colony has members')
        for key in ('founded_at', 'archived_at'):
            value = colony.get(key)
            require((key == 'archived_at' and value is None) or type(value) is int and 0 <= value <= world.tick,
                    'Invalid colony date')
    return True


def init_keys():
    return ('stage', 'graduated_at', 'colony_id', 'partners', 'affection',
            'conversations', 'thoughts', 'player_affection', 'parents')
