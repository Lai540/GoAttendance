# GoAttendance

GoAttendance is a lightweight, local-first school staff attendance management system built with **Flask**, **Bootstrap**, and **SQLite/MySQL**. It allows staff members to sign in and sign out while providing administrators with tools to manage attendance records, export reports, and monitor staff activity.

---

## ✨ Features
- 🔑 **Secure Login System** with first-time staff registration  
- ✅ **Sign In / Sign Out Attendance** with logout reasons  
- 📧 **Email Notifications** sent on login and logout  
- 🕔 **Automatic Reminders** if staff forget to sign out by evening  
- 🏠 **Dashboard** with staff status and quick actions  
- ⚙️ **Admin Panel** for managing attendance and exporting reports to Excel  
- 🔒 **Change Password** option for staff  
- 🌐 **Local Network Restriction** (only accessible within school Wi-Fi)  
- 📊 **Reports & Tracking** of login and logout history  

---

## 🛠 Tech Stack
- **Backend**: Python (Flask)  
- **Frontend**: HTML, CSS (Bootstrap 5)  
- **Database**: SQLite (default) / MySQL (optional)  
- **Other**: Flask-WTF (forms), Flask-Mail (email), Pandas (report export)  

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+  
- pip (Python package manager)  

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/GoAttendance.git
cd GoAttendance

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
