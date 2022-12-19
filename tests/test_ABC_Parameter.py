import sys
import pathlib

# Add parent directory to beginning of path variable
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


def test_abc_parameter():

    # check if msg (__non_key__) is ignored
    p1 = Param(3, 4.5)
    hash_hex1 = bf.hash_hex_from_object(p1)
    p2 = Param(3, 4.5, msg="told you!")
    hash_hex2 = bf.hash_hex_from_object(p2)
    assert hash_hex1 == hash_hex2

    # check if y=None is skipped in the binary footprint
    import binfootprint.binfootprint as bf_internal

    p = Param(x=3, y=None)
    bf_key = bf.dump(p)
    r = bf.load(bf_key)
    module = r[1]

    fake_bf_key = bytes([bf_internal._VERS])
    fake_bf_key += bytes([bf_internal._BFKEY])
    fake_bf_key += bf_internal._dump("Param")
    fake_bf_key += bf_internal._dump(module)
    fake_bf_key += bf_internal._dump([("x", 3)])

    assert fake_bf_key == bf_key


if __name__ == "__main__":
    test_abc_parameter()
