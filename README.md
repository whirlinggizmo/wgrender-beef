# wgrender-beef

[wgrender](https://github.com/whirlinggizmo/wgrender-c) for
[Beef](https://www.beeflang.org/): as much of the API as the `simple` example needs,
which makes it wgrender's Beef entry in the cross-binding benchmarks. It is not a
complete binding yet.

```
BeefProj.toml, src/wgr/  the binding: the `wgr` library project (Wgr.bf, hand-written)
examples/simple/         the port of wgrender's examples/simple.c: its workspace, its
                         project (depends on wgr) and build.py
examples/stress/         the port of wgrender's benchmark scene, tools/bench/stress.c
                         (every example's build.py is the same file)
project/lib/wgrender-c   wgrender, pinned (git submodule)
tools/benchmarks.py      this port against the C -> docs/benchmarks.md
```

## Build

```sh
git clone --recursive https://github.com/whirlinggizmo/wgrender-beef.git
cd wgrender-beef/examples/simple
python3 build.py web       # build/web/: simple.js + simple.wasm, wgrender's page shell
python3 build.py serve     # http://localhost:8000/
python3 build.py check     # load the web build in a headless browser, fail on errors
python3 build.py desktop   # build/Release_Linux64/simple/ (Release_Win64 on Windows); run it from here
```

BeefBuild, Python, and wgrender's own tools: Emscripten for the web, CMake and a C
compiler for the desktop. What to install, the IDE, and which wgrender is used:
[BUILDING.md](BUILDING.md).

## Benchmarks

`tools/benchmarks.py` builds `simple` and `stress` for the web and measures them with
wgrender's harness (`tools/bench/` in wgrender), against wgrender's C baseline, into
`bench/results.json` and [docs/benchmarks.md](docs/benchmarks.md). Run wgrender's own
`tools/benchmarks.py --all` to refresh every binding at once, or its plain run first
and then this one. By hand, not in CI; the stress scene needs Xvfb and a GPU.
