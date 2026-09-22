# attendance-api Delta

## ADDED Requirements

### Requirement: Session updates restricted to the active cycle
The bulk record update endpoint SHALL reject updates for a frozen session — an Attendance Session whose course's School Cycle does not contain today's date — with a 422 response and an error message explaining the session is read-only. Sessions owned by the requesting Teacher whose course's cycle contains today's date (including sessions dated before today) SHALL remain updatable.

#### Scenario: Frozen session update is rejected
- **WHEN** the Teacher sends an update payload for a session they own whose course's cycle does not contain today's date
- **THEN** the endpoint responds 422 with an error message explaining the session is read-only and no records are changed

#### Scenario: Past session inside the active cycle is updated
- **WHEN** the Teacher sends an update payload for a session dated before today whose course's cycle contains today's date
- **THEN** the records are updated and the response contains the saved records

## REMOVED Requirements

### Requirement: Any owned session is editable regardless of date
**Reason**: Replaced by the cycle-freshness rule — sessions belonging to a school cycle that no longer contains today's date are historical and must be immutable for Teachers.
**Migration**: Clients receive a 422 error with a read-only explanation instead of a 200 update for frozen sessions; sessions inside the active cycle behave unchanged.
