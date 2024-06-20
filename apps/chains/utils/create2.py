import eth_abi
from eth_typing.evm import HexAddress
from web3 import Web3
from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware
from web3.types import HexStr, TxParams, Wei
from web3.utils.address import get_create2_address


class InvalidChainIDException(Exception):
    def __init__(self, message):
        self.message = message


chain_ids = (97, 11155111)
factory_address = HexAddress(HexStr("0x9Dd64C6cC93dDb9719d43815fE8017174f29475d"))


def is_poa(w3: Web3) -> bool:
    try:
        w3.eth.get_block("latest")
        return False

    except ExtraDataLengthError:
        return True


def is_chain_valid(chain_id: int) -> bool:
    return chain_id in chain_ids


def predict_address(salt: HexStr, init_code: HexStr) -> HexStr:
    return get_create2_address(factory_address, salt, init_code)


def get_transaction_data(
        salt: HexStr,
        init_code: HexStr,
):
    encoded_params = eth_abi.encode(
        ["bytes", "uint256"],
        [
            bytes.fromhex(init_code),
            int.from_bytes(bytes.fromhex(salt), byteorder="big"),
        ],
    )

    data = "0x9c4ae2d0" + encoded_params.hex()
    return data


def create2(
        salt: HexStr,
        init_code: HexStr,
        private_key: HexStr,
        w3: Web3,
        gas=1280_000,
):
    if is_poa(w3):
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not is_chain_valid(w3.eth.chain_id):
        raise InvalidChainIDException("This chain is not support.")

    account = w3.eth.account.from_key(private_key)

    transaction: TxParams = {
        "chainId": w3.eth.chain_id,
        "nonce": w3.eth.get_transaction_count(account.address),
        "from": account.address,
        "to": factory_address,
        "value": Wei(0),
        "gas": gas,
        "gasPrice": w3.eth.gas_price,
        "data": get_transaction_data(salt, init_code),
    }

    signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)

    return tx_hash
