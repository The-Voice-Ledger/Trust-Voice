-- ============================================================
-- Migration: Add Milestone-Based Crowdfunding Tables
-- Date: 2025-02-10
-- Description: Adds project_milestones, milestone_verifications,
--              project_updates, platform_fees tables and new
--              columns on campaigns.
-- ============================================================

-- 1. Add milestone columns to campaigns
ALTER TABLE campaigns
    ADD COLUMN IF NOT EXISTS platform_fee_rate NUMERIC(5,4) DEFAULT 0.0600,
    ADD COLUMN IF NOT EXISTS use_milestones BOOLEAN DEFAULT FALSE;

-- 2. Project milestones
CREATE TABLE IF NOT EXISTS project_milestones (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    sequence INTEGER NOT NULL DEFAULT 1,
    target_amount_usd NUMERIC(12,2) NOT NULL,
    released_amount_usd NUMERIC(12,2) DEFAULT 0.0,
    platform_fee_usd NUMERIC(10,2) DEFAULT 0.0,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    evidence_notes TEXT,
    evidence_ipfs_hashes JSONB DEFAULT '[]'::jsonb,
    evidence_submitted_at TIMESTAMP,
    chain_tx_hash VARCHAR(66),
    due_date TIMESTAMP,
    released_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milestones_campaign
    ON project_milestones(campaign_id);

-- 3. Milestone verifications (field agent)
CREATE TABLE IF NOT EXISTS milestone_verifications (
    id SERIAL PRIMARY KEY,
    milestone_id INTEGER NOT NULL REFERENCES project_milestones(id),
    field_agent_id INTEGER NOT NULL REFERENCES users(id),
    agent_notes TEXT,
    photos JSONB DEFAULT '[]'::jsonb,
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,
    trust_score INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    agent_payout_amount_usd NUMERIC(8,2),
    agent_payout_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milestone_verifications_milestone
    ON milestone_verifications(milestone_id);

-- 4. Project updates (blog-style posts by campaign owner)
CREATE TABLE IF NOT EXISTS project_updates (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
    posted_by INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    media_ipfs_hashes JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_updates_campaign
    ON project_updates(campaign_id);

-- 5. Platform fees ledger
CREATE TABLE IF NOT EXISTS platform_fees (
    id SERIAL PRIMARY KEY,
    milestone_id INTEGER NOT NULL REFERENCES project_milestones(id),
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
    gross_amount_usd NUMERIC(12,2) NOT NULL,
    fee_rate NUMERIC(5,4) NOT NULL,
    fee_amount_usd NUMERIC(10,2) NOT NULL,
    net_to_project_usd NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Done!
-- To apply:  psql $DATABASE_URL -f database/migrations/add_milestones.sql
