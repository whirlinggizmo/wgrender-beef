#!/usr/bin/env python3
"""Build the simple example: wgrender's library first, then the Beef workspace.

    ./build.py web [release | debug]     build/web (default) or build/web-debug
    ./build.py desktop [release | debug] build/Release_Linux64/simple/ (or Debug_...)
    ./build.py serve [port] [site]       serve build/web on http://localhost:8000/ with
                                         wgrender's dev server (examples/assets at /assets)

The IDE builds the same thing (pick the wasm32 or Linux64 platform), but can't build
wgrender first: a pre-build step runs after BeefBuild has decided whether to relink.
So after changing wgrender, run this before building in the IDE. BeefBuild relinks
when libwgrender.a changes (it's in LibPaths).

BeefProj.toml's wasm32 configs call back into this script after linking:

    ./build.py page SITE      write SITE/index.html: wgrender's page with simple as the
                              default program, versioned by wgrender's webdeploy.py

wgrender is the repository's submodule, project/lib/wgrender-c: BeefProj.toml's
LibPaths name it, so unlike the other bindings there is no WGRENDER_DIR here. To try a
different wgrender, check it out in the submodule.

Env: BEEF_BUILD (the compiler; default BeefBuild on PATH).
"""
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
WGRENDER = (ROOT / '../../project/lib/wgrender-c').resolve()
BEEF_BUILD = os.environ.get('BEEF_BUILD', 'BeefBuild')
KINDS = {'release': ('Release', []), 'debug': ('Debug', ['WEB_DEBUG=1'])}


def run(cmd):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def need_wgrender():
    if not (WGRENDER / 'include/wgr.h').exists():
        sys.exit(f'no wgrender at {WGRENDER}: git submodule update --init')


def page(site):
    site = pathlib.Path(site)
    shell = site / 'index.template.html'
    text = (WGRENDER / 'examples/web/index.html').read_text()
    text = text.replace('params.get("ex") || "hello"', 'params.get("ex") || "simple"')
    text = text.replace('<title>wgrender examples</title>', '<title>simple (wgrender, Beef)</title>')
    shell.write_text(text)
    run(['python3', WGRENDER / 'tools/webdeploy.py', site, shell])
    shell.unlink()


def web(kind):
    config, make_vars = KINDS[kind]
    need_wgrender()
    # webgl2 without threads: the Beef objects aren't built with atomics
    run(['make', '--no-print-directory', '-s', '-C', WGRENDER, 'web', 'BACKEND=webgl2', 'WEB_THREADS=0',
         *make_vars])
    run([BEEF_BUILD, f'-workspace={ROOT}', f'-config={config}', '-platform=wasm32'])
    site = ROOT / 'build' / ('web' if kind == 'release' else 'web-debug')
    for f in ('simple.js', 'simple.wasm'):
        print(f'{f}: {(site / f).stat().st_size:,} bytes')
    print(f'built {site}: ./build.py serve{"" if kind == "release" else " 8000 build/web-debug"}, '
          'then open http://localhost:8000/')


def desktop(kind):
    config, _ = KINDS[kind]
    need_wgrender()
    run(['make', '--no-print-directory', '-s', '-C', WGRENDER])
    run([BEEF_BUILD, f'-workspace={ROOT}', f'-config={config}', '-platform=Linux64'])
    print(f'built {ROOT / "build" / f"{config}_Linux64/simple"}: run it from {ROOT} (assets/ is here)')


def serve(port='8000', site='build/web'):
    need_wgrender()
    os.execvp('python3', ['python3', str(WGRENDER / 'tools/serve.py'), port, str(ROOT / site)])


def main():
    args = sys.argv[1:]
    cmd, rest = (args[0], args[1:]) if args else ('web', [])
    if cmd == 'page' and len(rest) == 1:
        page(rest[0])
    elif cmd in ('web', 'desktop') and len(rest) <= 1 and (rest or ['release'])[0] in KINDS:
        (web if cmd == 'web' else desktop)((rest or ['release'])[0])
    elif cmd == 'serve' and len(rest) <= 2:
        serve(*rest)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
