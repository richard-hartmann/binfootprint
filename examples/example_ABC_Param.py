import sys
import pathlib

# Add parent directory to beginning of path variable
# NOT NECESSARY IF THE PACKAGE WAS INSTALLED
sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent))

import binfootprint as bf


class Param(bf.ABCParameter):
    __slots__ = ["x", "y", "__non_key__"]

    def __init__(self, x, y, msg=""):
        super().__init__()
        self.x = x
        self.y = y
        self.__non_key__ = dict()
        self.__non_key__["msg"] = msg

    # __bfkey__ is implemented by ABS_Parameter


p = Param(3, 4.5)
bfp = bf.dump(p)
print("{}\n has hex hash value {}...".format(p, bf.hash_hex_from_bin_data(bfp)[:6]))

p = Param(3, 4.5, msg="I told you, don't use x=3!")
bfp = bf.dump(p)
print("{}\n has hex hash value {}...".format(p, bf.hash_hex_from_bin_data(bfp)[:6]))
