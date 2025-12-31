-- LAB 9 Part 3: User Preferences Migration
-- Add user_preferences table for personalized conversations

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure one preference per key per user
    UNIQUE(user_id, preference_key)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(preference_key);

-- Comment
COMMENT ON TABLE user_preferences IS 'LAB 9 Part 3: Stores user preferences for personalized conversations (payment methods, favorite categories, default amounts)';
