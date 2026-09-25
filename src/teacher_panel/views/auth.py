from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View

# --- Template views (full pages) ---


class HomeRedirectView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect("account_login")
        if request.user.is_staff:
            return redirect("admin:index")
        return redirect("teacher_panel:dashboard")
