-- Add preferred_language to PendingRegistration table
-- Migration: Add preferred_language field for storing user's preferred language during registration

ALTER TABLE "pending_registrations" 
ADD COLUMN preferred_language VARCHAR(2) DEFAULT 'en';

-- Add index for better query performance
CREATE INDEX idx_pending_registrations_preferred_language 
ON "pending_registrations" (preferred_language);

-- Update existing records to have default English preference
UPDATE "pending_registrations" 
SET preferred_language = 'en' 
WHERE preferred_language IS NULL;
