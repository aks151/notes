import os
from pathlib import Path

class LaunchdManager:
    PLIST_LABEL = "com.user.notes.dailyrevision"

    @staticmethod
    def get_plist_path() -> Path:
        return Path.home() / "Library" / "LaunchAgents" / f"{LaunchdManager.PLIST_LABEL}.plist"

    @staticmethod
    def install(python_bin: str, cli_executable: str, hour: int = 8, minute: int = 0):
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LaunchdManager.PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{cli_executable}</string>
        <string>send</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{hour}</integer>
        <key>Minute</key>
        <integer>{minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{Path.home()}/Library/Logs/notes_revision.log</string>
    <key>StandardErrorPath</key>
    <string>{Path.home()}/Library/Logs/notes_revision_error.log</string>
</dict>
</plist>
'''
        plist_path = LaunchdManager.get_plist_path()
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        with open(plist_path, "w", encoding="utf-8") as f:
            f.write(plist_content)

        print(f"📄 Created launchd plist at: {plist_path}")
        os.system(f"launchctl unload '{plist_path}' 2>/dev/null")
        res = os.system(f"launchctl load '{plist_path}'")
        if res == 0:
            print(f"🚀 Successfully registered daily schedule to run at {hour:02d}:{minute:02d} AM/PM daily!")
            print(f"📋 Logs location: ~/Library/Logs/notes_revision.log")
        else:
            print(f"⚠️ Warning: launchctl load returned code {res}.")

    @staticmethod
    def status():
        res = os.popen(f"launchctl list | grep '{LaunchdManager.PLIST_LABEL}'").read()
        if res:
            print(f"✅ Schedule active: {res.strip()}")
        else:
            print("❌ Schedule currently not loaded.")

    @staticmethod
    def uninstall():
        plist_path = LaunchdManager.get_plist_path()
        if plist_path.exists():
            os.system(f"launchctl unload '{plist_path}' 2>/dev/null")
            plist_path.unlink()
            print("🗑️ Schedule removed.")
        else:
            print("ℹ️ No active schedule found.")
