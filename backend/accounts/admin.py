from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('루저시스템', {'fields': ('nickname', 'loser_badge_count', 'bonus_points', 'last_game_played')}),
    )