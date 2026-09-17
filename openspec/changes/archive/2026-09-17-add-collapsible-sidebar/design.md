## Context

The teacher panel chrome (`src/teachers/templates/teachers/base.html`) renders `<c-sidebar>` (fixed `w-16` icon rail with hover tooltips, five placeholder items with `href="#"`), a sidebar footer logout that is a GET `<a>` (broken: django-allauth ≥65 requires POST for logout), and a working logout POST form in the topbar. `<c-topbar.trigger />` renders a `panel_left` icon button with no behavior. Alpine.js is vendored and deferred-loaded; the `[x-cloak]` CSS rule already exists in `input.css` and `panel.css`. Cotton components live in `src/core_ui/templates/cotton/` and are used only by the teacher panel chrome.

## Goals / Non-Goals

**Goals:**

- Toggle the sidebar between collapsed rail (`w-16`, tooltips) and expanded (`w-64`, icon + label) from the topbar `panel_left` button.
- Persist the choice in `localStorage` across navigation and reloads.
- Single sidebar item: Home → `teachers:dashboard`, active only on the dashboard.
- Logout POST form in the sidebar footer; topbar keeps only the teacher name.

**Non-Goals:**

- Mobile overlay/drawer behavior, responsive breakpoints.
- Width animations beyond a simple opacity fade on labels.
- New sidebar destinations or changes to views/URLs/models.

## Decisions

- **State ownership: `x-data` on the `<aside>` in `sidebar/index.html`.** The sidebar owns its `open` state plus a `toggle()` that writes `localStorage['sidebar-open']` and seeds it on init. Alternatives rejected: an Alpine store registered in `teachers/base.html` (couples the design-system component to page-level JS and breaks standalone reuse) and hoisting `x-data` to the layout wrapper in `base.html` (same coupling, plus attrs plumbing through the trigger component).
- **Cross-tree communication via event**: the trigger is a sibling of the `<aside>`, outside its Alpine scope, so `topbar/trigger.html` does `$dispatch('toggle-sidebar')` and the aside listens with `@toggle-sidebar.window="toggle()"` — the documented Alpine pattern for sibling components. The trigger stays decoupled from sidebar internals. As a standalone element outside any `x-data` tree, the trigger carries a bare `x-data` on itself (same convention as `toast/trigger.html`): Alpine 3 initializes only `[x-data]`-rooted trees, so directives on rootless elements are never bound.
- **Width via static `w-16` + Alpine `:class="open && 'w-64'"`**: keeps the pre-Alpine render collapsed (no flash) since Alpine merges bound classes with the static class attribute.
- **Labels and tooltips**: item anchors toggle layout with `:class` (`grid place-content-center` ↔ `flex items-center gap-3`); the label span uses `x-show="open"` with `x-cloak` (rule already shipped), the tooltip span uses `x-show="!open"`. No `overflow-hidden` anywhere — it would clip the tooltips, which are absolutely positioned outside the aside.
- **Active state via cotton expression**: `:active="request.resolver_match.url_name == 'dashboard'"` on the item — Django `{% if %}` cannot be placed inside a cotton component tag's attribute area.
- **Logout as POST form in the footer slot** (in `base.html`, not a new component): mirrors `sidebar.item` styling, reuses the inherited `open` scope for its label/tooltip, includes `{% csrf_token %}` and `hx-boost="false"` like the previous topbar form. Fixes the broken GET logout link as a side effect.

## Risks / Trade-offs

- [Brief width flash when reloading while saved expanded] → Accepted: server-side rendering cannot know `localStorage`; the rail renders collapsed until Alpine initializes, then expands. Labels are `x-cloak`-hidden pre-Alpine.
- [`w-16` + `w-64` coexist when expanded] → Safe: Tailwind emits `w-64` after `w-16` in the compiled CSS, so the expanded width wins deterministically.
- [No-JS / Alpine failure] → Graceful degradation: the rail renders statically with hover tooltips; logout (POST form) and the Home link keep working without JS.
- [Component/store naming collisions if other panels adopt `c-sidebar`] → The event name `toggle-sidebar` and `localStorage` key are generic; revisit scoping if a second sidebar consumer appears.

## Migration Plan

Template-only change; no data migration. Ship templates, rebuild Tailwind (`uv run manage.py tailwind build`), verify with `manage.py check`, the test suite, and a manual pass (toggle, persistence, navigation, POST logout). Rollback is reverting the four template files.

## Open Questions

None.
