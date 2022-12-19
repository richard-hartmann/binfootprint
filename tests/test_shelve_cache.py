import shelve
import binfootprint as bfp


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


with shelve.open(fnc.f_name) as db:
    db.clear()


def test_shelve_cache():
    p = Point(4, -2)
    r = fnc(p)
    assert r[0] == -8
    assert r[1] == 2
    assert fnc(p, shelve_cache_flag="has_key") is True

    assert fnc(p, a=2, shelve_cache_flag="has_key") is False
    fnc(p, a=2, shelve_cache_flag="no_cache")
    assert fnc(p, a=2, shelve_cache_flag="has_key") is False
    fnc(p, a=2)
    assert fnc(p, a=2, shelve_cache_flag="has_key") is True

    with shelve.open(fnc.f_name) as db:
        key = fnc.param_hash(p, a=2)
        db[key] = None

    assert fnc(p, a=2) is None
    r = fnc(p, a=2, shelve_cache_flag="update")
    assert r is not None
    assert fnc(p, a=2, shelve_cache_flag="has_key") is True

    try:
        fnc(p, a=2, b=0, shelve_cache_flag="cache_only")
    except KeyError:
        pass
    else:
        assert False, "KeyError should have been raised"
