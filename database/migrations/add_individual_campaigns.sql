-- Migration: Add Individual Campaign Support
-- Date: 2025-12-27
-- Description: Make campaigns support both NGO and individual creators
--
-- Changes:
-- 1. Make ngo_id nullable (was NOT NULL)
-- 2. Add creator_user_id for individual campaigns
-- 3. Add index on creator_user_id for performance
-- 4. Add check constraint to ensure XOR (exactly one owner)

-- Step 1: Make ngo_id nullable
ALTER TABLE campaigns 
  ALTER COLUMN ngo_id DROP NOT NULL;

-- Step 2: Add creator_user_id column
ALTER TABLE campaigns 
  ADD COLUMN creator_user_id INTEGER REFERENCES users(id);

-- Step 3: Add index for performance
CREATE INDEX idx_campaigns_creator ON campaigns(creator_user_id);

-- Step 4: Add check constraint (XOR validation)
-- Ensures exactly one of ngo_id or creator_user_id is set
ALTER TABLE campaigns
  ADD CONSTRAINT campaigns_owner_xor 
  CHECK (
    (ngo_id IS NOT NULL AND creator_user_id IS NULL) OR
    (ngo_id IS NULL AND creator_user_id IS NOT NULL)
  );

-- Step 5: Add comment for documentation
COMMENT ON COLUMN campaigns.ngo_id IS 'NGO organization owner (for institutional campaigns)';
COMMENT ON COLUMN campaigns.creator_user_id IS 'Individual user owner (for grassroots campaigns)';
COMMENT ON CONSTRAINT campaigns_owner_xor ON campaigns IS 'Ensures exactly one owner type (NGO XOR Individual)';

-- Migration complete
-- NOTE: Existing campaigns with ngo_id will remain valid
-- New campaigns can now be created by individuals without NGO
