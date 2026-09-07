# LuxTime database

`db/` is the canonical and complete database source. Application startup does
not auto-generate or migrate schema.

## Ordering

Schema files execute lexically:

1. `001_extensions.sql` — required extensions, application schema, timestamp trigger
2. `010_projects.sql` — project records
3. `020_work_sessions.sql` — session metadata and state
4. `030_work_session_segments.sql` — interruption-safe tracked intervals
5. `040_settings.sql` — singleton application settings
6. `050_indexes.sql` — lookup, active-state, and open-segment indexes
7. `060_views.sql` — deterministic project/session totals

`seed/defaults.sql` creates only product defaults. It never creates projects or
sessions.

## Rebuild and verify

```powershell
pwsh .\db\rebuild\rebuild.ps1 -Confirm:$false
pwsh .\db\verify\verify.ps1
```

Rebuild validates connectivity, drops only the `luxtime` schema, executes each
SQL file with `ON_ERROR_STOP`, applies defaults, and runs verification. It is
destructive and uses PowerShell confirmation unless explicitly suppressed.

## Backup and restore

```powershell
pwsh .\db\backup\backup.ps1
pwsh .\db\backup\restore.ps1 -BackupFile .\db\backups\luxtime-YYYYMMDDTHHMMSSZ.dump -Confirm:$false
```

Backups use PostgreSQL's custom dump format, receive UTC timestamps, and are
validated with `pg_restore --list`. Runtime dumps live in the gitignored
`db/backups/` directory. Restore accepts files only from that directory, drops
the current application schema, exits on the first PostgreSQL error, and runs
verification afterward. Restore never overwrites the dump file.
