# Lonk Birds in Terraria

This is the first tModLoader prototype for bringing the XC Desktop Lonk birds into Terraria.

## Current slice

- `Lonk Feather` summon item, crafted from a Feather and Fallen Star at a Work Bench.
- Lonk uses Terraria’s vanilla bird texture while custom art is developed.
- Lonk follows the nearest active player and can be chatted with.
- The NPC is persistent in the world and cannot be damaged.
- C# code is intentionally separate from the Python/XC Desktop Lonk host.

## Build

Use tModLoader’s **Workshop > Develop Mods > Create Mod** workflow or place this folder in the tModLoader ModSources directory. The stable API target is Terraria 1.4.4/tModLoader; `ModNPC` supplies the companion AI and chat hooks.

For the next slice, the mod will send bounded world events to the XC/Python host over a local bridge. The host will return a small action/state record; the mod will remain responsible for rendering, movement, and multiplayer synchronization.

## Design boundary

The Terraria mod does not read arbitrary files or open network connections. The future bridge will be opt-in and localhost-only. The XC host remains the source of truth for memory, personality, and order-sensitive learning state.
On Windows, copy the folder into the default ModSources directory:

```powershell
$mods = Join-Path $env:USERPROFILE "Documents\My Games\Terraria\tModLoader\ModSources"
Copy-Item -Recurse -Force .\terraria\LonkBirds $mods
```
## Start the portal bridge

From `terraria\LonkBridge`, start the shared loopback service before launching the birds or tModLoader:

```powershell
python bridge.py --port 45871
```

Desktop Lonk visits automatically announce themselves when this service is available. Terraria integration uses the same versioned contract in `Bridge\LonkBridgeProtocol.cs`; the network adapter will be enabled after a local tModLoader build confirms the installed API.
