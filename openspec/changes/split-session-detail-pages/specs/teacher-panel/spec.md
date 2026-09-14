# Teacher Panel Delta: split-session-detail-pages

## ADDED Requirements

### Requirement: Dashboard session quick-access cards
The dashboard SHALL render, under each course card, a row of two compact cards: "Sesión de hoy" and "Historial de sesiones". The "Sesión de hoy" card SHALL have no body content and a single footer button that get-or-creates today's session for that course and navigates the Teacher to the today session page. The "Historial de sesiones" card SHALL navigate to that course's session history page.

#### Scenario: Teacher starts today's session from the dashboard
- **WHEN** the Teacher clicks the "Sesión de hoy" card button for a course with no session today
- **THEN** a session for today is created with attendance records for the group and the Teacher is taken to the today session page

#### Scenario: Today's session already exists when using the dashboard card
- **WHEN** the Teacher clicks the "Sesión de hoy" card button and a session for today already exists
- **THEN** no duplicate session is created and the Teacher is taken to the existing session's today page

#### Scenario: Teacher opens the history from the dashboard
- **WHEN** the Teacher clicks the "Historial de sesiones" card for a course
- **THEN** the Teacher is taken to that course's session history page

### Requirement: Session detail pages split by date
The panel SHALL provide two separate session detail pages: a today session page at `sessions/<pk>/today/`, reachable from the dashboard and course detail "Sesión de hoy" cards, and a previous session page at `sessions/<pk>/`, reachable from the history page's "Ver" action. Each page SHALL guard by date: requesting the today page for a session not dated today SHALL redirect to the previous session page, and requesting the previous page for a session dated today SHALL redirect to the today page. The session history list SHALL NOT include the course's session dated today.

#### Scenario: Today session opened via the previous URL
- **WHEN** the Teacher opens `sessions/<pk>/` for a session dated today
- **THEN** they are redirected to `sessions/<pk>/today/`

#### Scenario: Past session opened via the today URL
- **WHEN** the Teacher opens `sessions/<pk>/today/` for a session not dated today
- **THEN** they are redirected to `sessions/<pk>/`

#### Scenario: Today's session is not listed in the history
- **WHEN** the Teacher opens the session history page of a course that has a session dated today
- **THEN** the today session does not appear in the session list

#### Scenario: A today session appears in the history the next day
- **WHEN** the Teacher opens the session history page on a date after a session's date
- **THEN** that session is listed in the history

### Requirement: Attendance recording on the today session page
The today session page SHALL render the attendance editing interface by default: one row per student with a cyclic status button and a notes field. Status changes SHALL persist immediately per action via HTMX without a full page reload. Notes SHALL be saved by submitting the form, which re-renders the attendance panel in place with a confirmation and without a full page reload.

#### Scenario: Today's session opens in editing mode
- **WHEN** the Teacher opens the today session page
- **THEN** every student of the course's group is listed with an interactive status button and a notes field, with no extra action required

#### Scenario: Teacher saves notes on the today session page
- **WHEN** the Teacher enters notes and submits the form
- **THEN** the notes are stored and the attendance panel re-renders in place with a success confirmation

### Requirement: Past session review and correction
The previous session page SHALL render the session's records read-only by default, listing every student with their current status and note. The page SHALL offer an "Editar" control that enables a batch edit form: one row per student with a status selector (combobox or select) offering the four statuses and a notes field. No change SHALL be persisted until the Teacher submits the form; submitting SHALL save all rows at once and return the page to the read-only view with a confirmation.

#### Scenario: Past session opens read-only
- **WHEN** the Teacher opens the previous session page of a session dated before today
- **THEN** every student is listed with their current status and note shown read-only and no editing controls are rendered

#### Scenario: Teacher enables editing on a past session
- **WHEN** the Teacher clicks the "Editar" control on the previous session page
- **THEN** a batch edit form renders with one row per student, each with a status selector and a notes field

#### Scenario: Status selector offers the four statuses in Spanish
- **WHEN** the Teacher opens a status selector on the batch edit form
- **THEN** the options are exactly Presente, Ausente, Tarde, Justificado

#### Scenario: Teacher submits the batch edit form
- **WHEN** the Teacher changes one or more statuses or notes and submits the form
- **THEN** all changes are persisted together and the read-only view re-renders in place with a success confirmation

#### Scenario: Teacher exits editing without submitting
- **WHEN** the Teacher leaves edit mode without submitting the form
- **THEN** no status or note changes are persisted

### Requirement: Session deletion from the panel
The panel SHALL allow the Teacher to delete an Attendance Session from the history page's "Acciones" column and from the today session page. Both delete controls SHALL require confirmation through an alert dialog before the deletion is submitted. Deleting a past session from the history page SHALL remove the session and its records and re-render the session list in place without a full page reload. Deleting a today session from the today session page SHALL remove the session and its records and redirect the Teacher to the course detail page.

#### Scenario: Teacher deletes a past session from the history
- **WHEN** the Teacher confirms the deletion of a past session from the history page's "Acciones" column
- **THEN** the session and its records are removed and the session list re-renders in place without the deleted session

#### Scenario: Teacher deletes the last session of a course from the history
- **WHEN** the Teacher confirms the deletion of the course's only listed session
- **THEN** the re-rendered session list shows the empty state

#### Scenario: Teacher deletes a today session from the today page
- **WHEN** the Teacher confirms the deletion of a session dated today from the today session page
- **THEN** the session and its records are removed and the Teacher is redirected to the course detail page

#### Scenario: Deletion is cancelled
- **WHEN** the Teacher dismisses the delete confirmation dialog without confirming
- **THEN** no session is removed

## MODIFIED Requirements

### Requirement: Course sessions page
The panel SHALL provide a dedicated page per Course, reachable from the course detail page and the dashboard's "Historial de sesiones" card, that lists the Course's Attendance Sessions most recent first, excluding the session dated today. The page SHALL host a "Crear sesión en otra fecha" form at the top, and the session list SHALL show each session's date, creation timestamp, and an "Acciones" column with a "Ver" control linking to the previous session page and an "Eliminar" control behind a confirmation dialog. The page SHALL be restricted to the Course's Teacher and SHALL provide a way to return to the course detail page.

#### Scenario: Teacher opens the sessions page
- **WHEN** the Teacher opens the sessions page of one of their Courses
- **THEN** the page lists the course's past sessions most recent first with date, creation timestamp, and "Acciones" (Ver, Eliminar), excludes the session dated today, and shows the "Crear sesión en otra fecha" form at the top

#### Scenario: Teacher opens the sessions page of another teacher's course
- **WHEN** a Teacher requests the sessions page of another teacher's Course
- **THEN** the system denies access

#### Scenario: Sessions page links back to the course
- **WHEN** the Teacher is on the sessions page
- **THEN** the page provides a link back to the course detail page

### Requirement: Course detail view
The panel SHALL provide a detail page per Course showing the Subject, the physical classroom, the schedule slots, and the Student Group's members in a table. The student table SHALL include a column showing each student's attendance summary. The page SHALL show a "Sesión de hoy" card that get-or-creates today's session and navigates to the today session page, and SHALL provide a link to the Course's session history page. The page SHALL NOT host a create-session form for other dates.

#### Scenario: Teacher opens a course
- **WHEN** the Teacher opens one of their Courses
- **THEN** the page shows subject, physical classroom, schedule, the student members table with attendance summaries, the "Sesión de hoy" card, and a link to the session history page

#### Scenario: Teacher sees attendance summary for a student
- **WHEN** the Teacher views the student table on a course with recorded sessions
- **THEN** each row shows the student's name and their attendance as `attended/total (percentage%)`

#### Scenario: Teacher sees zero attendance before any session
- **WHEN** the Teacher views the student table on a course with no sessions
- **THEN** each row shows `0/0 (0%)` for attendance

### Requirement: Create today session shortcut
The "Sesión de hoy" cards on the dashboard and the course detail page SHALL provide a one-click control that get-or-creates the attendance session for the current date for that Course. When a session for the current date already exists, the control SHALL navigate to that session's today session page instead of creating a duplicate.

#### Scenario: Teacher starts today's session
- **WHEN** the Teacher clicks the "Sesión de hoy" control and no session exists for today
- **THEN** a session for today is created with attendance records for the group and the Teacher is taken to its today session page

#### Scenario: Today's session already exists
- **WHEN** the Teacher clicks the "Sesión de hoy" control and a session for today already exists
- **THEN** no duplicate session is created and the Teacher is taken to the existing session's today session page

### Requirement: Session creation from the panel
The panel SHALL allow the Teacher to create an attendance session for one of their Courses by choosing a date on the session history page's "Crear sesión en otra fecha" form. The chosen date SHALL be before today: dates in the future SHALL be rejected with a validation error, and today's date SHALL be rejected with a message directing the Teacher to the "Sesión de hoy" card. A date that already has a session for the Course SHALL be rejected. On success the session SHALL be created with per-student records and the Teacher SHALL be taken to the new session's page. On validation errors the form SHALL re-render in place with the errors, without a full page reload.

#### Scenario: Teacher creates a past session
- **WHEN** the Teacher picks a past date and submits the create-session form on the history page
- **THEN** a session is created for that date, per-student records are generated, and the Teacher is taken to the new session's page

#### Scenario: Future date rejected
- **WHEN** the Teacher submits the create-session form with a date after today
- **THEN** the form shows a validation error and no session is created

#### Scenario: Today's date rejected
- **WHEN** the Teacher submits the create-session form with today's date
- **THEN** the form shows a validation error directing to the "Sesión de hoy" card and no session is created

#### Scenario: Duplicate session date handled
- **WHEN** the Teacher submits the create-session form for a date that already has a session for that Course
- **THEN** the form shows a validation error and no duplicate session is created

### Requirement: Cyclic attendance status button
The today session page SHALL render each student's attendance status as a single button instead of radio buttons. Clicking the button SHALL advance the record's status to the next value in the cycle PRESENT → ABSENT → LATE → EXCUSED and back to PRESENT, persisting the change immediately without a full page reload. The previous session page SHALL NOT use the cyclic status button.

#### Scenario: Teacher cycles a student's status
- **WHEN** the course Teacher clicks the status button for a student on the today session page
- **THEN** the record's status advances to the next value in the cycle
- **AND** the updated status is saved on the server immediately
- **AND** only the status button is re-rendered via HTMX

#### Scenario: Another teacher's session record
- **WHEN** a Teacher who is not the Course's Teacher attempts to toggle a record's status
- **THEN** the system denies the action and the status is unchanged

### Requirement: HTMX fragment responses render template partials
The teacher panel SHALL serve each HTMX-driven swap — today-page attendance panel updates, per-record status button cycling, history create-form validation errors, past-session batch edit saves, and history session list re-renders after deletion — by rendering the corresponding Django template partial in isolation via the `template_name#partial_name` syntax, returning only the fragment without the full page shell. Fragment templates SHALL be defined inside their host page templates with `{% partialdef %}` rather than as separate partial files, and each fragment SHALL live in the page template whose view renders it.

#### Scenario: Status button toggle returns only the button
- **WHEN** the Teacher clicks a student's status button on the today session page
- **THEN** the response contains only the re-rendered status button fragment, not the full session page

#### Scenario: Attendance save returns only the attendance panel
- **WHEN** the Teacher saves attendance from the today session page
- **THEN** the response contains only the re-rendered attendance panel fragment

#### Scenario: Create-form error returns only the form
- **WHEN** the Teacher submits the history create-session form with an invalid date via HTMX
- **THEN** the response contains only the re-rendered create-form fragment with the errors

#### Scenario: Batch edit save returns only the read-only panel
- **WHEN** the Teacher submits the past-session batch edit form
- **THEN** the response contains only the re-rendered read-only attendance fragment with a success confirmation

#### Scenario: Session deletion returns only the session list
- **WHEN** the Teacher confirms the deletion of a past session from the history page
- **THEN** the response contains only the re-rendered session list fragment

## REMOVED Requirements

### Requirement: Session update and deletion from the panel
**Reason**: Session date editing is removed entirely — a session created on the wrong date must be deleted and recreated — and deletion is redesigned per page (history "Acciones" column and today page dialog), covered by the new "Session deletion from the panel" requirement.
**Migration**: To delete a session, use the history page's "Eliminar" action (past sessions) or the today session page's delete dialog (today sessions). To correct a wrong date, delete the session and create a new one with the correct date.

### Requirement: Attendance recording from the panel
**Reason**: The single session page is split into two workflows with different UIs and save semantics — today (live, per-action saves) and previous (read-only with a batch edit form) — covered by the new "Attendance recording on the today session page" and "Past session review and correction" requirements.
**Migration**: Sessions dated today are managed at `sessions/<pk>/today/` with cyclic status buttons and per-action saves; sessions dated in the past are reviewed at `sessions/<pk>/` and corrected via the "Editar" batch form.
