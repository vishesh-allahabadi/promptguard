export const DEFAULT_SETTINGS = {
  enabled: true,
  blockOn: ["CRITICAL", "HIGH"],
  warnOn: ["MEDIUM"],
  allowSendAnyway: true,
  customerNames: [],
  clientNames: [],
  companyNames: [],
  confidentialTerms: [],
  scanDebounceMs: 250
};

export async function getSettings() {
  if (!globalThis.chrome?.storage?.local) return { ...DEFAULT_SETTINGS };
  const stored = await chrome.storage.local.get(DEFAULT_SETTINGS);
  return normalizeSettings(stored);
}

export function onSettingsChanged(callback) {
  if (!globalThis.chrome?.storage?.onChanged) return () => {};
  const listener = (changes, area) => {
    if (area !== "local") return;
    const next = {};
    for (const [key, change] of Object.entries(changes)) {
      next[key] = change.newValue;
    }
    callback(normalizeSettings(next));
  };
  chrome.storage.onChanged.addListener(listener);
  return () => chrome.storage.onChanged.removeListener(listener);
}

export function normalizeSettings(settings = {}) {
  return {
    ...DEFAULT_SETTINGS,
    ...settings,
    blockOn: normalizeRiskList(settings.blockOn, DEFAULT_SETTINGS.blockOn),
    warnOn: normalizeRiskList(settings.warnOn, DEFAULT_SETTINGS.warnOn),
    customerNames: normalizeList(settings.customerNames),
    clientNames: normalizeList(settings.clientNames),
    companyNames: normalizeList(settings.companyNames),
    confidentialTerms: normalizeList(settings.confidentialTerms),
    allowSendAnyway: settings.allowSendAnyway ?? DEFAULT_SETTINGS.allowSendAnyway,
    enabled: settings.enabled ?? DEFAULT_SETTINGS.enabled,
    scanDebounceMs: Number(settings.scanDebounceMs || DEFAULT_SETTINGS.scanDebounceMs)
  };
}

function normalizeList(value) {
  if (Array.isArray(value)) return value.map((item) => String(item).trim()).filter(Boolean);
  if (typeof value === "string") return value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
  return [];
}

function normalizeRiskList(value, fallback) {
  const allowed = new Set(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);
  const source = Array.isArray(value) ? value : fallback;
  return source.map((item) => String(item).toUpperCase()).filter((item) => allowed.has(item));
}
