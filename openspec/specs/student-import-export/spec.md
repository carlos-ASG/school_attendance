# Student Import Export Specification

## Purpose

Define the CSV/XLSX import and export of the Student roster inside the Unfold-based Django admin, including round-trip updates by `id`, Spanish file headers, mapping to `StudentGroup` by name with validation, and staff-only access. (Purpose TBD refinement)

## Requirements

### Requirement: Student admin supports import and export
The system SHALL add import and export buttons to the `Student` admin changelist and change form using `django-import-export` integrated with Unfold styling.

#### Scenario: Staff user sees import/export buttons
- **WHEN** a staff user opens the Student changelist
- **THEN** import and export buttons are visible and styled consistently with Unfold

#### Scenario: Staff user exports students
- **WHEN** a staff user clicks "Exportar" and chooses a format
- **THEN** the browser downloads a file containing the student records

### Requirement: Student export includes roster fields
The system SHALL support exporting `id`, `first_name`, `paternal_surname`, `maternal_surname`, `email`, and the names of associated `StudentGroup` records. Both surnames SHALL be required model fields. File column headers SHALL be in Spanish, aligned with the model verbose names: `id`, `Nombre`, `Apellido paterno`, `Apellido materno`, `Correo electrónico`, `Grupos`.

#### Scenario: Export roster to CSV
- **WHEN** a staff user exports students in CSV format
- **THEN** the file contains columns `id`, `Nombre`, `Apellido paterno`, `Apellido materno`, `Correo electrónico`, and `Grupos`

### Requirement: Student import creates or updates records
The system SHALL allow importing students from CSV or XLSX files. Rows with an `id` matching an existing `Student` SHALL update that record; rows with a blank `id` SHALL create new `Student` records.

#### Scenario: Import new students from XLSX
- **WHEN** a staff user uploads a valid XLSX file with new students (blank `id`)
- **THEN** the system creates the corresponding `Student` records

#### Scenario: Import updates existing students by id
- **WHEN** a staff user uploads a file whose rows have `id` values of existing students
- **THEN** the matching students are updated instead of duplicated

#### Scenario: Import preview before confirmation
- **WHEN** a staff user uploads an import file
- **THEN** the system shows a preview of the rows to be imported and requires confirmation before saving

### Requirement: Student import maps groups by name
The system SHALL map the `Grupos` column to `StudentGroup` records by matching group names; missing groups SHALL be reported as validation errors and no group SHALL be created automatically.

#### Scenario: Import with valid group names
- **WHEN** a staff user uploads a file with a comma-separated list of existing group names in the `Grupos` column
- **THEN** the imported students are associated with those groups

#### Scenario: Import with invalid group names
- **WHEN** a staff user uploads a file with a non-existent group name
- **THEN** the import preview shows a validation error and refuses to import until fixed

### Requirement: Import and export are restricted to staff
The system SHALL allow only staff/superuser users to access the Student import and export functionality.

#### Scenario: Non-staff user cannot import
- **WHEN** a non-staff user tries to access the Student import URL
- **THEN** the system denies access
