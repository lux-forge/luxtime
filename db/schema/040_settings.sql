CREATE TABLE luxtime.settings (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    default_rate NUMERIC(12, 2) NOT NULL CHECK (default_rate >= 0),
    stop_on_lock BOOLEAN NOT NULL,
    stop_on_sleep BOOLEAN NOT NULL,
    resume_prompt BOOLEAN NOT NULL,
    idle_detection BOOLEAN NOT NULL,
    idle_threshold INTEGER NOT NULL CHECK (idle_threshold BETWEEN 1 AND 1440),
    engine_starts_with_windows BOOLEAN NOT NULL,
    startup_behaviour TEXT NOT NULL
        CHECK (startup_behaviour IN ('tray', 'compact', 'window')),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER settings_set_updated_at
BEFORE UPDATE ON luxtime.settings
FOR EACH ROW EXECUTE FUNCTION luxtime.set_updated_at();
