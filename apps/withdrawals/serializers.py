from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import Serializer
from web3.auto import w3 as auto_w3

from chains.models import Network, Account
from chains.utils.contract import get_erc20_contract
from tokens.models import Token, TokenAddress
from users.models import Player
from withdrawals.models import Withdrawal
from globals.models import Project


class CreateWithdrawalSerializer(Serializer):
    no = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    to = serializers.CharField(required=True)
    symbol = serializers.CharField(required=True)
    network = serializers.CharField(required=True)
    value = serializers.DecimalField(required=True, max_digits=32, decimal_places=8)

    def validate_no(self, value):
        if Withdrawal.objects.filter(no=value).exists():
            raise serializers.ValidationError(_("编号不可用."))
        return value

    def validate_to(self, value):
        if not auto_w3.is_checksum_address(value):
            raise serializers.ValidationError(_("请输入合法的校验和地址."))
        if Account.objects.filter(address=value).exists():
            raise serializers.ValidationError(_("无法提现到平台内地址."))
        return value

    def validate_symbol(self, value):
        if not Token.objects.filter(symbol=value).exists():
            raise serializers.ValidationError(_("代币未创建."))
        return value

    def validate_network(self, value):
        if not Network.objects.filter(name=value).exists():
            raise serializers.ValidationError(_(f"网络 {value} 未创建."))
        return value

    @staticmethod
    def _is_network_token_supported(attrs) -> bool:
        network = Network.objects.get(name=attrs["network"])
        token = Token.objects.get(symbol=attrs["symbol"])

        return token.support_this_network(network)

    @staticmethod
    def _is_contract_address(attrs) -> bool:
        network = Network.objects.get(name=attrs["network"])

        if network.is_contract(attrs["to"]):
            return True

        return False

    @staticmethod
    def _is_balance_enough(attrs) -> bool:
        project = Project.objects.get(pk=1)
        player, _ = Player.objects.get_or_create(uid=attrs["uid"])

        network = Network.objects.get(name=attrs["network"])
        token = Token.objects.get(symbol=attrs["symbol"])

        value_on_chain = attrs["value"] * 10**token.decimals

        if network.currency == token:
            return network.get_balance(address=project.distribution_address) >= value_on_chain
        else:
            network_token = TokenAddress.objects.get(network=network, token=token)
            erc20_contract = get_erc20_contract(address=network_token.address, w3=network.w3)
            return erc20_contract.functions.balanceOf(project.distribution_address).call() >= value_on_chain

    def validate(self, attrs):
        if not self._is_network_token_supported(attrs):
            raise serializers.ValidationError(_("网络与代币不匹配."))

        if not self._is_balance_enough(attrs):
            raise serializers.ValidationError(_("系统账户中的此代币余额不足."))

        if self._is_contract_address(attrs):
            raise serializers.ValidationError(_("收币地址不可以为合约地址."))

        return attrs
