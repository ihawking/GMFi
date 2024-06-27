from typing import NamedTuple

from web3.types import ChecksumAddress

from chains.models import Transaction
from tokens.models import TokenAddress, Token
from .contract import get_erc20_contract

erc20_contract = get_erc20_contract()


class TokenTransferTuple(NamedTuple):
    token: Token
    from_address: ChecksumAddress
    to_address: ChecksumAddress
    value: int


class TransactionParser:
    def __init__(self, transaction: Transaction) -> None:
        self.chain = transaction.block.chain
        self.metadata = transaction.metadata

    @property
    def token_transfer(self) -> TokenTransferTuple:
        if self.metadata["input"].startswith("0xa9059cbb"):
            return self._erc20_transfer()
        elif self.metadata["value"]:
            return self._currency_transfer()
        else:
            raise RuntimeError("Invalid token transfer format")

    def _currency_transfer(self) -> TokenTransferTuple:
        return TokenTransferTuple(
            self.chain.currency, self.metadata["from"], self.metadata["to"], self.metadata["value"]
        )

    def _erc20_transfer(self) -> TokenTransferTuple:
        receipt = self.chain.w3.eth.get_transaction_receipt(self.metadata["hash"])
        transfer_event = erc20_contract.events.Transfer().process_receipt(receipt)[0]

        chain_token = TokenAddress.objects.get(chain=self.chain, address=transfer_event["address"])

        return TokenTransferTuple(
            chain_token.token,
            transfer_event["args"]["from"],
            transfer_event["args"]["to"],
            transfer_event["args"]["value"],
        )
