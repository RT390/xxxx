import json
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL

def get_conn():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    return psycopg2.connect(
        host="localhost", database="fatwa",
        user="postgres", password="postgres"
    )

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fatwas (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            audio_url TEXT NOT NULL UNIQUE,
            status VARCHAR(20) DEFAULT 'pending',
            error TEXT,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            chat_id VARCHAR(64) UNIQUE NOT NULL,
            title VARCHAR(255),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key VARCHAR(64) PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# ============ الفتاوى ============
def load_fatwas_from_json(path="fatwas.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    for item in data:
        try:
            cur.execute(
                "INSERT INTO fatwas (title, audio_url) VALUES (%s, %s) ON CONFLICT (audio_url) DO NOTHING",
                (item["name"], item["url"])
            )
            if cur.rowcount:
                inserted += 1
        except Exception as e:
            print("skip:", e)
    conn.commit()
    cur.close()
    conn.close()
    return inserted

def get_pending_fatwa():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM fatwas WHERE status='pending' ORDER BY id LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def mark_fatwa(fatwa_id, status, error=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE fatwas SET status=%s, error=%s, sent_at=NOW() WHERE id=%s",
        (status, error, fatwa_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*) FROM fatwas GROUP BY status
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    stats = {"pending": 0, "sent": 0, "failed": 0, "total": 0}
    for status, count in rows:
        stats[status] = count
        stats["total"] += count
    return stats

def get_fatwas(limit=50, status=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if status:
        cur.execute("SELECT * FROM fatwas WHERE status=%s ORDER BY id DESC LIMIT %s", (status, limit))
    else:
        cur.execute("SELECT * FROM fatwas ORDER BY id DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ============ القنوات ============
def add_channel(chat_id, title=""):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO channels (chat_id, title) VALUES (%s, %s) ON CONFLICT (chat_id) DO UPDATE SET title=EXCLUDED.title",
            (str(chat_id), title)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
    cur.close()
    conn.close()

def remove_channel(chat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM channels WHERE chat_id=%s", (str(chat_id),))
    conn.commit()
    cur.close()
    conn.close()

def get_channels():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM channels ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# ============ الإعدادات ============
def set_setting(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value
    """, (key, str(value)))
    conn.commit()
    cur.close()
    conn.close()

def get_setting(key, default=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=%s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else default