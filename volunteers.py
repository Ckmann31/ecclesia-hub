from database import get_conn, ph, rows_to_dicts, scalar, is_pg

AVAILABILITIES = ["Every Sunday","Bi-weekly","Monthly","Special Events"]

def add_volunteer(member_id, ministry, role, availability):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    try:
        if is_pg():
            cur.execute(f"INSERT INTO volunteers (member_id,ministry,role,availability) VALUES ({p},{p},{p},{p}) ON CONFLICT (member_id) DO UPDATE SET ministry=EXCLUDED.ministry,role=EXCLUDED.role,availability=EXCLUDED.availability",
                        (member_id, ministry, role, availability))
        else:
            cur.execute("INSERT INTO volunteers (member_id,ministry,role,availability) VALUES (?,?,?,?) ON CONFLICT(member_id) DO UPDATE SET ministry=excluded.ministry,role=excluded.role,availability=excluded.availability",
                        (member_id, ministry, role, availability))
        conn.commit(); return True, "Volunteer saved."
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_all_volunteers(ministry_filter="All"):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    q = "SELECT v.*,m.full_name,m.phone FROM volunteers v JOIN members m ON v.member_id=m.member_id WHERE m.is_active=1"
    params = []
    if ministry_filter and ministry_filter != "All":
        q += f" AND v.ministry={p}"; params.append(ministry_filter)
    q += " ORDER BY m.full_name"
    cur.execute(q, params)
    rows = rows_to_dicts(cur, cur.fetchall()); conn.close(); return rows

def mark_volunteer_attendance(member_id, service_date, present):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    if is_pg():
        cur.execute(f"INSERT INTO volunteer_attendance (member_id,service_date,present) VALUES ({p},{p},{p}) ON CONFLICT (member_id,service_date) DO UPDATE SET present=EXCLUDED.present",
                    (member_id, service_date, 1 if present else 0))
    else:
        cur.execute("INSERT INTO volunteer_attendance (member_id,service_date,present) VALUES (?,?,?) ON CONFLICT(member_id,service_date) DO UPDATE SET present=excluded.present",
                    (member_id, service_date, 1 if present else 0))
    conn.commit(); conn.close()

def get_attendance_rate(member_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"SELECT COUNT(*) AS total, SUM(present) AS attended FROM volunteer_attendance WHERE member_id={p}", (member_id,))
    row = cur.fetchone(); conn.close()
    total = row[0] if isinstance(row, tuple) else row["total"]
    attended = row[1] if isinstance(row, tuple) else row["attended"]
    if total and total > 0:
        return round(((attended or 0) / total) * 100, 1)
    return 0.0

def get_all_volunteers_with_rates(ministry_filter="All"):
    vols = get_all_volunteers(ministry_filter)
    for v in vols: v["attendance_rate"] = get_attendance_rate(v["member_id"])
    return vols

def remove_volunteer(member_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"DELETE FROM volunteers WHERE member_id={p}", (member_id,)); conn.commit(); conn.close()

def get_active_volunteer_count():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM volunteers")
    return scalar(cur.fetchone())
