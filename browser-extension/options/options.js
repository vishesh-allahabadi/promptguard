import { DEFAULT_SETTINGS, normalizeSettings } from "../src/settings.js";

const form = document.querySelector("#settings-form");
const status = document.querySelector("#status");
const reset = document.querySelector("#reset");

load();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const settings = readForm();
  await chrome.storage.local.set(settings);
  showStatus("Saved locally.");
});

reset.addEventListener("click", async () => {
  await chrome.storage.local.set(DEFAULT_SETTINGS);
  writeForm(DEFAULT_SETTINGS);
  showStatus("Defaults restored.");
});

async function load() {
  const stored = await chrome.storage.local.get(DEFAULT_SETTINGS);
  writeForm(normalizeSettings(stored));
}

function readForm() {
  return {
    enabled: form.elements.enabled.checked,
    allowSendAnyway: form.elements.allowSendAnyway.checked,
    blockOn: checkedValues("blockOn"),
    warnOn: checkedValues("warnOn"),
    customerNames: lines("customerNames"),
    clientNames: lines("clientNames"),
    companyNames: lines("companyNames"),
    confidentialTerms: lines("confidentialTerms"),
    scanDebounceMs: DEFAULT_SETTINGS.scanDebounceMs
  };
}

function writeForm(settings) {
  form.elements.enabled.checked = settings.enabled;
  form.elements.allowSendAnyway.checked = settings.allowSendAnyway;
  setCheckedValues("blockOn", settings.blockOn);
  setCheckedValues("warnOn", settings.warnOn);
  form.elements.customerNames.value = settings.customerNames.join("\n");
  form.elements.clientNames.value = settings.clientNames.join("\n");
  form.elements.companyNames.value = settings.companyNames.join("\n");
  form.elements.confidentialTerms.value = settings.confidentialTerms.join("\n");
}

function checkedValues(name) {
  return [...form.querySelectorAll(`input[name="${name}"]:checked`)].map((input) => input.value);
}

function setCheckedValues(name, values) {
  const allowed = new Set(values);
  for (const input of form.querySelectorAll(`input[name="${name}"]`)) {
    input.checked = allowed.has(input.value);
  }
}

function lines(name) {
  return form.elements[name].value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function showStatus(message) {
  status.textContent = message;
  setTimeout(() => {
    status.textContent = "";
  }, 1800);
}
