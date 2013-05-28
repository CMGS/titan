#!/usr/local/bin/python2.7
#coding:utf-8

import string
import random
from config import TOKEN_LENGTH

LETTERS = string.letters + string.digits

def create_token(length=TOKEN_LENGTH):
    token = ''.join(random.sample(LETTERS, length))
    return token

