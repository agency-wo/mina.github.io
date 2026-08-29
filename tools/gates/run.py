#!/usr/bin/env python3
# [PERF-005] run.py — every gate, one process, one corpus read.
# DOES:   Loads each gate by path, calls its main(), collects the exit code, prints one summary.
#         Exits 1 if any gate failed, so CI and a Stop hook can both read it.
# IN:     python tools/gates/run.py [--all] [gate ...]   (bare = all of them)
# OUT:    each gate's own output verbatim, then a PASS/FAIL table and the wall-time.
# WHY:    Eight separate interpreter startups cost ~0.7 s before a single file is read, and each
#         process threw away the corpus the previous one had just walked. Running them in one
#         process is what lets corpus.py's cache span gates, which is where the real win is.
# NOTES:  GATE FILENAMES ARE HYPHENATED, so `import audit-watches` is a syntax error and every
#         gate must be loaded with spec_from_file_location. Not a style choice.
#         Every gate's main() ends in sys.exit(), so each call is wrapped in except SystemExit.
#         `findings` is a MODULE-LEVEL GLOBAL in every gate, so each is import-once/call-once.
#         Calling one twice in a process accumulates findings and reports a false failure.
#         verify-stats reads sys.argv AT IMPORT TIME to bind ALL, so argv is set before loading.
#         test_sync_stock stays a subprocess: it is a unittest module and calls unittest.main(),
#         which owns argv and the exit path.
#         NEVER import gen_product_pages - it has no __main__ guard and regenerates every
#         product page on import.
import importlib.util
import io
import subprocess
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]

# Order is the cheap-first order, so a fast failure surfaces before the slow gates run.
GATES = ["verify-chain", "verify-product-pages", "verify-blog-index", "verify-contact",
         "audit-watches", "faq-build", "verify-sitemap", "verify-stats"]

# Entry point per gate. Six expose main() and exit; faq-build exposes cmd_verify() and RETURNS
# its code, because the file is also the FAQ builder and its __main__ is an argparse dispatch.
ENTRY = {"faq-build": "cmd_verify"}


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_one(name):
    argv = sys.argv[:]
    sys.argv = [f"{name}.py"] + (["--verify"] if name == "faq-build" else [])
    if "--all" in argv:
        sys.argv.append("--all")
    buf = io.StringIO()
    rc = 0
    try:
        mod = load(name)                      # import time is when verify-stats binds ALL
        fn = getattr(mod, ENTRY.get(name, "main"))
        with redirect_stdout(buf):
            ret = fn()
        # some gates exit, some return their code; honour whichever this one does
        if isinstance(ret, int):
            rc = ret
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception as e:                    # a crashed gate is a failed gate, never a pass
        buf.write(f"  GATE CRASHED: {type(e).__name__}: {e}\n")
        rc = 1
    finally:
        sys.argv = argv
    return rc, buf.getvalue()


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("-")] or GATES
    t0 = time.time()
    results = []
    for name in want:
        t1 = time.time()
        rc, out = run_one(name)
        sys.stdout.write(out)
        results.append((name, rc, out.strip().splitlines()[-1] if out.strip() else "",
                        (time.time() - t1) * 1000))

    # unittest owns argv and the exit path, so this one stays a child process
    r = subprocess.run([sys.executable, str(BASE / "tools" / "test_sync_stock.py")],
                       capture_output=True, text=True)
    tail = (r.stderr or r.stdout).strip().splitlines()
    results.append(("test_sync_stock", r.returncode, tail[-1] if tail else "", 0.0))

    ms = (time.time() - t0) * 1000
    print("\n" + "=" * 72)
    for name, rc, last, el in results:
        print(f"  {'PASS' if rc == 0 else 'FAIL'}  {name:<22} {el:>6.0f} ms  {last[:40]}")
    bad = [n for n, rc, _, _ in results if rc]
    try:
        import corpus
        c = corpus.raw.cache_info()
        print(f"\n  corpus: {c.hits + c.misses} reads served from {c.misses} actual file opens")
    except Exception:
        pass
    print(f"  {len(results) - len(bad)}/{len(results)} passed in {ms:.0f} ms")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    sys.exit(main())
