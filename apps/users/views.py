from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import Player
from common import http_codes
from tokens.models import TokenAddress

# Create your views here.


class DepositAddress(APIView):
    def get(self, request):
        uid = request.GET.get("uid", None)
        chain = request.GET.get("chain", None)
        symbol = request.GET.get("symbol", None)

        if not uid:
            return Response(status=400, data={"error": "UID is required", "code": http_codes.HTTP_400001_INVALID_UID})

        if not TokenAddress.objects.filter(chain__chain_id=chain, token__symbol=symbol, active=True).exists():
            return Response(
                status=400,
                data={
                    "error": f"{symbol} of chain-{chain} is not valid",
                    "code": http_codes.HTTP_400002_INVALID_CHAIN_TOKEN,
                },
            )

        player, _ = Player.objects.get_or_create(uid=uid)

        return Response({"deposit_address": player.deposit_account.address})
