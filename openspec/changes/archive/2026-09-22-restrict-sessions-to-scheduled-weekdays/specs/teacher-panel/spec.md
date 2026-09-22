# Delta: teacher-panel

## MODIFIED Requirements

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
