"""Swagger UI docs with a spec selector.

One page at /api/docs renders Swagger UI configured with `urls` +
`urls.primaryName` (Swagger UI Topbar plugin) so the user can switch between
a filtered OpenAPI schema per auth type:

- attendance.json: endpoints authenticated by teacher session cookie
- desktop.json: endpoints authenticated by X-API-Key (desktop stations)

Each JSON is `api.get_openapi_schema()` with `paths` filtered and its own
`info.title`. The default NinjaAPI docs page is disabled (`docs_url=None`);
the full combined schema stays at /api/openapi.json.
"""

import json
from collections.abc import Callable
from typing import Any

from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from ninja.openapi.docs import Swagger, render_template

from .api import api

DESKTOP_PREFIX = '/api/desktop/'

ATTENDANCE_SPEC_NAME = 'Asistencia (cookie de sesión)'
DESKTOP_SPEC_NAME = 'Integraciones escritorio (X-API-Key)'

SPECS: dict[str, dict[str, Any]] = {
    'attendance': {
        'name': ATTENDANCE_SPEC_NAME,
        'title': 'API de Asistencia Escolar',
        'include': lambda path: not path.startswith(DESKTOP_PREFIX),
    },
    'desktop': {
        'name': DESKTOP_SPEC_NAME,
        'title': 'API de Integraciones Desktop',
        'include': lambda path: path.startswith(DESKTOP_PREFIX),
    },
}


def filtered_schema(spec: str) -> dict[str, Any]:
    definition = SPECS[spec]
    schema = dict(api.get_openapi_schema())
    schema['paths'] = {
        path: operations
        for path, operations in schema['paths'].items()
        if definition['include'](path)
    }
    schema['info'] = {**schema['info'], 'title': definition['title']}
    return schema


def schema_view(request: HttpRequest, spec: str) -> HttpResponse:
    if spec not in SPECS:
        raise Http404(f'Unknown docs spec: {spec}')
    return JsonResponse(filtered_schema(spec), json_dumps_params={'indent': 2})


class MultiSpecSwagger(Swagger):
    """Swagger UI page offering the per-auth spec selector in the topbar.

    Uses the vendored swagger-ui-standalone-preset (ninja's bundle lacks the
    Topbar plugin) and StandaloneLayout so the `urls` selector renders.
    """

    template = 'api/swagger_multispec.html'

    def render_page(self, request: HttpRequest, api, **kwargs: Any) -> HttpResponse:
        settings = {**self.settings}
        settings['layout'] = 'StandaloneLayout'
        settings['urls'] = [
            {'url': reverse('api-docs:schema', args=[slug]), 'name': definition['name']}
            for slug, definition in SPECS.items()
        ]
        settings['urls.primaryName'] = ATTENDANCE_SPEC_NAME
        context = {
            'swagger_settings': json.dumps(settings, indent=1),
            'api': api,
            'add_csrf': any(
                getattr(auth, 'csrf', False) for auth in api.auth  # type: ignore[union-attr]
            ),
        }
        return render_template(request, self.template, self.template_cdn, context)


multi_spec_swagger = MultiSpecSwagger()


def docs_view(request: HttpRequest) -> HttpResponse:
    return multi_spec_swagger.render_page(request, api)
