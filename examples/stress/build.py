#!/usr/bin/env python3
"""Build this example (named for its directory): wgrender's library first, then the
Beef workspace. Every example's build.py is this same file.

    ./build.py web [release | debug]     out/web/webgl2-nothreads[-debug]/
    ./build.py desktop [release | debug] out/linux/release/<name> (out/linux/debug,
                                         out/windows/msvc[-debug] on Windows)
    ./build.py serve [port] [site]       serve the web build on http://localhost:8000/ with
                                         wgrender's dev server (examples/assets at /assets)
    ./build.py check [site]              load the web build in a headless browser: fail on a
                                         console error or a blank screen; the screenshot
                                         goes to build/web/<variant>/check.png

wgrender's library comes from wgrender's own build: the web one from its
tools/buildweb.py (emcc and Python), the desktop one from CMake: on Linux its
`linux-release` preset, on Windows its `windows-msvc` or `windows-msvc-debug` preset
(Beef links with MSVC's linker, which can't take MinGW objects), in Visual Studio's own
environment (found with vswhere). Those use the static C runtime a Beef project links
by default (/MT, /MTd). Each is in wgrender's out/<platform>/<variant>/ (its work in
build/), the wg* family layout (whirlinggizmo/.github CONVENTIONS.md, "Build directories").

The IDE builds the same thing (pick the wasm32, Linux64 or Win64 platform), but can't build
wgrender first: a pre-build step runs after BeefBuild has decided whether to relink.
So after changing wgrender, run this before building in the IDE. BeefBuild relinks
when libwgrender.a changes (it's in LibPaths).

BeefBuild links into its own build/<Config>_<Platform>/<name>/, beside its
intermediates (its LTO cache, emit archive, build notes), and no setting moves it. So
every config in BeefProj.toml calls back into this script after linking, and the IDE's
builds land in out/ too:

    ./build.py install BUILT OUT   copy the program (and its .pdb on Windows) from BUILT
                                   to OUT, out/<platform>/<variant>/
    ./build.py page BUILT SITE     copy <name>.js and .wasm from BUILT to SITE and write
                                   SITE/index.html: wgrender's page with this example as
                                   the default program, versioned by wgrender's webdeploy.py

wgrender is the repository's submodule, project/lib/wgrender-c: BeefProj.toml's
LibPaths name it, so unlike the other bindings there is no WGRENDER_DIR here. To try a
different wgrender, check it out in the submodule.

Env: BEEF_BUILD (the compiler; default BeefBuild on PATH).
"""
import base64
import os
import pathlib
import shutil
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
WINDOWS = os.name == 'nt'
PLATFORM = 'Win64' if WINDOWS else 'Linux64'


# BeefProj.toml's post-build steps run this script again: on this Python, rather than
# whatever python3 is on the path (on Windows, perhaps the Microsoft Store's alias)
BEEF_ENV = dict(os.environ, WGR_PYTHON=sys.executable)


def run(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def need_wgrender():
    if not (WGRENDER / 'include/wgr.h').exists():
        sys.exit(f'no wgrender at {WGRENDER}: git submodule update --init')


def install(built, out):
    """The program, and on Windows its debug info (the .pdb the .exe names, which a
    debugger also looks for beside it), from BeefBuild's directory to out/."""
    built, out = pathlib.Path(built), pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = [built / (NAME + ('.exe' if WINDOWS else ''))] + sorted(built.glob(f'{NAME}*.pdb'))
    for f in files:
        shutil.copy2(f, out / f.name)
    print(f'installed {", ".join(f.name for f in files)} -> {out}')


def page(built, site):
    built, site = pathlib.Path(built), pathlib.Path(site)
    site.mkdir(parents=True, exist_ok=True)
    for f in (f'{NAME}.js', f'{NAME}.wasm'):
        shutil.copy2(built / f, site / f)
    shell = site / 'index.template.html'
    text = (WGRENDER / 'examples/web/index.html').read_text()
    text = text.replace('params.get("ex") || "hello"', f'params.get("ex") || "{NAME}"')
    text = text.replace('<title>wgrender examples</title>', f'<title>{NAME} (wgrender, Beef)</title>')
    shell.write_text(text)
    run([sys.executable, WGRENDER / 'tools/webdeploy.py', site, shell])
    shell.unlink()


def web_site(kind):
    """The web build's directory, out/web/<variant>/ (the wg* layout: what a build makes
    in out/<platform>/<variant>/, its work in build/), as BeefProj.toml's post-build step
    names it."""
    return 'out/web/webgl2-nothreads' + ('' if kind == 'release' else '-debug')


def desktop_out(kind):
    """The desktop build's directory: out/linux/release, out/windows/msvc-debug, ..."""
    if WINDOWS:
        return 'out/windows/msvc' + ('' if kind == 'release' else '-debug')
    return 'out/linux/' + kind


def web(kind):
    config, debug = KINDS[kind]
    need_wgrender()
    # webgl2 without threads: the Beef objects aren't built with atomics
    run([sys.executable, WGRENDER / 'tools/buildweb.py', 'BACKEND=webgl2', 'WEB_THREADS=0', f'WEB_DEBUG={debug}'],
        cwd=WGRENDER)
    run([BEEF_BUILD, f'-workspace={ROOT}', f'-config={config}', '-platform=wasm32'], env=BEEF_ENV)
    site = ROOT / web_site(kind)
    for f in (f'{NAME}.js', f'{NAME}.wasm'):
        print(f'{f}: {(site / f).stat().st_size:,} bytes')
    print(f'built {site}: ./build.py serve{"" if kind == "release" else " 8000 " + web_site(kind)}, '
          'then open http://localhost:8000/')


def vcvars():
    """Visual Studio's vcvars64.bat, found with the vswhere every install has."""
    vswhere = pathlib.Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
                           'Microsoft Visual Studio/Installer/vswhere.exe')
    if not vswhere.exists():
        sys.exit('no Visual Studio (vswhere.exe): Beef on Windows links with MSVC')
    install = subprocess.run([str(vswhere), '-latest', '-products', '*', '-requires',
                              'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'],
                             capture_output=True, text=True).stdout.strip()
    bat = pathlib.Path(install, 'VC/Auxiliary/Build/vcvars64.bat')
    if not install or not bat.exists():
        sys.exit('no Visual Studio with the C++ tools (vcvars64.bat)')
    return bat


def msvc_library(kind):
    """wgrender's library from its windows-msvc preset: MSVC, and the static C runtime
    Beef links."""
    preset = 'windows-msvc' if kind == 'release' else 'windows-msvc-debug'
    configure = f'cd /d "{WGRENDER}" && cmake --preset {preset}'
    build = f'cmake --build --preset {preset} --target wgrender'
    # vcvars's own exit code isn't to be trusted, so `&`; the build's is
    command = f'call "{vcvars()}" >nul & {configure} >nul && {build}'
    print('+', command, flush=True)
    if subprocess.run(command, shell=True).returncode != 0:
        sys.exit('building wgrender with MSVC failed')


def link_assets():
    """assets/ beside this example: wgrender's examples/assets, which the desktop build
    loads relative to the working directory. A link made here rather than committed:
    git checks a symlink out on Windows as a text file naming its target. A directory
    junction there, which needs no administrator or developer mode; a symlink elsewhere."""
    link, target = ROOT / 'assets', WGRENDER / 'examples/assets'
    if link.is_dir():
        return
    if link.exists() or link.is_symlink():
        link.unlink()  # a symlink git checked out as a file, or a broken link
    if WINDOWS:
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], check=True, stdout=subprocess.DEVNULL)
    else:
        link.symlink_to(os.path.relpath(target, ROOT))
    print(f'assets -> {target}')


def desktop(kind):
    config, _ = KINDS[kind]
    need_wgrender()
    link_assets()
    if WINDOWS:
        msvc_library(kind)
    else:
        # wgrender's linux-release preset, as far as the library: out/linux/release/libwgrender.a
        run(['cmake', '--preset', 'linux-release'], cwd=WGRENDER, stdout=subprocess.DEVNULL)
        run(['cmake', '--build', '--preset', 'linux-release', '--target', 'wgrender'], cwd=WGRENDER)
    run([BEEF_BUILD, f'-workspace={ROOT}', f'-config={config}', f'-platform={PLATFORM}'], env=BEEF_ENV)
    print(f'built {ROOT / desktop_out(kind) / NAME}: run it from {ROOT} (assets/ is here)')


def serve(port='8000', site=None):
    site = site or web_site('release')
    need_wgrender()
    sys.exit(subprocess.run([sys.executable, str(WGRENDER / 'tools/serve.py'), port, str(ROOT / site)]).returncode)


def check(site=None):
    """Serve the web build, load it in a headless browser for 8 s, move the mouse over
    the middle of the canvas, and fail on a console error, an uncaught exception, the
    browser's own error log, a program that never started (wgrender logs its backend
    when it does), or a screen of one colour (wgrender's tools/weblib.py)."""
    need_wgrender()
    site = site or web_site('release')
    missing = [f for f in (f'{NAME}.js', f'{NAME}.wasm') if not (ROOT / site / f).exists()]
    if missing:
        sys.exit(f'FAILED: {site} has no {" or ".join(missing)}: build it first (./build.py web)')
    sys.path.insert(0, str(WGRENDER / 'tools'))
    import weblib
    processes = weblib.RunProcesses(f'beef-{NAME}')
    errors, lines, started = [], [], []
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
                if 'libwgrender:' in text and 'backend' in text:
                    started.append(text)
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
        # the check's work, beside the build's: build/web/<variant>/check.png
        out = ROOT / 'build/web' / pathlib.Path(site).name / 'check.png'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(data))
        if not started:
            errors.append('the program never started (wgrender logged no backend)')
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
    if cmd == 'page' and len(rest) == 2:
        page(*rest)
    elif cmd == 'install' and len(rest) == 2:
        install(*rest)
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
