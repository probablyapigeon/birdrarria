import unittest
from colony import Colony


class ColonyTests(unittest.TestCase):
    def test_family_relationships_and_population(self):
        colony = Colony()
        colony.register("lonk", "terraria", "builder", "nestkeepers")
        colony.register("pip", "desktop", "archivist", "nestkeepers")
        family = colony.create_family("First Nest", ["lonk", "pip"], ["lonk"])
        colony.add_child("First Nest", "sprout", ["lonk", "pip"])
        snapshot = colony.snapshot()
        self.assertEqual(family["name"], "First Nest")
        self.assertIn("sprout", snapshot["families"][0]["children"])
        self.assertEqual(snapshot["relationships"]["lonk"]["sprout"], 2)


if __name__ == "__main__":
    unittest.main()
