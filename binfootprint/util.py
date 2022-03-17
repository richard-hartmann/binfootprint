class ABS_Parameter(object):

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
    def __init__(self, fnc):
        self.fnc = fnc
        self.fnc_sig = signature(fnc)
        self.f_name = __name__ + "_" + self.fnc.__name__
        print(self.f_name)

    def __call__(self, *args, **kwargs):
        ba = self.fnc_sig.bind(*args, **kwargs)
        fnc_args = ba.args
        with shelve.open(self.f_name) as db:
            if fnc_args in db:
                return db[fnc_args]
            else:
                r = self.fnc(*args, **kwargs)
                db[fnc_args] = r
                return r
