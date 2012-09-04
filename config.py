from xpybutil import keybind
import sys, os, traceback
import logger

#this sets the mouse combination to move windows around
mouse_move_string = 'Mod4-3'

#set how many workspaces you want here, there is no theoretical limit
workspaces=4

#This can be logger.Logger to simply print
#statements, or logger.DzenLogger in order to have Mozzarella
#output dzen formated text
#logger = logger.DzenLogger()

def spawn(command):
    #global logger
    '''
    Forks a command and disowns it.
    '''
    #logger.log("spawn"+ command[0])
    if os.fork() != 0:
        return

    try:
        # Child.
        os.setsid()     # Become session leader.
        if os.fork() != 0:
            os._exit(0)

        os.chdir(os.path.expanduser('~'))
        os.umask(0)

        # Close all file descriptors.
        import resource
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if maxfd == resource.RLIM_INFINITY:
            maxfd = 1024
        for fd in xrange(maxfd):
            try:
                os.close(fd)
            except OSError:
                pass

        # Open /dev/null for stdin, stdout, stderr.
        os.open('/dev/null', os.O_RDWR)
        os.dup2(0, 1)
        os.dup2(0, 2)

        os.execve(command[0], command, os.environ)
    except:
        try:
            # Error in child process.
            print >> sys.stderr, 'Error in child process:'
            traceback.print_exc()
        except:
            pass
        sys.exit(1)

#you have to define a function to bind to a keypress. A more elegant,
#or easier way to bind apps to keys would be nice, but then again,
#functions are nice for doing more than just launching apps.
#add your new function to bind_launcher_keys like this:
#keybind.bind_global_key('KeyRelease', 'key combination', function)

def bind_launcher_keys():
    keybind.bind_global_key('KeyRelease', 'Mod4-e', scite)
    keybind.bind_global_key('KeyRelease', 'Mod4-f', spacefm)
    keybind.bind_global_key('KeyRelease', 'Mod4-w', chromium)
    keybind.bind_global_key('KeyRelease', 'Mod4-m', quodlibet)
    keybind.bind_global_key('KeyRelease', 'Mod4-b', blender)
    keybind.bind_global_key('KeyRelease', 'Mod4-Return', sakura)
    #keybind.bind_global_key('KeyRelease', 'Mod4-k', kill_window)
    keybind.bind_global_key('KeyRelease', 'Mod4-space', dmenu)

def scite():
    spawn(['/usr/bin/scite'])
def spacefm():
    spawn(['/usr/bin/spacefm'])
def sakura():
    spawn(['/usr/bin/sakura'])
def chromium():
    spawn(['/usr/bin/chromium'])
def quodlibet():
    spawn(['/usr/bin/quodlibet'])
def blender():
    spawn(['/usr/bin/blender'])
def kill_window():
    spawn(['/usr/bin/xkill'])
def dmenu():
    spawn(['/usr/bin/dmenu_run', "-nb", '#0088cc', "-nf", '#ffffff', "-fn", "DejaVu Sans:8"])
