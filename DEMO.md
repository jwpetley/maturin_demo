# Walkthrough for the Software and Tools Demo

## Goal and preparation

**Main message:** keep Python as the application layer, implement selected work
in Rust, and call it through normal Python imports. Maturin builds and installs
the extension; PyO3 provides the bindings between Python and Rust.

Allow about 30 minutes. Run commands from the repository root. The shell
examples below use Bash on Linux, macOS, or WSL; for this checkout, use an Ubuntu
WSL terminal rather than Windows Python.

Before presenting, make sure Python 3.10+, Rust, and Cargo are available:

```bash
python3 --version
rustc --version
cargo --version
```

Create a virtual environment if needed, activate it, and install the project
with its development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

This installation already compiles the extension using maturin. Prepare it
before the session so dependency downloads do not interrupt the tutorial.

## 1. Project structure

Open these files while explaining the two halves of the project:

| File or directory | What to point out |
| --- | --- |
| [pyproject.toml](pyproject.toml) | Python dependencies, maturin build backend, and the extension's Python import name. |
| [Cargo.toml](Cargo.toml) | Rust dependencies and the `_native` library, built as a `cdylib`. |
| [src/lib.rs](src/lib.rs) | Rust implementations and PyO3 module registration. |
| [python/maturin_demo/](python/maturin_demo/) | Importable Python package, Flask app, and browser assets. |
| [python/tests/](python/tests/) | Python/Rust result parity and web endpoint tests. |

Highlight these settings in [pyproject.toml](pyproject.toml):

```toml
[tool.maturin]
python-source = "python"
module-name = "maturin_demo._native"
```

The distribution installed by pip is called `maturin-flask-demo`, but the Python
import is `maturin_demo`. Its `_native` submodule is the compiled Rust extension.
There is no separate Rust service to start.

## 2. Python code overview

1. Open [benchmarks.py](python/maturin_demo/benchmarks.py). Start with
   `sum_squares_python`: an ordinary Python loop adding the squares from 1
   through `n`. The other examples count primes, sum multiples of 3 or 5 below
   a limit, and calculate a Fibonacci checksum.
2. Open [__init__.py](python/maturin_demo/__init__.py). Show that `sum_squares`
   and the other numeric Rust functions are imported from `._native` and
   re-exported alongside the Python implementations. The caller does not need
   to know how the extension was built.
3. Open [models.py](python/maturin_demo/models.py). `Position` and `Portfolio`
   are Python dataclasses. Compare `Portfolio.value_python()` with
   `Portfolio.value_rust()`: the latter passes `self` to
   `_native.portfolio_value(self)`.
4. Briefly show [external_crate.py](python/maturin_demo/external_crate.py) and
   [web.py](python/maturin_demo/web.py). Python generates the sample data and
   runs the Flask application; the web comparisons call the same native
   functions that we will call from the REPL.

**Talking point:** this is incremental adoption, not a rewrite of the Python
application.

## 3. Rust code overview

Open [src/lib.rs](src/lib.rs) and trace `sum_squares`:

```rust
#[pyfunction]
fn sum_squares(n: u64) -> u64 {
    let mut total = 0_u64;
    for value in 1..=n {
        total += value * value;
    }
    total
}
```

- The algorithm mirrors the Python version.
- `#[pyfunction]` creates the Python-callable binding.
- PyO3 converts the Python argument into `u64` and the result back into a
  Python integer. Rust's fixed-width integers do not have Python's arbitrary
  precision; use the tutorial inputs rather than arbitrarily large values.
- At the bottom of the file, `#[pymodule] fn _native(...)` defines the module,
  and `module.add_function(wrap_pyfunction!(sum_squares, module)?)` registers
  the function. Annotating a function alone does not add it to the module.

Then show the two richer examples:

- `portfolio_value` accepts a Python object as `Bound<PyAny>`, reads attributes
  with `getattr`, and extracts typed values. This is explicit attribute access,
  not automatic conversion of a Python dataclass into a Rust struct. Errors
  propagate back to Python through `PyResult`.
- `count_tags` uses the existing `regex` and `rayon` crates declared in
  [Cargo.toml](Cargo.toml). It caches the regex, uses `py.detach` to release
  the GIL while scanning lines in parallel, and returns a Rust `HashMap` that
  PyO3 converts into a Python dictionary. Not every function in this file
  releases the GIL.

## 4. Building the Rust code with Cargo

In the activated environment, run:

```bash
cargo check
cargo build
```

Explain the distinction:

- `cargo check` checks the Rust code without producing the final library.
- `cargo build` compiles the library into Cargo's build output under `target/`.
- `cargo run` is not applicable: this repository has a library target, not a
  binary with a `main` function.
- A Cargo build alone does not install or update the importable extension in
  the virtual environment. Use maturin for that step.

## 5. Maturin develop and the Python REPL

### Build and install into the active environment

```bash
maturin develop
python
```

`maturin develop` builds the Rust extension and installs it into the active
virtual environment. Start with this development build; use
`maturin develop --release` later when comparing performance.

### Call Rust functions as ordinary Python functions

Type the lines after `>>>`; the following lines show expected results:

```pycon
>>> import maturin_demo as demo
>>> demo.sum_squares(10)
385
>>> demo.count_primes(30)
10
>>> demo.sum_multiples(10)
23
>>> demo.fibonacci_checksum(10)
143
>>> demo.sum_squares(1_000) == demo.sum_squares_python(1_000)
True
```

**Pause here:** these calls execute the compiled Rust implementations, directly
inside the Python process. Flask is not running and is not required.

### Discover and inspect the native functions

```pycon
>>> from maturin_demo import _native
>>> sorted(name for name in dir(_native) if not name.startswith("_"))
['count_primes', 'count_tags', 'fibonacci_checksum', 'portfolio_value', 'sum_multiples', 'sum_squares']
>>> demo.sum_squares is _native.sum_squares
True
>>> demo.sum_squares.__module__
'maturin_demo._native'
>>> import inspect
>>> inspect.isbuiltin(demo.sum_squares)
True
>>> str(inspect.signature(demo.sum_squares))
'(n)'
```

Also try these interactively:

```python
help(_native.sum_squares)
print(_native.__file__)
```

`help` shows the callable and its signature; there is no descriptive docstring
on this Rust function yet. The module path points to a native extension file
(`.so` on Linux/macOS, `.pyd` on Windows), not a Python implementation.
`inspect.getsource` cannot retrieve its Rust source; open
[src/lib.rs](src/lib.rs) instead. Use `q` if the help pager opens.

### Pass Python-owned objects into Rust

```pycon
>>> portfolio = demo.make_portfolio(10)
>>> type(portfolio).__name__
'Portfolio'
>>> type(portfolio.positions[0]).__name__
'Position'
>>> portfolio.value_rust() == portfolio.value_python()
True
>>> _native.portfolio_value(portfolio) == portfolio.value_python()
True
```

The object remains a Python dataclass. Its Rust-backed method is a normal Python
method delegating to the native function. Return to the attribute extraction in
[src/lib.rs](src/lib.rs) to connect the call to its implementation.

### Get a Python dictionary from existing Rust crates

```pycon
>>> text = "#rust #python #rust\n#maturin #python"
>>> sorted(_native.count_tags(text).items())
[('maturin', 1), ('python', 2), ('rust', 2)]
>>> _native.count_tags(text) == demo.count_tags_python(text)
True
```

Sort the items for display because Rust `HashMap` iteration order is not fixed.
The returned object is a normal Python dictionary.

### Show the type boundary

```python
demo.sum_squares(-1)
```

This raises `OverflowError` because a negative Python integer cannot be
converted into Rust's unsigned `u64`. The exact message can vary by version.
The binding performs conversions; it does not make the two languages' numeric
types identical.

### Rebuild, test, and show the application

Exit the REPL before rebuilding:

```pycon
>>> exit()
```

For performance comparisons, install an optimized build, then run the checks
and start the website:

```bash
maturin develop --release
pytest
python -m maturin_demo
```

Open <http://127.0.0.1:5000> and walk through **Benchmarks**, **Custom structs**,
and **Existing Rust crate**. Start with small inputs. Results are checked for
equality before timing; the UI reports median timings. Speedups depend on the
workload, build profile, conversion overhead, and machine, so do not promise a
fixed multiplier. Stop the development server with `Ctrl+C`.

**Development loop:** edit Rust, leave any running REPL/server, run
`maturin develop` (or `maturin develop --release`), then start a fresh Python
process. An already-loaded native module is not refreshed by rebuilding or by
`importlib.reload`.

### Quick recovery notes

- **Cannot import `maturin_demo` or `_native`:** activate the same virtual
  environment used to build, run `maturin develop`, and restart Python.
- **Unsure which Python is running:** execute
  `import sys; print(sys.executable)` in the REPL. Keep the interpreter,
  virtual environment, and compiler in the same OS environment; do not mix
  Windows Python with this checkout's WSL virtual environment.
- **Rust edits appear to have no effect:** rebuild with maturin, not just
  Cargo, and restart the REPL or server.

**Closing message:** Cargo manages the Rust library, PyO3 exposes its functions,
and maturin makes that library importable from Python. The application and
interactive workflow remain Python-first.