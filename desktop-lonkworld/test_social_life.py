import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

import lonk_language as language
import lonk_society as society
from lonk_engine import LonkWorld
from xc_app_runtime import XCApplication

ROOT = Path(__file__).parent


class SocialLifeTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.app = XCApplication(ROOT/'LonkWorld.xc')
        self.world = LonkWorld(controller=self.app, seed=404)

    def tearDown(self):
        self.redirect.__exit__(None, None, None)

    def test_user_words_become_spoken_and_reach_another_lonk(self):
        a, b = self.world.lonks[:2]
        self.world.config['culture']['innovation_chance'] = 0
        self.world.player_say('zorpberry moss sings softly', a.uid)
        self.assertIn('zorpberry', a.linguistics['tokens'])
        utterance = language.compose(a, prompt='zorpberry')
        self.assertIn('zorpberry', utterance)
        a.speak(utterance, target=b)
        self.assertIn('zorpberry', b.linguistics['tokens'])
        self.assertEqual(b.linguistics['origins']['zorpberry'], a.uid)

    def test_internal_language_evolves_without_faking_outside_experience(self):
        a = self.world.lonks[0]
        a.hear('moonberry dances with moss soup shimmer', player=True)
        heard = a.linguistics['total_heard']
        self.world.config['culture']['innovation_chance'] = 1
        thoughts = [language.reflect(a) for _ in range(12)]
        self.assertEqual(a.linguistics['total_heard'], heard)
        self.assertEqual(a.linguistics['reflections'], 12)
        self.assertTrue(a.linguistics['innovations'])
        self.assertGreater(len(set(thoughts)), 1)
        language.validate(a)

    def test_language_inheritance_is_independent(self):
        a = self.world.lonks[0]
        a.hear('zorpberry meadow friend', player=True)
        baby = a.rebirth()
        self.assertIn('zorpberry', baby.linguistics['tokens'])
        old = a.linguistics['tokens']['zorpberry']
        baby.linguistics['tokens']['zorpberry'] += 4
        self.assertEqual(a.linguistics['tokens']['zorpberry'], old)
        self.assertEqual(baby.linguistics['total_heard'], 0)

    def test_social_language_save_resume_is_exact(self):
        self.world.player_say('we adore the moonberry moss choir')
        for _ in range(8):
            self.world.world_tick()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'world.json'
            self.world.save(path)
            resumed = LonkWorld.load(path, controller=self.app)
            self.assertEqual(self.world.to_dict(), resumed.to_dict())
            for _ in range(8):
                self.world.world_tick()
                resumed.world_tick()
            self.assertEqual(self.world.to_dict(), resumed.to_dict())

    def test_legacy_world_migration_preserves_creatures_and_rng(self):
        import lonk_engine_v1_fixture
        legacy_app = XCApplication(ROOT/'LonkWorld-v1.xc')
        old = lonk_engine_v1_fixture.LonkWorld(controller=legacy_app, seed=321)
        old.player_say('old moss words survive')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'old.json'
            old.save(path)
            before = path.read_bytes()
            migrated = LonkWorld.load(path, controller=self.app)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(migrated.rng.getstate(), old.rng.getstate())
            self.assertEqual([x.uid for x in old.lonks], [x.uid for x in migrated.lonks])
            for former, current in zip(old.lonks, migrated.lonks):
                self.assertEqual(former.state, current.state)
                self.assertEqual(former.memory, current.memory)
                self.assertIn('moss', current.linguistics['tokens'])
            migrated.world_tick()
            migrated.save(Path(folder)/'migrated.json')
            again = LonkWorld.load(Path(folder)/'migrated.json', controller=self.app)
            self.assertEqual(migrated.to_dict(), again.to_dict())

    def test_multiple_mutual_partners_graduate_and_found_colony(self):
        a, b, c = self.world.lonks[:3]
        self.world.config['society']['bond_chance'] = 1
        for lonk in (a, b, c):
            lonk.age = 0
        for _ in range(8):
            a.speak('moss moon soup cuddle flower happy dream shiny cloud pebble nest song', target=b)
            b.speak('moss moon soup cuddle flower happy dream shiny cloud pebble nest song', target=a)
            a.speak('moss moon soup cuddle flower happy dream shiny cloud pebble nest song', target=c)
            c.speak('moss moon soup cuddle flower happy dream shiny cloud pebble nest song', target=a)
        self.assertEqual(set(a.social['partners']), {b.uid, c.uid})
        self.assertIn(a.uid, b.social['partners'])
        self.assertIn(a.uid, c.social['partners'])
        society.society_tick(self.world)
        self.assertTrue(all(x.social['stage'] == 'graduate' for x in (a, b, c)))
        cid = a.social['colony_id']
        self.assertIsNotNone(cid)
        self.assertEqual({a.uid, b.uid, c.uid}, set(self.world.colonies[cid]['members']))
        society.validate_world(self.world)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'colony.json'
            self.world.save(path)
            restored = LonkWorld.load(path, controller=self.app)
            self.assertEqual(restored.to_dict(), self.world.to_dict())
        a.alive = False
        society.on_departure(self.world, a)
        self.world.lonks.remove(a)
        society.society_tick(self.world)
        self.assertNotIn(a.uid, b.social['partners'])
        self.assertNotIn(a.uid, c.social['partners'])
        self.assertNotIn(a.uid, self.world.colonies[cid]['members'])
        society.validate_world(self.world)

    def test_default_play_develops_society(self):
        self.world.player_say('moss moon soup cuddle flower happy dream shiny cloud pebble nest song')
        for _ in range(70):
            self.world.world_tick()
        kinds = {entry['kind'] for entry in self.world.chronicle}
        self.assertTrue({'graduation', 'colony_founded', 'partnership'} <= kinds, kinds)
        self.assertTrue(any(x.social['thoughts'] for x in self.world.lonks))
        society.validate_world(self.world)

    def test_learning_stages_depend_on_learning_not_age(self):
        lonk = self.world.lonks[0]
        lonk.age = 100
        society.develop(lonk)
        self.assertEqual(lonk.social['stage'], 'hatchling')
        lonk.age = 0
        lonk.hear('moss', player=True)
        society.develop(lonk)
        self.assertEqual(lonk.social['stage'], 'apprentice')
        for _ in range(2):
            lonk.hear('moss moon soup', player=True)
        society.develop(lonk)
        self.assertEqual(lonk.social['stage'], 'storyteller')
        for _ in range(3):
            lonk.hear('moss moon soup cuddle flower happy dream shiny cloud pebble nest song', player=True)
        society.develop(lonk)
        self.assertEqual(lonk.social['stage'], 'graduate')
        self.assertEqual(lonk.age, 0)


if __name__ == '__main__':
    unittest.main()
