CREATE VIEW luxtime.project_totals AS
SELECT p.id,
       p.name,
       p.code,
       p.color,
       p.active,
       p.created_at,
       p.updated_at,
       COALESCE(
           ROUND(SUM(EXTRACT(EPOCH FROM (COALESCE(seg.ended_at, CURRENT_TIMESTAMP) - seg.started_at))))::BIGINT,
           0
       ) AS total_seconds
FROM luxtime.projects p
LEFT JOIN luxtime.work_sessions session ON session.project_id = p.id
LEFT JOIN luxtime.work_session_segments seg ON seg.session_id = session.id
GROUP BY p.id;

CREATE VIEW luxtime.session_totals AS
SELECT session.id AS session_id,
       COALESCE(
           ROUND(SUM(EXTRACT(EPOCH FROM (COALESCE(seg.ended_at, CURRENT_TIMESTAMP) - seg.started_at))))::BIGINT,
           0
       ) AS total_seconds
FROM luxtime.work_sessions session
LEFT JOIN luxtime.work_session_segments seg ON seg.session_id = session.id
GROUP BY session.id;
