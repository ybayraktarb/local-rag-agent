import os
import json
import hashlib
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
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

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
        Automatically updates registry state and saves it.
        
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
                # Document is new
                self.data[file_name] = {
                    "filename": file_name,
                    "hash": file_hash,
                    "status": "active",  # Defaults to active
                    "added_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                changes["added"].append(file_name)
            else:
                # Document already exists, compare hash
                if self.data[file_name]["hash"] != file_hash:
                    self.data[file_name]["hash"] = file_hash
                    self.data[file_name]["updated_at"] = datetime.now().isoformat()
                    changes["modified"].append(file_name)
                    
        # Check for deleted files (registered but no longer on disk)
        registered_files = list(self.data.keys())
        for file_name in registered_files:
            if file_name not in current_files:
                del self.data[file_name]
                changes["deleted"].append(file_name)

        if changes["added"] or changes["modified"] or changes["deleted"]:
            self.save()
            
        return changes

    def get_active_documents(self) -> List[str]:
        """
        Returns a list of active document filenames.
        """
        return [fname for fname, info in self.data.items() if info.get("status") == "active"]

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
