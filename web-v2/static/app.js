const uploadPanel = document.querySelector("#upload-panel");
const fileInput = document.querySelector("#pdf-input");
const editor = document.querySelector("#editor");
const filenameLabel = document.querySelector("#filename");
const pageSummary = document.querySelector("#page-summary");
const pageGrid = document.querySelector("#page-grid");
const selectedCount = document.querySelector("#selected-count");
const selectionTotal = document.querySelector("#selection-total");
const pageTotal = document.querySelector("#page-total");
const notice = document.querySelector("#notice");
const generateButton = document.querySelector("#generate");
const rangeInput = document.querySelector("#page-range");
const themeSelect = document.querySelector("#theme-select");
const accentSelect = document.querySelector("#accent-select");
const columnsSelect = document.querySelector("#columns-select");
const qualitySlider = document.querySelector("#quality-slider");
const qualityValue = document.querySelector("#quality-value");

let activeSession = null;
let pageCount = 0;
let selectedPages = new Set();
let noticeTimer = null;
let qualityTimer = null;
let thumbnailQuality = 60;

const gradientAccents = new Map([
  ["#00B4DB", ["#00B4DB", "#0083B0"]],
  ["#FF5F6D", ["#FF5F6D", "#FFC371"]],
  ["#00B09B", ["#00B09B", "#96C93D"]],
  ["#8E2DE2", ["#8E2DE2", "#4A00E0"]],
  ["#F12711", ["#F12711", "#F5AF19"]],
  ["#F953C6", ["#F953C6", "#B91D73"]],
]);

function applyAppearance() {
  const isDark = themeSelect.value === "dark"
    || (themeSelect.value === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = isDark ? "dark" : "light";

  const accent = accentSelect.value;
  const gradient = gradientAccents.get(accent);
  const accentHover = gradient ? gradient[1] : accent;
  document.documentElement.style.setProperty("--accent", accent);
  document.documentElement.style.setProperty(
    "--accent-background",
    gradient ? `linear-gradient(110deg, ${gradient[0]}, ${gradient[1]})` : accent,
  );
  document.documentElement.style.setProperty("--accent-hover", accentHover);
  document.querySelector('meta[name="theme-color"]').content = isDark ? "#171A21" : "#f5f6fa";
  localStorage.setItem("starz-theme", themeSelect.value);
  localStorage.setItem("starz-accent", accent);
}

function loadAppearance() {
  const savedTheme = localStorage.getItem("starz-theme");
  const savedAccent = localStorage.getItem("starz-accent");
  if (["light", "dark", "system"].includes(savedTheme)) themeSelect.value = savedTheme;
  if ([...accentSelect.options].some((option) => option.value === savedAccent)) {
    accentSelect.value = savedAccent;
  }
  applyAppearance();
}

function setThumbnailQuality(value) {
  thumbnailQuality = Number(value);
  qualityValue.value = `${thumbnailQuality}%`;
  localStorage.setItem("starz-thumbnail-quality", String(thumbnailQuality));

  pageGrid.querySelectorAll(".page-card img").forEach((image) => {
    const loading = image.nextElementSibling;
    image.classList.remove("loaded", "failed");
    loading.textContent = "Loading preview";
    image.addEventListener("load", () => image.classList.add("loaded"), { once: true });
    image.addEventListener("error", () => {
      image.classList.add("failed");
      loading.textContent = "Preview unavailable";
    }, { once: true });
    image.src = `/api/session/${encodeURIComponent(activeSession)}/thumbnail/${image.dataset.pageNumber}?scale=${thumbnailQuality}`;
  });
}

function showNotice(message, success = false) {
  clearTimeout(noticeTimer);
  notice.textContent = message;
  notice.classList.toggle("success", success);
  notice.hidden = false;
  noticeTimer = setTimeout(() => {
    notice.hidden = true;
  }, success ? 7000 : 10000);
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    return typeof body.detail === "string" ? body.detail : "The request failed.";
  } catch {
    return "The request failed. Please try again.";
  }
}

async function uploadPdf(file) {
  if (!file || (!file.type.includes("pdf") && !file.name.toLowerCase().endsWith(".pdf"))) {
    showNotice("Choose a PDF file to get started.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  uploadPanel.classList.add("is-loading");

  try {
    const response = await fetch("/api/upload", { method: "POST", body: formData });
    if (!response.ok) throw new Error(await errorMessage(response));

    const result = await response.json();
    activeSession = result.session_id;
    pageCount = result.page_count;
    selectedPages = new Set(Array.from({ length: pageCount }, (_, index) => index + 1));
    filenameLabel.textContent = result.filename;
    pageSummary.textContent = `${pageCount} ${pageCount === 1 ? "page" : "pages"}`;
    uploadPanel.hidden = true;
    editor.hidden = false;
    notice.hidden = true;
    renderPages();
  } catch (error) {
    showNotice(error.message || "Could not upload this PDF.");
  } finally {
    uploadPanel.classList.remove("is-loading");
    fileInput.value = "";
  }
}

function renderPages() {
  pageGrid.replaceChildren();
  pageTotal.textContent = `${pageCount} ${pageCount === 1 ? "page" : "pages"}`;

  const fragment = document.createDocumentFragment();
  for (let pageNumber = 1; pageNumber <= pageCount; pageNumber += 1) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "page-card";
    card.setAttribute("aria-pressed", String(selectedPages.has(pageNumber)));
    card.setAttribute("aria-label", `Page ${pageNumber}`);

    const image = document.createElement("img");
    image.alt = `Preview of page ${pageNumber}`;
    image.loading = pageNumber <= 12 ? "eager" : "lazy";
    image.dataset.pageNumber = String(pageNumber);
    const loading = document.createElement("span");
    loading.className = "page-loading";
    loading.textContent = "Loading preview";
    image.addEventListener("load", () => image.classList.add("loaded"), { once: true });
    image.addEventListener("error", () => {
      image.classList.add("failed");
      loading.textContent = "Preview unavailable";
    }, { once: true });
    image.src = `/api/session/${encodeURIComponent(activeSession)}/thumbnail/${pageNumber}?scale=${thumbnailQuality}`;

    const label = document.createElement("span");
    label.className = "page-number";
    label.innerHTML = `<span>Page ${pageNumber}</span><span class="page-check" aria-hidden="true">✓</span>`;

    card.append(image, loading, label);
    card.addEventListener("click", () => {
      if (selectedPages.has(pageNumber)) selectedPages.delete(pageNumber);
      else selectedPages.add(pageNumber);
      updateCard(card, pageNumber);
      updateSelectionCount();
    });
    fragment.append(card);
  }

  pageGrid.append(fragment);
  updateSelectionCount();
}

function updateCard(card, pageNumber) {
  const selected = selectedPages.has(pageNumber);
  card.classList.toggle("selected", selected);
  card.setAttribute("aria-pressed", String(selected));
}

function updateSelectionCount() {
  selectedCount.textContent = String(selectedPages.size);
  selectionTotal.textContent = `of ${pageCount} ${pageCount === 1 ? "page" : "pages"} selected`;
  generateButton.disabled = selectedPages.size === 0;
}

function setSelection(pages) {
  selectedPages = new Set(pages);
  pageGrid.querySelectorAll(".page-card").forEach((card, index) => {
    updateCard(card, index + 1);
  });
  updateSelectionCount();
}

function parsePageRange(text) {
  const pages = new Set();
  const entries = text.split(",");
  if (!text.trim() || entries.some((entry) => !entry.trim())) {
    throw new Error("Enter page numbers or ranges, for example 1-8, 11, 14-16.");
  }

  for (const entry of entries) {
    const value = entry.trim();
    const match = value.match(/^(\d+)(?:\s*-\s*(\d+))?$/);
    if (!match) throw new Error(`“${value}” is not a valid page number or range.`);

    const start = Number(match[1]);
    const end = match[2] ? Number(match[2]) : start;
    if (start < 1 || end > pageCount) {
      throw new Error(`Page numbers must be between 1 and ${pageCount}.`);
    }
    if (start > end) throw new Error(`In “${value}”, the first page must be smaller than the last.`);
    for (let page = start; page <= end; page += 1) pages.add(page);
  }

  return pages;
}

async function generateBooklet() {
  generateButton.disabled = true;
  generateButton.querySelector("span:first-child").textContent = "Preparing PDF…";

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: activeSession,
        page_numbers: [...selectedPages].sort((a, b) => a - b),
      }),
    });
    if (!response.ok) throw new Error(await errorMessage(response));

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "booklet.pdf";
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    showNotice("Your booklet PDF is ready and has been downloaded.", true);
  } catch (error) {
    showNotice(error.message || "Could not generate the booklet.");
  } finally {
    generateButton.querySelector("span:first-child").textContent = "Generate booklet";
    updateSelectionCount();
  }
}

fileInput.addEventListener("change", () => uploadPdf(fileInput.files[0]));
document.querySelector("#change-file").addEventListener("click", () => {
  editor.hidden = true;
  uploadPanel.hidden = false;
  pageGrid.replaceChildren();
  activeSession = null;
});
document.querySelector("#range-form").addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    setSelection(parsePageRange(rangeInput.value));
    notice.hidden = true;
  } catch (error) {
    showNotice(error.message);
  }
});
document.querySelector(".selection-actions").addEventListener("click", (event) => {
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (!action) return;
  if (action === "all") setSelection(Array.from({ length: pageCount }, (_, index) => index + 1));
  if (action === "none") setSelection([]);
  if (action === "odd") setSelection(Array.from({ length: pageCount }, (_, index) => index + 1).filter((page) => page % 2 === 1));
  if (action === "even") setSelection(Array.from({ length: pageCount }, (_, index) => index + 1).filter((page) => page % 2 === 0));
});
generateButton.addEventListener("click", generateBooklet);
themeSelect.addEventListener("change", applyAppearance);
accentSelect.addEventListener("change", applyAppearance);
columnsSelect.addEventListener("change", () => {
  document.documentElement.style.setProperty("--thumbnail-columns", columnsSelect.value);
  localStorage.setItem("starz-thumbnail-columns", columnsSelect.value);
});
qualitySlider.addEventListener("input", () => {
  qualityValue.value = `${qualitySlider.value}%`;
  clearTimeout(qualityTimer);
  qualityTimer = setTimeout(() => setThumbnailQuality(qualitySlider.value), 180);
});
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (themeSelect.value === "system") applyAppearance();
});

for (const eventName of ["dragenter", "dragover"]) {
  uploadPanel.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadPanel.classList.add("drag-over");
  });
}
for (const eventName of ["dragleave", "drop"]) {
  uploadPanel.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadPanel.classList.remove("drag-over");
  });
}
uploadPanel.addEventListener("drop", (event) => uploadPdf(event.dataTransfer.files[0]));

loadAppearance();
const savedColumns = localStorage.getItem("starz-thumbnail-columns");
if (["2", "3", "4", "5", "6"].includes(savedColumns)) columnsSelect.value = savedColumns;
document.documentElement.style.setProperty("--thumbnail-columns", columnsSelect.value);
const savedQuality = Number(localStorage.getItem("starz-thumbnail-quality"));
if (Number.isInteger(savedQuality) && savedQuality >= 10 && savedQuality <= 100) {
  qualitySlider.value = String(savedQuality);
  thumbnailQuality = savedQuality;
}
qualityValue.value = `${thumbnailQuality}%`;
