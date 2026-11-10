use pyo3::prelude::*;

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

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(sum_squares, module)?)?;
    module.add_function(wrap_pyfunction!(count_primes, module)?)?;
    Ok(())
}
