import os
import json
import hashlib
import tempfile
from datetime import datetime
from typing import Dict, Any, List
from src.config import settings

class DocumentRegistry:
    """
    Manages document metadata (filename, content hash, status, dates)
    and detects disk changes (added, modified, deleted PDFs).
    """
    
    def __init__(self, registry_path: str = None):
        """
        Initializes the registry and loads existing metadata.
        """
        self.registry_path = registry_path or os.path.join(settings.DB_DIR, "document_registry.json")
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """
        Loads registry data from JSON file.
        """
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        """
        Saves registry data to JSON file.
        """
        directory = os.path.dirname(self.registry_path)
        os.makedirs(directory, exist_ok=True)
        fd, temporary_path = tempfile.mkstemp(prefix=".registry-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary_path, self.registry_path)
        except Exception:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
            raise

    def _calculate_hash(self, file_path: str) -> str:
        """
        Calculates SHA-256 hash of a file for change detection.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def scan_docs_folder(self) -> Dict[str, List[str]]:
        """
        Scans docs/ folder and compares hashes to detect added, modified, or deleted files.
        This operation is read-only. Call mark_indexed/remove after vector-store success.
        
        Returns:
            Dict: Dictionary containing lists of 'added', 'modified', and 'deleted' file names.
        """
        docs_dir = settings.DOCS_DIR
        current_files = {}
        
        if os.path.exists(docs_dir):
            for file_name in os.listdir(docs_dir):
                if file_name.lower().endswith(".pdf"):
                    full_path = os.path.join(docs_dir, file_name)
                    if os.path.isfile(full_path):
                        current_files[file_name] = full_path

        changes = {"added": [], "modified": [], "deleted": []}
        
        # Check for added and modified files
        for file_name, path in current_files.items():
            file_hash = self._calculate_hash(path)
            if file_name not in self.data:
                changes["added"].append(file_name)
            else:
                # Document already exists, compare hash
                if self.data[file_name]["hash"] != file_hash:
                    changes["modified"].append(file_name)
                    
        # Check for deleted files (registered but no longer on disk)
        registered_files = list(self.data.keys())
        for file_name in registered_files:
            if file_name not in current_files:
                changes["deleted"].append(file_name)
        return changes

    def mark_indexed(self, filename: str, file_path: str = None, index_generation: str = None):
        path = file_path or os.path.join(settings.DOCS_DIR, filename)
        now = datetime.now().isoformat()
        old = self.data.get(filename, {})
        new_record = {
            "filename": filename, "hash": self._calculate_hash(path),
            "status": old.get("status", "active"),
            "added_at": old.get("added_at", now), "updated_at": now,
        }
        if index_generation is not None:
            new_record["index_generation"] = index_generation
        self.data[filename] = new_record
        try:
            self.save()
        except Exception:
            if old:
                self.data[filename] = old
            else:
                self.data.pop(filename, None)
            raise

    def remove(self, filename: str):
        if self.data.pop(filename, None) is not None:
            self.save()

    @property
    def registry(self):
        """Compatibility alias for older callers."""
        return self.data

    def get_active_documents(self) -> List[str]:
        """
        Returns a list of active document filenames.
        """
        return [fname for fname, info in self.data.items() if info.get("status") == "active"]

    def get_active_indexes(self) -> List[Dict[str, str]]:
        """Return active source/generation selectors; generation-less records are legacy."""
        return [
            {"source": fname, "index_generation": info.get("index_generation")}
            for fname, info in self.data.items() if info.get("status") == "active"
        ]

    def set_status(self, filename: str, status: str):
        """
        Sets document status to 'active' or 'passive'.
        """
        if status not in ["active", "passive"]:
            raise ValueError("Status 'active' veya 'passive' olmalıdır.")
        if filename in self.data:
            self.data[filename]["status"] = status
            self.data[filename]["updated_at"] = datetime.now().isoformat()
            self.save()
        else:
            raise KeyError(f"Doküman bulunamadı: {filename}")
            
    def get_document_info(self, filename: str) -> Dict[str, Any]:
        """
        Returns info for a specific registered document.
        """
        return self.data.get(filename)
