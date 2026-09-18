# Delta: attendance-tracking

## ADDED Requirements

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
