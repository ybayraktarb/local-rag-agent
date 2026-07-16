import os
import sys
from src.config import settings
from src.indexing.document_registry import DocumentRegistry
from src.indexing.chunker import DocumentChunker
from src.indexing.vectorstore_manager import VectorStoreManager
from src.indexing.index_lifecycle import synchronize_index
from src.agent.agent_builder import AgentBuilder
from src.audit.audit_export import export_audit_logs

def bootstrap_system():
    """
    Initializes and boots the RAG indexing system.
    """
    print("\n>>> Sistem başlatılıyor...")
    
    # 1. Ensure directories exist
    os.makedirs(settings.DOCS_DIR, exist_ok=True)
    os.makedirs(settings.DB_DIR, exist_ok=True)
    if settings.AUDIT_ENABLED:
        settings.validate_audit_settings()
        os.makedirs(settings.AUDIT_DIR, exist_ok=True)
    
    # 2. Document Registry Scan
    print("-> Dokümanlar taranıyor...")
    registry = DocumentRegistry()
    changes = registry.scan_docs_folder()
    
    if any(changes.values()):
        _, failures = synchronize_index(registry=registry)
        if failures:
            print("-> İndekslenemeyen ve sonraki açılışta yeniden denenecek dosyalar: " + ", ".join(failures))
    else:
        print("-> Doküman kayıtlarında yeni bir değişiklik tespit edilmedi.")

    # 5. Build and return RAG Agent pipeline
    print("-> RAG Ajanı kuruluyor...")
    agent = AgentBuilder.build_agent()
    print(">>> Sistem başarıyla hazırlandı!\n")
    return agent

def main():
    print("=" * 80)
    print("BANKA İÇİ YEREL RAG REHBERLİK ASİSTANI - CLI ARAYÜZÜ")
    print("=" * 80)
    print(f"Aktif Model: {settings.CHAT_MODEL}")
    print(f"Embedding Modeli: {settings.EMBED_MODEL}")
    print(f"Güvenlik Eşiği: {settings.CONFIDENCE_THRESHOLD}")
    print("=" * 80)
    
    try:
        agent = bootstrap_system()
    except Exception as e:
        print(f"\n[KRİTİK HATA] Sistem başlatılamadı: {e}")
        sys.exit(1)
        
    print("Komutlar:")
    print("  - ':q' veya ':quit' : Uygulamadan çıkış yapar.")
    print("  - ':export'         : Denetim (audit) günlüklerini CSV olarak ihraç eder.")
    print("  - ':status'         : Kayıtlı dokümanların durumunu listeler.")
    print("-" * 80)
    
    while True:
        try:
            query = input("\nSoru girin > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nÇıkış yapılıyor...")
            break
            
        if not query:
            continue
            
        if query in [":q", ":quit"]:
            print("Çıkış yapılıyor...")
            break
            
        if query == ":export":
            if not settings.AUDIT_ENABLED:
                print("[BİLGİ] Audit kapalı. .env içinde AUDIT_ENABLED=true olarak etkinleştirin.")
                continue
            csv_path = os.path.join(settings.AUDIT_DIR, "audit_log_cli.csv")
            try:
                export_audit_logs(export_path=csv_path, format="csv")
                print(f"[BAŞARILI] Günlükler '{csv_path}' adresine ihraç edildi.")
            except Exception as e:
                print(f"[HATA] Günlükler ihraç edilemedi: {e}")
            continue
            
        if query == ":status":
            registry = DocumentRegistry()
            print("\nKayıtlı Dokümanların Durumu:")
            for filename, info in registry.data.items():
                status = "Aktif" if info.get("status") == "active" else "Pasif"
                print(f"  - {filename} [{status}] (Son Güncelleme: {info.get('updated_at')})")
            continue
            
        # Execute query
        print("Yanıt aranıyor...")
        response = agent.query(query)
        
        print("\nCevap:")
        print(response["answer"])
        
        if response["sources"]:
            print("\nKaynaklar:")
            for src in response["sources"]:
                print(f"  - {src['source']} (Sayfa {src['page']})")
        else:
            print("\nKaynak: Yok (Güven Eşiği Altı)")
            
        print(f"Güven Skoru: {response['confidence_score']:.4f}")
        print("-" * 80)

if __name__ == "__main__":
    main()
