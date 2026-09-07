CREATE TABLE luxtime.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
    code VARCHAR(16) NULL CHECK (code IS NULL OR length(btrim(code)) BETWEEN 1 AND 16),
    color VARCHAR(7) NOT NULL DEFAULT '#22D3EE'
        CHECK (color ~ '^#[0-9A-Fa-f]{6}$'),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER projects_set_updated_at
BEFORE UPDATE ON luxtime.projects
FOR EACH ROW EXECUTE FUNCTION luxtime.set_updated_at();
