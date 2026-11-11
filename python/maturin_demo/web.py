import inspect
import statistics
import timeit
from collections.abc import Callable

from flask import Flask, jsonify, render_template, request

from . import _native
from .benchmarks import (
    count_primes_python,
    fibonacci_checksum_python,
    sum_multiples_python,
    sum_squares_python,
)
from .external_crate import count_tags_python, make_tag_corpus
from .models import Portfolio, Position, make_portfolio

PRESETS = {
    "small": "Small",
    "medium": "Medium",
    "large": "Large",
}

RUST_SOURCES = {
    "sum_squares": """#[pyfunction]
fn sum_squares(n: u64) -> u64 {
    let mut total = 0_u64;
    for value in 1..=n {
        total += value * value;
    }
    total
}""",
    "count_primes": """#[pyfunction]
fn count_primes(limit: usize) -> usize {
    if limit < 2 {
        return 0;
    }

    let mut is_prime = vec![true; limit + 1];
    is_prime[0] = false;
    is_prime[1] = false;

    let mut candidate = 2;
    while candidate <= limit / candidate {
        if is_prime[candidate] {
            for multiple in (candidate * candidate..=limit).step_by(candidate) {
                is_prime[multiple] = false;
            }
        }
        candidate += 1;
    }

    is_prime.into_iter().filter(|prime| *prime).count()
}""",
    "sum_multiples": """#[pyfunction]
fn sum_multiples(limit: u64) -> u64 {
    let mut total = 0_u64;
    for value in 0..limit {
        if value % 3 == 0 || value % 5 == 0 {
            total += value;
        }
    }
    total
}""",
    "fibonacci_checksum": """#[pyfunction]
fn fibonacci_checksum(terms: u64) -> u64 {
    let (mut previous, mut current) = (0_u64, 1_u64);
    let mut total = 0_u64;
    for _ in 0..terms {
        total = (total + current) % 1_000_000_007;
        (previous, current) = (current, (previous + current) % 1_000_000_007);
    }
    total
}""",
}

EXAMPLES = [
    {
        "key": "sum_squares",
        "name": "Sum of squares",
        "description": "Add the square of every integer from 1 through n.",
        "input_name": "n",
        "python_function": sum_squares_python,
        "rust_function": _native.sum_squares,
        "python_call": "_native.sum_squares(n)",
        "python_source": inspect.getsource(sum_squares_python),
        "rust_source": RUST_SOURCES["sum_squares"],
        "presets": [
            {"key": "small", "label": "Small — 50,000", "value": 50_000},
            {"key": "medium", "label": "Medium — 500,000", "value": 500_000},
            {"key": "large", "label": "Large — 2,000,000", "value": 2_000_000},
        ],
    },
    {
        "key": "count_primes",
        "name": "Count prime numbers",
        "description": "Use the Sieve of Eratosthenes to count primes up to a limit.",
        "input_name": "limit",
        "python_function": count_primes_python,
        "rust_function": _native.count_primes,
        "python_call": "_native.count_primes(limit)",
        "python_source": inspect.getsource(count_primes_python),
        "rust_source": RUST_SOURCES["count_primes"],
        "presets": [
            {"key": "small", "label": "Small — 100,000", "value": 100_000},
            {"key": "medium", "label": "Medium — 500,000", "value": 500_000},
            {"key": "large", "label": "Large — 2,000,000", "value": 2_000_000},
        ],
    },
    {
        "key": "sum_multiples",
        "name": "Sum multiples of 3 or 5",
        "description": "Add the numbers below a limit that are divisible by 3 or 5.",
        "input_name": "limit",
        "python_function": sum_multiples_python,
        "rust_function": _native.sum_multiples,
        "python_call": "_native.sum_multiples(limit)",
        "python_source": inspect.getsource(sum_multiples_python),
        "rust_source": RUST_SOURCES["sum_multiples"],
        "presets": [
            {"key": "small", "label": "Small — 10,000", "value": 10_000},
            {"key": "medium", "label": "Medium — 500,000", "value": 500_000},
            {"key": "large", "label": "Large — 2,000,000", "value": 2_000_000},
        ],
    },
    {
        "key": "fibonacci_checksum",
        "name": "Fibonacci checksum",
        "description": "Sum a fixed number of Fibonacci terms modulo 1,000,000,007.",
        "input_name": "terms",
        "python_function": fibonacci_checksum_python,
        "rust_function": _native.fibonacci_checksum,
        "python_call": "_native.fibonacci_checksum(terms)",
        "python_source": inspect.getsource(fibonacci_checksum_python),
        "rust_source": RUST_SOURCES["fibonacci_checksum"],
        "presets": [
            {"key": "small", "label": "Small — 1,000 terms", "value": 1_000},
            {"key": "medium", "label": "Medium — 100,000 terms", "value": 100_000},
            {"key": "large", "label": "Large — 1,000,000 terms", "value": 1_000_000},
        ],
    },
]

EXAMPLE_BY_KEY = {example["key"]: example for example in EXAMPLES}
COLLECTION_PRESETS = [
    {"key": "small", "label": "Small — 1,000 positions", "value": 1_000},
    {"key": "medium", "label": "Medium — 10,000 positions", "value": 10_000},
    {"key": "large", "label": "Large — 50,000 positions", "value": 50_000},
]
COLLECTION_PYTHON_SOURCE = (
    "from dataclasses import dataclass\nfrom maturin_demo import _native\n\n"
    + inspect.getsource(Position)
    + "\n\n"
    + inspect.getsource(Portfolio)
)
COLLECTION_RUST_SOURCE = """use pyo3::exceptions::{PyOverflowError, PyValueError};
use pyo3::prelude::*;

#[pyfunction]
fn portfolio_value(portfolio: &Bound<'_, PyAny>) -> PyResult<u64> {
    let positions = portfolio.getattr("positions")?;
    let mut total = 0_u64;

    for position in positions.try_iter()? {
        let position = position?;
        let active: bool = position.getattr("active")?.extract()?;
        if !active {
            continue;
        }

        let quantity: u64 = position.getattr("quantity")?.extract()?;
        let unit_price: u64 = position.getattr("unit_price")?.extract()?;
        let fee_bps: u64 = position.getattr("fee_bps")?.extract()?;
        if fee_bps > 10_000 {
            return Err(PyValueError::new_err("fee_bps must be at most 10,000"));
        }

        let mut modeled_value = quantity
            .checked_mul(unit_price)
            .ok_or_else(|| PyOverflowError::new_err("position value overflowed u64"))?;
        for _ in 0..12 {
            modeled_value = modeled_value
                .checked_mul(1_000_003)
                .and_then(|value| value.checked_add(quantity))
                .ok_or_else(|| PyOverflowError::new_err("position model overflowed u64"))?
                % 1_000_000_007;
        }
        let fee = modeled_value
            .checked_mul(fee_bps)
            .ok_or_else(|| PyOverflowError::new_err("position fee overflowed u64"))?
            / 10_000;
        total = total
            .checked_add(modeled_value - fee)
            .ok_or_else(|| PyOverflowError::new_err("portfolio value overflowed u64"))?;
    }
    Ok(total)
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(portfolio_value, module)?)?;
    Ok(())
}"""
CRATE_PRESETS = [
    {"key": "small", "label": "Small — 100 lines", "value": 100},
    {"key": "medium", "label": "Medium — 10,000 lines", "value": 10_000},
    {"key": "large", "label": "Large — 100,000 lines", "value": 100_000},
]
CRATE_CALL_SOURCE = """def count_tags_rust(text: str) -> dict[str, int]:
    return _native.count_tags(text)"""
CRATE_PYTHON_SOURCE = (
    "import re\nfrom collections import Counter\nfrom maturin_demo import _native\n\n"
    + inspect.getsource(count_tags_python)
    + "\n\n"
    + CRATE_CALL_SOURCE
)
CRATE_RUST_SOURCE = """use pyo3::prelude::*;
use rayon::prelude::*;
use regex::Regex;
use std::collections::HashMap;
use std::sync::OnceLock;

static TAG_PATTERN: OnceLock<Regex> = OnceLock::new();

#[pyfunction]
fn count_tags(py: Python<'_>, text: &str) -> HashMap<String, usize> {
    let pattern = TAG_PATTERN.get_or_init(|| {
        Regex::new(r"#([A-Za-z][A-Za-z0-9_]{1,31})")
            .expect("the built-in tag pattern is valid")
    });

    py.detach(|| {
        text.par_lines()
            .fold(HashMap::new, |mut counts, line| {
                for captures in pattern.captures_iter(line) {
                    *counts.entry(captures[1].to_owned()).or_insert(0) += 1;
                }
                counts
            })
            .reduce(HashMap::new, |mut left, right| {
                for (tag, count) in right {
                    *left.entry(tag).or_insert(0) += count;
                }
                left
            })
    })
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(count_tags, module)?)?;
    Ok(())
}"""


def _median_runtime(function: Callable[[], object]) -> float:
    timer = timeit.Timer(function)
    pilot_seconds = timer.timeit(number=1)
    number = max(1, min(100_000, int(0.01 / pilot_seconds)))
    return statistics.median(timer.repeat(repeat=3, number=number)) / number


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            examples=EXAMPLES,
            collection_python_source=COLLECTION_PYTHON_SOURCE,
            collection_rust_source=COLLECTION_RUST_SOURCE,
            collection_presets=COLLECTION_PRESETS,
            collection_call_source="return _native.portfolio_value(self)",
            crate_python_source=CRATE_PYTHON_SOURCE,
            crate_rust_source=CRATE_RUST_SOURCE,
            crate_call_source=CRATE_CALL_SOURCE,
            crate_presets=CRATE_PRESETS,
        )

    @app.post("/api/run")
    def run_benchmark():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Expected a JSON object with example and preset."), 400

        example_key = payload.get("example")
        if not isinstance(example_key, str) or example_key not in EXAMPLE_BY_KEY:
            return jsonify(error="Choose one of the listed examples."), 400
        example = EXAMPLE_BY_KEY[example_key]

        preset_key = payload.get("preset")
        if not isinstance(preset_key, str) or preset_key not in PRESETS:
            return jsonify(error="Choose one of the listed input sizes."), 400

        preset = next(
            item for item in example["presets"] if item["key"] == preset_key
        )
        value = preset["value"]
        python_result = example["python_function"](value)
        rust_result = example["rust_function"](value)
        if python_result != rust_result:
            return jsonify(error="The Python and Rust results did not match."), 500

        python_seconds = _median_runtime(
            lambda: example["python_function"](value)
        )
        rust_seconds = _median_runtime(lambda: example["rust_function"](value))
        speedup = python_seconds / rust_seconds if rust_seconds else None

        return jsonify(
            example=example["name"],
            input_name=example["input_name"],
            input_value=value,
            result=python_result,
            python_seconds=python_seconds,
            rust_seconds=rust_seconds,
            speedup=speedup,
        )

    @app.post("/api/run-collection")
    def run_collection_benchmark():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Expected a JSON object with a preset."), 400

        preset_key = payload.get("preset")
        if not isinstance(preset_key, str):
            return jsonify(error="Choose one of the listed record counts."), 400
        preset = next(
            (item for item in COLLECTION_PRESETS if item["key"] == preset_key),
            None,
        )
        if preset is None:
            return jsonify(error="Choose one of the listed record counts."), 400

        portfolio = make_portfolio(preset["value"])
        python_function = portfolio.value_python
        rust_function = portfolio.value_rust
        python_result = python_function()
        rust_result = rust_function()
        if python_result != rust_result:
            return jsonify(error="The Python and Rust results did not match."), 500

        python_seconds = _median_runtime(python_function)
        rust_seconds = _median_runtime(rust_function)
        speedup = python_seconds / rust_seconds if rust_seconds else None

        return jsonify(
            input_value=preset["value"],
            result={
                "portfolio_value": python_result,
                "positions": len(portfolio.positions),
            },
            python_seconds=python_seconds,
            rust_seconds=rust_seconds,
            speedup=speedup,
        )

    @app.post("/api/run-rust-crate")
    def run_rust_crate():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Expected a JSON object with a preset."), 400

        preset_key = payload.get("preset")
        if not isinstance(preset_key, str):
            return jsonify(error="Choose one of the listed text sizes."), 400
        preset = next(
            (item for item in CRATE_PRESETS if item["key"] == preset_key),
            None,
        )
        if preset is None:
            return jsonify(error="Choose one of the listed text sizes."), 400

        text = make_tag_corpus(preset["value"])
        python_function = lambda: count_tags_python(text)
        rust_function = lambda: _native.count_tags(text)
        python_result = python_function()
        rust_result = rust_function()
        if python_result != rust_result:
            return jsonify(error="The Python and Rust matches did not agree."), 500

        python_seconds = _median_runtime(python_function)
        rust_seconds = _median_runtime(rust_function)
        speedup = python_seconds / rust_seconds if rust_seconds else None
        return jsonify(
            lines=preset["value"],
            result={
                "matches": sum(rust_result.values()),
                "tags": rust_result,
            },
            python_seconds=python_seconds,
            rust_seconds=rust_seconds,
            speedup=speedup,
        )

    return app
