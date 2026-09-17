# theme-toggle Delta Spec

## ADDED Requirements

### Requirement: Theme toggle button in the topbar
The teacher panel topbar SHALL render a theme toggle button immediately to the right of the authenticated user's name, sharing a single flex row with it. The button SHALL be a design-system `c-button` in ghost variant with icon size, and its `aria-label` SHALL be in Spanish. The button SHALL be rendered inside the authenticated-user conditional of the panel base template.

#### Scenario: Button renders next to the username
- **WHEN** an authenticated teacher loads any panel page
- **THEN** the topbar shows the toggle button right beside the username text inside a shared flex wrapper, styled as a design-system ghost icon button

#### Scenario: Button is not rendered for unauthenticated sessions
- **WHEN** the panel base template renders with an unauthenticated user
- **THEN** neither the username nor the theme toggle button is rendered

### Requirement: Toggle switches theme without a page load
Clicking the toggle button SHALL add or remove the `dark` class on the root `<html>` element client-side via Alpine, with no navigation, form submission, or HTMX request. The button SHALL dispatch a `toggle-theme` window event consumed by the root scope, mirroring the existing `toggle-sidebar` dispatch pattern.

#### Scenario: Toggle from light to dark
- **WHEN** the theme is light and the user clicks the toggle button
- **THEN** the `dark` class is added to `<html>` and the page renders with the dark design-system variables, with no page reload

#### Scenario: Toggle from dark to light
- **WHEN** the theme is dark and the user clicks the toggle button
- **THEN** the `dark` class is removed from `<html>` and the page renders with the light design-system variables, with no page reload

### Requirement: Icon reflects the active theme
The toggle button SHALL display the sun icon when the theme is light and the moon-star icon when the theme is dark, swapping reactively with the theme state without a reload. Both icons SHALL be cotton icon components authored in-repo (lucide sun and moon-star SVGs), sized consistently with other topbar icons.

#### Scenario: Sun shown in light theme
- **WHEN** the theme is light
- **THEN** the button shows the sun icon component and the moon-star icon is not visible

#### Scenario: Moon shown in dark theme
- **WHEN** the theme is dark
- **THEN** the button shows the moon-star icon component and the sun icon is not visible

### Requirement: Theme persists across page loads
The selected theme SHALL persist in `localStorage` under the key `theme` with values `light` or `dark`, and SHALL be restored on any subsequent full page load or navigation within the panel.

#### Scenario: Reload preserves the dark theme
- **WHEN** the user sets the dark theme and then performs a full reload or navigates to another panel page
- **THEN** the page renders dark without the user toggling again

#### Scenario: First visit defaults to light
- **WHEN** a browser has never toggled the theme (no `theme` key in `localStorage`)
- **THEN** the panel renders in light theme

### Requirement: Theme is applied before first paint
The panel base template SHALL include an inline script that runs before first paint, reads the persisted theme, and applies the `dark` class to `<html>` so loading in dark mode produces no light flash.

#### Scenario: Dark theme loads without a light flash
- **WHEN** the persisted theme is dark and the user performs a full page load
- **THEN** the `dark` class is present on `<html>` before the first paint

### Requirement: Panel styles support the dark theme
The teacher panel SHALL use design-system theme variables instead of hardcoded light colors for its chrome: the body background SHALL come from `bg-background` rather than a fixed light utility class, and `teachers/css/panel.css` SHALL NOT contain hardcoded light-only colors that leave panel content unreadable under the dark theme. Design-system components used by the panel SHALL likewise rely on theme tokens rather than hardcoded palette colors: the `c-table` component SHALL use `divide-border`, `*:text-foreground`, and `*:even:bg-muted` (auto-flipping with `.dark`), and quiet text links SHALL be provided as the `c-quiet_text` component (`text-primary`, `decoration-border`, ring/focus variants) with `href` proxied through `{{ attrs }}`.

#### Scenario: Body background follows the theme
- **WHEN** the dark theme is active on any panel page
- **THEN** the body background renders from the background theme variable instead of the fixed `bg-zinc-50` class

#### Scenario: Panel CSS remains legible in dark theme
- **WHEN** the dark theme is active and elements styled by `teachers/css/panel.css` are visible
- **THEN** those elements use theme variables or dark-aware values and remain readable

#### Scenario: Table renders with theme variables
- **WHEN** any panel page renders a `c-table` in dark theme
- **THEN** the table's dividers, text, and zebra rows use `divide-border` / `*:text-foreground` / `*:even:bg-muted` and flip with the theme, with no hardcoded gray utilities in the component markup

#### Scenario: Quiet text link renders through the component
- **WHEN** `course_session_history.html` renders the session date link
- **THEN** it is rendered by `<c-quiet_text>` as an `<a>` with the intact `href` and semantic quiet-link classes that adapt to the dark theme
