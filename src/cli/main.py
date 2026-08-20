import os
import sys
from src.config import settings
from src.indexing.document_registry import DocumentRegistry
from src.indexing.chunker import DocumentChunker
from src.indexing.vectorstore_manager import VectorStoreManager
from src.indexing.index_lifecycle import synchronize_index
from src.agent.agent_builder import AgentBuilder
from src.audit.audit_export import export_audit_logs
from src.i18n import translate as tr
from src.ui.theme import load_language_preference, save_language_preference

def bootstrap_system(language="tr"):
    """
    Initializes and boots the RAG indexing system.
    """
    print("\n" + tr("cli.starting", language))
    
    # 1. Ensure directories exist
    os.makedirs(settings.DOCS_DIR, exist_ok=True)
    os.makedirs(settings.DB_DIR, exist_ok=True)
    if settings.AUDIT_ENABLED:
        settings.validate_audit_settings()
        os.makedirs(settings.AUDIT_DIR, exist_ok=True)
    
    # 2. Document Registry Scan
    print(tr("cli.scanning", language))
    registry = DocumentRegistry()
    changes = registry.scan_docs_folder()
    
    if any(changes.values()):
        _, failures = synchronize_index(registry=registry)
        if failures:
            print("-> İndekslenemeyen ve sonraki açılışta yeniden denenecek dosyalar: " + ", ".join(failures))
    else:
        print(tr("cli.no_changes", language))

    # 5. Build and return RAG Agent pipeline
    print(tr("cli.building", language))
    agent = AgentBuilder.build_agent() if language == "tr" else AgentBuilder.build_agent(language=language)
    print(tr("cli.ready", language) + "\n")
    return agent

def main():
    language = load_language_preference()
    print("=" * 80)
    print(tr("cli.title", language))
    print("=" * 80)
    print(f"{tr('cli.active_model', language)}: {settings.CHAT_MODEL}")
    print(f"{tr('cli.embedding_model', language)}: {settings.EMBED_MODEL}")
    print(f"{tr('cli.threshold', language)}: {settings.CONFIDENCE_THRESHOLD}")
    print("=" * 80)
    
    try:
        agent = bootstrap_system(language)
    except Exception as e:
        print(f"\n[KRİTİK HATA] Sistem başlatılamadı: {e}")
        sys.exit(1)
        
    print(tr("cli.help", language))
    print("-" * 80)
    
    while True:
        try:
            query = input("\n" + tr("cli.prompt", language)).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n" + tr("cli.exiting", language))
            break
            
        if not query:
            continue
            
        if query in [":q", ":quit"]:
            print(tr("cli.exiting", language))
            break

        if query.startswith(":language"):
            parts = query.split()
            if len(parts) != 2 or parts[1] not in ("tr", "en"):
                print(tr("cli.language_usage", language))
                continue
            language = parts[1]
            save_language_preference(language)
            agent.set_language(language)
            print(tr("cli.language_changed", language))
            print(tr("cli.help", language))
            continue
            
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
            print("\n" + tr("cli.status_title", language) + ":")
            for filename, info in registry.data.items():
                status = tr("status.active", language) if info.get("status") == "active" else tr("status.inactive", language)
                print(f"  - {filename} [{status}] ({tr('cli.updated', language)}: {info.get('updated_at')})")
            continue
            
        # Execute query
        print(tr("cli.searching", language))
        response = agent.query(query)
        
        print("\n" + tr("cli.answer", language) + ":")
        print(response["answer"])
        
        if response["sources"]:
            print("\n" + tr("sources", language) + ":")
            for src in response["sources"]:
                print(f"  - {src['source']} ({tr('page', language)} {src['page']})")
        else:
            print("\n" + tr("cli.no_source", language))
            
        print(f"{tr('cli.score', language)}: {response['confidence_score']:.4f}")
        print("-" * 80)

if __name__ == "__main__":
    main()
