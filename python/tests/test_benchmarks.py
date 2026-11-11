from types import SimpleNamespace

import pytest

from maturin_demo import (
    Portfolio,
    Position,
    count_primes,
    count_primes_python,
    fibonacci_checksum,
    fibonacci_checksum_python,
    sum_multiples,
    sum_multiples_python,
    sum_squares,
    sum_squares_python,
)
from maturin_demo import _native, count_tags_python, make_portfolio, make_tag_corpus


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
def test_python_portfolio_rust_method_matches_python(count: int) -> None:
    portfolio = make_portfolio(count)

    assert portfolio.value_rust() == portfolio.value_python()


def test_native_portfolio_method_accepts_another_python_class_shape() -> None:
    position = Position(
        symbol="ALT", quantity=3, unit_price=1_250, fee_bps=15, active=True
    )
    expected = Portfolio(name="Expected", positions=[position]).value_python()
    custom_position = SimpleNamespace(
        active=position.active,
        quantity=position.quantity,
        unit_price=position.unit_price,
        fee_bps=position.fee_bps,
    )
    custom_portfolio = SimpleNamespace(positions=[custom_position])

    assert _native.portfolio_value(custom_portfolio) == expected


def test_portfolio_rust_method_rejects_missing_python_attributes() -> None:
    with pytest.raises(AttributeError, match="positions"):
        _native.portfolio_value(object())


def test_portfolio_rust_method_rejects_invalid_fee() -> None:
    portfolio = make_portfolio(1)
    portfolio.positions[0] = Position(
        symbol="BAD", quantity=1, unit_price=100, fee_bps=10_001
    )

    with pytest.raises(ValueError, match="fee_bps"):
        portfolio.value_rust()


def test_portfolio_rust_method_rejects_incompatible_python_field() -> None:
    portfolio = make_portfolio(1)
    portfolio.positions[0].active = True
    portfolio.positions[0].quantity = "many"

    with pytest.raises(TypeError):
        portfolio.value_rust()


@pytest.mark.parametrize(
    "text",
    [
        "",
        "#pyo3 #maturin #Rust_2024",
        "skip #x and #9invalid but keep #valid_tag",
        "prefix#embedded and #two##second",
    ],
)
def test_existing_regex_crates_match_python(text: str) -> None:
    assert _native.count_tags(text) == count_tags_python(text)


def test_rust_crate_matches_python_on_generated_corpus() -> None:
    text = make_tag_corpus(100)

    counts = _native.count_tags(text)
    assert counts == count_tags_python(text)
    assert sum(counts.values()) == 500
