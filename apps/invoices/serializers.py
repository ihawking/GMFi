from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import Serializer

from chains.models import Network
from chains.serializers import NetworkSerializer
from invoices.models import Invoice, Payment
from tokens.models import Token


class InvoiceCreateSerializer(Serializer):
    appid = serializers.CharField()
    timestamp = serializers.IntegerField()
    out_no = serializers.CharField(required=True)
    subject = serializers.CharField(max_length=64)
    detail = serializers.JSONField(default=dict)
    token = serializers.CharField(required=True)
    network = serializers.CharField(required=True)
    value = serializers.DecimalField(required=True, max_digits=32, decimal_places=8)
    duration = serializers.IntegerField(default=60)

    def validate_token(self, value):
        if not Token.objects.filter(symbol=value).exists():
            raise serializers.ValidationError(_("代币未创建."))
        return value

    def validate_network(self, value):
        if not Network.objects.filter(name=value).exists():
            raise serializers.ValidationError(_("网络不存在."))
        return value

    @staticmethod
    def _is_network_token_supported(attrs) -> bool:
        network = Network.objects.get(name=attrs["network"])
        token = Token.objects.get(symbol=attrs["token"])

        return token.support_this_network(network)

    def validate(self, attrs):
        if not self._is_network_token_supported(attrs):
            raise serializers.ValidationError(_("网络与代币不匹配."))

        if attrs["duration"] < 10 or attrs["duration"] > 2 * 60:
            raise serializers.ValidationError(_("支付时间需要介于10分钟-2小时."))

        if Invoice.objects.filter(out_no=attrs["out_no"], proj__appid=attrs["appid"]).exists():
            raise serializers.ValidationError(_("商户订单号重复."))

        return attrs


class InvoiceSerializer(serializers.ModelSerializer):
    network = NetworkSerializer(read_only=True)
    pay_url = serializers.SerializerMethodField(default="")

    def get_pay_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.no)

    class Meta:
        model = Invoice
        fields = (
            "no",
            "out_no",
            "subject",
            "detail",
            "network",
            "token_symbol",
            "token_address",
            "pay_address",
            "pay_url",
            "redirect_url",
        )


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("tx_hash", "value_display", "confirm_process")
