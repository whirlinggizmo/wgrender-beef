#!/usr/bin/env python3
"""Build the web version of simple: wgrender's web library, then the wasm32 platform.

    ./build_web.py [release | debug]     build/web (default) or build/web-debug
    ./serve_web.sh [port] [site]         then open http://localhost:8000/

The IDE builds the same thing (pick the wasm32 platform), but can't build wgrender
first: a pre-build step runs after BeefBuild has decided whether to relink. So
after changing wgrender, run this (or make -C wgrender all WEB=1 WEB_THREADS=0, plus
WEB_DEBUG=1 for Debug) before building in the IDE. BeefBuild relinks when
libwgrender.a changes (it's in LibPaths).

BeefProj.toml's wasm32 configs call back into this script after linking:

    build_web.py page SITE    write SITE/index.html: wgrender's page with simple as
                              the default program, versioned by wgrender's webdeploy.py

Env overrides: LIBWGR_ROOT, BEEF_BUILD (compiler).
"""
import os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent
WGRENDER = pathlib.Path(os.environ.get('LIBWGR_ROOT', pathlib.Path.home()/'projects/github/whirlinggizmo/wgrender-c')).resolve()
BEEF_BUILD = os.environ.get('BEEF_BUILD', 'BeefBuild')
KINDS = {'release': ('Release', []), 'debug': ('Debug', ['WEB_DEBUG=1'])}


def run(cmd):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def page(site):
    site = pathlib.Path(site)
    shell = site/'index.template.html'
    text = (WGRENDER/'examples/web/index.html').read_text()
    text = text.replace('params.get("ex") || "hello"', 'params.get("ex") || "simple"')
    text = text.replace('<title>wgrender examples</title>', '<title>simple (wgrender, Beef)</title>')
    shell.write_text(text)
    run(['python3', WGRENDER/'tools/webdeploy.py', site, shell])
    shell.unlink()


def build(kind):
    config, make_vars = KINDS[kind]
    run(['make', '--no-print-directory', '-s', '-C', WGRENDER, 'all', 'WEB=1', 'WEB_THREADS=0', *make_vars])
    run([BEEF_BUILD, f'-workspace={ROOT}', f'-config={config}', '-platform=wasm32'])
    site = ROOT/'build'/('web' if kind == 'release' else 'web-debug')
    for f in ('simple.js', 'simple.wasm'):
        print(f'{f}: {(site/f).stat().st_size:,} bytes')
    print(f'built {site}: ./serve_web.sh{"" if kind == "release" else " 8000 build/web-debug"}, '
          'then open http://localhost:8000/')


def main():
    args = sys.argv[1:]
    if args[:1] == ['page'] and len(args) == 2:
        page(args[1])
    elif len(args) <= 1 and (args or ['release'])[0] in KINDS:
        build((args or ['release'])[0])
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
