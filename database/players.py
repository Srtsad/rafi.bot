import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("database/players.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    nickname TEXT,
    last_nick_change TEXT
)
""")
conn.commit()


def get_player(user_id: int):
    cursor.execute("SELECT nickname, last_nick_change FROM players WHERE user_id = ?", (user_id,))
    return cursor.fetchone()


def save_player(user_id: int, nickname: str):
    cursor.execute("""
    INSERT INTO players (user_id, nickname, last_nick_change)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        nickname = excluded.nickname,
        last_nick_change = excluded.last_nick_change
    """, (user_id, nickname, datetime.utcnow().isoformat()))
    conn.commit()
