import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), "ct_catalogue.db")

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Variants table with additional fields
    cur.execute("""
        CREATE TABLE IF NOT EXISTS variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code_id TEXT,
            weight REAL,
            length REAL,
            price REAL,
            image_path TEXT
        )
    """)

    # Media table for reference media and own shoot details
    cur.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant_id INTEGER,
            media_type TEXT,
            media_path TEXT,
            description TEXT,
            FOREIGN KEY (variant_id) REFERENCES variants (id)
        )
    """)

    conn.commit()
    conn.close()

def insert_variant(name, code_id="", weight=0.0, length=0.0, price=0.0):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO variants (name, code_id, weight, length, price, image_path)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, code_id, weight, length, price, ""))

    conn.commit()
    variant_id = cur.lastrowid
    conn.close()

    return variant_id

def update_variant(variant_id, name, code_id, weight, length, price):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE variants
        SET name = ?, code_id = ?, weight = ?, length = ?, price = ?
        WHERE id = ?
    """, (name, code_id, weight, length, price, variant_id))

    conn.commit()
    conn.close()

def update_image_path(variant_id, image_path):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE variants
        SET image_path = ?
        WHERE id = ?
    """, (image_path, variant_id))

    conn.commit()
    conn.close()

def delete_variant(name):
    conn = get_connection()
    cur = conn.cursor()

    # Get variant ID first
    cur.execute("SELECT id FROM variants WHERE LOWER(name)=LOWER(?)", (name,))
    row = cur.fetchone()
    if row:
        variant_id = row[0]
        # Delete associated media first
        cur.execute("DELETE FROM media WHERE variant_id=?", (variant_id,))
        # Then delete the variant
        cur.execute("DELETE FROM variants WHERE id=?", (variant_id,))
        
        conn.commit()
        conn.close()
        return True
        
    conn.close()
    return False

def get_variants():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, code_id, weight, length, price, image_path FROM variants")
    rows = cur.fetchall()

    conn.close()
    return rows

def insert_media(variant_id, media_type, media_path, description=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO media (variant_id, media_type, media_path, description)
        VALUES (?, ?, ?, ?)
    """, (variant_id, media_type, media_path, description))

    conn.commit()
    media_id = cur.lastrowid
    conn.close()

    return media_id

def update_media_path(media_id, media_path):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("UPDATE media SET media_path = ? WHERE id = ?", (media_path, media_id))

    conn.commit()
    conn.close()

def get_media(variant_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, media_type, media_path, description FROM media WHERE variant_id = ?", (variant_id,))
    rows = cur.fetchall()

    conn.close()
    return rows

def search_media(query):
    conn = get_connection()
    cur = conn.cursor()

    query_like = f"%{query}%"
    cur.execute("""
        SELECT m.id, v.name, m.media_type, m.media_path, m.description 
        FROM media m
        JOIN variants v ON m.variant_id = v.id
        WHERE m.description LIKE ? OR m.media_path LIKE ? OR v.name LIKE ?
    """, (query_like, query_like, query_like))
    rows = cur.fetchall()

    conn.close()
    return rows

def get_media_by_id(media_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, media_type, media_path, description FROM media WHERE id = ?", (media_id,))
    row = cur.fetchone()

    conn.close()
    return row

def get_all_media():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.id, v.name, m.media_type, m.media_path, m.description 
        FROM media m
        JOIN variants v ON m.variant_id = v.id
    """)
    rows = cur.fetchall()

    conn.close()
    return rows

def delete_media(media_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM media WHERE id = ?", (media_id,))

    conn.commit()
    conn.close()