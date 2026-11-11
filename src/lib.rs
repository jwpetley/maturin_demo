use pyo3::exceptions::{PyOverflowError, PyValueError};
use pyo3::prelude::*;

#[pyfunction]
fn sum_squares(n: u64) -> u64 {
    let mut total = 0_u64;
    for value in 1..=n {
        total += value * value;
    }
    total
}

#[pyfunction]
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
}

#[pyfunction]
fn sum_multiples(limit: u64) -> u64 {
    let mut total = 0_u64;
    for value in 0..limit {
        if value % 3 == 0 || value % 5 == 0 {
            total += value;
        }
    }
    total
}

#[pyfunction]
fn fibonacci_checksum(terms: u64) -> u64 {
    let (mut previous, mut current) = (0_u64, 1_u64);
    let mut total = 0_u64;
    for _ in 0..terms {
        total = (total + current) % 1_000_000_007;
        (previous, current) = (current, (previous + current) % 1_000_000_007);
    }
    total
}

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
    module.add_function(wrap_pyfunction!(sum_squares, module)?)?;
    module.add_function(wrap_pyfunction!(count_primes, module)?)?;
    module.add_function(wrap_pyfunction!(sum_multiples, module)?)?;
    module.add_function(wrap_pyfunction!(fibonacci_checksum, module)?)?;
    module.add_function(wrap_pyfunction!(portfolio_value, module)?)?;
    Ok(())
}
