# binfootprint

[![Build Status](https://travis-ci.org/cimatosa/binfootprint.svg?branch=master)](https://travis-ci.org/cimatosa/binfootprint)


Calculate a unique binary representation (binary footprint) for simple data structures 
with the intension to use this binary footprint as a loop up key for example in a data base.

The following atomic types are supported:
  * integer (32bit and python integer)
  * float (the usual 64bit)
  * complex (the usual 2 times 64bit)
  * string
  * bytes
  * numpy ndarray (see note below)

These atomic types can be structured arbitrarily nested using the following python standard containers:
  * tuple
  * named tuple
  * list
  * dict

Generating the binary footprint and reconstruction is done as follows:

```python
import binfootprint as bf

data = ['hallo', 42]
bin_key = bf.dump(data)

data_prime = bf.load(bin_key)
print(data_prime)
```

Further any class that implements `__getstate__` may be used as a container as well. When reconstructing, the class needs to have the `__setstate__` method implemented.
Additionally the `bf.load` function required a mapping from the class name to the class object, like this:
```python

import binfootprint as bf

class T(object):
    def __init__(self, a):
        self.a = a
    def __getstate__(self):
        return [self.a]
    def __setstate__(self, state):
        self.a = state[0]

ob = T(4)
bin_ob = bf.dump(ob)

# reconstruction
classes = {}
classes['T'] = T
ob_prime = bf.load(bin_ob, classes)

```

### Note on numpy ndarrays

As it has not been clarified/tested yet whether the buffer of the numpy ndarray is really unique also on different machines and architectures
is it not assured that the binary footprint serves as a valid key.
