-- Rollback Migration: Remove Individual Campaign Support
-- Date: 2025-12-27
-- WARNING: This will delete all individual campaigns (where creator_user_id is set)

-- Step 1: Check for individual campaigns
DO $$
DECLARE
    individual_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO individual_count
    FROM campaigns
    WHERE creator_user_id IS NOT NULL;
    
    IF individual_count > 0 THEN
        RAISE NOTICE 'WARNING: Found % individual campaigns that will be deleted!', individual_count;
    END IF;
END $$;

-- Step 2: Delete individual campaigns (or reassign to NGO if you prefer)
-- OPTION A: Delete (uncomment to use)
-- DELETE FROM campaigns WHERE creator_user_id IS NOT NULL;

-- OPTION B: Fail rollback if individual campaigns exist (safer)
DO $$
DECLARE
    individual_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO individual_count
    FROM campaigns
    WHERE creator_user_id IS NOT NULL;
    
    IF individual_count > 0 THEN
        RAISE EXCEPTION 'Cannot rollback: % individual campaigns exist. Reassign or delete them first.', individual_count;
    END IF;
END $$;

-- Step 3: Drop check constraint
ALTER TABLE campaigns
  DROP CONSTRAINT IF EXISTS campaigns_owner_xor;

-- Step 4: Drop index
DROP INDEX IF EXISTS idx_campaigns_creator;

-- Step 5: Drop creator_user_id column
ALTER TABLE campaigns 
  DROP COLUMN IF EXISTS creator_user_id;

-- Step 6: Make ngo_id required again
ALTER TABLE campaigns 
  ALTER COLUMN ngo_id SET NOT NULL;

-- Rollback complete
