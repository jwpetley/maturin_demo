def sum_squares_python(n: int) -> int:
    total = 0
    for value in range(1, n + 1):
        total += value * value
    return total


def count_primes_python(limit: int) -> int:
    if limit < 2:
        return 0

    is_prime = bytearray(b"\x01") * (limit + 1)
    is_prime[0:2] = b"\x00\x00"
    candidate = 2
    while candidate <= limit // candidate:
        if is_prime[candidate]:
            start = candidate * candidate
            count = (limit - start) // candidate + 1
            is_prime[start : limit + 1 : candidate] = b"\x00" * count
        candidate += 1

    return sum(is_prime)


def sum_multiples_python(limit: int) -> int:
    total = 0
    for value in range(limit):
        if value % 3 == 0 or value % 5 == 0:
            total += value
    return total


def fibonacci_checksum_python(terms: int) -> int:
    previous, current = 0, 1
    total = 0
    for _ in range(terms):
        total = (total + current) % 1_000_000_007
        previous, current = current, (previous + current) % 1_000_000_007
    return total
