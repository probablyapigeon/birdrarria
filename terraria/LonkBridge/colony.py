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
    families: list[dict[str, Any]] = field(default_factory=list)
    def register(self, bird, world, role="scout", faction="wanderers"):
        self.residents[bird] = {"bird": bird, "world": world, "role": role, "faction": faction}
        self.factions.setdefault(faction, {"name": faction, "members": []})
        if bird not in self.factions[faction]["members"]: self.factions[faction]["members"].append(bird)
        return self.residents[bird]
    def bond(self, first, second, amount=1):
        self.relationships.setdefault(first, {})[second] = self.relationships.setdefault(first, {}).get(second, 0) + amount
        self.relationships.setdefault(second, {})[first] = self.relationships.setdefault(second, {}).get(first, 0) + amount
    def add_job(self, title, target, assigned_to=None):
        job = {"title": title, "target": target, "assigned_to": assigned_to, "status": "open"}; self.jobs.append(job); return job
    def create_family(self, name, members, parents=None):
        family = {"name": name[:48], "members": list(dict.fromkeys(members)), "parents": list(dict.fromkeys(parents or [])), "children": []}
        for member in family["members"]:
            if member not in self.residents: self.register(member, "desktop")
        self.families.append(family); return family
    def add_child(self, family_name, child, parents):
        family = next((item for item in self.families if item["name"] == family_name), None)
        if family is None: family = self.create_family(family_name, parents + [child], parents)
        if child not in family["children"]: family["children"].append(child)
        if child not in family["members"]: family["members"].append(child)
        for parent in parents: self.bond(parent, child, 2)
        return family
    def add_myth(self, title, telling, teller):
        myth = {"title": title, "telling": telling[:240], "teller": teller}; self.myths.append(myth); return myth
    def add_settlement(self, name, world, x, y):
        settlement = {"name": name, "world": world, "x": x, "y": y, "population": 0}; self.settlements.append(settlement); return settlement
    def snapshot(self):
        result = deepcopy(self.__dict__)
        for settlement in result["settlements"]:
            settlement["population"] = sum(1 for resident in self.residents.values() if resident.get("world") == settlement["world"])
        return result
