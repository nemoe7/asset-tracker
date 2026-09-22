-- v0.2.0: scheduled backups (BKP-001..BKP-009).
-- backup_config.schedule moves from cron string to JSON recurrence
-- (e.g. {"type":"weekly","day":6,"time":"03:00"}). backup_location
-- column dropped: storage location comes from BACKUP_DIR env var
-- (BKP-016..BKP-018), configurable independently of the DB.
UPDATE backup_config
SET schedule = '{"type":"weekly","day":6,"time":"03:00"}'
WHERE schedule LIKE '%*%';

ALTER TABLE backup_config DROP COLUMN backup_location;
