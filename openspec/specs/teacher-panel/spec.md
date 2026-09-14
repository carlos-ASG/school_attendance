# Teacher Panel Specification

## Purpose

Define the teacher-facing web panel: authentication, role-based routing, course views, session CRUD, and HTMX-driven attendance recording with a cyclic status button, while admins continue to use the Django admin site.

## Requirements

### Requirement: Teacher panel authentication
The teacher panel SHALL use django-allauth (on top of Django's authentication system) for login, logout, and password flows. Only authenticated users linked to a Teacher SHALL access the panel; unauthenticated users SHALL be redirected to the account login page. Login SHALL accept username credentials, so existing username/password accounts continue to work unchanged. The login, logout, and password-flow pages SHALL render the shadcn design-system styling with Spanish copy.

#### Scenario: Anonymous user tries to open the panel
- **WHEN** an unauthenticated user opens any panel page
- **THEN** they are redirected to the account login page

#### Scenario: Non-teacher authenticated user tries to open the panel
- **WHEN** an authenticated user with no linked Teacher opens the panel
- **THEN** they are denied access and informed they are not a teacher

#### Scenario: Teacher logs in
- **WHEN** a user linked to a Teacher logs in with valid username credentials
- **THEN** they reach the panel dashboard listing their courses

#### Scenario: Login page renders the styled form
- **WHEN** any user opens the account login page
- **THEN** the login form renders with the design-system components and all visible copy is in Spanish

#### Scenario: Teacher logs out from the panel
- **WHEN** the Teacher submits the logout control on the panel
- **THEN** they are logged out and returned to the account login page

#### Scenario: Teacher resets a forgotten password
- **WHEN** a user requests a password reset for their account
- **THEN** reset instructions are sent (console email backend in development) and the password can be set through the styled allauth flow

### Requirement: Panel navigation menu
The panel chrome SHALL render a navigation menu built with the design-system navigation-menu component, showing the logged-in user's name, the panel destinations relevant to the user's role, and the logout control submitted as a POST form. All navigation menu text SHALL be in Spanish.

#### Scenario: Teacher sees the navigation menu
- **WHEN** an authenticated Teacher opens any panel page
- **THEN** the page chrome shows the navigation menu in Spanish with the panel destinations and the logout control

#### Scenario: Anonymous visitor has no panel navigation
- **WHEN** an unauthenticated user opens the account login page
- **THEN** the page renders without the panel navigation menu

### Requirement: Post-login routing by role
After login, the system SHALL route users by role: users who are staff SHALL be directed to the Django admin site, and teacher users SHALL be directed to the teacher panel.

#### Scenario: Staff user logs in
- **WHEN** a staff user logs in
- **THEN** they are redirected to the Django admin site

#### Scenario: Teacher user logs in
- **WHEN** a teacher (non-staff) user logs in
- **THEN** they are redirected to the teacher panel dashboard

### Requirement: Teacher course list
The panel dashboard SHALL list only the Courses of the logged-in Teacher, showing each Course's Subject, Student Group, student count, schedule slots, and physical classroom.

#### Scenario: Teacher sees only own courses
- **WHEN** a Teacher opens the dashboard
- **THEN** only Courses where that Teacher is assigned are listed

#### Scenario: Teacher opens a course they do not teach
- **WHEN** a Teacher requests the panel page of another teacher's Course
- **THEN** the system denies access

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

### Requirement: Course detail view
The panel SHALL provide a detail page per Course showing the Subject, the physical classroom, the schedule slots, the Student Group's members in a table, and the list of that Course's attendance sessions (most recent first), with a way to create a new session. The student table SHALL include a column showing each student's attendance summary.

#### Scenario: Teacher opens a course
- **WHEN** the Teacher opens one of their Courses
- **THEN** the page shows subject, physical classroom, schedule, student members in a table, each student's attendance summary, and the course's sessions

#### Scenario: Teacher sees attendance summary for a student
- **WHEN** the Teacher views the student table on a course with recorded sessions
- **THEN** each row shows the student's name and their attendance as `attended/total (percentage%)`

#### Scenario: Teacher sees zero attendance before any session
- **WHEN** the Teacher views the student table on a course with no sessions
- **THEN** each row shows `0/0 (0%)` for attendance

### Requirement: Course detail attendance calculation
The system SHALL compute each student's attendance percentage as the number of their records with status `PRESENT`, `LATE`, or `EXCUSED` divided by the total number of sessions for the course, multiplied by 100.

#### Scenario: Student with mixed attendance statuses
- **WHEN** a student has 10 records for a course with 12 sessions, where 8 are `PRESENT`, 1 is `LATE`, 1 is `EXCUSED`, and 2 are `ABSENT`
- **THEN** the displayed attendance is `10/12 (83.3%)`

#### Scenario: Student with only absents
- **WHEN** a student has 5 records for a course with 5 sessions and all are `ABSENT`
- **THEN** the displayed attendance is `0/5 (0.0%)`

#### Scenario: All students in group are listed
- **WHEN** the Teacher opens a course with students in its group
- **THEN** every student in the group appears in the table, even if they have no attendance records

### Requirement: Create today session shortcut
The course detail panel SHALL provide a one-click control labeled "Crear sesión de hoy" to create an attendance session for the current date. When a session for the current date already exists, the control SHALL navigate to that session's detail page instead of creating a duplicate.

#### Scenario: Teacher starts today's session
- **WHEN** the Teacher clicks the "Crear sesión de hoy" control and no session exists for today
- **THEN** a session for today is created with attendance records for the group and the Teacher is taken to its detail page

#### Scenario: Today's session already exists
- **WHEN** the Teacher clicks the control and a session for today already exists
- **THEN** no duplicate session is created and the Teacher is taken to the existing session's detail page

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

### Requirement: Cyclic attendance status button
The panel SHALL render each student's attendance status as a single button instead of radio buttons. Clicking the button SHALL advance the record's status to the next value in the cycle PRESENT → ABSENT → LATE → EXCUSED and back to PRESENT, persisting the change immediately without a full page reload.

#### Scenario: Teacher cycles a student's status
- **WHEN** the course Teacher clicks the status button for a student
- **THEN** the record's status advances to the next value in the cycle
- **AND** the updated status is saved on the server immediately
- **AND** only the status button is re-rendered via HTMX

#### Scenario: Another teacher's session record
- **WHEN** a Teacher who is not the Course's Teacher attempts to toggle a record's status
- **THEN** the system denies the action and the status is unchanged

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

### Requirement: Attendance notes from the panel
The panel SHALL provide a notes field on each Attendance Record so the Teacher can record a short reason or comment for a student's attendance.

#### Scenario: Teacher adds a note to a record
- **WHEN** the Teacher enters a note for a student's record and saves
- **THEN** the note is stored on that Attendance Record

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

### Requirement: Teacher panel text is in Spanish
The teacher panel SHALL display all user-visible text in Spanish, including page titles, headings, table headers, form labels, buttons, status labels, and confirmation or error messages. Code identifiers, model field names, choice values, and URL paths SHALL remain in English.

#### Scenario: Panel renders in Spanish
- **WHEN** a Teacher opens any panel page
- **THEN** every visible text element is shown in Spanish

#### Scenario: Attendance statuses shown in Spanish
- **WHEN** the Teacher selects a student's attendance status
- **THEN** the status options are displayed in Spanish (e.g. Presente, Ausente, Tarde, Justificado)

### Requirement: Admins use Django admin
Admin users SHALL manage all entities (Students, Teachers, Subjects, Student Groups, Courses, Sessions, Records) through the Django admin site and SHALL NOT need the teacher panel.

#### Scenario: Admin manages everything from admin site
- **WHEN** an Admin uses the Django admin site
- **THEN** all domain entities are available for management with useful listings and filters
