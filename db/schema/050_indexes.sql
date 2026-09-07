CREATE UNIQUE INDEX projects_name_unique_ci
    ON luxtime.projects (lower(name));

CREATE INDEX projects_active_name_idx
    ON luxtime.projects (active, name);

CREATE INDEX work_sessions_project_started_idx
    ON luxtime.work_sessions (project_id, started_at DESC);

CREATE INDEX work_sessions_status_started_idx
    ON luxtime.work_sessions (status, started_at DESC);

CREATE INDEX work_session_segments_session_started_idx
    ON luxtime.work_session_segments (session_id, started_at);

CREATE UNIQUE INDEX work_session_segments_one_open_idx
    ON luxtime.work_session_segments (session_id)
    WHERE ended_at IS NULL;
