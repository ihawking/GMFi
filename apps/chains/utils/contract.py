from web3.auto import w3 as auto_w3

from chains.utils.abis import ERC20ABI


def get_erc20_contract(address=None, w3=auto_w3):
    return w3.eth.contract(address=address, abi=ERC20ABI)
