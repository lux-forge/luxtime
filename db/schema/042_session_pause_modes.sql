ALTER TABLE luxtime.work_sessions
ADD COLUMN IF NOT EXISTS pause_mode TEXT NULL;

UPDATE luxtime.work_sessions
SET pause_mode = 'manual'
WHERE status = 'paused'
  AND pause_mode IS NULL;

ALTER TABLE luxtime.work_sessions
DROP CONSTRAINT IF EXISTS work_sessions_pause_mode_matches_status;

ALTER TABLE luxtime.work_sessions
ADD CONSTRAINT work_sessions_pause_mode_matches_status CHECK (
    (status = 'paused' AND pause_mode IN ('manual', 'away', 'sleep', 'lock'))
    OR (status <> 'paused' AND pause_mode IS NULL)
);
