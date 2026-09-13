## MODIFIED Requirements

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

## ADDED Requirements

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
