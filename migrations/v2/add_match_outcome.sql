-- Add `outcome` column to match table (how the match was decided: normal, walkover, ...)
-- Existing matches get 'normal', so their results and standings do not change.
-- Run once: mysql -u root -p khelclub < migrations/v2/add_match_outcome.sql

ALTER TABLE `match`
ADD COLUMN `outcome` VARCHAR(20) NOT NULL DEFAULT 'normal' AFTER `status`;

-- Rollback:
-- ALTER TABLE `match` DROP COLUMN `outcome`;
