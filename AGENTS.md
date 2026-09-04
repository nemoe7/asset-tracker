# AGENTS.md

## Project

- Repo: `nemoe7/asset-tracker`.
- Inspect the repo before changes.
- `docs/` is the source of truth for requirements, architecture, conventions, schema, and implementation status.
- Follow documented architecture/conventions and existing project patterns.
- Reuse existing APIs, services, fixtures, exceptions, and components.
- Avoid duplication, unnecessary dependencies, scope creep, and architectural changes.

## Documentation

- Check relevant docs before implementation.
- `docs/requirements.md` — requirements.
- `docs/implementation.md` — implementation status/priorities.
- `docs/conventions/` — project conventions.
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

## Testing

- Use `pytest`.
- Use installed/project test tooling and plugins when appropriate; inspect project configuration and dependencies before choosing alternatives.
- Use `pytest-xdist`/parallel test execution when available and compatible with the tests.
- Add/update tests for changed behavior.
- Reuse existing fixtures and helpers.
- Cover relevant success, failure, and authorization cases.
- Do not weaken, remove, or bypass tests.
- Run relevant tests after changes and investigate failures.

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
- Use imperative wording, lowercase after `:`, no period, and under 72 characters.
- Keep the subject focused on what changed.
- Avoid vague messages.
