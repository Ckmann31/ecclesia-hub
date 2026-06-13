import hashlib
from database import get_conn, ph, rows_to_dicts, row_to_dict

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login(username, password):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"SELECT * FROM users WHERE username={p} AND password={p}",
                (username.strip(), hash_pw(password)))
    row = row_to_dict(cur, cur.fetchone()); conn.close(); return row

def create_user(username, password, full_name, role, created_by_role):
    if created_by_role != "super_admin":
        return False, "Permission denied."
    conn = get_conn(); cur = conn.cursor(); p = ph()
    try:
        cur.execute(f"INSERT INTO users (username,password,full_name,role) VALUES ({p},{p},{p},{p})",
                    (username.strip(), hash_pw(password), full_name, role))
        conn.commit(); return True, "User created."
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_all_users():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id,username,full_name,role,created_at FROM users ORDER BY id")
    rows = rows_to_dicts(cur, cur.fetchall()); conn.close(); return rows

def delete_user(user_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"DELETE FROM users WHERE id={p}", (user_id,)); conn.commit(); conn.close()

def change_password(user_id, new_password):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"UPDATE users SET password={p} WHERE id={p}", (hash_pw(new_password), user_id))
    conn.commit(); conn.close()
