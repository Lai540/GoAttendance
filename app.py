from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from models import db, Staff, Attendance, Learners
from forms import LoginForm, LogoutForm, FirstTimeRegistrationForm
from datetime import datetime, date, timezone, time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import os
import collections

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
db.init_app(app)

# ------------------ Email Helper ------------------
def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = 'gofishnethappykids2025@yahoo.com'
        msg['To'] = to_email

        server = smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465)
        server.login('gofishnethappykids2025@yahoo.com', 'zlgpdrjjbowprpnh')  # <-- app password
        server.send_message(msg)
        server.quit()

        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed for {to_email}: {e}")


# ------------------ IP Restriction ------------------

#ALLOWED_PUBLIC_IP = "154.159.238.226"  # School's public IP

#def is_allowed_ip(ip_address):
    #return ip_address == ALLOWED_PUBLIC_IP


# ------------------ Helper: Early Departure Summary ------------------
def summarize_early_departures():
    """Return dict with counts of early logouts per staff (Mon–Fri before 4:30pm)."""
    records = Attendance.query.order_by(Attendance.login_time.desc()).all()
    cutoff = time(16, 30)  # 4:30pm
    summary = collections.Counter()

    for rec in records:
        if rec.logout_time:
            if rec.logout_time.weekday() < 5:  # Mon-Fri only
                if rec.logout_time.time() < cutoff:
                    summary[rec.staff_id] += 1
    return summary


# ------------------ Routes ------------------
@app.route('/', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        client_ip = request.remote_addr
        if not is_allowed_ip(client_ip):
            flash("You must be connected to the school network to log in.", "danger")
            return redirect(url_for('login'))

        staff = Staff.query.filter_by(staff_id=form.staff_id.data, password=form.password.data).first()
        if staff:
            session['staff_id'] = staff.staff_id
            if form.remember_me.data:
                session.permanent = True

            # First-time registration check
            if not staff.email or not staff.subjects:
                return redirect(url_for('first_time_register', staff_id=staff.staff_id))

            # Record login (Nairobi time)
            kenya_tz = pytz.timezone('Africa/Nairobi')
            attendance = Attendance(
                staff_id=staff.staff_id,
                login_time=datetime.now(timezone.utc).astimezone(kenya_tz)
            )
            db.session.add(attendance)
            db.session.commit()

            # Send login email
            if staff.email:
                send_email(
                    staff.email,
                    "Login Confirmation",
                    f"Hello {staff.name}, you logged in at {attendance.login_time.strftime('%H:%M')}."
                )

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)


@app.route('/register/<staff_id>', methods=['GET','POST'])
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


@app.route('/dashboard')
def dashboard():
    if 'staff_id' not in session:
        flash('Please login first.', 'danger')
        return redirect(url_for('login'))

    staff = Staff.query.filter_by(staff_id=session['staff_id']).first()

    # ✅ Get the latest learners data
    latest_learners = Learners.query.order_by(Learners.created_at.desc()).first()

    if not latest_learners:
        flash("No learners data available. Please ask admin to add it in Admin Dashboard.", "warning")
        return render_template("dashboard.html", staff=staff, learners=None)

    # ✅ Prepare chart data
    categories = ["ECDE", "Primary", "JSS"]
    girls_counts = [
        latest_learners.ecde_girls,
        latest_learners.primary_girls,
        latest_learners.jss_girls
    ]
    boys_counts = [
        latest_learners.ecde_boys,
        latest_learners.primary_boys,
        latest_learners.jss_boys
    ]

    return render_template(
        "dashboard.html",
        staff=staff,
        learners=latest_learners,
        categories=categories,
        girls_counts=girls_counts,
        boys_counts=boys_counts,
        total_population=latest_learners.total_population
    )


@app.route('/logout/<staff_id>', methods=['GET','POST'])
def logout(staff_id):
    staff = Staff.query.filter_by(staff_id=staff_id).first()
    if not staff:
        flash('Invalid Staff ID', 'danger')
        return redirect(url_for('login'))

    client_ip = request.remote_addr
    if not is_allowed_ip(client_ip):
        flash("You must be connected to the school network to log out.", "danger")
        return redirect(url_for('dashboard'))

    form = LogoutForm()
    if form.validate_on_submit():
        attendance = Attendance.query.filter_by(staff_id=staff_id).order_by(Attendance.id.desc()).first()
        if not attendance:
            attendance = Attendance(staff_id=staff_id)
            db.session.add(attendance)
            db.session.commit()

        # Record logout (Nairobi time)
        kenya_tz = pytz.timezone('Africa/Nairobi')
        attendance.logout_time = datetime.now(timezone.utc).astimezone(kenya_tz)
        attendance.logout_reason = form.reason.data
        db.session.commit()

        # Send logout email
        if staff.email:
            send_email(
                staff.email,
                "Logout Confirmation",
                f"You logged out at {attendance.logout_time.strftime('%H:%M')}. Reason: {attendance.logout_reason}"
            )

        flash(f'Logout successful! You logged out at {attendance.logout_time.strftime("%H:%M")}', 'success')
        return redirect(url_for('dashboard'))

    last_login = Attendance.query.filter_by(staff_id=staff_id).order_by(Attendance.id.desc()).first()
    last_login_time = last_login.login_time.strftime("%H:%M") if last_login else "N/A"

    return render_template('logout.html', form=form, staff=staff, last_login_time=last_login_time)


@app.route('/logout_session')
def logout_session():
    session.clear()
    flash("Logged out successfully!", "success")
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

    # Attendance records + early departures
    records = Attendance.query.order_by(Attendance.login_time.desc()).all()
    summary = summarize_early_departures()

    # ✅ Learners form handling
    from forms import LearnersDataForm
    form = LearnersDataForm()

    if form.validate_on_submit():
        learners = Learners(
            ecde_girls=form.ecde_girls.data,
            ecde_boys=form.ecde_boys.data,
            primary_girls=form.primary_girls.data,
            primary_boys=form.primary_boys.data,
            jss_girls=form.jss_girls.data,
            jss_boys=form.jss_boys.data,
            total_population=form.total_population.data,
        )
        db.session.add(learners)
        db.session.commit()
        flash("Learners data saved successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    # ✅ Get latest learners record (for display)
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
        attendance = Attendance.query.filter_by(staff_id=staff.staff_id)\
            .filter(Attendance.login_time >= datetime(today.year, today.month, today.day)).first()
        if attendance and attendance.logout_time is None:
            send_email(staff.email, "Reminder: Logout", "Please log out today to complete your attendance record.")

scheduler = BackgroundScheduler()
scheduler.add_job(send_reminders, 'cron', hour=17, minute=0)
scheduler.start()


# ------------------ Run App ------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Preload staff
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

    app.run(host='0.0.0.0', port=5000, debug=True)
