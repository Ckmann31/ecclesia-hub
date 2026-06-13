import datetime
from database import get_conn, ph, rows_to_dicts, scalar, is_pg

OFFERING_TYPES = ["Tithe","Thanksgiving Offering","Covenant Offering","Special Offering","Donation"]

def add_transaction(trans_date, offering_type, amount, recorded_by, notes=""):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    try:
        cur.execute(f"INSERT INTO finance (trans_date,type,amount,recorded_by,notes) VALUES ({p},{p},{p},{p},{p})",
                    (trans_date, offering_type, float(amount), recorded_by, notes))
        conn.commit(); return True, "Transaction recorded."
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_transactions(month=None, year=None, offering_type=None):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    q = "SELECT * FROM finance WHERE 1=1"; params = []
    if is_pg():
        if year: q += f" AND EXTRACT(YEAR FROM trans_date::date)={p}"; params.append(str(year))
        if month: q += f" AND EXTRACT(MONTH FROM trans_date::date)={p}"; params.append(str(month))
    else:
        if year: q += f" AND strftime('%Y',trans_date)={p}"; params.append(str(year))
        if month: q += f" AND strftime('%m',trans_date)={p}"; params.append(f"{month:02d}")
    if offering_type and offering_type != "All":
        q += f" AND type={p}"; params.append(offering_type)
    q += " ORDER BY trans_date DESC"
    cur.execute(q, params)
    rows = rows_to_dicts(cur, cur.fetchall()); conn.close(); return rows

def get_monthly_summary(month, year):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    if is_pg():
        cur.execute(f"SELECT type, SUM(amount) AS total FROM finance WHERE EXTRACT(YEAR FROM trans_date::date)={p} AND EXTRACT(MONTH FROM trans_date::date)={p} GROUP BY type",
                    (str(year), str(month)))
    else:
        cur.execute(f"SELECT type, SUM(amount) AS total FROM finance WHERE strftime('%Y',trans_date)={p} AND strftime('%m',trans_date)={p} GROUP BY type",
                    (str(year), f"{month:02d}"))
    rows = cur.fetchall(); conn.close()
    summary = {}
    for r in rows:
        t = r[0] if isinstance(r, tuple) else r["type"]
        a = r[1] if isinstance(r, tuple) else r["total"]
        summary[t] = a
    summary["TOTAL"] = sum(summary.values())
    return summary

def get_yearly_summary(year):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    if is_pg():
        cur.execute(f"SELECT TO_CHAR(trans_date::date,'MM') AS month, SUM(amount) AS total FROM finance WHERE EXTRACT(YEAR FROM trans_date::date)={p} GROUP BY month ORDER BY month", (str(year),))
    else:
        cur.execute(f"SELECT strftime('%m',trans_date) AS month, SUM(amount) AS total FROM finance WHERE strftime('%Y',trans_date)={p} GROUP BY month ORDER BY month", (str(year),))
    rows = cur.fetchall(); conn.close()
    names = {"01":"Jan","02":"Feb","03":"Mar","04":"Apr","05":"May","06":"Jun",
             "07":"Jul","08":"Aug","09":"Sep","10":"Oct","11":"Nov","12":"Dec"}
    return {names.get(r[0] if isinstance(r,tuple) else r["month"], "?"): (r[1] if isinstance(r,tuple) else r["total"]) for r in rows}

def delete_transaction(trans_id):
    conn = get_conn(); cur = conn.cursor(); p = ph()
    cur.execute(f"DELETE FROM finance WHERE id={p}", (trans_id,)); conn.commit(); conn.close()

def get_current_month_total():
    now = datetime.date.today()
    return get_monthly_summary(now.month, now.year).get("TOTAL", 0.0)
