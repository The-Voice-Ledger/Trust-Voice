-- ============================================================
-- Migration: Add Transparency Videos Table
-- Date: 2025-02-10
-- Description: Adds the transparency_videos table for the
--              three-act video transparency framework.
--
--   Act 1 — "Why We Need This" (campaign launch pitch)
--   Act 2 — "What We Are Doing" (progress stream)
--   Act 3 — "What We Did" (milestone closeout evidence)
--   Field Agent Verification (independent GPS-tagged evidence)
-- ============================================================

CREATE TABLE IF NOT EXISTS transparency_videos (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) NOT NULL UNIQUE,

    -- Three-act category: why, progress, completion, verification
    category VARCHAR(20) NOT NULL,

    -- Polymorphic parent: 'campaign' or 'milestone'
    parent_type VARCHAR(20) NOT NULL,
    parent_id INTEGER NOT NULL,

    -- Metadata
    title VARCHAR(255),
    description TEXT,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),

    -- Storage
    storage_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    content_hash_sha256 VARCHAR(64),
    ipfs_cid VARCHAR(100),
    blockchain_tx_hash VARCHAR(66),

    -- Technical
    duration_seconds INTEGER,
    resolution VARCHAR(20),
    file_size_bytes INTEGER,
    mime_type VARCHAR(50) DEFAULT 'video/mp4',

    -- Status & moderation
    status VARCHAR(20) NOT NULL DEFAULT 'ready',
    flag_reason TEXT,
    flagged_by INTEGER REFERENCES users(id),

    -- GPS evidence
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,

    -- Engagement
    view_count INTEGER DEFAULT 0,

    -- Extra metadata (device info, encoding params, etc.)
    metadata_json JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE UNIQUE INDEX IF NOT EXISTS ix_transparency_videos_uuid
    ON transparency_videos(uuid);

CREATE INDEX IF NOT EXISTS ix_video_parent
    ON transparency_videos(parent_type, parent_id);

CREATE INDEX IF NOT EXISTS ix_video_category_parent
    ON transparency_videos(category, parent_type, parent_id);

CREATE INDEX IF NOT EXISTS ix_video_status
    ON transparency_videos(status);

CREATE INDEX IF NOT EXISTS ix_video_uploaded_by
    ON transparency_videos(uploaded_by);

-- ============================================================
-- Verify migration
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE 'Migration complete: transparency_videos table created with indexes.';
END $$;
