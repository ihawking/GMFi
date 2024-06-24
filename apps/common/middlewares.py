import time

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from common.utils.crypto import validate_hmac
from common.utils.security import is_ip_in_whitelist
from globals.models import Project


class GMFiMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def get_proj(request):
        return Project.objects.get(pk=1)


class CheckHeadersMiddleware(GMFiMiddleware):
    def __call__(self, request):
        if "/api/" in request.path and request.method == "POST":
            if "HTTP_TIMESTAMP" not in request.META:
                return JsonResponse({"code": 40005, "msg": _("Headers 缺失Timestamp")}, status=400)
            if "HTTP_SIGNATURE" not in request.META:
                return JsonResponse({"code": 40006, "msg": _("Headers 缺失Signature")}, status=400)

            post_data = request.POST.copy()
            request.POST = post_data

        response = self.get_response(request)
        return response


class IPWhiteListMiddleware(GMFiMiddleware):
    def __call__(self, request):
        if "/api/" in request.path and request.method == "POST":
            project = self.get_proj(request)

            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

            if x_forwarded_for:
                client_ip = x_forwarded_for.split(",")[0]  # real client's ip
            else:
                client_ip = request.META.get("REMOTE_ADDR")

            if not is_ip_in_whitelist(whitelist=project.ip_white_list, ip=client_ip):
                return JsonResponse({"code": 40001, "msg": _("IP 禁止")}, status=403)

        response = self.get_response(request)
        return response


class HMACMiddleware(GMFiMiddleware):
    def __call__(self, request):
        if "/api/" in request.path and request.method == "POST":
            project = self.get_proj(request)

            if (
                not validate_hmac(
                    message_dict=request.POST, key=project.hmac_key, received_hmac=request.META.get("HTTP_SIGNATURE")
                )
                and False
            ):
                return JsonResponse({"code": 40002, "msg": _("签名验证失败")}, status=403)

            if time.time() > int(request.META.get("HTTP_TIMESTAMP")) / 1000 + 300:
                return JsonResponse({"code": 40003, "msg": _("时间戳超时")}, status=403)

        response = self.get_response(request)
        return response
