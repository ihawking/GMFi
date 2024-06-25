import pytest

from chains.models import Network


@pytest.fixture
def network(db):
    network = Network.objects.create(
        name="tbsc",
        chain_id=97,
        endpoint_uri="https://data-seed-prebsc-1-s1.binance.org:8545/",
        is_poa=True,
        currency_symbol="TBNB",
    )
    return network


@pytest.fixture
def latest_transaction_hash(network):
    latest_block_number = network.get_block_number()
    latest_block = network.w3.eth.get_block(latest_block_number)

    return latest_block.transactions[-1].hex()


def test_is_transaction_packed(network):
    assert network.is_transaction_packed(tx_hash="0xd41400c05944d88a1be002bd625b03056ad273fa3d4d7fd90b1f25e8e2c77c6e")


def test_is_transaction_confirmed(network, latest_transaction_hash):
    assert network.is_transaction_confirmed(
        tx_hash="0xd41400c05944d88a1be002bd625b03056ad273fa3d4d7fd90b1f25e8e2c77c6e"
    )
    assert not network.is_transaction_confirmed(tx_hash=latest_transaction_hash)
