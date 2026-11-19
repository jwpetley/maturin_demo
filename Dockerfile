FROM python:3.12-slim-bookworm AS builder

ENV PATH="/root/.cargo/bin:${PATH}"
WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup-init.sh \
    && sh /tmp/rustup-init.sh -y --profile minimal --default-toolchain stable \
    && rm /tmp/rustup-init.sh

COPY pyproject.toml Cargo.toml Cargo.lock README.md ./
COPY src/ src/
COPY python/ python/

FROM builder AS dev

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:/root/.cargo/bin:${PATH}"

RUN python -m venv "$VIRTUAL_ENV" \
    && python -m pip install --no-cache-dir -e ".[dev]"

CMD ["/bin/sh"]

FROM builder AS wheel-builder

RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /wheels .

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=wheel-builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels \
    && useradd --create-home --uid 10001 app

USER app
EXPOSE 5000

CMD ["waitress-serve", "--listen=0.0.0.0:5000", "--call", "maturin_demo.web:create_app"]
