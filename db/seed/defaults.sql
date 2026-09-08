INSERT INTO luxtime.settings (
    singleton,
    default_rate,
    stop_on_lock,
    stop_on_sleep,
    resume_prompt,
    idle_detection,
    idle_threshold,
    engine_starts_with_windows,
    startup_behaviour,
    application_name,
    accent_color
)
VALUES (TRUE, 50.00, TRUE, TRUE, TRUE, TRUE, 20, TRUE, 'tray', 'LuxTime', '#22D3EE')
ON CONFLICT (singleton) DO NOTHING;
