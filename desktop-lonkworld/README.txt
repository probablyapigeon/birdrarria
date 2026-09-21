LONKWORLD XC
============

Double-click LonkWorld.exe. Click Play to let the world advance, or Step to
advance one day. Select a creature to see its feelings, personality and items.
Type a message to Everyone or a selected Lonk. Save preserves the whole world;
closing the window also saves. Load restores the last saved world. New World
asks before replacing progress.

SOCIAL LIFE (RELEASE 2)
----------------------
Your words become part of each listener's vocabulary and word associations.
Lonks remix learned phrases, invent words in their private thoughts, teach one
another and pass language to their descendants. Select the Language tab to
watch their dialect grow. This is a local word-association simulation.

Lonks advance from hatchling to apprentice to storyteller, then graduate after
12 learned words and 6 conversations. Learning drives each stage; age does not.
Friendly graduates found and
join named colonies. Repeated mutual conversations build affection: a Lonk
can have several reciprocal sweethearts at once. These are nonexclusive bonds.
The Lonk tab shows partners and thoughts; Colonies shows community history.
Press Play and talk to them as they grow. All thresholds, probabilities and
colony name parts are editable in the source's culture and society sections.

This update imports saves from the original Desktop XC release, preserving
creatures, memories, feelings and random state. The update installer backs up
the old application and any existing world under LonkWorld XC\backups.

THE SINGLE APPLICATION SOURCE
-----------------------------
LonkWorld.xc combines the two original Lonk prototypes into one editable XC
application. It contains the dialogue, names, factions, territories, items,
world settings, emotional dynamics, action policy, event rules, AND executable
procedures for creatures, word learning, private thought, friendships,
graduation, colonies and the daily simulation loop.

This program uses XC Application Host 1 plus the new XC Procedures 1 extension,
provided by LonkWorld.exe. The original stock XC 0.3 command cannot run these
new declarations by itself. The executable bundles the interpreter and desktop
host; Python and Node are not required on a machine running the finished EXE.

To explicitly run the XC source, double-click Run LonkWorld XC.cmd, or use:
  LonkWorld.exe --source LonkWorld.xc
The EXE also loads that editable source by default. From workspace source:
  python lonk_app.py --source LonkWorld.xc

This is interpreted XC, packaged as a Windows executable, not a claim that XC
was compiled directly into native machine code. It is not Python renamed .xc.

EDITING
-------
Make a backup of LonkWorld.xc first. Its application declaration is a JSON
object (use double quotes; no trailing commas). The xembra declaration beneath
it uses numerical XC syntax. The procedures declaration contains executable
functions, records, loops, text and collection operations. For example, change
world.lifespan, a policy score, or the actual word-learning procedure.
Restart the application after editing. Saved worlds are bound to the exact
source (except the explicitly supported release-1 migration): restore the
previous source to resume an old save, or choose New World
to try edited behavior. Source errors are shown without replacing your save.

The initial six feeling channels and four personality traits retain the
original playful labels. They are simulation variables, not measurements of
real psychological states. Speech mixes learned associations and authored phrases;
no online AI service or paid API is used.

SAVE LOCATION
-------------
%LOCALAPPDATA%\LonkWorldXC\world.json

Saves include creature state, learned words/rumors, relationships, items,
lifecycles, XC memory/checkpoints, and the random generator state. They are
also saved with evolving dialects, thoughts, graduation, partners and colonies.
Saves are
written atomically. The original lonk_save.json format is not imported because
the reviewed originals could not reliably serialize their own state.

IMPLEMENTATION BOUNDARY
----------------------
XC defines the simulation algorithms as well as numerical behavior and content.
The bundled Python runtime provides the generic procedure interpreter, native
XC interpreter, Tk window, random/text/math primitives, and file persistence.
The desktop view renders XC-owned creature records. The runtime does not load
the historical Python simulation; those files exist only as test references.
The extension does not claim that every Python feature now exists in XC, or
that these new constructs already work in the unmodified stock XC runtime.

REBUILD FROM WORKSPACE SOURCE
----------------------------
The complete runner source, tests and packaging scripts are published at:
https://github.com/probablyapigeon/TheLonks

The two original Lonk files have not been modified.
