# wgrender-beef

[wgrender](https://github.com/whirlinggizmo/wgrender-c) for
[Beef](https://www.beeflang.org/): as much of the API as the `simple` example needs,
which makes it wgrender's Beef entry in the cross-binding benchmarks. It is not a
complete binding yet.

```
BeefProj.toml, src/      the binding: the `wgr` library project (Wgr.bf, hand-written)
examples/simple/         the port of wgrender's examples/simple.c: its workspace, its
                         project (depends on wgr) and build.py
project/lib/wgrender-c   wgrender, pinned (git submodule)
tools/benchmarks.py      this port against the C -> docs/benchmarks.md
```

## Build

```sh
git clone --recursive https://github.com/whirlinggizmo/wgrender-beef.git
cd wgrender-beef/examples/simple
./build.py web           # build/web/: simple.js + simple.wasm, wgrender's page shell
./build.py serve         # http://localhost:8000/
./build.py desktop       # build/Release_Linux64/simple/ (Linux; run it from here, beside assets/)
node check_web.mjs       # load the web build in a headless browser, fail on errors
```

It needs BeefBuild (`BEEF_BUILD` names another), Emscripten for the web, and wgrender's
own requirements (see its README). The IDE opens `examples/simple` as a workspace.
wgrender is the submodule only: `BeefProj.toml` links it by path, so to try another
wgrender, check it out there.

## Benchmarks

`tools/benchmarks.py` builds `simple` for the web and measures it with wgrender's
harness (`tools/bench/` in wgrender), against wgrender's C baseline, into
`bench/results.json` and [docs/benchmarks.md](docs/benchmarks.md). Run wgrender's own
`tools/benchmarks.py` first on the same machine; its doc collects this one's results
from a sibling checkout. By hand, not in CI.
