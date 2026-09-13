from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View


# --- Template views (full pages) ---

class LoginView(auth_views.LoginView):
    template_name = 'teachers/login/login_template.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('admin:index')
        return reverse('teachers:dashboard')


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('teachers:login')


class HomeRedirectView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('teachers:login')
        if request.user.is_staff:
            return redirect('admin:index')
        return redirect('teachers:dashboard')
