import inspect
import statistics
import timeit
from collections.abc import Callable

from flask import Flask, jsonify, render_template, request

from . import _native
from .benchmarks import (
    Trade,
    count_primes_python,
    fibonacci_checksum_python,
    make_trade_rows,
    sum_multiples_python,
    sum_squares_python,
    summarize_trades_python,
)

PRESETS = {
    "small": "Small",
    "medium": "Medium",
    "large": "Large",
}

RUST_SOURCES = {
    "sum_squares": """#[pyfunction]
fn sum_squares(n: u64) -> u64 {
    let mut total = std::hint::black_box(0_u64);
    for value in 1..=n {
        total = std::hint::black_box(total + value * value);
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
    let mut total = std::hint::black_box(0_u64);
    for value in 0..limit {
        if value % 3 == 0 || value % 5 == 0 {
            total = std::hint::black_box(total + value);
        }
    }
    total
}""",
    "fibonacci_checksum": """#[pyfunction]
fn fibonacci_checksum(terms: u64) -> u64 {
    let (mut previous, mut current) = (0_u64, 1_u64);
    let mut total = 0_u64;
    for _ in 0..terms {
        total = std::hint::black_box(total + current);
        total %= 1_000_000_007;
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
    {"key": "small", "label": "Small — 10,000 records", "value": 10_000},
    {"key": "medium", "label": "Medium — 100,000 records", "value": 100_000},
    {"key": "large", "label": "Large — 500,000 records", "value": 500_000},
]
COLLECTION_PYTHON_SOURCE = (
    inspect.getsource(Trade)
    + "\n\n"
    + inspect.getsource(summarize_trades_python)
)
COLLECTION_RUST_SOURCE = """struct Trade {
    unit_price: u64,
    quantity: u64,
}

#[pyfunction]
fn summarize_trades(rows: Vec<(u64, u64)>) -> (u64, usize) {
    let trades = rows
        .into_iter()
        .map(|(unit_price, quantity)| Trade {
            unit_price,
            quantity,
        });
    let mut total_notional = 0_u64;
    let mut count = 0;
    for trade in trades {
        total_notional += trade.unit_price * trade.quantity;
        count += 1;
    }
    (total_notional, count)
}"""


def _median_runtime(function: Callable[[], object]) -> float:
    return statistics.median(
        timeit.repeat(function, repeat=3, number=1)
    )


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

        rows = make_trade_rows(preset["value"])
        python_trades = [Trade(unit_price, quantity) for unit_price, quantity in rows]
        python_function = lambda: summarize_trades_python(python_trades)
        rust_function = lambda: _native.summarize_trades(rows)
        python_result = python_function()
        rust_result = rust_function()
        if python_result != rust_result:
            return jsonify(error="The Python and Rust results did not match."), 500

        python_seconds = _median_runtime(python_function)
        rust_seconds = _median_runtime(rust_function)
        speedup = python_seconds / rust_seconds if rust_seconds else None

        return jsonify(
            input_value=preset["value"],
            result={"total_notional": python_result[0], "records": python_result[1]},
            python_seconds=python_seconds,
            rust_seconds=rust_seconds,
            speedup=speedup,
        )

    return app
