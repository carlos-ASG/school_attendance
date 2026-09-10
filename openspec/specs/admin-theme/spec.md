# Admin Theme Specification

## Purpose

Define the Django admin theme based on django-unfold, including Unfold base classes for admin and inline classes, sidebar navigation configuration, Spanish-language admin text, and the guarantee that the `/panel/` teacher interface remains untouched by the theme. (Purpose TBD refinement)

## Requirements

### Requirement: Unfold is installed and enabled as the admin theme
The system SHALL include `django-unfold` in project dependencies and register `unfold` (and required contrib apps) in `INSTALLED_APPS` before `django.contrib.admin`.

#### Scenario: Successful dependency installation
- **WHEN** a developer runs the dependency sync command
- **THEN** `django-unfold` is available and `uv run manage.py check` passes

#### Scenario: Admin uses Unfold templates
- **WHEN** a staff user visits `/admin/`
- **THEN** the page is rendered with the Unfold theme

### Requirement: All admin classes use Unfold base classes
The system SHALL make every `ModelAdmin` class inherit from `unfold.admin.ModelAdmin` and every inline class inherit from `unfold.admin.TabularInline` or `unfold.admin.StackedInline`.

#### Scenario: Student admin uses Unfold styling
- **WHEN** a staff user opens the Student changelist or change form
- **THEN** the page uses Unfold components, filters, and form styling

#### Scenario: Classroom admin inlines use Unfold styling
- **WHEN** a staff user opens the Classroom change form
- **THEN** the `ClassSchedule` inline is rendered with Unfold inline styling

### Requirement: Sidebar navigation is configured
The system SHALL configure `UNFOLD["SIDEBAR"]` so that the existing school models are reachable and a "Reports" entry links to the custom reports page.

#### Scenario: Reports link appears in sidebar
- **WHEN** a staff user views any admin page
- **THEN** the sidebar contains a "Reports" navigation item that links to the reports page

### Requirement: Admin interface text is in Spanish
The Django admin interface SHALL display all user-visible text in Spanish, including the site title and header, sidebar navigation, model and field labels, choice labels (weekday and attendance status), filter names, column headers, and Django's built-in admin strings. Code identifiers, model field names, choice values, and URL paths SHALL remain in English.

#### Scenario: Admin renders in Spanish
- **WHEN** a staff user views any Django admin page
- **THEN** every visible label (navigation, model names, field names, buttons, filters) is shown in Spanish

#### Scenario: Code identifiers stay in English
- **WHEN** a developer inspects the code, model field names, or admin URLs
- **THEN** identifiers, field names, and URL paths remain in English (e.g. `/admin/school/student/`)

### Requirement: Teacher panel remains unchanged
The system SHALL NOT apply Unfold styling or behavior to the `/panel/` teacher interface.

#### Scenario: Teacher panel keeps existing templates
- **WHEN** a teacher visits `/panel/`
- **THEN** the page renders with the existing project templates, not Unfold admin templates
