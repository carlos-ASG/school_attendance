# Spec Delta — teacher-panel

## ADDED Requirements

### Requirement: Course attendance summary with date filters

The panel SHALL provide an attendance summary page per Course, at `courses/<pk>/attendance/`, reachable from the course detail page, listing every student of the Course's Student Group with their attendance rendered in the established `attended/total (percentage%)` format, each student's name linking to their course-scoped student detail page. The summary SHALL be scoped by an optional date range defined by two filters, `date_from` and `date_to`: an omitted bound SHALL leave that end of the range unbounded, and with both omitted the summary SHALL equal the course detail page's all-time summary. The denominator SHALL be the number of the Course's sessions dated inside the range and the numerator SHALL be the student's records with status `PRESENT`, `LATE` or `EXCUSED` in those sessions. Applying the filters SHALL NOT reload the full page: the filter form SHALL submit via HTMX `hx-get` and the response SHALL contain only the re-rendered summary fragment, with the filter values pushed into the browser URL so the filtered view is bookmarkable and the browser back button returns to the previous range. A range whose `date_from` is later than its `date_to` SHALL be rejected with a validation error shown in place. A range containing no sessions SHALL show an informative empty state. The page SHALL be restricted to the Course's Teacher, and all page text SHALL be in Spanish.

#### Scenario: Teacher opens the summary page without filters

- **WHEN** the Teacher opens the attendance summary page of one of their Courses with no query parameters
- **THEN** the page lists every student of the group with their all-time attendance summary, identical to the course detail page's student table

#### Scenario: Teacher filters the summary by a date range

- **WHEN** the Teacher sets `date_from` and `date_to` and applies the filters
- **THEN** only the summary fragment re-renders without a full page reload, each student's attendance is computed over the sessions dated inside the range, and the browser URL shows the filter values

#### Scenario: Range with only one bound

- **WHEN** the Teacher sets only `date_from` (or only `date_to`) and applies the filters
- **THEN** the summary counts sessions from that date onward (or up to that date) with the other end unbounded

#### Scenario: Range of a single day

- **WHEN** the Teacher sets `date_from` and `date_to` to the same date
- **THEN** the summary is computed over the sessions dated that day only

#### Scenario: Invalid range is rejected

- **WHEN** the Teacher applies filters whose `date_from` is later than their `date_to`
- **THEN** the fragment re-renders in place with a validation error and no summary data is replaced

#### Scenario: Range with no sessions

- **WHEN** the Teacher applies a range that contains no sessions of the Course
- **THEN** the page shows an informative empty state instead of an all-zero table

#### Scenario: Filtered URL is bookmarkable

- **WHEN** the Teacher opens the summary URL with `date_from` and `date_to` query parameters directly (no HTMX request)
- **THEN** the full page renders with the summary already scoped to that range

#### Scenario: Teacher opens the summary of another teacher's course

- **WHEN** a Teacher requests the attendance summary page of a Course they do not teach
- **THEN** the system denies access with a 404

## MODIFIED Requirements

### Requirement: Course detail view

The panel SHALL provide a detail page per Course showing the Subject, the physical classroom, the schedule slots, and the Student Group's members in a table. The student table SHALL include a column showing each student's attendance summary. The page SHALL show a "Sesión de hoy" card that get-or-creates today's session and navigates to the today session page, and SHALL provide links to the Course's session history page and to the Course's attendance summary page. The page SHALL NOT host a create-session form for other dates.

#### Scenario: Teacher opens a course

- **WHEN** the Teacher opens one of their Courses
- **THEN** the page shows subject, physical classroom, schedule, the student members table with attendance summaries, the "Sesión de hoy" card, and links to the session history page and the attendance summary page

#### Scenario: Teacher sees attendance summary for a student

- **WHEN** the Teacher views the student table on a course with recorded sessions
- **THEN** each row shows the student's name and their attendance as `attended/total (percentage%)`

#### Scenario: Teacher sees zero attendance before any session

- **WHEN** the Teacher views the student table on a course with no sessions
- **THEN** each row shows `0/0 (0%)` for attendance

#### Scenario: Teacher opens the attendance summary from the course page

- **WHEN** the Teacher clicks the "Resumen de asistencia" control on the course detail page
- **THEN** the Teacher is taken to the Course's attendance summary page

### Requirement: HTMX fragment responses render template partials

The teacher panel SHALL serve each HTMX-driven swap — history create-form validation errors, past-session batch edit saves, history session list re-renders after deletion, and attendance summary re-renders after date filtering — by rendering the corresponding Django template partial in isolation via the `template_name#partial_name` syntax, returning only the fragment without the full page shell. Fragment templates SHALL be defined inside their host page templates with `{% partialdef %}` rather than as separate partial files, and each fragment SHALL live in the page template whose view renders it. The today session page SHALL NOT use HTMX fragments for attendance recording.

#### Scenario: Create-form error returns only the form

- **WHEN** the Teacher submits the history create-session form with an invalid date via HTMX
- **THEN** the response contains only the re-rendered create-form fragment with the errors

#### Scenario: Batch edit save returns only the read-only panel

- **WHEN** the Teacher submits the past-session batch edit form
- **THEN** the response contains only the re-rendered read-only attendance fragment with a success confirmation

#### Scenario: Session deletion returns only the session list

- **WHEN** the Teacher confirms the deletion of a past session from the history page
- **THEN** the response contains only the re-rendered session list fragment

#### Scenario: Date filtering returns only the summary fragment

- **WHEN** the Teacher applies the date filters on the attendance summary page via HTMX
- **THEN** the response contains only the re-rendered summary fragment for the requested range
