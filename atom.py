import sys
from xpybutil import util, ewmh

atom_cache = []

def add_atom(atom_str):
    global atom_cache
    module = sys.modules[__name__]
    atom  =  util.get_atom(atom_str)
    setattr(module, atom_str, atom)
    atom_cache.append(getattr(module, atom_str))
    
def build_atom_cache(atoms):
    global atom_cache
    for atom in atoms:
        add_atom(atom)

def update_atom_cache(atoms):
    global atom_cache
    module = sys.modules[__name__]
    for atom in atoms:
        try:
            getattr(module, atom)
        except AttributeError:
            add_atom(atom)
        
