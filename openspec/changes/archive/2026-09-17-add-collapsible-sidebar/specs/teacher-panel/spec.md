## MODIFIED Requirements

### Requirement: Panel navigation menu
The panel chrome SHALL render a collapsible sidebar built with the design-system sidebar components: a collapsed icon rail by default, expandable to an expanded sidebar showing icon and label via a toggle control with the `panel_left` icon in the topbar. The sidebar SHALL show a single navigation item — Home — linking to the panel dashboard and highlighted as active only while on it, and SHALL present the logout control in its footer submitted as a POST form. The expanded/collapsed choice SHALL persist across page loads in the browser. All navigation text SHALL be in Spanish, and the topbar SHALL show the logged-in user's name.

#### Scenario: Teacher sees the sidebar navigation
- **WHEN** an authenticated Teacher opens any panel page
- **THEN** the page chrome shows the collapsed sidebar rail with the Home item in Spanish and the logout control in the footer

#### Scenario: Teacher expands and collapses the sidebar
- **WHEN** the Teacher presses the topbar toggle control with the `panel_left` icon
- **THEN** the sidebar alternates between the collapsed icon rail (icons with hover tooltips) and the expanded sidebar (icons with visible labels)

#### Scenario: Sidebar state persists across navigation
- **WHEN** the Teacher expands the sidebar and then navigates to another panel page or reloads
- **THEN** the sidebar renders expanded (and collapsed likewise when saved collapsed)

#### Scenario: Home item navigates to the dashboard
- **WHEN** the Teacher clicks the Home item in the sidebar from any panel page
- **THEN** they reach the panel dashboard, where the Home item is highlighted as active; on other pages it is not

#### Scenario: Teacher logs out from the sidebar
- **WHEN** the Teacher presses the "Cerrar sesión" control in the sidebar footer
- **THEN** a POST request logs them out and they are returned to the account login page

#### Scenario: Anonymous visitor has no panel navigation
- **WHEN** an unauthenticated user opens the account login page
- **THEN** the page renders without the panel sidebar or topbar chrome
