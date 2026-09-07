CREATE TABLE luxtime.work_session_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES luxtime.work_sessions(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (ended_at IS NULL OR ended_at > started_at),
    EXCLUDE USING gist (
        session_id WITH =,
        tstzrange(started_at, COALESCE(ended_at, 'infinity'::TIMESTAMPTZ), '[)') WITH &&
    )
);

CREATE TRIGGER work_session_segments_set_updated_at
BEFORE UPDATE ON luxtime.work_session_segments
FOR EACH ROW EXECUTE FUNCTION luxtime.set_updated_at();
