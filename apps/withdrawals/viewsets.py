from django.db import transaction as db_tx
from django.http.response import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response

from chains.models import Network
from globals.models import Project
from tokens.models import Token
from users.models import User
from withdrawals.models import Withdrawal
from withdrawals.serializers import CreateWithdrawalSerializer


class WithdrawalViewSet(viewsets.ModelViewSet):
    queryset = Withdrawal.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = CreateWithdrawalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated_data = serializer.validated_data

        user, _ = User.objects.get_or_create(username=validated_data["username"])
        network = Network.objects.get(name=validated_data["network"])
        token = Token.objects.get(symbol=validated_data["symbol"])

        value = validated_data["value"]

        account = Project.distribution_account
        account.get_lock()
        with db_tx.atomic():
            platform_tx = account.send_token(
                network=network, token=token, to=validated_data["to"], value=value * 10 ** token.decimals
            )
            Withdrawal.objects.create(
                no=validated_data["no"], user=user, value=value, token=token, platform_tx=platform_tx
            )
        account.release_lock()

        return HttpResponse("ok")
