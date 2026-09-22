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

### Requirement: Attendance session future date validation
The system SHALL reject any `AttendanceSession` whose date is in the future. The validation SHALL apply regardless of whether the session is created from the teacher panel, the Django admin, or programmatic code.

#### Scenario: Teacher tries to create a future session from the panel
- **WHEN** the Teacher submits a session creation form with a date greater than today
- **THEN** the system rejects the submission and shows a validation error

#### Scenario: Admin tries to create a future session from the admin
- **WHEN** an Admin saves an `AttendanceSession` with a date greater than today
- **THEN** the save is rejected and a validation error is displayed

#### Scenario: Today is allowed
- **WHEN** a session is saved with today's date
- **THEN** the save succeeds

#### Scenario: Past date is allowed
- **WHEN** a session is saved with a date before today
- **THEN** the save succeeds

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

### Requirement: Attendance freeze by school cycle
The system SHALL treat an Attendance Session as frozen (read-only for Teachers) when the session's course's School Cycle does not contain today's date. A frozen session's records SHALL NOT be editable or deletable by Teachers through any teacher-facing surface (panel or API). Sessions whose course's cycle contains today's date SHALL remain editable. When today's date falls outside every cycle (a gap between cycles), all sessions SHALL be frozen.

#### Scenario: Session inside the active cycle stays editable
- **WHEN** a session's course's School Cycle contains today's date
- **THEN** the session is not frozen and its records remain editable by the course's Teacher

#### Scenario: Session from a past cycle is frozen
- **WHEN** a session's course's School Cycle ended before today
- **THEN** the session is frozen and its records cannot be edited or deleted by Teachers through the panel or the API

#### Scenario: Today falls in a gap between cycles
- **WHEN** no School Cycle contains today's date
- **THEN** every session is frozen, including sessions of the most recently ended cycle

#### Scenario: Course without a cycle is frozen
- **WHEN** a session's course has no School Cycle assigned
- **THEN** the session is frozen

### Requirement: Attendance editing
The system SHALL allow the course's Teacher and Admin users to update the attendance statuses and optional notes of a session's records after the session is created, provided the session is not frozen (its course's School Cycle contains today's date). There SHALL be no closing or finalization state; records of non-frozen sessions remain editable. Admin users remain unrestricted.

#### Scenario: Teacher corrects attendance later
- **WHEN** the course's Teacher reopens a past session whose course's cycle contains today's date and changes a status or note
- **THEN** the updated status and note are saved

#### Scenario: Teacher edit on a frozen session is rejected
- **WHEN** the course's Teacher submits an attendance change for a session whose course's cycle does not contain today's date
- **THEN** no status or note change is persisted and the Teacher receives an error message explaining the session is read-only

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

### Requirement: Attendance session calendar validation
The system SHALL reject the creation of an Attendance Session whose date falls outside its Course's School Cycle or on a Non-School Day of that cycle. The validation SHALL apply regardless of whether the session is created from the teacher panel, the Django admin, or the session-creation code paths, and SHALL produce user-readable Spanish error messages that name the offending cycle or non-school day. Validation SHALL apply only at creation time: sessions that already exist SHALL NOT be invalidated or blocked from editing when the calendar changes afterwards.

#### Scenario: Date outside the course's cycle is rejected
- **WHEN** a session creation is attempted with a date outside the Course's School Cycle range
- **THEN** the system rejects it with a validation error naming the cycle and no session is created

#### Scenario: Non-school day is rejected
- **WHEN** a session creation is attempted with a date that is a Non-School Day of the Course's cycle
- **THEN** the system rejects it with a validation error naming the non-school day and no session is created

#### Scenario: In-cycle, non-holiday date is allowed
- **WHEN** a session creation is attempted with a past date inside the Course's cycle that is not a Non-School Day
- **THEN** the session is created

#### Scenario: Admin creation is validated too
- **WHEN** an Admin saves an AttendanceSession in the Django admin with a date that is a Non-School Day of the Course's cycle
- **THEN** the save is rejected with a validation error

#### Scenario: Existing sessions survive calendar changes
- **WHEN** an Admin marks a date as a Non-School Day after a session on that date already exists
- **THEN** the existing session and its records remain unchanged and editable

### Requirement: Attendance session schedule validation
The system SHALL reject the creation of an Attendance Session whose date falls on a weekday that does not match any of the Course's ClassSchedule slots. A Course with no schedule slots SHALL have no valid session dates. The validation SHALL apply regardless of whether the session is created from the teacher panel, the Django admin, or the session-creation code paths, and SHALL produce user-readable Spanish error messages naming the weekday or the missing schedule. Validation SHALL apply only at creation time: sessions that already exist SHALL NOT be invalidated or blocked from editing when the course's schedule changes afterwards. A slot's start and end times SHALL NOT affect validation; only the weekday is considered.

#### Scenario: Scheduled weekday is allowed
- **WHEN** a session creation is attempted for a date inside the Course's cycle, not a Non-School Day, whose weekday matches one of the Course's schedule slots
- **THEN** the session is created

#### Scenario: Non-scheduled weekday is rejected
- **WHEN** a session creation is attempted for a date whose weekday matches none of the Course's schedule slots
- **THEN** the system rejects it with a validation error naming the weekday and no session is created

#### Scenario: Course without schedule is rejected
- **WHEN** a session creation is attempted for a Course that has no schedule slots
- **THEN** the system rejects it with a validation error explaining the course has no assigned schedule and no session is created

#### Scenario: Admin creation is validated too
- **WHEN** an Admin saves an AttendanceSession in the Django admin with a date on a weekday the Course does not meet
- **THEN** the save is rejected with a validation error and no session is created

#### Scenario: Existing sessions survive schedule changes
- **WHEN** a schedule slot is removed from a Course after a session on that weekday already exists
- **THEN** the existing session and its records remain valid and editable
