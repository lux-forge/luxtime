DO $$
DECLARE
    missing_tables TEXT;
BEGIN
    SELECT string_agg(required.name, ', ' ORDER BY required.name)
    INTO missing_tables
    FROM (VALUES
        ('projects'),
        ('settings'),
        ('work_session_segments'),
        ('work_sessions')
    ) AS required(name)
    WHERE to_regclass('luxtime.' || required.name) IS NULL;

    IF missing_tables IS NOT NULL THEN
        RAISE EXCEPTION 'Missing LuxTime tables: %', missing_tables;
    END IF;

    IF (SELECT COUNT(*) FROM luxtime.settings) <> 1 THEN
        RAISE EXCEPTION 'LuxTime requires exactly one settings row';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM luxtime.work_sessions session
        LEFT JOIN luxtime.work_session_segments segment
            ON segment.session_id = session.id
        WHERE session.status = 'running'
        GROUP BY session.id
        HAVING COUNT(*) FILTER (WHERE segment.ended_at IS NULL) <> 1
    ) THEN
        RAISE EXCEPTION 'Every running session must have exactly one open segment';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM luxtime.work_sessions session
        JOIN luxtime.work_session_segments segment ON segment.session_id = session.id
        WHERE session.status IN ('paused', 'stopped')
          AND segment.ended_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Paused and stopped sessions cannot have open segments';
    END IF;
END;
$$;

SELECT 'LuxTime database verification passed' AS result;
