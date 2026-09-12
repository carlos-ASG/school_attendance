## ADDED Requirements

### Requirement: Course physical classroom
A Course SHALL have a physical classroom identifier stored as a string. The field SHALL have a database default of an empty string and SHALL be optional in forms.

#### Scenario: Admin creates a course with a classroom
- **WHEN** an Admin creates a Course and enters the physical classroom identifier
- **THEN** the Course is saved with that classroom

#### Scenario: Existing courses migrate with empty classroom
- **WHEN** the migration runs on existing data
- **THEN** every existing Course receives an empty string for the classroom field

## MODIFIED Requirements

### Requirement: Course composition
The system SHALL represent a Course as exactly one Student Group, one Teacher, one Subject, one physical classroom, and one schedule. The schedule SHALL consist of one or more weekly slots, each with a weekday, a start time, and an end time.

#### Scenario: Admin creates a course
- **WHEN** an Admin creates a Course selecting a group, a teacher, a subject, a physical classroom, and at least one schedule slot
- **THEN** the Course is saved with its schedule and classroom

#### Scenario: Course requires a schedule slot
- **WHEN** an Admin saves a Course with no schedule slots
- **THEN** the system rejects it, because a course must have a schedule

### Requirement: Course uniqueness
The system SHALL allow the same Teacher to teach the same Subject in multiple Courses, as long as each Course differs by Student Group and/or schedule. A Course SHALL be unique for the combination of Teacher, Subject, and Student Group; different meeting times for that combination SHALL be expressed as additional schedule slots of the same Course.

#### Scenario: Same teacher and subject, different groups
- **WHEN** an Admin creates two Courses with the same Teacher and Subject but different Student Groups
- **THEN** both Courses are saved as distinct courses

#### Scenario: Duplicate teacher, subject and group rejected
- **WHEN** an Admin creates a Course with a Teacher, Subject and Student Group combination that already exists
- **THEN** the system rejects it as a duplicate course

#### Scenario: Same teacher, subject and group on more days
- **WHEN** an Admin adds another schedule slot (e.g., Wednesday) to an existing Course
- **THEN** the Course's schedule covers both slots without creating a new Course
