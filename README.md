# binfootprint - unique serialization of python objects

## Why unique serialization

When caching computationally expansive function calls, the input arguments (*args, **kwargs)
serve as key to look up the result of the function.
To perform efficient lookups the key (often a large number of nested python objects) needs to be hashable.
Since python's build-in hash function is randomly seeded (and applies to a few data types only) it is not
suited for the purpose hashing function arguments. 
However, in order to use a general hash function, as provided by the 
[hashlib library](https://docs.python.org/3/library/hashlib.html), the object needs to be converted to
a sequence of bytes, which the hash function can digest.
Surely, python's pickle module provides such a serialization which, for our purpose, has the drawback that
the byte sequence is not guaranteed to be unique (e.g., a dictionary can be stored as different byte sequences,
as the order of the (key, value) pairs is irrelevant).

The binfootprint module fills that gap.
It guarantees that a particular python object will have a unique binary representation. 

## Which data types can be serialized

Python's fundamental data types

* integer 
* float (64bit)
* complex (128bit)
* strings
* byte arrays
* special build-in constants: True, False, None

as well as their nested combination by means of the data structures

- tuple
- list
- dictionary
- namedtuple

is natively supported. In addition, also

- np.ndarray

are supported. The serialization makes use of numpy's 
[format.write_array()](https://numpy.org/devdocs/reference/generated/numpy.lib.format.write_array.html) 
function using version 1.0.

Furthermore

- 'getstate' (objects that implement `__getstate__ and return a state that can be dumped as well)

can be dumped. To Restore these objects the load function needs a lookup given by the argument 'classes'
which maps the objects class name (`obj.__class__.__name__`) to the actual class definition (the class object).
Of course for these objects the `__setstate__` method needs to be implemented. 

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

    git clone https://github.com/cimatosa/binfootprint.git


## Examples

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
