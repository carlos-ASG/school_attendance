# Academic Structure Specification

## Purpose

Define the core academic entities (Students, Teachers, Subjects, Student Groups, and Courses) that make up the attendance domain and how they relate to each other.

## Requirements

### Requirement: Student management
The system SHALL allow Admin users to create, update, and delete Student records through Django admin. A Student SHALL have a first name, a last name, and an optional email, and SHALL NOT be a login user.

#### Scenario: Admin creates a student
- **WHEN** an Admin creates a Student with first name, last name and optional email in Django admin
- **THEN** the Student is saved and appears in the admin student list

#### Scenario: Student searchable by name
- **WHEN** an Admin searches the admin student list by first or last name
- **THEN** matching Students are returned

### Requirement: Teacher management
The system SHALL allow Admin users to create, update, and delete Teacher records through Django admin. A Teacher SHALL have a first name, a last name, and an optional one-to-one link to a Django User account; only a Teacher linked to a User SHALL be able to log into the teacher panel.

#### Scenario: Admin creates a teacher without a user account
- **WHEN** an Admin creates a Teacher with name fields and no linked User
- **THEN** the Teacher is saved and appears in the admin teacher list, but cannot log into the teacher panel

#### Scenario: Admin links a teacher to a user account
- **WHEN** an Admin links a Teacher to a Django User
- **THEN** that User gains access to the teacher panel as that Teacher

#### Scenario: Two teachers cannot share one user account
- **WHEN** an Admin tries to link a User that is already linked to another Teacher
- **THEN** the system rejects the change

### Requirement: Subject management
The system SHALL allow Admin users to create, update, and delete Subject records. A Subject SHALL have a unique name and an optional short code.

#### Scenario: Admin creates a subject
- **WHEN** an Admin creates a Subject with a name
- **THEN** the Subject is saved and can be assigned to Courses

#### Scenario: Duplicate subject name rejected
- **WHEN** an Admin creates a Subject with a name that already exists
- **THEN** the system rejects the duplicate

### Requirement: Student group management
The system SHALL allow Admin users to create named Student Groups and assign Students to them. A Student MAY belong to multiple groups, and a group MAY be used by multiple Courses.

#### Scenario: Admin creates a group with students
- **WHEN** an Admin creates a Student Group with a name and selects Students
- **THEN** the group is saved with those Students as members

#### Scenario: Group membership changes
- **WHEN** an Admin adds or removes a Student from a group
- **THEN** the group's membership reflects the change; existing Courses using the group show the updated membership

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

### Requirement: Course physical classroom
A Course SHALL have a physical classroom identifier stored as a string. The field SHALL have a database default of an empty string and SHALL be optional in forms.

#### Scenario: Admin creates a course with a classroom
- **WHEN** an Admin creates a Course and enters the physical classroom identifier
- **THEN** the Course is saved with that classroom

#### Scenario: Existing courses migrate with empty classroom
- **WHEN** the migration runs on existing data
- **THEN** every existing Course receives an empty string for the classroom field
