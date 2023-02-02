# python imports
from collections import namedtuple
from functools import partial

# third party imports
import numpy as np

# package imports
import binfootprint
from binfootprint import binfootprint as bfp
from tests import some_module


def test_version_tag():
    """
    test consistency in version
    """
    ob = 5
    b = bfp.dump(ob)
    assert b[0] == bfp.get_version()


def test_atom():
    """
    test list of atomic types
    """
    atoms = [
        12345678,
        3.141,
        "hallo Welt",
        "öäüß",
        True,
        False,
        None,
        2**65,
        -(3**65),
        b"\xff\fe\03",
        bytes(range(256)),
    ]

    for atom in atoms:
        bin_atom = bfp.dump(atom)
        atom_prime = bfp.load(bin_atom)
        bin_ob_prime = bfp.dump(atom_prime)
        assert bin_atom == bin_ob_prime
        hash(bin_atom)


def test_tuple():
    t = (
        12345678,
        3.141,
        "hallo Welt",
        "öäüß",
        True,
        False,
        None,
        (3, tuple(), (4, 5, None), "test"),
    )
    bin_tuple = bfp.dump(t)
    assert type(bin_tuple) is bytes
    t_prime = bfp.load(bin_tuple)
    assert t == t_prime
    bin_ob_prime = bfp.dump(t_prime)
    assert bin_tuple == bin_ob_prime


def test_nparray():
    ob = np.random.randn(3, 53, 2)
    bin_ob = bfp.dump(ob)
    assert type(bin_ob) is bytes
    ob_prime = bfp.load(bin_ob)
    assert np.all(ob == ob_prime)
    bin_ob_prime = bfp.dump(ob_prime)
    assert bin_ob == bin_ob_prime

    ob = np.random.randn(3, 53, 2)
    ob = (ob, ob, 4, None)
    bin_ob = bfp.dump(ob)
    ob_prime = bfp.load(bin_ob)
    assert np.all(ob[0] == ob_prime[0])
    assert np.all(ob[1] == ob_prime[1])
    bin_ob_prime = bfp.dump(ob_prime)
    assert bin_ob == bin_ob_prime


def test_list():
    ob = [1, 2, 3]
    bin_ob = bfp.dump(ob)
    assert type(bin_ob) is bytes
    ob_prime = bfp.load(bin_ob)
    assert np.all(ob == ob_prime)
    bin_ob_prime = bfp.dump(ob_prime)
    assert bin_ob == bin_ob_prime

    ob = [1, (2, 3), np.array([2j, 3j])]
    bin_ob = bfp.dump(ob)
    ob_prime = bfp.load(bin_ob)
    bin_ob_prime = bfp.dump(ob_prime)
    assert bin_ob == bin_ob_prime

    assert np.all(ob[0] == ob_prime[0])
    assert np.all(ob[1] == ob_prime[1])
    assert np.all(ob[2] == ob_prime[2])


class T(object):
    def __init__(self, a):
        self.a = a

    def __getstate__(self):
        return [self.a]

    def __setstate__(self, state):
        self.a = state[0]


def test_getstate():

    ob = T(4)
    bin_ob = bfp.dump(ob)
    assert type(bin_ob) is bytes

    ob_prime = bfp.load(bin_ob)

    assert np.all(ob.a == ob_prime.a)
    bin_ob_prime = bfp.dump(ob_prime)
    assert bin_ob == bin_ob_prime


def test_named_tuple():
    obj_type = namedtuple("obj_type", ["a", "b", "c"])

    obj = obj_type(12345678, 3.141, "hallo Welt")

    bin_obj = bfp.dump(obj)
    assert type(bin_obj) is bytes
    obj_prime = bfp.load(bin_obj)
    assert obj_prime.__class__.__name__ == obj.__class__.__name__
    assert obj_prime._fields == obj._fields
    assert obj_prime == obj
    bin_ob_prime = bfp.dump(obj_prime)
    assert bin_obj == bin_ob_prime


def test_complex():
    z = 3 + 4j
    bf = bfp.dump(z)
    assert type(bf) is bytes
    zr = bfp.load(bf)
    assert zr == z


def test_dict():
    a = {"a": 1, 5: 5, 3 + 4j: "l", False: b"ab4+#"}
    bf = bfp.dump(a)
    assert type(bf) is bytes
    a_restored = bfp.load(bf)
    for k in a:
        assert a[k] == a_restored[k]


def test_unsupported_type():
    obj = bytearray([4, 5, 6])
    try:
        bfp.dump(obj)
    except TypeError:
        pass
    else:
        assert False, "TypeError should have been raised!"


def generic_function(a, b, c):
    return a * b * c, "generic_function"


class CallableClass:
    var = None

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
        super().__init__()

    def __call__(self, a, b, c):
        return a * b * c, "CallableClass.__call__"

    def bound_function(self, a, b, c):
        return a * b * c, "CallableClass.bounded_function"

    @staticmethod
    def static_class_member(a, b, c):
        return a * b * c, "CallableClass.static_class_member"


def test_functools_partial():
    # what can we make partial
    cc = CallableClass(a=1, b=2, c=3)
    f_list = [
        (partial(generic_function, 2, c=3), True),
        (partial(CallableClass, 2, c=3), False),
        (partial(cc, 2, c=3), False),
        (partial(CallableClass.static_class_member, 2, c=3), True),
        (partial(cc.bound_function, 2, c=3), False),
        (partial(some_module.generic_function_in_some_module, 2, c=3), True),
    ]
    for partial_of_f, can_be_bf_dumped in f_list:
        # see if this yields a valid call for the partial
        partial_of_f(4)
        try:
            bin_data = binfootprint.dump(partial_of_f)
        except TypeError:
            bf_dump_success = False
        else:
            bf_dump_success = True

        assert bf_dump_success == can_be_bf_dumped
        if bf_dump_success:
            rec_data = binfootprint.load(bin_data)
            assert rec_data[0] == partial_of_f.func.__module__
            assert rec_data[1] == partial_of_f.func.__qualname__
            kwargs = rec_data[2]
            assert kwargs["a"] == 2
            assert kwargs["c"] == 3


if __name__ == "__main__":
    test_functools_partial()
