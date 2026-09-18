## 1. Service layer

- [ ] 1.1 Create `src/school/group_ops.py` with `move_group_members(origin, destination)` (atomic transfer; origin ends empty, kept; other memberships untouched; re-adding an existing member is a no-op). Given a group with members, when moving to a destination, then the M2M changes land in one transaction and past session records are untouched.
- [ ] 1.2 Add `empty_group(group)` (atomic removal of all memberships; group kept). Given a group with members, when emptying, then the group remains with zero members.
- [ ] 1.3 Add `duplicate_group(group, new_name)` (atomic: create group + copy membership; unique-name validation raises a readable Spanish error). Given "1° A" with 25 members, when duplicating as "2° A", then the new group exists with the same 25 members and the origin is unchanged.
- [ ] 1.4 Unit tests for the three operations: atomicity (failure mid-operation leaves no partial state), membership semantics (other groups untouched, no duplicates), and the existing-name rejection.

## 2. Admin actions

- [ ] 2.1 Add the "mover miembros" action to `StudentGroupAdmin` with an intermediate page to pick the destination group (showing both groups' member counts); applying calls the service and returns to the changelist with a Spanish success message. Admin test: the move is performed and reported.
- [ ] 2.2 Add the "vaciar grupo" action with an unfold confirmation; test that confirming empties the group and cancelling changes nothing.
- [ ] 2.3 Add the "duplicar grupo" action with an intermediate page asking for the new name (member count preview); test the happy path and the duplicate-name validation error.
- [ ] 2.4 Verify the existing `filter_horizontal` multi-select covers the bulk add/remove scenarios and pin them with admin form tests.

## 3. Verification

- [ ] 3.1 Run `uv run manage.py check` and the full test suite (`uv run manage.py test`).
- [ ] 3.2 Manual smoke: move a seeded group, empty another, duplicate a third, and confirm past sessions' records stay intact.
