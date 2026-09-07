CREATE TABLE luxtime.work_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES luxtime.projects(id) ON DELETE RESTRICT,
    work_type TEXT NOT NULL CHECK (
        work_type IN ('Development', 'Design', 'Research', 'Operations', 'Admin', 'Business')
    ),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 2000),
    hourly_rate NUMERIC(12, 2) NOT NULL CHECK (hourly_rate >= 0),
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'paused', 'stopped')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stopped_at TIMESTAMPTZ NULL,
    stop_reason TEXT NULL CHECK (
        stop_reason IS NULL OR stop_reason IN (
            'manual', 'lock', 'sleep', 'idle', 'shutdown', 'correction', 'system'
        )
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((status = 'stopped') = (stopped_at IS NOT NULL)),
    CHECK ((status = 'stopped') = (stop_reason IS NOT NULL)),
    CHECK (stopped_at IS NULL OR stopped_at >= started_at)
);

CREATE TRIGGER work_sessions_set_updated_at
BEFORE UPDATE ON luxtime.work_sessions
FOR EACH ROW EXECUTE FUNCTION luxtime.set_updated_at();
