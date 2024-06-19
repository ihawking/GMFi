import time
from concurrent.futures import ThreadPoolExecutor, as_completed

if __name__ == "__main__":
    import os
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GMFi.settings")
    django.setup()


from chains.models import Block


def block_count():
    while 1:
        print(Block.objects.count())
        time.sleep(2)


with ThreadPoolExecutor(max_workers=30) as pool:
    futures = [pool.submit(block_count) for _ in range(30)]
    for future in as_completed(futures):
        future.result()  # 获取线程的结果或异常
