import pytest

from maturin_demo.web import create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_home_page_shows_examples_and_maturin_tab(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Sum of squares" in page
    assert "Count prime numbers" in page
    assert "Sum multiples of 3 or 5" in page
    assert "Fibonacci checksum" in page
    assert "Custom structs" in page
    assert "Classes in Python. Structs in Rust." in page
    assert "What is maturin?" in page
    assert "fn count_primes" in page
    assert 'role="tablist"' in page


@pytest.mark.parametrize(
    ("example", "preset", "expected"),
    [
        ("sum_squares", "small", 41_667_916_675_000),
        ("count_primes", "small", 9_592),
    ],
)
def test_run_benchmark_returns_matching_result(
    client, example: str, preset: str, expected: int
) -> None:
    response = client.post(
        "/api/run", json={"example": example, "preset": preset}
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["result"] == expected
    assert result["python_seconds"] > 0
    assert result["rust_seconds"] > 0
    assert result["speedup"] > 0


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"example": "not-an-example", "preset": "small"},
        {"example": [], "preset": "small"},
        {"example": "sum_squares", "preset": "not-a-preset"},
        {"example": "sum_squares", "preset": []},
        {"example": "sum_squares", "preset": 2_000_000_000},
    ],
)
def test_run_benchmark_rejects_unlisted_inputs(client, payload) -> None:
    response = client.post("/api/run", json=payload)

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_run_benchmark_rejects_malformed_json(client) -> None:
    response = client.post(
        "/api/run", data="{", content_type="application/json"
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_run_collection_benchmark_returns_aggregate_and_timings(client) -> None:
    response = client.post("/api/run-collection", json={"preset": "small"})

    assert response.status_code == 200
    result = response.get_json()
    assert result["input_value"] == 10_000
    assert result["result"]["records"] == 10_000
    assert result["result"]["total_notional"] > 0
    assert result["python_seconds"] > 0
    assert result["rust_seconds"] > 0
    assert result["speedup"] > 0


@pytest.mark.parametrize("payload", [None, {}, {"preset": []}, {"preset": "huge"}])
def test_run_collection_benchmark_rejects_unlisted_sizes(client, payload) -> None:
    response = client.post("/api/run-collection", json=payload)

    assert response.status_code == 400
    assert "error" in response.get_json()
