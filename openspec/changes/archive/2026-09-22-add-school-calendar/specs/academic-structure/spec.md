# Delta: academic-structure

## MODIFIED Requirements

### Requirement: Course composition

The system SHALL represent a Course as exactly one Student Group, one Teacher, one Subject, one physical classroom, one School Cycle, and one schedule. The schedule SHALL consist of one or more weekly slots, each with a weekday, a start time, and an end time. The School Cycle SHALL be mandatory on every Course, and deleting a School Cycle that still has Courses SHALL be blocked.

#### Scenario: Admin creates a course

- **WHEN** an Admin creates a Course selecting a group, a teacher, a subject, a physical classroom, a School Cycle, and at least one schedule slot
- **THEN** the Course is saved with its schedule, classroom, and cycle

#### Scenario: Course requires a schedule slot

- **WHEN** an Admin saves a Course with no schedule slots
- **THEN** the system rejects it, because a course must have a schedule

#### Scenario: Course requires a school cycle

- **WHEN** an Admin saves a Course without selecting a School Cycle
- **THEN** the system rejects the save with a validation error

#### Scenario: Deleting a cycle with courses is blocked

- **WHEN** an Admin tries to delete a School Cycle that still has Courses assigned
- **THEN** the deletion is blocked

### Requirement: Course uniqueness

The system SHALL allow the same Teacher to teach the same Subject in multiple Courses, as long as each Course differs by Student Group and/or School Cycle. A Course SHALL be unique for the combination of Teacher, Subject, Student Group, and School Cycle; the same Teacher, Subject, and Student Group MAY recur in a different School Cycle. Different meeting times for that combination within one cycle SHALL be expressed as additional schedule slots of the same Course.

#### Scenario: Same teacher and subject, different groups

- **WHEN** an Admin creates two Courses with the same Teacher and Subject but different Student Groups
- **THEN** both Courses are saved as distinct courses

#### Scenario: Duplicate teacher, subject and group within a cycle rejected

- **WHEN** an Admin creates a Course with a Teacher, Subject and Student Group combination that already exists in the same School Cycle
- **THEN** the system rejects it as a duplicate course

#### Scenario: Same teacher, subject and group in a different cycle is allowed

- **WHEN** an Admin creates a Course with a Teacher, Subject and Student Group combination that already exists in a different School Cycle
- **THEN** the Course is saved as a distinct course of that cycle

#### Scenario: Same teacher, subject and group on more days

- **WHEN** an Admin adds another schedule slot (e.g., Wednesday) to an existing Course
- **THEN** the Course's schedule covers both slots without creating a new Course
