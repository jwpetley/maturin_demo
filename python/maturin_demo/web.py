import inspect
import statistics
import timeit
from collections.abc import Callable

from flask import Flask, jsonify, render_template, request

from . import _native
from .benchmarks import count_primes_python, sum_squares_python

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
]

EXAMPLE_BY_KEY = {example["key"]: example for example in EXAMPLES}


def _median_runtime(function: Callable[[int], int], value: int) -> float:
    return statistics.median(
        timeit.repeat(lambda: function(value), repeat=3, number=1)
    )


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", examples=EXAMPLES)

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

        python_seconds = _median_runtime(example["python_function"], value)
        rust_seconds = _median_runtime(example["rust_function"], value)
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

    return app
