# python imports
from hashlib import sha256
from inspect import signature
from pathlib import Path
import shelve

# module import
from . import binfootprint


def hash_hex_from_bin_data(bin_data):
    """
    apply SHA256 to binary data and return the hex-string representation of the hash value
    """
    return sha256(bin_data).hexdigest()


def hash_hex_from_object(ob):
    """
    apply SHA256 to binary footprint og the object `ob` data and
    return the hex-string representation of the hash value
    """
    return hash_hex_from_bin_data(binfootprint.dump(ob))


class ABCParameter:
    """
    abstract base class to conveniently manage a set of parameters

    Relevant parameters need to be explicitly specified as data member of the class
    in terms of python's `__slots__` mechanism.
    The '__bfkey__' method (see binaryfootprint module) returns the values for those class
    members. Their order in the `__slots__` definition is irrelevant since the `__bfkey__' method
    returns a sorted list.
    *Importantly*, class members are included only if they are not `None`.
    In this way a parameter class definition can be extended while still being able to reproduce the
    binary footprint of an older class definition.

    If present, the class member `__non_key__` has a special meaning.
    It is not included in the parameter-values list returned by `__bfkey__`.
    It is expected to be dictionary-like and allows storing additional / informative information.
    This is also reflected by the string representation of the class.
    """

    __slots__ = ["__non_key__"]

    def __init__(self):
        pass

    def __bfkey__(self):
        """
        Return a sorted list of parameter-value pairs.
        Exclude the class member `__non_key__`.
        """
        key = []
        sorted_slots = sorted(self.__slots__)
        if "__non_key__" in sorted_slots:
            sorted_slots.remove("__non_key__")
        for k in sorted_slots:
            atr = getattr(self, k)
            if atr is not None:
                key.append((k, atr))
        return key

    def __repr__(self):
        s = ""
        sorted_slots = sorted(self.__slots__)
        if "__non_key__" in sorted_slots:
            sorted_slots.remove("__non_key__")
        max_l = max([len(k) for k in sorted_slots])
        for k in sorted_slots:
            atr = getattr(self, k)
            if atr is not None:
                s += "{1:>{0}} : {2}\n".format(max_l, k, atr)
        if "__non_key__" in self.__slots__:
            s += "--- extra info ---\n"
            try:
                keys = sorted(self.__non_key__.keys())
                max_l = max([len(k) for k in keys])
                for k in keys:
                    s += "{1:>{0}} : {2}\n".format(max_l, k, self.__non_key__[k])
            except AttributeError:
                s += str(self.__non_key__)
        return s[:-1]


class ShelveCacheDec:
    """
    Provides a decorator to cache the return values of a function to disk.

    Use a python shelve to store the data, so pickle is used to store the return object of the functions to cache.
    The arguments pose the keys for the shelf.
    To use the arguments as keys, they are mapped to a dictionary including the full signature of the function (with
    default arguments) and serialized using the binfootprint module.
    The SHA256 hash value of the binary data is used as key for the shelf.
    """

    def __init__(self, path=".cache"):
        """
        Initialize the ShelveCacheDec class which caches function calls using python's shelve.

        The location where the corresponding database is stored is given by `path`.
        The path is created if necessary. The actual name of the database is retrieved from the
        name of the function and the name of the module defining that function.
        It is, thus, safe to use the ShelveCacheDec with the same path parameter on different functions.

        :param path: the path under which the database (shelve) is stored.
        """
        self.path = Path(path).absolute()
        self.path.mkdir(parents=True, exist_ok=True)

    def __call__(self, fnc):
        return ShelveCache(fnc, self.path)


class ShelveCache:
    def __init__(self, fnc, path):
        """
        Extend the function `fnc` by caching and adds the extra kwarg  `_cache_flag` which
        modifies the caching behavior as follows:

            `_cache_flag = 'no_cache'`: Simple call of `fnc` with no caching.
            `_cache_flag = 'update'`: Call `fnc` and update the cache with recent return value.
            `_cache_flag = 'has_key'`: Return `True` if the call has already been cached, otherwise `False`.
            `_cache_flag = 'cache_only'`: Raises a `KeyError` if the result has not been cached yet.

        :param fnc: function to be cached
        :param path: location where the cache data is stored
        """
        self.path = path
        self.fnc = fnc
        self.fnc_sig = signature(fnc)
        self.f_name = str(self.path / (self.fnc.__module__ + "." + self.fnc.__name__))

    def param_hash(self, *args, **kwargs):
        """
        calculate the hash value for the parameters `args` and `kwargs` with respect to the
        function `fnc`. The full mapping (kwargs dictionary) between the name of the arguments and their values
        including default values is used to calculate the hash.
        """
        ba = self.fnc_sig.bind(*args, **kwargs)
        ba.apply_defaults()
        fnc_args = ba.arguments
        fnc_args_key = hash_hex_from_object(fnc_args)
        return fnc_args_key

    def __call__(self, *args, **kwargs):
        """
        the actual wrapper function that implements the caching for `fnc`
        """
        flag = None
        if "_cache_flag" in kwargs:
            flag = kwargs["_cache_flag"]
            del kwargs["_cache_flag"]

        if flag == "no_cache":
            return self.fnc(*args, **kwargs)
        else:
            fnc_args_key = self.param_hash(*args, **kwargs)
            with shelve.open(self.f_name) as db:
                if flag == "has_key":
                    return fnc_args_key in db
                elif flag == "cache_only":
                    return db[fnc_args_key]
                elif (fnc_args_key not in db) or (flag == "update"):
                    r = self.fnc(*args, **kwargs)
                    db[fnc_args_key] = r
                    return r
                else:
                    return db[fnc_args_key]
