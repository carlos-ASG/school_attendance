# Teacher Panel Delta: add-attendance-api

## ADDED Requirements

### Requirement: Unsaved-changes guard on the today session page
The today session page SHALL surface pending (unsaved) attendance changes: the save control SHALL be disabled while no changes are pending and enabled once any record is pending; the page SHALL show a badge with the count of pending records; and closing or navigating away from the page while changes are pending SHALL trigger the browser's unload warning. The guard state SHALL reset after a successful save.

#### Scenario: Save control disabled without pending changes
- **WHEN** the Teacher opens the today session page or has just saved successfully
- **THEN** the save control is disabled and no pending-count badge is shown

#### Scenario: Save control enabled with a pending count
- **WHEN** the Teacher cycles a status or edits a note without saving
- **THEN** the save control becomes enabled and a badge shows the number of pending records

#### Scenario: Leaving with pending changes warns
- **WHEN** the Teacher closes the tab or navigates away with pending changes
- **THEN** the browser shows the unload confirmation warning

#### Scenario: Leaving without pending changes does not warn
- **WHEN** the Teacher closes the tab or navigates away with no pending changes
- **THEN** no unload warning is shown

## MODIFIED Requirements

### Requirement: Attendance recording on the today session page
The today session page SHALL render the attendance editing interface by default: one row per student with a cyclic status button and a notes field. The rows SHALL be rendered client-side by Alpine.js from the session's records serialized into the page as JSON, and every student of the course's group SHALL be listed. Status changes and note edits SHALL be applied to a client-side pending state without any network request. A single save control SHALL submit all pending records to the attendance JSON API in one request; on success the pending state SHALL clear and a success toast SHALL be shown; on failure the pending state SHALL be preserved and an error toast SHALL be shown. Saving SHALL NOT re-render any server-rendered fragment.

#### Scenario: Today's session opens in editing mode
- **WHEN** the Teacher opens the today session page
- **THEN** every student of the course's group is listed with an interactive status button and a notes field, rendered from the serialized records with no extra action required

#### Scenario: Status clicks and note edits stay local
- **WHEN** the Teacher cycles statuses or types notes on the today session page
- **THEN** the changes are held in the client-side pending state and no network request is issued

#### Scenario: Teacher saves all pending changes
- **WHEN** the Teacher clicks the save control with pending changes
- **THEN** all pending records are sent to the attendance API in one request, the pending state clears, and a success toast is shown

#### Scenario: Failed save preserves pending changes
- **WHEN** the save request fails or is rejected
- **THEN** the pending state is preserved, the changes remain staged, and an error toast is shown

### Requirement: Cyclic attendance status button
The today session page SHALL render each student's attendance status as a single button instead of radio buttons. Clicking the button SHALL advance the record's status to the next value in the cycle PRESENT → ABSENT → LATE → EXCUSED and back to PRESENT, updating only the client-side pending state: the change SHALL NOT be persisted and SHALL NOT issue any network request until the Teacher saves. The previous session page SHALL NOT use the cyclic status button.

#### Scenario: Teacher cycles a student's status
- **WHEN** the course Teacher clicks the status button for a student on the today session page
- **THEN** the record's status advances to the next value in the cycle in the client-side state
- **AND** no network request is made and nothing is persisted

#### Scenario: Cycled change persists only on save
- **WHEN** the Teacher cycles one or more statuses and then saves
- **THEN** the cycled statuses are persisted together with the single save request

### Requirement: HTMX fragment responses render template partials
The teacher panel SHALL serve each HTMX-driven swap — history create-form validation errors, past-session batch edit saves, and history session list re-renders after deletion — by rendering the corresponding Django template partial in isolation via the `template_name#partial_name` syntax, returning only the fragment without the full page shell. Fragment templates SHALL be defined inside their host page templates with `{% partialdef %}` rather than as separate partial files, and each fragment SHALL live in the page template whose view renders it. The today session page SHALL NOT use HTMX fragments for attendance recording.

#### Scenario: Create-form error returns only the form
- **WHEN** the Teacher submits the history create-session form with an invalid date via HTMX
- **THEN** the response contains only the re-rendered create-form fragment with the errors

#### Scenario: Batch edit save returns only the read-only panel
- **WHEN** the Teacher submits the past-session batch edit form
- **THEN** the response contains only the re-rendered read-only attendance fragment with a success confirmation

#### Scenario: Session deletion returns only the session list
- **WHEN** the Teacher confirms the deletion of a past session from the history page
- **THEN** the response contains only the re-rendered session list fragment
