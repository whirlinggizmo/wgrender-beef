# Building wgrender-beef

Each example's `build.py` builds wgrender's library first, with wgrender's own tools,
then the Beef workspace with BeefBuild. There is no make and no shell script.

## What you need

- BeefBuild (Beef 0.43; `BEEF_BUILD` names another), with the wasm32 platform set up
  for web builds (Beef's Emscripten path in its configuration). This is developed with
  [robknopf/Beef](https://github.com/robknopf/Beef), a fork of beefytech/Beef whose
  changes are the Linux IDE and debugger (LLDB hot reload, stepping); the command-line
  builds here use nothing of it that upstream doesn't have.
- for the web: Emscripten (emsdk), with `emcc` on `PATH`. wgrender's web library is
  built by its `tools/buildweb.py`, on the Python emsdk brings.
- for the desktop: CMake 3.21 or newer and a C compiler, which build wgrender's
  library (its `desktop` preset); on Linux, the system's GL, X11 and ALSA dev packages,
  which sokol links: `python3 project/lib/wgrender-c/tools/deps.py install` (apt, dnf or
  pacman)
- Python 3
- for `build.py check`: a Chromium-based browser (Brave, Chrome, Chromium or Edge); the
  check is Python, so there is no Node to install

The examples build for Linux (Linux64) and the web (wasm32). There are no Windows or
macOS configurations in the example projects yet.

## Build an example

```sh
git clone --recursive https://github.com/whirlinggizmo/wgrender-beef.git
cd wgrender-beef/examples/simple      # or examples/stress
python3 build.py web          # build/web/: simple.js + simple.wasm, wgrender's page shell
python3 build.py web debug    # build/web-debug/: no optimization, assertions
python3 build.py serve        # http://localhost:8000/ (assets at /assets)
python3 build.py check        # load build/web in a headless browser, fail on errors
python3 build.py desktop      # build/Release_Linux64/simple/ (run it from here, beside assets/)
```

The web build is WebGL2 without threads: the Beef objects aren't built with atomics, so
they can't link into shared memory.

The IDE opens an example's directory as a workspace and builds the same thing (pick the
wasm32 or Linux64 platform), but it can't build wgrender first: a pre-build step runs
after BeefBuild has decided whether to relink. So after changing wgrender, run
`build.py` before building in the IDE.

## Which wgrender

The submodule, `project/lib/wgrender-c`, and only that: the example projects link its
library by path (`LibPaths` in `BeefProj.toml`: `build/desktop/libwgrender.a` from the
CMake preset, `build/webgl2-nothreads[-debug]/libwgrender.a` from buildweb.py). To try
another wgrender, check it out in the submodule.

## Benchmarks

`python3 tools/benchmarks.py` builds `simple` and `stress` for the web and measures them
with wgrender's harness (`tools/bench/` in wgrender) against wgrender's C baseline (run
wgrender's `tools/benchmarks.py` first), into `bench/results.json` and
[docs/benchmarks.md](docs/benchmarks.md). By hand, not in CI; the stress scene needs
Xvfb and a GPU.
