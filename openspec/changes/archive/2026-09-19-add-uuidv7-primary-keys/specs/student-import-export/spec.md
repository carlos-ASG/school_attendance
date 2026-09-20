# student-import-export Delta

## MODIFIED Requirements

### Requirement: Student export includes roster fields
The system SHALL support exporting `id`, `first_name`, `paternal_surname`, `maternal_surname`, `email`, and the names of associated `StudentGroup` records. Both surnames SHALL be required model fields. The exported `id` SHALL be the student's UUID v7 primary key rendered as a UUID string. File column headers SHALL be in Spanish, aligned with the model verbose names: `id`, `Nombre`, `Apellido paterno`, `Apellido materno`, `Correo electrónico`, `Grupos`.

#### Scenario: Export roster to CSV
- **WHEN** a staff user exports students in CSV format
- **THEN** the file contains columns `id`, `Nombre`, `Apellido paterno`, `Apellido materno`, `Correo electrónico`, and `Grupos`, with UUID string values in the `id` column

### Requirement: Student import creates or updates records
The system SHALL allow importing students from CSV or XLSX files. Rows with an `id` matching an existing `Student` (a UUID string) SHALL update that record; rows with a blank `id` SHALL create new `Student` records, each receiving a newly generated UUID v7 primary key. An `id` that is neither blank nor a valid UUID SHALL be reported as a validation error and not imported.

#### Scenario: Import new students from XLSX
- **WHEN** a staff user uploads a valid XLSX file with new students (blank `id`)
- **THEN** the system creates the corresponding `Student` records with generated UUID v7 ids

#### Scenario: Import updates existing students by id
- **WHEN** a staff user uploads a file whose rows have UUID string `id` values of existing students
- **THEN** the matching students are updated instead of duplicated

#### Scenario: Malformed id rejected
- **WHEN** a row carries an `id` that is neither blank nor a valid UUID string
- **THEN** the import preview reports a validation error for that row and the row is not imported

#### Scenario: Import preview before confirmation
- **WHEN** a staff user uploads an import file
- **THEN** the system shows a preview of the rows to be imported and requires confirmation before saving
