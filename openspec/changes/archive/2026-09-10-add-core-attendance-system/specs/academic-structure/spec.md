## ADDED Requirements

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
- **THEN** the Subject is saved and can be assigned to Classrooms

#### Scenario: Duplicate subject name rejected
- **WHEN** an Admin creates a Subject with a name that already exists
- **THEN** the system rejects the duplicate

### Requirement: Student group management
The system SHALL allow Admin users to create named Student Groups and assign Students to them. A Student MAY belong to multiple groups, and a group MAY be used by multiple Classrooms.

#### Scenario: Admin creates a group with students
- **WHEN** an Admin creates a Student Group with a name and selects Students
- **THEN** the group is saved with those Students as members

#### Scenario: Group membership changes
- **WHEN** an Admin adds or removes a Student from a group
- **THEN** the group's membership reflects the change; existing Classrooms using the group show the updated membership

### Requirement: Classroom composition
The system SHALL represent a Classroom as exactly one Student Group, one Teacher, one Subject, and one schedule. The schedule SHALL consist of one or more weekly slots, each with a weekday, a start time, and an end time.

#### Scenario: Admin creates a classroom
- **WHEN** an Admin creates a Classroom selecting a group, a teacher, a subject, and at least one schedule slot
- **THEN** the Classroom is saved with its schedule

#### Scenario: Classroom requires a schedule slot
- **WHEN** an Admin saves a Classroom with no schedule slots
- **THEN** the system rejects it, because a classroom must have a schedule

### Requirement: Classroom uniqueness
The system SHALL allow the same Teacher to teach the same Subject in multiple Classrooms, as long as each Classroom differs by Student Group and/or schedule. A Classroom SHALL be unique for the combination of Teacher, Subject, and Student Group; different meeting times for that combination SHALL be expressed as additional schedule slots of the same Classroom.

#### Scenario: Same teacher and subject, different groups
- **WHEN** an Admin creates two Classrooms with the same Teacher and Subject but different Student Groups
- **THEN** both Classrooms are saved as distinct classrooms

#### Scenario: Duplicate teacher, subject and group rejected
- **WHEN** an Admin creates a Classroom with a Teacher, Subject and Student Group combination that already exists
- **THEN** the system rejects it as a duplicate classroom

#### Scenario: Same teacher, subject and group on more days
- **WHEN** an Admin adds another schedule slot (e.g., Wednesday) to an existing Classroom
- **THEN** the Classroom's schedule covers both slots without creating a new Classroom
