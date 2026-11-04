import os
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from config import TMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, BACKGROUND_IMAGE_URL, SHEIKH_NAME

FONT_PATH = "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/amiri/Amiri-Bold.ttf"

def download_audio(url, path):
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return path

def get_background():
    bg_path = os.path.join(TMP_DIR, "bg.jpg")
    if os.path.exists(bg_path):
        return bg_path
    try:
        r = requests.get(BACKGROUND_IMAGE_URL, timeout=30)
        r.raise_for_status()
        with open(bg_path, "wb") as f:
            f.write(r.content)
        return bg_path
    except Exception:
        # خلفية احتياطية سوداء
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (20, 30, 40))
        img.save(bg_path, "JPEG")
        return bg_path

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines

def make_thumbnail(title, out_path):
    """صورة 1280x720 فيها العنوان بشكل جميل"""
    bg_path = get_background()
    img = Image.open(bg_path).convert("RGB").resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img, "RGBA")

    # طبقة تعتيم
    draw.rectangle([0, 0, VIDEO_WIDTH, VIDEO_HEIGHT], fill=(0, 0, 0, 140))
    # شريط علوي
    draw.rectangle([0, 0, VIDEO_WIDTH, 90], fill=(0, 80, 60, 200))
    draw.rectangle([0, VIDEO_HEIGHT-70, VIDEO_WIDTH, VIDEO_HEIGHT], fill=(0, 80, 60, 200))

    try:
        font_sheikh = ImageFont.truetype(FONT_BOLD, 38)
        font_title = ImageFont.truetype(FONT_BOLD, 50)
    except Exception:
        font_sheikh = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # اسم الشيخ أعلى الصورة
    sheikh_reshaped = get_display(arabic_reshaper.reshape(SHEIKH_NAME))
    w = draw.textlength(sheikh_reshaped, font=font_sheikh)
    draw.text(((VIDEO_WIDTH - w) / 2, 22), sheikh_reshaped, font=font_sheikh, fill=(255, 255, 255))

    # العنوان في المنتصف
    reshaped = get_display(arabic_reshaper.reshape(title))
    lines = wrap_text(reshaped, font_title, VIDEO_WIDTH - 120, draw)
    total_h = len(lines) * 70
    y = (VIDEO_HEIGHT - total_h) / 2

    for line in lines:
        w = draw.textlength(line, font=font_title)
        # ظل
        draw.text(((VIDEO_WIDTH - w)/2 + 2, y + 2), line, font=font_title, fill=(0, 0, 0))
        draw.text(((VIDEO_WIDTH - w)/2, y), line, font=font_title, fill=(255, 255, 255))
        y += 70

    img.save(out_path, "JPEG", quality=90)
    return out_path

def make_video(title, audio_url, out_path):
    audio_path = os.path.join(TMP_DIR, "audio.mp3")
    thumb_path = os.path.join(TMP_DIR, "thumb.jpg")

    download_audio(audio_url, audio_path)
    make_thumbnail(title, thumb_path)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", thumb_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}",
        "-r", "25",
        "-preset", "veryfast",
        "-crf", "26",
        out_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise Exception(f"ffmpeg error: {result.stderr[-500:]}")

    try: os.remove(audio_path)
    except: pass
    try: os.remove(thumb_path)
    except: pass

    return out_path