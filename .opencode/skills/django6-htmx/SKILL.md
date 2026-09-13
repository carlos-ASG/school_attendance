---
name: django6-htmx
description: Use when building or refactoring Django 6 + HTMX features — template partials ({% partialdef %}, {% partial %}, render('page.html#partial_name')), HTMX fragment endpoints, flat template layout, or when the user mentions htmx, partials, fragments, or template structure in a Django app. Also covers the byte-diff verification harness for template refactors.
license: MIT
---

# Django 6 + HTMX patterns

Patterns for Django (>= 6.0) apps with django-htmx, verified byte-identical in
this repo's `teachers` app. Run all Django commands via `uv run manage.py <cmd>`.

## Recommended folder structure

Per app under `src/<app>/`:

```
src/<app>/
├── urls.py
├── forms.py
├── views/                  # package, NOT a single views.py
│   ├── __init__.py         # re-exports every view class
│   ├── mixins.py           # auth/permission mixins
│   ├── dashboard.py        # one module per page/flow
│   └── session_detail.py   # page view + ITS fragment endpoints, together
└── templates/<app>/
    ├── base.html
    ├── dashboard.html              # flat: one file per page/URL
    ├── course_detail.html
    └── session_detail.html         # contains its partialdef fragments
```

Rules:

- **Flat templates.** `templates/<app>/dashboard.html`, not
  `templates/<app>/dashboard/dashboard_template.html`. No `_template` suffix,
  no per-page subdirectories.
- **No separate partial files.** `*_partial.html` files are the pre-Django 6
  pattern; fragments are `{% partialdef %}` blocks inside their host page.
- One template file per page/URL. A fragment belongs in the page template
  that renders it (Locality of Behaviour).
- Fragment endpoint views live in the same module as the page's main view.
- `views/__init__.py` re-exports so `urls.py` imports from `.views`.

## Template partials

Django 6 built-ins: `{% partialdef %}`, `{% endpartialdef %}`, `{% partial %}`,
and the `template.html#partial_name` load/render syntax. They replace both
separate partial files and `django-template-partials`.

Fragments needed by HTMX endpoints are defined in the page template, then
rendered in isolation by the view:

```django
{# page template: fragments live after {% endblock %} #}
{% block content %}
    <div id="attendance-panel">
        {% if editable %}
            {% partial attendance_panel %}
        {% else %}
            {% partial attendance_readonly %}
        {% endif %}
    </div>
{% endblock %}
{% partialdef attendance_panel %}<ul class="messages">...</ul>
<form hx-post="{% url 'app:page' ... %}" hx-target="#attendance-panel" hx-swap="innerHTML">
    ...
</form>
{% endpartialdef attendance_panel %}
```

```python
# fragment endpoint — renders ONLY the fragment, no base chrome
return render(request, 'app/page.html#attendance_panel', context)
```

Placement rules (all verified byte-identical in practice):

- **Non-inline `partialdef`s go after `{% endblock %}`, definitions joined
  back-to-back** (no blank lines between `{% endpartialdef x %}` and the next
  `{% partialdef %}`). They are registered at parse time and never rendered by
  `{% extends %}` — safe for registration and invisible in full-page output.
- **`inline` renders at the definition position.** Use
  `{% partialdef name inline %}` only when you want in-place rendering, and
  position the definition exactly where the markup must appear (inside the
  target `<div>`, at the spot an `{% include %}` used to occupy).
- **Reuse within the same template** with `{% partial name %}`; adjust context
  per use with `{% with %}` — `{% partial %}` takes no arguments:

  ```django
  {% with record=form.instance %}{% partial record_status_button %}{% endwith %}
  ```

- Rendering `page.html#partial` works fine on templates that
  `{% extends %}` a base — only the fragment renders, never the base chrome.

Whitespace gotchas (bite only when output must stay byte-identical):

1. Text nodes *between* `{% partialdef %}` definitions inside rendered regions
   emit stray newlines → keep definitions outside blocks (or join them).
2. When replacing `{% include %}` of a separate file with inlined markup, the
   included file's trailing newline is consumed by the tag — reproduce it
   (usually one extra blank line before the next line of the host).
3. `{% partialdef x %}<content>` — start content on the same line as the tag
   to avoid a leading newline; end `{% endpartialdef %}` right after the final
   newline of the fragment.

## Views and HTMX wiring

Dependencies/config (django-htmx >= 1.23):

```python
INSTALLED_APPS = [..., 'django_htmx', ...]
MIDDLEWARE = [..., 'django_htmx.middleware.HtmxMiddleware']
```

```django
{# base.html #}
{% load django_htmx %}
<head>...{% htmx_script %}</head>
<body hx-headers='{"x-csrftoken": "{{ csrf_token }}"}'>
```

View patterns:

```python
from django_htmx.http import retarget

def post(self, request, *args, **kwargs):
    ...
    if form.is_valid():
        if request.htmx:
            return render(request, 'app/page.html#panel', context)  # success swap
        return HttpResponseRedirect(request.get_full_path())        # no-JS fallback
    response = render(request, 'app/page.html#panel', context)      # errors
    if request.htmx:
        return retarget(response, '#panel')                          # force target
    return response
```

- Every HTMX POST/GET endpoint has a non-HTMX fallback (redirect or full page)
  so the page still works without JS.
- Errors: re-render the *same* fragment plus error context, then `retarget()`
  to the element that must be swapped.
- After destructive actions from a page, respond with
  `HttpResponse(headers={'HX-Redirect': reverse(...)})` for HTMX requests.
- Small fragments (a status button) target themselves with
  `hx-target="this" hx-swap="outerHTML"`; forms target their container div.
- Never render a full page for an `request.htmx` request.

## Byte-diff verification harness

When refactoring views/templates without a test suite, prove output is
unchanged: capture rendered HTML before and after, byte-diff.

1. Copy the dev DB: `cp db.sqlite3 /tmp/work/db.sqlite3`, seed anything needed
   in the copy, snapshot it: `cp /tmp/work/db.sqlite3 /tmp/work/db.snapshot`.
2. Script (run via `uv run python script.py`), patching settings *after*
   `django.setup()` and before any DB access:

   ```python
   import os
   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
   import django
   django.setup()
   from django.conf import settings
   settings.DATABASES["default"]["NAME"] = "/tmp/work/db.sqlite3"
   settings.ALLOWED_HOSTS = ["testserver"]  # test runner normally adds this

   from django.test import Client
   c = Client()  # CSRF checks off by default
   HX = {"HTTP_HX_REQUEST": "true"}

   # login once, then capture full pages and fragments:
   #   c.get('/some/page/')                    -> full page
   #   c.post(url, data, **HX)                 -> HTMX fragment
   ```

3. Normalize per-request CSRF tokens before writing files:

   ```python
   import re
   def norm(content: bytes) -> bytes:
       s = content.decode()
       s = re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]*"', r'\g<1>CSRF', s)
       s = re.sub(r'("x-csrftoken": ")[^"]*"', r'\1CSRF"', s)
       return s.encode()
   ```

4. Restore the snapshot before every run
   (`cp /tmp/work/db.snapshot /tmp/work/db.sqlite3`) so mutations during one
   capture run don't skew the next.
5. `diff -r out_pre out_post` — the only acceptable output is "no diff".
   Missing blank lines mid-file mean a whitespace gotcha above.

Baseline checks: `uv run manage.py check` before and after.

## References

- Django 6 template partials:
  https://docs.djangoproject.com/en/stable/ref/templates/language/#template-partials
- django-htmx docs: https://django-htmx.readthedocs.io/
- Migration from django-template-partials:
  https://github.com/carltongibson/django-template-partials/blob/main/Migration.md
