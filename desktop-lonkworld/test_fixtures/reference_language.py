"""Small learned word-association culture, not semantic understanding.

All persistent data is JSON; all random choices use the world's saved RNG.
Internal rehearsal reinforces associations without increasing outside exposure.
"""
import copy
import math
import re


_COUNT = 1_000_000
_DEFAULTS = {'max_words': 256, 'max_phrases': 64, 'max_links': 768,
             'max_sentence_words': 14, 'innovation_chance': .12}
_CAPS = {'max_words': 256, 'max_phrases': 64, 'max_links': 768,
         'max_sentence_words': 32}
_TOKEN = re.compile(r"[\w']+", re.UNICODE)


def initial_language():
    return {'version': 1, 'tokens': {}, 'bigrams': {}, 'phrases': [],
            'origins': {}, 'dialect': {}, 'innovations': {},
            'total_heard': 0, 'total_spoken': 0, 'reflections': 0}


def _settings(lonk):
    raw = lonk.world.config.get('culture', {})
    raw = raw if isinstance(raw, dict) else {}
    result = {}
    for key, default in _DEFAULTS.items():
        value = raw.get(key, default)
        if type(value) not in (int, float) or not math.isfinite(value):
            value = default
        result[key] = (max(0., min(1., value)) if key == 'innovation_chance'
                       else max(1, min(_CAPS[key], int(value))))
    return result


def _words(message):
    return [word[:40] for word in _TOKEN.findall(str(message)[:500].lower())][:100]


def _bump(table, key):
    table[key] = min(_COUNT, table.get(key, 0) + 1)


def _prune(state, settings):
    tokens = state['tokens']
    while len(tokens) > settings['max_words']:
        del tokens[min(tokens, key=tokens.get)]
    for name in ('origins', 'dialect', 'innovations'):
        state[name] = {key: value for key, value in state[name].items() if key in tokens}
    links = {a: {b: count for b, count in row.items() if b in tokens}
             for a, row in state['bigrams'].items() if a in tokens}
    links = {a: row for a, row in links.items() if row}
    edges = [(count, a, b) for a, row in links.items() for b, count in row.items()]
    # Stable insertion-order ties survive save/load identically.
    for _, a, b in sorted(edges, key=lambda edge: edge[0])[:max(0, len(edges) - settings['max_links'])]:
        del links[a][b]
    state['bigrams'] = {a: row for a, row in links.items() if row}
    state['phrases'] = state['phrases'][-settings['max_phrases']:]


def learn(lonk, message, speaker_id='player', internal=False):
    """Learn words and directed transitions; never trigger another creature."""
    state = lonk.linguistics
    words = _words(message)
    if not words:
        return
    settings = _settings(lonk)
    source = str(speaker_id)[:80]
    for word in words:
        _bump(state['tokens'], word)
        state['origins'].setdefault(word, source)
        if word not in state['dialect']:
            state['dialect'][word] = lonk.world.rng.randint(1, 5)
    for a, b in zip(words, words[1:]):
        _bump(state['bigrams'].setdefault(a, {}), b)
    if not internal:
        state['total_heard'] = min(_COUNT, state['total_heard'] + 1)
        phrase = ' '.join(words[:settings['max_sentence_words']])
        if phrase in state['phrases']:
            state['phrases'].remove(phrase)
        state['phrases'].append(phrase)
    _prune(state, settings)


def _choose(rng, weighted):
    total = sum(weight for _, weight in weighted)
    draw = rng.randrange(total)
    for item, weight in weighted:
        draw -= weight
        if draw < 0:
            return item
    raise ValueError('Empty language choice')


def _innovate(lonk, word):
    state, rng = lonk.linguistics, lonk.world.rng
    known = list(state['tokens'])
    if len(word) < 2:
        return word
    other = rng.choice(known)
    if other != word and len(other) > 1:
        result = (word[:max(1, len(word) // 2)] + other[len(other) // 2:])[:40]
        bases = [word, other]
    else:
        index = rng.randrange(len(word))
        result = (word[:index] + rng.choice('aeiou') + word[index + 1:])[:40]
        bases = [word]
    if result == word or result in state['tokens']:
        return word
    state['innovations'][result] = bases
    state['origins'][result] = str(lonk.uid)[:80]
    state['tokens'][result] = 1
    state['dialect'][result] = 5
    # A new pronunciation inherits its source's associations.
    if word in state['bigrams']:
        state['bigrams'][result] = dict(state['bigrams'][word])
    return result


def compose(lonk, prompt=None, internal=False):
    """Recombine learned transitions, with occasional jumps and pronunciation drift.

    total_spoken counts generated outward utterances; callers should invoke this
    only when speech is enabled. Explicit scripted speech is counted by callers.
    """
    state, rng = lonk.linguistics, lonk.world.rng
    if not state['tokens']:
        return None
    settings = _settings(lonk)
    overlap = list(dict.fromkeys(w for w in _words(prompt or '') if w in state['tokens']))
    candidates = overlap or list(state['tokens'])
    def weighted(words):
        return [(w, max(1, int(math.sqrt(state['tokens'][w]))) * state['dialect'][w]) for w in words]
    word = _choose(rng, weighted(candidates))
    length = rng.randint(min(3, settings['max_sentence_words']), settings['max_sentence_words'])
    sentence = [word]
    for _ in range(length - 1):
        row = state['bigrams'].get(word, {})
        if row and rng.random() < .78:
            word = _choose(rng, [(w, count * state['dialect'][w]) for w, count in row.items()])
        else:
            word = _choose(rng, weighted(list(state['tokens'])))
        sentence.append(word)
    if rng.random() < settings['innovation_chance']:
        index = rng.randrange(len(sentence))
        sentence[index] = _innovate(lonk, sentence[index])
    text = ' '.join(sentence)
    # Familiar sequences are allowed, but an available alternative avoids a
    # systematic exact echo of the prompt or a memorized phrase.
    if text in state['phrases'] or text == ' '.join(_words(prompt or '')):
        alternatives = [w for w in state['tokens'] if w != sentence[-1]]
        if alternatives:
            sentence[-1] = _choose(rng, weighted(alternatives))
            text = ' '.join(sentence)
    if not internal:
        state['total_spoken'] = min(_COUNT, state['total_spoken'] + 1)
    _prune(state, settings)
    return text


def reflect(lonk):
    thought = compose(lonk, internal=True)
    if thought:
        learn(lonk, thought, speaker_id=lonk.uid, internal=True)
        lonk.linguistics['reflections'] = min(_COUNT, lonk.linguistics['reflections'] + 1)
    return thought


def inherit(parent, baby):
    """Copy culture/origins, reset heard/spoken/reflection developmental counters.

    Association frequencies remain cultural evidence, not the baby's experience.
    Personal preferences are rerolled so descendants develop their own voice.
    """
    baby.linguistics = copy.deepcopy(parent.linguistics)
    for key in ('total_heard', 'total_spoken', 'reflections'):
        baby.linguistics[key] = 0
    baby.linguistics['dialect'] = {w: baby.world.rng.randint(1, 5) for w in baby.linguistics['tokens']}
    _prune(baby.linguistics, _settings(baby))


def summary(lonk):
    state = lonk.linguistics
    return (f"{len(state['tokens'])} words · {state['total_heard']} heard · "
            f"{state['reflections']} thoughts · {len(state['innovations'])} inventions")


def validate_state(state):
    """Raise ValueError for malformed/unbounded saved language; return True."""
    def require(condition):
        if not condition:
            raise ValueError('Invalid learned language state')
    def token(value):
        return isinstance(value, str) and 0 < len(value) <= 40 and _TOKEN.fullmatch(value) is not None
    def count(value, low=0, high=_COUNT):
        return type(value) is int and low <= value <= high
    require(type(state) is dict and set(state) == set(initial_language()))
    require(type(state['version']) is int and state['version'] == 1)
    for key in ('total_heard', 'total_spoken', 'reflections'):
        require(count(state[key]))
    for key in ('tokens', 'bigrams', 'origins', 'dialect', 'innovations'):
        require(type(state[key]) is dict and len(state[key]) <= 256)
    tokens = state['tokens']
    require(all(token(w) and count(n, 1) for w, n in tokens.items()))
    require(set(state['origins']) == set(tokens) == set(state['dialect']))
    require(all(isinstance(s, str) and len(s) <= 80 for s in state['origins'].values()))
    require(all(count(n, 1, 5) for n in state['dialect'].values()))
    links = 0
    for word, row in state['bigrams'].items():
        require(word in tokens and type(row) is dict and 0 < len(row) <= 256)
        require(all(w in tokens and count(n, 1) for w, n in row.items()))
        links += len(row)
    require(links <= 768)
    require(type(state['phrases']) is list and len(state['phrases']) <= 64)
    require(all(isinstance(p, str) and 0 < len(p) <= 1311 and
                0 < len(p.split()) <= 32 and all(token(w) for w in p.split())
                for p in state['phrases']))
    for word, bases in state['innovations'].items():
        require(word in tokens and type(bases) is list and 1 <= len(bases) <= 2)
        require(all(token(w) for w in bases))
    return True


def validate(lonk):
    return validate_state(lonk.linguistics)
