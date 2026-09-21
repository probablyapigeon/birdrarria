import unittest
from types import SimpleNamespace

from xc_procedures import XCProcedures, XCProcedureError, XCBudgetError


def program(source, **kwargs):
    return XCProcedures('procedures Test version 1 {\nnamespace engine {\n' + source + '\n}\n}', **kwargs)


class ProcedureTests(unittest.TestCase):
    def test_loops_assignments_and_native_errors(self):
        p = program('''fn run(values) {
let result <- [];
for a, b in values {
if a < 0 {
continue;
}
result.append(a + b);
}
let result[1:] <- [7, 8];
remove result[-1];
let n <- 0;
while true {
let n <- n + 1;
if n == 3 {
break;
}
}
return result, n;
}
fn fail() {
raise ValueError('bad');
}''')
        self.assertEqual(p.namespaces['engine'].run([(1, 2), (-1, 9), (3, 4)]), ([3, 7], 3))
        with self.assertRaisesRegex(ValueError, 'bad'):
            p.namespaces['engine'].fail()

    def test_closures_comprehensions_and_keywords(self):
        p = program('''fn make(offset=2, *args, **kw) {
fn add(x, n=offset) {
return x + n;
}
let i <- 99;
let pairs <- [(i, j) for i in range(3) for j in range(i) if j == 0];
return add, pairs, i, args, kw;
}
fn format_name(a, b) {
return f'{a.name} and {b.name}', sorted([3,1,2], key=lambda x: -x);
}''')
        fn, pairs, i, args, kw = p.namespaces['engine'].make(5, 6, value=7)
        self.assertEqual((fn(3), pairs, i, args, kw), (8, [(1, 0), (2, 0)], 99, (6,), {'value': 7}))
        self.assertEqual(p.namespaces['engine'].format_name(SimpleNamespace(name='A'), SimpleNamespace(name='B')), ('A and B', [3, 2, 1]))

    def test_record_capability_and_namespace(self):
        p = XCProcedures('''procedures Test version 1 {
namespace language {
fn value() {
return 4;
}
}
namespace engine {
let factor <- 3;
record Lonk {
fn init(self, world, name=null) {
let self.value <- language.value() * factor;
let self.name <- name;
}
property vocabulary(self) {
return self.value;
}
}
fn create() {
return Lonk();
}
}
}''', {'Lonk': SimpleNamespace})
        obj = p.namespaces['engine'].create()
        p.records['Lonk'].methods['init'](obj, None, 'hello')
        self.assertEqual(p.records['Lonk'].properties['vocabulary'](obj), 12)
        self.assertEqual(obj.name, 'hello')

    def test_generator_is_lazy_and_boolean_short_circuit(self):
        seen = []
        p = program('''fn run() {
let values <- (track(x) for x in range(4));
return next(values), false and missing(), true or missing(), 1 < 2 < 3;
}''', capabilities={'track': lambda x: seen.append(x) or x})
        self.assertEqual(p.namespaces['engine'].run(), (0, False, True, True))
        self.assertEqual(seen, [0])

    def test_budget_and_depth(self):
        p = program('''fn forever() {
while true {
}
}
fn recurse() {
return recurse();
}''', max_steps=100, max_depth=10)
        with self.assertRaises(XCBudgetError):
            p.namespaces['engine'].forever()
        with self.assertRaisesRegex(XCBudgetError, 'depth'):
            p.namespaces['engine'].recurse()

    def test_collection_expansion_slices_and_call_binding(self):
        p = program('''fn collect(a, *, b=2, **rest) {
return a, b, rest;
}
fn run() {
let first, *middle, last <- range(5);
let mapping <- {x: x * x for x in middle};
let unique <- {x % 2 for x in range(6)};
let merged <- {'a': first, **mapping};
return collect(*[last], **{'b': 7, 'extra': 8}), middle[::-1], unique, merged, type(first) is int;
}''')
        self.assertEqual(p.namespaces['engine'].run(),
                         ((4, 7, {'extra': 8}), [3, 2, 1], {0, 1},
                          {'a': 0, 1: 1, 2: 4, 3: 9}, True))
        with self.assertRaises(TypeError):
            p.namespaces['engine'].collect()

    def test_reject_unsupported_and_malformed(self):
        for source in ('fn f() {\nreturn (x := 1);\n}', 'import os;', 'fn f() {\nreturn x.__class__;\n}', 'fn f() {'):
            with self.subTest(source=source):
                with self.assertRaises((XCProcedureError, NameError)):
                    program(source)


if __name__ == '__main__':
    unittest.main()
