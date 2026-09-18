# Design: add-sep-calendar-templates

## Context

Depends on `add-school-calendar` being implemented and archived: it populates `NonSchoolDay` entries of a `SchoolCycle`. Today every cycle's non-school days must be captured by hand in the admin inline. Mexican basic-education schools follow the SEP official calendar (mandatory holidays and fixed vacation windows) with school-specific additions on top.

## Goals / Non-Goals

**Goals:**

- Ship a versioned dataset of official SEP non-school days per school year.
- One admin action to seed a cycle from a template, clipped to the cycle's range.
- Idempotent application and full editability afterwards.

**Non-Goals:**

- No scraping/syncing SEP publications; no university/cuatrimestral templates; no parallel-cycle mode; no student-facing calendar views.

## Decisions

### D1: The dataset is curated per-school-year Python data, not computed

Each school year's official calendar is a hand-curated dict in `src/school/sep_templates.py` (e.g. `2025-2026`, `2026-2027`): fixed-date holidays (Nov 20, May 1, first Monday of February, third Monday of March) and vacation windows (Christmas, Holy Week) with Spanish names and `ASUETO`/`VACACIONES` types. Alternatives rejected: computing Easter algorithmically (windows shift anyway; SEP publishes a new calendar each year — data-in-repo is the honest representation, and adding a year is adding one dict entry) and scraping (staleness and fragility with zero control).

### D2: One template per school year; clipping adapts it to any cycle type

A template carries its school-year window. Applying it to a cycle clips each entry to the cycle's `[start, end]` range and drops entries that fall entirely outside — so the same `2026-2027` template serves an annual cycle (full year), an Ago–Dic semester (Aug–Dec portion), or a Sep–Dic cuatrimestre. No per-cycle-type templates.

### D3: Admin action calling a service function

An unfold admin action on the `SchoolCycle` changelist ("Cargar plantilla SEP") opens an intermediate page listing the templates whose school-year window overlaps the selected cycle; applying calls `apply_sep_template(cycle, template)` in `src/school/sep_templates.py` (pure service function, directly testable; a management command can wrap it later if ever needed). If exactly one template overlaps, the page still shows it for confirmation — no surprise application.

### D4: Template entries become ordinary `NonSchoolDay` rows — no provenance field

Applied entries are indistinguishable from hand-created ones: same model, same inline editing, same deletion. An `origin`/`source` field was rejected: extra schema for near-zero value, and it would imply template-vs-manual behavior differences that do not exist. Editability is the whole point: schools add puente days and local holidays on top, and correct whatever the official calendar gets wrong for them.

### D5: Idempotency by date coverage, not flags

A template entry is skipped when its (clipped) start date already falls inside an existing `NonSchoolDay` range of the cycle; otherwise it is created in full. Re-running the action is therefore a no-op (all starts already covered). Partial overlaps can create overlapping entries — allowed by `school-calendar`'s union semantics (D3 of `add-school-calendar`), harmless.

## Risks / Trade-offs

- [Dataset goes stale as years pass] → adding a school year is one curated dict entry with a test asserting every entry has valid dates; the action only offers overlapping templates, so stale years are simply never offered.
- [Clipping at cycle edges produces short stubs (e.g. one day of a vacation window)] → acceptable: the stub is correct (that day IS non-working within the cycle) and editable; the intermediate page shows what will be created before applying.
- [Admins may expect the template to "sync" later changes] → the confirmation page states entries are created once and become ordinary editable records.

## Migration Plan

No schema changes — only a new module, admin action, and tests. Deploy: none beyond the normal release. Rollback: remove the action; applied entries are ordinary rows and need no rollback.

## Open Questions

- Which school years to seed in the initial dataset (propose: the current and next school year at implementation time).
- Whether the intermediate page previews each entry (name + clipped range) before applying — proposed yes; cheap and prevents surprises.
