import datetime
import json
from pathlib import Path

DEFAULT_STATE_PATH = Path.home() / ".config" / "notes-revision" / "state.json"

class RevisionScheduler:
    def __init__(self, state_file: Path = None):
        self.state_file = state_file if state_file else DEFAULT_STATE_PATH
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state = self.load_state()

    def load_state(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Warning: Could not read state file ({e}). Starting fresh.")
        return {"notes": {}, "history": [], "streak": 0, "last_run": None}

    def save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def update_streak(self):
        now = datetime.datetime.now()
        last_run_str = self.state.get("last_run")
        if last_run_str:
            last_run = datetime.datetime.fromisoformat(last_run_str)
            delta_days = (now.date() - last_run.date()).days
            if delta_days == 1:
                self.state["streak"] = self.state.get("streak", 0) + 1
            elif delta_days > 1:
                self.state["streak"] = 1
        else:
            self.state["streak"] = 1
        self.state["last_run"] = now.isoformat()

    def pin_note(self, rel_path: str):
        notes_state = self.state.setdefault("notes", {})
        entry = notes_state.setdefault(rel_path, {})
        entry["pinned_next"] = True
        self.save_state()

    def select_notes(self, all_notes: list, count: int = 2, strategy: str = "category_balanced") -> list:
        notes_state = self.state.setdefault("notes", {})
        now_ts = datetime.datetime.now().timestamp()

        # Separate pinned notes (must be included in the next email digest)
        pinned_notes = []
        regular_notes = []

        for note in all_notes:
            rel_path = note["rel_path"]
            n_data = notes_state.get(rel_path, {})
            note["last_sent_ts"] = n_data.get("last_sent_ts", 0)
            note["send_count"] = n_data.get("send_count", 0)
            note["pinned_next"] = n_data.get("pinned_next", False)

            if note["pinned_next"]:
                pinned_notes.append(note)
            else:
                regular_notes.append(note)

        selected = list(pinned_notes)

        # If pinned notes exceed requested count, return top count pinned notes
        if len(selected) >= count:
            return selected[:count]

        needed_count = count - len(selected)

        if strategy == "category_balanced":
            categories = {}
            for note in regular_notes:
                categories.setdefault(note["category"], []).append(note)

            sorted_categories = sorted(categories.keys())
            cat_idx = 0
            while len(selected) < count and sorted_categories:
                cat_name = sorted_categories[cat_idx % len(sorted_categories)]
                cat_notes = categories[cat_name]
                cat_notes.sort(key=lambda x: (x["last_sent_ts"], x["send_count"], -x["mtime"]))
                
                chosen = cat_notes.pop(0)
                selected.append(chosen)
                
                if not cat_notes:
                    sorted_categories.remove(cat_name)
                    categories.pop(cat_name)
                
                if sorted_categories:
                    cat_idx = (cat_idx + 1) % len(sorted_categories)

            return selected

        elif strategy == "lru":
            sorted_notes = sorted(regular_notes, key=lambda x: (x["last_sent_ts"], x["send_count"], -x["mtime"]))
            selected.extend(sorted_notes[:needed_count])
            return selected

        elif strategy == "random":
            import random
            selected.extend(random.sample(regular_notes, min(needed_count, len(regular_notes))))
            return selected

        elif strategy == "spaced_repetition":
            INTERVALS = [1, 3, 7, 14, 30, 60]
            
            def due_score(note):
                last_ts = note["last_sent_ts"]
                cnt = note["send_count"]
                if last_ts == 0:
                    return 999999
                
                interval_days = INTERVALS[min(cnt, len(INTERVALS) - 1)]
                days_since = (now_ts - last_ts) / 86400.0
                return days_since / interval_days

            sorted_notes = sorted(regular_notes, key=due_score, reverse=True)
            selected.extend(sorted_notes[:needed_count])
            return selected

        else:
            sorted_notes = sorted(regular_notes, key=lambda x: (x["last_sent_ts"], x["send_count"]))
            selected.extend(sorted_notes[:needed_count])
            return selected

    def record_sent(self, selected_notes: list):
        now_iso = datetime.datetime.now().isoformat()
        now_ts = datetime.datetime.now().timestamp()
        
        self.update_streak()
        
        for note in selected_notes:
            rel = note["rel_path"]
            entry = self.state["notes"].setdefault(rel, {})
            entry.setdefault("first_sent", now_iso)
            entry.setdefault("history", [])
            entry["last_sent"] = now_iso
            entry["last_sent_ts"] = now_ts
            entry["send_count"] = entry.get("send_count", 0) + 1
            entry["pinned_next"] = False  # Clear pin once sent!
            entry["history"].append(now_iso)

        self.state.setdefault("history", []).append({
            "timestamp": now_iso,
            "notes": [n["rel_path"] for n in selected_notes]
        })
        self.save_state()
