## ADDED Requirements

### Requirement: Attendance session creation
The system SHALL allow the Teacher of a Classroom to create an Attendance Session for that Classroom on a given date. A Session SHALL belong to exactly one Classroom and SHALL record which Teacher created it and when.

#### Scenario: Teacher creates a session
- **WHEN** the classroom's Teacher creates a session for a date
- **THEN** the session is saved for that Classroom with the Teacher as creator and a creation timestamp

#### Scenario: One session per classroom and date
- **WHEN** a session already exists for a Classroom on a date and the Teacher tries to create another session for the same Classroom and date
- **THEN** the system rejects it, and the existing session is reused instead

### Requirement: Session creation restricted to the classroom's teacher
The system SHALL restrict session creation for a Classroom to that Classroom's Teacher and to Admin users. Other teachers SHALL NOT be able to create sessions for a Classroom they do not teach.

#### Scenario: Another teacher's classroom
- **WHEN** a Teacher who is not the Classroom's Teacher attempts to create a session for that Classroom
- **THEN** the system denies the action

#### Scenario: Admin manages sessions
- **WHEN** an Admin opens the Attendance Session admin page
- **THEN** the Admin can view, create, edit and delete sessions for any Classroom

### Requirement: Attendance records per student
When an Attendance Session is created, the system SHALL create one Attendance Record for every Student in the Classroom's Student Group at that moment. Each record SHALL default to the PRESENT status and SHALL be editable afterwards.

#### Scenario: Records generated on session creation
- **WHEN** a session is created for a Classroom whose group has 5 students
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
The system SHALL allow the classroom's Teacher and Admin users to update the attendance statuses of a session's records after the session is created. There SHALL be no closing or finalization state; records remain editable.

#### Scenario: Teacher corrects attendance later
- **WHEN** the classroom's Teacher reopens a past session and changes a status
- **THEN** the updated status is saved
