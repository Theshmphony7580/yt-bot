import os
import tempfile
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN")

SUPPORTED = (
    "youtube.com", "youtu.be",
    "instagram.com",
    "facebook.com", "fb.watch"
)

# -------- Telegram Bot --------

def is_supported(url: str) -> bool:
    return any(s in url for s in SUPPORTED)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if not is_supported(url):
        await update.message.reply_text("❌ Send a valid video link.")
        return

    try:
        await update.message.reply_text("⏳ Downloading…")

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "%(title).50s.%(ext)s")

            cmd = [
                "yt-dlp",
                "-f", "best[ext=mp4]/best",
                "--no-playlist",
                "--quiet",
                "-o", out,
                url
            ]

            subprocess.run(cmd, check=True)

            file = os.listdir(tmp)[0]
            path = os.path.join(tmp, file)

            await update.message.reply_text("📤 Uploading…")
            with open(path, "rb") as v:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=v,
                    supports_streaming=True
                )

    except Exception as e:
        await update.message.reply_text(f"❌ Error")

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Telegram bot running")
    app.run_polling()

# -------- Minimal Web Server (Render Keep-Alive) --------

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

# -------- Start Both --------

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_web()
