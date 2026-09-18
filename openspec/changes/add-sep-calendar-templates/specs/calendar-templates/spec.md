# Delta: calendar-templates (new capability)

## ADDED Requirements

### Requirement: SEP template dataset

The system SHALL ship a code-defined, versioned dataset of official SEP non-school days per school year, each entry carrying a Spanish name, a type (`ASUETO` or `VACACIONES`), and a start date with an optional end date. The dataset SHALL cover at least the school years relevant to the deployment and SHALL be extendable by adding a school year's entries in code.

#### Scenario: Dataset contains the official holidays of a school year

- **WHEN** the dataset for a school year is inspected
- **THEN** it contains the mandatory holidays (including November 20, May 1, the first Monday of February, and the third Monday of March) and the Christmas and Holy Week vacation windows

#### Scenario: Dataset entries are structurally valid

- **WHEN** the dataset is loaded
- **THEN** every entry has a name, a valid type, a start date, and either no end date or an end date on or after its start date

### Requirement: Apply a SEP template to a cycle

The system SHALL provide an admin action on School Cycles ("Cargar plantilla SEP") that lists the templates whose school-year window overlaps the selected cycle and, on confirmation, creates `NonSchoolDay` entries of that cycle from the chosen template. Each entry SHALL be clipped to the cycle's date range; entries falling entirely outside the cycle SHALL be skipped.

#### Scenario: Applying a template creates clipped entries

- **WHEN** an Admin applies a school-year template to a cycle contained inside that school year
- **THEN** the cycle gains one NonSchoolDay per template entry, with ranges clipped to the cycle bounds

#### Scenario: Entries outside the cycle are skipped

- **WHEN** the chosen template contains entries that fall entirely outside the cycle's range
- **THEN** those entries are not created and the rest are

#### Scenario: Partially overlapping entry is clipped

- **WHEN** a template entry's range extends past the cycle's end date
- **THEN** the created NonSchoolDay covers only the part inside the cycle

#### Scenario: No overlapping templates

- **WHEN** an Admin opens the action for a cycle that no template's school-year window overlaps
- **THEN** the page shows that no template is available and nothing is applied

### Requirement: Idempotent template application

Applying a template SHALL skip any entry whose (clipped) start date already falls inside an existing Non-School Day range of the cycle. Re-applying the same template SHALL NOT duplicate coverage.

#### Scenario: Applying twice creates nothing new

- **WHEN** an Admin applies the same template to the same cycle a second time
- **THEN** no new NonSchoolDay entries are created

#### Scenario: Uncovered entries are still created

- **WHEN** an Admin applies a template after manually deleting one of the previously applied entries
- **THEN** only the uncovered entry is re-created

### Requirement: Applied entries are fully editable

Non-School Days created from a template SHALL be ordinary `NonSchoolDay` records: editable and deletable like hand-created ones, with no behavioral difference. Schools SHALL be able to add extra days (e.g. puente days, local holidays) on top of an applied template.

#### Scenario: Admin edits an applied entry

- **WHEN** an Admin renames or re-dates a NonSchoolDay that came from a template
- **THEN** the change is saved exactly as for a hand-created entry

#### Scenario: Admin adds school-specific days on top

- **WHEN** an Admin adds a "puente" NonSchoolDay to a cycle that already has template-applied entries
- **THEN** the new entry is saved and coexists with the applied ones
