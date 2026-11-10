# Maturin Flask Demo

A small project for exploring Python and Rust together with [maturin](https://www.maturin.rs/). The Rust library is exposed to Python as a native extension using PyO3; Python remains the application layer.

## Requirements

- Python 3.10 or newer
- Rust and Cargo (install with [rustup](https://rustup.rs/))
- maturin 1.8 or newer

## Build and test the extension

From the project root, create and activate a virtual environment, then install the project and its development dependencies:

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

## Project structure

- `pyproject.toml` defines Python package metadata, dependencies, tests, and maturin's mixed-project settings.
- `Cargo.toml` and `src/lib.rs` define the PyO3 extension built as a Rust dynamic library.
- `python/maturin_demo/` contains the Python package and pure-Python implementations used for comparison.
- `python/tests/` checks that the Rust and Python implementations return matching values.

Keeping the Rust crate at the repository root lets maturin build it directly, while `python/` keeps the importable package separate from Rust's `src/` directory. Flask and the web demo will use the same installed Python package and native extension.
