import os
import tempfile
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

def is_supported(url: str) -> bool:
    sites = [
        "youtube.com", "youtu.be",
        "instagram.com",
        "facebook.com", "fb.watch"
    ]
    return any(site in url for site in sites)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if not is_supported(url):
        await update.message.reply_text(
            "❌ Send a valid YouTube / Instagram / Facebook link."
        )
        return

    try:
        await update.message.reply_text("⏳ Fetching video at MAX quality…")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "%(title).80s.%(ext)s")

            cmd = [
                "yt-dlp",
                "-f", "best[ext=mp4]/best",
                "-o", output_template,
                url
            ]

            subprocess.run(cmd, check=True)

            files = os.listdir(tmpdir)
            if not files:
                await update.message.reply_text("❌ Download failed.")
                return

            video_path = os.path.join(tmpdir, files[0])

            await update.message.reply_text("📤 Uploading to Telegram…")

            with open(video_path, "rb") as video:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=video,
                    caption="✅ Video downloaded (max quality)"
                )

    except subprocess.CalledProcessError:
        await update.message.reply_text(
            "❌ Failed to fetch video. It may be private or restricted."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error:\n{e}")

def main():
    app = ApplicationBuilder().token("8011292139:AAG9ilyi0guJOR-8nacGb8Su4eGNQzGzi28").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Social Media Downloader Bot running…")
    app.run_polling()

if __name__ == "__main__":
    main()
