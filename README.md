# Maturin Flask Demo

A small project for exploring Python and Rust together with [maturin](https://www.maturin.rs/). The Rust library is exposed to Python as a native extension using PyO3; Python remains the application layer.

## Requirements

- Python 3.10 or newer
- Rust and Cargo (install with [rustup](https://rustup.rs/))
- maturin 1.8 or newer

## Build and test the extension

From the project root, create and activate a virtual environment, then install the project and its development dependencies. A Rust toolchain is required because the package's maturin build backend compiles the extension during installation.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The PEP 517 build backend is maturin. It compiles the Rust crate and installs the Python package into the virtual environment. For iterative Rust development, rebuild the extension with:

```bash
maturin develop
```

Run the parity tests with:

```bash
pytest
```

## Run the website

Start the local Flask development server from the project root:

```bash
python -m maturin_demo
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The Benchmarks tab compares four functions: summing squares, counting primes, summing multiples of 3 or 5, and calculating a Fibonacci checksum. Each example shows both implementations and the Python call into `_native`. Choose one of the fixed input sizes and run the Python/Rust comparison. Results are checked for equality before timing, then each implementation is measured three times and the median is shown. Very short calls are batched to improve timer resolution.

The Rust code does not use `std::hint::black_box`: the extension's return value is observed by Python, so the results cannot be discarded. The release optimizer may still transform an algorithm while preserving its result—for example, it can replace the sum-of-squares loop with an equivalent formula. The page labels this result instead of presenting it as a loop-for-loop speedup. In general, timings compare the actual Python implementation with optimized compiled Rust, not necessarily identical machine-level steps. Treat them as an illustration of the result of moving a workload to Rust, not a controlled loop-by-loop microbenchmark.

The Custom structs tab focuses on a Python-first workflow: `Portfolio` and `Position` are normal Python dataclasses, and `Portfolio.value_rust()` calls `_native.portfolio_value(self)`. Maturin builds and packages the extension; PyO3 is the binding layer that accepts the Python object as `Bound<PyAny>`, reads `positions` and each required attribute with `getattr(...)?`, and converts values to typed Rust integers with `extract()?`. There is no automatic conversion of an arbitrary Python class into a Rust struct; the binding explicitly defines which attributes and types it needs. Missing attributes and incompatible values become Python errors. Both methods run the same 12-step CPU-heavy pricing calculation. The comparison excludes portfolio construction but includes Rust's attribute lookup and extraction overhead.

The endpoints only accept named examples and preset input sizes. They do not execute submitted code or accept arbitrary workload sizes. The local Flask server is for development; use a WSGI server for shared deployments.

## Project structure

- `pyproject.toml` defines Python package metadata, dependencies, tests, and maturin's mixed-project settings.
- `Cargo.toml` and `src/lib.rs` define the PyO3 extension built as a Rust dynamic library.
- `python/maturin_demo/benchmarks.py` contains pure-Python function implementations; `python/maturin_demo/models.py` contains the Python-owned portfolio classes and the direct call into the native method.
- `python/maturin_demo/templates/` and `static/` hold the page, styles, and browser behavior.
- `python/tests/` checks result parity, the page, and the benchmark endpoint.

Keeping the Rust crate at the repository root lets maturin build it directly, while `python/` keeps the importable package separate from Rust's `src/` directory. Flask and the web demo use the same installed Python package and native extension.

## Run with Docker

Build the image from the project root and publish its port:

```bash
docker build -t maturin-flask-demo .
docker run --rm -p 5000:5000 maturin-flask-demo
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000). The multi-stage Docker build compiles the extension in a Python environment with Rust tooling, then copies the wheel into a smaller runtime image. The app runs under Waitress as a non-root user.
