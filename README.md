# 360-Degree Feedback Application

A comprehensive enterprise-grade feedback management system built with Streamlit and Turso database.

## Overview

This application facilitates a performance review process where employees receive feedback from multiple sources - peers, subordinates, and supervisors - providing a "360-degree" view of their performance.

## Features

### 🔐 Authentication System
- **First-time password setup** for new users
- **Secure password hashing** with bcrypt
- **Role-based access control** (employee, hr, super_admin)

### 👥 Employee Features
- **Request Feedback** from 3-5 colleagues with relationship type declarations
- **View Anonymized Feedback** received from others
- **Complete Reviews** for colleagues with different question sets
- **Excel Export** of personal feedback data
- **Draft Saving** for incomplete reviews

### 👨‍💼 Manager Features
- **Approve/Reject Nominations** from team members
- **Review Relationship Types** declared by requesters
- **Provide Rejection Reasons** when declining nominations

### 📊 HR Dashboard
- **Create and Manage Review Cycles** with 4-5 week timelines
- **Monitor Progress** across all phases
- **Send Reminder Emails** to users with pending reviews
- **View Analytics** and completion metrics
- **Bulk Reminder Management**

### ⚙️ Admin Features
- **User Management** - add, activate/deactivate users
- **Role Assignment** - manage hr and super_admin roles
- **Question Management** - customize feedback questions
- **System Configuration** - manage settings and preferences

## Installation & Setup

### Prerequisites
- Python 3.8+
- Turso database account

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup
The application connects to your Turso database using credentials in `.streamlit/secrets.toml`:

```toml
DB_URL = "libsql://your-database-url.turso.io"
AUTH_TOKEN = "your-turso-auth-token"

# Optional: Email configuration
[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_user = "your-email@company.com"
email_password = "your-app-password"
```

### 3. Initialize Database
```bash
# Create database schema
python create_schema.py

# Insert initial data (roles, questions, users)
python simple_insert.py
```

### 4. Run Application
```bash
streamlit run main.py
```

## Initial Users & Roles

The system comes pre-populated with users from your organization:

### Super Admin
- **Donald Lobo** (lobo@projecttech4dev.org) - Full system access

### HR Personnel  
- **Erica Arya** (erica@projecttech4dev.org) - HR dashboard and management

### Employees
- All other users have employee role by default

## First-Time Login

1. **Set Password**: New users should use "Set Password" to create their account
2. **Login**: Use email and password to access the system
3. **Navigation**: Role-based menu appears based on user permissions

## How to Use

### For Employees

1. **Request Feedback**
   - Select 3-5 colleagues
   - Declare relationship types (peer, manager, direct_reportee, etc.)
   - Submit for manager approval

2. **Complete Reviews**
   - View pending requests in "Reviews to Complete"
   - Answer relationship-specific questions
   - Save drafts or submit final responses

3. **View Results**
   - Access anonymized feedback in "My Feedback"
   - Download Excel reports
   - Track completion progress

### For Managers

1. **Approve Nominations**
   - Review team member requests
   - Approve or reject with reasons
   - Consider reviewer workload and relationship accuracy

### For HR

1. **Create Review Cycles**
   - Set nomination, approval, and feedback deadlines
   - Monitor cycle progress
   - Send reminders to non-responders

2. **Manage Process**
   - Track completion rates
   - Send bulk or individual reminders
   - Generate progress reports

## Question Sets by Relationship Type

### Peers/Internal Stakeholders/Managers
- Collaboration, Communication, Reliability, Ownership ratings
- Open feedback on strengths and improvement areas

### Direct Reportees (Leadership Evaluation)
- Approachability, Openness to feedback, Clarity, Communication ratings
- Leadership effectiveness feedback

### External Stakeholders
- Professionalism, Reliability, Responsiveness, Understanding ratings
- Quality of delivery and collaboration examples

## Security Features

- **Password Hashing**: Secure bcrypt encryption
- **Role-Based Access**: Granular permission control
- **Anonymized Feedback**: Reviewers remain anonymous
- **Nomination Limits**: Prevents reviewer overload (max 4 per person)
- **Rejection Tracking**: Prevents re-nomination of rejected reviewers

## Workflow Timeline

### Week 1: Nomination Phase
- Employees submit 3-5 reviewer nominations
- System enforces min/max limits and permissions

### Week 2: Manager Approval Phase  
- Managers review and approve/reject nominations
- Approved requests sent to reviewers

### Weeks 3-5: Feedback Collection Phase
- Reviewers complete feedback forms
- Draft saving and reminder system active

### Week 5: Results Processing Phase
- Completed feedback compiled and shared
- Excel export available for employees

## Technical Architecture

- **Frontend**: Streamlit with role-based navigation
- **Database**: Turso (SQLite-compatible) with connection pooling
- **Authentication**: bcrypt password hashing + session management
- **Email**: SMTP integration for notifications
- **Export**: Excel generation with openpyxl

## File Structure

```
360_feedback_app/
├── main.py                          # Main app with navigation
├── login.py                         # Authentication page
├── password_setup.py                # First-time password setup
├── services/
│   ├── db_helper.py                # Database operations
│   ├── auth_service.py             # Authentication logic
│   └── email_service.py            # Email notifications
├── screens/
│   ├── employee/                   # Employee screens
│   ├── manager/                    # Manager screens
│   ├── hr/                         # HR screens
│   └── admin/                      # Admin screens
└── .streamlit/
    └── secrets.toml                # Database & email config
```

## Deployment

### Streamlit Cloud
1. Push code to GitHub repository
2. Connect Streamlit Cloud to repository
3. Add secrets in Streamlit Cloud dashboard
4. Deploy application

### Environment Variables
Required secrets:
- `DB_URL`: Turso database URL
- `AUTH_TOKEN`: Turso authentication token
- `email.*`: SMTP configuration (optional)

## Support & Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify Turso credentials in secrets.toml
   - Check network connectivity

2. **Login Problems**
   - Use "Set Password" for first-time users
   - Verify email exists in users table

3. **Email Issues**
   - Configure SMTP settings in secrets.toml
   - Use app-specific passwords for Gmail

### Admin Tasks

- **Add New Users**: Use Admin > User Management
- **Assign Roles**: Use HR > Manage Employees
- **Create Cycles**: Use HR Dashboard > Create New Review Cycle
- **System Health**: Use Admin > System Settings

## License

Internal use only - ProjectTech4Dev Organization

---

For technical support, contact your system administrator.