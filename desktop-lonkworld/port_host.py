"""One-time extraction of IO adapters from the historical Python test oracle."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    reference = ROOT/'test_fixtures/reference_engine.py'
    source = reference.read_text(encoding='utf-8')
    source = source.replace('import lonk_language as language', 'from test_fixtures import reference_language as language')
    source = source.replace('import lonk_society as society', 'from test_fixtures import reference_society as society')
    reference.write_text(source, encoding='utf-8')
    tree = ast.parse(source)
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
    header = '''"""XC record adapters and atomic persistence; simulation algorithms live in LonkWorld.xc."""
import copy
import json
import math
import os
import random
import re
import tempfile
from pathlib import Path
from functools import partial
import lonk_language as language
import lonk_society as society

SCHEMA = "lonkworld/2"
ACTIONS = ("attack", "explore", "think", "ouch", "idle")
EMOTIONS = ("power", "courage", "wisdom", "masochism", "joy", "anxiety")
TRAITS = ("aggression", "curiosity", "anxiety", "loyalty")

def _tuples(value):
    return tuple(_tuples(x) for x in value) if isinstance(value, list) else value

class _XCBacked:
    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        world = self if self._xc_record == 'LonkWorld' else object.__getattribute__(self, 'world')
        record = world.controller.procedures.records[self._xc_record]
        if name in record.properties:
            return record.properties[name](self)
        if name in record.methods:
            return partial(record.methods[name], self)
        raise AttributeError(name)

class Lonk(_XCBacked):
    _xc_record = 'Lonk'

    def __init__(self, world, name=None):
        world.controller.procedures.records['Lonk'].methods['init'](self, world, name)

'''
    lonk_save = next(n for n in classes['Lonk'].body if isinstance(n, ast.FunctionDef) and n.name == 'to_dict')
    header += '\n'.join('    '+line for line in ast.unparse(lonk_save).splitlines()) + '\n\n'
    header += '''class LonkWorld(_XCBacked):
    _xc_record = 'LonkWorld'

    def __init__(self, starting_population=5, max_population=20, controller=None, seed=2026):
        if controller is None or controller.procedures is None:
            raise ValueError('LonkWorld requires an XC source with its executable procedures.')
        self.controller = controller
        controller.procedures.records['LonkWorld'].methods['init'](
            self, starting_population, max_population, controller, seed)

'''
    for method in classes['LonkWorld'].body:
        if isinstance(method, ast.FunctionDef) and method.name in ('to_dict', 'save', 'load'):
            body = ast.unparse(method).replace('language.initial_language()', 'language.initial_language(controller)')
            header += '\n'.join('    '+line for line in body.splitlines()) + '\n\n'
    (ROOT/'lonk_engine.py').write_text(header, encoding='utf-8')
    for module in ('language', 'society'):
        shim = f'''"""Python-callable bridge to the {module} procedures authored in LonkWorld.xc."""

def __getattr__(name):
    if name.startswith('__'):
        raise AttributeError(name)
    def invoke(first, *args, **kwargs):
        world = first if hasattr(first, 'controller') else first.world
        return getattr(world.controller.procedures.namespaces['{module}'], name)(first, *args, **kwargs)
    return invoke
'''
        if module == 'language':
            shim += '''
def initial_language(controller):
    return controller.procedures.namespaces['language'].initial_language()
'''
        (ROOT/f'lonk_{module}.py').write_text(shim, encoding='utf-8')
    print('Host now contains persistence and XC bridges only.')


if __name__ == '__main__':
    main()
