-- Migration: Add Device Fingerprinting Support
-- Date: 2025-11-17
-- Purpose: Add device fingerprinting columns to transactions table for loan stacking detection
--
-- This migration adds two new columns:
-- 1. device_fingerprint: Stable browser fingerprint hash (used for fraud queries)
-- 2. fingerprint_components: Detailed component data for forensic analysis
--
-- Use Cases:
-- - Detect multiple users on same device (loan stacking)
-- - Detect high-velocity automated fraud
-- - Track devices with fraud history
-- - Enable consortium-level device tracking

-- ==========================================
-- Add Columns
-- ==========================================

-- Add device_fingerprint column (indexed for fast fraud queries)
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS device_fingerprint VARCHAR(255);

-- Add fingerprint_components column (JSONB for detailed forensics)
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS fingerprint_components JSONB;

-- ==========================================
-- Create Indexes
-- ==========================================

-- Index for loan stacking detection
-- Query: Find all transactions with same fingerprint
CREATE INDEX IF NOT EXISTS idx_device_fingerprint
ON transactions(device_fingerprint);

-- Composite index for consortium detection
-- Query: Find transactions with same fingerprint across different clients
CREATE INDEX IF NOT EXISTS idx_fingerprint_client
ON transactions(device_fingerprint, client_id);

-- GIN index for fingerprint component queries (forensic analysis)
-- Query: Search within fingerprint components (e.g., find all with specific user agent)
CREATE INDEX IF NOT EXISTS idx_fingerprint_components_gin
ON transactions USING GIN (fingerprint_components);

-- ==========================================
-- Add Comments
-- ==========================================

COMMENT ON COLUMN transactions.device_fingerprint IS
'Stable browser fingerprint hash from FingerprintJS. Used to detect loan stacking (multiple users on same device), high-velocity fraud, and devices with fraud history.';

COMMENT ON COLUMN transactions.fingerprint_components IS
'Detailed fingerprint components (screen, canvas, WebGL, fonts, etc.) stored as JSON. Used for forensic analysis and debugging fraud cases.';

-- ==========================================
-- Data Migration (if needed)
-- ==========================================

-- Set NULL for existing transactions (they don't have fingerprints)
-- New transactions will populate these fields via the API

-- ==========================================
-- Verify Migration
-- ==========================================

-- Check that columns were added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'transactions'
        AND column_name = 'device_fingerprint'
    ) THEN
        RAISE NOTICE 'Column device_fingerprint added successfully';
    ELSE
        RAISE EXCEPTION 'Failed to add device_fingerprint column';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'transactions'
        AND column_name = 'fingerprint_components'
    ) THEN
        RAISE NOTICE 'Column fingerprint_components added successfully';
    ELSE
        RAISE EXCEPTION 'Failed to add fingerprint_components column';
    END IF;
END $$;

-- Check that indexes were created
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'transactions'
        AND indexname = 'idx_device_fingerprint'
    ) THEN
        RAISE NOTICE 'Index idx_device_fingerprint created successfully';
    ELSE
        RAISE EXCEPTION 'Failed to create idx_device_fingerprint index';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'transactions'
        AND indexname = 'idx_fingerprint_client'
    ) THEN
        RAISE NOTICE 'Index idx_fingerprint_client created successfully';
    ELSE
        RAISE EXCEPTION 'Failed to create idx_fingerprint_client index';
    END IF;
END $$;

-- ==========================================
-- Rollback Script (if needed)
-- ==========================================

-- To rollback this migration, run:
-- DROP INDEX IF EXISTS idx_fingerprint_components_gin;
-- DROP INDEX IF EXISTS idx_fingerprint_client;
-- DROP INDEX IF EXISTS idx_device_fingerprint;
-- ALTER TABLE transactions DROP COLUMN IF EXISTS fingerprint_components;
-- ALTER TABLE transactions DROP COLUMN IF EXISTS device_fingerprint;
