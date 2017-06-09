import redis


db = redis.strictRedis()
db.delete()