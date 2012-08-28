#! /usr/bin/python2

import dzen_time
from xpybutil import ewmh

while 1:
    
    desktop = ewmh.get_current_desktop().reply()
    desktops = ewmh.get_number_of_desktops().reply()
    active = "^fg(#fffff)^bg(#0088cc)"
    desktopsf = " ^fg(#0088cc)^bg(white)"
    
    if desktop is not None:
        desktop += 1
        for desk in range(desktops):
            if desk == desktop:
                active += str(desktop)
            else:
                desktopsf += str(desk+1)
    
    time = dzen_time.update()
    print desktopsf+" ^fg(#0088cc)^bg(white)^p(+1400)"  + time 