from functools import wraps
from hashlib import md5

from django.core.cache import cache


def singleton_task(timeout, use_params=False):
    def task_decorator(task_func):
        @wraps(task_func)
        def wrapper(*args, **kwargs):
            if use_params:
                params_hash = md5((str(args) + str(kwargs)).encode()).hexdigest()
                lock_id = f"{task_func.__name__}-lock-{params_hash}"
            else:
                lock_id = f"{task_func.__name__}-lock"

            def acquire_lock():
                return cache.add(lock_id, "true", timeout)

            def release_lock():
                return cache.delete(lock_id)

            if acquire_lock():
                try:
                    return task_func(*args, **kwargs)
                finally:
                    release_lock()

        return wrapper

    return task_decorator
