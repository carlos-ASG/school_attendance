# Admin Reports Specification

## Purpose

Define the staff-only Reports page inside the Django admin: summary metrics, attendance status distribution (pie), daily attendance trend (line), attendance by classroom (bar), and a date range filter, all within the Unfold layout. (Purpose TBD refinement)

## Requirements

### Requirement: Reports page is reachable from the admin sidebar
The system SHALL add a staff-only custom admin page at `/admin/school/attendancesession/reports/` and link it from the Unfold sidebar.

#### Scenario: Staff user opens Reports
- **WHEN** a staff user clicks the "Reports" sidebar item
- **THEN** the browser navigates to the Reports page and renders within the Unfold layout

#### Scenario: Non-staff user is blocked
- **WHEN** a non-staff user tries to access the Reports URL directly
- **THEN** the system denies access

### Requirement: Reports page displays summary metrics
The system SHALL display summary cards showing total students, total classrooms, and the number of attendance sessions in the selected date range.

#### Scenario: Default date range shows current metrics
- **WHEN** a staff user opens the Reports page with the default filter
- **THEN** the page shows the current counts for students, classrooms, and sessions

### Requirement: Reports page shows attendance-by-status pie chart
The system SHALL render a pie chart showing the distribution of `AttendanceRecord` statuses (`PRESENT`, `ABSENT`, `LATE`, `EXCUSED`) for the selected date range.

#### Scenario: Pie chart reflects filtered records
- **WHEN** a staff user views the Reports page
- **THEN** the pie chart displays one segment per status with counts proportional to the records

### Requirement: Reports page shows daily attendance trend line chart
The system SHALL render a line chart showing the count of attendance records per day, split by status, for the selected date range.

#### Scenario: Line chart shows daily breakdown
- **WHEN** a staff user views the Reports page
- **THEN** the line chart displays one line per status with dates on the X axis

### Requirement: Reports page shows attendance-by-classroom bar chart
The system SHALL render a bar chart showing attendance counts grouped by classroom (subject name) for the selected date range.

#### Scenario: Bar chart groups by classroom
- **WHEN** a staff user views the Reports page
- **THEN** the bar chart displays one bar per classroom with the total number of records

### Requirement: Reports page supports a date range filter
The system SHALL allow the staff user to filter the data by a start date and an end date; the default range SHALL be the last 30 days.

#### Scenario: Changing the date range updates the charts
- **WHEN** a staff user selects a different date range and submits the filter
- **THEN** all metrics and charts update to reflect the selected range
