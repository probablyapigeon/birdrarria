"""Desktop home for LonkWorld, with a disposable command-line check mode."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import traceback

from lonk_engine import LonkWorld
from xc_app_runtime import XCApplication


def source_path(override=None):
    if override:
        return Path(override).resolve()
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
    external = base / "LonkWorld.xc"
    bundled = Path(getattr(sys, "_MEIPASS", base)) / "LonkWorld.xc"
    if not external.exists() and bundled.exists() and bundled != external:
        try:
            shutil.copyfile(bundled, external)
        except OSError:
            return bundled
    return external


def save_path():
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "LonkWorldXC" / "world.json"


def new_world(controller, seed):
    config = controller.config
    with redirect_stdout(io.StringIO()):
        world = LonkWorld(starting_population=int(config.get("starting_population", 5)),
                          max_population=int(config.get("max_population", 20)),
                          controller=controller, seed=seed)
    controller.validate_world(world)
    return world


class Desktop:
    COLORS = ("#71d5b0", "#93bafa", "#dfb4f5", "#edca86", "#f3a9bb")

    def __init__(self, root, source, seed=2026, persistent=True):
        import tkinter as tk
        from tkinter import ttk, messagebox
        self.tk, self.ttk, self.messagebox = tk, ttk, messagebox
        self.root, self.source, self.seed = root, source, seed
        self.persistent = persistent
        self.controller = self.world = None
        self.playing = False
        self.pending = None
        self.blocked = False
        self.dirty = False
        self.target_map = {}
        root.title("LonkWorld · XC")
        root.geometry("1180x820")
        root.minsize(860, 590)
        root.configure(bg="#111c29")
        root.report_callback_exception = self.callback_error
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.build()
        problem = None
        try:
            self.controller = XCApplication(source)
            if persistent and save_path().exists():
                self.world = LonkWorld.load(save_path(), controller=self.controller)
                self.controller.validate_world(self.world)
                self.append("Welcome back. Your little world is right where you left it.")
                self.migration_notice()
            else:
                self.world = new_world(self.controller, seed)
                self.append("A small world. Very big feelings. Say hello to your Lonks.")
        except Exception as exc:
            self.blocked = True
            problem = str(exc)
            self.append("Your saved world is protected. Load a compatible world or choose New World to begin again.")
        self.refresh()
        if problem and persistent:
            root.after_idle(lambda: messagebox.showerror("World needs attention", f"We could not open your world. Your save has not been changed.\n\n{problem}\n\nCorrect LonkWorld.xc and choose Load, or choose New World.", parent=root))

    def build(self):
        tk, ttk = self.tk, self.ttk
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#111c29")
        style.configure("TLabel", background="#111c29", foreground="#e6edf5", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground="#99adc2")
        style.configure("Title.TLabel", font=("Segoe UI", 26, "bold"), foreground="#8de3bf")
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7), background="#263b51", foreground="#eff5fc")
        style.map("TButton", background=[("active", "#36556f")])
        style.configure("TCheckbutton", background="#111c29", foreground="#dce6f0")
        style.map("TCheckbutton", background=[("active", "#263b51")])
        style.configure("Treeview", background="#192a3c", fieldbackground="#192a3c", foreground="#e6edf5", rowheight=34, font=("Segoe UI", 10), borderwidth=0)
        style.configure("Treeview.Heading", background="#263b51", foreground="#c3d5e8", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#355573")])
        style.configure("TNotebook", background="#111c29", borderwidth=0)
        style.configure("TNotebook.Tab", background="#263b51", foreground="#c3d5e8", padding=(15, 7))
        style.map("TNotebook.Tab", background=[("selected", "#355573")], foreground=[("selected", "#8de3bf")])
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text="LonkWorld", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="A pocketful of peculiar lives", style="Muted.TLabel").pack(side="left", padx=18)
        for title, command in (("New World", self.reset), ("Load", self.load), ("Save", self.save)):
            ttk.Button(header, text=title, command=command).pack(side="right", padx=3)
        bar = ttk.Frame(outer, padding=(0, 18, 0, 12))
        bar.pack(fill="x")
        self.play_button = ttk.Button(bar, text="▶ Play", command=self.toggle_play)
        self.play_button.pack(side="left")
        self.step_button = ttk.Button(bar, text="Step", command=self.step)
        self.step_button.pack(side="left", padx=6)
        self.speed = tk.StringVar(value="Easy · 1×")
        ttk.Combobox(bar, textvariable=self.speed, state="readonly", width=14,
                     values=("Easy · 1×", "Lively · 2×", "Wild · 4×")).pack(side="left", padx=6)
        self.status = tk.StringVar(value="Opening your world…")
        ttk.Label(bar, textvariable=self.status, style="Muted.TLabel").pack(side="right")
        toggles = ttk.Frame(outer)
        toggles.pack(fill="x", pady=(0, 14))
        self.toggle_vars = {}
        for key in ("talk", "violence", "dreams", "gossip", "trauma", "shinywars"):
            var = tk.BooleanVar(value=True)
            self.toggle_vars[key] = var
            ttk.Checkbutton(toggles, text={"violence": "Slapstick", "shinywars": "Shiny wars"}.get(key, key.title()),
                            variable=var, command=self.update_toggles).pack(side="left", padx=(0, 16))
        panes = ttk.Panedwindow(outer, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left, right = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(left, weight=3)
        panes.add(right, weight=4)
        ttk.Label(left, text="YOUR LONKS", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        self.tree = ttk.Treeview(left, columns=("age", "home"), show="tree headings", selectmode="browse", height=6)
        self.tree.heading("#0", text="Lonk")
        self.tree.heading("age", text="Age")
        self.tree.heading("home", text="Home")
        self.tree.column("#0", width=125, minwidth=90)
        self.tree.column("age", width=45, minwidth=40, stretch=False)
        self.tree.column("home", width=150, minwidth=70)
        self.tree.pack(fill="x", padx=(0, 14))
        for i, color in enumerate(self.COLORS):
            self.tree.tag_configure(str(i), foreground=color)
        self.tree.bind("<<TreeviewSelect>>", lambda event: self.details())
        self.notebook = ttk.Notebook(left)
        self.notebook.pack(fill="both", expand=True, pady=(10, 0), padx=(0, 14))
        for attribute, title in (("detail", "Lonk"), ("language_detail", "Language"), ("colony_detail", "Colonies")):
            page = ttk.Frame(self.notebook)
            self.notebook.add(page, text=title)
            panel = tk.Text(page, width=36, height=11, wrap="word", bg="#192a3c", fg="#d3e3f2", relief="flat", padx=12, pady=12, spacing3=5, font=("Segoe UI", 10), state="disabled")
            scrollbar = ttk.Scrollbar(page, command=panel.yview)
            panel.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            panel.pack(side="left", fill="both", expand=True)
            setattr(self, attribute, panel)
        ttk.Label(right, text="LIFE IN THE WORLD", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        log_frame = ttk.Frame(right)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, wrap="word", bg="#192a3c", fg="#d3e3f2", relief="flat", padx=16, pady=14, font=("Segoe UI", 10), spacing3=6, state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        composer = ttk.Frame(outer, padding=(0, 16, 0, 0))
        composer.pack(fill="x")
        self.target = tk.StringVar(value="Everyone")
        self.targets = ttk.Combobox(composer, textvariable=self.target, state="readonly", values=("Everyone",), width=19)
        self.targets.pack(side="left", padx=(0, 8))
        self.message = tk.StringVar()
        entry = ttk.Entry(composer, textvariable=self.message, font=("Segoe UI", 11))
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        entry.bind("<Return>", lambda event: self.send())
        self.send_button = ttk.Button(composer, text="Say hello", command=self.send)
        self.send_button.pack(side="left", padx=(8, 0))
        ttk.Label(outer, text="Teach one Lonk a distinctive phrase, then press Play and watch their friends pick it up.", style="Muted.TLabel").pack(anchor="w", pady=(7, 0))

    def migration_notice(self):
        note = getattr(self.world, "migration_note", None)
        if note:
            self.append(str(note))

    def append(self, text):
        if not text.strip():
            return
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        lines = int(self.log.index("end-1c").split(".")[0])
        if lines > 1200:
            self.log.delete("1.0", f"{lines - 1200}.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def capture(self, callback):
        output = io.StringIO()
        try:
            with redirect_stdout(output):
                return callback()
        finally:
            self.append(output.getvalue())

    def refresh(self):
        available = self.world is not None and not self.blocked
        for widget in (self.play_button, self.step_button, self.send_button):
            widget.configure(state="normal" if available else "disabled")
        if not available:
            self.status.set("Paused · your saved world is protected")
            return
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        self.target_map = {}
        for index, lonk in enumerate(self.world.lonks):
            self.tree.insert("", "end", iid=str(lonk.uid), text="●  " + lonk.name,
                             values=(lonk.age, lonk.territory or "Wandering"), tags=(str(index % len(self.COLORS)),))
            self.target_map[f"{lonk.name} · {lonk.uid}"] = lonk.uid
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])
        elif self.world.lonks:
            self.tree.selection_set(str(self.world.lonks[0].uid))
        self.targets.configure(values=("Everyone", *self.target_map))
        if self.target.get() not in self.target_map:
            self.target.set("Everyone")
        for key, var in self.toggle_vars.items():
            var.set(bool(self.world.toggles.get(key, True)))
        self.status.set(f"Day {self.world.tick}   ·   {len(self.world.lonks)} Lonks   ·   {'Playing' if self.playing else 'Paused'}")
        self.details()

    def details(self):
        if self.world is None:
            return
        selected = self.tree.selection()
        lonk = next((x for x in self.world.lonks if selected and str(x.uid) == selected[0]), None)
        text = "Select a Lonk to get to know them."
        language_text = "Select a Lonk to explore their language."
        if lonk:
            social = getattr(lonk, "social", {}) or {}
            language = getattr(lonk, "linguistics", {}) or {}
            colonies = getattr(self.world, "colonies", {}) or {}
            colony_id = social.get("colony_id", social.get("colony"))
            colony = colonies.get(colony_id, colonies.get(str(colony_id), {}))
            colony_name = colony.get("name", "Finding their people") if isinstance(colony, dict) else "Finding their people"
            names = {str(x.uid): x.name for x in self.world.lonks}
            partners = [names.get(str(uid), "A partner remembered") for uid in social.get("partners", [])]
            stage = social.get("learning_stage", social.get("stage", "Learning"))
            graduated = social.get("graduated_at") is not None or social.get("graduated", getattr(lonk, "graduated", False))
            learning = "Graduate" if graduated else str(stage).replace("_", " ").title()
            if social.get("graduated_at") is not None:
                learning += f" since day {social['graduated_at']}"
            emotions = ", ".join(f"{k}: {v:.0f}" if isinstance(v, (int, float)) else f"{k}: {v}" for k, v in lonk.emotion.items())
            traits = ", ".join(f"{k}: {v:.0f}" if isinstance(v, (int, float)) else f"{k}: {v}" for k, v in lonk.personality.items())
            text = (f"{lonk.name}  ·  Generation {lonk.generation}\n"
                    f"{learning}  ·  {colony_name}\n"
                    f"Partners  ·  {', '.join(partners) or 'No partners yet'}\n"
                    f"{lonk.faction or 'Free spirit'}\n\nFeelings  ·  {emotions}\n"
                    f"Personality  ·  {traits}\n\nPockets  ·  {', '.join(map(str, lonk.inventory)) or 'Nothing yet'}")
            thoughts = social.get("thoughts", [])[-4:]
            text += "\n\nPrivate thoughts\n" + ("\n".join(str(item.get("text", ""))[:260] if isinstance(item, dict) else str(item)[:260] for item in thoughts) or "Still taking in this little world.")
            tokens = language.get("tokens", {})
            vocabulary = sorted(tokens, key=lambda word: (-tokens[word], word))[:24]
            dialect = language.get("dialect", {})
            phrases = language.get("phrases", [])[-5:]
            innovations = language.get("innovations", {})
            language_text = (f"{lonk.name}'s language\n{learning}\n\n"
                             f"Learned words ({len(tokens)})\n{', '.join(vocabulary) or 'Waiting for a first conversation.'}\n\n"
                             f"Current dialect\n{', '.join(list(dialect)[:16]) or 'A voice still taking shape.'}\n\n"
                             "Remembered phrases\n" + ("\n".join(str(phrase)[:160] for phrase in phrases) or "Try teaching a distinctive phrase.") + "\n\n"
                             "Invented words\n" + (", ".join(list(innovations)[:12]) or "New words may grow from conversation and reflection."))
        colony_text = []
        colonies = getattr(self.world, "colonies", {}) or {}
        for colony_id, colony in colonies.items():
            if len(colony_text) >= 16:
                break
            if not isinstance(colony, dict) or colony.get("active") is False or colony.get("archived_at") is not None:
                continue
            members = [x for x in self.world.lonks if str((getattr(x, "social", {}) or {}).get("colony_id", (getattr(x, "social", {}) or {}).get("colony"))) == str(colony_id)]
            if not members:
                continue
            words = {}
            for member in members:
                for word, count in (getattr(member, "linguistics", {}) or {}).get("dialect", {}).items():
                    words[word] = words.get(word, 0) + count
            dialect_words = sorted(words, key=lambda word: (-words[word], word))[:10]
            colony_text.append(f"{colony.get('name', 'A little colony')}  ·  {len(members)} members\n"
                               + ", ".join(x.name for x in members) + "\nDialect: " + (", ".join(dialect_words) or "Still growing") + "\n")
        if not colony_text:
            colony_text.append("No colonies yet. Keep the world playing as Lonks learn, graduate, and find their people.\n")
        chronicle = getattr(self.world, "chronicle", []) or []
        colony_text.append("World memories")
        colony_text.extend(f"Day {event.get('tick', '?')} · {str(event.get('text', ''))[:260]}" for event in chronicle[-10:] if isinstance(event, dict))
        if not chronicle:
            colony_text.append("The story is just beginning.")
        for panel, content in ((self.detail, text), (self.language_detail, language_text), (self.colony_detail, "\n".join(colony_text))):
            position = panel.yview()[0]
            panel.configure(state="normal")
            panel.delete("1.0", "end")
            panel.insert("1.0", content)
            panel.yview_moveto(position)
            panel.configure(state="disabled")

    def update_toggles(self):
        if self.world is not None and not self.blocked:
            self.world.toggles.update({key: var.get() for key, var in self.toggle_vars.items()})
            self.dirty = True

    def step(self):
        if self.world is None or self.blocked:
            return
        self.dirty = True
        self.capture(self.world.world_tick)
        self.refresh()

    def pause(self):
        self.playing = False
        if self.pending is not None:
            self.root.after_cancel(self.pending)
            self.pending = None
        self.play_button.configure(text="▶ Play")

    def toggle_play(self):
        if self.playing:
            self.pause()
            self.refresh()
        elif self.world is not None and not self.blocked:
            self.playing = True
            self.play_button.configure(text="Ⅱ Pause")
            self.advance()

    def advance(self):
        self.pending = None
        if self.playing:
            self.step()
            delay = {"Easy · 1×": 1000, "Lively · 2×": 500, "Wild · 4×": 250}[self.speed.get()]
            self.pending = self.root.after(delay, self.advance)

    def send(self):
        message = self.message.get().strip()
        if not message or self.world is None or self.blocked:
            return
        self.dirty = True
        self.capture(lambda: self.world.player_say(message, target_uid=self.target_map.get(self.target.get())))
        self.message.set("")
        self.refresh()

    def save(self):
        if self.world is None or self.blocked:
            self.messagebox.showinfo("Save protected", "Load a compatible world or choose New World before saving.", parent=self.root)
            return False
        self.controller.validate_world(self.world)
        self.world.save(save_path())
        self.dirty = False
        self.append("World saved. Every tiny grudge included.")
        return True

    def load(self):
        self.pause()
        if self.dirty and not self.messagebox.askyesno("Load saved world?", "Replace your current unsaved progress with your saved world?", parent=self.root):
            return
        controller = XCApplication(self.source)
        world = LonkWorld.load(save_path(), controller=controller)
        controller.validate_world(world)
        self.controller, self.world = controller, world
        self.blocked = self.dirty = False
        self.append("Your saved world is back.")
        self.migration_notice()
        self.refresh()

    def reset(self):
        self.pause()
        if not self.messagebox.askyesno("Start a new world?", "Begin again with new Lonks? Your previous world will be replaced when you save or close.", parent=self.root):
            return
        controller = XCApplication(self.source)
        world = new_world(controller, self.seed)
        self.controller, self.world = controller, world
        self.blocked = False
        self.dirty = True
        self.append("A new beginning. The moss has high hopes.")
        self.refresh()

    def callback_error(self, kind, value, tb):
        self.pause()
        self.blocked = True
        self.refresh()
        self.append(f"Paused: {value}")
        self.messagebox.showerror("LonkWorld paused", f"Your last saved world is protected.\n\n{value}\n\nCorrect the source and load your saved world, or choose New World. Autosave is paused until recovery.", parent=self.root)

    def close(self):
        self.pause()
        if self.persistent and self.world is not None and not self.blocked:
            try:
                self.save()
            except Exception as exc:
                if not self.messagebox.askyesno("Could not save", f"Your last successful save is preserved.\n\n{exc}\n\nClose and discard unsaved progress? Choose No to keep this world open.", parent=self.root):
                    return
        self.root.destroy()


def write_report(path, report):
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="LonkWorld · XC")
    parser.add_argument("--headless", type=int, metavar="STEPS")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--gui-smoke", action="store_true")
    args = parser.parse_args(argv)
    if args.headless is not None and args.headless < 0:
        parser.error("--headless must be zero or greater")
    root = None
    try:
        source = source_path(args.source)
        if args.headless is not None:
            controller = XCApplication(source)
            world = new_world(controller, args.seed)
            with redirect_stdout(io.StringIO()):
                for _ in range(args.headless):
                    world.world_tick()
            controller.validate_world(world)
            report = {"ok": True, "tick": world.tick, "population": len(world.lonks), "source_hash": controller.source_hash, "world": world.to_dict()}
            write_report(args.report, report)
            if sys.stdout is not None:
                print(json.dumps({k: v for k, v in report.items() if k != "world"}))
            return 0
        import tkinter as tk
        root = tk.Tk()
        if args.gui_smoke:
            root.withdraw()
        app = Desktop(root, source, args.seed, persistent=not args.gui_smoke)
        result = {"ok": False}
        if args.gui_smoke:
            def smoke():
                try:
                    if app.blocked:
                        raise ValueError("Could not initialize the application")
                    app.step()
                    app.message.set("Hello, little Lonks! Zorpberry moon choir.")
                    app.send()
                    if not all('zorpberry' in lonk.linguistics['tokens'] for lonk in app.world.lonks):
                        raise AssertionError("GUI conversation did not teach its listeners")
                    app.details()
                    if 'zorpberry' not in app.language_detail.get('1.0', 'end').lower():
                        raise AssertionError("Language panel did not display the learned word")
                    with tempfile.TemporaryDirectory(prefix="lonkworld-smoke-") as folder:
                        temporary = Path(folder) / "world.json"
                        app.controller.validate_world(app.world)
                        app.world.save(temporary)
                        restored = LonkWorld.load(temporary, controller=app.controller)
                        if restored.to_dict() != app.world.to_dict():
                            raise AssertionError("Save round-trip changed world state")
                    result.update(ok=True, tick=app.world.tick, population=len(app.world.lonks), source_hash=app.controller.source_hash, save_roundtrip=True, teaching_and_language_panel=True)
                except Exception as exc:
                    result.update(error=str(exc), traceback=traceback.format_exc())
                finally:
                    root.destroy()
            root.after(10, smoke)
        root.mainloop()
        if args.gui_smoke:
            write_report(args.report, result)
            return 0 if result["ok"] else 1
        return 0
    except Exception as exc:
        write_report(args.report, {"ok": False, "error": str(exc), "traceback": traceback.format_exc()})
        if sys.stderr is not None:
            print(f"LonkWorld: {exc}", file=sys.stderr)
        if args.headless is None and not args.gui_smoke:
            try:
                from tkinter import messagebox
                messagebox.showerror("LonkWorld could not open", str(exc), parent=root)
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
