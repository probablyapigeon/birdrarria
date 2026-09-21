# Birdrarria

Birdrarria is a probabilistic shared world for Desktop Lonk, Pip, and Terraria Lonk birds. Each player can have a different flock, world history, culture, and building style while the XC rules remain inspectable.

## What is included

- `desktop-pet/`: runnable Desktop Lonk and Pip birds.
- `desktop-lonkworld/`: XC runtime used by the desktop flock.
- `terraria/LonkBridge/`: localhost-only JSON-lines portal bridge.
- `terraria/LonkBirds/`: tModLoader mod source with Lonk companion behavior and Creative Build Mode scaffolding.

## Run the portal bridge

```powershell
cd terraria\LonkBridge
python bridge.py --port 45871
```

Keep that window open. The bridge listens only on `127.0.0.1` and accepts bounded observations, visits, lessons, project progress, and build requests.

## Run Desktop Lonk birds

```powershell
cd desktop-pet
python -X utf8 desktop_pet.py --gui
```

The desktop flock stays usable when Terraria or the bridge is offline. When the bridge is available, it shares portal memories with Terraria Lonk.

## Install the Terraria mod

1. Install tModLoader through Steam and the matching .NET SDK required by its Develop Mods screen.
2. Copy `terraria\LonkBirds` into your active tModLoader `ModSources` folder. OneDrive installations commonly use:

   `C:\Users\<you>\OneDrive\Documents\My Games\Terraria\tModLoader\ModSources\LonkBirds`

3. In tModLoader, open **Workshop → Develop Mods → Lonk Birds → Build + Reload**.
4. Enable the mod and enter a world.

Lonk reports portal presence and observations through the bridge. Creative building is opt-in through the in-game mode controls and remains logged by the bridge.

## Tests

```powershell
cd terraria\LonkBridge
python -m unittest -v test_bridge.py

cd ..\..\desktop-pet
python -m unittest discover -s . -p "test_*.py" -q
```

Birdrarria is a glass-box experiment: world events, shared memories, project progress, and build requests are explicit data rather than hidden model state.
