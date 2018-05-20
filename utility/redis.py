import aioredis

redis_pool = None
redis_pool1 = None


def initialize_redis_pool(loop):
    global redis_pool
    global redis_pool1
    redis_pool = loop.run_until_complete(aioredis.create_redis_pool(('localhost', 6379), loop=loop))
    redis_pool1 = loop.run_until_complete(aioredis.create_redis_pool(('localhost', 6379), db=1, loop=loop))
