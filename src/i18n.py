"""Small, dependency-free Turkish/English localization catalog."""

import string

SUPPORTED_LANGUAGES = ("tr", "en")
DEFAULT_LANGUAGE = "tr"

TRANSLATIONS = {
    "tr": {
        "app.title": "Local Belge Asistanı", "documents": "Belgeler", "documents.upper": "BELGELER",
        "active.upper": "AKTİF", "new_chat": "Yeni sohbet", "settings": "Ayarlar",
        "preparing": "Hazırlanıyor", "ready": "Hazır", "offline": "Bağlantı yok",
        "status.loading_desc": "Belgeler ve yerel model kontrol ediliyor.",
        "status.ready_desc": "Yerel arama kullanıma hazır.", "status.error_desc": "Yerel servis başlatılamadı.",
        "appearance": "Görünüm", "light": "Açık", "dark": "Koyu", "light_theme": "Açık tema",
        "dark_theme": "Koyu tema", "language": "Dil", "export": "Dışa aktar",
        "search_documents": "Belge ara…", "select_document": "Bir belge seçin",
        "document_detail_hint": "Durum ve güncelleme bilgisi burada görünür.", "open_document": "Belgeyi aç",
        "loading": "Sistem yükleniyor, lütfen bekleyin...", "assistant": "Asistan",
        "welcome": "Merhaba, belgelerinizle ilgili ne öğrenmek istersiniz?",
        "query_placeholder": "Belgeleriniz hakkında bir soru sorun…", "send": "Gönder",
        "question": "Soru", "copy": "Kopyala", "copied": "Kopyalandı", "sources": "Kaynaklar",
        "page": "Sayfa", "open_document_tip": "Belgeyi aç", "confidence.high": "Yüksek Güven ({score:.2f})",
        "confidence.medium": "Orta Güven ({score:.2f})", "confidence.none": "Bulunamadı",
        "status.active": "Aktif", "status.inactive": "Pasif", "status.unknown": "Bilinmiyor",
        "last_updated": "Son güncelleme", "boot_error_short": "Önyükleme hatası nedeniyle servis dışı!",
        "boot_error_title": "Sistem Başlatma Hatası", "boot_error": "Veritabanı veya LLM servisleri yüklenemedi. Ollama uygulamasının arka planda çalıştığından emin olun.\n\nHata: {error}",
        "document_missing_title": "Belge bulunamadı", "document_missing": "Belge dosyasına erişilemiyor: {name}",
        "document_open_error_title": "Belge açılamadı", "document_open_error": "Belge varsayılan PDF görüntüleyicisinde açılamadı: {name}",
        "query_error_title": "Sorgu Hatası", "query_error": "Bağlantı kesintisi nedeniyle cevap alınamadı. Lütfen Ollama sunucusunu denetleyin.\n\nHata: {error}",
        "fallback": "İlgili dokümanlarda bu konuda yeterli bilgi bulunamadı.",
        "retrieval_error": "Yerel arama servisine ulaşılamadı. Ollama servisini ve embedding modelini kontrol edin.",
        "model_error": "Yerel dil modeli şu anda yanıt üretemedi. Ollama servisini ve model ayarlarını kontrol edin.",
        "unknown_document": "Bilinmeyen Doküman", "cli.title": "BANKA İÇİ YEREL RAG REHBERLİK ASİSTANI - CLI ARAYÜZÜ",
        "cli.active_model": "Aktif Model", "cli.embedding_model": "Embedding Modeli", "cli.threshold": "Güvenlik Eşiği",
        "cli.starting": ">>> Sistem başlatılıyor...", "cli.scanning": "-> Dokümanlar taranıyor...",
        "cli.no_changes": "-> Doküman kayıtlarında yeni bir değişiklik tespit edilmedi.", "cli.building": "-> RAG Ajanı kuruluyor...",
        "cli.ready": ">>> Sistem başarıyla hazırlandı!", "cli.help": "Komutlar:\n  - ':q' veya ':quit' : Uygulamadan çıkış yapar.\n  - ':export'         : Denetim (audit) günlüklerini CSV olarak ihraç eder.\n  - ':status'         : Kayıtlı dokümanların durumunu listeler.\n  - ':language tr|en' : Arayüz ve yanıt dilini değiştirir.",
        "cli.prompt": "Soru girin > ", "cli.exiting": "Çıkış yapılıyor...", "cli.searching": "Yanıt aranıyor...",
        "cli.answer": "Cevap", "cli.no_source": "Kaynak: Yok (Güven Eşiği Altı)", "cli.score": "Güven Skoru",
        "cli.status_title": "Kayıtlı Dokümanların Durumu", "cli.updated": "Son Güncelleme",
        "cli.language_changed": "Dil Türkçe olarak değiştirildi.", "cli.language_usage": "Kullanım: :language tr veya :language en",
        "init.indexing": "İndeksleniyor: {name}", "init.some_failed": "Bazı belgeler indekslenemedi; sonraki açılışta yeniden denenecek.",
        "audit.disabled_title": "Audit Kapalı", "audit.disabled": "AUDIT_ENABLED=true olmadan audit kaydı veya export oluşturulmaz.",
        "audit.export_title": "Denetim Kayıtlarını Dışa Aktar", "audit.file_filter": "CSV Dosyası (*.csv);;Excel Dosyası (*.xlsx)",
        "audit.success_title": "Başarılı", "audit.success": "Denetim kayıtları başarıyla ihraç edildi:\n{path}",
        "audit.error_title": "İhraç Hatası", "audit.error": "Kayıtlar ihraç edilirken hata: {error}",
    },
    "en": {
        "app.title": "Local Document Assistant", "documents": "Documents", "documents.upper": "DOCUMENTS",
        "active.upper": "ACTIVE", "new_chat": "New chat", "settings": "Settings",
        "preparing": "Preparing", "ready": "Ready", "offline": "Offline",
        "status.loading_desc": "Documents and the local model are being checked.",
        "status.ready_desc": "Local search is ready.", "status.error_desc": "The local service could not start.",
        "appearance": "Appearance", "light": "Light", "dark": "Dark", "light_theme": "Light theme",
        "dark_theme": "Dark theme", "language": "Language", "export": "Export",
        "search_documents": "Search documents…", "select_document": "Select a document",
        "document_detail_hint": "Status and update information will appear here.", "open_document": "Open document",
        "loading": "The system is loading, please wait...", "assistant": "Assistant",
        "welcome": "Hello, what would you like to learn from your documents?",
        "query_placeholder": "Ask a question about your documents…", "send": "Send",
        "question": "Question", "copy": "Copy", "copied": "Copied", "sources": "Sources",
        "page": "Page", "open_document_tip": "Open document", "confidence.high": "High Confidence ({score:.2f})",
        "confidence.medium": "Medium Confidence ({score:.2f})", "confidence.none": "Not found",
        "status.active": "Active", "status.inactive": "Inactive", "status.unknown": "Unknown",
        "last_updated": "Last updated", "boot_error_short": "Service unavailable due to a startup error!",
        "boot_error_title": "System Startup Error", "boot_error": "The database or LLM services could not be loaded. Make sure Ollama is running in the background.\n\nError: {error}",
        "document_missing_title": "Document not found", "document_missing": "The document file cannot be accessed: {name}",
        "document_open_error_title": "Document could not be opened", "document_open_error": "The document could not be opened in the default PDF viewer: {name}",
        "query_error_title": "Query Error", "query_error": "No answer was received due to a connection interruption. Please check the Ollama server.\n\nError: {error}",
        "fallback": "The relevant documents do not contain enough information about this topic.",
        "retrieval_error": "The local search service could not be reached. Check Ollama and the embedding model.",
        "model_error": "The local language model could not generate an answer. Check Ollama and the model settings.",
        "unknown_document": "Unknown Document", "cli.title": "INTERNAL BANK LOCAL RAG GUIDANCE ASSISTANT - CLI",
        "cli.active_model": "Active Model", "cli.embedding_model": "Embedding Model", "cli.threshold": "Confidence Threshold",
        "cli.starting": ">>> Starting system...", "cli.scanning": "-> Scanning documents...",
        "cli.no_changes": "-> No changes detected in document records.", "cli.building": "-> Building RAG Agent...",
        "cli.ready": ">>> System is ready!", "cli.help": "Commands:\n  - ':q' or ':quit'   : Exit the application.\n  - ':export'         : Export audit logs as CSV.\n  - ':status'         : List registered document statuses.\n  - ':language tr|en' : Change the interface and answer language.",
        "cli.prompt": "Enter a question > ", "cli.exiting": "Exiting...", "cli.searching": "Searching for an answer...",
        "cli.answer": "Answer", "cli.no_source": "Source: None (Below Confidence Threshold)", "cli.score": "Confidence Score",
        "cli.status_title": "Registered Document Status", "cli.updated": "Last Updated",
        "cli.language_changed": "Language changed to English.", "cli.language_usage": "Usage: :language tr or :language en",
        "init.indexing": "Indexing: {name}", "init.some_failed": "Some documents could not be indexed; they will be retried at the next startup.",
        "audit.disabled_title": "Audit Disabled", "audit.disabled": "Audit records or exports are not created unless AUDIT_ENABLED=true.",
        "audit.export_title": "Export Audit Records", "audit.file_filter": "CSV File (*.csv);;Excel File (*.xlsx)",
        "audit.success_title": "Success", "audit.success": "Audit records were exported successfully:\n{path}",
        "audit.error_title": "Export Error", "audit.error": "An error occurred while exporting records: {error}",
    },
}

def normalize_language(language):
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

def translate(key, language=DEFAULT_LANGUAGE, **values):
    language = normalize_language(language)
    text = TRANSLATIONS[language].get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    return text.format(**values) if values else text

def catalog_format_fields(language, key):
    text = TRANSLATIONS[language][key]
    return {field for _, field, _, _ in string.Formatter().parse(text) if field}
