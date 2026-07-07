# Browser Extension

PromptGuard's browser extension is a local live-scanning prototype for browser prompt boxes. It is designed to behave like a privacy Grammarly for AI prompts: warn while you type, show detected categories with masked previews, and help replace risky text with a safer rewritten prompt before sending.

## What It Does

- Scans supported browser text boxes locally while you type.
- Detects common secrets, PII, configured names, confidential terms, production context, legal/health/finance context, financial amounts, and dates.
- Shows an overlay for `MEDIUM`, `HIGH`, and `CRITICAL` risk prompts.
- Shows categories and masked previews, not full raw detected values.
- Can anonymise the active prompt box.
- Can copy only the safe rewritten prompt.
- Best-effort blocks common send gestures when policy says `block`.
- Stores settings locally in the browser.

## What It Does Not Do

- It does not use a backend.
- It does not send prompt text to any server.
- It does not make external API calls.
- It does not include telemetry or analytics.
- It does not permanently store raw prompts.
- It does not guarantee privacy, security, compliance, or complete send interception.

## Supported Surfaces

The content script detects:

- `textarea`
- `input[type=text]`
- `input[type=search]`
- `[contenteditable=true]`
- `[role=textbox]`
- `.ProseMirror`
- `.cm-content`

For normal textarea and input elements, PromptGuard can add a warning border and replace the value directly. For contenteditable, ProseMirror, and CodeMirror-like editors, replacement is best effort because controlled editors may manage their own internal state.

## Local-Only Privacy Model

The extension uses local JavaScript pattern matching in `browser-extension/src/engine.js`. Prompt text stays in the page context and is not written to `chrome.storage`, `localStorage`, logs, or a remote service.

Settings such as policy and configured names are stored in `chrome.storage.local`. Raw prompts are not stored there.

## Settings

The options page supports:

- Enable or disable live scanning.
- Choose `blockOn` risk levels.
- Choose `warnOn` risk levels.
- Enable or disable one-time Send Anyway.
- Configure customer names, client names, company names, and confidential terms.

Open the extension options page from the browser extension manager after loading the unpacked extension.

## Load Unpacked

1. Open `chrome://extensions` or `edge://extensions`.
2. Enable Developer Mode.
3. Click **Load unpacked**.
4. Select the `browser-extension` folder.
5. Open `browser-extension/demo/test_page.html` or a supported AI site.
6. Type a fake risky prompt.
7. Use **Anonymise Prompt** before sending.

## Demo Page

The demo page is at:

```text
browser-extension/demo/test_page.html
```

It includes a textarea, a contenteditable prompt box, fake send buttons, and fake risky prompt examples. Use it to verify overlay behavior, safe replacement, copy-safe-prompt, and common send blocking.

## Send Blocking Limitations

PromptGuard blocks common keyboard sends and nearby send-button clicks when policy says `block`. This is best effort:

- Dynamic web apps may change button labels, DOM structure, or event handling.
- Some apps may submit from code paths that are not visible as ordinary button clicks or keyboard events.
- Browser extensions run in an isolated environment and cannot control every page framework behavior.

For stronger pre-submit enforcement where available, use the Codex hook or local workflows.

## Why No Backend

PromptGuard's privacy boundary is local-first operation. Sending raw prompts to a backend for scanning would introduce the same exposure the tool is meant to reduce.

## Why Inline Highlighting Is Cautious

Many AI prompt boxes are controlled React, ProseMirror, or CodeMirror editors. Destructive inline span wrapping can break cursor position, editor state, undo history, or page-controlled rendering. Milestone 3 uses warning borders, a small marker, overlay findings, and masked previews instead of mutating editor DOM for inline underlines.

## Known Limitations

- Pattern matching can miss sensitive data or overflag harmless content.
- Safe rewrites may preserve context that is still sensitive.
- Contenteditable replacement is best effort.
- Clipboard copy uses browser clipboard APIs and may require user gesture permissions.
- Send blocking is not a complete security boundary.

## Milestone 3.1 Roadmap

- Safer editor-specific adapters for popular AI prompt boxes.
- Non-destructive inline decorations for stable textareas.
- Site-specific send button heuristics.
- More configurable pattern rules.
- Import/export for local settings.
