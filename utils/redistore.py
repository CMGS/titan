#!/usr/local/bin/python2.7
#coding:utf-8

import redis
import common

rdb = redis.Redis(connection_pool=common.redis_pool)

