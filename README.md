# binfootprint - unique serialization of python objects

[![PyPI version](https://badge.fury.io/py/binfootprint.svg)](https://badge.fury.io/py/binfootprint)

## Why unique serialization

When caching computationally expansive function calls, the input arguments (*args, **kwargs)
serve as key to look up the result of the function.
To perform efficient lookups these keys (often a large number of nested python objects) needs to be hashable.
Since python's build-in hash function is randomly seeded (and applies to a few data types only) it is not
suited for persistent caching.
Alternatively, standard hash functions, as provided by the 
[hashlib library](https://docs.python.org/3/library/hashlib.html), can be used.
As they relay on  byte sequences as input, python objects need to be converted to such a sequence first.
Surely, python's pickle module provides such a serialization which, for our purpose, has the drawback that
the byte sequence is not guaranteed to be unique (e.g., a dictionary can be stored as different byte sequences,
as the order of the (key, value) pairs is irrelevant).

The binfootprint module fills that gap.
It guarantees that a particular python object will have a unique binary representation which 
can serve as input for any hash function.  

## Quick start

`binfootprint.dump(data)` generate a unique binary representation 
(binary footprint) of `data`.
```python
b = binfootprint.dump(['hallo', 42])
```

Its output can serve as suitable input for a hash function.
```python
hashlib.sha256(b).hexdigest()
```

`binfootprint.load(data)` reconstructs the original python object.
```python
ob = binfootprint.load(b)
```

Numpy array can be serialized.
```python
a = numpy.asarray([0, 2.3, 4])
b = binfootprint.dump(a)
```

Classes which implement `__getstate__` (pickle interface) or `__bfkey__` can be
serialized too.

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __getstate__(self):
        return [self.x, self.y]
        
ob = Point(4, -2)
b = binfootprint.dump(ob)
```
If `__bfkey__` is implemented, it is used over `__getstate__`.

### cache decorator 

Utilizing the unique binary representation of python objects, a persistent 
cache for quite general functions is provided by the `ShelveCache` class.
The decorator `ShelveCacheDec` makes it really easy to use: 

```python
@binfootprint.ShelveCacheDec(path='.cache')
def area(p):
    return p.x * p.y
```

### parameter base class

To conveniently organize a set of parameters suitable as key for caching 
you can subclass `ABCParameter`. Why should you do that?

- The `__bfkey__` method of `ABCParameter` ignores parameters that are `None`.
  This allows to extend your function interface without loosing access to 
  cached results from earlier stages.
- You can add informative information to the `__non_key__` member which
  are not included in the binary representation of the parameter class.

```python
class Param(bf.ABCParameter):
    __slots__ = ["x", "y", "__non_key__"]

    def __init__(self, x, y, msg=""):
        super().__init__()
        self.x = x
        self.y = y
        self.__non_key__ = dict()
        self.__non_key__["msg"] = msg
```


## Which data types can be serialized

Python's **fundamental data types** are supported
* integer 
* float (64bit)
* complex (128bit)
* strings
* byte arrays
* special build-in constants: `True`, `False`, `None`

as well as their **nested combination** by means of the **native data structures**
- tuple
- list
- dictionary
- namedtuple.

In addition, also
- numpy `ndarray`

is supported. 
The serialization makes use of numpy's 
[format.write_array()](https://numpy.org/devdocs/reference/generated/numpy.lib.format.write_array.html) 
function using version 1.0.

Furthermore, any class that implements 

- `__getstate__` (python's pickle interface)

can be serialized as well, given that the returned data from `__getstate__` can be serialized.
Distinction between objects is realized by adding the class name and the name of the module which defines 
the class to the binary data.
This in turn allows to also reconstruct the original object by means of the `__setstate__` method.

In case the `__getstate__` method is not suitable, you can implement

- `__bfkey__`

which should return the necessary data to distinguish different objects.
The spirit of `__kfkey__` is very similar to that of `__getstate__`, although it is meant
for serialization only, and to for reconstruction the original object.

Note that, if `__bfkey__` is implemented it will be used, regardless of `__getstate__`.

Note: dumping older version is not supported anymore. If backwards compatibility is needed check out older
code from git. If needed converters should/will be written.

## Installation

### pip
install the latest version using pip

    pip install binfootprint

### poetry
Using poetry allows you to include this package in your project as a dependency.

### git
check out the code from github

    git clone https://github.com/richard-hartmann/binfootprint.git

### dependencies

- python3
- numpy

## How to use the binfootprint module

### data serialization

Generating the binary footprint is done using the `dump(obj)` method.

#### very simple
```python
import binfootprint as bf
bf.dump(['hallo', 42])
```

#### more complex
```python
import hashlib
import binfootprint as bf

SIGMA_Z = 0x34
data = {
    'Færøerne': {
        'area': (1399, 'km^2'),
        'population': 54000
    },
    SIGMA_Z: [[-1, 0],
              [0, 1]],
    'usefulness': None
}
b = bf.dump(data)
print("MD5 check sum:", hashlib.md5(b).hexdigest())
```

### reconstruct serialized data

Although the primary focus of this module is the binary representation,
for reasons of convenience or debugging it might be useful restore the original
python object from the binary data. 
Calling the `load(bin_data)` function achieves that task. 
  
```python
import binfootprint as bf

data = ['hallo', 42]
b = bf.dump(data)
data_prime = bf.load(b)
print(data_prime)
```

### python objects - `__getstate__`

Since `__getstate__` is assumed to uniquely represent the state of an
object by means of the returned data, it can be used to generate a unique binary
representation.

```python
import binfootprint as bf

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __getstate__(self):
        return [self.x, self.y]
    def __setstate__(self, state):
        self.x = state[0]
        self.y = state[1]

ob = Point(4, -2)
b = bf.dump(ob)
```
Since `__setstate__` is implemented as well, the original object can be
reconstructed.
```python
ob_prime = bf.load(b)
print("type:", type(ob_prime))
# type: <class '__main__.Point'>
print("member x:", ob_prime.x)
# member x: 4
print("member y:", ob_prime.y)
# member y: -2
```

### implement `__bfkey__` if `__getstate__` is not suited

In case `__getstate__` returns data which is not sufficient to uniquely label
an object or if the data cannot be serialized by the binaryfootprint module,
the method `__bfkey__` should be implemented.
It is expected to return serializable data which uniquely identifies the state
of the object.
Note that, if `__bfkey__` is present, `__getstate__` is ignored.

**Importantly**, when deserializing the binary data from an object implementing 
`__bfkey__`, the python object **is not returned**, since there is no 
`__setstate__`equivalent. Instead, the class name, the name of the module defining 
the class and the data returned by `__bfkey__` is recovered.
This should not pose a problem, since the main focus of the binfootprint module is
the unique binary serialization of an object.
To ensure deserialization use python's `pickle` module.

```python
class Point2(Point):
    def __bfkey__(self):
        return {'x': self.x, 'y': self.y}

ob = Point2(5, 3)
b = bf.dump(ob)

ob_prime = bf.load(b)
print("load on bfkey:", ob_prime)
# load on bfkey: ('Point2', '__main__', {'x': 5, 'y': 3})
```

### numpy ndarrays

Numpy's `ndarray` are supported by relaying on numpy's binary serialization 
using [format.write_array()](https://numpy.org/devdocs/reference/generated/numpy.lib.format.write_array.html).

```python
import binfootprint as bf
import numpy as np

a = np.asarray([0, 1, 1, 0])
b1 = bf.dump(a)
```

As expected, changing the shape or data type yield a different binary representation

```python
a2 = a1.reshape(2,2)
b2 = bf.dump(a2)
a3 = np.asarray(a1, dtype=np.complex128)
b3 = bf.dump(a3)
print("            MD5 of int array :", hashlib.md5(b1).hexdigest())
# 949bfba1237c48007a066398f744a161
print("MD5 of int array shape (2,2) :", hashlib.md5(b2).hexdigest())
# e9049a19f82c6f282d65466a72360cd8
print("        MD5 of complex array :", hashlib.md5(b3).hexdigest())
# 2274ea54925d88ec4d53853050e55a82
```

# caching

With the binaryfootprint module, caching function calls is straight forward.
An implementation of such a cache using python's `shelve` for persistent storage
is provided by the `ShelveCacheDec` class.

```python
@binfootprint.ShelveCacheDec()
def area(p):
    print(" * f(p(x={},y={})) called".format(p.x, p.y))
    return p.x * p.y
```

It is safe to use the `ShelveCacheDec` with the same data location (`path`)   
on different functions, since the name of the function and the name of the 
module defining the function determined the name of the underlying database.  

In addition to caching the decorator extends the function signature by the 
kwarg `_cache_flag` which modifies the caching behavior as follows:

- `_cache_flag = 'no_cache'`: Simple call of `fnc` with no caching.
- `_cache_flag = 'update'`: Call `fnc` and update the cache with recent return value.
- `_cache_flag = 'has_key'`: Return `True` if the call has already been cached, otherwise `False`.
- `_cache_flag = 'cache_only'`: Raises a `KeyError` if the result has not been cached yet.

```python
p = Point(10, 10)
print("first call results in")
print(area(p))
# * f(p(x=10,y=10)) called
# 100

print("second call results in")
print(area(p))
# 100
p = Point(10, 11)

print("f(p(10, 11)) is in cache?")
print(area(p, _cache_flag='has_key'))
# False
```

# pitfalls

### ints and floats

Since the binary representation between ints and floats is different, `1` and `1.0`
will be treated as different things.
This means that the cached value of a function call with an argument being `1` is
not found when passing `1.0` as argument.
Although the result of the function will most likely be the same.
Obviously, the same holds true for numpy array of different `dtype`.

# Parameter class

Tha abstract base class `ABCParameter` allows to conveniently manage a set 
of parameters.

Relevant parameters, explicitly specified as data member via `__slots__` 
mechanism, are returned by `__bfkey__` method (see above).
Their order in the `__slots__` definition is irrelevant.
**Importantly**, class members are included only if they are not `None`.
In this way a parameter class definition can be extended while still being 
able to reproduce the binary footprint of an older class definition.

If present, the class member `__non_key__` has a special meaning.
It is not included in the parameter-values list returned by `__bfkey__`.
It is expected to be dictionary-like and allows storing 
additional / informative information.
This is also reflected by the string representation of the class.

```python
class Param(binfootprint.ABCParameter):
    __slots__ = ["x", "y", "__non_key__"]

    def __init__(self, x, y, msg=""):
        super().__init__()
        self.x = x
        self.y = y
        self.__non_key__ = dict()
        self.__non_key__['msg'] = msg


p = Param(3, 4.5)
bfp = binfootprint.dump(p)
print("{}\n has hex hash value {}...".format(
    p, binfootprint.hash_hex_from_bin_data(bfp)[:6])
)
# x : 3
# y : 4.5
# --- extra info ---
# msg : 
# has hex hash value 38dbe8...

p = Param(3, 4.5, msg="I told you, don't use x=3!")
bfp = binfootprint.dump(p)
print("{}\n has hex hash value {}...".format(
    p, binfootprint.hash_hex_from_bin_data(bfp)[:6])
)
# x : 3
# y : 4.5
# --- extra info ---
# msg : I told you, don't use x=3!
# has hex hash value 38dbe8...
```