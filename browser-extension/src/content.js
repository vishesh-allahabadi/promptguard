(async () => {
  const extensionUrl = (path) => chrome.runtime.getURL(path);
  const [{ scanText, anonymizeText }, { createPromptGuardOverlay }, settingsModule] = await Promise.all([
    import(extensionUrl("src/engine.js")),
    import(extensionUrl("src/overlay.js")),
    import(extensionUrl("src/settings.js"))
  ]);

  let settings = await settingsModule.getSettings();
  let activeEditable = null;
  let lastResult = null;
  let lastTextHash = "";
  let allowedOnceHash = null;
  let postAnonymizeStatusUntil = 0;
  let scanTimer = null;

  const overlay = createPromptGuardOverlay();
  const marker = document.createElement("div");
  marker.className = "pg-risk-marker";
  marker.hidden = true;
  document.documentElement.appendChild(marker);

  settingsModule.onSettingsChanged((partial) => {
    settings = { ...settings, ...partial };
    scheduleScan();
  });

  document.addEventListener("focusin", (event) => {
    const editable = findNearestEditableFromEvent(event);
    if (!editable) return;
    activeEditable = editable;
    overlay.resetDismissal();
    scheduleScan();
  }, true);

  document.addEventListener("input", (event) => {
    const editable = findNearestEditableFromEvent(event);
    if (!editable) return;
    activeEditable = editable;
    overlay.resetDismissal();
    scheduleScan();
  }, true);

  document.addEventListener("keydown", (event) => {
    if (!activeEditable || !isBlockedNow()) return;
    const singleLine = activeEditable instanceof HTMLInputElement;
    const sendKey = (event.key === "Enter" && (event.metaKey || event.ctrlKey)) || (singleLine && event.key === "Enter");
    if (!sendKey) return;
    if (consumeAllowedOnce()) return;
    blockEvent(event);
    showBlockingOverlay();
  }, true);

  document.addEventListener("click", (event) => {
    if (event.target?.closest?.(".pg-overlay")) return;
    if (!activeEditable || !isBlockedNow()) return;
    const button = event.target?.closest?.("button, [role='button'], input[type='submit'], input[type='button']");
    if (!button || !looksLikeSendButton(button) || !isNearActiveEditable(button)) return;
    if (consumeAllowedOnce()) return;
    blockEvent(event);
    showBlockingOverlay();
  }, true);

  function scheduleScan() {
    clearTimeout(scanTimer);
    scanTimer = setTimeout(scanActive, settings.scanDebounceMs || 250);
  }

  function scanActive() {
    if (!settings.enabled || !activeEditable || !isEditableCandidate(activeEditable)) {
      hideRiskUi();
      return;
    }
    const text = getEditableText(activeEditable);
    const hash = textHash(text);
    if (lastTextHash && hash !== lastTextHash) {
      postAnonymizeStatusUntil = 0;
    }
    if (!text.trim()) {
      hideRiskUi();
      return;
    }
    lastTextHash = hash;
    lastResult = scanText(text, settings);
    if (lastResult.riskLevel === "LOW") {
      hideRiskUi();
      return;
    }
    const status = Date.now() < postAnonymizeStatusUntil ? "Prompt anonymised locally." : "";
    showRiskUi(activeEditable, lastResult, status);
  }

  function showRiskUi(element, result, status = "") {
    element.classList.toggle("pg-risk-border", element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement);
    positionMarker(element);
    overlay.show({
      result,
      anchor: element,
      settings,
      status,
      handlers: {
        onAnonymize: anonymizeActivePrompt,
        onCopy: copySafePrompt,
        onSendAnyway: allowSendAnyway
      }
    });
  }

  function showBlockingOverlay() {
    if (!activeEditable || !lastResult) return;
    overlay.resetDismissal();
    overlay.show({
      result: lastResult,
      anchor: activeEditable,
      settings,
      blocking: true,
      handlers: {
        onAnonymize: anonymizeActivePrompt,
        onCopy: copySafePrompt,
        onSendAnyway: allowSendAnyway
      }
    });
  }

  function hideRiskUi() {
    overlay.hide();
    marker.hidden = true;
    document.querySelectorAll(".pg-risk-border").forEach((element) => element.classList.remove("pg-risk-border"));
  }

  function anonymizeActivePrompt() {
    if (!activeEditable) return;
    const original = getEditableText(activeEditable);
    const safe = anonymizeText(original, settings);
    if (!setEditableText(activeEditable, safe.safeText)) {
      overlay.show({
        result: safe,
        anchor: activeEditable,
        settings,
        status: "PromptGuard could not safely replace this editor. Copy the safe prompt manually.",
        handlers: { onCopy: copySafePrompt, onSendAnyway: allowSendAnyway, onAnonymize: anonymizeActivePrompt }
      });
      return;
    }
    const rescanned = scanText(safe.safeText, settings);
    lastResult = rescanned;
    lastTextHash = textHash(safe.safeText);
    postAnonymizeStatusUntil = Date.now() + 1800;
    overlay.show({
      result: rescanned,
      anchor: activeEditable,
      settings,
      status: "Prompt anonymised locally.",
      handlers: { onCopy: copySafePrompt, onSendAnyway: allowSendAnyway, onAnonymize: anonymizeActivePrompt }
    });
  }

  async function copySafePrompt() {
    if (!activeEditable) return;
    const safe = anonymizeText(getEditableText(activeEditable), settings);
    await copyText(safe.safeText);
    overlay.show({
      result: safe,
      anchor: activeEditable,
      settings,
      status: "Safe prompt copied locally.",
      handlers: { onCopy: copySafePrompt, onSendAnyway: allowSendAnyway, onAnonymize: anonymizeActivePrompt }
    });
  }

  function allowSendAnyway() {
    if (!settings.allowSendAnyway || !activeEditable) return;
    allowedOnceHash = textHash(getEditableText(activeEditable));
    overlay.hide();
  }

  function isBlockedNow() {
    if (!lastResult || lastResult.policy !== "block") return false;
    if (!activeEditable) return false;
    return textHash(getEditableText(activeEditable)) === lastTextHash;
  }

  function consumeAllowedOnce() {
    if (!activeEditable || !allowedOnceHash) return false;
    const currentHash = textHash(getEditableText(activeEditable));
    if (currentHash !== allowedOnceHash) return false;
    allowedOnceHash = null;
    return true;
  }

  function positionMarker(element) {
    const rect = element.getBoundingClientRect();
    marker.style.left = `${Math.max(6, rect.right - 8)}px`;
    marker.style.top = `${Math.max(6, rect.top - 6)}px`;
    marker.hidden = false;
  }

  async function copyText(text) {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }

  function blockEvent(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation?.();
  }

  function looksLikeSendButton(button) {
    const value = [
      button.getAttribute("aria-label"),
      button.getAttribute("title"),
      button.value,
      button.textContent
    ].filter(Boolean).join(" ").toLowerCase();
    return /\b(send|submit|run|ask|prompt)\b/.test(value);
  }

  function isNearActiveEditable(button) {
    const activeRect = activeEditable.getBoundingClientRect();
    const buttonRect = button.getBoundingClientRect();
    const horizontal = Math.abs((activeRect.left + activeRect.right) / 2 - (buttonRect.left + buttonRect.right) / 2);
    const vertical = Math.abs((activeRect.top + activeRect.bottom) / 2 - (buttonRect.top + buttonRect.bottom) / 2);
    return horizontal < 700 && vertical < 500;
  }
})();

function getEditableText(element) {
  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) return element.value;
  return element.innerText ?? element.textContent ?? "";
}

function setEditableText(element, value) {
  if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
    element.value = value;
    element.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertReplacementText", data: value }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }
  if (element.isContentEditable || element.getAttribute("role") === "textbox") {
    element.textContent = value;
    element.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertReplacementText", data: value }));
    return true;
  }
  return false;
}

function isEditableCandidate(element) {
  if (!element || !(element instanceof Element)) return false;
  if (element instanceof HTMLTextAreaElement) return true;
  if (element instanceof HTMLInputElement) return !element.type || element.type === "text" || element.type === "search";
  if (element.isContentEditable) return true;
  if (element.getAttribute("contenteditable") === "true") return true;
  if (element.getAttribute("role") === "textbox") return true;
  return element.matches(".ProseMirror, .cm-content");
}

function findNearestEditableFromEvent(event) {
  const target = event.target;
  if (!target?.closest) return null;
  const candidate = target.closest("textarea, input[type='text'], input[type='search'], [contenteditable='true'], [role='textbox'], .ProseMirror, .cm-content");
  return isEditableCandidate(candidate) ? candidate : null;
}

function textHash(text) {
  let hash = 5381;
  for (let index = 0; index < text.length; index += 1) {
    hash = ((hash << 5) + hash) ^ text.charCodeAt(index);
  }
  return String(hash >>> 0);
}
