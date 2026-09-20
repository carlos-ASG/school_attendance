from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import User


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
