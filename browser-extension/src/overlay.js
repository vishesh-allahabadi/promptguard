export function createPromptGuardOverlay() {
  const root = document.createElement("section");
  root.className = "pg-overlay";
  root.setAttribute("role", "dialog");
  root.setAttribute("aria-live", "polite");
  root.hidden = true;
  document.documentElement.appendChild(root);

  let callbacks = {};
  let passiveClosed = false;

  root.addEventListener("click", (event) => {
    const action = event.target?.closest?.("[data-pg-action]")?.dataset.pgAction;
    if (!action) return;
    if (action === "anonymize") callbacks.onAnonymize?.();
    if (action === "copy") callbacks.onCopy?.();
    if (action === "send") callbacks.onSendAnyway?.();
    if (action === "cancel") {
      passiveClosed = true;
      hide();
      callbacks.onCancel?.();
    }
  });

  function show({ result, anchor, settings, blocking = false, status = "", handlers = {} }) {
    callbacks = handlers;
    if (!blocking && passiveClosed) return;
    passiveClosed = false;
    root.innerHTML = render(result, settings, blocking, status);
    positionNear(root, anchor);
    root.hidden = false;
  }

  function hide() {
    root.hidden = true;
  }

  function resetDismissal() {
    passiveClosed = false;
  }

  return { show, hide, resetDismissal };
}

function render(result, settings, blocking, status) {
  const riskClass = `pg-risk-${result.riskLevel.toLowerCase()}`;
  const categoryChips = result.categories.length
    ? result.categories.map((category) => `<span class="pg-chip">${escapeHtml(category)}</span>`).join("")
    : `<span class="pg-muted">No risky categories.</span>`;
  const findingRows = result.findings.slice(0, 6).map((finding) => {
    return `<li><strong>${escapeHtml(finding.label)}</strong><span>${escapeHtml(finding.preview)}</span></li>`;
  }).join("");
  const sendAnyway = settings.allowSendAnyway
    ? `<button type="button" class="pg-btn pg-btn-secondary" data-pg-action="send">Send Anyway</button>`
    : "";
  const headline = blocking
    ? "PromptGuard blocked this prompt before sending because it contains sensitive data."
    : "Sensitive data detected before sending.";
  return `
    <div class="pg-head">
      <strong>PromptGuard</strong>
      <span class="pg-badge ${riskClass}">${escapeHtml(result.riskLevel)}</span>
      <span class="pg-badge">${escapeHtml(result.policy)}</span>
    </div>
    <p class="pg-summary">${escapeHtml(status || headline)}</p>
    <div class="pg-chip-row">${categoryChips}</div>
    ${findingRows ? `<ul class="pg-findings">${findingRows}</ul>` : ""}
    <div class="pg-actions">
      <button type="button" class="pg-btn pg-btn-primary" data-pg-action="anonymize">Anonymise Prompt</button>
      <button type="button" class="pg-btn pg-btn-secondary" data-pg-action="copy">Copy Safe Prompt</button>
      ${sendAnyway}
      <button type="button" class="pg-btn pg-btn-ghost" data-pg-action="cancel">Cancel</button>
    </div>
  `;
}

function positionNear(root, anchor) {
  const rect = anchor?.getBoundingClientRect?.();
  if (!rect) {
    root.style.left = "20px";
    root.style.top = "20px";
    return;
  }
  const width = 360;
  const left = Math.max(12, Math.min(window.innerWidth - width - 12, rect.left));
  const top = Math.max(12, Math.min(window.innerHeight - 280, rect.bottom + 10));
  root.style.left = `${left}px`;
  root.style.top = `${top}px`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
  });
}
