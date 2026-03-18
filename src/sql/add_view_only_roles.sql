-- Add View-Only Dashboard Roles and Users
-- Roles: 44 (Live Answering), 45 (Special Teams), 46 (Clinical Pharmacy), 47 (SMS ChatBot)
-- Each role gets a dedicated user with view-only access to filtered patient data.

-- ============================================================
-- 1. Create Roles
-- ============================================================
INSERT INTO roles (role_id, role_name, description)
VALUES (44, 'LA', 'Live Answering Service - View-only patient contact info')
ON CONFLICT(role_id) DO UPDATE SET
    description = 'Live Answering Service - View-only patient contact info';

INSERT INTO roles (role_id, role_name, description)
VALUES (45, 'ST', 'Special Teams - View-only BH/Cog/RPM team assignments')
ON CONFLICT(role_id) DO UPDATE SET
    description = 'Special Teams - View-only BH/Cog/RPM team assignments';

INSERT INTO roles (role_id, role_name, description)
VALUES (46, 'CPh', 'Clinical Pharmacy - View-only medication list')
ON CONFLICT(role_id) DO UPDATE SET
    description = 'Clinical Pharmacy - View-only medication list';

INSERT INTO roles (role_id, role_name, description)
VALUES (47, 'CB', 'SMS ChatBot - View-only patient contact points')
ON CONFLICT(role_id) DO UPDATE SET
    description = 'SMS ChatBot - View-only patient contact points';

-- ============================================================
-- 2. Create Users (password = SHA-256 of 'pass123456')
-- ============================================================
-- SHA-256('pass123456') = e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74

INSERT INTO users (username, password, first_name, last_name, email, full_name, status, hire_date)
VALUES ('answering', 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
        'Live', 'Answering', 'answering@myhealthteam.org', 'Live Answering Service', 'active', date('now'))
ON CONFLICT(email) DO UPDATE SET
    password = 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
    email = 'answering@myhealthteam.org',
    full_name = 'Live Answering Service';

INSERT INTO users (username, password, first_name, last_name, email, full_name, status, hire_date)
VALUES ('specialteams', 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
        'Special', 'Teams', 'specialteams@myhealthteam.org', 'Special Teams Dashboard', 'active', date('now'))
ON CONFLICT(email) DO UPDATE SET
    password = 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
    email = 'specialteams@myhealthteam.org',
    full_name = 'Special Teams Dashboard';

INSERT INTO users (username, password, first_name, last_name, email, full_name, status, hire_date)
VALUES ('pharmacy', 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
        'Clinical', 'Pharmacy', 'pharmacy@myhealthteam.org', 'Clinical Pharmacy', 'active', date('now'))
ON CONFLICT(email) DO UPDATE SET
    password = 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
    email = 'pharmacy@myhealthteam.org',
    full_name = 'Clinical Pharmacy';

INSERT INTO users (username, password, first_name, last_name, email, full_name, status, hire_date)
VALUES ('chatbot', 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
        'SMS', 'ChatBot', 'chatbot@myhealthteam.org', 'SMS ChatBot Service', 'active', date('now'))
ON CONFLICT(email) DO UPDATE SET
    password = 'e8779e0367b50fdf6f2b1d77fef879df92dcaafc3e5ef0a3b6e3867eccd2fd74',
    email = 'chatbot@myhealthteam.org',
    full_name = 'SMS ChatBot Service';

-- ============================================================
-- 3. Assign Roles to Users
-- ============================================================
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT user_id, 44 FROM users WHERE username = 'answering';

INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT user_id, 45 FROM users WHERE username = 'specialteams';

INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT user_id, 46 FROM users WHERE username = 'pharmacy';

INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT user_id, 47 FROM users WHERE username = 'chatbot';

-- ============================================================
-- 4. Verify
-- ============================================================
SELECT u.user_id, u.username, u.email, u.full_name, r.role_id, ro.role_name
FROM users u
JOIN user_roles r ON u.user_id = r.user_id
JOIN roles ro ON r.role_id = ro.role_id
WHERE r.role_id IN (44, 45, 46, 47)
ORDER BY r.role_id;
