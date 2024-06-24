from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_celery_results.models import TaskResult
from web3.auto import w3 as w3_auto

from common.admin import ModelAdmin
from globals.models import Project

admin.site.unregister(TaskResult)


# Register your models here.
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"

    def clean_collection_address(self):
        collection_address = self.cleaned_data.get("collection_address")

        if not w3_auto.is_checksum_address(collection_address):  # 验证表单中的 uri 指向的 chain id，是否和数据库中的数据匹配
            raise forms.ValidationError("请输入大小写混合的校验和格式地址")
        return collection_address

    def clean_ip_white_list(self):
        """
        检查设置的白名单IP 地址或网络是否合法
        :return: None
        """
        ip_white_list = self.cleaned_data.get("ip_white_list")

        from common.utils.security import is_ip_or_network

        if not all(is_ip_or_network(addr) for addr in ip_white_list.split(",")):
            raise forms.ValidationError(_("IP 白名单格式错误."))
        return ip_white_list


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = (
        "distribution_account",
        "collection_address",
        "webhook",
    )
    readonly_fields = ("distribution_account",)
    form = ProjectForm
    fieldsets = (
        (
            "系统",
            {"fields": ("webhook", "notification_failed_times")},
        ),
        ("资金", {"fields": ("distribution_account", "collection_address")}),
        ("安全", {"fields": ("ip_white_list", "hmac_key")}),
    )

    def has_delete_permission(self, request, obj=None):
        return False  # 禁止删除

    def has_add_permission(self, request):
        return False  # 禁止添加


@admin.register(TaskResult)
class TaskResultAdmin(ModelAdmin):
    list_display = ("task_id", "task_name", "status", "date_done")
    list_filter = ("status", "task_name", "date_done")


admin.site.empty_value_display = "（空）"
