import asyncio
import json

if __name__ == "__main__":
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GMFi.settings")
    django.setup()


from chains.models import Network, Block
from chains.tasks import filter_and_store_tx
from web3.types import HexStr
from web3.datastructures import AttributeDict
from django.core.cache import cache
from django.conf import settings
import loguru

logger = loguru.logger
logger.bind(name="monitoring")
logger.add(settings.BASE_DIR / "GMFi.log", rotation="12:00")


async def get_block_data(network: Network, block_identifier: HexStr | int) -> AttributeDict:
    return await network.async_w3.eth.get_block(block_identifier, full_transactions=True)


async def get_block_data_list(network: Network, block_identifiers: list[HexStr | int]) -> list[AttributeDict]:
    """
    通过协程，异步获取批量区块数据
    :param network:
    :param block_identifiers:
    :return:
    """
    get_block_data_tasks = [get_block_data(network, block_identifier) for block_identifier in block_identifiers]
    block_datas = await asyncio.gather(*get_block_data_tasks)
    # noinspection PyTypeChecker
    return block_datas


async def get_parent_block(network: Network, parent_hash: HexStr) -> Block | None:
    """
    只有缺失数量不多的情况下，才会进入此追溯父块的函数，因为此函数会发生递归调用，需控制深度；
    根据父区块的哈希值获取数据库对应的 Block，若不存在，则创建父区块；
    :param network: 区块网络
    :param parent_hash: 父块哈希值
    :return: 父 Block；如果是新系统干净无区块，则返回 None
    """
    try:
        return await Block.objects.aget(hash=parent_hash)

    except Block.DoesNotExist:
        if await network.block_set.aexists():
            parent_data = await get_block_data(network, parent_hash)
            return await store_block_with_txs(network, parent_data)
        else:
            return None


async def store_block_with_txs(network: Network, block_data: AttributeDict) -> Block:
    """
    将本区块，和它的交易入库；
    :param block_data:
    :param network:
    :return: Block
    """
    await Block.objects.filter(network=network, number__gte=block_data["number"]).adelete()  # 删除同网络中所有比本区块号大的区块
    parent_block = await get_parent_block(network, block_data["parentHash"].hex())

    block_obj: Block = await Block.objects.acreate(
        hash=block_data["hash"].hex(),
        parent=parent_block,
        number=block_data["number"],
        network=network,
        timestamp=block_data["timestamp"],
    )

    for tx in block_data["transactions"]:
        tx_metadata = json.loads(network.w3.to_json(tx))
        filter_and_store_tx.delay(block_obj.id, tx_metadata)

    print(f"{block_data['number']}  {block_data['hash'].hex()} ok")

    return block_obj


async def monitor_the_network(network: Network):
    """
    监控区块链网络；
    当数据库中的 Network 数据发生变化时，结束本次监控任务；
    监控过程中，需要判断数据库的最新区块，是否大幅落后于区块链，如果是的话，需要运行区块补齐逻辑，否则将当前最新区块入库；
    :param network:
    :return: None
    """
    while True:
        try:
            block_filter = await network.async_w3.eth.filter("latest")

            while True:
                if cache.get("networks_changed", False):
                    return

                new_block_hashes = await block_filter.get_new_entries()
                new_block_data_list = await get_block_data_list(network, new_block_hashes)

                need_aligned, align_from_numer, align_to_numer = await network.need_aligned(new_block_data_list)

                if need_aligned:
                    new_block_data_list = await get_block_data_list(
                        network, list(range(align_from_numer, align_to_numer))
                    )

                for new_block_data in new_block_data_list:  # 此处需要保证必须按照从小到大的顺序插入区块
                    await store_block_with_txs(network, new_block_data)

        except:
            await asyncio.sleep(1)


async def main():
    """
    主函数，持续运行；
    任务组的任务全部 return，说明数据库网络被修改，需要重新载入 Network 参数进行监控；
    :return:
    """
    while True:
        try:
            cache.set("networks_changed", False)
            async with asyncio.TaskGroup() as task_group:
                async for network in Network.objects.all():
                    task_group.create_task(monitor_the_network(network))
        except:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
