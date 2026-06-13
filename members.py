import datetime
from database import get_conn, ph, rows_to_dicts, row_to_dict, scalar

MINISTRIES = ["Choir","Ushering","Media","Youth","Prayer",
               "Children's Church","Security","Evangelism","Administration","Other"]

def _new_id():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM members")
    n = scalar(cur.fetchone()) + 1
    conn.close()
    return f"CM{datetime.date.today().year}{n:04d}"

def add_member(full_name, phone, gender, age, ministry, joined_date):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    mid = _new_id()
    try:
        cur.execute(f"INSERT INTO members (member_id,full_name,phone,gender,age,ministry,joined_date) VALUES ({p},{p},{p},{p},{p},{p},{p})",
                    (mid, full_name.strip(), phone, gender, age, ministry, joined_date))
        conn.commit(); return True, mid
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_all_members(search="", ministry_filter="All", active_only=True):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    q = "SELECT * FROM members WHERE 1=1"; params = []
    if active_only: q += " AND is_active=1"
    if search:
        q += f" AND (full_name LIKE {p} OR member_id LIKE {p} OR phone LIKE {p})"
        s = f"%{search}%"; params += [s,s,s]
    if ministry_filter and ministry_filter != "All":
        q += f" AND ministry={p}"; params.append(ministry_filter)
    q += " ORDER BY full_name"
    cur.execute(q, params)
    rows = rows_to_dicts(cur, cur.fetchall()); conn.close(); return rows

def get_member_by_id(member_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"SELECT * FROM members WHERE member_id={p}", (member_id,))
    row = row_to_dict(cur, cur.fetchone()); conn.close(); return row

def update_member(member_id, full_name, phone, gender, age, ministry, joined_date):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    try:
        cur.execute(f"UPDATE members SET full_name={p},phone={p},gender={p},age={p},ministry={p},joined_date={p} WHERE member_id={p}",
                    (full_name, phone, gender, age, ministry, joined_date, member_id))
        conn.commit(); return True, "Member updated."
    except Exception as e: return False, str(e)
    finally: conn.close()

def delete_member(member_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"DELETE FROM members WHERE member_id={p}", (member_id,))
    conn.commit(); conn.close()

def get_member_count():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM members WHERE is_active=1")
    n = scalar(cur.fetchone()); conn.close(); return n
