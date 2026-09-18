## Why

After `add-school-calendar`, configuring each cycle's non-school days by hand is tedious and error-prone. Mexican basic-education schools follow the SEP official calendar — mandatory holidays and fixed vacation periods — with only minor school-specific additions (puente days, local holidays). Seeding a cycle from an official template removes most of the capture work.

## What Changes

- A built-in dataset of official SEP non-school days per school year: fixed-date holidays (e.g. November 20, May 1, first Monday of February, third Monday of March) and recurring vacation windows (Christmas, Holy Week — Easter-relative).
- An admin action on `SchoolCycle` ("Cargar plantilla SEP") that creates `NonSchoolDay` entries from the dataset, clipped to the cycle's date range.
- Applied entries are ordinary, fully editable `NonSchoolDay` records — schools freely add puente days and local holidays on top afterwards.
- The action is idempotent: dates already covered by an existing non-school day are skipped, never duplicated.

## Non-goals

- No automatic scraping or syncing of SEP publications — the dataset is versioned in code and updated manually.
- No university/cuatrimestral calendar templates — custom cycles remain hand-captured.
- No multi-cycle parallel mode (a school running two overlapping cycles simultaneously) — out of scope for now.
- No student/parent-facing calendar views.

## Capabilities

### New Capabilities
- `calendar-templates`: SEP template dataset and apply-to-cycle flow, including range clipping, idempotency, and post-apply editability.

### Modified Capabilities

(none — `school-calendar` entity behavior is unchanged; this change only populates it)

## Impact

- `src/school/`: admin (cycle action), a template dataset module, seeder, tests.
- Depends on `add-school-calendar` being implemented and archived first (reuses `SchoolCycle` / `NonSchoolDay`).
