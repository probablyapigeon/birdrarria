"""Glass-box colony state shared by Desktop Lonk and Terraria adapters."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Colony:
    residents: dict[str, dict[str, Any]] = field(default_factory=dict)
    relationships: dict[str, dict[str, int]] = field(default_factory=dict)
    factions: dict[str, dict[str, Any]] = field(default_factory=dict)
    jobs: list[dict[str, Any]] = field(default_factory=list)
    settlements: list[dict[str, Any]] = field(default_factory=list)
    myths: list[dict[str, Any]] = field(default_factory=list)

    def register(self, bird: str, world: str, role: str = "scout", faction: str = "wanderers") -> dict[str, Any]:
        self.residents[bird] = {"bird": bird, "world": world, "role": role, "faction": faction}
        self.factions.setdefault(faction, {"name": faction, "members": []})
        if bird not in self.factions[faction]["members"]:
            self.factions[faction]["members"].append(bird)
        return self.residents[bird]

    def bond(self, first: str, second: str, amount: int = 1) -> None:
        self.relationships.setdefault(first, {})[second] = self.relationships.setdefault(first, {}).get(second, 0) + amount
        self.relationships.setdefault(second, {})[first] = self.relationships.setdefault(second, {}).get(first, 0) + amount

    def add_job(self, title: str, target: str, assigned_to: str | None = None) -> dict[str, Any]:
        job = {"title": title, "target": target, "assigned_to": assigned_to, "status": "open"}
        self.jobs.append(job)
        return job

    def add_myth(self, title: str, telling: str, teller: str) -> dict[str, Any]:
        myth = {"title": title, "telling": telling[:240], "teller": teller}
        self.myths.append(myth)
        return myth

    def add_settlement(self, name: str, world: str, x: int, y: int) -> dict[str, Any]:
        settlement = {"name": name, "world": world, "x": x, "y": y, "population": 0}
        self.settlements.append(settlement)
        return settlement

    def snapshot(self) -> dict[str, Any]:
        result = deepcopy(self.__dict__)
        for settlement in result["settlements"]:
            settlement["population"] = sum(1 for resident in self.residents.values() if resident.get("world") == settlement["world"])
        return result
