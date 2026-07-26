import os
from pathlib import Path

class NoteScanner:
    def __init__(self, root_dir: str, exclude_dirs: list, exclude_files: list):
        self.root_dir = Path(root_dir).resolve()
        self.exclude_dirs = set(exclude_dirs)
        self.exclude_files = set(exclude_files)

    def scan_all_notes(self) -> list:
        notes = []
        if not self.root_dir.exists():
            return notes

        for root, dirs, files in os.walk(self.root_dir):
            # Exclude specified directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith(".")]

            for file in files:
                if file in self.exclude_files or file.startswith("."):
                    continue
                if file.endswith(".md") or file.endswith(".txt"):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(self.root_dir))
                    
                    # Determine top-level category
                    parts = Path(rel_path).parts
                    category = parts[0] if len(parts) > 1 else "General"
                    
                    notes.append({
                        "rel_path": rel_path,
                        "full_path": str(full_path),
                        "filename": file,
                        "category": category,
                        "mtime": os.path.getmtime(full_path),
                        "size": os.path.getsize(full_path)
                    })
        return notes
