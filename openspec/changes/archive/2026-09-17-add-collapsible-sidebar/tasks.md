## 1. Cotton sidebar components

- [x] 1.1 Update `src/core_ui/templates/cotton/sidebar/index.html`: add `x-data` owning `open` + `toggle()` with `localStorage['sidebar-open']` seeding/persistence, `@toggle-sidebar.window="toggle()"`, `shrink-0`, and width binding `:class="open && 'w-64'"` on top of the static `w-16`
- [x] 1.2 Update `src/core_ui/templates/cotton/sidebar/item.html`: toggle anchor layout via `:class` (`grid place-content-center` ↔ `flex items-center gap-3`), add label span `x-show="open" x-cloak`, gate tooltip span with `x-show="!open"`

## 2. Topbar trigger and panel chrome

- [x] 2.1 Update `src/core_ui/templates/cotton/topbar/trigger.html`: add `@click="$dispatch('toggle-sidebar')"` to the button (standalone triggers dispatching events need their own Alpine root — bare `x-data` on the button, matching `toast/trigger.html` — otherwise Alpine 3 never binds directives outside an `x-data` tree)
- [x] 2.2 Update `src/teachers/templates/teachers/base.html`: replace the five placeholder items with a single Home item (`icon="house"`, `tooltip="Inicio"`, `href="{% url 'teachers:dashboard' %}"`, `:active="request.resolver_match.url_name == 'dashboard'"`)
- [x] 2.3 Update `src/teachers/templates/teachers/base.html` sidebar footer: replace the GET `<a>` with a POST form to `{% url 'account_logout' %}` (`{% csrf_token %}`, `hx-boost="false"`, `log_out` icon, label/tooltip "Cerrar sesión" reusing the inherited `open` scope)
- [x] 2.4 Update `src/teachers/templates/teachers/base.html` topbar: remove the logout form, keep the teacher name span

## 3. Verification

- [x] 3.1 Rebuild Tailwind (`uv run manage.py tailwind build`) and run `uv run manage.py check` and `uv run manage.py test`
- [x] 3.2 Manual pass with `uv run manage.py runserver`: toggle expands/collapses, state persists across navigation/reload, Home navigates to dashboard and is active only there, sidebar logout POSTs and redirects to login, tooltips only when collapsed
