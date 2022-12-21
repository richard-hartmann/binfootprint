import sys
import pathlib

# Add parent directory to beginning of path variable
# NOT NECESSARY IF THE PACKAGE WAS INSTALLED
sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent))

import binfootprint as bf
import shelve


class Point:
    """a Point class"""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getstate__(self):
        return [self.x, self.y]

    def __setstate__(self, state):
        self.x = state[0]
        self.y = state[1]


@bf.ShelveCacheDec()
def area(p):
    """some area"""
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
