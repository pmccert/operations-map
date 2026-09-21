# AGENTS.md

## Mission

Keep the incident map reliable, understandable, and deployable as a static
site. Prefer small changes that improve the user's workflow without adding
infrastructure or a build step.

## Architecture at a glance

- `index.html` is the application: UI, state, Leaflet map behavior, Google
  Sheets/Drive integration, polling, and persistence live here.
- `assets/disaster-modes.json` is the source of truth for startup modes. Do not
  duplicate presets in JavaScript.
- `addresses.json` is generated data. Change its generator rather than hand
  editing it.
- `scripts/fetch_addresses.py` generates the local address lookup data.
- `tests/test_fetch_addresses.py` covers the address generator.
- `README.md` documents setup and user-visible behavior.

The app must work when served by a static host over HTTP. Keep credentials out
of exported map files and do not introduce a server dependency unless the
requirements explicitly change.

## Architectural guidance

### Keep responsibilities and state explicit

- Extend existing state, rendering, persistence, and polling flows before
  creating parallel ones.
- When adding a map layer, include its enabled state in the saved runtime state
  so it is restored after a page reload.
- Keep pure transformations separate from DOM and network effects where
  practical; this makes behavior easier to test and reason about.
- Give each concept one source of truth. Avoid duplicated preset definitions,
  persistence keys, URL parsing rules, or layer-registration logic.
- Keep unrelated concerns orthogonal: a change to sheet refresh should not
  silently alter map styling, shared-map synchronization, or startup setup.

### Design for change

- Prefer data-driven configuration (`assets/disaster-modes.json`) over branches
  that encode product choices in `index.html`.
- Make external boundaries explicit: validate Google Sheet rows, fetched JSON,
  URL parameters, and local storage before using them.
- Treat network responses, missing columns, stale shared state, and geocoding
  misses as normal failure paths with visible status or error messages.
- Choose reversible changes when requirements are uncertain. Avoid coupling
  persisted formats or public URLs to an implementation detail without a
  migration or compatibility plan.

### Program by contract

- Every non-trivial function must have a function docstring that states its
  contract before implementation details are considered.
- Put all preconditions, postconditions, invariants, accepted input shapes,
  side effects, and expected failures in that docstring. Do not maintain a
  separate contract comment or rely on an undocumented implicit assumption.
- Use the repository's language-appropriate function documentation format:
  JSDoc for JavaScript and Python docstrings for Python. Use clear contract
  labels such as `@pre`, `@post`, `@invariant`, and `@throws` in JSDoc where
  they improve precision.
- Enforce preconditions at the function boundary, preserve invariants while
  mutating state, and make postconditions observable through the return value
  or documented side effect. Report contract violations explicitly.

### Keep the code honest

- Use assertions/guards for assumptions stated by a function contract that
  would otherwise produce a success-shaped result with invalid data.
- Do not hide errors with broad catches or silent fallbacks. Preserve useful
  context in the status UI and console where appropriate.
- Remove duplication when it is clearly the same knowledge, but do not create
  abstractions merely to make similar-looking code share a helper.
- Prefer the simplest implementation that meets the requirement and remains
  easy to delete or replace.

### Work in thin, verifiable slices

- Use a tracer-bullet approach for behavior that crosses UI, network, and
  persistence boundaries: wire the smallest complete path first, then extend
  it.
- Keep each change reviewable and runnable. Do not mix broad refactors with a
  feature or bug fix.
- Automate repeatable checks. Before completing a change, run `npm test`; for
  Python changes also run `python -m unittest discover tests`.
- For UI changes, serve the repository over HTTP and smoke-test setup, preset
  selection, map rendering, and the affected workflow.

## Change checklist

1. Search for an existing helper, state field, persistence key, or data shape
   before adding a new one.
2. Update the owning source of truth and any directly related documentation.
3. Preserve compatibility with existing saved map files, shared-map URLs, and
   static hosting unless a deliberate breaking change is required.
4. Validate inputs at boundaries and make failures visible.
5. Run the smallest relevant checks, then inspect the diff for accidental
   changes.

## Repository-specific cautions

- Do not assume `file://` works; Google APIs and fetches require HTTP hosting.
- Do not add hidden inline disaster presets when
  `assets/disaster-modes.json` is unavailable.
- Preserve auto-refresh, shared-map polling, map-state persistence, and URL
  parameter behavior when editing `index.html`.
- For spatial tile layers, preserve over-zoom behavior by pairing the highest
  native tile zoom with a higher display `maxZoom`.
