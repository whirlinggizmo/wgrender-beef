#!/usr/bin/env python3
"""wgrender-beef against the C: the `simple` example compiled Beef -> one wasm, beside
wgrender's own C build of it.

    tools/benchmarks.py          build it, measure it, write bench/results.json and
                                 docs/benchmarks.md
    tools/benchmarks.py --doc    only regenerate docs/benchmarks.md

The harness is wgrender's (tools/bench/measure.py, from the submodule) and so is the
C baseline: run wgrender's tools/benchmarks.py first, on the same machine, so its
bench/results.json is there to compare against. Needs BeefBuild (BEEF_BUILD).

Run by hand, not in CI (CI has no Beef toolchain). Commit bench/results.json and
docs/benchmarks.md afterwards.
"""
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WGRENDER = ROOT / 'project/lib/wgrender-c'
if not (WGRENDER / 'tools/bench/measure.py').is_file():
    sys.exit(f'no wgrender benchmark harness in {WGRENDER} (git submodule update --init)')
sys.path.insert(0, str(WGRENDER / 'tools/bench'))
import measure  # noqa: E402

RESULTS = ROOT / 'bench/results.json'
DOC = ROOT / 'docs/benchmarks.md'
EXAMPLE = ROOT / 'examples/simple'


def measure_all():
    measure.run(['python3', 'build.py', 'web'], cwd=EXAMPLE)
    beef = subprocess.run([os.environ.get('BEEF_BUILD', 'BeefBuild'), '-version'],
                          capture_output=True, text=True).stdout.strip().splitlines()[0]
    site = EXAMPLE / 'build/web'
    page = {'probe': 'simple.js'}
    config = {
        'id': 'beef', 'label': 'Beef', 'project': 'wgrender-beef', 'example': 'simple',
        'toolchain': beef,
        'sizes': measure.sizes([site / 'simple.wasm', site / 'simple.js']),
        'frame': measure.frame(site, 'beef', **page),
        'gc': measure.gc(site, 'beef', **page),
    }
    return measure.write_results(RESULTS, 'wgrender-beef', measure.wgrender_info(WGRENDER, 'submodule'),
                                 [config])


def main():
    baseline_path = WGRENDER / 'bench/results.json'
    if not baseline_path.is_file():
        sys.exit(f'no C baseline at {baseline_path}: run wgrender\'s tools/benchmarks.py first')
    baseline = measure.load_results(baseline_path)
    ours = measure.load_results(RESULTS) if '--doc' in sys.argv[1:] else measure_all()
    lead = ('`simple` compiled Beef -> one wasm, beside the C. The C row and the call costs are '
            'wgrender\'s baseline (its `bench/results.json`); every binding is collected in '
            'wgrender\'s `docs/benchmarks.md`.')
    DOC.parent.mkdir(exist_ok=True)
    DOC.write_text(measure.render_doc('wgrender-beef benchmarks', lead, [baseline, ours], baseline,
                                      'tools/benchmarks.py'))
    print(f'wrote {DOC}')


if __name__ == '__main__':
    main()
