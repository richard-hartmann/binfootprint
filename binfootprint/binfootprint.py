# python imports
from collections import namedtuple
import io
from math import ceil
import struct
import sys

# third party imports
import numpy as np
from numpy.lib import format as np_format


##########################################
#   define constants
##########################################

_spec_types = (bool, type(None))

_SPEC = 0x00  # True, False, None
_INT = 0x01
_FLOAT = 0x02
_COMPLEX = 0x03
_STR = 0x04
_BYTES = 0x05  # only for python3, as bytes and str are equivalent in python2
# _INT = 0x06
_TUPLE = 0x07
_NAMEDTUPLE = 0x08
_NPARRAY = 0x09
_LIST = 0x0A
_GETSTATE = 0x0B  # only used when __bfkey__ is not present
_DICT = 0x0C
# _INT_NEG = 0x0D
_BFKEY = 0x0E  # a special BF-Key member __bfkey__ is used if implemented, uses __getstate__ as fallback
# _SP_CSC_MAT = 0x0F  # scipy csc sparse matrix

# _VERS = 0x90        # use pickle to binfootprint numpy arrays / this breaks backwards compatibility
_VERS = 0x91  # unify ints / this breaks backwards compatibility

__max_int32 = +2147483647
__min_int32 = -2147483648


def get_version():
    """return the current version used for dump"""
    return _VERS


class BFLoadError(Exception):
    pass


def _dump_spec(ob):
    """serialize special object 'ob' (True, False, None)"""
    if ob is True:
        b = bytes([_SPEC, ord("T")])
    elif ob is False:
        b = bytes([_SPEC, ord("F")])
    elif ob is None:
        b = bytes([_SPEC, ord("N")])
    else:
        raise RuntimeError("object is not of 'special' kind!")
    return b


def _load_spec(b):
    """convert bytes 'b' to special object (True, False, None)"""
    assert b[0] == _SPEC
    if b[1] == ord("T"):
        return True, 2
    elif b[1] == ord("F"):
        return False, 2
    elif b[1] == ord("N"):
        return None, 2
    else:
        raise BFLoadError("internal error (unknown code for 'special' {})".format(b[1]))


def _dump_int(ob):
    """serialize an integer"""
    ob_bytes = ob.to_bytes(ceil((ob.bit_length() + 1) / 8), "big", signed=True)
    num_bytes = len(ob_bytes)

    b = bytes([_INT])
    b += struct.pack(">I", num_bytes)
    b += ob_bytes
    return b


def _load_int(b):
    """converts bytes 'b' to integer"""
    assert b[0] == _INT
    num_bytes = struct.unpack(">I", b[1:5])[0]
    b_ = b[5 : 5 + num_bytes]
    i = int.from_bytes(b_, byteorder="big", signed=True)
    return i, 5 + num_bytes


def _dump_float(ob):
    """serialize 32bit float (double)"""
    b = bytes([_FLOAT])
    b += struct.pack(">d", ob)
    return b


def _load_float(b):
    """convert bytes 'b' to 32bit float (double)"""
    assert b[0] == _FLOAT
    f = struct.unpack(">d", b[1:9])[0]
    return f, 9


def _dump_complex(ob):
    """serialize 32bit complex (2x double)"""
    b = bytes([_COMPLEX])
    b += struct.pack(">d", ob.real)
    b += struct.pack(">d", ob.imag)
    return b


def _load_complex(b):
    """convert bytes 'b' to 32bit complex"""
    assert b[0] == _COMPLEX
    re = struct.unpack(">d", b[1:9])[0]
    im = struct.unpack(">d", b[9:17])[0]
    return re + 1j * im, 13


def _dump_str(ob):
    """serialize a string"""
    b = bytes([_STR])
    str_bytes = bytes(ob, "utf8")
    num_bytes = len(str_bytes)
    b += struct.pack(">I", num_bytes)
    b += str_bytes
    return b


def _load_str(b):
    """convert bytes 'b' to string"""
    assert b[0] == _STR
    num_bytes = struct.unpack(">I", b[1:5])[0]
    s = str(b[5 : 5 + num_bytes], "utf8")
    return s, 5 + num_bytes


def _dump_bytes(ob):
    """serialize a byte array"""
    b = bytes([_BYTES])
    num_bytes = len(ob)
    b += struct.pack(">I", num_bytes)
    b += ob
    return b


def _load_bytes(b):
    """convert bytes 'b' to a byte array"""
    assert b[0] == _BYTES
    num_bytes = struct.unpack(">I", b[1:5])[0]
    b_ = b[5 : 5 + num_bytes]
    return b_, 5 + num_bytes


def _dump_tuple(t):
    """serialize a tuple"""
    b = bytes([_TUPLE])
    size = len(t)
    b += struct.pack(">I", size)
    for ti in t:
        b += _dump(ti)
    return b


def _load_tuple(b):
    """convert bytes 'b' to tuple"""
    assert b[0] == _TUPLE
    size = struct.unpack(">I", b[1:5])[0]
    idx = 5
    t = []
    for i in range(size):
        ob, len_ob = _load(b[idx:])
        t.append(ob)
        idx += len_ob
    return tuple(t), idx


def _dump_namedtuple(t):
    """serialize a namedtuple"""
    b = bytes([_NAMEDTUPLE])
    size = len(t)
    b += struct.pack(">I", size)
    b += _dump(t.__class__.__name__)
    for i in range(size):
        b += _dump(t._fields[i])
        b += _dump(t[i])
    return b


def _load_namedtuple(b):
    """convert bytes 'b' to namedtuple"""
    assert b[0] == _NAMEDTUPLE
    size = struct.unpack(">I", b[1:5])[0]
    class_name, len_ob = _load_str(b[5:])
    idx = 5 + len_ob
    t = []
    fields = []
    for i in range(size):
        ob, len_ob = _load(b[idx:])
        fields.append(ob)
        idx += len_ob

        ob, len_ob = _load(b[idx:])
        t.append(ob)
        idx += len_ob

    np_class = namedtuple(class_name, fields)
    np_obj = np_class(*t)

    return np_obj, idx


def _dump_list(t):
    """serialize a list"""
    b = bytes([_LIST])
    size = len(t)
    b += struct.pack(">I", size)
    for ti in t:
        b += _dump(ti)
    return b


def _load_list(b):
    """convert bytes 'b' to list"""
    assert b[0] == _LIST
    size = struct.unpack(">I", b[1:5])[0]
    idx = 5
    t = []
    for i in range(size):
        ob, len_ob = _load(b[idx:])
        t.append(ob)
        idx += len_ob
    return t, idx


def _dump_np_array(np_array):
    """
    Serialize a numpy array - relays on numpy's 'format.write_array()' which implements the '.npy' file format.
    Here we use version 1.0.

    In the doc it says:

        The ``.npy`` format is the standard binary file format in NumPy for
        persisting a *single* arbitrary NumPy array on disk. The format stores all
        of the shape and dtype information necessary to reconstruct the array
        correctly even on another machine with a different architecture.
        The format is designed to be as simple as possible while achieving
        its limited goals.

    so it should be suited for our purpose.
    """
    b = bytes([_NPARRAY])
    nparray_bytes_io = io.BytesIO()
    np_format.write_array(nparray_bytes_io, np_array, version=(1, 0))
    nparray_bytes = nparray_bytes_io.getvalue()
    size = len(nparray_bytes)
    b += struct.pack(">I", size)
    b += nparray_bytes
    return b


def _load_np_array(b):
    """convert bytes 'b' to numpy array"""
    assert b[0] == _NPARRAY
    size = struct.unpack(">I", b[1:5])[0]
    nparray_bytesIO = io.BytesIO(b[5 : size + 5])
    npa = np_format.read_array(nparray_bytesIO)
    return npa, size + 5


def _dump_bf_key(ob):
    """
    serialize an object based on the '__bfkey__' member

    This is similar to the __getstate__ member used to pickle python objects.
    So in order to work, the returned object of __bfkey__() needs to be compatible
    with the binaryfootprint serialization.
    To uniquely identify objects, their class name and the name of the module which defines
    the class is serialized as well.

    New in version 0.3: add name of the module to serialization
    """
    b = bytes([_BFKEY])
    bf_key = ob.__bfkey__()
    cls_name = ob.__class__.__name__
    cls_module = ob.__class__.__module__
    b += _dump(str(cls_name))
    b += _dump(str(cls_module))
    b += _dump(bf_key)
    return b


def _load_bf_key(b):
    """convert bytes 'b' to (class_name, class_module, bf_key)"""
    assert b[0] == _BFKEY
    cls_name, l_cls_name = _load_str(b[1:])
    cls_module, l_cls_module = _load_str(b[l_cls_name + 1 :])
    bf_key, l_state = _load(b[l_cls_name + l_cls_module + 1 :])
    return (cls_name, cls_module, bf_key), l_cls_name + l_cls_module + l_state + 1


def _dump_getstate(ob):
    """
    serialize an object based on the '__getstate__' member used by pickle

    To uniquely identify objects, their class name and the name of the module which defines
    the class is serialized as well.

    New in version 0.3: add name of the module to serialization
    """
    b = bytes([_GETSTATE])
    state = ob.__getstate__()
    cls_name = ob.__class__.__name__
    cls_module = ob.__class__.__module__
    b += _dump(str(cls_name))
    b += _dump(str(cls_module))
    b += _dump(state)
    return b


def _load_getstate(b):
    """
    convert bytes 'b' to an object

    Use __new__ constructor and __setstate__ to initialize the class, which is then returned.
    Note that the module which defined the class needs to be loaded in order to
    construct the object from binary data (similar to pickle.load()).
    """
    assert b[0] == _GETSTATE
    cls_name, l_cls_name = _load_str(b[1:])
    cls_module, l_cls_module = _load_str(b[l_cls_name + 1 :])
    state, l_state = _load(b[l_cls_name + l_cls_module + 1 :])
    m = sys.modules[cls_module]
    cls = getattr(m, cls_name)
    obj = cls.__new__(cls)
    obj.__setstate__(state)
    return obj, l_cls_name + l_cls_module + l_state + 1


def _dump_dict(ob):
    """
    serialize a dictionary

    Sorting the tuple containing the binary key and the binary value yields a unique
    representation for the whole dictionary.
    """
    b = bytes([_DICT])
    keys = ob.keys()
    bin_keys = []
    for k in keys:
        try:
            bin_keys.append((_dump(k), _dump(ob[k])))
        except:
            print("failed to dump key '{}'".format(k))
            raise
    b += _dump_list(sorted(bin_keys))
    return b


def _load_dict(b):
    """convert bytes 'b' to dictionary"""
    assert b[0] == _DICT
    sorted_keys_value, l = _load_list(b[1:])
    res_dict = {}
    for i in range(len(sorted_keys_value)):
        key = _load(sorted_keys_value[i][0])[0]
        value = _load(sorted_keys_value[i][1])[0]
        res_dict[key] = value

    return res_dict, l + 1


def _dump(ob):
    if isinstance(ob, _spec_types):
        return _dump_spec(ob)
    elif isinstance(ob, int):
        return _dump_int(ob)
    elif isinstance(ob, float):
        return _dump_float(ob)
    elif isinstance(ob, complex):
        return _dump_complex(ob)
    elif isinstance(ob, str):
        return _dump_str(ob)
    elif isinstance(ob, bytes):
        return _dump_bytes(ob)
    elif isinstance(ob, tuple):
        if hasattr(ob, "_fields"):
            return _dump_namedtuple(ob)
        else:
            return _dump_tuple(ob)
    elif isinstance(ob, list):
        return _dump_list(ob)
    elif isinstance(ob, np.ndarray):
        return _dump_np_array(ob)
    elif isinstance(ob, dict):
        return _dump_dict(ob)
    elif hasattr(ob, "__bfkey__"):
        return _dump_bf_key(ob)
    elif hasattr(ob, "__getstate__"):
        return _dump_getstate(ob)
    else:
        raise TypeError("unsupported type for dump '{}' ({})".format(type(ob), ob))


def _load(b):
    identifier = b[0]
    if isinstance(identifier, str):
        identifier = ord(identifier)
    if identifier == _SPEC:
        return _load_spec(b)
    elif identifier == _INT:
        return _load_int(b)
    elif identifier == _FLOAT:
        return _load_float(b)
    elif identifier == _COMPLEX:
        return _load_complex(b)
    elif identifier == _STR:
        return _load_str(b)
    elif identifier == _BYTES:
        return _load_bytes(b)
    elif identifier == _TUPLE:
        return _load_tuple(b)
    elif identifier == _NAMEDTUPLE:
        return _load_namedtuple(b)
    elif identifier == _LIST:
        return _load_list(b)
    elif identifier == _NPARRAY:
        return _load_np_array(b)
    elif identifier == _DICT:
        return _load_dict(b)
    elif identifier == _BFKEY:
        return _load_bf_key(b)
    elif identifier == _GETSTATE:
        return _load_getstate(b)
    else:
        raise BFLoadError(
            "internal error (unknown identifier '{}')".format(hex(identifier))
        )


def dump(ob):
    """
        returns the binary footprint of the object 'ob' as bytes
    """
    return bytes([_VERS]) + _dump(ob)


def load(b):
    """
        reconstruct the object from the binary footprint given as bytes 'b'
    """
    vers = b[0]
    if vers != _VERS:
        raise BFLoadError("wrong version (converter needed!)")

    return _load(b[1:])[0]
