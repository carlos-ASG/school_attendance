# Attendance API Delta: add-attendance-api

## ADDED Requirements

### Requirement: Attendance API authentication
The attendance JSON API SHALL accept only requests from authenticated users linked to a Teacher, authenticated by the Django session cookie with CSRF protection enforced. Unauthenticated requests SHALL be rejected with HTTP 401; authenticated users without a linked Teacher SHALL be rejected with HTTP 403; requests missing a valid CSRF token SHALL be rejected.

#### Scenario: Anonymous request is rejected
- **WHEN** an unauthenticated client calls any attendance API endpoint
- **THEN** the response is HTTP 401 and no data is modified

#### Scenario: Non-teacher authenticated request is rejected
- **WHEN** an authenticated user with no linked Teacher calls any attendance API endpoint
- **THEN** the response is HTTP 403 and no data is modified

#### Scenario: Request without CSRF token is rejected
- **WHEN** a session-authenticated request without a valid CSRF token calls a mutating attendance API endpoint
- **THEN** the request is rejected and no data is modified

### Requirement: Bulk record update endpoint
The API SHALL provide `PATCH /api/sessions/{session_id}/records` accepting a JSON body with a `records` list where each entry carries the record `id`, the `status` (one of PRESENT, ABSENT, LATE, EXCUSED), and `notes`. The endpoint SHALL update the referenced records of the referenced session in a single atomic transaction and SHALL respond with the saved records and their authoritative field values.

#### Scenario: Teacher saves pending records
- **WHEN** the course Teacher sends a payload of valid records belonging to their session
- **THEN** all records are updated with the sent statuses and notes in one transaction and the response contains the saved records

#### Scenario: Invalid status rejected
- **WHEN** a payload entry carries a status outside PRESENT, ABSENT, LATE, EXCUSED
- **THEN** the response is HTTP 422 and no records are modified

#### Scenario: Notes are saved together with statuses
- **WHEN** a payload entry includes both a status and notes
- **THEN** both fields are persisted on that record

### Requirement: Session ownership scoping
The bulk record update endpoint SHALL only operate on Attendance Sessions whose Course belongs to the requesting Teacher. A request referencing a nonexistent session or a session owned by another teacher SHALL be rejected with HTTP 404 and no records SHALL be modified.

#### Scenario: Another teacher's session
- **WHEN** a Teacher sends an update payload referencing a session whose Course they do not teach
- **THEN** the response is HTTP 404 and no records are modified

#### Scenario: Nonexistent session
- **WHEN** a Teacher sends an update payload referencing a session id that does not exist
- **THEN** the response is HTTP 404 and no records are modified

### Requirement: Record membership validation
Every record id in the payload SHALL be validated to belong to the referenced session. A payload referencing an unknown record id or a record of a different session SHALL be rejected with HTTP 422 identifying the offending entries, and no records SHALL be modified.

#### Scenario: Record from another session
- **WHEN** the payload references a record that belongs to a different session
- **THEN** the response is HTTP 422 identifying that entry and no records are modified

#### Scenario: Unknown record id
- **WHEN** the payload references a record id that does not exist
- **THEN** the response is HTTP 422 identifying that entry and no records are modified

#### Scenario: Mixed valid and invalid entries are atomic
- **WHEN** the payload contains valid entries and at least one invalid entry
- **THEN** the response is HTTP 422 and none of the valid entries are saved

### Requirement: Duplicate payload entries resolve last-wins
When the same record id appears multiple times in one payload, the last entry for that id SHALL be applied.

#### Scenario: Same record sent twice
- **WHEN** the payload contains two entries for the same record id with different statuses
- **THEN** the record is updated with the status of the last entry

### Requirement: Any owned session is editable regardless of date
The bulk record update endpoint SHALL accept updates for any Attendance Session owned by the requesting Teacher, whether dated today or in the past.

#### Scenario: Past session updated through the API
- **WHEN** the Teacher sends an update payload for a session dated before today that they own
- **THEN** the records are updated and the response contains the saved records
