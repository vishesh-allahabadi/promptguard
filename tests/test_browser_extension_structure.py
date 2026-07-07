import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXTENSION = ROOT / "browser-extension"


def test_browser_extension_manifest_is_valid() -> None:
    manifest_path = EXTENSION / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert manifest["name"] == "PromptGuard"
    assert manifest["options_page"] == "options/options.html"
    assert "storage" in manifest["permissions"]
    content_script = manifest["content_scripts"][0]
    assert "src/content.js" in content_script["js"]
    assert "src/styles.css" in content_script["css"]
    assert "<all_urls>" not in content_script["matches"]


def test_browser_extension_files_exist() -> None:
    for relative in (
        "README.md",
        "package.json",
        "src/content.js",
        "src/engine.js",
        "src/overlay.js",
        "src/settings.js",
        "src/styles.css",
        "options/options.html",
        "options/options.js",
        "options/options.css",
        "demo/test_page.html",
        "tests/engine.test.mjs",
        "../docs/browser_extension.md",
    ):
        assert (EXTENSION / relative).resolve().exists(), relative


def test_browser_extension_package_has_test_script() -> None:
    package_json = json.loads((EXTENSION / "package.json").read_text(encoding="utf-8"))
    assert package_json["type"] == "module"
    assert package_json["scripts"]["test"] == "node tests/engine.test.mjs"
