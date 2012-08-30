#! /usr/bin/python2

import time



def update():
    time.sleep(1)
    now = time.localtime(time.time())
    nowf = time.strftime("%b %d %Y %H:%M:%S", now)
    return nowf