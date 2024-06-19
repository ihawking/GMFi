from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from common.admin import ReadOnlyModelAdmin, ModelAdmin
from users.models import User, Manager


# Register your models here.


@admin.register(User)
class UserAdmin(ReadOnlyModelAdmin):
    list_display = ("username",)


@admin.register(Manager)
class ManagerAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "is_staff", "is_active")
