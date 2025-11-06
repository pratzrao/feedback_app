#!/usr/bin/env python3
"""
Simple script to insert data using parameterized queries
"""

from services.db_helper import get_connection

def insert_data():
    conn = get_connection()
    
    try:
        print("Inserting data...")
        
        # 1. Insert roles
        role_data = [
            ('super_admin', 'System administrator with full access'),
            ('hr', 'HR personnel with dashboard and management access'),
            ('employee', 'Regular employee with feedback access')
        ]
        
        for role in role_data:
            conn.execute("INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)", role)
        print("✅ Roles inserted")
        
        # 2. Insert feedback questions
        questions_data = [
            # Peer questions
            ('Collaboration', 'rating', 'peer', 1),
            ('Communication', 'rating', 'peer', 2),
            ('Reliability', 'rating', 'peer', 3),
            ('Ownership (Trust)', 'rating', 'peer', 4),
            ('One or two things you value or appreciate about how this person works — things you would like them to continue doing.', 'text', 'peer', 5),
            ('One or two things you feel this person could get even better at, to perform even more effectively in their role.', 'text', 'peer', 6),
            
            # Internal stakeholder questions (same as peer)
            ('Collaboration', 'rating', 'internal_stakeholder', 1),
            ('Communication', 'rating', 'internal_stakeholder', 2),
            ('Reliability', 'rating', 'internal_stakeholder', 3),
            ('Ownership (Trust)', 'rating', 'internal_stakeholder', 4),
            ('One or two things you value or appreciate about how this person works — things you would like them to continue doing.', 'text', 'internal_stakeholder', 5),
            ('One or two things you feel this person could get even better at, to perform even more effectively in their role.', 'text', 'internal_stakeholder', 6),
            
            # Manager questions (same as peer)
            ('Collaboration', 'rating', 'manager', 1),
            ('Communication', 'rating', 'manager', 2),
            ('Reliability', 'rating', 'manager', 3),
            ('Ownership (Trust)', 'rating', 'manager', 4),
            ('One or two things you value or appreciate about how this person works — things you would like them to continue doing.', 'text', 'manager', 5),
            ('One or two things you feel this person could get even better at, to perform even more effectively in their role.', 'text', 'manager', 6),
            
            # Direct reportee questions (leadership)
            ('Approachability', 'rating', 'direct_reportee', 1),
            ('Openness to feedback (Openness & Trust)', 'rating', 'direct_reportee', 2),
            ('Clarity in direction', 'rating', 'direct_reportee', 3),
            ('Effectiveness in communication', 'rating', 'direct_reportee', 4),
            ('A short note on what helps or could help you work better under their leadership.', 'text', 'direct_reportee', 5),
            
            # External stakeholder questions
            ('Professionalism', 'rating', 'external_stakeholder', 1),
            ('Reliability (Trust & Excellence)', 'rating', 'external_stakeholder', 2),
            ('Responsiveness', 'rating', 'external_stakeholder', 3),
            ('Clarity in communication (Openness & Collaboration)', 'rating', 'external_stakeholder', 4),
            ('Understanding of your needs', 'rating', 'external_stakeholder', 5),
            ('Quality of delivery (Social-Sector Focus & Innovation)', 'rating', 'external_stakeholder', 6),
            ('Share your thoughts on how this person collaborates, communicates, and delivers in your interactions. Any examples of what worked well or areas for growth?', 'text', 'external_stakeholder', 7)
        ]
        
        for question in questions_data:
            conn.execute("INSERT OR IGNORE INTO feedback_questions (question_text, question_type, relationship_type, sort_order) VALUES (?, ?, ?, ?)", question)
        print("✅ Questions inserted")
        
        # 3. Insert users - handle founder separately
        users_data = [
            ('Siddhant', 'Singh', 'siddhant@projecttech4dev.org', 'Dalgo', 'Team Lead', 'pradeep@projecttech4dev.org'),
            ('Abhishek', 'Nair', 'abhishek@projecttech4dev.org', 'Dalgo', 'Manager', 'ashwin@projecttech4dev.org'),
            ('Sneha', 'Trivedi', 'sneha@projecttech4dev.org', 'Glific', 'Team Lead', 'radhika@projecttech4dev.org'),
            ('Erica', 'Arya', 'erica@projecttech4dev.org', 'HOP', 'Director', 'lobo@projecttech4dev.org'),
            ('Dwibhashi', 'Krishnapriya', 'dwibhashi@projecttech4dev.org', 'Glific', 'Manager', 'radhika@projecttech4dev.org'),
            ('Radhika', '', 'radhika@projecttech4dev.org', 'Glific', 'Associate Director', 'erica@projecttech4dev.org'),
            ('Ashwin', '', 'ashwin@projecttech4dev.org', 'Dalgo', 'Associate Director', 'erica@projecttech4dev.org'),
            ('Pradeep', 'Kaushik', 'pradeep@projecttech4dev.org', 'Dalgo', 'Associate Director', 'ashwin@projecttech4dev.org'),
            ('Shijith', 'K', 'shijith@projecttech4dev.org', 'Glific', 'Team Lead', 'radhika@projecttech4dev.org')
        ]
        
        for user in users_data:
            conn.execute("INSERT OR IGNORE INTO users (first_name, last_name, email, vertical, designation, reporting_manager_email) VALUES (?, ?, ?, ?, ?, ?)", user)
        
        # Insert founder separately (no manager)
        conn.execute("INSERT OR IGNORE INTO users (first_name, last_name, email, vertical, designation) VALUES (?, ?, ?, ?, ?)", 
                    ('Donald', 'Lobo', 'lobo@projecttech4dev.org', '', 'Founder'))
        print("✅ Users inserted")
        
        # 4. Assign roles
        # All users get employee role
        users = conn.execute("SELECT user_type_id FROM users").fetchall()
        for user in users:
            conn.execute("INSERT OR IGNORE INTO user_roles (user_type_id, role_id) VALUES (?, 3)", (user[0],))
        
        # Erica gets HR role  
        conn.execute("INSERT OR IGNORE INTO user_roles (user_type_id, role_id) SELECT user_type_id, 2 FROM users WHERE email = 'erica@projecttech4dev.org'")
        
        # Donald gets super admin role
        conn.execute("INSERT OR IGNORE INTO user_roles (user_type_id, role_id) SELECT user_type_id, 1 FROM users WHERE email = 'lobo@projecttech4dev.org'")
        
        print("✅ Roles assigned")
        
        conn.commit()
        print("🎉 All data inserted successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False

if __name__ == "__main__":
    insert_data()