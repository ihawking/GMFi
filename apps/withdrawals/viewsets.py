from django.db import transaction as db_tx
from django.http.response import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response

from chains.models import Chain
from globals.models import Project
from tokens.models import Token
from users.models import Player
from withdrawals.models import Withdrawal
from withdrawals.serializers import CreateWithdrawalSerializer


class WithdrawalViewSet(viewsets.ModelViewSet):
    queryset = Withdrawal.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = CreateWithdrawalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated_data = serializer.validated_data

        player, _ = Player.objects.get_or_create(uid=validated_data["uid"])
        chain = Chain.objects.get(chain_id=validated_data["chain"])
        token = Token.objects.get(symbol=validated_data["symbol"])

        value = validated_data["value"]

        account = chain.project.distribution_account
        account.get_lock()

        with db_tx.atomic():
            transaction_queue = account.send_token(
                chain=chain, token=token, to=validated_data["to"], value=int(value * 10**token.decimals)
            )
            Withdrawal.objects.create(
                no=validated_data["no"],
                to=validated_data["to"],
                player=player,
                value=value,
                token=token,
                transaction_queue=transaction_queue,
            )
        account.release_lock()

        return HttpResponse("ok")
