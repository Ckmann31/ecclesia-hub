from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime, os
import database, auth, members as mem, visitors as vis
import attendance as att, follow_ups as fu, finance as fin, volunteers as vol

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ecclesia_hub_2024")
database.init_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def dec(*a, **kw):
        if "user" not in session: return redirect(url_for("login"))
        return f(*a, **kw)
    return dec

def me(): return session.get("user", {})
def is_super(): return me().get("role") == "super_admin"
def is_admin(): return me().get("role") in ("super_admin","admin")

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = auth.login(request.form["username"], request.form["password"])
        if user:
            session["user"] = user
            att.auto_flag_absent_members()
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    stats = {"members": mem.get_member_count(), "visitors": vis.get_visitor_count_this_month(),
             "followups": fu.get_pending_count(), "finance": fin.get_current_month_total(),
             "volunteers": vol.get_active_volunteer_count()}
    pending = fu.get_all_follow_ups(resolved=False)[:8]
    return render_template("dashboard.html", stats=stats, pending=pending, user=me())

@app.route("/members")
@login_required
def members_page():
    search = request.args.get("search",""); ministry = request.args.get("ministry","All")
    return render_template("members.html", members=mem.get_all_members(search, ministry),
                           ministries=mem.MINISTRIES, search=search, ministry=ministry, user=me())

@app.route("/members/add", methods=["GET","POST"])
@login_required
def member_add():
    if request.method == "POST":
        ok, result = mem.add_member(request.form["full_name"], request.form["phone"],
                                     request.form["gender"], request.form.get("age",0),
                                     request.form["ministry"], request.form["joined_date"])
        if ok: flash(f"Member added! ID: {result}", "success"); return redirect(url_for("members_page"))
        flash(result, "error")
    return render_template("member_form.html", member=None, ministries=mem.MINISTRIES, user=me())

@app.route("/members/edit/<member_id>", methods=["GET","POST"])
@login_required
def member_edit(member_id):
    m = mem.get_member_by_id(member_id)
    if not m: flash("Member not found.", "error"); return redirect(url_for("members_page"))
    if request.method == "POST":
        ok, msg = mem.update_member(member_id, request.form["full_name"], request.form["phone"],
                                     request.form["gender"], request.form.get("age",0),
                                     request.form["ministry"], request.form["joined_date"])
        flash(msg, "success" if ok else "error"); return redirect(url_for("members_page"))
    return render_template("member_form.html", member=m, ministries=mem.MINISTRIES, user=me())

@app.route("/members/delete/<member_id>")
@login_required
def member_delete(member_id):
    if not is_super(): flash("Permission denied.", "error"); return redirect(url_for("members_page"))
    mem.delete_member(member_id); flash("Member deleted.", "success")
    return redirect(url_for("members_page"))

@app.route("/visitors")
@login_required
def visitors_page():
    status = request.args.get("status","All"); search = request.args.get("search","")
    return render_template("visitors.html", visitors=vis.get_all_visitors(search, status),
                           statuses=vis.FOLLOW_UP_STATUSES, status=status, search=search, user=me())

@app.route("/visitors/add", methods=["GET","POST"])
@login_required
def visitor_add():
    if request.method == "POST":
        ok, msg = vis.add_visitor(request.form["full_name"], request.form["phone"],
                                   request.form["visit_date"], request.form.get("invited_by","Walk-in"),
                                   request.form.get("assigned_leader",""), request.form.get("notes",""))
        flash(msg, "success" if ok else "error"); return redirect(url_for("visitors_page"))
    return render_template("visitor_form.html", user=me())

@app.route("/visitors/update/<int:visitor_id>", methods=["POST"])
@login_required
def visitor_update(visitor_id):
    ok, msg = vis.update_visitor_status(visitor_id, request.form["status"])
    flash(msg, "success" if ok else "error"); return redirect(url_for("visitors_page"))

@app.route("/visitors/delete/<int:visitor_id>")
@login_required
def visitor_delete(visitor_id):
    vis.delete_visitor(visitor_id); flash("Visitor removed.", "success")
    return redirect(url_for("visitors_page"))

@app.route("/followups")
@login_required
def followups_page():
    resolved = request.args.get("resolved","0") == "1"
    return render_template("followups.html", followups=fu.get_all_follow_ups(resolved=resolved),
                           resolved=resolved, outcomes=fu.OUTCOMES, user=me())

@app.route("/followups/add", methods=["GET","POST"])
@login_required
def followup_add():
    if request.method == "POST":
        ok, msg = fu.add_manual_follow_up(request.form["member_id"], request.form["full_name"],
                                           request.form["phone"], request.form["reason"],
                                           request.form["action_taken"], request.form["outcome"],
                                           request.form["follow_up_date"])
        flash(msg, "success" if ok else "error"); return redirect(url_for("followups_page"))
    return render_template("followup_form.html", outcomes=fu.OUTCOMES, user=me())

@app.route("/followups/update/<int:fu_id>", methods=["POST"])
@login_required
def followup_update(fu_id):
    fu.update_follow_up(fu_id, request.form["reason"], request.form["action_taken"],
                        request.form["outcome"], request.form["follow_up_date"],
                        request.form.get("resolved") == "on")
    flash("Follow-up updated.", "success"); return redirect(url_for("followups_page"))

@app.route("/followups/resolve/<int:fu_id>")
@login_required
def followup_resolve(fu_id):
    fu.resolve_follow_up(fu_id); flash("Marked resolved.", "success")
    return redirect(url_for("followups_page"))

@app.route("/followups/autodetect")
@login_required
def followup_autodetect():
    count = att.auto_flag_absent_members()
    flash(f"{count} member(s) auto-flagged." if count else "No new absences.", "success")
    return redirect(url_for("followups_page"))

@app.route("/finance")
@login_required
def finance_page():
    if not is_admin(): flash("Access denied.", "error"); return redirect(url_for("dashboard"))
    now = datetime.date.today()
    month = int(request.args.get("month", now.month)); year = int(request.args.get("year", now.year))
    return render_template("finance.html", transactions=fin.get_transactions(month, year),
                           summary=fin.get_monthly_summary(month, year), month=month, year=year,
                           offering_types=fin.OFFERING_TYPES, user=me())

@app.route("/finance/add", methods=["GET","POST"])
@login_required
def finance_add():
    if request.method == "POST":
        ok, msg = fin.add_transaction(request.form["trans_date"], request.form["type"],
                                       request.form["amount"], request.form["recorded_by"],
                                       request.form.get("notes",""))
        flash(msg, "success" if ok else "error"); return redirect(url_for("finance_page"))
    return render_template("finance_form.html", offering_types=fin.OFFERING_TYPES,
                           user=me(), recorded_by=me().get("full_name",""))

@app.route("/finance/delete/<int:trans_id>")
@login_required
def finance_delete(trans_id):
    if not is_super(): flash("Permission denied.", "error"); return redirect(url_for("finance_page"))
    fin.delete_transaction(trans_id); flash("Deleted.", "success")
    return redirect(url_for("finance_page"))

@app.route("/finance/yearly")
@login_required
def finance_yearly():
    year = int(request.args.get("year", datetime.date.today().year))
    summary = fin.get_yearly_summary(year); total = sum(summary.values())
    return render_template("finance_yearly.html", summary=summary, total=total, year=year, user=me())

@app.route("/attendance")
@login_required
def attendance_page():
    sundays = att.get_last_n_sundays(8)
    selected = request.args.get("date", sundays[0] if sundays else "")
    return render_template("attendance.html", records=att.get_attendance_for_date(selected),
                           sundays=sundays, selected=selected, user=me())

@app.route("/attendance/mark", methods=["POST"])
@login_required
def attendance_mark():
    sunday_date = request.form["sunday_date"]
    present_ids = request.form.getlist("present")
    for m in mem.get_all_members():
        att.mark_attendance(m["member_id"], sunday_date, m["member_id"] in present_ids)
    flash(f"Attendance saved for {sunday_date}.", "success")
    return redirect(url_for("attendance_page", date=sunday_date))

@app.route("/volunteers")
@login_required
def volunteers_page():
    ministry = request.args.get("ministry","All")
    return render_template("volunteers.html", volunteers=vol.get_all_volunteers_with_rates(ministry),
                           ministries=mem.MINISTRIES, ministry=ministry, user=me())

@app.route("/volunteers/add", methods=["GET","POST"])
@login_required
def volunteer_add():
    if request.method == "POST":
        ok, msg = vol.add_volunteer(request.form["member_id"], request.form["ministry"],
                                     request.form["role"], request.form["availability"])
        flash(msg, "success" if ok else "error"); return redirect(url_for("volunteers_page"))
    return render_template("volunteer_form.html", ministries=mem.MINISTRIES,
                           availabilities=vol.AVAILABILITIES, user=me())

@app.route("/volunteers/attendance/<member_id>", methods=["POST"])
@login_required
def volunteer_attendance(member_id):
    vol.mark_volunteer_attendance(member_id, request.form["service_date"],
                                   request.form.get("present") == "on")
    flash("Attendance recorded.", "success"); return redirect(url_for("volunteers_page"))

@app.route("/volunteers/remove/<member_id>")
@login_required
def volunteer_remove(member_id):
    vol.remove_volunteer(member_id); flash("Volunteer removed.", "success")
    return redirect(url_for("volunteers_page"))

@app.route("/users")
@login_required
def users_page():
    if not is_super(): flash("Access denied.", "error"); return redirect(url_for("dashboard"))
    return render_template("users.html", users=auth.get_all_users(), user=me())

@app.route("/users/add", methods=["GET","POST"])
@login_required
def user_add():
    if not is_super(): flash("Access denied.", "error"); return redirect(url_for("dashboard"))
    if request.method == "POST":
        ok, msg = auth.create_user(request.form["username"], request.form["password"],
                                    request.form["full_name"], request.form["role"],
                                    me().get("role",""))
        flash(msg, "success" if ok else "error"); return redirect(url_for("users_page"))
    return render_template("user_form.html", user=me())

@app.route("/users/delete/<int:user_id>")
@login_required
def user_delete(user_id):
    if not is_super(): flash("Access denied.", "error"); return redirect(url_for("users_page"))
    if me().get("id") == user_id: flash("Cannot delete your own account.", "error"); return redirect(url_for("users_page"))
    auth.delete_user(user_id); flash("User deleted.", "success")
    return redirect(url_for("users_page"))


@app.route("/change-password", methods=["GET","POST"])
@login_required
def change_password():
    if request.method == "POST":
        current = request.form["current_password"]
        new_pw  = request.form["new_password"]
        confirm = request.form["confirm_password"]
        if new_pw != confirm:
            flash("New passwords do not match.", "error")
            return redirect(url_for("change_password"))
        # Verify current password
        user = auth.login(me().get("username"), current)
        if not user:
            flash("Current password is incorrect.", "error")
            return redirect(url_for("change_password"))
        auth.change_password(me().get("id"), new_pw)
        flash("Password updated successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("change_password.html", user=me())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
