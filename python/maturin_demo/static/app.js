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
    const example = button.dataset.example;
    const preset = document.getElementById(`preset-${example}`).value;
    const resultPanel = document.querySelector(`[data-result="${example}"]`);
    button.disabled = true;
    button.textContent = "Running…";
    resultPanel.textContent = "Running both implementations…";
    resultPanel.classList.add("is-running");

    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ example, preset }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "The benchmark could not be completed.");
      }

      const pythonMs = result.python_seconds * 1000;
      const rustMs = result.rust_seconds * 1000;
      const comparison = result.speedup === null
        ? "The Rust run was too short to time reliably"
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
      detail.textContent =
        `Result: ${result.result.toLocaleString()} · ` +
        `Python ${pythonMs.toFixed(3)} ms · Rust ${rustMs.toFixed(3)} ms`;
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
