"""
    This module intents to generate a binary representation of a python object
    where it is guaranteed that the same objects will result in the same binary
    representation.
    
    By far not all python objects are supported. Here is the list of supported types
        
        - special build-in constants: True, False, None
        - integer 
        - float (64bit)
        - complex (128bit)

    as well as

        - tuples
        - lists
        - dictionaries
        - namedtuple

    of the above.

    Also

        - np.ndarray

    are supported, however, as of changing details in the numpy implementation future
    version may of numpy may break backwards compatibility.

    In the current version (0.2.x) of binfootprint, a numpy array is serialized using
    the (npy file format)[https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html#module-numpy.lib.format].


    For any nested combination of these objects it is also guaranteed that the
    original objects can be restored without any extra information.
    
    Additionally
    
        - 'getstate' (objects that implement __getstate__ and return a state that can be dumped as well)
    
    can be dumped. To Restore these objects the load function needs a lookup given by the argument 'classes'
    which maps the objects class name (obj.__class__.__name__) to the actual class definition (the class object).
    Of course for these objects the __setstate__ method needs to be implemented. 

    Note: dumping older version is not supported anymore. If backwards compatibility is needed check out older
    code from git. If needed converters should/will be written.
"""

# python imports
from collections import namedtuple
import io
from math import ceil
import struct

# third party imports
import numpy as np
from numpy.lib import format as np_format

try:
    import scipy
    from scipy.sparse import isspmatrix_csc
except ImportError:
    scipy = None

##########################################
#   define constants
##########################################

_spec_types = (bool, type(None))

_SPEC = 0x00  # True, False, None
_INT_32 = 0x01
_FLOAT = 0x02
_COMPLEX = 0x03
_STR = 0x04
_BYTES = 0x05  # only for python3, as bytes and str are equivalent in python2
_INT = 0x06
_TUPLE = 0x07
_NAMEDTUPLE = 0x08
_NPARRAY = 0x09
_LIST = 0x0A
_GETSTATE = 0x0B  # only used when __bfkey__ is not present
_DICT = 0x0C
_INT_NEG = 0x0D
_BFKEY = 0x0E  # a special BF-Key member __bfkey__ is used if implemented, uses __getstate__ as fallback
_SP_CSC_MAT = 0x0F  # scipy csc sparse matrix

# _VERS = 0x80     # is broken with numpy 1.22, since the dump/load API has changed
_VERS = 0x90     # use pickle to binfootprint numpy arrays / this breaks backwards compatibility

__max_int32 = +2147483647
__min_int32 = -2147483648



def getVersion():
    return _VERS


def __int_to_bytes(i):
    m = 0xFF
    assert i >= 0
    ba = str()
    while i > 0:
        b = i & m
        ba += str(bytearray([b]))
        i = i >> 8
    return ba[::-1]


def __bytes_to_int(ba):
    i = 0
    for b in ba:
        i = i << 8
        i += ord(b)
    return i


def char_eq_byte(ch, b):
    return ord(ch) == b


def byte_eq_byte(b1, b2):
    return b1 == b2


BIN_TYPE = bytes
str_to_bytes = lambda s: bytes(s, "utf8")
bytes_to_str = lambda b: str(b, "utf8")
LONG_TYPE = int
init_BYTES = lambda b: bytes(b)
comp_id = byte_eq_byte
char_to_byte = lambda ch: ord(ch)
byte_to_ord = lambda b: b
int_to_bytes = lambda i: i.to_bytes(ceil(i.bit_length() / 8), "big")
bytes_to_int = lambda ba: int.from_bytes(ba, "big")

try:
    int_to_bytes(2 ** 77)
except AttributeError:
    int_to_bytes = __int_to_bytes

__b_tmp = int_to_bytes(2 ** 77)

try:
    bytes_to_int(__b_tmp)
except AttributeError:
    bytes_to_int = __bytes_to_int

assert bytes_to_int(__b_tmp) == 2 ** 77


class BFLoadError(Exception):
    pass


class BFUnkownClassError(Exception):
    def __init__(self, classname):
        Exception.__init__(
            self,
            "could not load object of type '{}', no class definition found in classes\n".format(
                classname
            )
            + "Please provide the lookup 'classes' when calling load, that maps the class name of the object to the actual "
            + "class definition (class object).",
        )


def _dump_spec(ob):
    if ob == True:
        b = init_BYTES([_SPEC, char_to_byte("T")])
    elif ob == False:
        b = init_BYTES([_SPEC, char_to_byte("F")])
    elif ob == None:
        b = init_BYTES([_SPEC, char_to_byte("N")])
    else:
        raise RuntimeError("object is not of 'special' kind!")
    return b


def _load_spec(b):
    assert comp_id(b[0], _SPEC)
    if b[1] == char_to_byte("T"):
        return True, 2
    elif b[1] == char_to_byte("F"):
        return False, 2
    elif b[1] == char_to_byte("N"):
        return None, 2
    else:
        raise BFLoadError("internal error (unknown code for 'special' {})".format(b[1]))


def _dump_int_32(ob):
    b = init_BYTES([_INT_32])
    b += struct.pack(">i", ob)
    return b


def _load_int_32(b):
    assert comp_id(b[0], _INT_32)
    i = struct.unpack(">i", b[1:5])[0]
    return i, 5


def _dump_int(ob):
    if ob < 0:
        b = init_BYTES([_INT_NEG])
        ob *= -1
    else:
        b = init_BYTES([_INT])

    ib = int_to_bytes(ob)
    num_bytes = len(ib)
    b += struct.pack(">I", num_bytes)
    b += ib
    return b


def _load_int(b):
    if comp_id(b[0], _INT):
        m = 1
    elif comp_id(b[0], _INT_NEG):
        m = -1
    else:
        raise BFLoadError("internal error (unknown int id {})".format(b[0]))
    num_bytes = struct.unpack(">I", b[1:5])[0]
    i = m * bytes_to_int(b[5 : 5 + num_bytes])
    return i, num_bytes + 5


def _dump_float(ob):
    b = init_BYTES([_FLOAT])
    b += struct.pack(">d", ob)
    return b


def _load_float(b):
    assert comp_id(b[0], _FLOAT)
    f = struct.unpack(">d", b[1:9])[0]
    return f, 9


def _dump_complex(ob):
    b = init_BYTES([_COMPLEX])
    b += struct.pack(">d", ob.real)
    b += struct.pack(">d", ob.imag)
    return b


def _load_complex(b):
    assert comp_id(b[0], _COMPLEX)
    re = struct.unpack(">d", b[1:9])[0]
    im = struct.unpack(">d", b[9:17])[0]
    return re + 1j * im, 13


def _dump_str(ob):
    b = init_BYTES([_STR])
    str_bytes = str_to_bytes(ob)
    num_bytes = len(str_bytes)
    b += struct.pack(">I", num_bytes)
    b += str_bytes
    return b


def _load_str(b):
    assert comp_id(b[0], _STR)
    num_bytes = struct.unpack(">I", b[1:5])[0]
    s = bytes_to_str(b[5 : 5 + num_bytes])
    return s, 5 + num_bytes


def _dump_bytes(ob):
    b = init_BYTES([_BYTES])
    num_bytes = len(ob)
    b += struct.pack(">I", num_bytes)
    b += ob
    return b


def _load_bytes(b):
    assert comp_id(b[0], _BYTES)
    num_bytes = struct.unpack(">I", b[1:5])[0]
    b_ = b[5 : 5 + num_bytes]
    return b_, 5 + num_bytes


def _dump_tuple(t):
    b = init_BYTES([_TUPLE])
    size = len(t)
    b += struct.pack(">I", size)
    for ti in t:
        b += _dump(ti)
    return b


def _load_tuple(b, classes):
    assert comp_id(b[0], _TUPLE)
    size = struct.unpack(">I", b[1:5])[0]
    idx = 5
    t = []
    for i in range(size):
        ob, len_ob = _load(b[idx:], classes)
        t.append(ob)
        idx += len_ob
    return tuple(t), idx


def _dump_namedtuple(t):
    b = init_BYTES([_NAMEDTUPLE])
    size = len(t)
    b += struct.pack(">I", size)
    b += _dump(t.__class__.__name__)
    for i in range(size):
        b += _dump(t._fields[i])
        b += _dump(t[i])
    return b


def _load_namedtuple(b, classes):
    assert comp_id(b[0], _NAMEDTUPLE)
    size = struct.unpack(">I", b[1:5])[0]
    class_name, len_ob = _load_str(b[5:])
    idx = 5 + len_ob
    t = []
    fields = []
    for i in range(size):
        ob, len_ob = _load(b[idx:], classes)
        fields.append(ob)
        idx += len_ob

        ob, len_ob = _load(b[idx:], classes)
        t.append(ob)
        idx += len_ob

    np_class = namedtuple(class_name, fields)
    np_obj = np_class(*t)

    return np_obj, idx


def _dump_list(t):
    b = init_BYTES([_LIST])
    size = len(t)
    b += struct.pack(">I", size)
    for ti in t:
        b += _dump(ti)
    return b


def _load_list(b, classes):
    assert comp_id(b[0], _LIST)
    size = struct.unpack(">I", b[1:5])[0]
    idx = 5
    t = []
    for i in range(size):
        ob, len_ob = _load(b[idx:], classes)
        t.append(ob)
        idx += len_ob
    return t, idx


def _dump_np_array(np_array):
    b = init_BYTES([_NPARRAY])

    nparray_bytesIO = io.BytesIO()
    np_format.write_array(nparray_bytesIO, np_array, version=(1, 0))
    nparray_bytes = nparray_bytesIO.getvalue()
    size = len(nparray_bytes)
    b += struct.pack(">I", size)
    b += nparray_bytes
    return b


def _load_np_array(b):
    assert comp_id(b[0], _NPARRAY)
    size = struct.unpack(">I", b[1:5])[0]
    nparray_bytesIO = io.BytesIO(b[5 : size + 5])
    npa = np_format.read_array(nparray_bytesIO)
    return npa, size + 5


def _dump_bfkey(ob):
    b = init_BYTES([_BFKEY])
    bfkey = ob.__bfkey__()
    obj_type = ob.__class__.__name__
    b += _dump(str(obj_type))
    b += _dump(bfkey)
    return b


def _load_bfkey(b, classes):
    assert comp_id(b[0], _BFKEY)
    obj_type, l_obj_type = _load_str(b[1:])
    bfkey, l_state = _load(b[l_obj_type + 1 :], classes)
    return (obj_type, bfkey), l_obj_type + l_state + 1


def _dump_getstate(ob):
    b = init_BYTES([_GETSTATE])
    state = ob.__getstate__()
    obj_type = ob.__class__.__name__
    b += _dump(str(obj_type))
    b += _dump(state)

    return b


def _load_getstate(b, classes):
    assert comp_id(b[0], _GETSTATE)
    obj_type, l_obj_type = _load_str(b[1:])
    state, l_state = _load(b[l_obj_type + 1 :], classes)
    try:
        cls = classes[obj_type]
    except KeyError:
        raise BFUnkownClassError(obj_type)
    obj = cls.__new__(cls)
    obj.__setstate__(state)
    return obj, l_obj_type + l_state + 1


def _dump_dict(ob):
    b = init_BYTES([_DICT])
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


def _load_dict(b, classes):
    assert comp_id(b[0], _DICT)
    sorted_keys_value, l = _load_list(b[1:], classes)
    res_dict = {}
    for i in range(len(sorted_keys_value)):
        key = _load(sorted_keys_value[i][0], classes)[0]
        value = _load(sorted_keys_value[i][1], classes)[0]
        res_dict[key] = value

    return res_dict, l + 1


def _dump_scipy_csc_matrix(ob):
    b = init_BYTES([_SP_CSC_MAT])

    b += _dump_np_array(ob.data)
    b += _dump_np_array(ob.indices)
    b += _dump_np_array(ob.indptr)
    b += _dump_tuple(ob.shape)

    return b


def _load_scipy_csc_matrix(b):
    assert comp_id(b[0], _SP_CSC_MAT)
    l = 0
    data, _l = _load_np_array(b[1:])
    l += _l
    indices, _l = _load_np_array(b[1 + l :])
    l += _l
    indptr, _l = _load_np_array(b[1 + l :])
    l += _l
    shape, _l = _load_tuple(b[1 + l :], classes={})
    l += _l
    return scipy.csc_matrix((data, indices, indptr), shape=shape), l + 1


def _dump(ob):
    if isinstance(ob, _spec_types):
        return _dump_spec(ob)
    elif isinstance(ob, (int, LONG_TYPE)):
        if (__min_int32 <= ob) and (ob <= __max_int32):
            return _dump_int_32(ob)
        else:
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
        return _dump_bfkey(ob)
    elif hasattr(ob, "__getstate__"):
        return _dump_getstate(ob)
    elif scipy and isspmatrix_csc(ob):
        return _dump_scipy_csc_matrix(ob)
    else:
        raise TypeError("unsupported type for dump '{}' ({})".format(type(ob), ob))


def _load(b, classes):
    identifier = b[0]
    if isinstance(identifier, str):
        identifier = ord(identifier)
    if identifier == _SPEC:
        return _load_spec(b)
    elif identifier == _INT_32:
        return _load_int_32(b)
    elif (identifier == _INT) or (identifier == _INT_NEG):
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
        return _load_tuple(b, classes)
    elif identifier == _NAMEDTUPLE:
        return _load_namedtuple(b, classes)
    elif identifier == _LIST:
        return _load_list(b, classes)
    elif identifier == _NPARRAY:
        return _load_np_array(b)
    elif identifier == _DICT:
        return _load_dict(b, classes)
    elif identifier == _BFKEY:
        return _load_bfkey(b, classes)
    elif identifier == _GETSTATE:
        return _load_getstate(b, classes)
    elif identifier == _SP_CSC_MAT:
        return _load_scipy_csc_matrix(b)
    else:
        raise BFLoadError(
            "internal error (unknown identifier '{}')".format(hex(identifier))
        )


def dump(ob):
    """
        returns the binary footprint of the object 'ob' as bytes
    """
    return init_BYTES([_VERS]) + _dump(ob)


def load(b, classes={}):
    """
        reconstruct the object from the binary footprint given as bytes 'b'
    """
    vers = b[0]
    if byte_to_ord(vers) != _VERS:
        raise BFLoadError("wrong version (converter needed!)")

    return _load(b[1:], classes)[0]