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
