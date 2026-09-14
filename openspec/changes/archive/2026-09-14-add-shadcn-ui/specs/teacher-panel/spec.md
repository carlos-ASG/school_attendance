# teacher-panel — Spec Delta

## MODIFIED Requirements

### Requirement: Teacher panel authentication
The teacher panel SHALL use django-allauth (on top of Django's authentication system) for login, logout, and password flows. Only authenticated users linked to a Teacher SHALL access the panel; unauthenticated users SHALL be redirected to the account login page. Login SHALL accept username credentials, so existing username/password accounts continue to work unchanged. The login, logout, and password-flow pages SHALL render the shadcn design-system styling with Spanish copy.

#### Scenario: Anonymous user tries to open the panel
- **WHEN** an unauthenticated user opens any panel page
- **THEN** they are redirected to the account login page

#### Scenario: Non-teacher authenticated user tries to open the panel
- **WHEN** an authenticated user with no linked Teacher opens the panel
- **THEN** they are denied access and informed they are not a teacher

#### Scenario: Teacher logs in
- **WHEN** a user linked to a Teacher logs in with valid username credentials
- **THEN** they reach the panel dashboard listing their courses

#### Scenario: Login page renders the styled form
- **WHEN** any user opens the account login page
- **THEN** the login form renders with the design-system components and all visible copy is in Spanish

#### Scenario: Teacher logs out from the panel
- **WHEN** the Teacher submits the logout control on the panel
- **THEN** they are logged out and returned to the account login page

#### Scenario: Teacher resets a forgotten password
- **WHEN** a user requests a password reset for their account
- **THEN** reset instructions are sent (console email backend in development) and the password can be set through the styled allauth flow

## ADDED Requirements

### Requirement: Panel navigation menu
The panel chrome SHALL render a navigation menu built with the design-system navigation-menu component, showing the logged-in user's name, the panel destinations relevant to the user's role, and the logout control submitted as a POST form. All navigation menu text SHALL be in Spanish.

#### Scenario: Teacher sees the navigation menu
- **WHEN** an authenticated Teacher opens any panel page
- **THEN** the page chrome shows the navigation menu in Spanish with the panel destinations and the logout control

#### Scenario: Anonymous visitor has no panel navigation
- **WHEN** an unauthenticated user opens the account login page
- **THEN** the page renders without the panel navigation menu
