from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class AccountAdapter(DefaultAccountAdapter):
    """Allauth adapter preserving the panel's post-login role routing."""

    def get_login_redirect_url(self, request):
        if request.user.is_staff:
            return reverse('admin:index')
        return reverse('teachers:dashboard')

    def is_open_for_signup(self, request):
        # Business rule: accounts are created by admins via django-admin.
        # Flip to True (and re-add the login-page link) to open registration.
        return False
