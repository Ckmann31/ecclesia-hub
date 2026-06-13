import os, hashlib

DATABASE_URL = os.environ.get("DATABASE_URL", "")

def is_pg():
    return bool(DATABASE_URL)

def ph():
    return "%s" if is_pg() else "?"

def get_conn():
    if is_pg():
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    import sqlite3
    path = os.path.join(os.path.dirname(__file__), "ecclesia.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def rows_to_dicts(cur, rows):
    if is_pg():
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]
    return [dict(r) for r in rows]

def row_to_dict(cur, row):
    if row is None:
        return None
    if is_pg():
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    return dict(row)

def scalar(row):
    if row is None:
        return 0
    return row[0] if isinstance(row, tuple) else list(row)[0]

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    if is_pg():
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL, full_name TEXT NOT NULL,
            role TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_DATE)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY, member_id TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL, phone TEXT, gender TEXT, age INTEGER,
            ministry TEXT, joined_date TEXT, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_DATE)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS visitors (
            id SERIAL PRIMARY KEY, full_name TEXT NOT NULL, phone TEXT,
            visit_date TEXT NOT NULL, invited_by TEXT DEFAULT 'Walk-in',
            follow_up_status TEXT DEFAULT 'Pending', assigned_leader TEXT,
            notes TEXT, created_at TEXT DEFAULT CURRENT_DATE)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY, member_id TEXT NOT NULL,
            sunday_date TEXT NOT NULL, present INTEGER DEFAULT 0,
            UNIQUE(member_id, sunday_date))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS follow_ups (
            id SERIAL PRIMARY KEY, member_id TEXT NOT NULL,
            full_name TEXT NOT NULL, phone TEXT, reason TEXT,
            action_taken TEXT, outcome TEXT, follow_up_date TEXT,
            flagged_auto INTEGER DEFAULT 0, resolved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_DATE)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS finance (
            id SERIAL PRIMARY KEY, trans_date TEXT NOT NULL,
            type TEXT NOT NULL, amount REAL NOT NULL,
            recorded_by TEXT NOT NULL, notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS volunteers (
            id SERIAL PRIMARY KEY, member_id TEXT NOT NULL UNIQUE,
            ministry TEXT NOT NULL, role TEXT, availability TEXT,
            created_at TEXT DEFAULT CURRENT_DATE)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS volunteer_attendance (
            id SERIAL PRIMARY KEY, member_id TEXT NOT NULL,
            service_date TEXT NOT NULL, present INTEGER DEFAULT 0,
            UNIQUE(member_id, service_date))""")
    else:
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL, full_name TEXT NOT NULL, role TEXT NOT NULL,
            created_at TEXT DEFAULT (DATE('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT, member_id TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL, phone TEXT, gender TEXT, age INTEGER,
            ministry TEXT, joined_date TEXT, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (DATE('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, phone TEXT,
            visit_date TEXT NOT NULL, invited_by TEXT DEFAULT 'Walk-in',
            follow_up_status TEXT DEFAULT 'Pending', assigned_leader TEXT,
            notes TEXT, created_at TEXT DEFAULT (DATE('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, member_id TEXT NOT NULL,
            sunday_date TEXT NOT NULL, present INTEGER DEFAULT 0,
            UNIQUE(member_id, sunday_date))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS follow_ups (
            id INTEGER PRIMARY KEY AUTOINCREMENT, member_id TEXT NOT NULL,
            full_name TEXT NOT NULL, phone TEXT, reason TEXT, action_taken TEXT,
            outcome TEXT, follow_up_date TEXT, flagged_auto INTEGER DEFAULT 0,
            resolved INTEGER DEFAULT 0, created_at TEXT DEFAULT (DATE('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trans_date TEXT NOT NULL,
            type TEXT NOT NULL, amount REAL NOT NULL, recorded_by TEXT NOT NULL,
            notes TEXT, created_at TEXT DEFAULT (DATETIME('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, member_id TEXT NOT NULL UNIQUE,
            ministry TEXT NOT NULL, role TEXT, availability TEXT,
            created_at TEXT DEFAULT (DATE('now')))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS volunteer_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT, member_id TEXT NOT NULL,
            service_date TEXT NOT NULL, present INTEGER DEFAULT 0,
            UNIQUE(member_id, service_date))""")

    p = ph()
    cur.execute(f"SELECT id FROM users WHERE username={p}", ('admin',))
    if not cur.fetchone():
        cur.execute(
            f"INSERT INTO users (username,password,full_name,role) VALUES ({p},{p},{p},{p})",
            ('admin', hash_pw('admin123'), 'System Administrator', 'super_admin'))
    conn.commit()
    conn.close()
    print("[DB] Initialised.")
