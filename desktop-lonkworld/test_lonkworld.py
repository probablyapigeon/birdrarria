"""Behavior and persistence checks; never open the user's actual saved world."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from lonk_engine import LonkWorld
from xc_app_runtime import XCApplication

SOURCE = Path(__file__).with_name('LonkWorld.xc')


class LonkTests(unittest.TestCase):
    def setUp(self):
        self.capture = contextlib.redirect_stdout(io.StringIO())
        self.capture.__enter__()
        self.app = XCApplication(SOURCE)
        self.world = LonkWorld(controller=self.app, seed=711)

    def tearDown(self):
        self.capture.__exit__(None, None, None)

    def test_native_xc_tick_changes_state(self):
        lonk = self.world.lonks[0]
        before = list(lonk.state)
        self.world.world_tick()
        self.assertNotEqual(before, lonk.state)
        self.assertIsNotNone(lonk.xc_checkpoint)
        self.assertEqual(self.world.tick, 1)

    def test_save_roundtrip_and_exact_continuation(self):
        for _ in range(12):
            self.world.world_tick()
        self.world.player_say('You are a good moss friend')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'nested'/'world.json'
            self.world.save(path)
            restored = LonkWorld.load(path, controller=self.app)
            self.assertEqual(restored.to_dict(), self.world.to_dict())
            for _ in range(35):
                self.world.world_tick()
                restored.world_tick()
            self.assertEqual(restored.to_dict(), self.world.to_dict())

    def test_speech_seeds_rumors_and_affects_xc_emotion(self):
        lonk = self.world.lonks[0]
        old = lonk.emotion['joy']
        self.world.player_say('nice friend', target_uid=lonk.uid)
        self.assertGreater(lonk.emotion['joy'], old)
        self.assertEqual(lonk.memory['player_words']['friend'], 1)
        self.assertTrue(any(r['text'] == 'nice friend' for r in lonk.memory['rumors']))

    def test_disabled_talk_and_trauma_are_respected(self):
        self.world.toggles['talk'] = False
        before = self.world.to_dict()
        self.world.player_say('hello')
        self.assertEqual(before, self.world.to_dict())
        lonk = self.world.lonks[0]
        self.world.toggles['trauma'] = False
        self.app.event(lonk, 'hurt')
        self.app.event(lonk, 'ouch')
        self.assertEqual(lonk.trauma, 0)

    def test_violence_toggle_blocks_harmful_actions(self):
        self.world.toggles['violence'] = False
        lonk = self.world.lonks[0]
        lonk.perform_action('attack')
        lonk.perform_action('ouch')
        self.assertEqual(lonk.habits['attack'], 0)
        self.assertEqual(lonk.habits['ouch'], 0)
        self.assertEqual(lonk.habits['idle'], 2)

    def test_all_host_events_are_executable(self):
        lonk = self.world.lonks[0]
        for event in self.app.ir['program']['events']:
            self.app.event(lonk, event)
        self.world.save(Path(self.temp_folder())/'world.json')

    def temp_folder(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        return folder.name

    def test_modified_xc_policy_controls_action(self):
        text = SOURCE.read_text(encoding='utf-8')
        self.assertIn('score IDLE = 0.3', text)
        path = Path(self.temp_folder())/'modified.xc'
        path.write_text(text.replace('score IDLE = 0.3', 'score IDLE = 100000'), encoding='utf-8')
        app = XCApplication(path)
        world = LonkWorld(controller=app)
        self.assertEqual(app.step(world.lonks[0]), 'idle')

    def test_source_mismatch_rejects_saved_world(self):
        folder = Path(self.temp_folder())
        self.world.save(folder/'world.json')
        altered = folder/'changed.xc'
        altered.write_text(SOURCE.read_text(encoding='utf-8')+'\n// changed\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'different version'):
            LonkWorld.load(folder/'world.json', controller=XCApplication(altered))

    def test_invalid_world_and_failed_save_preserve_good_file(self):
        path = Path(self.temp_folder())/'world.json'
        self.world.save(path)
        original = path.read_bytes()
        self.world.lonks[0].state[0] = float('nan')
        with self.assertRaises(ValueError):
            self.world.save(path)
        self.assertEqual(path.read_bytes(), original)
        broken = json.loads(original)
        broken['schema'] = 'not-lonkworld'
        path.write_text(json.dumps(broken), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'schema'):
            LonkWorld.load(path, controller=self.app)

    def test_long_run_is_bounded_and_generations_continue(self):
        self.world.lonks[0].lifespan = 1
        self.world.config['world']['rebirth_chance'] = 1
        self.world.lonks[0].hear('moss remembers', player=True)
        self.world.world_tick()
        self.assertTrue(any(x.generation == 2 for x in self.world.lonks))
        for _ in range(160):
            self.world.world_tick()
        self.assertLessEqual(len(self.world.lonks), self.world.max_population)
        for lonk in self.world.lonks:
            self.assertTrue(all(0 <= value <= 1 for value in lonk.state))
            self.assertLessEqual(len(lonk.memory['rumors']), 32)
            self.assertLessEqual(len(lonk.memory['events']), 64)
            self.assertLessEqual(len(lonk.long_memory), 128)
        self.world.save(Path(self.temp_folder())/'world.json')


if __name__ == '__main__':
    unittest.main()
