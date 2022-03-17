# binfootprint

[![PyPI version](https://badge.fury.io/py/binfootprint.svg)](https://badge.fury.io/py/binfootprint)
[![Build Status](https://travis-ci.org/cimatosa/binfootprint.svg?branch=master)](https://travis-ci.org/cimatosa/binfootprint)
[![codecov](https://codecov.io/gh/cimatosa/binfootprint/branch/master/graph/badge.svg)](https://codecov.io/gh/cimatosa/binfootprint)

## Description

This module intents to generate a binary representation of a python object
where it is guaranteed that the same objects will result in the same binary
representation.
    
By far not all python objects are supported. Here is the list of supported types
        
* special build-in constants: True, False, None
* integer 
* float (64bit)
* complex (128bit)

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
