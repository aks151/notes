import datetime
import html
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class MarkdownRenderer:
    """Zero-dependency Markdown to styled HTML renderer optimized for email digest."""
    
    @staticmethod
    def render(text: str, file_path: str = "") -> str:
        lines = text.splitlines()
        html_output = []
        in_code_block = False
        code_lang = ""
        code_buffer = []
        in_list = False
        list_type = None

        def flush_list():
            nonlocal in_list, list_type
            if in_list:
                html_output.append("</ul>" if list_type == "ul" else "</ol>")
                in_list = False
                list_type = None

        for line in lines:
            # Code block handling
            if line.strip().startswith("```"):
                if in_code_block:
                    code_content = html.escape("\n".join(code_buffer))
                    html_output.append(
                        f'<pre style="background: #1e1e2e; color: #cdd6f4; padding: 14px 18px; '
                        f'border-radius: 8px; font-family: \'JetBrains Mono\', Menlo, Monaco, Consolas, monospace; '
                        f'font-size: 13px; line-height: 1.5; overflow-x: auto; border: 1px solid #313244; margin: 12px 0;">'
                        f'<code>{code_content}</code></pre>'
                    )
                    code_buffer = []
                    in_code_block = False
                else:
                    flush_list()
                    in_code_block = True
                    code_lang = line.strip().lstrip("`").strip()
                continue

            if in_code_block:
                code_buffer.append(line)
                continue

            # Headers
            header_match = re.match(r'^(#{1,6})\s+(.*)', line)
            if header_match:
                flush_list()
                level = len(header_match.group(1))
                h_text = MarkdownRenderer.inline_styles(header_match.group(2))
                sizes = {1: "22px", 2: "18px", 3: "16px", 4: "14px", 5: "13px", 6: "12px"}
                margins = {1: "20px 0 10px 0", 2: "16px 0 8px 0", 3: "12px 0 6px 0"}
                h_size = sizes.get(level, "14px")
                h_margin = margins.get(level, "10px 0 5px 0")
                border_css = "border-bottom: 1px solid #e2e8f0; padding-bottom: 6px;" if level <= 2 else ""
                html_output.append(
                    f'<h{level} style="font-size: {h_size}; color: #1e1e2e; margin: {h_margin}; '
                    f'font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; '
                    f'{border_css}">'
                    f'{h_text}</h{level}>'
                )
                continue

            # Blockquotes / Alerts
            if line.strip().startswith(">"):
                flush_list()
                quote_text = line.strip().lstrip(">").strip()
                alert_bg = "#f0fdf4"
                alert_border = "#22c55e"
                alert_title = "NOTE"
                
                alert_match = re.match(r'^\[\!(NOTE|IMPORTANT|WARNING|TIP|CAUTION)\]\s*(.*)', quote_text, re.IGNORECASE)
                if alert_match:
                    a_kind = alert_match.group(1).upper()
                    quote_text = alert_match.group(2)
                    if a_kind in ("WARNING", "CAUTION"):
                        alert_bg = "#fff1f2"
                        alert_border = "#f43f5e"
                        alert_title = "⚠️ WARNING"
                    elif a_kind == "IMPORTANT":
                        alert_bg = "#eff6ff"
                        alert_border = "#3b82f6"
                        alert_title = "📌 IMPORTANT"
                    elif a_kind == "TIP":
                        alert_bg = "#f0fdf4"
                        alert_border = "#10b981"
                        alert_title = "💡 TIP"
                    else:
                        alert_title = "ℹ️ NOTE"
                
                q_inline = MarkdownRenderer.inline_styles(quote_text)
                html_output.append(
                    f'<blockquote style="margin: 12px 0; padding: 10px 16px; background-color: {alert_bg}; '
                    f'border-left: 4px solid {alert_border}; border-radius: 4px; color: #334155; font-size: 14px;">'
                    f'<strong style="color: {alert_border}; display: block; margin-bottom: 4px; font-size: 12px; letter-spacing: 0.5px;">{alert_title}</strong>'
                    f'{q_inline}</blockquote>'
                )
                continue

            # Unordered lists (* or -)
            ul_match = re.match(r'^\s*[\*\-]\s+(.*)', line)
            if ul_match:
                if not in_list or list_type != "ul":
                    flush_list()
                    html_output.append('<ul style="margin: 8px 0; padding-left: 24px; color: #334155; line-height: 1.6;">')
                    in_list = True
                    list_type = "ul"
                li_text = MarkdownRenderer.inline_styles(ul_match.group(1))
                html_output.append(f'<li style="margin-bottom: 4px; font-size: 14px;">{li_text}</li>')
                continue

            # Ordered lists
            ol_match = re.match(r'^\s*\d+\.\s+(.*)', line)
            if ol_match:
                if not in_list or list_type != "ol":
                    flush_list()
                    html_output.append('<ol style="margin: 8px 0; padding-left: 24px; color: #334155; line-height: 1.6;">')
                    in_list = True
                    list_type = "ol"
                li_text = MarkdownRenderer.inline_styles(ol_match.group(1))
                html_output.append(f'<li style="margin-bottom: 4px; font-size: 14px;">{li_text}</li>')
                continue

            # Empty line
            if not line.strip():
                flush_list()
                html_output.append('<div style="height: 8px;"></div>')
                continue

            # Paragraph
            flush_list()
            p_text = MarkdownRenderer.inline_styles(line)
            html_output.append(
                f'<p style="margin: 6px 0; font-size: 14px; line-height: 1.65; color: #334155; '
                f'font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">{p_text}</p>'
            )

        flush_list()
        return "\n".join(html_output)

    @staticmethod
    def inline_styles(text: str) -> str:
        text = html.escape(text)
        
        # Inline code `code`
        text = re.sub(
            r'`([^`]+)`',
            r'<code style="background-color: #f1f5f9; color: #0f172a; padding: 2px 6px; '
            r'border-radius: 4px; font-family: monospace; font-size: 85%%; border: 1px solid #e2e8f0;">\1</code>',
            text
        )

        # Bold **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)

        # Italic *text*
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)

        # Wikilinks [[Note Name]]
        text = re.sub(
            r'\[\[([^\]]+)\]\]',
            r'<span style="background: #e0e7ff; color: #3730a3; padding: 2px 6px; border-radius: 4px; font-weight: 500;">🔗 \1</span>',
            text
        )

        # Markdown links [text](url) or [text] (url)
        text = re.sub(
            r'\[([^\]]+)\]\s*\(([^)]+)\)',
            r'<a href="\2" style="color: #2563eb; text-decoration: underline;">\1</a>',
            text
        )

        return text


class DigestEmailBuilder:
    @staticmethod
    def build_email(notes_data: list, config: dict, streak: int = 1, total_notes_count: int = 0) -> tuple:
        today_str = datetime.date.today().strftime("%B %d, %Y")
        subject = f"🧠 Daily Note Revision Digest — {today_str}"
        
        toc_items = []
        for idx, note in enumerate(notes_data, 1):
            category = note["category"]
            title = note["filename"].replace(".md", "").replace(".txt", "").replace("-", " ").title()
            toc_items.append(f'<li><a href="#note-{idx}" style="color: #2563eb; text-decoration: none; font-weight: 500;"><strong>[{category}]</strong> {title}</a></li>')
        toc_html = "".join(toc_items)

        note_cards = []
        plain_sections = []

        for idx, note in enumerate(notes_data, 1):
            category = note["category"]
            rel_path = note["rel_path"]
            full_path = note["full_path"]
            title = note["filename"].replace(".md", "").replace(".txt", "").replace("-", " ").title()
            
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                content = f"*(Error reading note file: {e})*"

            max_len = config.get("max_note_length_chars", 12000)
            if len(content) > max_len:
                content = content[:max_len] + "\n\n*(...Note content truncated for email length...)*"

            rendered_html = MarkdownRenderer.render(content, full_path)
            vscode_link = f"vscode://file{full_path}"

            card_html = f'''
            <div id="note-{idx}" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 28px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); overflow: hidden;">
                <div style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: #dbeafe; color: #1e40af; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; border-radius: 9999px; display: inline-block; margin-bottom: 6px;">
                            📁 {category}
                        </span>
                        <h2 style="margin: 0; font-size: 18px; color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            {title}
                        </h2>
                        <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                            <code>{rel_path}</code>
                        </div>
                    </div>
                    <div>
                        <a href="{vscode_link}" style="background: #2563eb; color: #ffffff; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600; display: inline-block; white-space: nowrap;">
                            ✏️ Open in VS Code
                        </a>
                    </div>
                </div>
                
                <div style="padding: 24px 24px; color: #334155;">
                    {rendered_html}
                </div>
                
                <div style="background: #f8fafc; border-top: 1px solid #f1f5f9; padding: 12px 20px; font-size: 12px; color: #64748b; text-align: right;">
                    <span>Times revised: <strong>{note.get("send_count", 0) + 1}</strong></span>
                </div>
            </div>
            '''
            note_cards.append(card_html)
            plain_sections.append(f"=== [{category}] {title} ===\nFile: {rel_path}\nVSCode: {vscode_link}\n\n{content}\n")

        all_cards_html = "".join(note_cards)

        full_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{subject}</title>
</head>
<body style="background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20px 10px; color: #334155;">
    <div style="max-width: 760px; margin: 0 auto;">
        
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; padding: 32px 28px; border-radius: 12px 12px 0 0; text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);">
            <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">⚡ Daily Revision Digest</h1>
            <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 14px;">{today_str} • Master your knowledge base every day</p>
            
            <div style="margin-top: 20px; display: inline-flex; gap: 16px; background: rgba(255,255,255,0.08); padding: 8px 18px; border-radius: 20px; font-size: 13px;">
                <span>🔥 Streak: <strong>{streak} day{"s" if streak != 1 else ""}</strong></span>
                <span style="color: #64748b;">|</span>
                <span>📚 Total Notes: <strong>{total_notes_count}</strong></span>
            </div>
        </div>
        
        <div style="background: #ffffff; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; padding: 16px 24px; font-size: 14px;">
            <strong style="color: #0f172a; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; display: block; margin-bottom: 8px;">Today's Selected Notes:</strong>
            <ul style="margin: 0; padding-left: 20px; line-height: 1.6;">
                {toc_html}
            </ul>
        </div>
        
        <div style="height: 24px;"></div>
        
        {all_cards_html}

        <div style="text-align: center; padding: 20px 0; color: #94a3b8; font-size: 12px;">
            <p style="margin: 0;">Automated by <strong>Notes Revision CLI</strong> 🤖</p>
            <p style="margin: 4px 0 0 0;">Keep reviewing, keep building!</p>
        </div>

    </div>
</body>
</html>
'''
        plain_text = f"DAILY REVISION DIGEST ({today_str})\n" + "="*40 + "\n\n" + "\n\n".join(plain_sections)
        return subject, full_html, plain_text


class AppleMailSender:
    @staticmethod
    def send_or_draft(subject: str, html_body: str, plain_text: str, recipient: str, auto_send: bool = True):
        import subprocess
        safe_subject = subject.replace('"', '\\"')
        safe_text = plain_text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        script = f'''
        tell application "Mail"
            set msg to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_text}", visible:true}}
            tell msg
                make new to recipient at end of to recipients with properties {{address:"{recipient}"}}
            end tell
            activate
            send msg
        end tell
        '''
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"🚀 Email automatically dispatched via macOS Apple Mail to {recipient}! (Zero Password Required)")
        else:
            raise RuntimeError(f"AppleScript error: {res.stderr}")


class EmailSender:
    @staticmethod
    def send_email(subject: str, html_body: str, plain_text: str, config: dict, use_mailapp: bool = False):
        recipient = config.get("recipient_email", "kumar.ayush151@gmail.com")
        
        if use_mailapp:
            AppleMailSender.send_or_draft(subject, html_body, plain_text, recipient, auto_send=True)
            return

        smtp_cfg = config.get("smtp", {})
        server_host = smtp_cfg.get("server", "smtp.gmail.com")
        server_port = smtp_cfg.get("port", 587)
        use_tls = smtp_cfg.get("use_tls", True)
        username = smtp_cfg.get("username")
        password = smtp_cfg.get("password")
        sender_name = config.get("sender_name", "Notes Bot")

        if not username or "YOUR_EMAIL" in username or not password or "YOUR_APP_PASSWORD" in password:
            print("⚠️ SMTP credentials not configured. Sending directly via macOS Apple Mail (Zero Password Required)...")
            AppleMailSender.send_or_draft(subject, html_body, plain_text, recipient, auto_send=True)
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{username}>"
        msg["To"] = recipient

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        print(f"📧 Connecting to SMTP server {server_host}:{server_port}...")
        with smtplib.SMTP(server_host, server_port) as server:
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
            server.login(username, password)
            server.sendmail(username, [recipient], msg.as_string())
        print(f"✅ Email successfully sent to {recipient}!")
