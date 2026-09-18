# Delta: group-management (new capability)

## ADDED Requirements

### Requirement: Move all members between groups

The system SHALL provide a Django admin action on Student Groups that transfers all members of a selected group to another existing group in a single atomic operation. The origin group SHALL end with no members, the origin group itself SHALL NOT be deleted, and each moved student SHALL keep any memberships in other groups. Adding a student who is already a member of the destination SHALL be a no-op for that student.

#### Scenario: Admin moves a whole group

- **WHEN** an Admin selects a group with 30 members and the "mover miembros" action, picks a destination group, and confirms
- **THEN** all 30 students become members of the destination, the origin ends with no members, and the origin group still exists

#### Scenario: Other memberships are untouched

- **WHEN** a moved student also belongs to a third group
- **THEN** that membership remains after the move

#### Scenario: Students already in the destination are not duplicated

- **WHEN** some of the origin's members already belong to the destination
- **THEN** the move completes and those students appear once in the destination

#### Scenario: Past sessions keep their records

- **WHEN** a group is moved after sessions were recorded for courses using the origin group
- **THEN** those sessions and their records remain unchanged

### Requirement: Empty a group

The system SHALL provide a Django admin action on Student Groups that removes all members of a selected group in a single atomic operation, behind an explicit confirmation. The group itself SHALL NOT be deleted. Cancelling the confirmation SHALL change nothing.

#### Scenario: Admin empties a group

- **WHEN** an Admin selects a group with members and the "vaciar grupo" action, and confirms
- **THEN** the group remains with no members

#### Scenario: Cancelled confirmation does nothing

- **WHEN** the Admin dismisses the confirmation dialog
- **THEN** the group's membership is unchanged

### Requirement: Duplicate a group

The system SHALL provide a Django admin action on Student Groups that creates a new group with a chosen name, copying all members of the selected group in a single atomic operation. The origin group and its membership SHALL remain unchanged. The new name SHALL be validated for uniqueness.

#### Scenario: Admin duplicates a group for the next cycle

- **WHEN** an Admin selects group "1° A" and the "duplicar grupo" action, enters the name "2° A", and confirms
- **THEN** a new group "2° A" exists with exactly the members of "1° A", and "1° A" is unchanged

#### Scenario: Duplicate with an existing name is rejected

- **WHEN** the Admin enters a name that already exists
- **THEN** the action page shows a validation error and no group is created

### Requirement: Bulk membership editing

The system SHALL allow Admin users to add or remove many students at once in a group, via multi-select membership editing on the group's admin change form.

#### Scenario: Admin adds several students at once

- **WHEN** an Admin selects multiple students in the group form's member selector and saves
- **THEN** all of them become members of the group

#### Scenario: Admin removes several students at once

- **WHEN** an Admin deselects multiple members in the group form's member selector and saves
- **THEN** none of them remain members of the group
