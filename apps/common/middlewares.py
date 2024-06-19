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
        try:
            proj = Project.objects.get(appid=request.META.get("HTTP_APPID"))
        except Project.DoesNotExist:
            return JsonResponse({"code": 1000, "msg": _("Appid 不存在")}, status=400)

        return proj


class CheckHeadersMiddleware(GMFiMiddleware):
    def __call__(self, request):
        if "/api/" in request.path and request.method == "POST":
            if "HTTP_APPID" not in request.META:
                return JsonResponse({"code": 1004, "msg": _("Headers 缺失AppID")}, status=400)
            if "HTTP_TIMESTAMP" not in request.META:
                return JsonResponse({"code": 1005, "msg": _("Headers 缺失Timestamp")}, status=400)
            if "HTTP_SIGNATURE" not in request.META:
                return JsonResponse({"code": 1006, "msg": _("Headers 缺失Signature")}, status=400)

            post_data = request.POST.copy()
            post_data["appid"] = request.META.get("HTTP_APPID", "")
            request.POST = post_data

        response = self.get_response(request)
        return response


class IPWhiteListMiddleware(GMFiMiddleware):
    def __call__(self, request):
        if "/api/" in request.path and request.method == "POST":
            proj = self.get_proj(request)

            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

            if x_forwarded_for:
                client_ip = x_forwarded_for.split(",")[0]  # real client's ip
            else:
                client_ip = request.META.get("REMOTE_ADDR")

            if not is_ip_in_whitelist(whitelist=proj.ip_white_list, ip=client_ip):
                return JsonResponse({"code": 1001, "msg": _("IP 禁止")}, status=403)

        response = self.get_response(request)
        return response


class HMACMiddleware(GMFiMiddleware):
    def __call__(self, request):
        if "/api/" in request.path and request.method == "POST":
            proj = self.get_proj(request)

            if (
                not validate_hmac(
                    message_dict=request.POST, key=proj.hmac_key, received_hmac=request.META.get("HTTP_SIGNATURE")
                )
                and False
            ):
                return JsonResponse({"code": 1002, "msg": _("签名验证失败")}, status=403)

            if time.time() > int(request.META.get("HTTP_TIMESTAMP")) / 1000 + 300:
                return JsonResponse({"code": 1003, "msg": _("时间戳超时")}, status=403)

        response = self.get_response(request)
        return response
