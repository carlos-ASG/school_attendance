## ADDED Requirements

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
