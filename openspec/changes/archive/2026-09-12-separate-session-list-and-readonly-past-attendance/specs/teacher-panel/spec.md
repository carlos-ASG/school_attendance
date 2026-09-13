## ADDED Requirements

### Requirement: Course sessions page
The panel SHALL provide a dedicated page per Course, reachable from the course detail page, that lists the Course's Attendance Sessions most recent first, links each session to its session detail page, and hosts the create-session form. The page SHALL be restricted to the Course's Teacher, SHALL provide a way to return to the course detail page, and the session list SHALL NOT include edit or delete controls.

#### Scenario: Teacher opens the sessions page
- **WHEN** the Teacher opens the sessions page of one of their Courses
- **THEN** the page lists the course's sessions most recent first, each linking to its session detail page, and shows the create-session form

#### Scenario: Teacher opens the sessions page of another teacher's course
- **WHEN** a Teacher requests the sessions page of another teacher's Course
- **THEN** the system denies access

#### Scenario: Sessions page links back to the course
- **WHEN** the Teacher is on the sessions page
- **THEN** the page provides a link back to the course detail page

## MODIFIED Requirements

### Requirement: Course detail view
The panel SHALL provide a detail page per Course showing the Subject, the physical classroom, the schedule slots, the Student Group's members in a table with each student's attendance summary, and a shortcut to the Course's session for the current date ("Crear sesión de hoy" when none exists, "Sesión de hoy" when it exists). The course detail page SHALL provide a button to open the course sessions page and SHALL NOT embed the session list or the create-session form.

#### Scenario: Teacher opens a course
- **WHEN** the Teacher opens one of their Courses
- **THEN** the page shows subject, physical classroom, schedule, student members in a table, each student's attendance summary, the today-session shortcut, and a button linking to the course sessions page

#### Scenario: Teacher sees attendance summary for a student
- **WHEN** the Teacher views the student table on a course with recorded sessions
- **THEN** each row shows the student's name and their attendance as `attended/total (percentage%)`

#### Scenario: Teacher sees zero attendance before any session
- **WHEN** the Teacher views the student table on a course with no sessions
- **THEN** each row shows `0/0 (0%)` for attendance

#### Scenario: Course detail does not show the session list
- **WHEN** the Teacher opens a course detail page
- **THEN** the course's full session list is not rendered on that page

### Requirement: Session creation from the panel
The panel SHALL allow the Teacher to create an attendance session for one of their Courses by choosing a date on the course sessions page. The creation request SHALL be submitted with HTMX and the session list SHALL update without a full page reload.

#### Scenario: Teacher creates a session via HTMX
- **WHEN** the Teacher picks a date and submits the create-session form on the course sessions page
- **THEN** a session is created for that date, per-student records are generated, and the session list updates in place without a full page reload

#### Scenario: Duplicate session date handled
- **WHEN** the Teacher submits a create-session form for a date that already has a session for that Course
- **THEN** the form shows a validation error and no duplicate session is created

### Requirement: Session update and deletion from the panel
The panel SHALL allow the Teacher to edit an Attendance Session's date and to delete an Attendance Session from the session detail page. The session list SHALL NOT offer edit or delete controls. Editing SHALL be submitted with HTMX and update the session detail page in place. Deleting SHALL require the Teacher to confirm the deletion and, once confirmed, SHALL remove the session and its records and redirect the Teacher to the course sessions page.

#### Scenario: Teacher edits a session date via HTMX
- **WHEN** the Teacher changes the date of an existing session on the session detail page and submits the edit form
- **THEN** the session is updated, the new date respects the one-session-per-course-per-date rule, and the session detail page updates in place

#### Scenario: Deletion requires confirmation
- **WHEN** the Teacher clicks the delete control on the session detail page
- **THEN** a confirmation message is shown before the deletion is submitted

#### Scenario: Teacher deletes a session after confirming
- **WHEN** the Teacher confirms the deletion of a session from the session detail page
- **THEN** the session and its records are removed and the Teacher is redirected to the course sessions page

### Requirement: Attendance recording from the panel
The panel SHALL provide a session page where the Teacher can set each student's status (PRESENT, ABSENT, LATE, EXCUSED), add an optional note, and save. The session page SHALL render the attendance editing interface by default only when the session's date is the current date; for sessions dated in the past it SHALL render the attendance read-only and SHALL offer an explicit "Editar" control that enables the editing interface. Saving SHALL be submitted with HTMX and update the student list in place with a confirmation, without a full page reload.

#### Scenario: Today's session opens in editing mode
- **WHEN** the Teacher opens the session page of a session dated today
- **THEN** the attendance editing interface (status buttons and note fields) is editable without any extra action

#### Scenario: Past session opens read-only
- **WHEN** the Teacher opens the session page of a session dated before today
- **THEN** every student of the course's group is listed with their current status and note shown read-only
- **AND** no editing controls are rendered

#### Scenario: Teacher enables editing on a past session
- **WHEN** the Teacher clicks the "Editar" control on a past session page
- **THEN** the attendance editing interface becomes available and statuses and notes can be changed and saved

#### Scenario: Teacher records attendance via HTMX
- **WHEN** the Teacher changes statuses or notes on the session page and saves
- **THEN** all records are updated and the student list re-renders in place with a success confirmation

#### Scenario: All group students listed with statuses
- **WHEN** the Teacher opens a session page, editable or read-only
- **THEN** every student of the course's group is listed with their current status and note
