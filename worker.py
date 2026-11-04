import os
import time
import asyncio
import threading
import logging
from datetime import datetime

from config import BOT_TOKEN, TMP_DIR, SEND_DELAY, SHEIKH_NAME
from database import (
    get_pending_fatwa, mark_fatwa, get_setting, set_setting
)
from video_maker import make_video
from telegram import Bot

logger = logging.getLogger(__name__)

class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.stop_flag = False
        self.bot = Bot(token=BOT_TOKEN)

    def run(self):
        logger.info("🚀 Worker started")
        while not self.stop_flag:
            try:
                state = get_setting("state", "stopped")
                if state != "running":
                    time.sleep(3)
                    continue

                fatwa = get_pending_fatwa()
                if not fatwa:
                    logger.info("✅ No pending fatwas")
                    set_setting("state", "done")
                    time.sleep(5)
                    continue

                self.process(fatwa)
                time.sleep(SEND_DELAY)

            except Exception as e:
                logger.error(f"worker err: {e}")
                time.sleep(5)

    def process(self, fatwa):
        fid = fatwa["id"]
        title = fatwa["title"]
        url = fatwa["audio_url"]
        video_path = os.path.join(TMP_DIR, f"fatwa_{fid}.mp4")

        logger.info(f"▶️ [{fid}] {title[:60]}")

        try:
            # 1. صنع الفيديو
            make_video(title, url, video_path)

            # 2. الإرسال
            caption = f"🎙️ <b>{title}</b>\n\n📖 {SHEIKH_NAME}"
            asyncio.run(self._send_all(video_path, caption))

            # 3. حذف
            try: os.remove(video_path)
            except: pass

            mark_fatwa(fid, "sent")
            logger.info(f"✅ [{fid}] sent")

        except Exception as e:
            logger.error(f"❌ [{fid}] {e}")
            mark_fatwa(fid, "failed", str(e)[:400])
            try: os.remove(video_path)
            except: pass

    async def _send_all(self, video_path, caption):
        from database import get_channels, ADMIN_ID

        # للأدمن
        try:
            with open(video_path, "rb") as f:
                await self.bot.send_video(
                    chat_id=ADMIN_ID, video=f, caption=caption,
                    parse_mode="HTML", supports_streaming=True,
                    read_timeout=300, write_timeout=300
                )
        except Exception as e:
            logger.error(f"admin send: {e}")

        # للقنوات
        for c in get_channels():
            try:
                with open(video_path, "rb") as f:
                    await self.bot.send_video(
                        chat_id=c["chat_id"], video=f, caption=caption,
                        parse_mode="HTML", supports_streaming=True,
                        read_timeout=300, write_timeout=300
                    )
            except Exception as e:
                logger.error(f"channel {c['chat_id']}: {e}")

worker_instance = None

def start_worker():
    global worker_instance
    if worker_instance is None or not worker_instance.is_alive():
        worker_instance = Worker()
        worker_instance.start()