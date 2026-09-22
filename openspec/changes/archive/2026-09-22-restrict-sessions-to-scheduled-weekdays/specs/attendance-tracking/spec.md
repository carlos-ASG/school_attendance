# Delta: attendance-tracking

## ADDED Requirements

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
