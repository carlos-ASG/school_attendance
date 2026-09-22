# Delta: school-calendar (new capability)

## ADDED Requirements

### Requirement: School cycle definition

The system SHALL allow Admin users to create School Cycles with a name (e.g. "Agosto – Diciembre 2026"), a cycle type (ANNUAL, SEMESTRAL, or QUATRIMESTRAL), a start date, and an end date. The start date SHALL be before the end date.

#### Scenario: Admin creates a cycle

- **WHEN** an Admin creates a School Cycle with name "Agosto – Diciembre 2026", type SEMESTRAL, a start date, and an end date after the start
- **THEN** the cycle is saved and appears in the admin cycle list

#### Scenario: Start not before end is rejected

- **WHEN** an Admin saves a School Cycle whose start date is on or after its end date
- **THEN** the system rejects the save with a validation error

### Requirement: Cycle duration bounds by type

The system SHALL reject a School Cycle whose duration in days falls outside the bounds for its type: ANNUAL 240–400 days, SEMESTRAL 110–240 days, QUATRIMESTRAL 85–145 days. The bounds SHALL be named constants in the school app, adjustable without schema changes.

#### Scenario: Short "annual" cycle is rejected

- **WHEN** an Admin saves an ANNUAL cycle running from February to April (about 3 months)
- **THEN** the system rejects the save with a validation error

#### Scenario: Real-length semester is accepted

- **WHEN** an Admin saves a SEMESTRAL cycle from around August 18 to around December 12 (about 116 days)
- **THEN** the cycle is saved

#### Scenario: Real-length cuatrimestre is accepted

- **WHEN** an Admin saves a QUATRIMESTRAL cycle from around September 7 to around December 19 (about 103 days)
- **THEN** the cycle is saved

### Requirement: One cycle at a time

The system SHALL reject a School Cycle whose date range overlaps any other School Cycle's date range. Consecutive cycles and gaps between cycles SHALL be allowed.

#### Scenario: Overlapping cycle is rejected

- **WHEN** an Admin saves a School Cycle whose range overlaps an existing cycle's range
- **THEN** the system rejects the save with a validation error

#### Scenario: Adjacent cycles are allowed

- **WHEN** an Admin saves a cycle starting the day after an existing cycle ends
- **THEN** the cycle is saved

#### Scenario: Gap between cycles is allowed

- **WHEN** an Admin saves a cycle that starts weeks after the previous cycle ended (e.g. after summer)
- **THEN** the cycle is saved

### Requirement: Non-school day definition

The system SHALL allow Admin users to define Non-School Days belonging to a School Cycle, each with a name, a type (ASUETO, VACACIONES, or OTRO), a start date, and an optional end date. A NULL end date SHALL mean a single non-working day; a non-NULL end date SHALL mean an inclusive date range (vacation period). A Non-School Day's date or range SHALL fall inside its cycle's bounds. Overlapping Non-School Days SHALL be allowed.

#### Scenario: Single non-working day

- **WHEN** an Admin creates a Non-School Day named "20 de noviembre" with a start date and no end date in an active cycle
- **THEN** it is saved as a single non-working day of that cycle

#### Scenario: Vacation range

- **WHEN** an Admin creates a Non-School Day named "Vacaciones de navidad" with a start date and an end date after it, both inside the cycle
- **THEN** it is saved as an inclusive range of that cycle

#### Scenario: Range outside the cycle is rejected

- **WHEN** an Admin saves a Non-School Day whose start or end date falls outside its cycle's bounds
- **THEN** the system rejects the save with a validation error

#### Scenario: Overlapping non-school days are allowed

- **WHEN** an Admin saves a Non-School Day that overlaps another Non-School Day of the same cycle
- **THEN** both are saved (the union of both ranges is non-working time)

### Requirement: Admin management of the calendar

The system SHALL provide Django admin management for School Cycles with a Non-School Day inline on the Cycle admin page, and SHALL expose the cycle field on the Course admin. Deleting a School Cycle that still has Courses SHALL be blocked. Deleting a School Cycle without Courses SHALL delete its Non-School Days.

#### Scenario: Admin manages non-school days inline

- **WHEN** an Admin opens a School Cycle's change page in the admin
- **THEN** its Non-School Days can be added, edited, and removed inline

#### Scenario: Deleting a cycle with courses is blocked

- **WHEN** an Admin tries to delete a School Cycle that has Courses assigned
- **THEN** the deletion is blocked

#### Scenario: Deleting a childless cycle removes its non-school days

- **WHEN** an Admin deletes a School Cycle with no Courses
- **THEN** the cycle and its Non-School Days are removed
