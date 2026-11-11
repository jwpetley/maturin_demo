import re
from collections import Counter

TAG_PATTERN = re.compile(r"#([A-Za-z][A-Za-z0-9_]{1,31})")
TAG_SAMPLE = (
    "Ship #pyo3 bindings with #maturin; profile #python, #rust, and #fastpath. "
    "Ignore #9invalid and single-letter #x tags."
)


def count_tags_python(text: str) -> dict[str, int]:
    return dict(Counter(TAG_PATTERN.findall(text)))


def make_tag_corpus(repetitions: int) -> str:
    return "\n".join(TAG_SAMPLE for _ in range(repetitions))
