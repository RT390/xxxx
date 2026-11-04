import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler
)
from config import BOT_TOKEN, ADMIN_ID
from database import (
    get_stats, get_channels, add_channel, remove_channel,
    set_setting, get_setting
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

application = None

def is_admin(uid):
    return uid == ADMIN_ID

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ غير مصرح لك")
        return
    txt = (
        "🤖 *بوت الفتاوى الصوتية*\n\n"
        "الأوامر:\n"
        "/status - حالة المعالجة\n"
        "/channels - القنوات\n"
        "/addchannel - إضافة قناة\n"
        "/pause - إيقاف\n"
        "/resume - استئناف\n"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    s = get_stats()
    state = get_setting("state", "stopped")
    txt = (
        f"📊 *الحالة:* {state}\n\n"
        f"📚 الإجمالي: {s['total']}\n"
        f"✅ أُرسلت: {s['sent']}\n"
        f"⏳ معلقة: {s['pending']}\n"
        f"❌ فشلت: {s['failed']}\n"
    )
    await update.message.reply_text(txt, parse_mode="Markdown")

async def channels_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    chans = get_channels()
    if not chans:
        await update.message.reply_text("لا توجد قنوات مضافة")
        return
    txt = "📢 *القنوات:*\n\n" + "\n".join(
        f"• `{c['chat_id']}` - {c['title'] or 'بدون اسم'}" for c in chans
    )
    await update.message.reply_text(txt, parse_mode="Markdown")

async def addchannel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("استخدم: `/addchannel @username` أو `/addchannel -100xxx`", parse_mode="Markdown")
        return
    add_channel(args[0])
    await update.message.reply_text(f"✅ أُضيفت: {args[0]}")

async def pause_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    set_setting("state", "paused")
    await update.message.reply_text("⏸️ تم الإيقاف")

async def resume_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    set_setting("state", "running")
    await update.message.reply_text("▶️ تم الاستئناف")

async def send_video_to_all(bot, video_path, caption):
    """ترسل الفيديو للأدمن + القنوات"""
    sent_to = []
    try:
        with open(video_path, "rb") as f:
            await bot.send_video(
                chat_id=ADMIN_ID, video=f,
                caption=caption, parse_mode="HTML",
                supports_streaming=True,
                read_timeout=300, write_timeout=300
            )
        sent_to.append("admin")
    except Exception as e:
        logger.error(f"admin send fail: {e}")

    for c in get_channels():
        try:
            with open(video_path, "rb") as f:
                await bot.send_video(
                    chat_id=c["chat_id"], video=f,
                    caption=caption, parse_mode="HTML",
                    supports_streaming=True,
                    read_timeout=300, write_timeout=300
                )
            sent_to.append(c["chat_id"])
        except Exception as e:
            logger.error(f"channel {c['chat_id']} fail: {e}")
    return sent_to

def build_application():
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("channels", channels_cmd))
    application.add_handler(CommandHandler("addchannel", addchannel_cmd))
    application.add_handler(CommandHandler("pause", pause_cmd))
    application.add_handler(CommandHandler("resume", resume_cmd))
    return application