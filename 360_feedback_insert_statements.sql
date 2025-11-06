-- 360-Degree Feedback App - Database Insert Statements
-- Run these after creating the tables with the CREATE statements from the specification

-- 1. Insert roles (required for user authentication)
INSERT INTO roles (role_name, description) VALUES 
('super_admin', 'System administrator with full access'),
('hr', 'HR personnel with dashboard and management access'),
('employee', 'Regular employee with feedback access');

-- 2. Insert feedback questions for different relationship types

-- Questions for Peers and Internal Stakeholders (collaboration focus)
INSERT INTO feedback_questions (question_text, question_type, relationship_type, sort_order) VALUES 
('Collaboration', 'rating', 'peer', 1),
('Communication', 'rating', 'peer', 2),
('Reliability', 'rating', 'peer', 3),
('Ownership (Trust)', 'rating', 'peer', 4),
('One or two things you value or appreciate about how this person works — things you'd like them to continue doing.', 'text', 'peer', 5),
('One or two things you feel this person could get even better at, to perform even more effectively in their role.', 'text', 'peer', 6);

INSERT INTO feedback_questions (question_text, question_type, relationship_type, sort_order) VALUES 
('Collaboration', 'rating', 'internal_stakeholder', 1),
('Communication', 'rating', 'internal_stakeholder', 2),
('Reliability', 'rating', 'internal_stakeholder', 3),
('Ownership (Trust)', 'rating', 'internal_stakeholder', 4),
('One or two things you value or appreciate about how this person works — things you'd like them to continue doing.', 'text', 'internal_stakeholder', 5),
('One or two things you feel this person could get even better at, to perform even more effectively in their role.', 'text', 'internal_stakeholder', 6);

-- Questions for Managers
INSERT INTO feedback_questions (question_text, question_type, relationship_type, sort_order) VALUES 
('Collaboration', 'rating', 'manager', 1),
('Communication', 'rating', 'manager', 2),
('Reliability', 'rating', 'manager', 3),
('Ownership (Trust)', 'rating', 'manager', 4),
('One or two things you value or appreciate about how this person works — things you'd like them to continue doing.', 'text', 'manager', 5),
('One or two things you feel this person could get even better at, to perform even more effectively in their role.', 'text', 'manager', 6);

-- Questions for Direct Reportees (leadership evaluation)
INSERT INTO feedback_questions (question_text, question_type, relationship_type, sort_order) VALUES 
('Approachability', 'rating', 'direct_reportee', 1),
('Openness to feedback (Openness & Trust)', 'rating', 'direct_reportee', 2),
('Clarity in direction', 'rating', 'direct_reportee', 3),
('Effectiveness in communication', 'rating', 'direct_reportee', 4),
('A short note on what helps or could help you work better under their leadership.', 'text', 'direct_reportee', 5);

-- Questions for External Stakeholders
INSERT INTO feedback_questions (question_text, question_type, relationship_type, sort_order) VALUES 
('Professionalism', 'rating', 'external_stakeholder', 1),
('Reliability (Trust & Excellence)', 'rating', 'external_stakeholder', 2),
('Responsiveness', 'rating', 'external_stakeholder', 3),
('Clarity in communication (Openness & Collaboration)', 'rating', 'external_stakeholder', 4),
('Understanding of your needs', 'rating', 'external_stakeholder', 5),
('Quality of delivery (Social-Sector Focus & Innovation)', 'rating', 'external_stakeholder', 6),
('Share your thoughts on how this person collaborates, communicates, and delivers in your interactions. Any examples of what worked well or areas for growth?', 'text', 'external_stakeholder', 7);

-- 3. Insert users from Employee_list.csv

INSERT INTO users (first_name, last_name, email, vertical, designation, reporting_manager_email) VALUES 
('Siddhant', 'Singh', 'siddhant@projecttech4dev.org', 'Dalgo', 'Team Lead', 'pradeep@projecttech4dev.org'),
('Abhishek', 'Nair', 'abhishek@projecttech4dev.org', 'Dalgo', 'Manager', 'ashwin@projecttech4dev.org'),
('Sneha', 'Trivedi', 'sneha@projecttech4dev.org', 'Glific', 'Team Lead', 'radhika@projecttech4dev.org'),
('Erica', 'Arya', 'erica@projecttech4dev.org', 'HOP', 'Director', 'lobo@projecttech4dev.org'),
('Dwibhashi', 'Krishnapriya', 'dwibhashi@projecttech4dev.org', 'Glific', 'Manager', 'radhika@projecttech4dev.org'),
('Mohd', 'Shamoon', 'mohd@projecttech4dev.org', 'fcxo', 'Team Lead', 'thomas@projecttech4dev.org'),
('Akhilesh', 'Negi', 'akhilesh@projecttech4dev.org', 'AI/LLM', 'Team Lead', 'kartikeya@projecttech4dev.org'),
('Amisha', 'Bisht', 'amisha@projecttech4dev.org', 'Glific', 'Analyst', 'shijith@projecttech4dev.org'),
('Tejas', 'Mahajan', 'tejas@projecttech4dev.org', 'Glific', 'Team Lead', 'radhika@projecttech4dev.org'),
('Sangeeta', 'Mishra', 'sangeeta@projecttech4dev.org', 'Glific', 'Associate', 'krishna@projecttech4dev.org'),
('Anandu', 'Pavanan', 'anandu@projecttech4dev.org', 'Glific', 'Team Lead', 'shijith@projecttech4dev.org'),
('Diana', 'Gomes', 'diana@projecttech4dev.org', 'TM', 'Manager', 'erica@projecttech4dev.org'),
('Vinod', '', 'vinod@projecttech4dev.org', 'fCxO', 'Associate Director', 'lobo@projecttech4dev.org'),
('Amit', 'Srivastava', 'amit@projecttech4dev.org', 'Finance', 'Team Lead', 'erica@projecttech4dev.org'),
('Thomas', '', 'thomas@projecttech4dev.org', 'fCxO', 'Associate Director', 'vinod@projecttech4dev.org'),
('Devi', 'A S L', 'devi@projecttech4dev.org', 'fCxO', 'Consultant', 'vinod@projecttech4dev.org'),
('Radhika', '', 'radhika@projecttech4dev.org', 'Glific', 'Associate Director', 'erica@projecttech4dev.org'),
('Ashwin', '', 'ashwin@projecttech4dev.org', 'Dalgo', 'Associate Director', 'erica@projecttech4dev.org'),
('Aiswarya', '', 'aiswarya@projecttech4dev.org', 'Finance', 'Associate', 'amit@projecttech4dev.org'),
('Aishwarya', 'C S', 'aishwarya@projecttech4dev.org', 'Glific', 'Associate', 'sneha@projecttech4dev.org'),
('Akansha', '', 'akansha@projecttech4dev.org', 'Glific', 'Analyst', 'shijith@projecttech4dev.org'),
('Himanshu', 'Dube', 'himanshu@projecttech4dev.org', 'Dalgo', 'Associate', 'pradeep@projecttech4dev.org'),
('Priyesh', 'Kumar Sikariwal', 'priyesh@projecttech4dev.org', 'Dalgo', 'Associate', 'abhishek@projecttech4dev.org'),
('Nishika', 'Yadav', 'nishika@projecttech4dev.org', 'AI/LLM', 'Analyst', 'kartikeya@projecttech4dev.org'),
('Pratiksha', 'Rao', 'pratiksha@projecttech4dev.org', 'Dalgo', 'Analyst', 'anusha@projecttech4dev.org'),
('Antony', 'VJ', 'antony@projecttech4dev.org', 'fCxO', 'Associate Director', 'vinod@projecttech4dev.org'),
('Deepak', 'Nanda', 'deepak@projecttech4dev.org', 'Communications', 'Lead', 'erica@projecttech4dev.org'),
('Ninad', 'Khanolkar', 'ninad@projecttech4dev.org', 'Sashkt', 'Lead', 'erica@projecttech4dev.org'),
('Vijay', 'Rasquinha', 'vijay@projecttech4dev.org', 'fcxo', 'CTO', 'vinod@projecttech4dev.org'),
('Shijith', 'K', 'shijith@projecttech4dev.org', 'Glific', 'Team Lead', 'radhika@projecttech4dev.org'),
('Mohammed', 'Fawas', 'mohammed@projecttech4dev.org', 'Glific', 'Analyst', 'krishna@projecttech4dev.org'),
('Sakshi', 'Raut', 'sakshi@projecttech4dev.org', 'fcxo', 'Associate', 'antony@projecttech4dev.org'),
('Ashana', 'Shukla', 'ashana@projecttech4dev.org', 'Cohort', 'Manager', 'lobo@projecttech4dev.org'),
('Tanu', 'Prasad', 'tanu@projecttech4dev.org', 'Glific', 'Analyst', 'krishna@projecttech4dev.org'),
('Stuti', 'Nabazza', 'stuti@projecttech4dev.org', 'Dalgo', 'Team Lead', 'abhishek@projecttech4dev.org'),
('Aviraj', 'Gour', 'aviraj@projecttech4dev.org', 'AI/LLM', 'Associate', 'kartikeya@projecttech4dev.org'),
('Apeksha', 'Gangurde', 'apeksha@projecttech4dev.org', 'Sashkt', 'Analyst', 'ninad@projecttech4dev.org'),
('Priyanshu', '', 'priyanshu@projecttech4dev.org', 'Glific', 'Analyst', 'shijith@projecttech4dev.org'),
('Sheetal', 'Sridhar', 'sheetal@projecttech4dev.org', 'CoS', 'Team Lead', 'erica@projecttech4dev.org'),
('Ishan', 'Koradia', 'ishan@projecttech4dev.org', 'Dalgo', 'Team Lead', 'pradeep@projecttech4dev.org'),
('Ritabrata', 'Roy', 'ritabrata@projecttech4dev.org', 'Dalgo', 'Associate', 'anusha@projecttech4dev.org'),
('Pradeep', 'Kaushik', 'pradeep@projecttech4dev.org', 'Dalgo', 'Associate Director', 'ashwin@projecttech4dev.org'),
('Kartikeya', 'Pophali', 'kartikeya@projecttech4dev.org', 'AI/LLM', 'Sr. Manager', 'vijay@projecttech4dev.org'),
('Sushil', 'Kambampati', 'sushil@projecttech4dev.org', 'fcxo', 'Consultant', 'vinod@projecttech4dev.org'),
('Donald', 'Lobo', 'lobo@projecttech4dev.org', '', 'Founder', NULL);

-- 4. Assign roles to users (all employees get 'employee' role by default)
-- HR personnel and super_admin will need to be assigned manually based on your organization

-- All users get employee role
INSERT INTO user_roles (user_type_id, role_id)
SELECT user_type_id, 3 FROM users; -- role_id 3 = employee

-- Sample HR assignment (adjust email as needed)
-- You'll need to manually assign HR and super_admin roles
-- Example:
-- INSERT INTO user_roles (user_type_id, role_id)
-- SELECT user_type_id, 2 FROM users WHERE email = 'hr@projecttech4dev.org'; -- role_id 2 = hr

-- INSERT INTO user_roles (user_type_id, role_id) 
-- SELECT user_type_id, 1 FROM users WHERE email = 'admin@projecttech4dev.org'; -- role_id 1 = super_admin

-- IMPORTANT: Update these email addresses above to match your actual HR and admin personnel
-- You can run these individual INSERT statements after identifying who should have HR/admin access

-- 5. Note: The following tables will be populated by the application during use:
-- - feedback_cycles (created by HR when starting new feedback cycles)
-- - feedback_requests (created when employees request feedback)
-- - nomination_approvals (created when managers approve/reject nominations)
-- - feedback_responses (created when reviewers submit feedback)
-- - feedback_reminders (created when sending reminder emails)
-- - password_reset_tokens (created during password reset process)

-- All core reference data and users are now seeded!
-- Password hashes are NULL by design - users will set passwords on first login