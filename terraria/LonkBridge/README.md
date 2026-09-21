# Lonk Portal Bridge

This folder defines the first shared language between Desktop Lonk birds and the Terraria mod. It is a deliberately bounded, loopback-only JSON-lines service.

Run it from PowerShell:

```powershell
python bridge.py --port 45871
```

Messages are limited to short observations, visits, lessons, and project progress. The service binds only to `127.0.0.1`; it does not execute commands, open files, or accept remote connections. XC remains the source of truth for learner state. Desktop and Terraria adapters can reconnect and receive the shared bird memories and current project snapshot.

Protocol smoke tests:

```powershell
python -m unittest -v test_bridge.py
```

The Terraria mod scaffold currently contains the in-game bird and summon item. Its adapter will consume this protocol once tModLoader is installed and the mod can be compiled against the user's current tModLoader API.
