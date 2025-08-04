# Tool Version Audit & Notification System

A comprehensive system that tracks software tool versions, compares them with latest releases, and notifies users about outdated tools with upgrade instructions.

## 🎯 Features

- **Web-based submission form** for tool version entries
- **Automated version comparison** using semantic versioning
- **Email notifications** for outdated tools
- **User dashboard** to view current status
- **Daily automated checks** via Python script
- **Upgrade instructions** fetched from official sources

## 🏗️ System Architecture

```
Frontend (HTML/CSS/JS) → Backend (Flask/Python) → Database (SQLite) → Email Service
                                    ↓
                            Daily Cron Job (Python Script)
                                    ↓
                            Version Check & Notification
```

## 📋 Workflow

1. **User Submission**: Users submit tool name, version, and email via web form
2. **Data Storage**: Submissions stored in SQLite database with timestamp
3. **Daily Processing**: Python script checks all entries against latest versions
4. **Version Comparison**: Uses semantic versioning for accurate comparison
5. **Notification**: Sends email alerts for outdated tools with upgrade steps
6. **Dashboard**: Users can view their submission status and recommendations

## 🚀 Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the web application: `python app.py`
3. Access the form at: `http://localhost:5000`
4. Set up daily cron job: `python daily_check.py`

## 📁 Project Structure

```
├── app.py                 # Main Flask web application
├── daily_check.py         # Daily version check script
├── version_checker.py     # Version comparison logic
├── email_notifier.py      # Email notification system
├── database.py           # Database operations
├── static/               # CSS, JS, images
├── templates/            # HTML templates
├── data/                 # Database and logs
└── requirements.txt      # Python dependencies
```

## 🛠️ Supported Tools

- SQL Server
- Oracle Database
- Python
- Node.js
- Java
- .NET Framework
- And more...

## 📧 Email Notifications

Automated emails include:
- Current vs Latest version comparison
- Security updates and bug fixes
- Step-by-step upgrade instructions
- Links to official documentation

## 🔒 Security & Privacy

- No AI services used (per CTS requirements)
- Open-source libraries only
- Local data storage
- Secure email handling

---
*Built for the vibe coding project - Tool Version Audit & Notification System*
