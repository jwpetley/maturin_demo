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

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The Benchmarks tab has two examples: summing squares and counting primes. Choose one of the fixed input sizes and run the Python/Rust comparison. Each side is measured three times and the median is shown; results are checked for equality before timing. The Rust sum-of-squares loop uses `std::hint::black_box` to keep the optimizer from replacing this tiny arithmetic loop with a closed-form result. These measurements are illustrative and depend on the machine and system load.

The endpoint only accepts a named example and one of its preset input sizes. It does not execute submitted code or accept arbitrary workload sizes. The local Flask server is for development; use a WSGI server for shared deployments.

## Project structure

- `pyproject.toml` defines Python package metadata, dependencies, tests, and maturin's mixed-project settings.
- `Cargo.toml` and `src/lib.rs` define the PyO3 extension built as a Rust dynamic library.
- `python/maturin_demo/benchmarks.py` contains pure-Python implementations, while `web.py` contains the Flask routes and comparison logic.
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
