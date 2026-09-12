# Attendance Tracking Specification

## Purpose

Define how attendance sessions are created for Courses and how per-student attendance records, statuses, and notes are captured and edited.

## Requirements

### Requirement: Attendance session creation
The system SHALL allow the Teacher of a Course to create an Attendance Session for that Course on a given date. A Session SHALL belong to exactly one Course and SHALL record which Teacher created it, when it was created, and when it was last updated.

#### Scenario: Teacher creates a session
- **WHEN** the course's Teacher creates a session for a date
- **THEN** the session is saved for that Course with the Teacher as creator, a creation timestamp, and a NULL updated timestamp

#### Scenario: One session per course and date
- **WHEN** a session already exists for a Course on a date and the Teacher tries to create another session for the same Course and date
- **THEN** the system rejects it, and the existing session is reused instead

### Requirement: Session creation restricted to the course's teacher
The system SHALL restrict session creation for a Course to that Course's Teacher and to Admin users. Other teachers SHALL NOT be able to create sessions for a Course they do not teach.

#### Scenario: Another teacher's course
- **WHEN** a Teacher who is not the Course's Teacher attempts to create a session for that Course
- **THEN** the system denies the action

#### Scenario: Admin manages sessions
- **WHEN** an Admin opens the Attendance Session admin page
- **THEN** the Admin can view, create, edit and delete sessions for any Course

### Requirement: Attendance records per student
When an Attendance Session is created, the system SHALL create one Attendance Record for every Student in the Course's Student Group at that moment. Each record SHALL default to the PRESENT status, SHALL be editable afterwards, and SHALL track when it was last updated.

#### Scenario: Records generated on session creation
- **WHEN** a session is created for a Course whose group has 5 students
- **THEN** 5 attendance records are created, one per student, each defaulting to PRESENT

#### Scenario: One record per student per session
- **WHEN** the system generates attendance records for a session
- **THEN** each Student in the group has exactly one record in that session

#### Scenario: Group changes do not alter past sessions
- **WHEN** a Student is added to or removed from a group after a session was recorded
- **THEN** previously created sessions keep their original set of records

### Requirement: Attendance statuses
An Attendance Record SHALL have exactly one status from: PRESENT, ABSENT, LATE, EXCUSED.

#### Scenario: Teacher marks a student absent
- **WHEN** the Teacher changes a student's record from PRESENT to ABSENT and saves
- **THEN** the record stores the ABSENT status

#### Scenario: Status is always one of the allowed values
- **WHEN** a record is saved with a status outside PRESENT, ABSENT, LATE or EXCUSED
- **THEN** the system rejects the invalid status

### Requirement: Attendance editing
The system SHALL allow the course's Teacher and Admin users to update the attendance statuses and optional notes of a session's records after the session is created. There SHALL be no closing or finalization state; records remain editable.

#### Scenario: Teacher corrects attendance later
- **WHEN** the course's Teacher reopens a past session and changes a status or note
- **THEN** the updated status and note are saved

### Requirement: Attendance record notes
An Attendance Record SHALL have an optional notes field. The notes field SHALL default to an empty string and SHALL NOT be NULL.

#### Scenario: Record is created without a note
- **WHEN** an Attendance Record is created
- **THEN** its notes field is an empty string

#### Scenario: Teacher saves a note
- **WHEN** a Teacher saves a note on an Attendance Record
- **THEN** the note is persisted with the record

### Requirement: Attendance record student validation
An Attendance Record SHALL only be saved for a Student who is a member of the Attendance Session's Course's Student Group. Both the Django admin inline and model validation SHALL enforce this rule.

#### Scenario: Admin tries to add a student outside the course group
- **WHEN** an Admin selects a Student who is not in the Course's Student Group in the Attendance Session inline
- **THEN** the form rejects the save and shows a validation error

#### Scenario: Programmatic save with invalid student is rejected
- **WHEN** code calls full_clean or save on an Attendance Record whose student is not in the Course's Student Group
- **THEN** a ValidationError is raised
