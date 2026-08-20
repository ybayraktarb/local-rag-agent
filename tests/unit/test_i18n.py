import json

from src.i18n import TRANSLATIONS, catalog_format_fields, translate


def test_catalogs_have_matching_keys_and_format_fields():
    assert set(TRANSLATIONS["tr"]) == set(TRANSLATIONS["en"])
    for key in TRANSLATIONS["tr"]:
        assert catalog_format_fields("tr", key) == catalog_format_fields("en", key)


def test_translation_formats_and_unknown_language_falls_back():
    assert translate("page", "en") == "Page"
    assert translate("confidence.high", "en", score=.9) == "High Confidence (0.90)"
    assert translate("fallback", "invalid") == TRANSLATIONS["tr"]["fallback"]


def test_preferences_migrate_and_preserve_fields(tmp_path, monkeypatch):
    from src.ui import theme
    path = tmp_path / "ui_settings.json"
    monkeypatch.setattr(theme, "SETTINGS_FILE", str(path))
    path.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
    assert theme.load_preferences() == {"theme": "dark", "language": "tr"}
    theme.save_language_preference("en")
    assert theme.load_preferences() == {"theme": "dark", "language": "en"}
    theme.save_theme_preference("light")
    assert theme.load_preferences() == {"theme": "light", "language": "en"}
    path.write_text(json.dumps({"theme": "dark", "language": "xx"}), encoding="utf-8")
    assert theme.load_preferences()["language"] == "tr"
