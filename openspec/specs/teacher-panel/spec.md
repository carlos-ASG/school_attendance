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
The panel chrome SHALL render a collapsible sidebar built with the design-system sidebar components: a collapsed icon rail by default, expandable to an expanded sidebar showing icon and label via a toggle control with the `panel_left` icon in the topbar. The sidebar SHALL show a single navigation item — Home — linking to the panel dashboard and highlighted as active only while on it, and SHALL present the logout control in its footer submitted as a POST form. The expanded/collapsed choice SHALL persist across page loads in the browser. All navigation text SHALL be in Spanish, and the topbar SHALL show the logged-in user's name.

#### Scenario: Teacher sees the sidebar navigation
- **WHEN** an authenticated Teacher opens any panel page
- **THEN** the page chrome shows the collapsed sidebar rail with the Home item in Spanish and the logout control in the footer

#### Scenario: Teacher expands and collapses the sidebar
- **WHEN** the Teacher presses the topbar toggle control with the `panel_left` icon
- **THEN** the sidebar alternates between the collapsed icon rail (icons with hover tooltips) and the expanded sidebar (icons with visible labels)

#### Scenario: Sidebar state persists across navigation
- **WHEN** the Teacher expands the sidebar and then navigates to another panel page or reloads
- **THEN** the sidebar renders expanded (and collapsed likewise when saved collapsed)

#### Scenario: Home item navigates to the dashboard
- **WHEN** the Teacher clicks the Home item in the sidebar from any panel page
- **THEN** they reach the panel dashboard, where the Home item is highlighted as active; on other pages it is not

#### Scenario: Teacher logs out from the sidebar
- **WHEN** the Teacher presses the "Cerrar sesión" control in the sidebar footer
- **THEN** a POST request logs them out and they are returned to the account login page

#### Scenario: Anonymous visitor has no panel navigation
- **WHEN** an unauthenticated user opens the account login page
- **THEN** the page renders without the panel sidebar or topbar chrome

### Requirement: Post-login routing by role
After login, the system SHALL route users by role: users who are staff SHALL be directed to the Django admin site, and teacher users SHALL be directed to the teacher panel.

#### Scenario: Staff user logs in
- **WHEN** a staff user logs in
- **THEN** they are redirected to the Django admin site

#### Scenario: Teacher user logs in
- **WHEN** a teacher (non-staff) user logs in
- **THEN** they are redirected to the teacher panel dashboard

### Requirement: Teacher course list
The panel dashboard SHALL list only the Courses of the logged-in Teacher whose School Cycle contains the current date, showing each Course's Subject, Student Group, student count, schedule slots, and physical classroom. When the Teacher has Courses in cycles that do not contain the current date, the dashboard SHALL additionally list them in a separate "Otros ciclos" section showing each Course with its cycle name and linking to its course detail page, without a "Sesión de hoy" card. When no School Cycle contains the current date, the main list SHALL show no courses.

#### Scenario: Teacher sees only own current-cycle courses
- **WHEN** a Teacher opens the dashboard on a date contained by one of their courses' cycles
- **THEN** only that teacher's Courses whose cycle contains the current date are listed in the main list

#### Scenario: Teacher opens a course they do not teach
- **WHEN** a Teacher requests the panel page of another teacher's Course
- **THEN** the system denies access

#### Scenario: Other-cycle courses are listed separately
- **WHEN** a Teacher opens the dashboard and has Courses in cycles that do not contain the current date
- **THEN** those Courses appear in the "Otros ciclos" section with their cycle name, linking to their course detail pages

#### Scenario: No active cycle shows an empty main list
- **WHEN** a Teacher opens the dashboard on a date not contained by any School Cycle
- **THEN** the main course list is empty and the dashboard shows the no-cycle notice banner

### Requirement: Dashboard course card actions
The dashboard SHALL render, under each course card, a single "Ver curso" button that navigates the Teacher to that course's detail page. The dashboard SHALL NOT provide a "Sesión de hoy" quick-access control or a "Historial de sesiones" control; today's session is created from the course detail page and sessions are listed from the course's session history page.

#### Scenario: Teacher opens a course from the dashboard
- **WHEN** the Teacher clicks the "Ver curso" button for a course
- **THEN** the Teacher is taken to that course's detail page

#### Scenario: Dashboard has no session quick-access
- **WHEN** the Teacher opens the dashboard
- **THEN** no course card offers a "Sesión de hoy" or "Historial de sesiones" control

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
The previous session page SHALL render the session's records read-only by default, listing every student with their current status and note. The page SHALL offer an "Editar" control that enables a batch edit form: one row per student with a status selector (combobox or select) offering the four statuses and a notes field. No change SHALL be persisted until the Teacher submits the form; submitting SHALL save all rows at once and return the page to the read-only view with a confirmation. For a frozen session (its course's School Cycle does not contain today's date), the "Editar" control SHALL NOT enable the batch edit form; it SHALL open an alert dialog explaining that the session belongs to a cycle that is no longer active and is read-only. A frozen session's edit form submission SHALL be rejected with an error message and the read-only view.

#### Scenario: Past session opens read-only
- **WHEN** the Teacher opens the previous session page of a session dated before today
- **THEN** every student is listed with their current status and note shown read-only and no editing controls are rendered

#### Scenario: Teacher enables editing on a past session
- **WHEN** the Teacher clicks the "Editar" control on the previous session page of a session whose course's cycle contains today's date
- **THEN** a batch edit form renders with one row per student, each with a status selector and a notes field

#### Scenario: Status selector offers the four statuses in Spanish
- **WHEN** the Teacher opens a status selector on the batch edit form
- **THEN** the options are exactly Presente, Ausente, Tarde, Justificado

#### Scenario: Teacher submits the batch edit form
- **WHEN** the Teacher changes one or more statuses or notes and submits the form of a session whose course's cycle contains today's date
- **THEN** all changes are persisted together and the read-only view re-renders in place with a success confirmation

#### Scenario: Teacher exits editing without submitting
- **WHEN** the Teacher leaves edit mode without submitting the form
- **THEN** no status or note changes are persisted

#### Scenario: Frozen session stays read-only when edit mode is requested
- **WHEN** the Teacher opens the previous session page of a frozen session with the edit flag (`?edit=1`)
- **THEN** the page renders the read-only view and no edit form is rendered

#### Scenario: Frozen session's edit button opens a read-only notice dialog
- **WHEN** the Teacher clicks the "Editar" control on the previous session page of a frozen session
- **THEN** an alert dialog opens explaining the session belongs to a cycle that is no longer active and cannot be edited, with a single acknowledgment control

#### Scenario: Frozen session's edit form submission is rejected
- **WHEN** the Teacher submits the batch edit form for a frozen session (e.g. a stale form posted directly)
- **THEN** no changes are persisted, an error message explains the session is read-only, and the read-only view re-renders in place

### Requirement: Session deletion from the panel
The panel SHALL allow the Teacher to delete an Attendance Session from the history page's "Acciones" column and from the today session page. Both delete controls SHALL require confirmation through an alert dialog before the deletion is submitted. Deleting a past session from the history page SHALL remove the session and its records and re-render the session list in place without a full page reload. Deleting a today session from the today session page SHALL remove the session and its records and redirect the Teacher to the course detail page. A frozen session (its course's School Cycle does not contain today's date) SHALL NOT be deletable: the delete control SHALL NOT be rendered on its session page, and a delete request submitted directly SHALL be rejected with an error message.

#### Scenario: Teacher deletes a past session from the history
- **WHEN** the Teacher confirms the deletion of a past session of a non-frozen course from the history page's "Acciones" column
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

#### Scenario: Frozen session hides the delete control
- **WHEN** the Teacher opens the previous session page of a frozen session
- **THEN** no delete control is rendered for that session

#### Scenario: Frozen session deletion is rejected
- **WHEN** the Teacher submits a delete request for a frozen session directly
- **THEN** the session and its records are not removed and an error message explains the session is read-only

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
The course detail page SHALL provide a "Sesión de hoy" one-click control that get-or-creates the attendance session for the current date for that Course. When a session for the current date already exists, the control SHALL navigate to that session's today session page instead of creating a duplicate. When the current date cannot host a session — a Non-School Day of the Course's cycle, a date outside the Course's cycle, a weekday that matches no schedule slot of the Course, or a Course with no schedule slots at all — the control SHALL NOT create a session and SHALL be rendered disabled with an informative Spanish message explaining why.

#### Scenario: Teacher starts today's session
- **WHEN** the Teacher clicks the "Sesión de hoy" control on a weekday the Course meets, with a date inside the cycle and not a Non-School Day, and no session exists for today
- **THEN** a session for today is created with attendance records for the group and the Teacher is taken to its today session page

#### Scenario: Today's session already exists
- **WHEN** the Teacher clicks the "Sesión de hoy" control and a session for today already exists
- **THEN** no duplicate session is created and the Teacher is taken to the existing session's today session page

#### Scenario: Today control rejected on a non-school day
- **WHEN** the Teacher opens the course detail page on a date that is a Non-School Day of the Course's cycle
- **THEN** the "Sesión de hoy" control is disabled and a message explains why

#### Scenario: Today control rejected outside the cycle
- **WHEN** the Teacher opens the course detail page on a date outside the Course's cycle range
- **THEN** the "Sesión de hoy" control is disabled and a message explains why

#### Scenario: Today control rejected on a non-scheduled weekday
- **WHEN** the Teacher opens the course detail page on a weekday that matches none of the Course's schedule slots
- **THEN** the "Sesión de hoy" control is disabled and a message names the weekday the course does not meet

#### Scenario: Today control rejected for a course without schedule
- **WHEN** the Teacher opens the course detail page of a Course that has no schedule slots
- **THEN** the "Sesión de hoy" control is disabled and a message explains the course has no assigned schedule

### Requirement: Session creation from the panel
The panel SHALL allow the Teacher to create an attendance session for one of their Courses by choosing a date on the session history page's "Crear sesión en otra fecha" form. The chosen date SHALL be before today: dates in the future SHALL be rejected with a validation error, and today's date SHALL be rejected with a message directing the Teacher to the "Sesión de hoy" card. A date that already has a session for the Course SHALL be rejected. A date outside the Course's School Cycle SHALL be rejected with a validation error naming the cycle, a date that is a Non-School Day of the Course's cycle SHALL be rejected with a validation error naming the non-school day, and a date on a weekday that matches no schedule slot of the Course SHALL be rejected with a validation error naming the weekday. On success the session SHALL be created with per-student records and the Teacher SHALL be taken to the new session's page. On validation errors the form SHALL re-render in place with the errors, without a full page reload.

#### Scenario: Teacher creates a past session
- **WHEN** the Teacher picks a past date inside the course's cycle that is not a non-school day and falls on a weekday the course meets, and submits the create-session form on the history page
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

#### Scenario: Out-of-cycle date rejected
- **WHEN** the Teacher submits the create-session form with a date outside the Course's School Cycle range
- **THEN** the form shows a validation error naming the cycle and no session is created

#### Scenario: Non-school day date rejected
- **WHEN** the Teacher submits the create-session form with a date that is a Non-School Day of the Course's cycle
- **THEN** the form shows a validation error naming the non-school day and no session is created

#### Scenario: Non-scheduled weekday rejected
- **WHEN** the Teacher submits the create-session form with a past, in-cycle date on a weekday that matches none of the Course's schedule slots
- **THEN** the form shows a validation error naming the weekday and no session is created

#### Scenario: Course without schedule rejected
- **WHEN** the Teacher submits the create-session form for a Course that has no schedule slots
- **THEN** the form shows a validation error explaining the course has no assigned schedule and no session is created

### Requirement: Attendance recording on the today session page
The today session page SHALL render the attendance editing interface by default: one row per student with a cyclic status button and a notes field. The rows SHALL be rendered client-side by Alpine.js from the session's records serialized into the page as JSON, and every student of the course's group SHALL be listed. Status changes and note edits SHALL be applied to a client-side pending state without any network request. A single save control SHALL submit all pending records to the attendance JSON API in one request; on success the pending state SHALL clear and a success toast SHALL be shown; on failure the pending state SHALL be preserved and an error toast SHALL be shown. Saving SHALL NOT re-render any server-rendered fragment.

#### Scenario: Today's session opens in editing mode
- **WHEN** the Teacher opens the today session page
- **THEN** every student of the course's group is listed with an interactive status button and a notes field, rendered from the serialized records with no extra action required

#### Scenario: Status clicks and note edits stay local
- **WHEN** the Teacher cycles statuses or types notes on the today session page
- **THEN** the changes are held in the client-side pending state and no network request is issued

#### Scenario: Teacher saves all pending changes
- **WHEN** the Teacher clicks the save control with pending changes
- **THEN** all pending records are sent to the attendance API in one request, the pending state clears, and a success toast is shown

#### Scenario: Failed save preserves pending changes
- **WHEN** the save request fails or is rejected
- **THEN** the pending state is preserved, the changes remain staged, and an error toast is shown

### Requirement: Cyclic attendance status button
The today session page SHALL render each student's attendance status as a single button instead of radio buttons. Clicking the button SHALL advance the record's status to the next value in the cycle PRESENT → ABSENT → LATE → EXCUSED and back to PRESENT, updating only the client-side pending state: the change SHALL NOT be persisted and SHALL NOT issue any network request until the Teacher saves. The previous session page SHALL NOT use the cyclic status button.

#### Scenario: Teacher cycles a student's status
- **WHEN** the course Teacher clicks the status button for a student on the today session page
- **THEN** the record's status advances to the next value in the cycle in the client-side state
- **AND** no network request is made and nothing is persisted

#### Scenario: Cycled change persists only on save
- **WHEN** the Teacher cycles one or more statuses and then saves
- **THEN** the cycled statuses are persisted together with the single save request

### Requirement: HTMX fragment responses render template partials
The teacher panel SHALL serve each HTMX-driven swap — history create-form validation errors, past-session batch edit saves, and history session list re-renders after deletion — by rendering the corresponding Django template partial in isolation via the `template_name#partial_name` syntax, returning only the fragment without the full page shell. Fragment templates SHALL be defined inside their host page templates with `{% partialdef %}` rather than as separate partial files, and each fragment SHALL live in the page template whose view renders it. The today session page SHALL NOT use HTMX fragments for attendance recording.

#### Scenario: Create-form error returns only the form
- **WHEN** the Teacher submits the history create-session form with an invalid date via HTMX
- **THEN** the response contains only the re-rendered create-form fragment with the errors

#### Scenario: Batch edit save returns only the read-only panel
- **WHEN** the Teacher submits the past-session batch edit form
- **THEN** the response contains only the re-rendered read-only attendance fragment with a success confirmation

#### Scenario: Session deletion returns only the session list
- **WHEN** the Teacher confirms the deletion of a past session from the history page
- **THEN** the response contains only the re-rendered session list fragment

### Requirement: Attendance notes from the panel
The panel SHALL provide a notes field on each Attendance Record so the Teacher can record a short reason or comment for a student's attendance.

#### Scenario: Teacher adds a note to a record
- **WHEN** the Teacher enters a note for a student's record and saves
- **THEN** the note is stored on that Attendance Record

### Requirement: Unsaved-changes guard on the today session page
The today session page SHALL surface pending (unsaved) attendance changes: the save control SHALL be disabled while no changes are pending and enabled once any record is pending; the page SHALL show a badge with the count of pending records; and closing or navigating away from the page while changes are pending SHALL trigger the browser's unload warning. The guard state SHALL reset after a successful save.

#### Scenario: Save control disabled without pending changes
- **WHEN** the Teacher opens the today session page or has just saved successfully
- **THEN** the save control is disabled and no pending-count badge is shown

#### Scenario: Save control enabled with a pending count
- **WHEN** the Teacher cycles a status or edits a note without saving
- **THEN** the save control becomes enabled and a badge shows the number of pending records

#### Scenario: Leaving with pending changes warns
- **WHEN** the Teacher closes the tab or navigates away with pending changes
- **THEN** the browser shows the unload confirmation warning

#### Scenario: Leaving without pending changes does not warn
- **WHEN** the Teacher closes the tab or navigates away with no pending changes
- **THEN** no unload warning is shown

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

### Requirement: Non-school day and cycle status banner
The dashboard SHALL show a banner when the current date is not a class day: when the current date is a Non-School Day of the cycle containing it, the banner SHALL show "Hoy no hay clases — {nombre del día inhábil}"; when no School Cycle contains the current date, the banner SHALL show a notice that there is no cycle in progress. The banner text SHALL be in Spanish.

#### Scenario: Banner on a non-school day
- **WHEN** a Teacher opens the dashboard on a date that is a Non-School Day of the cycle containing that date
- **THEN** the dashboard shows a banner reading "Hoy no hay clases —" followed by the non-school day's name

#### Scenario: Banner when no cycle is in progress
- **WHEN** a Teacher opens the dashboard on a date not contained by any School Cycle
- **THEN** the dashboard shows a notice that there is no cycle in progress

#### Scenario: No banner on a normal class day
- **WHEN** a Teacher opens the dashboard on a date contained by a cycle and not marked as a non-school day
- **THEN** no banner is shown
