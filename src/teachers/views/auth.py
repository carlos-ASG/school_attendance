from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View

# --- Template views (full pages) ---


class HomeRedirectView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect('account_login')
        if request.user.is_staff:
            return redirect('admin:index')
        return redirect('teachers:dashboard')
