import os
from datetime import timedelta

import eth_abi
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from web3.types import HexStr

from chains.models import Network
from chains.utils import create2
from common.utils.crypto import generate_random_code
from globals.models import Project
from invoices.bytecodes import ETHInvoice, ERC20Invoice
from invoices.models import Invoice
from invoices.serializers import InvoiceCreateSerializer, InvoiceSerializer
from tokens.models import Token


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    @staticmethod
    def get_init_code(network: Network, token: Token, proj: Project):
        if network.currency == token:
            constructor_arguments = [proj.collection_address]
            encoded_arguments = eth_abi.encode(["address"], constructor_arguments)
            init_code = ETHInvoice + encoded_arguments.hex()
        else:
            constructor_arguments = [token.address(network), proj.collection_address]
            encoded_arguments = eth_abi.encode(["address", "address"], constructor_arguments)
            init_code = ERC20Invoice + encoded_arguments.hex()

        return init_code

    def create(self, request, *args, **kwargs):
        serializer = InvoiceCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated_data = serializer.validated_data

        token = Token.objects.get(symbol=validated_data["token"])
        network = Network.objects.get(name=validated_data["network"])
        proj = Project.objects.first()

        with db_transaction.atomic():
            salt = os.urandom(32).hex()
            init_code = self.get_init_code(network, token, proj)

            pay_address = create2.predict_address(HexStr(salt), init_code)

            invoice = Invoice.objects.create(
                proj=proj,
                no=f"G{generate_random_code(length=31)}",
                out_no=validated_data["out_no"],
                subject=validated_data["subject"],
                detail=validated_data["detail"],
                token=token,
                network=network,
                value=validated_data["value"],
                expired_time=timezone.now() + timedelta(minutes=validated_data["duration"]),
                salt=salt,
                init_code=init_code,
                pay_address=pay_address,
                collection_address=proj.collection_address,
            )

            serializer_context = {
                "request": request,
            }
            return Response(InvoiceSerializer(invoice, context=serializer_context).data, status=status.HTTP_200_OK)
