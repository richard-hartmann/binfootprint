from inspect import signature
import shelve
from pathlib import Path
from . import binfootprint
from hashlib import sha256


def get_hash_str(bin_data):
    return sha256(bin_data).hexdigest()


class ABS_Parameter(object):
    """
    needs docs and testing
    """

    __slots__ = ["__non_key__"]

    def __init__(self):
        pass

    def __bfkey__(self):
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
            keys = sorted(self.__non_key__.keys())
            mal_l = max([k for k in keys])
            for k in keys:
                s += "{1:>{0}} : {2}\n".format(max_l, k, self.__non_key__[k])
        return s


class ShelveCacheDec:
    """
    Provides a decorator to cache the return value of a function to disk.

    Use a shelve to store the data, so pickle is used to store the return object.
    The arguments are mapped to a dictionary including the full signature of the function (with
    default arguments). The key is constructed using the binfootprint module.
    This means that the arguments have to be digestable by tha dump function of that module
    (see binfootprint for details).
    """
    def __init__(self, path = ".cache"):
        """
        :param path: the path under which the database (shelve) is stored
        """
        self.path = Path(path).absolute()
        self.path.mkdir(parents=True, exist_ok=True)


    def __call__(self, fnc):
        self.fnc = fnc
        self.fnc_sig = signature(fnc)
        self.f_name = str(self.path / (self.fnc.__module__ + "." + self.fnc.__name__))
        print(self.f_name)

        def wrapper(*args, **kwargs):
            ba = self.fnc_sig.bind(*args, **kwargs)
            ba.apply_defaults()
            fnc_args = ba.arguments
            print(fnc_args)
            fnc_args_key = get_hash_str(binfootprint.dump(fnc_args))
            
            with shelve.open(self.f_name) as db:
                if fnc_args_key in db:
                    return db[fnc_args_key]
                else:
                    r = self.fnc(*args, **kwargs)
                    db[fnc_args_key] = r
                    return r

        return wrapper


@ShelveCacheDec()
def test_fnc(a, b):
    return a + b