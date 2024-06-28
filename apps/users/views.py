from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Player
from common import http_codes

# Create your views here.


class DepositAddress(APIView):
    def get(self, request):
        uid = request.GET.get("uid", None)

        if not uid:
            return Response(status=400, data={"error": "UID is required", "code": http_codes.HTTP_400001_INVALID_UID})

        player, _ = Player.objects.get_or_create(uid=uid)

        return Response({"deposit_address": player.deposit_account.address})
