const form = document.getElementById("scrapeForm");
const inputDir = document.getElementById("inputDir");
const outputFile = document.getElementById("outputFile");
const invalidFile = document.getElementById("invalidFile");
const resultBox = document.getElementById("resultBox");
const statusPill = document.getElementById("statusPill");
const loadDefaults = document.getElementById("loadDefaults");
const resetForm = document.getElementById("resetForm");
const pickInput = document.getElementById("pickInput");
const pickOutput = document.getElementById("pickOutput");
const pickInvalid = document.getElementById("pickInvalid");
const refreshHistory = document.getElementById("refreshHistory");
const historyBox = document.getElementById("historyBox");

const setStatus = (text, state) => {
  statusPill.textContent = text;
  statusPill.classList.remove("success", "error", "working");
  if (state) {
    statusPill.classList.add(state);
  }
};

const renderResult = (html) => {
  resultBox.innerHTML = html;
};

const setFormDisabled = (disabled) => {
  Array.from(form.elements).forEach((el) => {
    el.disabled = disabled;
  });
};

const downloadLink = (path, label) => {
  const encoded = encodeURIComponent(path);
  return `<a class="download-link" href="/download?path=${encoded}">${label}</a>`;
};

const loadDefaultValues = async () => {
  try {
    const res = await fetch("/defaults");
    const data = await res.json();
    inputDir.value = data.input || "";
    outputFile.value = data.output || "";
    invalidFile.value = data.invalid || "";
  } catch (err) {
    renderResult("<p>Could not load defaults.</p>");
  }
};

const loadHistory = async () => {
  try {
    const res = await fetch("/history");
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      historyBox.innerHTML = "<p>No history yet.</p>";
      return;
    }

    const rows = data
      .map(
        (item) => `
        <div class="history-item">
          <p><strong>${item.timestamp}</strong> — ${item.status || "unknown"}</p>
          <p>Input: <code>${item.input}</code></p>
          <p>Output: <code>${item.output}</code></p>
          <p>Invalid: <code>${item.invalid}</code></p>
          <div class="download-row">
            ${downloadLink(item.output, "Download Output")}
            ${downloadLink(item.invalid, "Download Invalid")}
          </div>
        </div>
      `
      )
      .join("");

    historyBox.innerHTML = rows;
  } catch (err) {
    historyBox.innerHTML = "<p>Could not load history.</p>";
  }
};

const pickPath = async (endpoint, target) => {
  try {
    const res = await fetch(endpoint);
    const data = await res.json();
    if (data.ok && data.path) {
      target.value = data.path;
    }
  } catch (err) {
    renderResult("<p>Could not open dialog.</p>");
  }
};

loadDefaults.addEventListener("click", (event) => {
  event.preventDefault();
  loadDefaultValues();
});

resetForm.addEventListener("click", () => {
  inputDir.value = "";
  outputFile.value = "";
  invalidFile.value = "";
  renderResult("<p>No runs yet.</p>");
  setStatus("Idle");
});

pickInput.addEventListener("click", () => {
  pickPath("/pick-input", inputDir);
});

pickOutput.addEventListener("click", () => {
  pickPath("/pick-output", outputFile);
});

pickInvalid.addEventListener("click", () => {
  pickPath("/pick-invalid", invalidFile);
});

refreshHistory.addEventListener("click", () => {
  loadHistory();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Running...", "working");
  setFormDisabled(true);
  renderResult("<p>Scraper is running. Please wait.</p>");

  try {
    const res = await fetch("/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        input: inputDir.value.trim(),
        output: outputFile.value.trim(),
        invalid: invalidFile.value.trim(),
      }),
    });

    const data = await res.json();
    if (!res.ok || !data.ok) {
      const msg = data.error || "Unknown error.";
      setStatus("Failed", "error");
      renderResult(`<p>Run failed: ${msg}</p>`);
      if (data.stderr) {
        renderResult(
          `<p>Run failed: ${msg}</p><p><strong>stderr</strong></p><code>${data.stderr}</code>`
        );
      }
      return;
    }

    setStatus("Complete", "success");
    renderResult(
      `<p>Scrape completed successfully.</p>
       <p>Output CSV: <code>${data.output}</code></p>
       <p>Invalid links CSV: <code>${data.invalid}</code></p>
       <div class="download-row">
         ${downloadLink(data.output, "Download Output")}
         ${downloadLink(data.invalid, "Download Invalid")}
       </div>`
    );
    loadHistory();
  } catch (err) {
    setStatus("Failed", "error");
    renderResult("<p>Run failed: network error.</p>");
  } finally {
    setFormDisabled(false);
  }
});

loadDefaultValues();
loadHistory();
