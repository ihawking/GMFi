from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from common.admin import ReadOnlyModelAdmin, ModelAdmin
from users.models import Player, Manager


# Register your models here.


@admin.register(Player)
class PlayerAdmin(ReadOnlyModelAdmin):
    list_display = ("uid",)


@admin.register(Manager)
class ManagerAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "is_staff", "is_active")
