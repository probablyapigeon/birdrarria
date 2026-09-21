"""Finite, deterministic LonkWorld simulation and versioned JSON persistence."""

import copy
import json
import math
import os
import random
import re
import tempfile
from pathlib import Path

SCHEMA = "lonkworld/1"
ACTIONS = ("attack", "explore", "think", "ouch", "idle")
EMOTIONS = ("power", "courage", "wisdom", "masochism", "joy", "anxiety")
TRAITS = ("aggression", "curiosity", "anxiety", "loyalty")

def clamp(value, low=0.0, high=100.0):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Simulation values must be finite")
    return max(low, min(high, value))

def bounded_append(sequence, value, limit=64):
    sequence.append(value)
    del sequence[:-limit]

def _tuples(value):
    return tuple(_tuples(x) for x in value) if isinstance(value, list) else value












class Lonk:
    """A creature whose references are IDs and whose memories are plain JSON data."""
    def __init__(self, world, name=None):
        self.world = world
        self.uid = f'lonk-{world.next_uid}'
        world.next_uid += 1
        rng = world.rng
        self.name = name or (rng.choice(world.config['name_start']) + rng.choice(world.config['name_end']))
        self.state = list(world.config['world']['initial_state'])
        low, high = world.config['world']['initial_stats']
        self.emotion = {key: rng.randint(low, high) for key in EMOTIONS}
        self.personality = {key: rng.randint(low, high) for key in TRAITS}
        self.habits = {key: 0 for key in ACTIONS}
        self.age = 0
        self.lifespan = rng.randint(*world.config['world']['lifespan'])
        self.alive = True
        self.generation = 1
        self.territory = rng.choice(list(world.config['territories']))
        self.faction = rng.choice(world.config['factions'])
        self.inventory = []
        self.relationships = {}
        self.memory = {'player_words': {}, 'lonk_words': {}, 'word_counts': {},
                       'rumors': [], 'events': [], 'player_interactions': []}
        self.long_memory = []
        self.trauma = 0
        self.dopamine = 50
        self.crush = None
        self.catchphrase = None
        self.rival = None
        self.xc_checkpoint = None
        for _ in range(rng.randint(0, 2)):
            self.inventory.append(rng.choice(list(world.config['items'])))

    @property
    def vocabulary(self):
        return self.memory['word_counts']

    @property
    def language(self):
        return self.memory['word_counts']

    @property
    def items(self):
        return self.inventory

    def normalize(self):
        if len(self.state) != 5:
            raise ValueError('Lonk state must contain five values')
        self.state = [clamp(x, 0, 1) for x in self.state]
        for mapping in (self.emotion, self.personality):
            for key in mapping:
                mapping[key] = clamp(mapping[key])
        for key in self.habits:
            self.habits[key] = clamp(self.habits[key], 0, 1000)
        self.trauma = clamp(self.trauma)
        self.dopamine = clamp(self.dopamine)
        for key in self.relationships:
            self.relationships[key] = clamp(self.relationships[key], -100, 100)
        del self.inventory[:-32]
        del self.long_memory[:-128]

    def remember(self, message):
        event = {'tick': self.world.tick, 'text': str(message)[:500]}
        if len(self.memory['events']) >= 64:
            bounded_append(self.long_memory, self.memory['events'][0], 128)
        bounded_append(self.memory['events'], event)

    def hear(self, message, speaker=None, player=False):
        message = str(message)[:500]
        counts = self.memory['player_words' if player else 'lonk_words']
        for word in re.findall(r"[\w']+", message.lower())[:100]:
            for table in (counts, self.memory['word_counts']):
                if word not in table and len(table) >= 256:
                    oldest = min(table, key=table.get)
                    del table[oldest]
                table[word] = min(1000000, table.get(word, 0) + 1)
        self.remember(message)
        if player:
            bounded_append(self.memory['player_interactions'], {'tick': self.world.tick, 'text': message})
        # Every heard statement can seed gossip; no custom RumorMemory object.
        if self.world.toggles['gossip'] and message:
            if not any(r['text'] == message for r in self.memory['rumors']):
                bounded_append(self.memory['rumors'], {'text': message, 'source': speaker.uid if speaker else 'player',
                                                      'tick': self.world.tick}, 32)
        if speaker:
            self.update_relationship(speaker, 1)
        self.world.event(self, 'hear_player' if player else 'hear')
        words = set(re.findall(r"[\w']+", message.lower()))
        if words.intersection(self.world.config['keywords']['positive']):
            self.world.event(self, 'hear_positive')
        if words.intersection(self.world.config['keywords']['negative']):
            self.world.event(self, 'hear_negative')
        if words.intersection(self.world.config['keywords']['friend']):
            self.world.event(self, 'hear_friend')

    def speak(self, message=None, target=None, context='general', **values):
        if not self.world.toggles['talk']:
            return
        message = message or self.world.line(context, **values)
        print(f'{self.name}' + (f' -> {target.name}' if target else '') + f': {message}')
        listeners = [target] if target else self.world.neighbors(self)
        for other in listeners:
            if other is not self and other.alive:
                other.hear(message, self)

    def update_relationship(self, other, amount):
        affinity = 3 if self.faction == other.faction else -1
        self.relationships[other.uid] = clamp(self.relationships.get(other.uid, 0) + amount + affinity, -100, 100)
        if len(self.relationships) > self.world.max_population * 2:
            live_ids = {x.uid for x in self.world.lonks}
            self.relationships = {k: v for k, v in self.relationships.items() if k in live_ids}



    def register_pain(self, amount):
        if self.world.controller is not None:
            self.world.event(self, 'hurt')
            return
        self.state[4] = clamp(self.state[4] + amount, 0, 1)
        self.state[2] = clamp(self.state[2] + .3 * amount, 0, 1)
        if self.world.toggles['trauma']:
            self.trauma = clamp(self.trauma + amount * 100)

    def perform_action(self, action):
        world, rng = self.world, self.world.rng
        if action not in ACTIONS:
            raise ValueError(f'Controller returned unknown action: {action!r}')
        if not world.toggles['violence'] and action in ('attack', 'ouch'):
            action = 'idle'
        self.habits[action] = min(1000, self.habits[action] + 1)
        world.event(self, action)
        if action == 'attack':
            neighbors = world.neighbors(self)
            if neighbors:
                opponent = min(neighbors, key=lambda other: self.relationships.get(other.uid, 0))
                self.duel(opponent)
        elif action == 'explore':
            self.territory = rng.choice(list(world.config['territories']))
            territory = world.config['territories'][self.territory]
            print(f'{self.name} wanders into {self.territory} -- {territory["vibe"]}.')
            if world.controller is None:
                self.apply_effects(territory.get('bonus', {}))
            world.event(self, 'territory')
            if rng.random() < world.config['world']['item_chance']:
                item = rng.choice(list(world.config['items']))
                bounded_append(self.inventory, item, 32)
                if world.controller is None:
                    self.apply_effects(world.config['items'][item].get('effect', {}))
                world.event(self, 'find_item')
                self.speak(context='item', item=item)
        else:
            print(f'{self.name} {world.line(action)}')
            if world.controller is None:
                if action == 'think':
                    self.emotion['wisdom'] += 2
                elif action == 'ouch':
                    self.register_pain(.1)
                else:
                    self.state[0] += .03
        self.remember(action)
        self.normalize()

    def apply_effects(self, effects):
        for key, amount in effects.items():
            table = self.emotion if key in self.emotion else self.personality
            if key in table:
                table[key] += amount

    def duel(self, opponent):
        if not self.world.toggles['violence']:
            return
        self.rival = opponent.uid
        self.speak(context='fight', target=opponent)
        winner = self.world.rng.choice([self, opponent])
        loser = opponent if winner is self else self
        print(f'BONK! {winner.name} bonks {loser.name} with comedic force!')
        self.world.event(winner, 'win_duel')
        self.world.event(loser, 'lose_duel')
        if self.world.controller is None:
            loser.register_pain(.15)
        else:
            self.world.event(loser, 'hurt')
        loser.update_relationship(winner, -12)
        winner.update_relationship(loser, -4)
        winner.speak(context='victory')
        loser.speak(context='defeat')
        if self.world.toggles['shinywars'] and loser.inventory:
            bounded_append(winner.inventory, loser.inventory.pop(), 32)
        winner.normalize()
        loser.normalize()

    def dream(self):
        nightmare = self.world.toggles['trauma'] and self.trauma > 20 and self.world.rng.random() < .5
        print(f'{self.name} {self.world.config["dialogue"]["dream"][int(nightmare)]}')
        self.world.event(self, 'nightmare' if nightmare else 'dream')
        if self.world.controller is None:
            self.personality['anxiety' if nightmare else 'loyalty'] += 3
            self.trauma = max(0, self.trauma - 5)
        self.remember('nightmare' if nightmare else 'dream')
        self.normalize()

    def rebirth(self):
        self.alive = False
        baby = Lonk(self.world)
        baby.generation = self.generation + 1
        baby.faction = self.faction
        baby.territory = self.territory
        mutation = self.world.config['world']['inheritance_mutation']
        baby.personality = {k: clamp(v + self.world.rng.randint(-mutation, mutation)) for k, v in self.personality.items()}
        baby.memory['word_counts'] = dict(sorted(self.vocabulary.items(), key=lambda item: -item[1])[:64])
        baby.long_memory = copy.deepcopy((self.long_memory + self.memory['events'])[-24:])
        baby.memory['rumors'] = copy.deepcopy(self.memory['rumors'][-8:])
        self.world.event(baby, 'birth')
        print(f'{self.name} dissolves into dream-mist... A dream-egg hatches into {baby.name}! (Gen {baby.generation})')
        return baby

    def respond_to_player(self, message):
        rng, rules = self.world.rng, self.world.config['world']
        words = set(re.findall(r"[\w']+", message.lower()))
        if self.crush is None and rng.random() < rules['crush_chance']:
            self.crush = 'Player'
        if self.catchphrase is None and rng.random() < rules['catchphrase_chance']:
            self.catchphrase = self.world.line('catchphrase')
        if self.crush == 'Player':
            reply = self.world.line('crush')
        elif 'hug' in words:
            reply = self.world.line('hug')
        elif words.intersection(self.world.config['keywords']['positive']):
            reply = self.world.line('praise')
        elif self.long_memory and rng.random() < rules['recall_chance']:
            reply = str(rng.choice(self.long_memory).get('text', ''))
        else:
            reply = self.world.line('greeting')
        return reply + (' ' + self.catchphrase if self.catchphrase and rng.random() < .3 else '')

    def to_dict(self):
        return copy.deepcopy({k: v for k, v in self.__dict__.items() if k != 'world'})


class LonkWorld:
    def __init__(self, starting_population=5, max_population=20, controller=None, seed=2026):
        if (type(starting_population) is not int or type(max_population) is not int
                or not 0 <= starting_population <= max_population or max_population < 1):
            raise ValueError('Population must be integers with 0 <= starting_population <= max_population and max_population >= 1')
        if controller is None:
            raise ValueError('An XC application controller is required.')
        self.controller = controller
        self.source_hash = controller.source_hash
        self.config = copy.deepcopy(controller.config)
        self.rng = random.Random(seed)
        self.next_uid = 1
        self.tick = 0
        self.max_population = max_population
        self.toggles = {'talk': True, 'violence': True, 'dreams': True, 'gossip': True, 'trauma': True, 'shinywars': False}
        self.lonks = []
        for _ in range(starting_population):
            creature = Lonk(self)
            self.lonks.append(creature)
            self.event(creature, 'birth')

    def event(self, lonk, event_name):
        if self.controller is not None and hasattr(self.controller, 'event'):
            self.controller.event(lonk, event_name)
            lonk.normalize()

    def line(self, context='general', **values):
        pool = self.config['dialogue'].get(context, self.config['dialogue']['general'])
        values.setdefault('title', self.config['title_for_player'])
        return self.rng.choice(pool).format(**values)

    def neighbors(self, lonk):
        return [other for other in self.lonks if other is not lonk and other.alive and other.territory == lonk.territory]

    def player_say(self, message, target_uid=None):
        if not isinstance(message, str) or not message.strip():
            raise ValueError('Message must be nonempty text')
        if not self.toggles['talk']:
            print('Talking is currently paused.')
            return
        listeners = [x for x in self.lonks if x.alive and (target_uid is None or x.uid == target_uid)]
        if target_uid is not None and not listeners:
            raise ValueError(f'No living Lonk with ID {target_uid!r}')
        message = message.strip()[:500]
        print(f'YOU say: {message}')
        for lonk in listeners:
            lonk.hear(message, player=True)
            if self.toggles['talk']:
                print(f'{lonk.name} -> YOU: {lonk.respond_to_player(message)}')

    def world_tick(self):
        self.tick += 1
        print(f'WORLD TICK {self.tick}')
        babies = []
        for lonk in list(self.lonks):
            if not lonk.alive:
                continue
            action = self.controller.step(lonk)
            lonk.normalize()
            lonk.perform_action(action)
            neighbors = self.neighbors(lonk)
            if neighbors and self.rng.random() < self.config['world']['social_chance']:
                other = self.rng.choice(neighbors)
                lonk.update_relationship(other, 2)
                other.update_relationship(lonk, 2)
                self.event(lonk, 'social')
                if self.toggles['gossip'] and lonk.memory['rumors']:
                    rumor = self.rng.choice(lonk.memory['rumors'])['text']
                    if self.rng.random() < self.config['world']['rumor_mutation_chance']:
                        rumor = (rumor + ' maybe')[:500]
                    if self.toggles['talk']:
                        lonk.speak(rumor, other)
            if self.toggles['talk'] and self.rng.random() < self.config['world']['speech_chance']:
                lonk.speak()
            if self.toggles['dreams'] and self.rng.random() < self.config['world']['dream_chance']:
                lonk.dream()
            for uid in lonk.relationships:
                lonk.relationships[uid] *= self.config['world']['relationship_decay']
            lonk.age += 1
            if lonk.age >= lonk.lifespan:
                if self.rng.random() < self.config['world']['rebirth_chance']:
                    babies.append(lonk.rebirth())
                else:
                    lonk.alive = False
                    print(f'{lonk.name} poofs into sparkles at age {lonk.age}.')
            lonk.normalize()
        self.lonks = [lonk for lonk in self.lonks if lonk.alive]
        self.lonks.extend(babies[:max(0, self.max_population - len(self.lonks))])
        if len(self.lonks) < self.max_population and self.rng.random() < self.config['world']['arrival_chance']:
            creature = Lonk(self)
            self.lonks.append(creature)
            self.event(creature, 'birth')
            print(f'A wild Lonk appears: {creature.name}!')

    def to_dict(self):
        return {'schema': SCHEMA, 'tick': self.tick, 'max_population': self.max_population,
                'source_hash': self.source_hash,
                'next_uid': self.next_uid, 'toggles': copy.deepcopy(self.toggles),
                'config': copy.deepcopy(self.config),
                'rng_state': json.loads(json.dumps(self.rng.getstate())),
                'lonks': [lonk.to_dict() for lonk in self.lonks]}

    def save(self, path):
        path = Path(path)
        payload = json.dumps(self.to_dict(), ensure_ascii=False, indent=2, allow_nan=False)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                             prefix=path.name + '.', suffix='.tmp', delete=False) as stream:
                temp_path = stream.name
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    @classmethod
    def load(cls, path, controller=None):
        try:
            data = json.loads(Path(path).read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('schema') != SCHEMA:
                raise ValueError(f'Unsupported world schema; expected {SCHEMA}')
            world = cls.__new__(cls)
            world.controller = controller
            world.source_hash = data.get('source_hash')
            world.tick = data['tick']
            world.max_population = data['max_population']
            world.next_uid = data['next_uid']
            if any(type(n) is not int for n in (world.tick, world.max_population, world.next_uid)):
                raise ValueError('World counters must be integers')
            if world.tick < 0 or world.max_population < 1 or world.next_uid < 1:
                raise ValueError('World counters are out of range')
            world.config = data['config']
            for key in ('territories', 'items', 'dialogue'):
                if not isinstance(world.config[key], dict) or not world.config[key]:
                    raise ValueError(f'Invalid world configuration: {key}')
            world.toggles = data['toggles']
            required_toggles = ('talk', 'violence', 'dreams', 'gossip', 'trauma', 'shinywars')
            if set(world.toggles) != set(required_toggles) or any(type(v) is not bool for v in world.toggles.values()):
                raise ValueError('Invalid world toggles')
            world.rng = random.Random()
            world.rng.setstate(_tuples(data['rng_state']))
            world.lonks = []
            seen = set()
            if not isinstance(data['lonks'], list) or len(data['lonks']) > world.max_population:
                raise ValueError('Invalid saved population')
            required = {'uid', 'name', 'state', 'emotion', 'personality', 'habits', 'age', 'lifespan',
                        'alive', 'generation', 'territory', 'faction', 'inventory', 'relationships',
                        'memory', 'long_memory', 'trauma', 'dopamine', 'crush', 'catchphrase', 'rival', 'xc_checkpoint'}
            for record in data['lonks']:
                if not isinstance(record, dict) or set(record) != required:
                    raise ValueError('Invalid creature record fields')
                uid = record['uid']
                if not isinstance(uid, str) or not re.fullmatch(r'lonk-[1-9][0-9]*', uid) or uid in seen:
                    raise ValueError('Creature IDs must be unique stable IDs')
                if int(uid.split('-')[1]) >= world.next_uid:
                    raise ValueError('Creature ID counter would collide')
                seen.add(uid)
                if not isinstance(record['name'], str) or not record['name']:
                    raise ValueError('Creature name must be nonempty text')
                if type(record['alive']) is not bool:
                    raise ValueError('Invalid alive flag')
                for key in ('age', 'lifespan', 'generation'):
                    if type(record[key]) is not int or record[key] < (0 if key == 'age' else 1):
                        raise ValueError(f'Invalid creature {key}')
                for key, expected in (('emotion', EMOTIONS), ('personality', TRAITS), ('habits', ACTIONS)):
                    if not isinstance(record[key], dict) or set(record[key]) != set(expected):
                        raise ValueError(f'Invalid creature {key}')
                if not isinstance(record['state'], list) or len(record['state']) != 5:
                    raise ValueError('Creature state must have five numbers')
                for key in ('inventory', 'long_memory'):
                    if not isinstance(record[key], list) or len(record[key]) > (32 if key == 'inventory' else 128):
                        raise ValueError(f'Invalid bounded {key}')
                if record['territory'] not in world.config['territories'] or record['faction'] not in world.config['factions']:
                    raise ValueError('Unknown territory or faction')
                if not isinstance(record['relationships'], dict):
                    raise ValueError('Relationships must be a dictionary')
                if record['xc_checkpoint'] is not None and not isinstance(record['xc_checkpoint'], dict):
                    raise ValueError('XC checkpoint must be an object or null')
                memory = record['memory']
                for key in ('player_words', 'lonk_words', 'word_counts'):
                    if not isinstance(memory[key], dict) or len(memory[key]) > 256:
                        raise ValueError('Invalid vocabulary')
                    if any(not isinstance(k, str) or type(v) is not int or not 0 <= v <= 1000000 for k, v in memory[key].items()):
                        raise ValueError('Invalid word counts')
                for key in ('rumors', 'events', 'player_interactions'):
                    if not isinstance(memory[key], list) or len(memory[key]) > (32 if key == 'rumors' else 64):
                        raise ValueError('Invalid bounded memory')
                    if any(not isinstance(entry, dict) or not isinstance(entry.get('text'), str) for entry in memory[key]):
                        raise ValueError('Memory entries must contain text')
                lonk = Lonk.__new__(Lonk)
                lonk.__dict__.update(copy.deepcopy(record))
                lonk.world = world
                # Validate without normalization: load must not mutate serialized state.
                numbers = [(n, 0, 1) for n in lonk.state]
                numbers += [(n, 0, 100) for n in list(lonk.emotion.values()) + list(lonk.personality.values()) + [lonk.trauma, lonk.dopamine]]
                numbers += [(n, 0, 1000) for n in lonk.habits.values()]
                numbers += [(n, -100, 100) for n in lonk.relationships.values()]
                if any(type(n) not in (int, float) or not math.isfinite(n) or not low <= n <= high for n, low, high in numbers):
                    raise ValueError('Creature stats must be finite and within bounds')
                world.lonks.append(lonk)
            if controller is None:
                raise ValueError('An XC application controller is required to load a world.')
            controller.validate_world(world)
            return world
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
            raise ValueError(f'Cannot load LonkWorld save: {exc}') from exc
