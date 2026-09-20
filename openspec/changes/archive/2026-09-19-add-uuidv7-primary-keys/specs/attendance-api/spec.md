# attendance-api Delta

## MODIFIED Requirements

### Requirement: Bulk record update endpoint
The API SHALL provide `PATCH /api/sessions/{session_id}/records` accepting a JSON body with a `records` list where each entry carries the record `id`, the `status` (one of PRESENT, ABSENT, LATE, EXCUSED), and `notes`. The `session_id` path parameter, the record `id` in each payload entry, the `id` in each response record, and the `id` in each error detail entry SHALL be UUID values (UUID strings in JSON). A malformed `session_id` SHALL be rejected with HTTP 422 by schema validation. The endpoint SHALL update the referenced records of the referenced session in a single atomic transaction and SHALL respond with the saved records and their authoritative field values.

#### Scenario: Teacher saves pending records
- **WHEN** the course Teacher sends a payload of valid records, identified by UUID strings, belonging to their session
- **THEN** all records are updated with the sent statuses and notes in one transaction and the response contains the saved records with UUID string ids

#### Scenario: Invalid status rejected
- **WHEN** a payload entry carries a status outside PRESENT, ABSENT, LATE, EXCUSED
- **THEN** the response is HTTP 422 and no records are modified

#### Scenario: Notes are saved together with statuses
- **WHEN** a payload entry includes both a status and notes
- **THEN** both fields are persisted on that record

#### Scenario: Malformed session id rejected by validation
- **WHEN** a request targets a `session_id` path segment that is not a valid UUID
- **THEN** the response is HTTP 422 and no records are modified
