# AGENTS.md

## Project

- Repo: `nemoe7/asset-tracker`.
- Inspect the repo before changes.
- `docs/` is the source of truth for requirements, architecture, conventions, schema, and implementation status.
- Follow documented architecture/conventions and existing project patterns.
- Reuse existing APIs, services, fixtures, exceptions, and components.
- Avoid duplication, unnecessary dependencies, scope creep, and architectural changes.
- Use the venv `.venv` if present

## Documentation

- Check relevant docs before implementation.
- `docs/SRS.md` — requirements.
- `docs/implementation.md` — implementation status/priorities. Notes are exceptions, empty by default: a note exists only for non-derivable information — what blocks a 🟡/🔴 row, or a 🟢 row's caveat/constraint a future implementer must know (scope limits, external dependencies, traps, unverified assumptions). Never narrate what was done or how it works — the code and tests are the record.
- `docs/conventions/` — project conventions. Permissions use `namespace.operation` (e.g. `inventory.read`, `field.<field_id>.read`, `field.<field_id>.update`); field-level access is not `.manage`. Authoritative source: `docs/conventions/auth/authorization.md`.
- `docs/schema/` and `database/schema.sql` — schema guidance.
- Update documentation when changes make it inaccurate.

## Architecture

- Preserve existing Flask layer boundaries:
  - `app/routes/` — HTTP concerns.
  - `app/services/` — application services.
  - `app/services/data/` — persistent data operations.
  - `app/services/exceptions/` — service exceptions.
  - `app/templates/` — templates.
  - `app/static/` — frontend assets.
  - `database/schema.sql` — database schema.
- Follow existing patterns instead of introducing parallel abstractions.
- Keep data/application logic out of routes when an appropriate service exists.
- Do not move responsibilities between layers without a documented reason.

## Code

- Follow existing naming, structure, formatting, and dependency conventions.
- Use 2-space indentation.
- Prefer the smallest complete change that satisfies the requirement.
- Preserve existing behavior unless a requirement requires changing it.
- Leave unrelated code untouched.
- The tailwindcss watcher/generator may touch `app/static/css/app.css`, ALWAYS include the file in commits. It doesn't need a separate commit.
- ALWAYS update `docs/implementation.md` when adding or changing functionality.

## Testing

- Use `pytest`.
- Prefer `pytest --testmon -q` as the default test gate after code changes.
- After testmon passes, run the full `pytest -q` suite and record both results.
- Use installed/project test tooling and plugins when appropriate; inspect project configuration and dependencies before choosing alternatives.
- Use `pytest-xdist`/parallel test execution when available and compatible with the tests.
- Add/update tests for changed behavior.
- Reuse existing fixtures and helpers.
- Cover relevant success, failure, and authorization cases.
- Do not weaken, remove, or bypass tests.
- Run relevant tests after changes and investigate failures.
- Run the full `pytest -q` suite when Testmon coverage is uncertain or changes affect shared fixtures, test infrastructure, configuration, or broadly used code.
- If Playwright MCP is installed, use it for browser-based testing and UI interaction verification.

## Requirements

- Check `docs/implementation.md` before feature work.
- Verify functionality is not already implemented.
- Follow documented requirements and priorities.
- Do not include unrelated or lower-priority work.
- Preserve completed functionality.

## Git

- Keep commits focused; exclude unrelated changes.
- Follow Conventional Commits:
  `<type>(optional scope): <short description>`
- Prefer existing scopes.
- Use imperative wording, lowercase after `: `, no period, and under 72 characters.
- Keep the subject focused on what changed.
- Avoid vague messages.

## Glossary

- `checks`: a QR code scan
