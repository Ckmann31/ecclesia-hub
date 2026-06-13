from database import get_conn, ph, rows_to_dicts, row_to_dict, scalar, is_pg
import members as mem

FOLLOW_UP_STATUSES = ["Pending","In Progress","Completed","Converted to Member"]

def add_visitor(full_name, phone, visit_date, invited_by, assigned_leader, notes=""):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    try:
        cur.execute(f"INSERT INTO visitors (full_name,phone,visit_date,invited_by,assigned_leader,notes) VALUES ({p},{p},{p},{p},{p},{p})",
                    (full_name.strip(), phone, visit_date, invited_by, assigned_leader, notes))
        conn.commit(); return True, "Visitor added."
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_all_visitors(search="", status_filter="All"):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    q = "SELECT * FROM visitors WHERE 1=1"; params = []
    if search:
        q += f" AND (full_name LIKE {p} OR phone LIKE {p})"
        s = f"%{search}%"; params += [s,s]
    if status_filter and status_filter != "All":
        q += f" AND follow_up_status={p}"; params.append(status_filter)
    q += " ORDER BY visit_date DESC"
    cur.execute(q, params)
    rows = rows_to_dicts(cur, cur.fetchall()); conn.close(); return rows

def update_visitor_status(visitor_id, new_status, assigned_leader=None):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    if assigned_leader:
        cur.execute(f"UPDATE visitors SET follow_up_status={p},assigned_leader={p} WHERE id={p}",
                    (new_status, assigned_leader, visitor_id))
    else:
        cur.execute(f"UPDATE visitors SET follow_up_status={p} WHERE id={p}", (new_status, visitor_id))
    if new_status == "Converted to Member":
        cur.execute(f"SELECT * FROM visitors WHERE id={p}", (visitor_id,))
        v = row_to_dict(cur, cur.fetchone())
        if v:
            conn.commit(); conn.close()
            mem.add_member(v["full_name"], v["phone"], "", 0, "", v["visit_date"])
            return True, "Visitor converted to member!"
    conn.commit(); conn.close(); return True, "Status updated."

def delete_visitor(visitor_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"DELETE FROM visitors WHERE id={p}", (visitor_id,))
    conn.commit(); conn.close()

def get_visitor_count_this_month():
    conn = get_conn(); cur = conn.cursor()
    if is_pg():
        cur.execute("SELECT COUNT(*) FROM visitors WHERE TO_CHAR(visit_date::date,'YYYY-MM')=TO_CHAR(CURRENT_DATE,'YYYY-MM')")
    else:
        cur.execute("SELECT COUNT(*) FROM visitors WHERE strftime('%Y-%m',visit_date)=strftime('%Y-%m','now')")
    n = scalar(cur.fetchone()); conn.close(); return n
