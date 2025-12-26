-- Migration: Add Impact Verification Fields
-- Date: 2025-12-25
-- Purpose: Support field agent impact reports with trust scoring and payouts

-- Update ImpactVerification table
ALTER TABLE impact_verifications
    -- Change id to UUID
    ALTER COLUMN id TYPE UUID USING id::uuid,
    ALTER COLUMN id SET DEFAULT gen_random_uuid(),
    
    -- Change campaign_id to UUID
    ALTER COLUMN campaign_id TYPE UUID USING campaign_id::uuid,
    
    -- Add field agent reference
    ADD COLUMN IF NOT EXISTS field_agent_id UUID REFERENCES users(id),
    
    -- Update verification details
    ADD COLUMN IF NOT EXISTS verification_date TIMESTAMP DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS agent_notes TEXT,
    ADD COLUMN IF NOT EXISTS testimonials TEXT,
    
    -- Rename and update media columns
    ADD COLUMN IF NOT EXISTS photos JSON,
    
    -- Update location columns
    ADD COLUMN IF NOT EXISTS gps_latitude FLOAT,
    ADD COLUMN IF NOT EXISTS gps_longitude FLOAT,
    
    -- Add trust scoring
    ADD COLUMN IF NOT EXISTS trust_score INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending',
    
    -- Add agent payout fields
    ADD COLUMN IF NOT EXISTS agent_payout_amount_usd FLOAT,
    ADD COLUMN IF NOT EXISTS agent_payout_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS agent_payout_transaction_id VARCHAR(100),
    
    -- Add timestamps
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Migrate old data if exists
UPDATE impact_verifications
SET 
    photos = photo_urls::json
WHERE photos IS NULL AND photo_urls IS NOT NULL;

-- Drop old columns (optional - comment out if you want to keep backups)
-- ALTER TABLE impact_verifications 
--     DROP COLUMN IF EXISTS verifier_phone,
--     DROP COLUMN IF EXISTS verifier_name,
--     DROP COLUMN IF EXISTS verification_type,
--     DROP COLUMN IF EXISTS description,
--     DROP COLUMN IF EXISTS audio_recording_url,
--     DROP COLUMN IF EXISTS photo_urls,
--     DROP COLUMN IF EXISTS gps_coordinates,
--     DROP COLUMN IF EXISTS blockchain_anchor_tx,
--     DROP COLUMN IF EXISTS verified_at;

-- Add verification metrics to campaigns
ALTER TABLE campaigns
    ADD COLUMN IF NOT EXISTS verification_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_trust_score FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS avg_trust_score FLOAT DEFAULT 0.0;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_impact_verifications_field_agent 
    ON impact_verifications(field_agent_id);
    
CREATE INDEX IF NOT EXISTS idx_impact_verifications_campaign 
    ON impact_verifications(campaign_id);
    
CREATE INDEX IF NOT EXISTS idx_impact_verifications_status 
    ON impact_verifications(status);
    
CREATE INDEX IF NOT EXISTS idx_impact_verifications_trust_score 
    ON impact_verifications(trust_score);

-- Add check constraint for trust score
ALTER TABLE impact_verifications
    ADD CONSTRAINT check_trust_score CHECK (trust_score >= 0 AND trust_score <= 100);

-- Comments
COMMENT ON COLUMN impact_verifications.trust_score IS 'Automated trust score 0-100 based on photo count, GPS, testimonials, description quality';
COMMENT ON COLUMN impact_verifications.status IS 'pending, approved, rejected - auto-approved if trust_score >= 80';
COMMENT ON COLUMN impact_verifications.agent_payout_amount_usd IS 'Standard field agent fee: $30 USD';
COMMENT ON COLUMN campaigns.avg_trust_score IS 'Average trust score across all verifications - higher score = more trustworthy campaign';
