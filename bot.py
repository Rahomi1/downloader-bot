import telebot
import yt_dlp
import os
import time
import threading
from flask import Flask

# سيرفر مصغر لإبقاء استضافة Hugging Face شغالة 24 ساعة
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web():
    app.run(host="0.0.0.0", port=7860)

threading.Thread(target=run_web, daemon=True).start()

# إعدادات بوت التيليجرام
BOT_TOKEN = "8851741499:AAGhTH0xiSj5wcyTdF2IOo79vebQ-jqZE9E"
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "أهلاً بك في بوت التحميل الشامل بالجودة الأصلية (يعمل 24 ساعة سحابياً)! 🚀🎬\n\n"
        "أرسل لي أي رابط من:\n"
        "• تيك توك (بدون علامة مائية وبالجودة الخام)\n"
        "• يوتيوب (فيديو وشورتس بأعلى دقة مع دمج الصوت)\n"
        "• فيسبوك & انستغرام & تويتر\n\n"
        "فقط أرسل الرابط وسأتكفل بالباقي."
    )

@bot.message_handler(func=lambda message: message.text and ('http://' in message.text or 'https://' in message.text))
def download_video(message):
    words = message.text.split()
    url = next((w for w in words if w.startswith(('http://', 'https://'))), None)
    
    if not url:
        bot.reply_to(message, "⚠️ لم أتمكن من العثور على رابط صحيح في رسالتك.")
        return

    wait_msg = bot.reply_to(message, "⏳ جاري فحص الرابط وسحب أعلى جودة أصلية بدون علامة مائية...")
    
    unique_id = f"{message.chat.id}_{int(time.time())}"
    output_template = f"/tmp/video_{unique_id}.%(ext)s"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
    }

    downloaded_file = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'فيديو محمل')
            downloaded_file = ydl.prepare_filename(info)
            if not os.path.exists(downloaded_file):
                base_name = os.path.splitext(downloaded_file)[0]
                if os.path.exists(base_name + ".mp4"):
                    downloaded_file = base_name + ".mp4"

        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        if file_size_mb > 49.5:
            bot.edit_message_text("⚠️ حجم الفيديو يتجاوز 50MB، جاري جلب جودة متوافقة مع تيليجرام...", message.chat.id, wait_msg.message_id)
            os.remove(downloaded_file)
            ydl_opts['format'] = 'best[filesize<49M]/best[height<=720]'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                if not os.path.exists(downloaded_file):
                    downloaded_file = os.path.splitext(downloaded_file)[0] + ".mp4"

        bot.edit_message_text("📤 تم التحميل! جاري الرفع إلى تيليجرام...", message.chat.id, wait_msg.message_id)

        with open(downloaded_file, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=f"✅ {title[:100]}\n✨ الجودة الأصلية - بدون علامة مائية",
                supports_streaming=True,
                timeout=120
            )

        bot.delete_message(message.chat.id, wait_msg.message_id)

    except Exception as e:
        try:
            bot.edit_message_text(f"❌ تعذر تحميل هذا الرابط:\n{str(e)[:200]}", message.chat.id, wait_msg.message_id)
        except:
            pass
    finally:
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)

bot.infinity_polling(timeout=60, long_polling_timeout=60)
