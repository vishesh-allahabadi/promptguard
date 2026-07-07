# PromptGuard Browser Extension

PromptGuard for Chrome, Edge, and Chromium browsers scans supported prompt text boxes locally while you type. It warns on risky content, shows detected categories with masked previews, and can replace the prompt with a safe rewritten version before sending.

This is a dependency-light Manifest V3 prototype. It has no backend, no telemetry, no analytics, no remote scripts, and no network calls.

## Load Unpacked

1. Open `chrome://extensions` or `edge://extensions`.
2. Enable Developer Mode.
3. Select **Load unpacked**.
4. Choose this `browser-extension` folder.
5. Open `demo/test_page.html` or a supported AI site.
6. Type a fake risky prompt and click **Anonymise Prompt** before sending.

## Supported Surfaces

The content script looks for:

- `textarea`
- `input[type=text]`
- `[contenteditable=true]`
- `[role=textbox]`
- `.ProseMirror`
- `.cm-content`

Dynamic web apps can change their DOM behavior. Send blocking is best effort; test PromptGuard on your target site before relying on it.

## Local Settings

Use the extension options page to configure policy, one-time override behavior, customer/client/company names, and confidential terms. Settings are stored in `chrome.storage.local`. Prompt text is not stored.

## Development

```bash
npm --prefix browser-extension test
```
