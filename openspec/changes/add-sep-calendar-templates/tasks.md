## 1. Template dataset

- [ ] 1.1 Create `src/school/sep_templates.py` with the per-school-year dataset structure (Spanish name, `ASUETO`/`VACACIONES` type, start date, optional end date) and curated entries for the current and next school year. Given the dataset module, when it is loaded, then every entry is structurally valid (named, typed, end >= start when present).
- [ ] 1.2 Add dataset tests asserting the mandatory holidays (Nov 20, May 1, first Monday of February, third Monday of March) and the Christmas and Holy Week windows exist per school year.

## 2. Application service

- [ ] 2.1 Implement `apply_sep_template(cycle, template)`: clip each entry to the cycle's range, skip entries entirely outside, skip entries whose clipped start date is already covered by an existing `NonSchoolDay` of the cycle, and create the rest in one transaction. Given a clean cycle, when a template is applied, then one entry per template row is created clipped; when applied again, then nothing new is created.
- [ ] 2.2 Add service tests: clipping at both cycle edges, fully-outside entries skipped, manual-deletion re-apply creates only the uncovered entry, overlap with existing manual entries is respected.

## 3. Admin action

- [ ] 3.1 Add the "Cargar plantilla SEP" unfold admin action on the `SchoolCycle` changelist with an intermediate page that lists overlapping templates, previews the entries each would create (name + clipped range), and applies on confirmation; shows an empty state when no template overlaps. All copy in Spanish.
- [ ] 3.2 Add admin tests: action lists only overlapping templates; applying creates the entries and redirects back with a success message; applying with no overlapping template shows the empty state.

## 4. Verification

- [ ] 4.1 Run `uv run manage.py check` and the full test suite (`uv run manage.py test`).
- [ ] 4.2 Manual smoke: apply a template to the demo cycle, edit one applied entry, add a puente day, re-apply (no duplicates).
