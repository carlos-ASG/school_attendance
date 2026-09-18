## Why

Group membership is managed one student at a time in the admin widget, but real schools restructure groups every cycle: some promote a whole group year over year (1°A becomes 2°A), others rebuild all groups each cycle while students pick their own schedules and end up belonging to several groups at once (the existing M2M already supports multi-group membership). What is missing is operational convenience: bulk moves, bulk membership edits, and emptying groups.

## What Changes

- Admin bulk operation "mover miembros": transfer all members of one group to another existing group in a single action (the origin group ends empty).
- Admin bulk operation "vaciar grupo": remove all members from a group in a single action.
- Bulk membership editing: select many students at once to add them to a group, and select many members at once to remove them (mid-cycle altas/bajas).
- Admin operation "duplicar grupo": create a new group copying an existing group's membership — the next-cycle group creation flow (e.g. 1°A → 2°A) starts from the same students and is then adjusted.
- All operations leave past attendance sessions untouched: records keep the students that were in the group at session-creation time.

## Non-goals

- No student self-service enrollment or schedule selection UI.
- No automatic group promotion workflows or scheduled renames.
- No group archiving/hiding.
- No CSV import/export of memberships (the existing student import/export stays as is).

## Capabilities

### New Capabilities
- `group-management`: bulk group membership operations (move all, empty, bulk add/remove, duplicate group) in Django admin.

### Modified Capabilities

(none — `academic-structure` group membership semantics are unchanged; this change adds convenience operations on top)

## Impact

- `src/school/`: admin actions/forms, small service helpers, tests.
- Independent of the calendar changes; most useful once courses belong to cycles (cycle context for each restructure).
