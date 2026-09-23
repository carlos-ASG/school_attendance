## ADDED Requirements

### Requirement: Course student detail view

The panel SHALL provide a detail page per student scoped to a Course, at `courses/<course_pk>/students/<pk>/`, reachable from the course detail page's student list where each student's name SHALL link to the page via a quiet-text control. The page SHALL show the student's photo (with a centered image-off icon placeholder when the student has no photo), the student's personal data (given name, paternal and maternal surnames, email when set, and the course's student group), and the student's attendance average in that course rendered in the established `attended/total (percentage%)` format. The attendance average SHALL be computed with the same formula as the course detail student table: records with status `PRESENT`, `LATE`, or `EXCUSED` divided by the course's total session count, multiplied by 100. The page SHALL be restricted to the Course's Teacher, and the student SHALL be a member of the Course's Student Group. The page SHALL provide a way to return to the course detail page, and all page text SHALL be in Spanish.

#### Scenario: Teacher opens a student of their course

- **WHEN** the Teacher opens the student detail page for a student in the group of one of their Courses
- **THEN** the page shows the student's photo (or the image-off placeholder when none), the student's personal data, and the attendance average in that course as `attended/total (percentage%)`

#### Scenario: Student name in the course detail links to the page

- **WHEN** the Teacher views the student table on a course detail page
- **THEN** each student's name links to that student's course-scoped detail page

#### Scenario: Teacher opens a student through another teacher's course

- **WHEN** a Teacher requests the student detail page using the id of a Course they do not teach
- **THEN** the system denies access with a 404

#### Scenario: Student is not a member of the course's group

- **WHEN** a Teacher requests the student detail page for a student who is not in the Course's Student Group
- **THEN** the system denies access with a 404

#### Scenario: Course without sessions shows zero attendance

- **WHEN** the Teacher opens the student detail page for a Course with no sessions
- **THEN** the attendance average shows `0/0 (0%)`

#### Scenario: Page offers navigation back to the course

- **WHEN** the Teacher is on the student detail page
- **THEN** the page provides a way back to the course detail page
