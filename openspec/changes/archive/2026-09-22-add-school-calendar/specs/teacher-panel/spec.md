# Delta: teacher-panel

## MODIFIED Requirements

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

### Requirement: Create today session shortcut

The course detail page SHALL provide a "Sesión de hoy" one-click control that get-or-creates the attendance session for the current date for that Course. When a session for the current date already exists, the control SHALL navigate to that session's today session page instead of creating a duplicate. When the current date is a Non-School Day of the Course's cycle or falls outside the Course's cycle, the control SHALL NOT create a session and SHALL show an informative message instead.

#### Scenario: Teacher starts today's session

- **WHEN** the Teacher clicks the "Sesión de hoy" control and no session exists for today
- **THEN** a session for today is created with attendance records for the group and the Teacher is taken to its today session page

#### Scenario: Today's session already exists

- **WHEN** the Teacher clicks the "Sesión de hoy" control and a session for today already exists
- **THEN** no duplicate session is created and the Teacher is taken to the existing session's today session page

#### Scenario: Today control rejected on a non-school day

- **WHEN** the Teacher clicks the "Sesión de hoy" control on a date that is a Non-School Day of the Course's cycle
- **THEN** no session is created and a message explains why

#### Scenario: Today control rejected outside the cycle

- **WHEN** the Teacher clicks the "Sesión de hoy" control on a date outside the Course's cycle range
- **THEN** no session is created and a message explains why

### Requirement: Session creation from the panel

The panel SHALL allow the Teacher to create an attendance session for one of their Courses by choosing a date on the session history page's "Crear sesión en otra fecha" form. The chosen date SHALL be before today: dates in the future SHALL be rejected with a validation error, and today's date SHALL be rejected with a message directing the Teacher to the "Sesión de hoy" card. A date that already has a session for the Course SHALL be rejected. A date outside the Course's School Cycle SHALL be rejected with a validation error naming the cycle, and a date that is a Non-School Day of the Course's cycle SHALL be rejected with a validation error naming the non-school day. On success the session SHALL be created with per-student records and the Teacher SHALL be taken to the new session's page. On validation errors the form SHALL re-render in place with the errors, without a full page reload.

#### Scenario: Teacher creates a past session

- **WHEN** the Teacher picks a past date inside the course's cycle that is not a non-school day, and submits the create-session form on the history page
- **THEN** a session is created for that date, per-student records are generated, and the Teacher is taken to the new session's page

#### Scenario: Future date rejected

- **WHEN** the Teacher submits the create-session form with a date after today
- **THEN** the form shows a validation error and no session is created

#### Scenario: Today's date rejected

- **WHEN** the Teacher submits the create-session form with today's date
- **THEN** the form shows a validation error directing to the "Sesión de hoy" card and no session is created

#### Scenario: Duplicate session date handled

- **WHEN** the Teacher submits the create-session form for a date that already has a session for the Course
- **THEN** the form shows a validation error and no duplicate session is created

#### Scenario: Out-of-cycle date rejected

- **WHEN** the Teacher submits the create-session form with a date outside the Course's School Cycle range
- **THEN** the form shows a validation error naming the cycle and no session is created

#### Scenario: Non-school day date rejected

- **WHEN** the Teacher submits the create-session form with a date that is a Non-School Day of the Course's cycle
- **THEN** the form shows a validation error naming the non-school day and no session is created

## ADDED Requirements

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
