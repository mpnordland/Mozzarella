import mozzarella
import sys
import traceback

'''
This is the main .py file for mozzerella, a mouse friendly, tiling window manager
written entirely in python using the python Xlib bindings. You shouldn't need to mess with anything here.
All the tinkering should be done in the mozzarella.Frame and mozzarella.Tiler classes.
'''


def main():
    

    try:
        
        #create a Manager object to handle all the X connection, setup and events for us
           
        wm = mozzarella.Manager() 
    #There is certainly no point in continuing if there isn't an unmanaged screen for us
    except mozzarella.NoUnmanagedScreens:
            print >> sys.stderr, 'No unmanaged screens found'
            return 2
    try:
    #start the eventloop, this will give us the events we need to do our managing
        wm.main_loop()
    #If we get a keyboard interupt, end nicely    
    except KeyboardInterrupt:
        print "We got Ctrl-C, exiting"
        return 0
    #Not entirely sure what this does, I borrowed it from simplewm.py by Joshua D. Bartlett
    except SystemExit:
        print "system exit"
        raise
    except:
        traceback.print_exc()
        return 1
        
#if somehow somebody accidentally imports this, we wouldn't want to
#mess up their system, would we?
if __name__ == '__main__':
    main()
    print "we're done here, no problems"
    
