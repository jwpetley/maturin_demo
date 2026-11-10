use pyo3::prelude::*;

struct Trade {
    unit_price: u64,
    quantity: u64,
}

#[pyfunction]
fn sum_squares(n: u64) -> u64 {
    let mut total = std::hint::black_box(0_u64);
    for value in 1..=n {
        total = std::hint::black_box(total + value * value);
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
    let mut total = std::hint::black_box(0_u64);
    for value in 0..limit {
        if value % 3 == 0 || value % 5 == 0 {
            total = std::hint::black_box(total + value);
        }
    }
    total
}

#[pyfunction]
fn fibonacci_checksum(terms: u64) -> u64 {
    let (mut previous, mut current) = (0_u64, 1_u64);
    let mut total = 0_u64;
    for _ in 0..terms {
        total = std::hint::black_box(total + current);
        total %= 1_000_000_007;
        (previous, current) = (current, (previous + current) % 1_000_000_007);
    }
    total
}

#[pyfunction]
fn summarize_trades(rows: Vec<(u64, u64)>) -> (u64, usize) {
    let trades = rows.into_iter().map(|(unit_price, quantity)| Trade {
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
}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(sum_squares, module)?)?;
    module.add_function(wrap_pyfunction!(count_primes, module)?)?;
    module.add_function(wrap_pyfunction!(sum_multiples, module)?)?;
    module.add_function(wrap_pyfunction!(fibonacci_checksum, module)?)?;
    module.add_function(wrap_pyfunction!(summarize_trades, module)?)?;
    Ok(())
}
