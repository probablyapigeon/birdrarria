# XC Application Host 1

This local extension hosts the repaired LonkWorld application. It is not an
upstream XC language-standard change. A source file consists of:

```text
application Name { JSON application declaration }
xembra Model version 1.0 { ...native XC model... }
procedures Name version 1 { ...executable application algorithms... }
```

The first declaration supplies world configuration, dialogue, item/territory
effects, numeric host bindings, and random-input ports. It is parsed as JSON,
not evaluated as Python. The second declaration is parsed by the user's
existing XC Runtime 0.3.0, whose original source SHA-256 is
`ca3cf2de7fe717de70407e59d13cdd5175031e7b4b65c0d7e41b52874f36b29e`.

The adapter adds scalar field assignments by lowering each `field <- expr`
into a native whole-state vector assignment. Assignments execute sequentially.
The existing runtime source itself is unchanged. Randomness is an explicit
host input: one saved, per-world RNG supplies uniform or Gumbel values before
Tick; event calculations and ordered action argmax execute in XC.

The single source hash covers all declarations. A saved world from another
source is rejected without overwriting it, except for the explicitly allowlisted
release-1 source migrated by release 2. The host owns JSON persistence,
windowing, record adaptation, native event dispatch, and primitive services.
Creature identity, text-memory operations, population scheduling, inheritance,
and social algorithms execute from XC procedures. Numerical item/territory
effects and content are declarative data
in the same source. Episodic numeric recall uses the native XC memory engine.

The port binds the original five state channels plus feeling/personality
dictionaries and trauma/dopamine. Positive/negative speech, actions, dreams,
and duels dispatch source events. Unlike the broken originals, Tick calls the
emotional update, player speech seeds rumors, stats are bounded, and save/load
preserves a deterministic continuation.

Run from source: `python lonk_app.py --source LonkWorld.xc`.
Run without a window: `python lonk_app.py --headless 20 --report report.json`.
Verify: `python -m unittest test_lonkworld -v`.

Release 2 adds XC-based word association learning, phonetic word invention,
private rehearsal, inherited dialects, learning stages, reciprocal nonexclusive
partnerships, and colonies. Their configuration is in the XC manifest's
`culture` and `society` objects; their algorithms are procedures in the same
XC source. [XC Procedures 1](XC_PROCEDURES.md) documents the extension and its
generic interpreter. These new constructs require this runtime, not stock 0.3.
Social checks: `python -m unittest test_social_life -v`.

The independent Round 4 frozen backend and artifacts are unrelated to this
application packaging and have not been changed.
