from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from models import db, Staff, Attendance, Learners
# Note: we expect LoginForm, LogoutForm, FirstTimeRegistrationForm in forms.py
# If you added a LearnersDataForm in forms.py, we will import it; otherwise a fallback is defined below.
from forms import LoginForm, LogoutForm, FirstTimeRegistrationForm
from datetime import datetime, date, timezone, time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os
import collections

# Try importing LearnersDataForm from forms, otherwise define a simple fallback.
try:
    from forms import LearnersDataForm
except Exception:
    # Fallback simple form definition so admin can still post learners data
    from flask_wtf import FlaskForm
    from wtforms import IntegerField, SubmitField
    from wtforms.validators import NumberRange, Optional

    class LearnersDataForm(FlaskForm):
        ecde_girls = IntegerField('ECDE Girls', validators=[Optional(), NumberRange(min=0)])
        ecde_boys = IntegerField('ECDE Boys', validators=[Optional(), NumberRange(min=0)])
        primary_girls = IntegerField('Primary Girls', validators=[Optional(), NumberRange(min=0)])
        primary_boys = IntegerField('Primary Boys', validators=[Optional(), NumberRange(min=0)])
        jss_girls = IntegerField('JSS Girls', validators=[Optional(), NumberRange(min=0)])
        jss_boys = IntegerField('JSS Boys', validators=[Optional(), NumberRange(min=0)])
        total_population = IntegerField('Total Population', validators=[Optional(), NumberRange(min=0)])
        submit = SubmitField('Save Learners Data')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
# Use environment variable for production DB; fallback to sqlite for local testing
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
db.init_app(app)


# ------------------ Email Helper ------------------
def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = 'gofishnethappykids2025@yahoo.com'
        msg['To'] = to_email

        server = smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465)
        server.login('gofishnethappykids2025@yahoo.com', 'zlgpdrjjbowprpnh')  # <-- app password (secure this)
        server.send_message(msg)
        server.quit()

        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed for {to_email}: {e}")


# ------------------ Helper: Early Departure Summary ------------------
def summarize_early_departures():
    """Return Counter with counts of early logouts per staff (Mon–Fri before 4:30pm)."""
    records = Attendance.query.order_by(Attendance.login_time.desc()).all()
    cutoff = time(16, 30)  # 4:30pm
    summary = collections.Counter()

    for rec in records:
        if rec.logout_time:
            try:
                if rec.logout_time.weekday() < 5:  # Mon-Fri only
                    if rec.logout_time.time() < cutoff:
                        summary[rec.staff_id] += 1
            except Exception:
                # If timezone-naive / unexpected value, skip
                continue
    return summary


# ------------------ Routes ------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    """System login (authentication only). Do NOT create attendance here."""
    form = LoginForm()
    if form.validate_on_submit():
        staff = Staff.query.filter_by(staff_id=form.staff_id.data, password=form.password.data).first()
        if staff:
            session['staff_id'] = staff.staff_id
            if form.remember_me.data:
                session.permanent = True

            # First-time registration check
            if not staff.email or not staff.subjects:
                return redirect(url_for('first_time_register', staff_id=staff.staff_id))

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)


@app.route('/register/<staff_id>', methods=['GET', 'POST'])
def first_time_register(staff_id):
    staff = Staff.query.filter_by(staff_id=staff_id).first()
    if not staff:
        flash('Invalid Staff ID', 'danger')
        return redirect(url_for('login'))

    form = FirstTimeRegistrationForm()
    if form.validate_on_submit():
        staff.email = form.email.data
        staff.is_class_teacher = form.is_class_teacher.data
        staff.grade_assigned = form.grade_assigned.data if form.is_class_teacher.data else None
        staff.subjects = form.subjects.data
        db.session.commit()
        flash('Registration completed! Use your Staff ID and initial password 123456 to login.', 'success')
        return redirect(url_for('login'))

    return render_template('first_time_register.html', form=form, staff_name=staff.name)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """Staff dashboard: shows learners data and provides quick actions (Sign In, Sign Out, Change Password)."""
    if 'staff_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    staff = Staff.query.filter_by(staff_id=session['staff_id']).first()
    if not staff:
        # Rare: session contains an unknown staff_id
        session.clear()
        flash('Invalid session. Please login again.', 'danger')
        return redirect(url_for('login'))

    # Check if staff has an open attendance (signed in but not signed out)
    open_att = Attendance.query.filter_by(staff_id=staff.staff_id, logout_time=None).first()
    staff.attendance_active = open_att is not None

    # Retrieve latest learners data for charts
    latest_learners = Learners.query.order_by(Learners.created_at.desc()).first()

    if not latest_learners:
        # render dashboard without learners charts (admin should add data)
        return render_template("dashboard.html", staff=staff, learners=None)

    categories = ["ECDE", "Primary", "JSS"]
    girls_counts = [
        latest_learners.ecde_girls or 0,
        latest_learners.primary_girls or 0,
        latest_learners.jss_girls or 0
    ]
    boys_counts = [
        latest_learners.ecde_boys or 0,
        latest_learners.primary_boys or 0,
        latest_learners.jss_boys or 0
    ]
    total_population = latest_learners.total_population or (sum(girls_counts) + sum(boys_counts))

    return render_template(
        "dashboard.html",
        staff=staff,
        learners=latest_learners,
        categories=categories,
        girls_counts=girls_counts,
        boys_counts=boys_counts,
        total_population=total_population
    )


# ------------------ Attendance Sign In ------------------
@app.route('/attendance/signin', methods=['POST'])
def sign_in_attendance():
    """Create a new attendance record for the logged-in staff (if none open)."""
    if 'staff_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    staff_id = session['staff_id']
    kenya_tz = pytz.timezone('Africa/Nairobi')

    # Prevent duplicate open attendance rows
    open_attendance = Attendance.query.filter_by(staff_id=staff_id, logout_time=None).first()
    if open_attendance:
        flash("You already signed in and haven't signed out yet.", "warning")
        return redirect(url_for('dashboard'))

    attendance = Attendance(
        staff_id=staff_id,
        login_time=datetime.now(timezone.utc).astimezone(kenya_tz)
    )
    db.session.add(attendance)
    db.session.commit()

    # Optional: send email if staff has email
    staff = Staff.query.filter_by(staff_id=staff_id).first()
    if staff and staff.email:
        send_email(
            staff.email,
            "Attendance Signed In",
            f"Hello {staff.name}, you signed in for attendance at {attendance.login_time.strftime('%Y-%m-%d %H:%M')}."
        )

    flash(f"✅ Attendance signed in at {attendance.login_time.strftime('%H:%M')}", "success")
    return redirect(url_for('dashboard'))


# ------------------ Attendance Sign Out (with reason form) ------------------
@app.route('/logout/<staff_id>', methods=['GET', 'POST'])
def logout(staff_id):
    """Sign out attendance (update the latest open attendance row), and optionally end session if needed."""
    staff = Staff.query.filter_by(staff_id=staff_id).first()
    if not staff:
        flash('Invalid Staff ID', 'danger')
        return redirect(url_for('login'))

    form = LogoutForm()
    if form.validate_on_submit():
        # Find the latest open attendance (signed in but not signed out)
        attendance = Attendance.query.filter_by(staff_id=staff_id, logout_time=None) \
            .order_by(Attendance.id.desc()).first()

        if attendance:
            kenya_tz = pytz.timezone('Africa/Nairobi')
            attendance.logout_time = datetime.now(timezone.utc).astimezone(kenya_tz)
            attendance.logout_reason = form.reason.data
            db.session.commit()

            # Optional email notification
            if staff.email:
                send_email(
                    staff.email,
                    "Attendance Signed Out",
                    f"Hello {staff.name}, you signed out at {attendance.logout_time.strftime('%Y-%m-%d %H:%M')}. Reason: {attendance.logout_reason}"
                )

            flash(f'✅ Signed out at {attendance.logout_time.strftime("%H:%M")}', 'success')
        else:
            flash("⚠️ No active sign-in record found to sign out.", "warning")

        # After sign-out keep the session active (don't auto-logout session), user can logout of system via logout_session
        return redirect(url_for('dashboard'))

    # If GET: show the sign-out form, and display last sign-in time for reference
    last_login = Attendance.query.filter_by(staff_id=staff_id).order_by(Attendance.id.desc()).first()
    last_login_time = last_login.login_time.strftime("%Y-%m-%d %H:%M") if last_login else "N/A"

    return render_template('logout.html', form=form, staff=staff, last_login_time=last_login_time)


@app.route('/attendance/signout_simple', methods=['POST'])
def signout_attendance_simple():
    """
    Optional: a simple sign-out endpoint (no reason), used if you want a one-click signout.
    Keeps behaviour consistent: updates the latest open attendance record.
    """
    if 'staff_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    staff_id = session['staff_id']
    attendance = Attendance.query.filter_by(staff_id=staff_id, logout_time=None).order_by(Attendance.id.desc()).first()
    if attendance:
        kenya_tz = pytz.timezone('Africa/Nairobi')
        attendance.logout_time = datetime.now(timezone.utc).astimezone(kenya_tz)
        db.session.commit()
        flash(f'✅ Signed out at {attendance.logout_time.strftime("%H:%M")}', 'success')
    else:
        flash('⚠️ No active sign-in record found.', 'warning')

    return redirect(url_for('dashboard'))


@app.route('/logout_session')
def logout_session():
    """End the web session (no attendance changes)."""
    session.clear()
    flash("Logged out of system successfully!", "success")
    return redirect(url_for('login'))


# ------------------ Admin ------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'staff_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    staff = Staff.query.filter_by(staff_id=session['staff_id']).first()
    if not staff or not staff.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Attendance records (most recent first)
    records = Attendance.query.order_by(Attendance.login_time.desc()).all()
    summary = summarize_early_departures()

    # Learners form
    form = LearnersDataForm()
    if form.validate_on_submit():
        # Use 0 defaults if fields are None
        ecde_girls = form.ecde_girls.data or 0
        ecde_boys = form.ecde_boys.data or 0
        primary_girls = form.primary_girls.data or 0
        primary_boys = form.primary_boys.data or 0
        jss_girls = form.jss_girls.data or 0
        jss_boys = form.jss_boys.data or 0
        total_population = form.total_population.data or (ecde_girls + ecde_boys + primary_girls + primary_boys + jss_girls + jss_boys)

        learners = Learners(
            ecde_girls=ecde_girls,
            ecde_boys=ecde_boys,
            primary_girls=primary_girls,
            primary_boys=primary_boys,
            jss_girls=jss_girls,
            jss_boys=jss_boys,
            total_population=total_population
        )
        db.session.add(learners)
        db.session.commit()
        flash("Learners data saved successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    # Latest learners for display
    latest_learners = Learners.query.order_by(Learners.created_at.desc()).first()

    return render_template(
        'admin.html',
        records=records,
        summary=summary,
        form=form,
        learners=latest_learners
    )


# ------------------ Admin Export ------------------
@app.route('/admin/export')
def export_reports():
    staff = Staff.query.filter_by(staff_id=session.get('staff_id')).first()
    if not staff or not staff.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))

    # Export attendance table to Excel
    df = pd.read_sql_table('attendance', db.engine)
    file_path = 'attendance_report.xlsx'
    df.to_excel(file_path, index=False)

    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('Failed to generate report.', 'danger')
        return redirect(url_for('admin_dashboard'))


# ------------------ Scheduler ------------------
def send_reminders():
    today = date.today()
    staff_list = Staff.query.all()
    for staff in staff_list:
        # today's date midnight in local
        kenya_tz = pytz.timezone('Africa/Nairobi')
        start_of_today = datetime(today.year, today.month, today.day, tzinfo=timezone.utc).astimezone(kenya_tz)
        attendance = Attendance.query.filter_by(staff_id=staff.staff_id) \
            .filter(Attendance.login_time >= start_of_today).first()
        if attendance and attendance.logout_time is None and staff.email:
            send_email(staff.email, "Reminder: Logout", "Please sign out today to complete your attendance record.")


scheduler = BackgroundScheduler()
scheduler.add_job(send_reminders, 'cron', hour=17, minute=0)
scheduler.start()


# ------------------ Run App ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Preload staff (if empty)
        if Staff.query.count() == 0:
            staff_list = [
                ("GFHKTS001", "Wilfred Lai"), ("GFHKTS002", "Josephine Ochieng"),
                ("GFHKTS003", "Catherine Mwende"), ("GFHKTS004", "Samuel Orimba"),
                ("GFHKTS005", "Melvine Ogada"), ("GFHKTS006", "Evance Oduor"),
                ("GFHKTS007", "Emma Muthoka"), ("GFHKTS008", "Pamela Aduka"),
                ("GFHKTS009", "Quinter Owuor"), ("GFHKTS010", "Siprose Juma"),
                ("GFHKTS011", "Alice Nyahela"), ("GFHKTS012", "Dorcus Oranga"),
                ("GFHKTS013", "Mable Wafula"), ("GFHKTS014", "Vivian Omuoyo"),
                ("GFHKTS015", "Karilus Orao"), ("GFHKTS016", "Tony Otieno"),
                ("GFHKTS017", "Walter Otieno"), ("GFHKTS018", "Hilda Asiavugwa")
            ]
            for staff_id, name in staff_list:
                staff = Staff(staff_id=staff_id, name=name, password='123456')
                db.session.add(staff)

            admin = Staff(staff_id='Gofishnet001', name='Administrator', password='Gofishnet001*', is_admin=True)
            db.session.add(admin)

            db.session.commit()
            print("Staff table preloaded with 18 teachers + admin account!")

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)

