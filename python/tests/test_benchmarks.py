import pytest

from maturin_demo import (
    count_primes,
    count_primes_python,
    sum_squares,
    sum_squares_python,
)


@pytest.mark.parametrize("n", [0, 1, 25, 2_000_000])
def test_sum_squares_matches_python(n: int) -> None:
    assert sum_squares(n) == sum_squares_python(n)


@pytest.mark.parametrize("limit", [0, 1, 2, 10, 100, 100_000])
def test_count_primes_matches_python(limit: int) -> None:
    assert count_primes(limit) == count_primes_python(limit)
