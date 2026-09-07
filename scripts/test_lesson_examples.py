#!/usr/bin/env python3
"""Extract marked public lesson examples; execute ONLY in new temporary directories.

Python 3.9+, Git 2.28+, bash, Make, C17 compiler. --sanitize needs ASan/UBSan.
Deliberately faulty programs are checked against explicit failure expectations.
This is executable evidence, not independent learner evaluation.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
C_LESSONS = ROOT / 'knowledge-sets/c-programming/lessons'
GIT_LESSONS = ROOT / 'knowledge-sets/toolchain-and-git/lessons'


def command(args: list[str], cwd: Path, expected: int = 0,
            contains: str | None = None, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=180, env=env)
    if (expected == -1 and result.returncode == 0) or (expected != -1 and result.returncode != expected):
        raise AssertionError(f'{args}: exit {result.returncode}, expected {expected}\n{result.stdout}')
    if contains is not None and contains not in result.stdout:
        raise AssertionError(f'{args}: missing {contains!r}\n{result.stdout}')
    return result.stdout


def marked(directory: Path, kind: str) -> dict[str, str]:
    result = {}
    pattern = rf'<!-- {kind}: ([\w.\-]+) -->\s*```\w+\n(.*?)\n```'
    for path in sorted(directory.glob('*.md')):
        for name, code in re.findall(pattern, path.read_text(encoding="utf-8"), re.S):
            if name in result:
                raise ValueError(f'duplicate marker {name}')
            result[name] = code + '\n'
    return result


def verify_c(directory: Path, sanitize: bool) -> None:
    examples = marked(C_LESSONS, 'executable')
    required = {'hello.c', 'args.c', 'types.c', 'numeric.c', 'search.c', 'functions.c',
                'sum.c', 'countdown.c', 'health.h', 'health.c', 'main.c', 'Makefile',
                'parse_health.c', 'alias.c', 'layout.c', 'value.c', 'buffer.c', 'save.c',
                'debug_damage.c', 'oob.c'}
    if set(examples) != required:
        raise AssertionError(f'example inventory differs: {set(examples) ^ required}')
    for name, code in examples.items():
        (directory / name).write_text(code)
    compiler = shlex.split(os.environ.get('CC', 'cc'))
    flags = ['-std=c17', '-Wall', '-Wextra', '-Wpedantic', '-Werror', '-O0', '-g']
    expected = {'hello':'arena ready\n', 'args':'seed text = 42\n',
                'types':'health=20 max=20\n', 'numeric':'numeric: passed\n',
                'search':'search: passed\n', 'functions':'functions: passed\n',
                'sum':'sum: passed\n',
                'countdown':'enter 2\nenter 1\nenter 0\nleave 0\nleave 1\nleave 2\n',
                'alias':'AABCD\n', 'value':'points=7\nratio=0.50\n',
                'buffer':'buffer: all checks passed\n', 'save':'save: all checks passed\n',
                'debug_damage':'damage=-2 health=12\n'}
    programs = [name for name in examples if name.endswith('.c') and name not in {'health.c','main.c','oob.c'}]
    for mode in (['plain', 'san'] if sanitize else ['plain']):
        extra = ['-fsanitize=address,undefined'] if mode == 'san' else []
        for name in programs:
            stem = Path(name).stem
            binary = directory / f'{stem}-{mode}'
            command(compiler + flags + extra + [name, '-o', str(binary)], directory)
            args = [str(binary)] + (['42'] if stem == 'args' else [])
            output = command(args, directory, 1 if stem == 'debug_damage' else 0)
            if stem in expected:
                assert output == expected[stem], (stem, output)
            if stem == 'layout':
                assert re.fullmatch(r'size=\d+ health_offset=\d+\n', output), output
            if stem == 'parse_health':
                assert output.splitlines() == [f'case={i} ok={int(i < 3)} health={v}' for i, v in enumerate([42, 0, 1000, 77, 77, 77, 77, 77])], output
            if stem == 'args':
                command([str(binary)], directory, 2, 'usage:')
        fixed = examples['debug_damage.c'].replace('return damage;', 'return damage > 0 ? damage : 0;')
        for attack, armor, health in [(3,5,10),(8,5,7),(0,0,10)]:
            text = fixed.replace('damage_after_armor(3, 5)', f'damage_after_armor({attack}, {armor})')
            text = text.replace('health == 10', f'health == {health}')
            (directory / 'debug_fixed.c').write_text(text)
            command(compiler + flags + extra + ['debug_fixed.c', '-o', 'debug_fixed'], directory)
            command(['./debug_fixed'], directory, 0, f'health={health}')
    # Exercise the same staged translation commands taught in chapter 1.
    command(compiler + flags + ['-E', 'hello.c', '-o', 'hello.i'], directory)
    command(compiler + flags + ['-S', 'hello.c', '-o', 'hello.s'], directory)
    command(compiler + flags + ['-c', 'hello.c', '-o', 'hello.o'], directory)
    command(compiler + ['hello.o', '-o', 'hello-stages'], directory)
    command(['./hello-stages'], directory, 0, 'arena ready')
    command(['make', 'all', 'CC=' + shlex.join(compiler)], directory)
    command(['./health-demo'], directory, 0, '20\n')
    assert ' -c ' not in command(['make', '-n'], directory)
    # Ensure portable timestamp separation even on coarse filesystems.
    latest = max((directory / f).stat().st_mtime for f in ['main.o', 'health.o', 'health-demo'])
    os.utime(directory / 'health.h', (latest + 2, latest + 2))
    dry = command(['make', '-n'], directory)
    assert '-c main.c' in dry and '-c health.c' in dry, dry
    command(compiler + flags + ['main.c', '-o', 'missing'], directory, -1, 'clamp_health')
    command(['make', 'clean'], directory)
    # Link omission, duplicate definition, and incompatible declaration are distinct.
    command(compiler + flags + ['main.c', 'health.c', 'health.c', '-o', 'duplicate'], directory, -1, 'clamp_health')
    (directory / 'mismatch.c').write_text('#include "health.h"\ndouble clamp_health(int h, int m) { return h > m ? m : h; }\n')
    command(compiler + flags + ['-c', 'mismatch.c'], directory, -1, 'clamp_health')
    # A constraint violation must receive a diagnostic, not a predicted runtime value.
    (directory / 'constraint.c').write_text('int main(void) { return 0 }\n')
    command(compiler + flags + ['constraint.c', '-o', 'constraint'], directory, -1)
    if sanitize:
        # Exercise the chapter 7 off-by-one; skip NULL/0 ONLY in the faulty copy
        # so the stack array overrun is reached. The original ran above unchanged.
        faulty_search = examples['search.c'].replace('i < count', 'i <= count')
        faulty_search = faulty_search.replace('    assert(find_enemy(NULL, 0u, 7) == 0u);\n', '')
        (directory / 'search_fault.c').write_text(faulty_search)
        command(compiler + flags + ['-fsanitize=address', 'search_fault.c', '-o', 'search_fault'], directory)
        command(['./search_fault'], directory, -1, 'stack-buffer-overflow')
        command(compiler + flags + ['-fsanitize=address', 'oob.c', '-o', 'oob'], directory)
        command(['./oob'], directory)
        command(['./oob', 'trigger'], directory, -1, 'heap-buffer-overflow')
        fixed = examples['oob.c'].replace('values[index] = 7;', 'if (index >= 2u) { free(values); return 1; }\n    values[index] = 7;')
        (directory / 'oob_fixed.c').write_text(fixed)
        command(compiler + flags + ['-fsanitize=address', 'oob_fixed.c', '-o', 'oob_fixed'], directory)
        output = command(['./oob_fixed', 'trigger'], directory, 1)
        assert 'AddressSanitizer' not in output
        command(['./oob_fixed'], directory)
    print(f'C LESSONS OK: {len(examples)} extracted files; sanitizer={sanitize}', flush=True)


def verify_git(directory: Path) -> None:
    blocks = marked(GIT_LESSONS, 'git-scenario')
    assert set(blocks) == {'02','03','04','04bisect','05'}, blocks.keys()
    # Isolate global config, hooks, identities, signing, pager and inherited Git routing.
    home = directory / 'home'; home.mkdir()
    env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home), GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0',
               GIT_EDITOR='true', GIT_MERGE_AUTOEDIT='no', TMPDIR=str(directory),
               LC_ALL='C', GIT_PAGER='cat', PYTHONOPTIMIZE='0')
    script = 'set -eu\n' + '\n'.join(blocks[n] for n in ['02','03','04','04bisect','05'])
    script += '\ntest -z "$(git -C "$git_lab/work" status --porcelain)"\n'
    path = directory / 'scenario.sh'; path.write_text(script)
    command(['bash', str(path)], directory, env=env)
    print('GIT LESSONS OK: staged snapshots, two clones, conflicts, abort/continue, rescue, revert, bisect, artifact', flush=True)


def main() -> None:
    if not __debug__:
        raise RuntimeError('Do not disable verification assertions with python -O')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sanitize', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='knowledge-lessons-') as temp:
        root = Path(temp); c = root/'c'; c.mkdir(); git = root/'git'; git.mkdir()
        verify_c(c, args.sanitize)
        verify_git(git)
    print('LESSON EXAMPLES OK (not a platform or learner certification)')


if __name__ == '__main__':
    main()
