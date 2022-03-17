import binfootprint as bfp
from binfootprint import util

@bfp.ShelveCacheDec()
def test_fnc(a=1, b=2):
    return None


def test_shelfe_cache():
    r = test_fnc(a=1)
    assert r is None

    r = util.test_fnc(a=1, b=2)
    assert r == 3


if __name__ == '__main__':
    test_shelfe_cache()

