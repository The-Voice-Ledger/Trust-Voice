-- Migration: Add conversation analytics tables
-- Created: 2025-12-31
-- Purpose: Track conversation events and daily metrics for analytics dashboard

-- Create conversation_events table
CREATE TABLE IF NOT EXISTS conversation_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    conversation_state VARCHAR(50),
    current_step VARCHAR(50),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for conversation_events
CREATE INDEX IF NOT EXISTS idx_conv_events_session ON conversation_events(session_id);
CREATE INDEX IF NOT EXISTS idx_conv_events_type ON conversation_events(event_type);
CREATE INDEX IF NOT EXISTS idx_conv_events_created ON conversation_events(created_at);
CREATE INDEX IF NOT EXISTS idx_conv_events_user ON conversation_events(user_id);

-- Create conversation_metrics table
CREATE TABLE IF NOT EXISTS conversation_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    conversation_type VARCHAR(50) NOT NULL,
    started_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    abandoned_count INTEGER DEFAULT 0,
    avg_duration_seconds INTEGER,
    avg_messages INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, conversation_type)
);

-- Create indexes for conversation_metrics
CREATE INDEX IF NOT EXISTS idx_conv_metrics_date ON conversation_metrics(date);
CREATE INDEX IF NOT EXISTS idx_conv_metrics_type ON conversation_metrics(conversation_type);

-- Add comments for documentation
COMMENT ON TABLE conversation_events IS 'Tracks all conversation events for analytics and debugging';
COMMENT ON TABLE conversation_metrics IS 'Daily aggregated metrics for conversation performance';

COMMENT ON COLUMN conversation_events.event_type IS 'Event types: conversation_started, step_completed, clarification_requested, context_switched, conversation_completed, conversation_abandoned, error_occurred';
COMMENT ON COLUMN conversation_events.event_data IS 'Additional event metadata stored as JSON';

COMMENT ON COLUMN conversation_metrics.conversation_type IS 'Type of conversation: donating, searching, creating_campaign, etc.';
COMMENT ON COLUMN conversation_metrics.avg_duration_seconds IS 'Average conversation duration in seconds';
COMMENT ON COLUMN conversation_metrics.avg_messages IS 'Average number of messages per conversation';
