from eth_account.messages import encode_typed_data
from web3.auto import w3
import json

from django.conf import settings


def chain_icon_url(chain_id):
    slugs_path = settings.BASE_DIR / "apps" / "chains" / "data" / "slugs.json"

    with open(slugs_path, "r", encoding="utf-8") as file:
        slugs_data = json.load(file)

    slug = slugs_data[str(chain_id)] if str(chain_id) in slugs_data else None

    return f"https://icons.llamao.fi/icons/chains/rsz_{slug}.jpg" if slug else None


def chain_metadata(chain_id):
    # 指定JSON文件的路径
    file_path = settings.BASE_DIR / "apps" / "chains" / "data" / "chains.json"

    # 打开并读取JSON文件
    with open(file_path, "r", encoding="utf-8") as file:
        chains = json.load(file)

    for chain in chains:
        if chain["chainId"] == chain_id:
            data = {
                "name": chain["name"],
                "symbol": chain["chain"],
                "currency": {
                    "name": chain["nativeCurrency"]["name"],
                    "symbol": chain["nativeCurrency"]["symbol"],
                    "decimals": chain["nativeCurrency"]["decimals"],
                },
            }
            return data


class TransactionTypedDataSignature:
    def __init__(
        self,
        signer_private_key: str,
        types: list[str],
        names: list[str],
        inputs: list[str | int],
        primary_type: str,
        domain: dict[str, str | int],
    ):
        self.signer_private_key = signer_private_key
        self.names = names
        self.types = types
        self.inputs = inputs
        self.primary_type = primary_type
        self.domain = domain
        self.signature: str = self.get_signature()

    @staticmethod
    def sign_typed_data(signer_private_key, typed_data: dict[str, str | dict]) -> str:
        encoded_data = encode_typed_data(typed_data)

        return w3.eth.account.sign_message(encoded_data, signer_private_key).signature.hex()

    def get_typed_data(self) -> dict[str, str | dict]:
        typed_message = {name: self.inputs[key] for key, name in enumerate(self.names)}

        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                self.primary_type: [{"name": self.names[i], "type": self.types[i]} for i in range(len(self.names))],
            },
            "primaryType": self.primary_type,
            "domain": self.domain,
            "message": typed_message,
        }
        return typed_data

    def get_signature(self) -> str:
        typed_data = self.get_typed_data()

        return self.sign_typed_data(self.signer_private_key, typed_data)


if __name__ == "__main__":
    pass
