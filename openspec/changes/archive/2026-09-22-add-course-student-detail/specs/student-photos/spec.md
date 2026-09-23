## MODIFIED Requirements

### Requirement: Optional photo per student managed from the Django admin

Each Student SHALL have an optional photo settable from the Student admin change form. The photo SHALL be stored under `MEDIA_ROOT` and SHALL NOT be displayed anywhere in the teacher panel EXCEPT the course student detail page, nor in the admin changelist or any import/export flow.

#### Scenario: Admin uploads a photo

- **WHEN** an Admin attaches an image file to a Student's change form and saves
- **THEN** the Student has a stored photo and the change form shows the upload widget again on reload

#### Scenario: Photo stays optional

- **WHEN** a Student is created or saved without a photo
- **THEN** saving succeeds and the Student has no photo

#### Scenario: No display outside the admin form and the student detail page

- **WHEN** any teacher-panel page other than the course student detail page (dashboard, course detail, session pages) renders
- **THEN** no student photo is requested or shown

#### Scenario: Photo displayed on the course student detail page

- **WHEN** the course's Teacher opens the student detail page for a student with a stored photo
- **THEN** the photo is displayed on the page
