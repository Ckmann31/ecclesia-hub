from database import get_conn, ph, rows_to_dicts, scalar

OUTCOMES = ["Pending","Returning","Needs Support","Unreachable","Left Church"]

def get_all_follow_ups(resolved=False, search=""):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    q = f"SELECT * FROM follow_ups WHERE resolved={p}"; params = [1 if resolved else 0]
    if search:
        q += f" AND (full_name LIKE {p} OR member_id LIKE {p})"
        s = f"%{search}%"; params += [s,s]
    q += " ORDER BY created_at DESC"
    cur.execute(q, params)
    rows = rows_to_dicts(cur, cur.fetchall()); conn.close(); return rows

def update_follow_up(fu_id, reason, action_taken, outcome, follow_up_date, resolve=False):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"UPDATE follow_ups SET reason={p},action_taken={p},outcome={p},follow_up_date={p},resolved={p} WHERE id={p}",
                (reason, action_taken, outcome, follow_up_date, 1 if resolve else 0, fu_id))
    conn.commit(); conn.close()

def add_manual_follow_up(member_id, full_name, phone, reason, action_taken, outcome, follow_up_date):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    try:
        cur.execute(f"INSERT INTO follow_ups (member_id,full_name,phone,reason,action_taken,outcome,follow_up_date,flagged_auto,resolved) VALUES ({p},{p},{p},{p},{p},{p},{p},0,0)",
                    (member_id, full_name, phone, reason, action_taken, outcome, follow_up_date))
        conn.commit(); return True, "Follow-up added."
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_pending_count():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM follow_ups WHERE resolved=0")
    n = scalar(cur.fetchone()); conn.close(); return n

def resolve_follow_up(fu_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"UPDATE follow_ups SET resolved=1 WHERE id={p}", (fu_id,))
    conn.commit(); conn.close()

def delete_follow_up(fu_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"DELETE FROM follow_ups WHERE id={p}", (fu_id,))
    conn.commit(); conn.close()
