# ⚡ Notes Revision CLI (`notes-revision`)

A powerful command-line interface (CLI) to automate daily revision digests of your Markdown notes directly to your email inbox with smart category balancing, spaced repetition, and VS Code deep links.

---

## 🚀 Installation

Install locally in editable mode:
```bash
cd /Users/aks/Desktop/notes/notes-revision-cli
python3 -m pip install -e .
```

After installation, the `notes-revision` executable will be available directly in your terminal.

---

## 🛠️ CLI Usage & Commands

### 1. Capture / Collect a Note (For You & AI Agents)
Capture any note on-the-fly while working. It creates the markdown file and automatically **pins** it to be included in your **very next revision digest** (tonight or tomorrow morning):

```bash
# Add note with title, content, and category
notes-revision add "Postgres Lock Contention" \
  --content "Explicit ACCESS EXCLUSIVE lock is acquired during ALTER TABLE operations." \
  --category mistakes-learning

# Quick single-command note snippet
notes-revision add "Always check EXPLAIN ANALYZE before deploying new indexes."

# Import an existing markdown file into your revision queue
notes-revision add --file /path/to/my_notes.md --category system-design
```

> 🤖 **AI Agent Usage (Cursor / Claude / Antigravity)**:
> Simply tell your AI agent:
> *"Use `notes-revision add` to save this key learning about distributed mutexes so I review it in tomorrow morning's digest."*

### 2. Initialize Configuration
```bash
notes-revision init --notes-dir /Users/aks/Desktop/notes
```
Creates configuration file at `~/.config/notes-revision/config.json`.

### 3. Generate Local HTML Email Preview
```bash
notes-revision preview
```

### 4. Send Email Digest
```bash
notes-revision send
```

### 5. View Statistics & Revision Queue
```bash
notes-revision stats
```

### 6. Manage Automated macOS Daily Schedule
```bash
# Register daily background schedule (default: 8:00 AM)
notes-revision schedule install --time 08:00

# Check schedule status
notes-revision schedule status

# Remove schedule
notes-revision schedule uninstall
```

---

## ⚙️ Configuration (`~/.config/notes-revision/config.json`)

```json
{
  "notes_dir": "/Users/aks/Desktop/notes",
  "smtp": {
    "server": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "username": "your_email@gmail.com",
    "password": "your_app_password"
  },
  "recipient_email": "your_email@gmail.com",
  "sender_name": "Notes Revision Bot 🧠",
  "notes_per_email": 2,
  "selection_strategy": "category_balanced"
}
```

### Selection Strategies Available
- `category_balanced` (Default): Picks least recently revised notes round-robin across top-level category folders (`system-design`, `lld`, `mistakes-learning`, `multigres`).
- `lru`: Least Recently Used across entire repository.
- `spaced_repetition`: Adapts revision intervals (1d, 3d, 7d, 14d, 30d, 60d).
- `random`: Random topic discovery.
