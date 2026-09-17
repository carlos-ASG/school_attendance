## Why

The teacher panel chrome has a decorative sidebar toggle button (topbar `panel_left` icon) that does nothing, five placeholder sidebar items pointing to `#`, and a logout control duplicated in the topbar while the sidebar footer logout link is broken (GET link against allauth's POST-only logout). The sidebar needs real navigation and the toggle needs to work.

## What Changes

- Make the sidebar expandable/collapsible with Alpine.js: pressing the topbar `panel_left` trigger toggles between the icon rail (`w-16`, tooltips) and an expanded sidebar (`w-64`, icon + label). State persists in `localStorage`.
- Reduce the sidebar to a single navigation item: Home (icon `house`) linking to `teachers:dashboard`, marked active only when on the dashboard.
- Move the logout control from the topbar to the sidebar footer as a POST form (matches allauth's POST requirement); the topbar keeps only the teacher name.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `teacher-panel`: The "Panel navigation menu" requirement changes — panel chrome now uses a collapsible sidebar (instead of the navigation-menu chrome) with a single Home destination, an expand/collapse toggle in the topbar, and the logout control in the sidebar footer.

## Non-goals

- No mobile/overlay drawer behavior; desktop toggle only.
- No new sidebar destinations beyond Home (course navigation stays in-page via breadcrumbs).
- No changes to views, URLs, models, or the API layer.

## Impact

- Templates only: `src/teachers/templates/teachers/base.html` and cotton components `src/core_ui/templates/cotton/sidebar/index.html`, `sidebar/item.html`, `topbar/trigger.html`.
- Tailwind rebuild required (`uv run manage.py tailwind build`) for new utility classes.
- Logout is now a POST form in the sidebar footer (also fixes the broken GET logout link).
