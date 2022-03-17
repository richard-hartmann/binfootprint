class ShelveCacheDec:
    def __init__(self, fnc):
        self.fnc = fnc
        self.fnc_sig = signature(fnc)
        self.f_name = __name__ + '_' + self.fnc.__name__
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