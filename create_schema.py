#!/usr/bin/env python3
"""
Script to create the database schema for the 360 Feedback Application
"""

from services.db_helper import get_connection

def create_schema():
    conn = get_connection()
    
    # SQL statements to create tables
    schema_sql = [
        # 1. Users table
        """
        CREATE TABLE IF NOT EXISTS users (
            user_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            vertical TEXT,
            designation TEXT,
            reporting_manager_email TEXT,
            password_hash TEXT NULL,
            password_reset_token TEXT NULL,
            password_reset_expires DATETIME NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 2. Roles table
        """
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 3. User role assignments
        """
        CREATE TABLE IF NOT EXISTS user_roles (
            user_type_id INTEGER,
            role_id INTEGER,
            assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_type_id, role_id),
            FOREIGN KEY (user_type_id) REFERENCES users (user_type_id),
            FOREIGN KEY (role_id) REFERENCES roles (role_id)
        );
        """,
        
        # 4. Review cycles
        """
        CREATE TABLE IF NOT EXISTS review_cycles (
            cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_name TEXT NOT NULL,
            nomination_start_date DATE NOT NULL,
            nomination_deadline DATE NOT NULL,
            approval_deadline DATE NOT NULL, 
            feedback_deadline DATE NOT NULL,
            results_deadline DATE NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (user_type_id)
        );
        """,
        
        # 5. Feedback requests
        """
        CREATE TABLE IF NOT EXISTS feedback_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER NOT NULL,
            requester_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            relationship_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending_approval',
            approval_status TEXT DEFAULT 'pending',
            approved_by INTEGER NULL,
            rejection_reason TEXT NULL,
            approval_date DATETIME NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME NULL,
            FOREIGN KEY (cycle_id) REFERENCES review_cycles (cycle_id),
            FOREIGN KEY (requester_id) REFERENCES users (user_type_id),
            FOREIGN KEY (reviewer_id) REFERENCES users (user_type_id),
            FOREIGN KEY (approved_by) REFERENCES users (user_type_id)
        );
        """,
        
        # 6. Feedback questions
        """
        CREATE TABLE IF NOT EXISTS feedback_questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'rating',
            relationship_type TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 7. Draft responses
        """
        CREATE TABLE IF NOT EXISTS draft_responses (
            draft_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            response_value TEXT,
            rating_value INTEGER,
            saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES feedback_requests (request_id),
            FOREIGN KEY (question_id) REFERENCES feedback_questions (question_id),
            UNIQUE(request_id, question_id)
        );
        """,
        
        # 8. Final feedback responses
        """
        CREATE TABLE IF NOT EXISTS feedback_responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            response_value TEXT,
            rating_value INTEGER,
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES feedback_requests (request_id),
            FOREIGN KEY (question_id) REFERENCES feedback_questions (question_id)
        );
        """,
        
        # 9. Reviewer nomination tracking
        """
        CREATE TABLE IF NOT EXISTS reviewer_nominations (
            nomination_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reviewer_id INTEGER NOT NULL,
            nomination_count INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reviewer_id) REFERENCES users (user_type_id),
            UNIQUE(reviewer_id)
        );
        """,
        
        # 10. Rejected nominations
        """
        CREATE TABLE IF NOT EXISTS rejected_nominations (
            rejection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER NOT NULL,
            rejected_reviewer_id INTEGER NOT NULL,
            rejected_by INTEGER NOT NULL,
            rejection_reason TEXT,
            rejected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (requester_id) REFERENCES users (user_type_id),
            FOREIGN KEY (rejected_reviewer_id) REFERENCES users (user_type_id),
            FOREIGN KEY (rejected_by) REFERENCES users (user_type_id),
            UNIQUE(requester_id, rejected_reviewer_id)
        );
        """,
        
        # 11. Email logs
        """
        CREATE TABLE IF NOT EXISTS email_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT NOT NULL,
            email_type TEXT NOT NULL,
            subject TEXT,
            status TEXT DEFAULT 'pending',
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT NULL
        );
        """
    ]
    
    print("Creating database schema...")
    
    try:
        for sql in schema_sql:
            conn.execute(sql)
        
        conn.commit()
        print("✅ Database schema created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
        return False

if __name__ == "__main__":
    create_schema()