const form = document.querySelector("#humanizer-form");
const sourceText = document.querySelector("#source-text");
const audience = document.querySelector("#audience");
const tone = document.querySelector("#tone");
const submitButton = document.querySelector("#submit-button");
const resetButton = document.querySelector("#reset-button");
const exampleButton = document.querySelector("#example-button");
const copyButton = document.querySelector("#copy-button");
const characterCount = document.querySelector("#character-count");
const wordCount = document.querySelector("#word-count");
const servicePill = document.querySelector("#service-pill");
const serviceStatus = document.querySelector("#service-status");

const states = {
  empty: document.querySelector("#empty-state"),
  loading: document.querySelector("#loading-state"),
  error: document.querySelector("#error-state"),
  result: document.querySelector("#result-state"),
};

const resultCopy = document.querySelector("#result-copy");
const scoreRing = document.querySelector("#score-ring");
const scoreValue = document.querySelector("#score-value");
const scoreLabel = document.querySelector("#score-label");
const passesValue = document.querySelector("#passes-value");
const modelValue = document.querySelector("#model-value");
const resultWordCount = document.querySelector("#result-word-count");
const errorMessage = document.querySelector("#error-message");
const loadingMessage = document.querySelector("#loading-message");

const loadingMessages = [
  "Reworking structure and phrasing",
  "Checking clarity and sentence rhythm",
  "Reviewing the draft against your voice",
];

const exampleText =
  "Furthermore, it is important to note that the implementation of this innovative solution " +
  "will enable organizations to leverage enhanced efficiencies and drive meaningful outcomes " +
  "across their operational ecosystem.";

let loadingTimer;

function countWords(value) {
  const trimmed = value.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

function updateInputCounts() {
  const words = countWords(sourceText.value);
  wordCount.textContent = `${words} ${words === 1 ? "word" : "words"}`;
  characterCount.textContent = `${sourceText.value.length.toLocaleString()} / 12,000`;
}

function showState(name) {
  Object.entries(states).forEach(([key, element]) => {
    element.classList.toggle("is-hidden", key !== name);
  });
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  resetButton.disabled = isLoading;
  exampleButton.disabled = isLoading;
  submitButton.querySelector(".button-label").textContent = isLoading
    ? "Humanizing…"
    : "Humanize text";

  window.clearInterval(loadingTimer);
  if (!isLoading) return;

  let messageIndex = 0;
  loadingMessage.textContent = loadingMessages[messageIndex];
  loadingTimer = window.setInterval(() => {
    messageIndex = (messageIndex + 1) % loadingMessages.length;
    loadingMessage.textContent = loadingMessages[messageIndex];
  }, 2600);
}

async function checkService() {
  try {
    const response = await fetch("/ready", { headers: { Accept: "application/json" } });
    if (response.ok) {
      servicePill.dataset.state = "ready";
      serviceStatus.textContent = "Ready";
      return;
    }
    servicePill.dataset.state = "warning";
    serviceStatus.textContent = "API key needed";
  } catch (_error) {
    servicePill.dataset.state = "warning";
    serviceStatus.textContent = "Service unavailable";
  }
}

function renderResult(data) {
  const roundedScore = Math.round(data.score);
  resultCopy.textContent = data.text;
  scoreValue.textContent = roundedScore;
  scoreRing.style.setProperty("--score-angle", `${Math.min(roundedScore, 100) * 3.6}deg`);
  scoreLabel.textContent = roundedScore >= 90 ? "Natural" : roundedScore >= 80 ? "Polished" : "Refined";
  passesValue.textContent = data.passes;
  modelValue.textContent = data.model;
  modelValue.title = data.model;
  resultWordCount.textContent = countWords(data.text);
  copyButton.disabled = false;
  showState("result");
}

async function humanize(event) {
  event.preventDefault();
  const text = sourceText.value.trim();
  if (!text) {
    sourceText.focus();
    return;
  }

  setLoading(true);
  copyButton.disabled = true;
  showState("loading");

  try {
    const response = await fetch("/humanize", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        text,
        audience: audience.value.trim() || "general readers",
        tone: tone.value,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "The request could not be completed.");
    }
    renderResult(data);
  } catch (error) {
    errorMessage.textContent = error.message || "Check your connection and try again.";
    showState("error");
  } finally {
    setLoading(false);
  }
}

async function copyResult() {
  if (!resultCopy.textContent) return;
  try {
    await navigator.clipboard.writeText(resultCopy.textContent);
    copyButton.querySelector("span").textContent = "Copied";
    window.setTimeout(() => {
      copyButton.querySelector("span").textContent = "Copy";
    }, 1600);
  } catch (_error) {
    copyButton.querySelector("span").textContent = "Select text to copy";
  }
}

function resetWorkspace() {
  form.reset();
  sourceText.value = "";
  audience.value = "general readers";
  resultCopy.textContent = "";
  copyButton.disabled = true;
  updateInputCounts();
  showState("empty");
  sourceText.focus();
}

sourceText.addEventListener("input", updateInputCounts);
sourceText.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    form.requestSubmit();
  }
});
form.addEventListener("submit", humanize);
resetButton.addEventListener("click", resetWorkspace);
copyButton.addEventListener("click", copyResult);
exampleButton.addEventListener("click", () => {
  sourceText.value = exampleText;
  updateInputCounts();
  sourceText.focus();
});

updateInputCounts();
checkService();
