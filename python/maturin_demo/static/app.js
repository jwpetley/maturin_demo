const tabButtons = document.querySelectorAll(".tab-button");

for (const button of tabButtons) {
  button.addEventListener("click", () => {
    for (const tab of tabButtons) {
      const selected = tab === button;
      tab.classList.toggle("is-active", selected);
      tab.setAttribute("aria-selected", String(selected));
      document.getElementById(tab.dataset.tab).hidden = !selected;
    }
  });
}

for (const button of document.querySelectorAll(".run-button")) {
  button.addEventListener("click", async () => {
    const isCollection = button.dataset.collection === "true";
    const isCrate = button.dataset.crate === "true";
    const example = button.dataset.example;
    const resultKey = isCollection ? "collection" : isCrate ? "crate" : example;
    const preset = document.getElementById(`preset-${resultKey}`).value;
    const resultPanel = document.querySelector(`[data-result="${resultKey}"]`);
    button.disabled = true;
    button.textContent = "Running…";
    resultPanel.textContent = "Running both implementations…";
    resultPanel.classList.add("is-running");

    try {
      const response = await fetch(
        isCollection
          ? "/api/run-collection"
          : isCrate
            ? "/api/run-rust-crate"
            : "/api/run",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(
            isCollection || isCrate ? { preset } : { example, preset },
          ),
        },
      );
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "The benchmark could not be completed.");
      }

      const formatTime = (seconds) => seconds >= 0.001
        ? `${(seconds * 1000).toFixed(3)} ms`
        : `${(seconds * 1_000_000).toFixed(2)} µs`;
      const comparison = result.speedup === null
        ? "The Rust run was too short to time reliably"
        : result.example === "Sum of squares" && result.speedup > 1000
          ? "Rust optimized the loop into an equivalent formula"
        : result.speedup >= 1
          ? `Rust was ${result.speedup.toFixed(1)}× faster in this run`
          : `Python was ${(1 / result.speedup).toFixed(1)}× faster in this run`;
      resultPanel.classList.remove("is-running");
      resultPanel.replaceChildren();

      const summary = document.createElement("strong");
      summary.className = "result-summary";
      summary.textContent = comparison;
      const detail = document.createElement("span");
      detail.className = "result-detail";
      const resultText = result.result.tags !== undefined
        ? `${result.result.matches.toLocaleString()} matches · ` +
          Object.entries(result.result.tags)
            .sort(([left], [right]) => left.localeCompare(right))
            .map(([tag, count]) => `#${tag}: ${count.toLocaleString()}`)
            .join(" · ")
        : typeof result.result === "object"
          ? `Portfolio value: ${result.result.portfolio_value.toLocaleString()} · ` +
            `${result.result.positions.toLocaleString()} positions`
          : `Result: ${result.result.toLocaleString()}`;
      detail.textContent =
        `${resultText} · ` +
        `Python ${formatTime(result.python_seconds)} · ` +
        `Rust ${formatTime(result.rust_seconds)}`;
      resultPanel.append(summary, detail);
    } catch (error) {
      resultPanel.classList.remove("is-running");
      resultPanel.textContent = `Could not run the comparison: ${error.message}`;
    } finally {
      button.disabled = false;
      button.innerHTML = '<span aria-hidden="true">▶</span> Run comparison';
    }
  });
}
