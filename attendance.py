import datetime
from database import get_conn, ph, rows_to_dicts, row_to_dict, scalar, is_pg

def get_last_n_sundays(n=8):
    today = datetime.date.today()
    days = (today.weekday() + 1) % 7
    last = today - datetime.timedelta(days=days)
    return [(last - datetime.timedelta(weeks=i)).isoformat() for i in range(n)]

def mark_attendance(member_id, sunday_date, present):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    if is_pg():
        cur.execute(f"INSERT INTO attendance (member_id,sunday_date,present) VALUES ({p},{p},{p}) ON CONFLICT (member_id,sunday_date) DO UPDATE SET present=EXCLUDED.present",
                    (member_id, sunday_date, 1 if present else 0))
    else:
        cur.execute("INSERT INTO attendance (member_id,sunday_date,present) VALUES (?,?,?) ON CONFLICT(member_id,sunday_date) DO UPDATE SET present=excluded.present",
                    (member_id, sunday_date, 1 if present else 0))
    conn.commit(); conn.close()

def get_attendance_for_date(sunday_date):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"SELECT m.member_id,m.full_name,m.ministry,COALESCE(a.present,0) AS present FROM members m LEFT JOIN attendance a ON m.member_id=a.member_id AND a.sunday_date={p} WHERE m.is_active=1 ORDER BY m.full_name",
                (sunday_date,))
    rows = rows_to_dicts(cur, cur.fetchall()); conn.close(); return rows

def detect_absent_members(consecutive_misses=2):
    sundays = get_last_n_sundays(consecutive_misses)
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute("SELECT member_id,full_name,phone FROM members WHERE is_active=1")
    all_members = rows_to_dicts(cur, cur.fetchall())
    absent = []
    for m in all_members:
        mid = m["member_id"]; missed_all = True
        for s in sundays:
            cur.execute(f"SELECT present FROM attendance WHERE member_id={p} AND sunday_date={p}", (mid, s))
            row = cur.fetchone()
            if row and (row[0] if isinstance(row, tuple) else row["present"]) == 1:
                missed_all = False; break
        if missed_all:
            cur.execute(f"SELECT id FROM follow_ups WHERE member_id={p} AND resolved=0 AND flagged_auto=1", (mid,))
            if not cur.fetchone():
                absent.append({"member_id": mid, "full_name": m["full_name"], "phone": m["phone"]})
    conn.close(); return absent

def auto_flag_absent_members():
    absent = detect_absent_members(2)
    conn = get_conn(); cur = conn.cursor(); p = ph()
    today = datetime.date.today().isoformat(); count = 0
    for m in absent:
        cur.execute(f"INSERT INTO follow_ups (member_id,full_name,phone,reason,action_taken,outcome,follow_up_date,flagged_auto,resolved) VALUES ({p},{p},{p},{p},{p},{p},{p},1,0)",
                    (m["member_id"],m["full_name"],m["phone"],"Absent from church (auto-detected)","Pending contact","Pending",today))
        count += 1
    conn.commit(); conn.close(); return count
