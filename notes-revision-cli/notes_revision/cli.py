import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

from .config import ConfigManager
from .scanner import NoteScanner
from .scheduler import RevisionScheduler
from .renderer import DigestEmailBuilder, EmailSender
from .launchd import LaunchdManager

def main():
    parser = argparse.ArgumentParser(
        prog="notes-revision",
        description="⚡ Daily Notes Revision CLI — Spaced Repetition, Note Collection & Daily Email Digest",
        epilog="""
Examples:
  # 1. Capture a note on-the-fly (auto-pinned for your next digest):
  notes-revision add "Postgres Lock Contention" --content "Details..." --category mistakes-learning

  # 2. Generate local HTML email preview (dry run):
  notes-revision preview

  # 3. Send daily revision email digest to inbox:
  notes-revision send

  # 4. View statistics, streak, category counts & revision queue:
  notes-revision stats

  # 5. Install daily background schedule on macOS (runs at 8:00 AM daily):
  notes-revision schedule install --time 08:00
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", type=str, default=None, help="Custom path to config.json")
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: add / collect / capture
    add_parser = subparsers.add_parser(
        "add",
        aliases=["collect", "capture"],
        help="Collect/capture a note to include in your upcoming revision email",
        epilog="""
Examples:
  # Capture note with title and body:
  notes-revision add "Distributed Locks" -c "Use TTL to avoid deadlocks..." -cat system-design

  # Quick single-line snippet:
  notes-revision add "Always run EXPLAIN ANALYZE before deploying new indexes"

  # Import an existing markdown file:
  notes-revision add --file /path/to/note.md --category lld
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    add_parser.add_argument("title", type=str, nargs="?", default=None, help="Note title or quick text snippet")
    add_parser.add_argument("--content", "-c", type=str, default="", help="Markdown body content for the note")
    add_parser.add_argument("--category", "-cat", type=str, default="quick-notes", help="Category folder (default: quick-notes)")
    add_parser.add_argument("--file", "-f", type=str, default=None, help="Path to existing markdown file to import")
    add_parser.add_argument("--pin", action="store_true", default=True, help="Pin to force inclusion in your very next revision digest (default: True)")
    add_parser.add_argument("--no-pin", dest="pin", action="store_false", help="Do not pin to next digest (use normal LRU scheduling)")

    # Subcommand: init
    init_parser = subparsers.add_parser("init", help="Initialize CLI configuration")
    init_parser.add_argument("--notes-dir", type=str, default=None, help="Path to your markdown notes directory")

    # Subcommand: preview
    preview_parser = subparsers.add_parser("preview", help="Generate local HTML email preview (dry run)")
    preview_parser.add_argument("--out", type=str, default="preview_email.html", help="Output HTML file path")

    # Subcommand: send
    send_parser = subparsers.add_parser("send", help="Run selection engine and send daily email digest")
    send_parser.add_argument("--mailapp", action="store_true", help="Use macOS Apple Mail app directly (Zero Password required)")

    # Subcommand: open
    open_parser = subparsers.add_parser("open", help="Open today's daily revision digest directly in your browser")

    # Subcommand: stats
    stats_parser = subparsers.add_parser("stats", help="Display note stats, category counts, streak, and queue")

    # Subcommand: schedule
    schedule_parser = subparsers.add_parser(
        "schedule",
        help="Manage macOS daily background schedule",
        epilog="""
Examples:
  # Install daily schedule at 8:00 AM:
  notes-revision schedule install --time 08:00

  # Check active schedule status:
  notes-revision schedule status

  # Remove daily background schedule:
  notes-revision schedule uninstall
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    schedule_parser.add_argument("action", choices=["install", "status", "uninstall"], help="Action to perform")
    schedule_parser.add_argument("--time", type=str, default="08:00", help="Daily time in HH:MM format (default: 08:00)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 1. COMMAND: INIT (Does not require scanning existing notes)
    if args.command == "init":
        notes_dir = args.notes_dir if args.notes_dir else "/Users/aks/Desktop/notes"
        cfg_path = ConfigManager.init_config(args.config, notes_dir)
        print(f"🎉 Initialized notes-revision configuration at: {cfg_path}")
        print(f"📁 Target Notes Directory: {notes_dir}")
        print(f"💡 Please edit {cfg_path} with your email & SMTP settings.")
        return

    # Load Config
    config, cfg_path = ConfigManager.load_config(args.config)
    notes_dir = Path(config.get("notes_dir", "/Users/aks/Desktop/notes")).resolve()

    state_file = Path.home() / ".config" / "notes-revision" / "state.json"
    scheduler = RevisionScheduler(state_file)

    # 2. COMMAND: ADD / COLLECT / CAPTURE
    if args.command in ("add", "collect", "capture"):
        if not args.title and not args.file:
            print("❌ Please provide a note title or --file path.")
            print("Usage: notes-revision add \"Postgres Lock Contention\" --content \"Lock details...\" --category mistakes-learning")
            sys.exit(1)

        target_file_path = None
        rel_path = None
        category = args.category.strip()

        if args.file:
            source_file = Path(args.file).resolve()
            if not source_file.exists():
                print(f"❌ Source file not found: {source_file}")
                sys.exit(1)
            
            # If already inside notes_dir
            try:
                rel_path = str(source_file.relative_to(notes_dir))
                target_file_path = source_file
            except ValueError:
                # Copy to notes_dir/<category>/
                dest_dir = notes_dir / category
                dest_dir.mkdir(parents=True, exist_ok=True)
                target_file_path = dest_dir / source_file.name
                shutil.copy(source_file, target_file_path)
                rel_path = str(target_file_path.relative_to(notes_dir))
        else:
            raw_title = args.title.strip()
            content_text = args.content.strip()
            if not content_text and len(raw_title) > 60:
                content_text = raw_title
                title_line = raw_title[:50].strip() + "..."
            else:
                title_line = raw_title

            slug = re.sub(r'[^a-zA-Z0-9_\-]+', '-', title_line.lower()).strip('-')
            if not slug:
                slug = f"note-{int(datetime.datetime.now().timestamp())}"
            
            filename = f"{slug}.md"
            dest_dir = notes_dir / category
            dest_dir.mkdir(parents=True, exist_ok=True)
            target_file_path = dest_dir / filename

            file_body = f"# {title_line}\n\n"
            if content_text:
                file_body += f"{content_text}\n"
            else:
                file_body += f"*(Captured on {datetime.date.today().strftime('%Y-%m-%d')})*\n"

            with open(target_file_path, "w", encoding="utf-8") as f:
                f.write(file_body)

            rel_path = str(target_file_path.relative_to(notes_dir))

        if args.pin:
            scheduler.pin_note(rel_path)

        print("\n" + "📝"*25)
        print("✅ NOTE CAPTURED SUCCESSFULLY!")
        print("📝"*25)
        print(f"• File Location: {target_file_path}")
        print(f"• Category: {category}")
        print(f"• Priority: {'📌 Pinned for your VERY NEXT revision digest (tonight/tomorrow morning)!' if args.pin else 'Standard scheduling queue'}")
        print("📝"*25 + "\n")
        return

    # Scan existing notes for remaining commands
    scanner = NoteScanner(notes_dir, config.get("exclude_dirs", []), config.get("exclude_files", []))
    all_notes = scanner.scan_all_notes()

    if not all_notes and args.command in ("preview", "send", "stats"):
        print(f"❌ No markdown or text notes found in directory: {notes_dir}")
        print(f"💡 Run `notes-revision init --notes-dir /path/to/notes` to configure directory.")
        sys.exit(1)

    # 3. COMMAND: PREVIEW
    if args.command == "preview":
        notes_per_email = config.get("notes_per_email", 2)
        strategy = config.get("selection_strategy", "category_balanced")
        selected_notes = scheduler.select_notes(all_notes, count=notes_per_email, strategy=strategy)

        streak = scheduler.state.get("streak", 0) + 1
        subject, html_body, plain_text = DigestEmailBuilder.build_email(selected_notes, config, streak=streak, total_notes_count=len(all_notes))

        out_path = Path(args.out).resolve()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_body)

        print("\n" + "✨"*25)
        print("🧪 TEST PREVIEW GENERATED")
        print("✨"*25)
        print(f"• Subject: {subject}")
        print(f"• Selected Notes ({len(selected_notes)}):")
        for n in selected_notes:
            pinned_str = " 📌 [PINNED]" if n.get("pinned_next") else ""
            print(f"   - [{n['category']}] {n['rel_path']}{pinned_str}")
        print(f"• Saved HTML Email Preview to: {out_path}")
        print(f"💡 Double-click or open '{out_path}' in your browser to inspect the rendering!")
        print("✨"*25 + "\n")

    # 4. COMMAND: OPEN (Browser Dashboard)
    elif args.command == "open":
        notes_per_email = config.get("notes_per_email", 2)
        strategy = config.get("selection_strategy", "category_balanced")
        selected_notes = scheduler.select_notes(all_notes, count=notes_per_email, strategy=strategy)

        streak = scheduler.state.get("streak", 0) + 1
        subject, html_body, plain_text = DigestEmailBuilder.build_email(selected_notes, config, streak=streak, total_notes_count=len(all_notes))

        out_path = notes_dir / "preview_email.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_body)

        import webbrowser
        webbrowser.open(f"file://{out_path}")
        print(f"🚀 Opening Daily Revision Digest in your browser ({out_path})...")
        return

    # 5. COMMAND: SEND
    elif args.command == "send":
        notes_per_email = config.get("notes_per_email", 2)
        strategy = config.get("selection_strategy", "category_balanced")
        selected_notes = scheduler.select_notes(all_notes, count=notes_per_email, strategy=strategy)

        streak = scheduler.state.get("streak", 0) + 1
        subject, html_body, plain_text = DigestEmailBuilder.build_email(selected_notes, config, streak=streak, total_notes_count=len(all_notes))

        try:
            EmailSender.send_email(subject, html_body, plain_text, config, use_mailapp=args.mailapp)
            scheduler.record_sent(selected_notes)
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            sys.exit(1)

    # 5. COMMAND: STATS
    elif args.command == "stats":
        print("\n" + "="*52)
        print(f"📊 NOTES REVISION CLI STATISTICS")
        print("="*52)
        print(f"• Config File: {cfg_path}")
        print(f"• Notes Directory: {notes_dir}")
        print(f"• Total Notes Found: {len(all_notes)}")
        print(f"• Current Streak: {scheduler.state.get('streak', 0)} day(s)")
        print(f"• Last Run Date: {scheduler.state.get('last_run', 'Never')}")
        
        cat_counts = {}
        for n in all_notes:
            cat_counts[n["category"]] = cat_counts.get(n["category"], 0) + 1
        print("\n📁 Notes Breakdown by Category:")
        for cat, cnt in sorted(cat_counts.items()):
            print(f"   - {cat}: {cnt} note(s)")
            
        print("\n⏳ Next Up in Revision Queue (Least Recently Revised / Pinned):")
        rev_notes = scheduler.select_notes(all_notes, count=5, strategy="lru")
        for idx, n in enumerate(rev_notes, 1):
            last_s = n.get("last_sent_ts")
            last_str = datetime.datetime.fromtimestamp(last_s).strftime("%Y-%m-%d") if last_s else "Never"
            pinned_str = " 📌 [PINNED FOR NEXT DIGEST]" if n.get("pinned_next") else ""
            print(f"   {idx}. [{n['category']}] {n['rel_path']} (Revised: {n.get('send_count', 0)} times, Last: {last_str}){pinned_str}")
        print("="*52 + "\n")

    # 6. COMMAND: SCHEDULE
    elif args.command == "schedule":
        if args.action == "status":
            LaunchdManager.status()
        elif args.action == "uninstall":
            LaunchdManager.uninstall()
        elif args.action == "install":
            try:
                time_parts = args.time.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1])
            except Exception:
                print("❌ Invalid time format. Please use HH:MM format (e.g., 08:00).")
                sys.exit(1)

            python_bin = sys.executable
            cli_bin = shutil.which("notes-revision")
            if not cli_bin:
                cli_bin = f"{python_bin} -m notes_revision.cli"

            LaunchdManager.install(python_bin, cli_bin, hour=hour, minute=minute)

if __name__ == "__main__":
    main()
