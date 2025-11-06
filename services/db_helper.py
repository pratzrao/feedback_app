import libsql_experimental as libsql
import streamlit as st
from datetime import datetime

db_url = st.secrets["DB_URL"]
auth_token = st.secrets["AUTH_TOKEN"]

if not db_url or not auth_token:
    raise Exception("Database URL or Auth Token is missing. Check your .streamlit/secrets.toml file.")

_connection = None

def get_connection():
    global _connection
    try:
        if _connection is None:
            _connection = libsql.connect(database=db_url, auth_token=auth_token)
            print("Established a new database connection.")
        else:
            try:
                _connection.execute("SELECT 1;")
                print("Connection is healthy.")
            except Exception as conn_error:
                if "STREAM_EXPIRED" in str(conn_error):
                    print("Connection stream expired. Reinitializing connection.")
                    _connection = libsql.connect(database=db_url, auth_token=auth_token)
                else:
                    raise conn_error
    except Exception as e:
        print(f"Error establishing connection: {e}")
        _connection = libsql.connect(database=db_url, auth_token=auth_token)
    return _connection

def fetch_user_by_email(email):
    """Fetch user by email for authentication."""
    conn = get_connection()
    query = "SELECT * FROM users WHERE email = ? AND is_active = 1;"
    try:
        result = conn.execute(query, (email,))
        user = result.fetchone()
        if user:
            return {
                "user_type_id": user[0],
                "email": user[1],
                "first_name": user[2],
                "last_name": user[3],
                "vertical": user[4],
                "designation": user[5],
                "reporting_manager_email": user[6],
                "password_hash": user[7]
            }
        return None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def fetch_user_roles(user_type_id):
    """Fetch roles for a specific user."""
    conn = get_connection()
    query = """
        SELECT r.role_id, r.role_name, r.description 
        FROM roles r
        JOIN user_roles ur ON r.role_id = ur.role_id
        WHERE ur.user_type_id = ?;
    """
    try:
        result = conn.execute(query, (user_type_id,))
        roles = result.fetchall()
        return [{"role_id": row[0], "role_name": row[1], "description": row[2]} for row in roles]
    except Exception as e:
        print(f"Error fetching user roles: {e}")
        return []

def set_user_password(email, password_hash):
    """Set password for first-time login."""
    conn = get_connection()
    query = "UPDATE users SET password_hash = ? WHERE email = ?"
    try:
        conn.execute(query, (password_hash, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting password: {e}")
        return False

def get_users_for_selection(exclude_user_id=None, requester_user_id=None):
    """Get list of users for reviewer selection with nomination tracking and rejection filtering."""
    conn = get_connection()
    query = """
        SELECT u.user_type_id, u.first_name, u.last_name, u.vertical, u.designation,
               COALESCE(rn.nomination_count, 0) as nomination_count,
               CASE WHEN rej.rejected_reviewer_id IS NOT NULL THEN 1 ELSE 0 END as is_rejected
        FROM users u
        LEFT JOIN reviewer_nominations rn ON u.user_type_id = rn.reviewer_id
        LEFT JOIN rejected_nominations rej ON u.user_type_id = rej.rejected_reviewer_id 
            AND rej.requester_id = ?
        WHERE u.is_active = 1
    """
    params = [requester_user_id or 0]
    
    if exclude_user_id:
        query += " AND u.user_type_id != ?"
        params.append(exclude_user_id)
    
    query += " ORDER BY u.first_name, u.last_name"
    
    try:
        result = conn.execute(query, params)
        users = []
        for row in result.fetchall():
            is_over_limit = row[5] >= 4
            is_rejected = row[6] == 1
            users.append({
                "user_type_id": row[0],
                "name": f"{row[1]} {row[2]}",
                "vertical": row[3],
                "designation": row[4],
                "nomination_count": row[5],
                "is_over_limit": is_over_limit,
                "is_rejected": is_rejected,
                "is_selectable": not (is_over_limit or is_rejected)
            })
        return users
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

def get_manager_level_from_designation(designation):
    """Get numeric manager level from designation text."""
    if not designation:
        return 0
    
    designation_lower = designation.lower()
    
    if 'founder' in designation_lower:
        return 5
    elif 'associate director' in designation_lower:
        return 4  
    elif 'director' in designation_lower:
        return 3
    elif 'manager' in designation_lower or 'sr. manager' in designation_lower:
        return 2
    elif 'lead' in designation_lower:
        return 1
    else:
        return 0

def check_external_stakeholder_permission(user_id):
    """Check if user has manager level or above to request external stakeholder feedback."""
    conn = get_connection()
    query = "SELECT designation FROM users WHERE user_type_id = ?"
    try:
        result = conn.execute(query, (user_id,))
        user = result.fetchone()
        if user:
            manager_level = get_manager_level_from_designation(user[0])
            return manager_level >= 2
        return False
    except Exception as e:
        print(f"Error checking external stakeholder permission: {e}")
        return False

def get_active_review_cycle():
    """Get the currently active review cycle."""
    conn = get_connection()
    query = """
        SELECT cycle_id, cycle_name, nomination_start_date, nomination_deadline, 
               approval_deadline, feedback_deadline, results_deadline, created_at
        FROM review_cycles 
        WHERE is_active = 1
        LIMIT 1
    """
    try:
        result = conn.execute(query)
        cycle = result.fetchone()
        if cycle:
            return {
                'cycle_id': cycle[0],
                'cycle_name': cycle[1],
                'nomination_start_date': cycle[2],
                'nomination_deadline': cycle[3],
                'approval_deadline': cycle[4],
                'feedback_deadline': cycle[5],
                'results_deadline': cycle[6],
                'created_at': cycle[7]
            }
        return None
    except Exception as e:
        print(f"Error fetching active cycle: {e}")
        return None

def create_feedback_requests_with_approval(requester_id, reviewer_data):
    """Create feedback requests that require manager approval."""
    conn = get_connection()
    try:
        # Get active cycle
        active_cycle = get_active_review_cycle()
        if not active_cycle:
            return False, "No active review cycle found"
        
        cycle_id = active_cycle['cycle_id']
        
        # Get requester's manager
        manager_query = """
            SELECT m.user_type_id 
            FROM users u 
            JOIN users m ON u.reporting_manager_email = m.email 
            WHERE u.user_type_id = ?
        """
        manager_result = conn.execute(manager_query, (requester_id,))
        manager = manager_result.fetchone()
        
        if not manager:
            return False, "No reporting manager found"
        
        manager_id = manager[0]
        
        # Create requests for each reviewer
        for reviewer_id, relationship_type in reviewer_data:
            request_query = """
                INSERT INTO feedback_requests 
                (cycle_id, requester_id, reviewer_id, relationship_type, status, approval_status) 
                VALUES (?, ?, ?, ?, 'pending_approval', 'pending')
            """
            conn.execute(request_query, (cycle_id, requester_id, reviewer_id, relationship_type))
            
            # Update nomination count
            nomination_query = """
                INSERT INTO reviewer_nominations (reviewer_id, nomination_count) 
                VALUES (?, 1)
                ON CONFLICT(reviewer_id) DO UPDATE SET
                nomination_count = nomination_count + 1,
                last_updated = CURRENT_TIMESTAMP
            """
            conn.execute(nomination_query, (reviewer_id,))
        
        conn.commit()
        return True, "Requests submitted for manager approval"
    except Exception as e:
        print(f"Error creating feedback requests: {e}")
        conn.rollback()
        return False, str(e)

def get_pending_approvals_for_manager(manager_id):
    """Get feedback requests pending approval for a manager."""
    conn = get_connection()
    query = """
        SELECT fr.request_id, fr.requester_id, fr.reviewer_id, fr.relationship_type,
               req.first_name as requester_name, req.last_name as requester_surname,
               rev.first_name as reviewer_name, rev.last_name as reviewer_surname,
               rev.vertical, rev.designation, fr.created_at
        FROM feedback_requests fr
        JOIN users req ON fr.requester_id = req.user_type_id
        JOIN users rev ON fr.reviewer_id = rev.user_type_id
        JOIN users mgr ON req.reporting_manager_email = mgr.email
        WHERE mgr.user_type_id = ? AND fr.approval_status = 'pending'
        ORDER BY fr.created_at ASC
    """
    try:
        result = conn.execute(query, (manager_id,))
        return result.fetchall()
    except Exception as e:
        print(f"Error fetching pending approvals: {e}")
        return []

def approve_reject_feedback_request(request_id, manager_id, action, rejection_reason=None):
    """Approve or reject a feedback request."""
    conn = get_connection()
    try:
        if action == 'approve':
            update_query = """
                UPDATE feedback_requests 
                SET approval_status = 'approved', status = 'approved', 
                    approved_by = ?, approval_date = CURRENT_TIMESTAMP
                WHERE request_id = ?
            """
            conn.execute(update_query, (manager_id, request_id))
                
        elif action == 'reject':
            update_query = """
                UPDATE feedback_requests 
                SET approval_status = 'rejected', status = 'rejected',
                    approved_by = ?, approval_date = CURRENT_TIMESTAMP,
                    rejection_reason = ?
                WHERE request_id = ?
            """
            conn.execute(update_query, (manager_id, rejection_reason, request_id))
            
            # Add to rejected nominations
            request_details = conn.execute(
                "SELECT requester_id, reviewer_id FROM feedback_requests WHERE request_id = ?", 
                (request_id,)
            ).fetchone()
            if request_details:
                reject_query = """
                    INSERT INTO rejected_nominations 
                    (requester_id, rejected_reviewer_id, rejected_by, rejection_reason)
                    VALUES (?, ?, ?, ?)
                """
                conn.execute(reject_query, (
                    request_details[0], request_details[1], manager_id, rejection_reason
                ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error processing approval/rejection: {e}")
        conn.rollback()
        return False

def get_pending_reviews_for_user(user_id):
    """Get feedback requests pending for a user to complete."""
    conn = get_connection()
    query = """
        SELECT fr.request_id, req.first_name, req.last_name, req.vertical, 
               fr.created_at, fr.relationship_type,
               COUNT(dr.draft_id) as draft_count
        FROM feedback_requests fr
        JOIN users req ON fr.requester_id = req.user_type_id
        LEFT JOIN draft_responses dr ON fr.request_id = dr.request_id
        WHERE fr.reviewer_id = ? AND fr.status = 'approved'
        GROUP BY fr.request_id, req.first_name, req.last_name, req.vertical, fr.created_at, fr.relationship_type
        ORDER BY fr.created_at ASC
    """
    try:
        result = conn.execute(query, (user_id,))
        return result.fetchall()
    except Exception as e:
        print(f"Error fetching pending reviews: {e}")
        return []

def get_questions_by_relationship_type(relationship_type):
    """Get questions for a specific relationship type."""
    conn = get_connection()
    query = """
        SELECT question_id, question_text, question_type, sort_order
        FROM feedback_questions 
        WHERE relationship_type = ? AND is_active = 1
        ORDER BY sort_order ASC
    """
    try:
        result = conn.execute(query, (relationship_type,))
        return result.fetchall()
    except Exception as e:
        print(f"Error fetching questions: {e}")
        return []

def get_draft_responses(request_id):
    """Get draft responses for a request."""
    conn = get_connection()
    query = """
        SELECT question_id, response_value, rating_value
        FROM draft_responses 
        WHERE request_id = ?
    """
    try:
        result = conn.execute(query, (request_id,))
        drafts = {}
        for row in result.fetchall():
            drafts[row[0]] = {
                'response_value': row[1],
                'rating_value': row[2]
            }
        return drafts
    except Exception as e:
        print(f"Error fetching draft responses: {e}")
        return {}

def save_draft_response(request_id, question_id, response_value, rating_value=None):
    """Save draft response for partial completion."""
    conn = get_connection()
    query = """
        INSERT INTO draft_responses (request_id, question_id, response_value, rating_value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(request_id, question_id) DO UPDATE SET
        response_value = excluded.response_value,
        rating_value = excluded.rating_value,
        saved_at = CURRENT_TIMESTAMP
    """
    try:
        conn.execute(query, (request_id, question_id, response_value, rating_value))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving draft: {e}")
        return False

def submit_final_feedback(request_id, responses):
    """Submit completed feedback and move from draft to final."""
    conn = get_connection()
    try:
        # Insert final responses
        for question_id, response_data in responses.items():
            response_query = """
                INSERT INTO feedback_responses (request_id, question_id, response_value, rating_value)
                VALUES (?, ?, ?, ?)
            """
            conn.execute(response_query, (
                request_id, 
                question_id, 
                response_data.get('response_value'), 
                response_data.get('rating_value')
            ))
        
        # Update request status
        update_query = """
            UPDATE feedback_requests 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE request_id = ?
        """
        conn.execute(update_query, (request_id,))
        
        # Clear draft responses
        clear_draft_query = "DELETE FROM draft_responses WHERE request_id = ?"
        conn.execute(clear_draft_query, (request_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        conn.rollback()
        return False

def get_anonymized_feedback_for_user(user_id):
    """Get completed feedback received by a user (anonymized - no reviewer names)."""
    conn = get_connection()
    query = """
        SELECT fr.request_id, fr.relationship_type, fr.completed_at,
               fq.question_text, fres.response_value, fres.rating_value, fq.question_type
        FROM feedback_requests fr
        JOIN feedback_responses fres ON fr.request_id = fres.request_id
        JOIN feedback_questions fq ON fres.question_id = fq.question_id
        WHERE fr.requester_id = ? AND fr.status = 'completed'
        ORDER BY fr.request_id, fq.sort_order ASC
    """
    try:
        result = conn.execute(query, (user_id,))
        feedback_groups = {}
        for row in result.fetchall():
            request_id = row[0]
            if request_id not in feedback_groups:
                feedback_groups[request_id] = {
                    'relationship_type': row[1],
                    'completed_at': row[2],
                    'responses': []
                }
            feedback_groups[request_id]['responses'].append({
                'question_text': row[3],
                'response_value': row[4],
                'rating_value': row[5],
                'question_type': row[6]
            })
        return feedback_groups
    except Exception as e:
        print(f"Error fetching anonymized feedback: {e}")
        return {}

def get_feedback_progress_for_user(user_id):
    """Get feedback request progress for a user showing anonymized completion status."""
    conn = get_connection()
    query = """
        SELECT 
            COUNT(*) as total_requests,
            SUM(CASE WHEN fr.status = 'completed' THEN 1 ELSE 0 END) as completed_requests,
            SUM(CASE WHEN fr.status = 'approved' THEN 1 ELSE 0 END) as pending_requests,
            SUM(CASE WHEN fr.approval_status = 'pending' THEN 1 ELSE 0 END) as awaiting_approval
        FROM feedback_requests fr
        WHERE fr.requester_id = ? AND fr.status != 'rejected'
    """
    try:
        result = conn.execute(query, (user_id,))
        progress = result.fetchone()
        if progress:
            return {
                'total_requests': progress[0],
                'completed_requests': progress[1], 
                'pending_requests': progress[2],
                'awaiting_approval': progress[3]
            }
        return {'total_requests': 0, 'completed_requests': 0, 'pending_requests': 0, 'awaiting_approval': 0}
    except Exception as e:
        print(f"Error fetching feedback progress: {e}")
        return {'total_requests': 0, 'completed_requests': 0, 'pending_requests': 0, 'awaiting_approval': 0}

def generate_feedback_excel_data(user_id):
    """Generate Excel-ready data for a user's feedback."""
    feedback_data = get_anonymized_feedback_for_user(user_id)
    
    excel_rows = []
    
    for request_id, feedback in feedback_data.items():
        relationship_type = feedback['relationship_type']
        completed_at = feedback['completed_at']
        
        for response in feedback['responses']:
            excel_rows.append({
                'Review_Number': f"Review_{request_id}",
                'Relationship_Type': relationship_type.replace('_', ' ').title(),
                'Question': response['question_text'],
                'Question_Type': response['question_type'],
                'Rating': response['rating_value'] if response['rating_value'] else '',
                'Text_Response': response['response_value'] if response['response_value'] else '',
                'Completed_Date': completed_at
            })
    
    return excel_rows

def create_new_review_cycle(cycle_name, nomination_start, nomination_deadline, approval_deadline, feedback_deadline, results_deadline, created_by):
    """Create a new review cycle (HR function)."""
    conn = get_connection()
    try:
        # Deactivate any existing active cycles
        deactivate_query = "UPDATE review_cycles SET is_active = 0"
        conn.execute(deactivate_query)
        
        # Create new cycle
        insert_query = """
            INSERT INTO review_cycles 
            (cycle_name, nomination_start_date, nomination_deadline, approval_deadline, 
             feedback_deadline, results_deadline, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """
        conn.execute(insert_query, (
            cycle_name, nomination_start, nomination_deadline, approval_deadline,
            feedback_deadline, results_deadline, created_by
        ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating review cycle: {e}")
        conn.rollback()
        return False

def get_current_cycle_phase():
    """Determine which phase of the review cycle we're currently in."""
    from datetime import date
    
    cycle = get_active_review_cycle()
    if not cycle:
        return "No active cycle"
    
    today = date.today()
    
    if today <= cycle['nomination_deadline']:
        return "Nomination Phase"
    elif today <= cycle['approval_deadline']:
        return "Manager Approval Phase"
    elif today <= cycle['feedback_deadline']:
        return "Feedback Collection Phase"
    elif today <= cycle['results_deadline']:
        return "Results Processing Phase"
    else:
        return "Cycle Complete"

def get_hr_dashboard_metrics():
    """Get comprehensive metrics for HR dashboard."""
    conn = get_connection()
    try:
        metrics = {}
        
        # Total users
        total_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()[0]
        
        # Pending feedback requests
        pending_requests = conn.execute(
            "SELECT COUNT(*) FROM feedback_requests WHERE status = 'approved'"
        ).fetchone()[0]
        
        # Completed feedback this month
        completed_this_month = conn.execute("""
            SELECT COUNT(*) FROM feedback_requests 
            WHERE status = 'completed' AND DATE(completed_at) >= DATE('now', 'start of month')
        """).fetchone()[0]
        
        # Users with incomplete reviews
        incomplete_reviews = conn.execute("""
            SELECT COUNT(DISTINCT reviewer_id) FROM feedback_requests 
            WHERE status = 'approved'
        """).fetchone()[0]
        
        metrics.update({
            'total_users': total_users,
            'pending_requests': pending_requests,
            'completed_this_month': completed_this_month,
            'users_with_incomplete': incomplete_reviews
        })
        
        return metrics
    except Exception as e:
        print(f"Error fetching HR metrics: {e}")
        return {}

def get_users_with_pending_reviews():
    """Get users who have pending reviews to complete."""
    conn = get_connection()
    query = """
        SELECT u.user_type_id, u.first_name, u.last_name, u.vertical, u.email,
               COUNT(fr.request_id) as pending_count
        FROM users u
        JOIN feedback_requests fr ON u.user_type_id = fr.reviewer_id
        WHERE fr.status = 'approved' AND u.is_active = 1
        GROUP BY u.user_type_id, u.first_name, u.last_name, u.vertical, u.email
        ORDER BY pending_count DESC, u.first_name
    """
    try:
        result = conn.execute(query)
        users = []
        for row in result.fetchall():
            users.append({
                'user_type_id': row[0],
                'name': f"{row[1]} {row[2]}",
                'vertical': row[3],
                'email': row[4],
                'pending_count': row[5]
            })
        return users
    except Exception as e:
        print(f"Error fetching users with pending reviews: {e}")
        return []