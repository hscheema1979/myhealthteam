-- Create user_sessions table for OAuth session persistence
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_data TEXT NOT NULL,  -- JSON string containing session data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    oauth_token TEXT,
    refresh_token TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active);

-- Clean up expired sessions (optional cleanup)
DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP OR is_active = 0;