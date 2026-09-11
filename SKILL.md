# SKILL.md

## Purpose

This repository is a static, client-side incident map application. Most product
behavior lives in `index.html`.

Use this guide when making changes so edits stay small, safe, and consistent
with the repository's structure.

## Repository shape

Primary files:

- `index.html`
  - Main application UI, map logic, Google Sheets integration, shared map
    behavior, and runtime features.
- `assets/disaster-modes.json`
  - Startup disaster presets; treat this as the source of truth for startup
    modes.
- `scripts/fetch_addresses.py`
  - Generates `addresses.json`.
- `tests/test_fetch_addresses.py`
  - Tests for the address-fetching script.
- `README.md`
  - User-facing behavior and setup expectations.

## Working rules

1. Prefer surgical edits.
   - Do not refactor large sections of `index.html` unless the task requires it.
   - Preserve existing naming, DOM structure, and inline architectural patterns.
2. Respect runtime assumptions.
   - The app must be served over HTTP; do not assume `file://` support.
   - Startup presets come from `assets/disaster-modes.json`; do not add hidden
     inline fallback presets unless explicitly requested.
3. Keep static-hosting compatibility.
   - Avoid introducing backend requirements.
   - Avoid build steps unless the task explicitly asks for them.
4. Protect existing workflows.
   - Google Sheet loading
   - address/geocoding behavior
   - disaster preset loading
   - shared map state loading and saving
   - polling-driven refresh behavior

## Validation

Before finishing changes:

1. Run `npm test`.
   - In this repository, that runs ESLint against `index.html`.
2. If Python code changed, also run:
   - `pytest tests/test_fetch_addresses.py`
3. If UI behavior changed, do a quick manual smoke test over HTTP and confirm:
   - the app loads
   - the setup modal works
   - a preset can be selected
   - the map renders without console errors

## Change guidance

### If changing `index.html`

- Search for existing helpers before adding new ones.
- Prefer extending existing state and rendering flows over creating parallel
  logic.
- Be careful with persistence keys, polling timers, and URL parameter handling.

### If changing disaster presets

- Update `assets/disaster-modes.json`.
- Confirm `README.md` still matches actual preset behavior.

### If changing address generation

- Update `scripts/fetch_addresses.py`.
- Run the Python test file.

## When to update docs

Update `README.md` when changing:

- setup steps
- preset behavior
- HTTP hosting expectations
- geocoder requirements
- user-visible map features
