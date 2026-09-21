"""Check executable XC algorithms against the preserved behavioral reference."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from lonk_engine import LonkWorld
from xc_app_runtime import XCApplication
from test_fixtures.reference_engine import LonkWorld as ReferenceWorld

SOURCE = Path(__file__).with_name('LonkWorld.xc')


class XCPortTests(unittest.TestCase):
    def test_xc_simulation_matches_reference_and_random_stream(self):
        app = XCApplication(SOURCE)
        self.assertIsNotNone(app.procedures)
        actual = LonkWorld(controller=app, seed=911)
        expected = ReferenceWorld(controller=app, seed=911)
        self.assertEqual(actual.to_dict(), expected.to_dict())
        for tick in range(24):
            actual_log, expected_log = io.StringIO(), io.StringIO()
            for world, log in ((actual, actual_log), (expected, expected_log)):
                with contextlib.redirect_stdout(log):
                    if tick in (0, 6, 12):
                        world.player_say('moss moon soup cuddle flower happy dream shiny cloud pebble nest song')
                    world.world_tick()
            self.assertEqual(actual_log.getvalue(), expected_log.getvalue(), f'tick {tick}')
            self.assertEqual(actual.to_dict(), expected.to_dict(), f'tick {tick}')

    def test_editing_xc_changes_learning_algorithm(self):
        source = SOURCE.read_text(encoding='utf-8')
        old = 'let table[key] <- min(_COUNT, table.get(key, 0) + 1);'
        self.assertIn(old, source)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'learning.xc'
            path.write_text(source.replace(old, 'let table[key] <- min(_COUNT, table.get(key, 0) + 7);'), encoding='utf-8')
            app = XCApplication(path)
            world = LonkWorld(controller=app)
            with contextlib.redirect_stdout(io.StringIO()):
                world.lonks[0].hear('zorpberry', player=True)
            self.assertEqual(world.lonks[0].linguistics['tokens']['zorpberry'], 7)


if __name__ == '__main__':
    unittest.main()
