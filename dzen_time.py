#! /usr/bin/python2

import time



def update():
    now = time.localtime(time.time())
    nowf = time.strftime("%b %d %Y %H:%M", now)
    return nowf