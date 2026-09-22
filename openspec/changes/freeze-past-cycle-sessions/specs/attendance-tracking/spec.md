# attendance-tracking Delta

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Attendance editing
The system SHALL allow the course's Teacher and Admin users to update the attendance statuses and optional notes of a session's records after the session is created, provided the session is not frozen (its course's School Cycle contains today's date). There SHALL be no closing or finalization state; records of non-frozen sessions remain editable. Admin users remain unrestricted.

#### Scenario: Teacher corrects attendance later
- **WHEN** the course's Teacher reopens a past session whose course's cycle contains today's date and changes a status or note
- **THEN** the updated status and note are saved

#### Scenario: Teacher edit on a frozen session is rejected
- **WHEN** the course's Teacher submits an attendance change for a session whose course's cycle does not contain today's date
- **THEN** no status or note change is persisted and the Teacher receives an error message explaining the session is read-only
