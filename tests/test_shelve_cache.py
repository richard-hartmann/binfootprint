import pytest

import binfootprint as bfp
from functools import partial
import math
import shelve


import binfootprint.util


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getstate__(self):
        return [self.x, self.y]

    def __setstate__(self, state):
        self.x = state[0]
        self.y = state[1]


@bfp.ShelveCacheDec()
def fnc(p, a=1, b=2):
    return (p.x * p.y) ** a, a * b


with shelve.open(str(fnc.f_name)) as db:
    db.clear()


def test_shelve_cache():
    p = Point(4, -2)
    r = fnc(p)
    assert r[0] == -8
    assert r[1] == 2
    assert fnc(p, _cache_flag="has_key") is True

    assert fnc(p, a=2, _cache_flag="has_key") is False
    fnc(p, a=2, _cache_flag="no_cache")
    assert fnc(p, a=2, _cache_flag="has_key") is False
    fnc(p, a=2)
    assert fnc(p, a=2, _cache_flag="has_key") is True

    with shelve.open(str(fnc.f_name)) as db:
        key = fnc.param_hash(p, a=2)
        db[key] = None

    assert fnc(p, a=2) is None
    r = fnc(p, a=2, _cache_flag="update")
    assert r is not None
    assert fnc(p, a=2, _cache_flag="has_key") is True

    try:
        fnc(p, a=2, b=0, _cache_flag="cache_only")
    except KeyError:
        pass
    else:
        assert False, "KeyError should have been raised"


def gaussian(x, a, sigma, x0):
    return a * math.exp(-((x - x0) ** 2) / 2 / sigma**2)


@binfootprint.util.ShelveCacheDec()
def quad(f, x_min, x_max, dx):
    r = 0
    x = x_min
    while x < x_max:
        r += f(x)
        x += dx
    return dx * r


def test_cache_integral():
    g = partial(gaussian, a=1, sigma=1, x0=-2.34)
    with shelve.open(str(quad.f_name)) as db:
        db.clear()
    with pytest.raises(KeyError):
        quad(g, x_min=-10, x_max=10, dx=0.001, _cache_flag="cache_only")

    r = quad(g, x_min=-10, x_max=10, dx=0.001)
    r2 = quad(g, x_min=-10, x_max=10, dx=0.001, _cache_flag="cache_only")
    assert r == r2

    g2 = partial(gaussian, sigma=1, x0=-2.34, a=1)
    r3 = quad(g2, -10, 10, 0.001, _cache_flag="cache_only")
    assert r == r3

    g = partial(gaussian, a=1, sigma=1.2, x0=-2.34)
    with pytest.raises(KeyError):
        quad(g, x_min=-10, x_max=10, dx=0.001, _cache_flag="cache_only")


if __name__ == "__main__":
    test_cache_integral()
