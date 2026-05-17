PEP Talk #3. Slug: pep-talk-03-pep-684.

The article covers PEP 684: A Per-Interpreter GIL (Python 3.12), and uses PEP 734's
`concurrent.interpreters` module (Python 3.14) as the user-facing surface for
demonstrating what PEP 684 actually buys you.

Framing: this is one of two big "GIL is finally moving" PEPs landing right now. PEP
703 (the no-GIL / free-threaded build) tends to get more press, but PEP 684 is the
other path: keep the GIL, but give every subinterpreter its *own* GIL so multiple
interpreters can run Python bytecode in parallel on different cores in the same
process. The two PEPs are complementary, not rivals.

Key content points:

1. The GIL refresher: one lock that serializes Python bytecode execution across
   threads in a process. Why it exists (cheap refcount-based memory management,
   simple C extension story), why it hurts (no multi-core scaling for pure-Python
   CPU work). The classic workarounds: `multiprocessing` (heavy, IPC overhead),
   native threads in C extensions that release the GIL (great for NumPy, useless
   for your code), `asyncio` (concurrency, not parallelism).

2. Two ways out: PEP 703 vs PEP 684.
   - PEP 703: free-threaded build, removes the GIL entirely. Different binary
     (`python3.14t`), needs every C extension recompiled with the no-GIL ABI,
     incurs single-threaded performance overhead from new locking.
   - PEP 684: keep the GIL, but make it per-interpreter. Same binary, no ABI
     break, opt-in via creating new interpreters. Multi-core parallelism, but at
     the granularity of interpreters not threads — and interpreters don't share
     objects.
   Acknowledge both are landing; this post is about PEP 684.

3. What subinterpreters are (the missing context). They've been in CPython's C
   API for ~25 years (`Py_NewInterpreter` since Python 1.5). Each one has its
   own `sys.modules`, its own imported state, its own classes. Pre-3.12 they
   still *shared one GIL*, so they were good for isolation (e.g. embedding
   Python in Apache mod_wsgi) but useless for parallelism. PEP 684 fixes that.

4. PEP 684 in one sentence: move the runtime state the GIL protects out of
   process globals and into `PyInterpreterState`, then let each interpreter
   carry its own GIL. Eric Snow's work. Landed in Python 3.12 (2023).

5. The C-API surface (briefly, so readers know it exists):
   `PyInterpreterConfig`, `Py_NewInterpreterFromConfig`, the `own_gil` flag.
   Mention `PyInterpreterConfig_INIT` (own GIL, isolated) vs
   `PyInterpreterConfig_LEGACY_INIT` (shared GIL, legacy behavior). Don't
   linger here — most readers don't write C extensions.

6. The Python-level surface: PEP 734's `concurrent.interpreters` module
   (Python 3.14). This is what you actually touch. Walk through:
   - `interpreters.create()` returns an `Interpreter`
   - `interp.exec(code)` runs source synchronously in the subinterpreter
   - `interp.call(callable)` for a function (currently no-arg, plain functions only)
   - `interp.call_in_thread(callable)` to run in a fresh OS thread inside the subinterpreter
   - `interp.prepare_main(**kwargs)` to seed `__main__` with starting values
   - `interp.close()` to tear down
   Make clear this module *is* available in 3.13 too, but as `interpreters`
   (provisional); the stable home is `concurrent.interpreters` in 3.14.

7. Hello-world subinterpreter:

   ```python
   from concurrent import interpreters

   interp = interpreters.create()
   interp.exec("print('hello from another interpreter')")
   interp.close()
   ```

   Note that this runs in the *current* OS thread and blocks. Parallelism comes
   from `call_in_thread`.

8. A real parallel example: CPU-bound work across N interpreters in N threads,
   showing actual wall-clock speedup vs the same code on regular threads. The
   key thing readers should *feel* is that pure-Python CPU work finally scales
   with cores without `multiprocessing`. Roughly:

   ```python
   from concurrent import interpreters
   import threading, time

   CODE = """
   total = 0
   for i in range(N):
       total += i * i
   results.put(total)
   """

   results = interpreters.create_queue()
   N = 50_000_000

   def worker():
       interp = interpreters.create()
       interp.prepare_main(N=N, results=results)
       interp.exec(CODE)
       interp.close()

   threads = [threading.Thread(target=worker) for _ in range(4)]
   t0 = time.perf_counter()
   for t in threads: t.start()
   for t in threads: t.join()
   print(f"4 interpreters: {time.perf_counter() - t0:.2f}s")
   ```

   Compare against running the same loop four times sequentially, or in four
   regular `threading.Thread` instances (which won't speed up because of the
   single shared GIL). Show approximate numbers and the intuition.

9. Isolation: what subinterpreters do NOT share.
   - No shared `sys.modules`. Each interpreter re-imports.
   - No shared global state. A module-level dict in one is invisible in another.
   - No shared object identity. You can't pass a regular Python object across.
   This sounds like a downside, but it's the *whole point*: shared mutable state
   would force a shared GIL.

10. Cross-interpreter communication.
    - `interpreters.create_queue()`: a Queue that lives outside any one
      interpreter and ferries data across.
    - What's "shareable": pickleable objects are sent as their underlying data
      (copy-on-send), buffer-protocol objects (memoryview, numpy arrays via
      buffer) actually share memory — this is how you avoid copy overhead for
      large payloads.
    - `prepare_main(**kwargs)`: passes shareable values into the subinterpreter
      before exec.

11. Gotchas / current limitations.
    - C extension compatibility. Extensions must use multi-phase init (PEP 489)
      to load in a subinterpreter, and even that doesn't guarantee they're safe
      under a per-interpreter GIL if they have C-level global state. NumPy in
      particular: getting closer but not all the way there yet — check status
      when you read this. (Don't speculate about exact NumPy version status; tell
      reader to check.)
    - Startup cost. Spinning up an interpreter is much more expensive than
      starting a thread. You want a pool, not a fresh interpreter per task.
    - `call()` is still restrictive: plain functions, no args (in 3.14 — this is
      expected to grow). Use `exec` + `prepare_main` + a queue for richer
      patterns today.
    - Memory: each interpreter has its own copy of stdlib modules it imports.
      Multiplies memory use.
    - It's not magic concurrency. You still write the parallel decomposition
      yourself; this is parallelism *primitive*, not a parallel framework.

12. When to reach for PEP 684 vs alternatives.
    - Use subinterpreters for: in-process parallelism with isolation guarantees,
      embedded scenarios (one host process, many sandboxed plugins), workloads
      where you want `multiprocessing`-style isolation without IPC + pickle +
      process startup overhead.
    - Use threads + native release-the-GIL libs for: numeric / I/O work where
      the heavy lifting is already in C (numpy, requests, etc).
    - Use `multiprocessing` for: pre-3.14 environments, or when you genuinely
      need OS-level isolation (separate address spaces, separate crashes).
    - Use free-threaded build (PEP 703) when: you need shared objects + true
      thread parallelism and you're OK with experimental territory and rebuilt
      C extensions.

13. The bigger picture. After ~30 years the GIL is finally not the only story.
    PEP 684 + PEP 734 give you parallel Python via isolated interpreters; PEP
    703 gives you parallel Python via removing the GIL. Both are real, both are
    landing in shipping CPython, and you can start playing with the per-
    interpreter GIL story *today* without recompiling anything.

Series format: PEP Talk series structure (emoji-wrapped H2 headers, hook+quote
opening, series index linking to #1 and #2, Take Home Points, default book plug
for the multi-agent AI book, closing greeting). Languages used so far in PEP
Talk: Greek (#1), Swedish (#2). Pick a fresh one — Italian (Arrivederci amici!)
is a good fit, energetic and matches the "finally getting somewhere" vibe.

Categories: Python, PEP, Concurrency
Date: 2026-05-17

Images:
- hero.png: bright, energetic hero image. Visual concept: a single Python logo
  cracking open into multiple smaller Python interpreters running side by side,
  each on its own CPU core, suggesting parallelism. Confident retro-comic style,
  vibrant colors, no text.
- diagram-gil-paths.png: xkcd-style diagram comparing three paths to multi-core
  Python: (left) classic single-GIL threading with a queue of threads waiting on
  one lock, (middle) PEP 684 with several interpreter "bubbles" each holding
  their own GIL running in parallel, (right) PEP 703 free-threaded with shared
  objects and no GIL. Light background, hand-drawn labels.
- diagram-interpreter-isolation.png: xkcd-style diagram of two subinterpreters
  side by side, each with its own `sys.modules`, its own globals, its own GIL,
  connected only by a Queue in the middle and a prepare_main arrow. Make the
  isolation visually obvious — bubbles around each interpreter's state.

Keep under 2500 words. Sprinkle 3-4 emojis in the opening hook. No em-dashes.
No markdown tables.
