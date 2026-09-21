# XC Procedures 1

LonkWorld needed text, mutable collections, reusable functions, and control
flow beyond XC Runtime 0.3's numerical model. This versioned local extension
adds those features without changing the copied native runtime. It is an
experimental extension, not a claim of support in unmodified XC 0.3.

The single `LonkWorld.xc` contains the application manifest, native emotional
model, and all creature, language, social, and world-tick algorithms. The
Python host supplies the window, record adapters, native event dispatch,
random/math/text primitives, and JSON persistence. The preserved Python
implementations in `test_fixtures` are independent comparison fixtures; the
application never imports them.

```xc
procedures Example version 1 {
  namespace learning {
    fn reinforce(counts, word) {
      let counts[word] <- counts.get(word, 0) + 1;
      return counts[word];
    }
  }
}
```

Blocks use braces on separate lines; each statement ends with `;`. Keep each
expression on one line. `//` comments occupy their own lines. Supported forms:

- `namespace name { ... }`, with constants and `fn` declarations.
- `record Name { ... }`, containing `fn` methods and `property` getters.
- `let target <- expression;`, including tuple unpacking and indexed fields.
- `if condition { ... }`, optional `else { ... }`, `for target in iterable`,
  and `while condition` blocks; `break;` and `continue;`.
- `return expression;`, `return;`, `remove target;`, `raise error;`, and calls.
- Lexically scoped functions, defaults, keyword arguments, and closures.

Expressions intentionally use a Python-like subset: numbers, text, `true`,
`false`, `null`, lists, dictionaries, sets, tuples, indexing, slices, arithmetic,
comparisons, short-circuit booleans, calls, lambdas, comprehensions, lazy
generators, and formatted strings. The parser uses Python's `ast.parse` for
expression syntax; an explicit interpreter evaluates supported nodes. It does
not use `eval`, `exec`, or compiled Python code to execute the application.
Import statements and unsupported syntax fail. The extension is tested with
Python 3.14; the packaged Windows EXE includes its own interpreter.

The host explicitly provides callable primitives. Source programs are trusted
local programs, not a security sandbox: host capabilities are trusted objects.
XC evaluation has a 2,000,000-step budget per outer call and call-depth limit
of 128. These bounds do not limit work performed inside a host capability.

LonkWorld's record adapters expose the XC methods to the GUI. There is one
saved random generator per world. Save files bind to the full source hash,
including procedures. The known first desktop release can migrate with its
creatures and random stream preserved; other source changes require a new
world or the matching original source.

Verification includes primitive interpreter tests, simulation/reference parity
for output/state/randomness, editing a learning algorithm in XC and observing
its changed behavior, long simulations, persistence, and a frozen GUI check.
The one-time `port_to_xc.py` / `port_host.py` migration tools are historical
development aids. Ordinary execution and packaging never run them; edit
`LonkWorld.xc` directly.
