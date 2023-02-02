import sys
import pathlib

# Add parent directory to beginning of path variable
# NOT NECESSARY IF THE PACKAGE WAS INSTALLED
sys.path.append(str(pathlib.Path(__file__).absolute().parent.parent))

import binfootprint as bf

atoms = [
    12345678,  # int32
    3.141,  # float
    "hallo Welt",  # ascii string
    "öäüß",  # utf8 string
    True,  #
    False,  #
    None,  # special Values
    2**65,  # large int
    -(3**65),  # large negative int
    b"\xff\fe\03",  # byte sequence
]  # bytes

print("convert a list of objects with different type to byte sequences")
print(atoms)
print()

# generate a unique byte sequence
byte_seq = bf.dump(atoms)
print("the first 100 bytes are (hex):")
for i in range(10):
    for j in range(10):
        print("{} ".format(byte_seq[10 * i + j : 10 * i + j + 1].hex()), end="")
    print()
print()

print("reconstruct object from byte sequence:")
# restore the original object
atoms_prime = bf.load(byte_seq)
print(atoms_prime)
