import eth_abi
from web3.types import HexStr, ChecksumAddress


def generate_data(to: ChecksumAddress, value: int) -> HexStr:
    encoded_params = eth_abi.encode(
        ["address", "uint256"],
        [
            to,
            value,
        ],
    )

    return "0xa9059cbb" + encoded_params.hex()
