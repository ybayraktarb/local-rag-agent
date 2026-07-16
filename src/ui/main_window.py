import os
import sys
import logging
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QListWidget, QFileDialog, QMessageBox,
    QProgressBar, QScrollArea, QFrame, QSplitter, QApplication, QButtonGroup
)
from src.config import settings
from src.audit.audit_export import export_audit_logs
from src.ui.theme import generate_qss, load_theme_preference, save_theme_preference, THEMES

logger = logging.getLogger(__name__)

class InitWorker(QThread):
    """
    Worker thread that runs database bootstrap, scans registry,
    and indexes new documents in the background upon application startup.
    """
    status_updated = Signal(str)
    finished = Signal(object)  # Emits the initialized Agent instance
    error_occurred = Signal(str)

    def run(self):
        try:
            self.status_updated.emit("Dizin yapıları kontrol ediliyor...")
            from src.config import settings
            from src.indexing.document_registry import DocumentRegistry
            from src.indexing.chunker import DocumentChunker
            from src.loaders.pdf_loader import PDFLoader
            from src.indexing.vectorstore_manager import VectorStoreManager
            from src.agent.agent_builder import AgentBuilder

            os.makedirs(settings.DOCS_DIR, exist_ok=True)
            os.makedirs(settings.DB_DIR, exist_ok=True)
            if settings.AUDIT_ENABLED:
                settings.validate_audit_settings()
                os.makedirs(settings.AUDIT_DIR, exist_ok=True)

            self.status_updated.emit("Belgeler taranıyor...")
            registry = DocumentRegistry()
            changes = registry.scan_docs_folder()

            if any(changes.values()):
                from src.indexing.index_lifecycle import synchronize_index
                _, failures = synchronize_index(registry=registry, progress=lambda name: self.status_updated.emit(f"İndeksleniyor: {name}"))
                if failures:
                    self.status_updated.emit("Bazı belgeler indekslenemedi; sonraki açılışta yeniden denenecek.")

            self.status_updated.emit("RAG Ajanı kuruluyor...")
            agent = AgentBuilder.build_agent()
            self.finished.emit(agent)
            
        except Exception as e:
            logger.error(f"Sistem önyükleme hatası: {e}")
            self.error_occurred.emit(str(e))


class QueryWorker(QThread):
    """
    Worker thread that runs the LLM/RAG query in the background
    so the GUI thread remains responsive.
    """
    finished = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, agent, query_text):
        super().__init__()
        self.agent = agent
        self.query_text = query_text

    def run(self):
        try:
            response = self.agent.query(self.query_text)
            self.finished.emit(response)
        except Exception as e:
            logger.error(f"Sorgu işlemi hatası: {e}")
            self.error_occurred.emit(str(e))


class SettingsPopover(QFrame):
    """Compact application settings shown below the header gear button."""

    theme_changed = Signal(bool)
    export_requested = Signal()

    def __init__(self, audit_enabled: bool, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("SettingsPopover")
        self.setFixedWidth(276)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.status_card = QFrame()
        self.status_card.setObjectName("SystemStatusCard")
        status_card_layout = QHBoxLayout(self.status_card)
        status_card_layout.setContentsMargins(12, 11, 12, 11)
        status_card_layout.setSpacing(9)

        self.status_dot = QFrame()
        self.status_dot.setObjectName("SystemStatusDot")
        self.status_dot.setFixedSize(8, 8)
        status_text_layout = QVBoxLayout()
        status_text_layout.setContentsMargins(0, 0, 0, 0)
        status_text_layout.setSpacing(2)
        self.status_label = QLabel("Hazırlanıyor")
        self.status_label.setObjectName("SystemStatusValue")
        self.status_description = QLabel("Belgeler ve yerel model kontrol ediliyor.")
        self.status_description.setObjectName("SystemStatusDescription")
        self.status_description.setWordWrap(True)
        status_text_layout.addWidget(self.status_label)
        status_text_layout.addWidget(self.status_description)
        status_card_layout.addWidget(self.status_dot, alignment=Qt.AlignTop)
        status_card_layout.addLayout(status_text_layout, stretch=1)
        layout.addWidget(self.status_card)

        separator = QFrame()
        separator.setObjectName("SettingsSeparator")
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)

        theme_label = QLabel("Görünüm")
        theme_label.setObjectName("SettingsSectionTitle")
        layout.addWidget(theme_label)

        theme_selector = QFrame()
        theme_selector.setObjectName("ThemeSelector")
        theme_layout = QHBoxLayout(theme_selector)
        theme_layout.setContentsMargins(3, 3, 3, 3)
        theme_layout.setSpacing(3)
        self.light_theme_button = QPushButton("Açık")
        self.light_theme_button.setObjectName("ThemeOption")
        self.light_theme_button.setAccessibleName("Açık tema")
        self.light_theme_button.setCheckable(True)
        self.dark_theme_button = QPushButton("Koyu")
        self.dark_theme_button.setObjectName("ThemeOption")
        self.dark_theme_button.setAccessibleName("Koyu tema")
        self.dark_theme_button.setCheckable(True)
        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.addButton(self.light_theme_button, 0)
        self.theme_group.addButton(self.dark_theme_button, 1)
        self.light_theme_button.setChecked(True)
        self.theme_group.idClicked.connect(lambda theme_id: self.theme_changed.emit(theme_id == 1))
        theme_layout.addWidget(self.light_theme_button)
        theme_layout.addWidget(self.dark_theme_button)
        layout.addWidget(theme_selector)

        self.export_button = QPushButton("Dışa aktar")
        self.export_button.setObjectName("PopoverExportButton")
        self.export_button.clicked.connect(self.export_requested)
        self.export_button.setVisible(audit_enabled)
        if audit_enabled:
            layout.addWidget(self.export_button)

    def set_system_status(self, text: str, state: str):
        self.status_label.setText(text)
        descriptions = {
            "loading": "Belgeler ve yerel model kontrol ediliyor.",
            "ready": "Yerel arama kullanıma hazır.",
            "error": "Yerel servis başlatılamadı.",
        }
        self.status_description.setText(descriptions.get(state, ""))
        self.status_dot.setProperty("state", state)
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)


class ChatCard(QFrame):
    """
    Premium card display for user queries and AI responses with sources and badges.
    """
    source_requested = Signal(str, object)

    def __init__(self, query: str, answer: str, sources: list, confidence: float, colors: dict):
        super().__init__()
        self.answer = answer
        self.confidence = confidence
        self.setObjectName("ChatCard")
        self.setFrameShape(QFrame.StyledPanel)
        
        card_layout = QVBoxLayout(self)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(20, 18, 20, 18)

        # 1. Header line (Query text + Confidence Badge)
        header_layout = QHBoxLayout()
        query_label = QLabel(f"Soru: {query}")
        query_label.setObjectName("UserQueryLabel")
        query_label.setWordWrap(True)
        header_layout.addWidget(query_label, stretch=4)

        # Confidence Score Badge
        self.confidence_badge = QLabel()
        self.confidence_badge.setObjectName("ConfidenceBadge")
        self.confidence_badge.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.confidence_badge)
        card_layout.addLayout(header_layout)

        # 2. Divider
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.HLine)
        self.divider.setFrameShadow(QFrame.Sunken)
        card_layout.addWidget(self.divider)

        # 3. Bot Response body
        self.answer_label = QLabel(answer)
        self.answer_label.setObjectName("BotAnswerLabel")
        self.answer_label.setWordWrap(True)
        self.answer_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        card_layout.addWidget(self.answer_label)

        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        self.copy_button = QPushButton("Kopyala")
        self.copy_button.setObjectName("CopyButton")
        self.copy_button.clicked.connect(self.copy_answer)
        actions_layout.addWidget(self.copy_button)
        card_layout.addLayout(actions_layout)

        # 4. Sources list (if any)
        if sources:
            sources_layout = QHBoxLayout()
            sources_layout.setSpacing(6)
            sources_layout.addWidget(QLabel("Kaynaklar"))
            for source in sources:
                page = source.get("page", "")
                page_text = f" · Sayfa {page}" if page not in (None, "") else ""
                filename = os.path.basename(str(source.get("source", "")))
                chip = QPushButton(f"{filename}{page_text}")
                chip.setObjectName("SourceChip")
                chip.setCursor(Qt.PointingHandCursor)
                chip.setToolTip("Belgeyi aç")
                chip.clicked.connect(
                    lambda checked=False, name=filename, page_number=page:
                    self.source_requested.emit(name, page_number)
                )
                sources_layout.addWidget(chip)
            sources_layout.addStretch()
            card_layout.addLayout(sources_layout)

        self.apply_colors(colors)

    def apply_colors(self, colors):
        if self.confidence >= settings.CONFIDENCE_HIGH_THRESHOLD:
            badge_color = colors["success"]
            badge_text = f"Yüksek Güven ({self.confidence:.2f})"
        elif self.confidence >= settings.CONFIDENCE_THRESHOLD:
            badge_color = colors["warning"]
            badge_text = f"Orta Güven ({self.confidence:.2f})"
        else:
            badge_color = colors["error"]
            badge_text = "Bulunamadı"
        self.confidence_badge.setText(badge_text)
        self.confidence_badge.setStyleSheet(
            f"background-color: {badge_color}; border-radius: 9px; padding: 3px 9px; "
            "color: #FFFFFF; font-weight: 700; font-size: 10px;"
        )
        self.divider.setStyleSheet(
            f"background-color: {colors['border']}; max-height: 1px;"
        )

    def copy_answer(self):
        QApplication.clipboard().setText(self.answer)
        self.copy_button.setText("Kopyalandı")
        QTimer.singleShot(1200, lambda: self.copy_button.setText("Kopyala"))


class MainWindow(QMainWindow):
    """
    Main application dashboard view.
    Combines sidebar, chat cards, status metrics, and theme toggle actions.
    """
    def __init__(self):
        super().__init__()
        self.agent = None
        self.init_worker = None
        self.query_worker = None
        
        # Load theme setting
        self.current_theme = load_theme_preference()
        
        self.setWindowTitle("Local Belge Asistanı")
        self.resize(1120, 760)
        self.setMinimumSize(860, 600)
        
        self._init_ui()
        self.apply_theme()
        self._bootstrap_system()

    def _init_ui(self):
        # Base Layout Wrapper
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        window_layout = QVBoxLayout(central_widget)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)

        # =====================================================================
        # 1. Header Bar (Navbar)
        # =====================================================================
        self.header_bar = QWidget()
        self.header_bar.setObjectName("HeaderBar")
        self.header_bar.setFixedHeight(56)
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(18, 0, 18, 0)
        header_layout.setSpacing(12)

        app_title = QLabel("Local Belge Asistanı")
        app_title.setObjectName("AppTitle")
        header_layout.addWidget(app_title)

        self.documents_btn = QPushButton("Belgeler · 0")
        self.documents_btn.setObjectName("DocumentsButton")
        self.documents_btn.clicked.connect(self.toggle_document_drawer)
        header_layout.addWidget(self.documents_btn)
        header_layout.addStretch()

        self.new_chat_btn = QPushButton("Yeni sohbet")
        self.new_chat_btn.setObjectName("NewChatButton")
        self.new_chat_btn.clicked.connect(self.new_chat)
        header_layout.addWidget(self.new_chat_btn)

        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("SettingsButton")
        self.settings_btn.setAccessibleName("Ayarlar")
        self.settings_btn.setToolTip("Ayarlar")
        self.settings_btn.setFixedSize(34, 34)
        icon_path = os.path.join(settings.BASE_DIR, "assets", "settings.svg")
        self.settings_btn.setIcon(QIcon(icon_path))
        self.settings_popover = SettingsPopover(settings.AUDIT_ENABLED, self)
        self.settings_popover.theme_changed.connect(self.set_dark_theme)
        self.settings_popover.export_requested.connect(self.export_audit)
        self.settings_btn.clicked.connect(self.toggle_settings_popover)
        header_layout.addWidget(self.settings_btn)

        window_layout.addWidget(self.header_bar)

        # =====================================================================
        # 2. Main Dashboard Split Layout (Sidebar + Chat Area)
        # =====================================================================
        dashboard_splitter = QSplitter(Qt.Horizontal)
        dashboard_splitter.setHandleWidth(1)

        # --- Sidebar panel ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(280)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        sidebar_title = QLabel("BELGELER")
        sidebar_title.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(sidebar_title)

        self.document_search = QLineEdit()
        self.document_search.setObjectName("DocumentSearch")
        self.document_search.setPlaceholderText("Belge ara…")
        self.document_search.textChanged.connect(self.filter_documents)
        sidebar_layout.addWidget(self.document_search)

        # Document Registry list widget
        self.docs_list = QListWidget()
        self.docs_list.setTextElideMode(Qt.ElideRight)
        self.docs_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.docs_list.itemClicked.connect(self.show_document_details)
        self.docs_list.itemDoubleClicked.connect(self.open_document_item)
        sidebar_layout.addWidget(self.docs_list)

        self.document_details = QFrame()
        self.document_details.setObjectName("DocumentDetails")
        details_layout = QVBoxLayout(self.document_details)
        details_layout.setContentsMargins(14, 12, 14, 12)
        details_layout.setSpacing(4)
        self.detail_name = QLabel("Bir belge seçin")
        self.detail_name.setObjectName("DocumentDetailName")
        self.detail_name.setWordWrap(True)
        self.detail_meta = QLabel("Durum ve güncelleme bilgisi burada görünür.")
        self.detail_meta.setObjectName("DocumentDetailMeta")
        self.detail_meta.setWordWrap(True)
        details_layout.addWidget(self.detail_name)
        details_layout.addWidget(self.detail_meta)
        self.open_document_btn = QPushButton("Belgeyi aç")
        self.open_document_btn.setObjectName("OpenDocumentButton")
        self.open_document_btn.setEnabled(False)
        self.open_document_btn.clicked.connect(self.open_selected_document)
        details_layout.addWidget(self.open_document_btn)
        sidebar_layout.addWidget(self.document_details)

        dashboard_splitter.addWidget(self.sidebar)
        self.sidebar.hide()

        # --- Right Chat Area panel ---
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Loader loading indicators
        self.loading_panel = QWidget()
        self.loading_panel.setObjectName("LoadingPanel")
        loading_layout = QVBoxLayout(self.loading_panel)
        loading_layout.setContentsMargins(20, 20, 20, 20)
        self.loading_label = QLabel("Sistem yükleniyor, lütfen bekleyin...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.loading_bar)
        chat_layout.addWidget(self.loading_panel)

        # Scrollable conversation area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("ChatStream")
        self.stream_layout = QVBoxLayout(self.scroll_widget)
        self.stream_layout.setContentsMargins(20, 20, 20, 20)
        self.stream_layout.setSpacing(14)
        self.welcome_label = QWidget()
        self.welcome_label.setObjectName("WelcomePanel")
        welcome_layout = QHBoxLayout(self.welcome_label)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        self.welcome_bubble = QFrame()
        self.welcome_bubble.setObjectName("AssistantWelcomeBubble")
        bubble_layout = QVBoxLayout(self.welcome_bubble)
        bubble_layout.setContentsMargins(16, 13, 16, 13)
        assistant_label = QLabel("Asistan")
        assistant_label.setObjectName("AssistantLabel")
        self.welcome_message = QLabel("Merhaba, belgelerinizle ilgili ne öğrenmek istersiniz?")
        self.welcome_message.setObjectName("WelcomeMessage")
        self.welcome_message.setWordWrap(True)
        bubble_layout.addWidget(assistant_label)
        bubble_layout.addWidget(self.welcome_message)
        welcome_layout.addWidget(self.welcome_bubble)
        welcome_layout.addStretch()
        self.stream_layout.addWidget(self.welcome_label)
        self.stream_layout.addStretch()  # Forces cards to top
        self.scroll_area.setWidget(self.scroll_widget)
        
        chat_layout.addWidget(self.scroll_area)

        # Input & Query submissions box
        self.input_area = QWidget()
        self.input_area.setObjectName("InputArea")
        self.input_area.setFixedHeight(76)
        input_layout = QHBoxLayout(self.input_area)
        input_layout.setContentsMargins(20, 14, 20, 14)
        input_layout.setSpacing(10)

        self.query_input = QLineEdit()
        self.query_input.setObjectName("QueryInput")
        self.query_input.setPlaceholderText("Belgeleriniz hakkında bir soru sorun…")
        self.query_input.setEnabled(False)
        self.query_input.returnPressed.connect(self.send_query)
        input_layout.addWidget(self.query_input, stretch=6)

        self.send_btn = QPushButton("Gönder")
        self.send_btn.setMinimumWidth(96)
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_query)
        input_layout.addWidget(self.send_btn, stretch=1)

        chat_layout.addWidget(self.input_area)
        
        dashboard_splitter.addWidget(chat_panel)
        dashboard_splitter.setSizes([0, 1120])

        window_layout.addWidget(dashboard_splitter)

    def apply_theme(self):
        """
        Applies compiled QSS stylesheets dynamically to the UI structure.
        """
        qss = generate_qss(self.current_theme)
        self.setStyleSheet(qss)
        
        self.settings_popover.light_theme_button.setChecked(self.current_theme == "light")
        self.settings_popover.dark_theme_button.setChecked(self.current_theme == "dark")

    def toggle_theme(self):
        """
        Toggles between light/dark options and applies it instantly.
        """
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        save_theme_preference(self.current_theme)
        
        theme = THEMES[self.current_theme]
        for i in range(self.stream_layout.count()):
            widget = self.stream_layout.itemAt(i).widget()
            if isinstance(widget, ChatCard):
                widget.apply_colors(theme.colors)

    def set_dark_theme(self, enabled):
        target = "dark" if enabled else "light"
        if self.current_theme == target:
            return
        self.toggle_theme()

    def toggle_settings_popover(self):
        if self.settings_popover.isVisible():
            self.settings_popover.hide()
            return
        self.settings_popover.adjustSize()
        anchor = self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomRight())
        self.settings_popover.move(
            anchor.x() - self.settings_popover.width(), anchor.y() + 6
        )
        self.settings_popover.show()

    def _bootstrap_system(self):
        """
        Runs document parsing and indexing in the background.
        """
        self.init_worker = InitWorker()
        self.init_worker.status_updated.connect(self.update_init_status)
        self.init_worker.finished.connect(self.on_init_finished)
        self.init_worker.error_occurred.connect(self.on_init_error)
        self.init_worker.start()

    def update_init_status(self, text):
        self.loading_label.setText(text)

    def on_init_finished(self, agent_instance):
        self.agent = agent_instance
        
        # Disable loading overlays
        self.loading_panel.setVisible(False)
        
        # Activate input controls
        self.query_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.query_input.setFocus()
        
        # Populate Sidebar document states
        self.populate_sidebar()
        
        self.settings_popover.set_system_status("Hazır", "ready")

    def on_init_error(self, error_str):
        self.loading_label.setText("Önyükleme hatası nedeniyle servis dışı!")
        self.settings_popover.set_system_status("Bağlantı yok", "error")
        
        QMessageBox.critical(
            self,
            "Sistem Başlatma Hatası",
            f"Veritabanı veya LLM servisleri yüklenemedi. "
            f"Ollama uygulamasının arka planda çalıştığından emin olun.\n\nHata: {error_str}"
        )

    def populate_sidebar(self):
        """
        Loads document registry configurations into the sidebar list.
        """
        self.docs_list.clear()
        try:
            from src.indexing.document_registry import DocumentRegistry
            registry = DocumentRegistry()
            active_count = 0
            
            for fname, info in registry.data.items():
                is_active = info.get("status") == "active"
                if is_active:
                    bullet = "●"
                    active_count += 1
                    status_str = "Aktif"
                else:
                    bullet = "○"
                    status_str = "Pasif"
                
                item_text = f"{bullet}  {fname}"
                self.docs_list.addItem(item_text)
                item = self.docs_list.item(self.docs_list.count() - 1)
                item.setToolTip(fname)
                item.setData(Qt.UserRole, {"filename": fname, **info, "status_label": status_str})
                
            self.documents_btn.setText(f"Belgeler · {self.docs_list.count()}")
            sidebar_title = self.sidebar.findChild(QLabel, "SidebarTitle")
            if sidebar_title:
                sidebar_title.setText(f"BELGELER  ·  {active_count} AKTİF")
        except Exception as e:
            logger.error(f"Doküman listesi yüklenemedi: {e}")
            self.documents_btn.setText("Belgeler · 0")

    def toggle_document_drawer(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def new_chat(self):
        for index in range(self.stream_layout.count() - 1, -1, -1):
            widget = self.stream_layout.itemAt(index).widget()
            if isinstance(widget, ChatCard):
                self.stream_layout.removeWidget(widget)
                widget.deleteLater()
        self.welcome_label.show()

    def filter_documents(self, text):
        query = text.strip().casefold()
        for index in range(self.docs_list.count()):
            item = self.docs_list.item(index)
            metadata = item.data(Qt.UserRole) or {}
            item.setHidden(query not in metadata.get("filename", item.text()).casefold())

    def show_document_details(self, item):
        metadata = item.data(Qt.UserRole) or {}
        filename = metadata.get("filename", item.text())
        status = metadata.get("status_label", "Bilinmiyor")
        updated_at = metadata.get("updated_at", "-")
        if updated_at and updated_at != "-":
            updated_at = updated_at.replace("T", " ")[:16]
        self.detail_name.setText(filename)
        self.detail_meta.setText(f"{status}  ·  Son güncelleme: {updated_at}")
        self.open_document_btn.setEnabled(True)

    def open_selected_document(self):
        item = self.docs_list.currentItem()
        if item is not None:
            self.open_document_item(item)

    def open_document_item(self, item):
        metadata = item.data(Qt.UserRole) or {}
        self.open_document(metadata.get("filename", item.text()))

    def open_document(self, filename, page=None):
        safe_name = os.path.basename(str(filename))
        docs_root = os.path.realpath(settings.DOCS_DIR)
        document_path = os.path.realpath(os.path.join(docs_root, safe_name))
        try:
            inside_docs = os.path.commonpath([docs_root, document_path]) == docs_root
        except ValueError:
            inside_docs = False
        if not inside_docs or not os.path.isfile(document_path):
            QMessageBox.warning(
                self, "Belge bulunamadı",
                f"Belge dosyasına erişilemiyor: {safe_name}"
            )
            return False

        url = QUrl.fromLocalFile(document_path)
        if page not in (None, ""):
            url.setFragment(f"page={page}")
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(
                self, "Belge açılamadı",
                f"Belge varsayılan PDF görüntüleyicisinde açılamadı: {safe_name}"
            )
            return False
        return True

    def _show_status(self, text, timeout=0):
        # Technical progress is intentionally confined to the startup panel.
        logger.debug(text)

    def send_query(self):
        """
        Executes search queries asynchronously on QThread.
        """
        query_text = self.query_input.text().strip()
        if not query_text or not self.agent:
            return
            
        # Disable inputs to prevent query overlapping
        self.query_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        self.query_worker = QueryWorker(self.agent, query_text)
        self.query_worker.finished.connect(self.on_query_finished)
        self.query_worker.error_occurred.connect(self.on_query_error)
        self.query_worker.start()

    def on_query_finished(self, response):
        # Enable inputs
        self.query_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.query_input.clear()
        self.query_input.setFocus()
        
        if self.welcome_label.isVisible():
            self.welcome_label.hide()

        # Create ChatCard widget and add to stream layout
        theme = THEMES[self.current_theme]
        card = ChatCard(
            query=self.query_worker.query_text,
            answer=response["answer"],
            sources=response["sources"],
            confidence=response["confidence_score"],
            colors=theme.colors
        )
        card.source_requested.connect(self.open_document)
        
        # Insert card right above the stretch item
        self.stream_layout.insertWidget(self.stream_layout.count() - 1, card)
        
        # Scroll to bottom dynamically
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        

    def on_query_error(self, error_str):
        self.query_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        QMessageBox.warning(
            self,
            "Sorgu Hatası",
            f"Bağlantı kesintisi nedeniyle cevap alınamadı. "
            f"Lütfen Ollama sunucusunu denetleyin.\n\nHata: {error_str}"
        )
        self._show_status("Sorgu hatası oluştu")

    def export_audit(self):
        """
        Triggers save dialog and exports audit history logs.
        """
        if not settings.AUDIT_ENABLED:
            QMessageBox.information(self, "Audit Kapalı", "AUDIT_ENABLED=true olmadan audit kaydı veya export oluşturulmaz.")
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Denetim Kayıtlarını Dışa Aktar",
            "",
            "CSV Dosyası (*.csv);;Excel Dosyası (*.xlsx)"
        )
        
        if not file_path:
            return
            
        export_format = "xlsx" if file_path.endswith(".xlsx") else "csv"
        if export_format == "csv" and not file_path.endswith(".csv"):
            file_path += ".csv"
            
        try:
            export_audit_logs(export_path=file_path, format=export_format)
            QMessageBox.information(
                self,
                "Başarılı",
                f"Denetim kayıtları başarıyla ihraç edildi:\n{file_path}"
            )
            self._show_status("İşlem kayıtları dışa aktarıldı", 4000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "İhraç Hatası",
                f"Kayıtlar ihraç edilirken hata: {str(e)}"
            )
            self._show_status("Dışa aktarma hatası")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
