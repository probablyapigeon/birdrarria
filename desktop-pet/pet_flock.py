"""Coordinate the two optional Desktop Lonk birds."""

from __future__ import annotations

from pathlib import Path


class Flock:
    """Own the shared Tk root, Lonk/Pip brains, and their pet windows."""

    def __init__(self, root, data, brain_type, pet_type):
        self.root = root
        self.data = Path(data)
        self.brain_type = brain_type
        self.pet_type = pet_type
        self.paused = False
        self.closed = False
        self.portal_seen = set()
        self.portal_job = None
        try:
            from pet_portal import PortalClient
            self.portal = PortalClient()
        except ImportError:
            self.portal = None

        lonk = brain_type(self.data, name="Lonk")
        pip = brain_type(self.data / "Pip", name="Pip")
        self.brains = [lonk, pip]
        self.pets = [pet_type(root, lonk, self), self._make_peer(root, pip)]
        self.pets[0].peer = self.pets[1] if hasattr(self.pets[0], "peer") else None
        self.pets[1].peer = self.pets[0] if hasattr(self.pets[1], "peer") else None
        self._schedule_portal_poll()

    def _make_peer(self, root, brain):
        import tkinter as tk
        peer_root = tk.Toplevel(root)
        pet = self.pet_type(peer_root, brain, self)
        left, top, right, bottom = pet.area
        pet.x = max(left, min(pet.x + 150, right - pet.WIDTH))
        pet.tx = pet.x
        pet.position()
        return pet

    def _schedule_portal_poll(self):
        if self.portal is not None and not self.closed:
            self.portal_job = self.root.after(4000, self._poll_portal)

    def _poll_portal(self):
        if self.closed or self.portal is None:
            return
        response = self.portal.request(kind="visit", bird="lonk", world="desktop")
        shared = response.get("shared", {}) if isinstance(response, dict) else {}
        memories = shared.get("memories", {}) if isinstance(shared, dict) else {}
        for entry in memories.get("lonk", []):
            if not isinstance(entry, dict) or entry.get("world") != "terraria":
                continue
            marker = (entry.get("kind"), entry.get("text"), entry.get("world"))
            if marker in self.portal_seen:
                continue
            self.portal_seen.add(marker)
            text = str(entry.get("text", "")).strip()
            if text:
                self.brains[0].code.remember(self.brains[0].state, "Terraria Lonk shared: " + text[:180])
                self.brains[0].message = "I heard Lonk through the Terraria portal!"
                self.brains[0].save()
        self._schedule_portal_poll()

    def other(self, pet):
        for candidate in self.pets:
            if candidate is not pet:
                return candidate
        raise ValueError("The flock has no other bird")

    def visit(self, pet):
        if self.portal is not None:
            self.portal.visit(pet.brain.name.lower())
        other = self.other(pet)
        other.follow_peer = pet
        other.follow_until = __import__("time").monotonic() + 12
        return other

    def toggle(self):
        self.paused = not self.paused
        for pet in self.pets:
            pet.paused = self.paused

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.portal_job is not None:
            try:
                self.root.after_cancel(self.portal_job)
            except Exception:
                pass
        for pet in self.pets:
            pet.running = False
            if pet.chat_window:
                pet.chat_window.cancel_reply()
        for brain in self.brains:
            brain.save()
        self.root.destroy()
