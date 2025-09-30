-- Add OAuth columns to users table for Google OAuth integration
-- This migration adds necessary columns for OAuth authentication

-- Add OAuth provider column
ALTER TABLE users ADD COLUMN oauth_provider TEXT DEFAULT NULL;

-- Add Google ID column for OAuth
ALTER TABLE users ADD COLUMN google_id TEXT DEFAULT NULL;

-- Add profile picture URL column
ALTER TABLE users ADD COLUMN picture_url TEXT DEFAULT NULL;

-- Create index on email for faster OAuth lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Create index on google_id for OAuth
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Update existing users to have NULL OAuth provider (indicating local auth)
UPDATE users SET oauth_provider = NULL WHERE oauth_provider IS NULL;