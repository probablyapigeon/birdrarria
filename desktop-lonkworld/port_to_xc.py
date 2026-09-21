"""One-time migration tool; the resulting .xc is the editable application source.

The historical Python implementations remain test oracles, never runtime inputs.
This tool does not execute Python source or embed it in the XC application.
"""
import ast
import io
from pathlib import Path
import tokenize

ROOT = Path(__file__).resolve().parent


def expression(node):
    value = ast.unparse(node)
    tokens = []
    for token in tokenize.generate_tokens(io.StringIO(value).readline):
        if token.type == tokenize.NAME and token.string in ('None', 'True', 'False'):
            token = token._replace(string={'None': 'null', 'True': 'true', 'False': 'false'}[token.string])
        tokens.append(token)
    return tokenize.untokenize(tokens).strip()


def statements(nodes, indent=0):
    lines = []
    pad = '  ' * indent
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for line in node.value.value.splitlines():
                lines.append(pad + '// ' + line.strip())
        elif isinstance(node, ast.Assign):
            value = expression(node.value)
            if len(node.targets) != 1:
                temporary = f'_assigned_{node.lineno}'
                lines.append(pad + f'let {temporary} <- {value};')
                value = temporary
            for target in node.targets:
                lines.append(pad + f'let {expression(target)} <- {value};')
        elif isinstance(node, ast.AugAssign):
            value = ast.BinOp(left=node.target, op=node.op, right=node.value)
            lines.append(pad + f'let {expression(node.target)} <- {expression(value)};')
        elif isinstance(node, ast.Delete):
            for target in node.targets:
                lines.append(pad + f'remove {expression(target)};')
        elif isinstance(node, ast.FunctionDef):
            kind = 'property' if any(isinstance(d, ast.Name) and d.id == 'property' for d in node.decorator_list) else 'fn'
            name = 'init' if node.name == '__init__' else node.name
            lines.append(pad + f'{kind} {name}({expression(node.args)}) {{')
            lines.extend(statements(node.body, indent + 1))
            lines.append(pad + '}')
        elif isinstance(node, ast.ClassDef):
            lines.append(pad + f'record {node.name} {{')
            body = [n for n in node.body if not isinstance(n, ast.FunctionDef) or n.name not in ('to_dict', 'save', 'load')]
            lines.extend(statements(body, indent + 1))
            lines.append(pad + '}')
        elif isinstance(node, (ast.If, ast.While, ast.For)):
            if isinstance(node, ast.For):
                header = f'for {expression(node.target)} in {expression(node.iter)}'
            else:
                header = ('if ' if isinstance(node, ast.If) else 'while ') + expression(node.test)
            lines.append(pad + header + ' {')
            lines.extend(statements(node.body, indent + 1))
            lines.append(pad + '}')
            if node.orelse:
                if not isinstance(node, ast.If):
                    raise ValueError('Loop-else unsupported')
                lines.append(pad + 'else {')
                lines.extend(statements(node.orelse, indent + 1))
                lines.append(pad + '}')
        elif isinstance(node, ast.Return):
            lines.append(pad + ('return ' + expression(node.value) if node.value else 'return') + ';')
        elif isinstance(node, ast.Raise):
            if node.cause or not node.exc:
                raise ValueError('Exception chaining unsupported')
            lines.append(pad + 'raise ' + expression(node.exc) + ';')
        elif isinstance(node, ast.Expr):
            lines.append(pad + expression(node.value) + ';')
        elif isinstance(node, (ast.Continue, ast.Break)):
            lines.append(pad + ('continue;' if isinstance(node, ast.Continue) else 'break;'))
        else:
            raise ValueError(f'Unsupported migration statement: {type(node).__name__}')
    return lines


def main():
    source = (ROOT/'test_fixtures/hybrid-v2.xc').read_text(encoding='utf-8')
    lines = ['// XC Procedures 1: executable Lonk algorithms, interpreted without Python eval/exec.',
             'procedures LonkWorld version 1 {']
    for module in ('language', 'society', 'engine'):
        tree = ast.parse((ROOT/f'test_fixtures/reference_{module}.py').read_text(encoding='utf-8'))
        nodes = [n for n in tree.body if not isinstance(n, ast.FunctionDef) or n.name != '_tuples']
        lines.append(f'  namespace {module} {{')
        lines.extend(statements(nodes, 2))
        lines.append('  }')
    lines.append('}')
    (ROOT/'LonkWorld.xc').write_text(source.rstrip() + '\n\n' + '\n'.join(lines) + '\n', encoding='utf-8')
    print('Wrote executable procedure source to LonkWorld.xc')


if __name__ == '__main__':
    main()
