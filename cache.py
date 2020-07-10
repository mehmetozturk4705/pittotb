import time
"""
Custom key cache implementation by Mehmet Öztürk
"""
class Cache:
    __caches = {}
    def __init__(self, cache_key=None, timeout = None):
        if not callable(cache_key):
            raise ValueError("cache_key should be a callable")
        if type(timeout)!=int:
            raise ValueError("timeout should not be integer type")
        self.__cache_key = cache_key
        self.__timeout = timeout
    @classmethod
    def collect(cls):
        will_delete = []
        for k in cls.__caches:
            if cls.__caches[k]["timeout"]<time.time():
                will_delete.append(k)

        for k in will_delete:
            del cls.__caches[k]

    def __call__(self, f):

        def func(*args, **kwargs):
            Cache.collect()
            cur_key = self.__cache_key(*args, **kwargs)
            if type(cur_key) != str:
                raise ValueError("cache_key should return string")
            try:
                res = self.__caches[cur_key]
                return res["result"]
            except KeyError:
                result = f(*args, **kwargs)
                self.__caches[cur_key] = {"result": result, "timeout": (time.time()+self.__timeout)}
                return result

        func.__name__ = f.__name__
        return func
