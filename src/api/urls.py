from django.urls import path

from . import docs

app_name = "api-docs"

urlpatterns = [
    path("docs", docs.docs_view, name="docs"),
    path("docs/<slug:spec>.json", docs.schema_view, name="schema"),
]
