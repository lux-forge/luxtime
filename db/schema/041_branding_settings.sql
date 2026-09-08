ALTER TABLE luxtime.settings
    ADD COLUMN IF NOT EXISTS application_name VARCHAR(48) NOT NULL DEFAULT 'LuxTime'
        CHECK (BTRIM(application_name) <> ''),
    ADD COLUMN IF NOT EXISTS accent_color VARCHAR(7) NOT NULL DEFAULT '#22D3EE'
        CHECK (accent_color ~ '^#[0-9A-Fa-f]{6}$');
