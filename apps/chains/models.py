import json
import time
import eth_abi
from typing import cast

from django.core.cache import cache
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from django.db import transaction as db_transaction
from django.db.models import F, Sum, Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from web3 import AsyncWeb3
from web3 import Web3
from web3.auto import w3 as auto_w3
from web3.datastructures import AttributeDict
from web3.exceptions import ExtraDataLengthError
from web3.exceptions import TransactionNotFound
from web3.middleware import geth_poa_middleware, async_geth_poa_middleware
from web3.types import ChecksumAddress, HexStr, TxParams

from common.fields import ChecksumAddressField, HexStr64Field
from common.utils.crypto import aes_cipher
from chains.utils import chain_metadata, chain_icon_url
from globals.models import Project
from invoices.models import Invoice, Payment
from notifications.models import Notification
from tokens.models import Token, TokenAddress, AccountTokenBalance, TokenTransfer, TokenType


# Create your models here.
class Chain(models.Model):
    chain_id = models.PositiveIntegerField(_("Chain ID"), blank=True, primary_key=True)
    name = models.CharField(_("名称"), max_length=32, unique=True, blank=True)
    currency = models.ForeignKey(
        "tokens.Token",
        verbose_name="原生代币",
        on_delete=models.PROTECT,
        blank=True,
        related_name="chains_as_currency",
    )
    is_poa = models.BooleanField(_("是否为 POA 网络"), blank=True, editable=False)
    endpoint_uri = models.CharField(
        _("HTTP RPC 节点地址"), help_text="只需填写 RPC 地址，会自动识别公链信息", max_length=256, unique=True
    )

    block_confirmations_count = models.PositiveSmallIntegerField(
        verbose_name=_("区块确认数量"),
        default=18,
        blank=True,
        help_text="交易的确认数越多，则该交易在区块链中埋的越深，就越不容易被篡改；<br/>"
        "高于此确认数，系统将认定此交易被区块链最终接受；<br/>"
        "数值参考：<br>ETH: 12; BSC: 15; Others: 16；",
    )
    active = models.BooleanField(
        default=True, verbose_name=_("启用"), help_text="关闭将会停止接受此链出块信息，且停止与其相关的接口调用"
    )

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    def __str__(self):
        return f"{self.name}"

    @property
    def icon(self):
        return chain_icon_url(self.chain_id)

    @property
    def gas_price(self) -> int:
        return self.w3.eth.gas_price

    def is_contract(self, address: ChecksumAddress):
        return self.w3.eth.get_code(address).hex() != "0x"

    def get_balance(self, address: ChecksumAddress) -> int:
        return self.w3.eth.get_balance(address)

    def get_transaction_receipt(self, tx_hash: HexStr) -> dict:
        return json.loads(Web3.to_json(self.w3.eth.get_transaction_receipt(tx_hash)))

    def get_transaction(self, tx_hash: HexStr) -> dict:
        return json.loads(Web3.to_json(self.w3.eth.get_transaction(tx_hash)))

    def get_block(self, block_number: int) -> dict:
        return json.loads(Web3.to_json(self.w3.eth.get_block(block_number)))

    def get_block_number(self) -> int:
        return self.w3.eth.get_block_number()

    def is_block_number_confirmed(self, block_number):
        return block_number + self.block_confirmations_count < self.get_block_number()

    def is_transaction_should_be_processed(self, tx: dict) -> bool:
        if (
            tx["input"].startswith("0xa9059cbb") and TokenAddress.objects.filter(chain=self, address=tx["to"]).exists()
        ):  # 平台所支持的 ERC20 代币的转账 (transfer)
            return True

        if Invoice.objects.filter(
            pay_address=tx["to"], platform_tx__transaction__isnull=True
        ).exists():  # 转入 ETH 到平台内的账单地址，且账单合约未失效
            return True

        if Account.objects.filter(address=tx["from"]).exists():  # 平台内部账户发起的交易
            return True

        if Account.objects.filter(address=tx["to"]).exists():  # 转入 ETH 到平台内部账户
            return True

        return False

    def is_transaction_packed(self, tx_hash: HexStr) -> bool:
        try:
            self.get_transaction_receipt(tx_hash)
        except TransactionNotFound:
            return False
        else:
            return True

    def is_transaction_success(self, tx_hash: HexStr) -> bool:
        receipt = self.get_transaction_receipt(tx_hash)

        return receipt["status"] == 1

    def is_transaction_fail(self, tx_hash: HexStr) -> bool:
        return not self.is_transaction_success(tx_hash)

    def is_transaction_confirmed(self, tx_hash: HexStr) -> bool:
        receipt = self.get_transaction_receipt(tx_hash)
        return self.is_block_number_confirmed(receipt["blockNumber"])

    def is_block_confirmed(self, block_number: int, block_hash: HexStr) -> bool:
        return self.get_block(block_number)["hash"] == block_hash

    @property
    def w3(self):
        w3 = Web3(Web3.HTTPProvider(self.endpoint_uri))
        if self.is_poa:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        return w3

    @property
    def async_w3(self):
        aw3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(self.endpoint_uri))
        if self.is_poa:
            aw3.middleware_onion.inject(async_geth_poa_middleware, layer=0)

        return aw3

    @property
    def get_is_poa(self) -> bool:
        try:
            self.w3.eth.get_block("latest")
            return False

        except ExtraDataLengthError:
            return True

    @property
    def max_block_number(self) -> int:
        max_block = Block.objects.filter(chain=self).order_by("-number").first()
        return max_block.number

    @property
    async def amax_block_number(self) -> int | None:
        max_block = await Block.objects.filter(chain=self).order_by("-number").afirst()
        return max_block.number if max_block else None

    @property
    def project(self):
        return Project.objects.get(pk=1)

    async def need_aligned(self, block_datas: list[AttributeDict]) -> tuple[bool, int, int]:
        no_need = (False, 0, 0)

        if not block_datas:
            return no_need

        current_number = block_datas[0]["number"]
        max_block_number = await self.amax_block_number

        if max_block_number:
            if current_number > max_block_number + 21:
                return True, max_block_number + 1, max_block_number + 22
            else:
                return no_need
        return no_need

    class Meta:
        ordering = ("chain_id",)
        verbose_name = _("公链")
        verbose_name_plural = _("公链")


@receiver(post_save, sender=Chain)
def chains_changed(*args, **kwargs):
    cache.set("chains_changed", True)


@receiver(pre_save, sender=Chain)
def chain_fill_up(sender, instance: Chain, **kwargs):
    if not Chain.objects.filter(pk=instance.pk).exists():
        instance.is_poa = instance.get_is_poa
        instance.chain_id = instance.w3.eth.chain_id

        metadata = chain_metadata(instance.chain_id)
        if not metadata:
            raise ValidationError("不支持此网络.")

        instance.name = metadata["name"]

        try:
            token = Token.objects.get(symbol=metadata["currency"]["symbol"])
            if token.decimals != metadata["currency"]["decimals"] or token.type != TokenType.Native:
                raise ValidationError("此网络的原生代币与系统中已存在的代币冲突.")
        except Token.DoesNotExist:
            token = Token.objects.create(
                symbol=metadata["currency"]["symbol"],
                decimals=metadata["currency"]["decimals"],
                type=TokenType.Native,
            )
        instance.currency = token

        TokenAddress.objects.create(
            token=instance.currency, chain=instance, address="0x0000000000000000000000000000000000000000"
        )


class Block(models.Model):
    hash = HexStr64Field()
    parent = models.OneToOneField("chains.Block", on_delete=models.CASCADE, blank=True, null=True)
    chain = models.ForeignKey("chains.Chain", on_delete=models.PROTECT)
    number = models.PositiveIntegerField(db_index=True)
    timestamp = models.PositiveIntegerField()

    confirmed = models.BooleanField(default=False)

    @property
    def next_number(self):
        return self.number + 1

    @property
    def confirm_process(self):
        return min(((self.chain.max_block_number - self.number) / self.chain.block_confirmations_count), 1)

    def confirm(self) -> bool:
        if self.confirmed:
            return True

        if self.chain.is_block_confirmed(block_number=self.number, block_hash=self.hash):
            self.confirmed = True
            self.save()
            return True
        else:
            self.delete()
            return False

    def __str__(self):
        return f"{self.chain.name}-{self.number}"

    class Meta:
        ordering = (
            "chain",
            "-number",
        )
        unique_together = (
            "chain",
            "number",
        )
        verbose_name = _("区块")
        verbose_name_plural = _("区块")


@receiver(post_save, sender=Block)
def block_created(sender, instance, created, **kwargs):
    if created:
        from chains.tasks import confirm_past_blocks

        confirm_past_blocks.delay(instance.pk)


class Transaction(models.Model):
    class Type(models.TextChoices):
        Paying = "paying", "Paying"
        Depositing = "depositing", "Depositing"
        Withdrawal = "withdrawal", "Withdrawal"

        Funding = "funding", "Funding"
        GasRecharging = "gas_recharging", "GasRecharging"
        DepositGathering = "d_gathering", "DepositGathering"
        InvoiceGathering = "i_gathering", "InvoiceGathering"

    block = models.ForeignKey("chains.Block", on_delete=models.CASCADE, related_name="transactions")
    hash = HexStr64Field()
    transaction_index = models.PositiveSmallIntegerField()
    metadata = models.JSONField()
    receipt = models.JSONField()

    type = models.CharField(_("类型"), max_length=16, choices=Type.choices, blank=True, null=True)

    @db_transaction.atomic
    def initialize(self):
        self.link_platform_tx()

        if self.success:
            self.set_token_transfer()
            self.set_type()
            if self.type is None:
                self.delete()

            self.parse()

            if self.block.chain.project.pre_notify:
                self.notify(as_pre=True)

    @db_transaction.atomic
    def confirm(self):
        try:
            self.set_token_transfer()
        except:
            pass
        if self.success:
            self.notify()
            self.update_account_balance()

    def link_platform_tx(self):
        try:
            platform_tx = PlatformTransaction.objects.get(
                chain=self.block.chain, account=self.metadata["from"], nonce=self.metadata["nonce"]
            )
            platform_tx.transaction = self
            platform_tx.save()

        except PlatformTransaction.DoesNotExist:
            pass

    def get_token_transfer_tuple(self):
        from chains.utils.transactions import TransactionParser

        tx_parser = TransactionParser(self)  # 交易解析器
        return tx_parser.token_transfer

    def set_token_transfer(self):
        if hasattr(self, "platform_tx") and hasattr(
            self.platform_tx, "invoice"
        ):  # 部署账单合约，是特殊情况，因为无法通过解析交易得到内部转账信息
            invoice = self.platform_tx.invoice
            TokenTransfer.objects.create(
                transaction=self,
                token=invoice.token,
                from_address=invoice.pay_address,
                to_address=invoice.collection_address,
                value=Payment.objects.filter(invoice=invoice).aggregate(total=Sum("value"))["total"],
            )
        else:
            token_transfer_tuple = self.get_token_transfer_tuple()
            TokenTransfer.objects.create(
                transaction=self,
                token=token_transfer_tuple.token,
                from_address=token_transfer_tuple.from_address,
                to_address=token_transfer_tuple.to_address,
                value=token_transfer_tuple.value,
            )

    def set_type(self):
        token_transfer = self.token_transfer

        if hasattr(self, "platform_tx") and hasattr(
            self.platform_tx, "invoice"
        ):  # 部署账单合约是特殊情况，因为无法通过解析得到内部转账信息
            _type = Transaction.Type.InvoiceGathering

        elif Project.objects.filter(
            distribution_account__address=token_transfer.from_address
        ).exists():  # 项目的代币分发地址往外转币的话只有两种可能 1、Gas 分发 2、提币
            if Account.objects.filter(address=token_transfer.to_address).exists():
                _type = Transaction.Type.GasRecharging
                Account.objects.get(address=token_transfer.to_address).clear_tx_callable_failed_times()
            else:
                _type = Transaction.Type.Withdrawal

        elif Account.objects.filter(
            address=token_transfer.to_address, player__isnull=False
        ).exists():  # 排除 gas 充值的情况下，向平台内部绑定了用户的账户转币，代表充值
            _type = Transaction.Type.Depositing

        elif Account.objects.filter(
            address=token_transfer.from_address, player__isnull=False
        ).exists():  # 绑定用户的平台内部地址向外转账，代表归集充值的代币
            _type = Transaction.Type.DepositGathering

        elif Project.objects.filter(
            distribution_account__address=token_transfer.to_address
        ).exists():  # 系统账户接收代币，代表注入资金到系统账户
            _type = Transaction.Type.Funding
            Account.objects.get(address=token_transfer.to_address).clear_tx_callable_failed_times()

        elif Invoice.objects.filter(
            pay_address=token_transfer.to_address,
            token=token_transfer.token,
            chain=self.block.chain,
            platform_tx__transaction__isnull=True,  # 账单如果已经归集了，那任何支付都是无效的
        ).exists():  # 如果接收代币的是账单地址，代表支付账单的行为
            _type = Transaction.Type.Paying

        else:
            return

        self.type = _type
        self.save()

    def parse(self):
        token_transfer = self.token_transfer

        if self.type == Transaction.Type.Depositing:
            try:
                from deposits.models import Deposit

                Deposit.parse_transaction(self)
            except AttributeError:
                pass

        elif self.type == Transaction.Type.Paying:
            try:
                invoice = Invoice.objects.get(
                    pay_address=token_transfer.to_address,
                    token=token_transfer.token,
                    chain=self.block.chain,
                    platform_tx__isnull=True,
                )
                Payment.objects.create(transaction=self, invoice=invoice, value=token_transfer.value)
            except Invoice.DoesNotExist:
                pass

    def update_account_balance(self):
        with db_transaction.atomic():
            token_transfer = self.token_transfer

            try:
                account_as_tx_from = Account.objects.get(address=self.metadata["from"])
                account_as_tx_from.alter_balance(
                    chain=self.block.chain,
                    token=self.block.chain.currency,
                    value=-(self.metadata["gasPrice"] * self.receipt["gasUsed"]),
                )  # 扣 Gas
            except Account.DoesNotExist:
                pass

            try:
                account_as_from = Account.objects.get(address=token_transfer.from_address)
                account_as_from.alter_balance(
                    chain=self.block.chain, token=token_transfer.token, value=-token_transfer.value
                )
            except Account.DoesNotExist:
                pass

            try:
                account_as_to = Account.objects.get(address=token_transfer.to_address)
                account_as_to.alter_balance(
                    chain=self.block.chain, token=token_transfer.token, value=token_transfer.value
                )
            except Account.DoesNotExist:
                pass

    @property
    def raw_receipt(self):
        return None

    @property
    def confirm_process(self):
        return self.block.confirm_process

    @property
    def success(self):
        return self.receipt["status"] == 1

    @property
    def withdrawal(self):
        return self.platform_tx.withdrawal

    @property
    def tx_data(self) -> dict:
        return {
            "chain": self.block.chain.name,
            "chain_id": self.block.chain.chain_id,
            "block": self.block.number,
            "hash": self.hash,
            "timestamp": self.block.timestamp,
            "confirmed": self.block.confirmed,
        }

    def notify(self, as_pre=False):
        content = {"transaction": self.tx_data}

        if as_pre and content["transaction"]["confirmed"]:  # 如果是预通知，那就只会通知未确认的区块交易
            return

        if self.type == Transaction.Type.Paying:
            if self.payment.invoice.paid:  # 本次支付账单支付进度完成，才会进行通知
                content.update(self.payment.invoice.notification_content)
            else:
                return
        elif self.type == Transaction.Type.Depositing:
            content.update(self.deposit.notification_content)
        elif self.type == Transaction.Type.Withdrawal:
            content.update(self.withdrawal.notification_content)
        else:
            return

        Notification.objects.create(transaction=self, content=content)

    def __str__(self):
        return self.hash

    class Meta:
        ordering = ("block", "transaction_index")
        verbose_name = _("交易")
        verbose_name_plural = _("交易")


@receiver(post_save, sender=Transaction)
def transaction_created(sender, instance: Transaction, created, **kwargs):
    if created:
        instance.initialize()


class Account(models.Model):
    address = ChecksumAddressField(_("地址"), unique=True, db_index=True)
    encrypted_private_key = models.TextField()

    tx_callable_failed_times = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    def __str__(self):
        return f"{self.address}-{self.type}"

    @property
    def type(self):
        if hasattr(self, "player"):
            return _("充币账户")
        else:
            return _("系统账户")

    def alter_balance(self, chain, token, value: int):
        try:
            balance = AccountTokenBalance.objects.select_for_update().get(account=self, chain=chain, token=token)
        except AccountTokenBalance.DoesNotExist:
            balance, _ = AccountTokenBalance.objects.get_or_create(account=self, chain=chain, token=token)
            balance = AccountTokenBalance.objects.select_for_update().get(pk=balance.pk)

        balance.value = F("value") + value
        balance.save()

    def get_lock(self):
        while True:
            if self.is_locked:
                time.sleep(0.05)
            else:
                return cache.set(f"lock_account_{self.address}", True, timeout=4)

    def release_lock(self):
        cache.delete(f"lock_account_{self.address}")

    @property
    def is_locked(self):
        return cache.get(f"lock_account_{self.address}")

    @classmethod
    def generate(cls):
        acc = auto_w3.eth.account.create()

        return cls.objects.create(address=acc.address, encrypted_private_key=aes_cipher.encrypt(acc.key.hex()))

    @property
    def private_key(self):
        return aes_cipher.decrypt(self.encrypted_private_key)

    def balance(self, chain: Chain) -> int:
        return chain.get_balance(self.address)

    def nonce(self, chain: Chain) -> int:
        return PlatformTransaction.objects.filter(chain=chain, account=self).count()

    def send_eth(self, chain: Chain, to: ChecksumAddress, value: int):
        return PlatformTransaction.objects.create(
            account=self, chain=chain, to=to, value=value, nonce=self.nonce(chain)
        )

    @staticmethod
    def get_erc20_transfer_data(to: ChecksumAddress, value: int) -> HexStr:
        encoded_params = eth_abi.encode(
            ["address", "uint256"],
            [
                to,
                value,
            ],
        )

        return "0xa9059cbb" + encoded_params.hex()  # type: ignore

    def send_token(self, chain: Chain, token: Token, to: ChecksumAddress, value: int):
        if chain.currency == token:
            return self.send_eth(chain, to, value)

        token_address = TokenAddress.objects.get(chain=chain, token=token).address

        return PlatformTransaction.objects.create(
            account=self,
            chain=chain,
            to=token_address,
            nonce=self.nonce(chain),
            data=self.get_erc20_transfer_data(to, value),
        )

    def delete(self, *args, **kwargs):
        raise ValidationError(_("为保护数据完整性，禁止删除."))

    # 如果你想确保批量删除也被阻止，可以覆盖 delete 方法
    @classmethod
    def delete_queryset(cls, queryset):
        raise ValidationError(_("为保护数据完整性，禁止删除."))

    def clear_tx_callable_failed_times(self):
        self.tx_callable_failed_times = 0
        self.save()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("本地账户")
        verbose_name_plural = _("本地账户")


class PlatformTransaction(models.Model):
    chain = models.ForeignKey("chains.Chain", on_delete=models.DO_NOTHING, verbose_name=_("网络"))

    account = models.ForeignKey("chains.Account", on_delete=models.PROTECT, verbose_name=_("账户"))
    nonce = models.PositiveIntegerField(_("Nonce"))
    to = ChecksumAddressField(_("To"))
    value = models.DecimalField(_("Value"), max_digits=36, decimal_places=0, default=0)
    data = models.TextField(_("Data"), blank=True, null=True)
    gas = models.PositiveIntegerField(_("Gas"), default=160000)

    transaction = models.OneToOneField(
        "chains.Transaction", on_delete=models.SET_NULL, verbose_name=_("交易"), null=True, related_name="platform_tx"
    )

    transacted_at = models.DateTimeField(_("交易提交时间"), blank=True, null=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    def __str__(self):
        if self.transaction:
            return self.transaction.hash
        else:
            return f"{self.chain.name}-{self.account.address}-{self.nonce}"

    def generate_transaction_dict(self) -> dict:
        transaction = {
            "chainId": self.chain.chain_id,
            "nonce": self.nonce,
            "from": self.account.address,
            "to": self.to,
            "value": int(self.value),
            "data": self.data if self.data else b"",
            "gas": self.gas,
            "gasPrice": self.chain.gas_price * 1,
        }

        return transaction

    def is_transaction_callable(self, transaction: dict) -> bool:
        """
        预判本次交易是否会执行成功
        :param transaction:
        :return:
        """
        try:
            self.chain.w3.eth.call(cast(TxParams, transaction))
        except ValueError:
            return False
        else:
            return True

    @db_transaction.atomic
    def check_tx(self):
        if PlatformTransaction.objects.filter(
            chain=self.chain, account=self.account, nonce__gt=self.nonce, transaction__isnull=False
        ).exists():
            # 如果存在比当前nonce更大的交易完成，说明本次交易已经提交成功，只不过没有入库，所以仅需根据hash查询交易入库就行了
            try:
                self.transaction = Transaction.objects.get(
                    block__chain=self.chain, metadata__from=self.account.address, metadata__nonce=self.nonce
                )
                self.save()
            except Transaction.DoesNotExist:
                self.transact()
        else:
            self.transact()

    @db_transaction.atomic
    def transact(self):
        """
        执行本次交易
        :return:
        """
        transaction_dict = self.generate_transaction_dict()

        if self.is_transaction_callable(transaction_dict):
            self.transacted_at = timezone.now()
            self.save()

            signed_transaction = self.chain.w3.eth.account.sign_transaction(transaction_dict, self.account.private_key)
            self.chain.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        else:
            self.account.tx_callable_failed_times += 1
            self.account.save()

    def delete(self, *args, **kwargs):
        raise ValidationError(_("为保护数据完整性，禁止删除."))

    # 如果你想确保批量删除也被阻止，可以覆盖 delete 方法
    @classmethod
    def delete_queryset(cls, queryset):
        raise ValidationError(_("为保护数据完整性，禁止删除."))

    class Meta:
        unique_together = (
            "account",
            "chain",
            "nonce",
        )

        ordering = ("created_at",)

        verbose_name = _("发送交易")
        verbose_name_plural = _("发送交易")
