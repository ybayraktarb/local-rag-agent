import os
import sys
import logging
from datetime import datetime
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QListWidget, QFileDialog, QMessageBox,
    QProgressBar, QStatusBar, QScrollArea, QFrame, QSplitter
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
            os.makedirs(settings.AUDIT_DIR, exist_ok=True)

            self.status_updated.emit("Belgeler taranıyor...")
            registry = DocumentRegistry()
            changes = registry.scan_docs_folder()

            # Handle delta indexing
            if changes["added"] or changes["modified"]:
                to_index = changes["added"] + changes["modified"]
                total_files = len(to_index)
                self.status_updated.emit(f"{total_files} adet yeni/değişen belge indeksleniyor, lütfen bekleyin...")
                
                vstore_manager = VectorStoreManager()
                chunker = DocumentChunker()

                for idx, filename in enumerate(to_index):
                    file_path = os.path.join(settings.DOCS_DIR, filename)
                    self.status_updated.emit(f"Yükleniyor ve İndeksleniyor ({idx+1}/{total_files}): {filename}...")
                    
                    loader = PDFLoader(file_path)
                    docs = loader.load()
                    chunks = chunker.split_documents(docs)
                    vstore_manager.add_documents(chunks)
                    
            # Handle document cleanup
            if changes["deleted"]:
                self.status_updated.emit("Silinen dosyaların verileri temizleniyor...")
                vstore_manager = VectorStoreManager()
                for filename in changes["deleted"]:
                    vstore_manager.delete_document_chunks(filename)

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


class ChatCard(QFrame):
    """
    Premium card display for user queries and AI responses with sources and badges.
    """
    def __init__(self, query: str, answer: str, sources: list, confidence: float, colors: dict):
        super().__init__()
        self.setObjectName("ChatCard")
        self.setFrameShape(QFrame.StyledPanel)
        
        card_layout = QVBoxLayout(self)
        card_layout.setSpacing(8)
        card_layout.setContentsMargins(16, 16, 16, 16)

        # 1. Header line (Query text + Confidence Badge)
        header_layout = QHBoxLayout()
        query_label = QLabel(f"Soru: {query}")
        query_label.setObjectName("UserQueryLabel")
        query_label.setWordWrap(True)
        header_layout.addWidget(query_label, stretch=4)

        # Confidence Score Badge
        badge = QLabel()
        badge.setObjectName("ConfidenceBadge")
        badge.setAlignment(Qt.AlignCenter)
        
        # Color coding configuration
        if confidence >= settings.CONFIDENCE_HIGH_THRESHOLD:
            badge_color = colors["success"]
            badge_text = f"Yüksek Güven ({confidence:.2f})"
        elif confidence >= settings.CONFIDENCE_THRESHOLD:
            badge_color = colors["warning"]
            badge_text = f"Orta Güven ({confidence:.2f})"
        else:
            badge_color = colors["error"]
            badge_text = "Bulunamadı"

        badge.setText(badge_text)
        badge.setStyleSheet(f"background-color: {badge_color}; border-radius: 4px; padding: 2px 8px; color: #FFFFFF; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(badge, stretch=1)
        card_layout.addLayout(header_layout)

        # 2. Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {colors['border']}; max-height: 1px;")
        card_layout.addWidget(line)

        # 3. Bot Response body
        answer_label = QLabel(answer)
        answer_label.setObjectName("BotAnswerLabel")
        answer_label.setWordWrap(True)
        answer_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        card_layout.addWidget(answer_label)

        # 4. Sources list (if any)
        if sources:
            sources_layout = QHBoxLayout()
            src_texts = [f"{s.get('source', '')} (S.{s.get('page', '')})" for s in sources]
            src_label = QLabel(f"Kaynaklar: {', '.join(src_texts)}")
            src_label.setObjectName("SourcesLabel")
            src_label.setWordWrap(True)
            sources_layout.addWidget(src_label)
            card_layout.addLayout(sources_layout)


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
        
        self.setWindowTitle("Kılavuz: Kurumsal Bilgi Asistanı")
        self.resize(1000, 700)
        
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
        self.header_bar.setFixedHeight(50)
        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(15, 0, 15, 0)

        # Monogram Icon / Abstract Brand Symbol
        monogram = QLabel("⚙️")
        monogram.setStyleSheet("font-size: 18px;")
        header_layout.addWidget(monogram)

        # App branding name
        app_title = QLabel("Kılavuz: Kurumsal Bilgi Asistanı")
        app_title.setObjectName("AppTitle")
        header_layout.addWidget(app_title)
        header_layout.addStretch()

        # Theme toggle action
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("ThemeToggle")
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)

        window_layout.addWidget(self.header_bar)

        # =====================================================================
        # 2. Main Dashboard Split Layout (Sidebar + Chat Area)
        # =====================================================================
        dashboard_splitter = QSplitter(Qt.Horizontal)
        dashboard_splitter.setHandleWidth(1)

        # --- Sidebar panel ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        sidebar_title = QLabel("DOKÜMAN REHBERİ")
        sidebar_title.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(sidebar_title)

        # Document Registry list widget
        self.docs_list = QListWidget()
        sidebar_layout.addWidget(self.docs_list)

        dashboard_splitter.addWidget(self.sidebar)

        # --- Right Chat Area panel ---
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Loader loading indicators
        self.loading_panel = QWidget()
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
        self.stream_layout.setSpacing(10)
        self.stream_layout.addStretch()  # Forces cards to top
        self.scroll_area.setWidget(self.scroll_widget)
        
        chat_layout.addWidget(self.scroll_area)

        # Input & Query submissions box
        self.input_area = QWidget()
        self.input_area.setObjectName("InputArea")
        self.input_area.setFixedHeight(65)
        input_layout = QHBoxLayout(self.input_area)
        input_layout.setContentsMargins(15, 10, 15, 10)

        self.query_input = QLineEdit()
        self.query_input.setObjectName("QueryInput")
        self.query_input.setPlaceholderText("Kurumsal prosedürlerle ilgili sorunuzu sorun (örn: Kredi başvuruları...)")
        self.query_input.setEnabled(False)
        self.query_input.returnPressed.connect(self.send_query)
        input_layout.addWidget(self.query_input, stretch=6)

        self.send_btn = QPushButton("Sor")
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(self.send_query)
        input_layout.addWidget(self.send_btn, stretch=1)

        chat_layout.addWidget(self.input_area)
        
        dashboard_splitter.addWidget(chat_panel)
        dashboard_splitter.setSizes([240, 760]) # Initialize sizes

        window_layout.addWidget(dashboard_splitter)

        # =====================================================================
        # 3. Status Bar
        # =====================================================================
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Left status indicators
        self.status_ollama = QLabel("Ollama: Yükleniyor...")
        self.status_docs = QLabel("Dokümanlar: -")
        self.status_bar.addPermanentWidget(self.status_ollama)
        self.status_bar.addPermanentWidget(self.status_docs)

        # Right status export action
        self.export_btn = QPushButton("Günlüğü İhraç Et")
        self.export_btn.setObjectName("ExportButton")
        self.export_btn.clicked.connect(self.export_audit)
        self.status_bar.addPermanentWidget(self.export_btn)

    def apply_theme(self):
        """
        Applies compiled QSS stylesheets dynamically to the UI structure.
        """
        qss = generate_qss(self.current_theme)
        self.setStyleSheet(qss)
        
        # Update toggle buttons icon representation
        if self.current_theme == "dark":
            self.theme_btn.setText("☀️ Açık Tema")
        else:
            self.theme_btn.setText("🌙 Koyu Tema")

    def toggle_theme(self):
        """
        Toggles between light/dark options and applies it instantly.
        """
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        save_theme_preference(self.current_theme)
        
        # Re-render chat card metrics so their border/divider styles refresh with the theme colors
        theme = THEMES[self.current_theme]
        for i in range(self.stream_layout.count()):
            widget = self.stream_layout.itemAt(i).widget()
            if isinstance(widget, ChatCard):
                widget.setStyleSheet(f"background-color: {theme.colors['surface']}; border: 1px solid {theme.colors['border']};")

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
        self.status_bar.showMessage(text)

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
        
        self.status_ollama.setText("Ollama: Bağlı")
        self.status_bar.showMessage("Sistem hazır. Sorunuzu yöneltebilirsiniz.", 6000)

    def on_init_error(self, error_str):
        self.loading_label.setText("Önyükleme hatası nedeniyle servis dışı!")
        self.status_ollama.setText("Ollama: Bağlantı Yok")
        
        QMessageBox.critical(
            self,
            "Sistem Başlatma Hatası",
            f"Veritabanı veya LLM servisleri yüklenemedi. "
            f"Ollama uygulamasının arka planda çalıştığından emin olun.\n\nHata: {error_str}"
        )
        self.status_bar.showMessage("Hata: Servis başlatılamadı.")

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
                
                item_text = f"{bullet}  {fname} ({status_str})"
                self.docs_list.addItem(item_text)
                
            self.status_docs.setText(f"Dokümanlar: {active_count} Aktif")
        except Exception as e:
            logger.error(f"Doküman listesi yüklenemedi: {e}")
            self.status_docs.setText("Dokümanlar: Hata")

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
        self.status_bar.showMessage("Sorgu işleniyor, lütfen bekleyin...")
        
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
        
        # Create ChatCard widget and add to stream layout
        theme = THEMES[self.current_theme]
        card = ChatCard(
            query=self.query_worker.query_text,
            answer=response["answer"],
            sources=response["sources"],
            confidence=response["confidence_score"],
            colors=theme.colors
        )
        
        # Insert card right above the stretch item
        self.stream_layout.insertWidget(self.stream_layout.count() - 1, card)
        
        # Scroll to bottom dynamically
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        
        self.status_bar.showMessage("Yanıt hazır.", 3000)

    def on_query_error(self, error_str):
        self.query_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        QMessageBox.warning(
            self,
            "Sorgu Hatası",
            f"Bağlantı kesintisi nedeniyle cevap alınamadı. "
            f"Lütfen Ollama sunucusunu denetleyin.\n\nHata: {error_str}"
        )
        self.status_bar.showMessage("Sorgu hatası oluştu.")

    def export_audit(self):
        """
        Triggers save dialog and exports audit history logs.
        """
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
            self.status_bar.showMessage("İşlem kayıtları ihraç edildi.", 4000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "İhraç Hatası",
                f"Kayıtlar ihraç edilirken hata: {str(e)}"
            )
            self.status_bar.showMessage("İhraç hatası.")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
