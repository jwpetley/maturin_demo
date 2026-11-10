import pytest

from maturin_demo import (
    count_primes,
    count_primes_python,
    fibonacci_checksum,
    fibonacci_checksum_python,
    sum_multiples,
    sum_multiples_python,
    sum_squares,
    sum_squares_python,
    summarize_trades,
    summarize_trades_python,
    Trade,
)
from maturin_demo.benchmarks import make_trade_rows


@pytest.mark.parametrize("n", [0, 1, 25, 2_000_000])
def test_sum_squares_matches_python(n: int) -> None:
    assert sum_squares(n) == sum_squares_python(n)


@pytest.mark.parametrize("limit", [0, 1, 2, 10, 100, 100_000])
def test_count_primes_matches_python(limit: int) -> None:
    assert count_primes(limit) == count_primes_python(limit)


@pytest.mark.parametrize("limit", [0, 1, 3, 10_000, 2_000_000])
def test_sum_multiples_matches_python(limit: int) -> None:
    assert sum_multiples(limit) == sum_multiples_python(limit)


@pytest.mark.parametrize("terms", [0, 1, 2, 100, 1_000_000])
def test_fibonacci_checksum_matches_python(terms: int) -> None:
    assert fibonacci_checksum(terms) == fibonacci_checksum_python(terms)


@pytest.mark.parametrize("count", [0, 1, 100, 10_000])
def test_trade_struct_aggregation_matches_python(count: int) -> None:
    rows = make_trade_rows(count)
    python_trades = [Trade(unit_price, quantity) for unit_price, quantity in rows]

    assert summarize_trades(rows) == summarize_trades_python(python_trades)
