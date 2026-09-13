## ADDED Requirements

### Requirement: HTMX fragment responses render template partials
The teacher panel SHALL serve each HTMX-driven swap — attendance panel updates, per-record status button cycling, session date edit form fetch, and session header update — by rendering the corresponding Django template partial in isolation via the `template_name#partial_name` syntax, returning only the fragment without the full page shell. Fragment templates SHALL be defined inside their host page templates with `{% partialdef %}` rather than as separate partial files.

#### Scenario: Status button toggle returns only the button
- **WHEN** the Teacher clicks a student's status button
- **THEN** the response contains only the re-rendered status button fragment, not the full session page

#### Scenario: Attendance save returns only the attendance panel
- **WHEN** the Teacher saves attendance from the session page
- **THEN** the response contains only the re-rendered attendance panel fragment

#### Scenario: Session edit form fetch returns only the form
- **WHEN** the Teacher requests the edit-date form via HTMX
- **THEN** the response contains only the session edit form fragment

#### Scenario: Session edit success returns only the session header
- **WHEN** the Teacher submits a valid session date change via HTMX
- **THEN** the response contains only the re-rendered session header fragment
