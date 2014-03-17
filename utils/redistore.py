#!/usr/local/bin/python2.7
#coding:utf-8

import redis
import config

pool = redis.ConnectionPool(
        host=config.REDIS_HOST, port=config.REDIS_PORT, \
        db=config.REDIS_DB, password=config.REDIS_PASSWORD, \
        max_connections=config.REDIS_POOL_SIZE)

rdb = redis.Redis(connection_pool=pool)

