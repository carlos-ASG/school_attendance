# Teacher Panel Specification

## Purpose

Define the teacher-facing web panel: authentication, role-based routing, classroom views, and HTMX-driven session and attendance recording, while admins continue to use the Django admin site.

## Requirements

### Requirement: Teacher panel authentication
The teacher panel SHALL use Django's built-in authentication. Only authenticated users linked to a Teacher SHALL access the panel; unauthenticated or unauthorized users SHALL be redirected to the panel login page.

#### Scenario: Anonymous user tries to open the panel
- **WHEN** an unauthenticated user opens any panel page
- **THEN** they are redirected to the panel login page

#### Scenario: Non-teacher authenticated user tries to open the panel
- **WHEN** an authenticated user with no linked Teacher opens the panel
- **THEN** they are denied access and informed they are not a teacher

#### Scenario: Teacher logs in
- **WHEN** a user linked to a Teacher logs in with valid credentials
- **THEN** they reach the panel dashboard listing their classrooms

### Requirement: Post-login routing by role
After login, the system SHALL route users by role: users who are staff SHALL be directed to the Django admin site, and teacher users SHALL be directed to the teacher panel.

#### Scenario: Staff user logs in
- **WHEN** a staff user logs in
- **THEN** they are redirected to the Django admin site

#### Scenario: Teacher user logs in
- **WHEN** a teacher (non-staff) user logs in
- **THEN** they are redirected to the teacher panel dashboard

### Requirement: Teacher classroom list
The panel dashboard SHALL list only the Classrooms of the logged-in Teacher, showing each Classroom's Subject, Student Group, student count, and schedule slots.

#### Scenario: Teacher sees only own classrooms
- **WHEN** a Teacher opens the dashboard
- **THEN** only Classrooms where that Teacher is assigned are listed

#### Scenario: Teacher opens a classroom they do not teach
- **WHEN** a Teacher requests the panel page of another teacher's Classroom
- **THEN** the system denies access

### Requirement: Classroom detail view
The panel SHALL provide a detail page per Classroom showing the Subject, the Student Group's members, the schedule slots, and the list of that Classroom's attendance sessions (most recent first), with a way to create a new session.

#### Scenario: Teacher opens a classroom
- **WHEN** the Teacher opens one of their Classrooms
- **THEN** the page shows subject, schedule, student members, and the classroom's sessions

### Requirement: Session creation from the panel
The panel SHALL allow the Teacher to create an attendance session for one of their Classrooms by choosing a date. The creation request SHALL be submitted with HTMX and the session list SHALL update without a full page reload.

#### Scenario: Teacher creates a session via HTMX
- **WHEN** the Teacher picks a date and submits the create-session form on a classroom page
- **THEN** a session is created for that date, per-student records are generated, and the session list updates in place without a full page reload

#### Scenario: Duplicate session date handled
- **WHEN** the Teacher submits a create-session form for a date that already has a session for that Classroom
- **THEN** the form shows a validation error and no duplicate session is created

### Requirement: Attendance recording from the panel
The panel SHALL provide a session page where the Teacher can set each student's status (PRESENT, ABSENT, LATE, EXCUSED) and save. Saving SHALL be submitted with HTMX and update the student list in place with a confirmation, without a full page reload.

#### Scenario: Teacher records attendance via HTMX
- **WHEN** the Teacher changes statuses on the session page and saves
- **THEN** all records are updated and the student list re-renders in place with a success confirmation

#### Scenario: All group students listed with statuses
- **WHEN** the Teacher opens a session page
- **THEN** every student of the classroom's group is listed with their current status selectable

### Requirement: Teacher panel text is in Spanish
The teacher panel SHALL display all user-visible text in Spanish, including page titles, headings, table headers, form labels, buttons, status labels, and confirmation or error messages. Code identifiers, model field names, choice values, and URL paths SHALL remain in English.

#### Scenario: Panel renders in Spanish
- **WHEN** a Teacher opens any panel page
- **THEN** every visible text element is shown in Spanish

#### Scenario: Attendance statuses shown in Spanish
- **WHEN** the Teacher selects a student's attendance status
- **THEN** the status options are displayed in Spanish (e.g. Presente, Ausente, Tarde, Justificado)

### Requirement: Admins use Django admin
Admin users SHALL manage all entities (Students, Teachers, Subjects, Student Groups, Classrooms, Sessions, Records) through the Django admin site and SHALL NOT need the teacher panel.

#### Scenario: Admin manages everything from admin site
- **WHEN** an Admin uses the Django admin site
- **THEN** all domain entities are available for management with useful listings and filters
