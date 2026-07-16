import sys
import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QListWidgetItem, QPushButton


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp, monkeypatch):
    from src.ui.main_window import MainWindow

    monkeypatch.setattr(MainWindow, "_bootstrap_system", lambda self: None)
    monkeypatch.setattr("src.ui.main_window.load_theme_preference", lambda: "light")
    monkeypatch.setattr("src.ui.main_window.save_theme_preference", lambda theme: None)
    result = MainWindow()
    result.show()
    qapp.processEvents()
    yield result
    result.close()

def test_ui_imports():
    """
    Verify that all PySide6 window and worker classes can be imported without errors.
    """
    from src.ui.main_window import MainWindow, InitWorker, QueryWorker
    assert MainWindow is not None
    assert InitWorker is not None
    assert QueryWorker is not None

def test_query_worker_run():
    """
    Verify QueryWorker background thread execution behavior with mock objects.
    """
    from src.ui.main_window import QueryWorker
    
    mock_agent = MagicMock()
    mock_agent.query.return_value = {"answer": "Test answer", "sources": []}
    
    worker = QueryWorker(agent=mock_agent, query_text="Test query")
    
    # Mock signals
    worker.finished = MagicMock()
    worker.error_occurred = MagicMock()
    
    # Run the worker synchronously for testing
    worker.run()
    
    mock_agent.query.assert_called_once_with("Test query")
    worker.finished.emit.assert_called_once_with({"answer": "Test answer", "sources": []})
    worker.error_occurred.emit.assert_not_called()


def test_referans_header_and_document_drawer(window, qapp):
    assert window.windowTitle() == "Local Belge Asistanı"
    assert window.sidebar.isHidden()
    assert window.sidebar.width() == 280

    window.documents_btn.click()
    qapp.processEvents()
    assert window.sidebar.isVisible()
    window.documents_btn.click()
    assert window.sidebar.isHidden()


def test_document_filter_and_selection_details(window):
    first = QListWidgetItem("●  rehber.pdf")
    first.setData(Qt.UserRole, {
        "filename": "rehber.pdf", "status_label": "Aktif",
        "updated_at": "2026-07-16T10:30:00",
    })
    second = QListWidgetItem("●  politika.pdf")
    second.setData(Qt.UserRole, {"filename": "politika.pdf"})
    window.docs_list.addItem(first)
    window.docs_list.addItem(second)

    window.document_search.setText("rehber")
    assert not first.isHidden()
    assert second.isHidden()
    window.show_document_details(first)
    assert window.detail_name.text() == "rehber.pdf"
    assert "Aktif" in window.detail_meta.text()
    assert "2026-07-16 10:30" in window.detail_meta.text()

    window.docs_list.setCurrentItem(first)
    opener = MagicMock()
    window.open_document = opener
    window.docs_list.itemDoubleClicked.emit(first)
    window.open_document_btn.click()
    assert opener.call_count == 2
    assert all(entry.args == ("rehber.pdf",) for entry in opener.call_args_list)


@pytest.mark.parametrize("audit_enabled, expected", [(False, False), (True, True)])
def test_settings_theme_and_audit_visibility(qapp, monkeypatch, audit_enabled, expected):
    from src.ui.main_window import MainWindow

    monkeypatch.setattr(MainWindow, "_bootstrap_system", lambda self: None)
    monkeypatch.setattr("src.ui.main_window.load_theme_preference", lambda: "light")
    monkeypatch.setattr("src.ui.main_window.save_theme_preference", lambda theme: None)
    monkeypatch.setattr("src.ui.main_window.settings.AUDIT_ENABLED", audit_enabled)
    tested = MainWindow()
    assert (not tested.settings_popover.export_button.isHidden()) is expected
    assert tested.settings_popover.status_label.text() == "Hazırlanıyor"
    tested.settings_popover.dark_theme_button.click()
    assert tested.current_theme == "dark"
    assert tested.settings_popover.dark_theme_button.isChecked()
    assert not tested.settings_popover.light_theme_button.isChecked()
    assert tested.settings_popover.dark_theme_button.accessibleName() == "Koyu tema"
    tested.settings_popover.light_theme_button.click()
    assert tested.current_theme == "light"
    tested.close()


@pytest.mark.parametrize(
    "text,state,description",
    [
        ("Hazırlanıyor", "loading", "Belgeler ve yerel model kontrol ediliyor."),
        ("Hazır", "ready", "Yerel arama kullanıma hazır."),
        ("Bağlantı yok", "error", "Yerel servis başlatılamadı."),
    ],
)
def test_settings_system_status(window, text, state, description):
    window.settings_popover.set_system_status(text, state)
    assert window.settings_popover.status_label.text() == text
    assert window.settings_popover.status_description.text() == description
    assert window.settings_popover.status_dot.property("state") == state


def test_new_chat_copy_and_source_chips(window, qapp):
    from src.ui.main_window import ChatCard
    from src.ui.theme import THEMES

    card = ChatCard(
        "Soru", "Doğru cevap", [{"source": "/belgeler/rehber.pdf", "page": 4}],
        0.9, THEMES["light"].colors,
    )
    window.stream_layout.insertWidget(window.stream_layout.count() - 1, card)
    window.welcome_label.hide()
    card.copy_button.click()
    assert QApplication.clipboard().text() == "Doğru cevap"
    chips = card.findChildren(QPushButton, "SourceChip")
    assert [chip.text() for chip in chips] == ["rehber.pdf · Sayfa 4"]

    window.new_chat_btn.click()
    qapp.processEvents()
    assert not any(
        isinstance(window.stream_layout.itemAt(i).widget(), ChatCard)
        for i in range(window.stream_layout.count())
    )
    assert window.welcome_label.isVisible()


def test_light_and_dark_views_render(window, qapp):
    light_render = window.grab().toImage()
    assert not light_render.isNull()
    assert light_render.width() == window.width()

    window.toggle_theme()
    qapp.processEvents()
    dark_render = window.grab().toImage()
    assert not dark_render.isNull()
    assert dark_render.pixelColor(5, 100) != light_render.pixelColor(5, 100)


def test_populate_sidebar_uses_total_document_count(window, monkeypatch):
    registry = MagicMock()
    registry.data = {
        "aktif.pdf": {"status": "active"},
        "pasif.pdf": {"status": "inactive"},
    }
    monkeypatch.setattr(
        "src.indexing.document_registry.DocumentRegistry", lambda: registry
    )
    window.populate_sidebar()
    assert window.documents_btn.text() == "Belgeler · 2"
    assert window.findChild(type(window.detail_name), "SidebarTitle").text() == "BELGELER  ·  1 AKTİF"


def test_welcome_is_an_assistant_message(window):
    assert window.welcome_message.text() == (
        "Merhaba, belgelerinizle ilgili ne öğrenmek istersiniz?"
    )
    assert window.findChild(type(window.detail_name), "WelcomeTitle") is None


def test_document_and_source_open_pdf(window, tmp_path, monkeypatch, qapp):
    docs = tmp_path / "docs"
    docs.mkdir()
    pdf = docs / "rehber.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    opened_urls = []
    monkeypatch.setattr("src.ui.main_window.settings.DOCS_DIR", str(docs))
    monkeypatch.setattr(
        "src.ui.main_window.QDesktopServices.openUrl",
        lambda url: opened_urls.append(url) or True,
    )

    assert window.open_document("rehber.pdf", 4) is True
    assert opened_urls[-1].toLocalFile() == str(pdf)
    assert opened_urls[-1].fragment() == "page=4"

    from src.ui.main_window import ChatCard
    from src.ui.theme import THEMES
    card = ChatCard(
        "Soru", "Yanıt", [{"source": "rehber.pdf", "page": 2}],
        0.9, THEMES["light"].colors,
    )
    card.source_requested.connect(window.open_document)
    card.findChild(QPushButton, "SourceChip").click()
    qapp.processEvents()
    assert opened_urls[-1].fragment() == "page=2"


def test_missing_document_shows_warning(window, tmp_path, monkeypatch):
    monkeypatch.setattr("src.ui.main_window.settings.DOCS_DIR", str(tmp_path))
    warning = MagicMock()
    monkeypatch.setattr("src.ui.main_window.QMessageBox.warning", warning)
    assert window.open_document("yok.pdf") is False
    assert "yok.pdf" in warning.call_args.args[2]
