# Design: add-group-management

## Context

`StudentGroup.students` is a M2M to `Student` — multi-group membership already works at the schema level, and the admin change form uses `filter_horizontal` (multi-select add/remove of members one group at a time). What real schools lack is cycle-rollover convenience: moving a whole group's members to another group, emptying groups that get rebuilt each cycle, and creating next cycle's group from this cycle's membership (1°A → 2°A). Attendance semantics already guarantee past sessions keep their records (`attendance-tracking`: records are generated at session creation).

This change is independent of the calendar changes, but is most useful once Courses belong to cycles — the restructure always happens between cycles.

## Goals / Non-Goals

**Goals:**

- Atomic bulk operations on group membership from Django admin: move all members to another group, empty a group, duplicate a group with its membership.
- Pin multi-select membership editing (add/remove many at once) as supported behavior.

**Non-Goals:**

- No student self-service enrollment or schedule picking; no automatic promotion workflows or renames; no group archiving; no membership import/export.

## Decisions

### D1: Service functions in `src/school/group_ops.py`, admin actions as thin wrappers

`move_group_members(origin, destination)`, `empty_group(group)`, `duplicate_group(group, new_name)` — each a single atomic function, directly unit-testable. The admin actions validate input and call them. Mirrors the `calendar.py` helper pattern from `add-school-calendar` (D5): business rules in the school app, UI layers stay thin.

### D2: Move = transfer, origin ends empty

"Move all members" removes members from the origin and adds them to the destination in one transaction; the origin group itself is kept (an empty shell — deleting groups is a separate concern, and `Course` FKs are `PROTECT`ed anyway). Each student's other group memberships are untouched (only the origin→destination pair changes). Adding a student who is already a member of the destination is a no-op for that student (M2M set semantics). Alternative rejected: "copy" semantics (origin keeps members) — that is exactly the duplicate operation; keeping move and duplicate separate makes both unambiguous.

### D3: Empty = confirmation-guarded destructive action

Unfold admin action with a confirmation step; removes all memberships of the group in one transaction; the group itself remains. Cancellation does nothing.

### D4: Duplicate = intermediate page asking for the new group's name

`StudentGroup.name` is unique, so the action opens an intermediate page (unfold) asking for the new name; on submit, `duplicate_group` creates the group and copies the membership in one transaction. The origin is untouched. This is the 1°A → 2°A rollover: the new group starts identical and is then adjusted (move-ins/outs) with the bulk editing already available.

### D5: Bulk add/remove stays on the existing `filter_horizontal` widget

The change form's multi-select widget already supports selecting many students to add or remove at once. No new UI is built for this; the spec pins the behavior so it stays supported. Alternative rejected: a dedicated bulk-membership page — duplicates the widget for no capability gain.

### D6: No attendance special-casing

The operations only touch the M2M table. Past sessions and their records are untouched by construction (records are per-session rows), and future sessions pick up the new membership — both already spec'd behaviors in `attendance-tracking` ("Group changes do not alter past sessions").

## Risks / Trade-offs

- [Moving members into a group used by active courses changes future session rosters silently] → same as any membership edit today; the confirmation page names the destination group so the operator sees the target; no further safeguard in v1.
- [Duplicate creates near-identical groups; typos in names] → the intermediate page validates name uniqueness and shows the member count being copied.
- [Operations scale with M2M size] → single SQL statements per operation; school-scale memberships are trivial.

## Migration Plan

No schema changes — new module, admin actions, tests. Rollback: remove actions.

## Open Questions

- Should "mover miembros" also be offered as a per-student bulk action on the Student changelist (move selected students)? Deferred — the group-centric flow covers the described cycle-rollover workflows.
