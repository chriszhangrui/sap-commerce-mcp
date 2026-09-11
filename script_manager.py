import os
import json
import re
import datetime
from typing import Optional, List, Dict, Any

LIBRARY_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "script_library")

class ScriptManager:
    def __init__(self, base_dir: str = LIBRARY_BASE):
        self.base_dir = base_dir
        self.impex_dir = os.path.join(base_dir, "impex")
        self.groovy_dir = os.path.join(base_dir, "groovy")
        self.templates_dir = os.path.join(base_dir, "templates")
        self.index_file = os.path.join(base_dir, "index.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(self.impex_dir, exist_ok=True)
        os.makedirs(self.groovy_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        if not os.path.exists(self.index_file):
            self._save_index([])

    def _load_index(self) -> List[Dict[str, Any]]:
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_index(self, data: List[Dict[str, Any]]):
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def archive_script(
        self,
        content: str,
        script_type: str,  # "impex" or "groovy"
        name: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        description: str = "",
        client_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Archives a verified successful script into the unified script library.
        """
        now = datetime.datetime.now()
        ts_str = now.strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5-]', '_', name).strip('_')
        stype = script_type.lower().strip()
        
        ext = "impex" if stype == "impex" else "groovy"
        target_sub = self.impex_dir if ext == "impex" else self.groovy_dir
        
        file_name = f"{ts_str}_{slug}.{ext}"
        full_path = os.path.join(target_sub, file_name)

        header_comment = f"# Verified Script: {name}\n# Category: {category} | Client: {client_name or 'Generic'}\n# Date: {now.strftime('%Y-%m-%d %H:%M:%S')}\n# Tags: {', '.join(tags or [])}\n\n" if ext == "impex" else f"// Verified Script: {name}\n// Category: {category} | Client: {client_name or 'Generic'}\n// Date: {now.strftime('%Y-%m-%d %H:%M:%S')}\n// Tags: {', '.join(tags or [])}\n\n"
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(header_comment + content)

        script_entry = {
            "id": f"{ext}_{ts_str}_{slug}",
            "name": name,
            "type": ext,
            "category": category,
            "client": client_name or "Generic",
            "tags": tags or [],
            "description": description,
            "file_name": file_name,
            "path": full_path,
            "line_count": len(content.splitlines()),
            "created_at": now.isoformat()
        }

        index = self._load_index()
        index.insert(0, script_entry)
        self._save_index(index)

        return script_entry

    def list_scripts(
        self,
        script_type: Optional[str] = None,
        category: Optional[str] = None,
        client: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches the unified library for saved working scripts.
        """
        index = self._load_index()
        results = []
        q_lower = query.lower() if query else None

        for item in index:
            if script_type and item["type"].lower() != script_type.lower():
                continue
            if category and item["category"].lower() != category.lower():
                continue
            if client and item.get("client", "").lower() != client.lower():
                continue
            if q_lower:
                text_to_search = f"{item['name']} {item.get('description','')} {' '.join(item.get('tags',[]))} {item.get('client','')}".lower()
                if q_lower not in text_to_search:
                    continue
            results.append(item)
        return results

    def get_script_by_id(self, script_id: str) -> Optional[Dict[str, Any]]:
        index = self._load_index()
        for item in index:
            if item["id"] == script_id:
                if os.path.exists(item["path"]):
                    with open(item["path"], "r", encoding="utf-8") as f:
                        item["content"] = f.read()
                return item
        return None
