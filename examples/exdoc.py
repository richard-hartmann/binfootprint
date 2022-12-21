import sys
import pathlib
import hashlib

# Add parent directory to beginning of path variable
sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent))

import shelve
import numpy as np
import binfootprint as bf


##############
# Example  1 #
##############
bf.dump(["hallo", 42])


##############
# Example  2 #
##############
SIGMA_Z = 0x34
data = {
    "Færøerne": {"area": (1399, "km^2"), "population": 54000},
    SIGMA_Z: [[-1, 0], [0, 1]],
    "usefulness": None,
}
b = bf.dump(data)
print("sha256 check sum:", hashlib.sha256(b).hexdigest())


##############
# Example  3 #
##############
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getstate__(self):
        return [self.x, self.y]

    def __setstate__(self, state):
        self.x = state[0]
        self.y = state[1]


ob = Point(4, -2)
b = bf.dump(ob)

ob_prime = bf.load(b)
print("type:", type(ob_prime))
print("member x:", ob_prime.x)
print("member y:", ob_prime.y)

##############
# Example  4 #
##############
class Point2(Point):
    def __bfkey__(self):
        return {"x": self.x, "y": self.y}


ob = Point2(5, 3)
b = bf.dump(ob)

ob_prime = bf.load(b)
print("load on bfkey:", ob_prime)

##############
# Example  5 #
##############
a1 = np.asarray([0, 1, 1, 0])
b1 = bf.dump(a1)

a2 = a1.reshape(2, 2)
b2 = bf.dump(a2)

a3 = np.asarray(a1, dtype=np.complex128)
b3 = bf.dump(a3)

print("            sha256 of int array :", hashlib.sha256(b1).hexdigest())
print("sha256 of int array shape (2,2) :", hashlib.sha256(b2).hexdigest())
print("        sha256 of complex array :", hashlib.sha256(b3).hexdigest())


##############
# Example  6 #
##############
@bf.ShelveCacheDec()
def area(p):
    print(" * f(p(x={},y={})) called".format(p.x, p.y))
    return p.x * p.y


with shelve.open(area.f_name) as db:
    db.clear()

p = Point(10, 10)
print("first call results in")
print(area(p))
print("second call results in")
print(area(p))

p = Point(10, 11)
print("f(p(10, 11)) is in cache?")
print(area(p, _cache_flag="has_key"))


##############
# Example  7 #
##############
class Param(bf.ABCParameter):
    __slots__ = ["x", "y", "__non_key__"]

    def __init__(self, x, y, msg=""):
        super().__init__()
        self.x = x
        self.y = y
        self.__non_key__ = dict()
        self.__non_key__["msg"] = msg


p = Param(3, 4.5)
bfp = bf.dump(p)
print("{}\n has hex hash value {}...".format(p, bf.hash_hex_from_bin_data(bfp)[:6]))

p = Param(3, 4.5, msg="I told you, don't use x=3!")
bfp = bf.dump(p)
print("{}\n has hex hash value {}...".format(p, bf.hash_hex_from_bin_data(bfp)[:6]))
