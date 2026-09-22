# teacher-panel Delta

## MODIFIED Requirements

### Requirement: Past session review and correction
The previous session page SHALL render the session's records read-only by default, listing every student with their current status and note. The page SHALL offer an "Editar" control that enables a batch edit form: one row per student with a status selector (combobox or select) offering the four statuses and a notes field. No change SHALL be persisted until the Teacher submits the form; submitting SHALL save all rows at once and return the page to the read-only view with a confirmation. For a frozen session (its course's School Cycle does not contain today's date), the "Editar" control SHALL NOT enable the batch edit form; it SHALL open an alert dialog explaining that the session belongs to a cycle that is no longer active and is read-only. A frozen session's edit form submission SHALL be rejected with an error message and the read-only view.

#### Scenario: Past session opens read-only
- **WHEN** the Teacher opens the previous session page of a session dated before today
- **THEN** every student is listed with their current status and note shown read-only and no editing controls are rendered

#### Scenario: Teacher enables editing on a past session
- **WHEN** the Teacher clicks the "Editar" control on the previous session page of a session whose course's cycle contains today's date
- **THEN** a batch edit form renders with one row per student, each with a status selector and a notes field

#### Scenario: Status selector offers the four statuses in Spanish
- **WHEN** the Teacher opens a status selector on the batch edit form
- **THEN** the options are exactly Presente, Ausente, Tarde, Justificado

#### Scenario: Teacher submits the batch edit form
- **WHEN** the Teacher changes one or more statuses or notes and submits the form of a session whose course's cycle contains today's date
- **THEN** all changes are persisted together and the read-only view re-renders in place with a success confirmation

#### Scenario: Teacher exits editing without submitting
- **WHEN** the Teacher leaves edit mode without submitting the form
- **THEN** no status or note changes are persisted

#### Scenario: Frozen session stays read-only when edit mode is requested
- **WHEN** the Teacher opens the previous session page of a frozen session with the edit flag (`?edit=1`)
- **THEN** the page renders the read-only view and no edit form is rendered

#### Scenario: Frozen session's edit button opens a read-only notice dialog
- **WHEN** the Teacher clicks the "Editar" control on the previous session page of a frozen session
- **THEN** an alert dialog opens explaining the session belongs to a cycle that is no longer active and cannot be edited, with a single acknowledgment control

#### Scenario: Frozen session's edit form submission is rejected
- **WHEN** the Teacher submits the batch edit form for a frozen session (e.g. a stale form posted directly)
- **THEN** no changes are persisted, an error message explains the session is read-only, and the read-only view re-renders in place

### Requirement: Session deletion from the panel
The panel SHALL allow the Teacher to delete an Attendance Session from the history page's "Acciones" column and from the today session page. Both delete controls SHALL require confirmation through an alert dialog before the deletion is submitted. Deleting a past session from the history page SHALL remove the session and its records and re-render the session list in place without a full page reload. Deleting a today session from the today session page SHALL remove the session and its records and redirect the Teacher to the course detail page. A frozen session (its course's School Cycle does not contain today's date) SHALL NOT be deletable: the delete control SHALL NOT be rendered on its session page, and a delete request submitted directly SHALL be rejected with an error message.

#### Scenario: Teacher deletes a past session from the history
- **WHEN** the Teacher confirms the deletion of a past session of a non-frozen course from the history page's "Acciones" column
- **THEN** the session and its records are removed and the session list re-renders in place without the deleted session

#### Scenario: Teacher deletes the last session of a course from the history
- **WHEN** the Teacher confirms the deletion of the course's only listed session
- **THEN** the re-rendered session list shows the empty state

#### Scenario: Teacher deletes a today session from the today page
- **WHEN** the Teacher confirms the deletion of a session dated today from the today session page
- **THEN** the session and its records are removed and the Teacher is redirected to the course detail page

#### Scenario: Deletion is cancelled
- **WHEN** the Teacher dismisses the delete confirmation dialog without confirming
- **THEN** no session is removed

#### Scenario: Frozen session hides the delete control
- **WHEN** the Teacher opens the previous session page of a frozen session
- **THEN** no delete control is rendered for that session

#### Scenario: Frozen session deletion is rejected
- **WHEN** the Teacher submits a delete request for a frozen session directly
- **THEN** the session and its records are not removed and an error message explains the session is read-only
