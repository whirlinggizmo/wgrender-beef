#!/usr/bin/env python3
"""Build this example (named for its directory): wgrender's library first, then the
Beef workspace. Every example's build.py is this same file.

    ./build.py web [release | debug]     build/web (default) or build/web-debug
    ./build.py desktop [release | debug] build/Release_Linux64/<name>/ (or Debug_...)
    ./build.py serve [port] [site]       serve build/web on http://localhost:8000/ with
                                         wgrender's dev server (examples/assets at /assets)
    ./build.py check [site]              load build/web in a headless browser: fail on a
                                         console error or a blank screen; the screenshot
                                         goes to build/web-check.png

wgrender's library comes from wgrender's own build: the web one from its
tools/buildweb.py (emcc and Python), the desktop one from its `desktop` CMake preset.
The IDE builds the same thing (pick the wasm32 or Linux64 platform), but can't build
wgrender first: a pre-build step runs after BeefBuild has decided whether to relink.
So after changing wgrender, run this before building in the IDE. BeefBuild relinks
when libwgrender.a changes (it's in LibPaths).

BeefProj.toml's wasm32 configs call back into this script after linking:

    ./build.py page SITE      write SITE/index.html: wgrender's page with this example as the
                              default program, versioned by wgrender's webdeploy.py

wgrender is the repository's submodule, project/lib/wgrender-c: BeefProj.toml's
LibPaths name it, so unlike the other bindings there is no WGRENDER_DIR here. To try a
different wgrender, check it out in the submodule.

Env: BEEF_BUILD (the compiler; default BeefBuild on PATH).
"""
import base64
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent
NAME = ROOT.name
WGRENDER = (ROOT / '../../project/lib/wgrender-c').resolve()
BEEF_BUILD = os.environ.get('BEEF_BUILD', 'BeefBuild')
KINDS = {'release': ('Release', '0'), 'debug': ('Debug', '1')}


def run(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def need_wgrender():
    if not (WGRENDER / 'include/wgr.h').exists():
        sys.exit(f'no wgrender at {WGRENDER}: git submodule update --init')


def page(site):
    site = pathlib.Path(site)
    shell = site / 'index.template.html'
    text = (WGRENDER / 'examples/web/index.html').read_text()
    text = text.replace('params.get("ex") || "hello"', f'params.get("ex") || "{NAME}"')
    text = text.replace('<title>wgrender examples</title>', f'<title>{NAME} (wgrender, Beef)</title>')
    shell.write_text(text)
    run([sys.executable, WGRENDER / 'tools/webdeploy.py', site, shell])
    shell.unlink()


def web(kind):
    config, debug = KINDS[kind]
    need_wgrender()
    # webgl2 without threads: the Beef objects aren't built with atomics
    run([sys.executable, WGRENDER / 'tools/buildweb.py', 'BACKEND=webgl2', 'WEB_THREADS=0', f'WEB_DEBUG={debug}'],
        cwd=WGRENDER)
    run([BEEF_BUILD, f'-workspace={ROOT}', f'-config={config}', '-platform=wasm32'])
    site = ROOT / 'build' / ('web' if kind == 'release' else 'web-debug')
    for f in (f'{NAME}.js', f'{NAME}.wasm'):
        print(f'{f}: {(site / f).stat().st_size:,} bytes')
    print(f'built {site}: ./build.py serve{"" if kind == "release" else " 8000 build/web-debug"}, '
          'then open http://localhost:8000/')


def desktop(kind):
    config, _ = KINDS[kind]
    need_wgrender()
    # wgrender's desktop CMake preset, as far as the library: build/desktop/libwgrender.a
    run(['cmake', '--preset', 'desktop'], cwd=WGRENDER, stdout=subprocess.DEVNULL)
    run(['cmake', '--build', '--preset', 'desktop', '--target', 'wgrender'], cwd=WGRENDER)
    run([BEEF_BUILD, f'-workspace={ROOT}', f'-config={config}', '-platform=Linux64'])
    print(f'built {ROOT / "build" / f"{config}_Linux64/{NAME}"}: run it from {ROOT} (assets/ is here)')


def serve(port='8000', site='build/web'):
    need_wgrender()
    sys.exit(subprocess.run([sys.executable, str(WGRENDER / 'tools/serve.py'), port, str(ROOT / site)]).returncode)


def check(site='build/web'):
    """Serve the web build, load it in a headless browser for 8 s, move the mouse over
    the middle of the canvas, and fail on a console error, an uncaught exception, the
    browser's own error log, or a screen of one colour (wgrender's tools/weblib.py)."""
    need_wgrender()
    sys.path.insert(0, str(WGRENDER / 'tools'))
    import weblib
    processes = weblib.RunProcesses(f'beef-{NAME}')
    errors, lines = [], []
    try:
        port = weblib.free_port()
        processes.spawn([weblib.PYTHON, WGRENDER / 'tools/serve.py', port, ROOT / site])
        weblib.wait_for(f'http://127.0.0.1:{port}/examples.json', 'tools/serve.py')
        debug_base, browser = weblib.launch_browser(processes, weblib.find_browser(), 'headless')
        target = browser.send('Target.createTarget', {'url': 'about:blank'})['targetId']
        tab = weblib.open_session(f'ws://{urllib.parse.urlsplit(debug_base).netloc}/devtools/page/{target}')

        def on_event(msg):
            p = msg.get('params', {})
            if msg['method'] == 'Runtime.consoleAPICalled':
                text = ' '.join(str(a['value']) if 'value' in a else a.get('description', '') for a in p['args'])
                lines.append(text)
                if p.get('type') == 'error' or re.search(r'\[(ERROR|FATAL)', text):
                    errors.append(text)
            elif msg['method'] == 'Runtime.exceptionThrown':
                d = p['exceptionDetails']
                errors.append((d.get('exception') or {}).get('description') or d.get('text'))
            elif msg['method'] == 'Log.entryAdded' and p['entry']['level'] == 'error' \
                    and p['entry']['source'] != 'network':
                errors.append(f'[{p["entry"]["source"]}] {p["entry"].get("text", "")}')

        tab.on_event(on_event)
        for domain in ('Runtime', 'Log', 'Page'):
            tab.send(f'{domain}.enable')
        tab.send('Page.navigate', {'url': f'http://127.0.0.1:{port}/'})
        time.sleep(8)
        # the middle of the canvas (below the page's 38px bar), a little low: over the model
        x, y = tab.send('Runtime.evaluate', {
            'expression': "(() => { const r = document.getElementById('canvas').getBoundingClientRect();"
                          " return [r.left + r.width / 2, r.top + r.height / 2 + 20]; })()",
            'returnByValue': True})['result']['value']
        tab.send('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y})
        time.sleep(1)
        data = tab.send('Page.captureScreenshot', {'format': 'png'})['data']
        out = ROOT / 'build/web-check.png'
        out.write_bytes(base64.b64decode(data))
        if weblib.distinct_colours(tab, data) < 2:
            errors.append(f'the screen is one flat colour: nothing was drawn ({out})')
        for line in lines:
            print(f'  console: {line}')
        print(f'screenshot: {out}')
    finally:
        processes.stop()
    if errors:
        sys.exit('FAILED:\n  ' + '\n  '.join(str(e) for e in errors))
    print('ok')


def main():
    args = sys.argv[1:]
    cmd, rest = (args[0], args[1:]) if args else ('web', [])
    if cmd == 'page' and len(rest) == 1:
        page(rest[0])
    elif cmd in ('web', 'desktop') and len(rest) <= 1 and (rest or ['release'])[0] in KINDS:
        (web if cmd == 'web' else desktop)((rest or ['release'])[0])
    elif cmd == 'serve' and len(rest) <= 2:
        serve(*rest)
    elif cmd == 'check' and len(rest) <= 1:
        check(*rest)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as e:  # weblib's: a browser or server that didn't come up
        sys.exit(f'build.py: {e}')
