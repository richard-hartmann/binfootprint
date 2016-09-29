 #!/usr/bin/env python
# -*- coding: utf-8 -*-
# To create a distribution package for pip or easy-install:
# python setup.py sdist

from setuptools import setup

author = u"Richard Hartmann"
authors = [author]
description = 'binary representation for simple data structured'
name = 'binfootprint'
version = '0.1.0'

if __name__ == "__main__":
    setup(
        name=name,
        author=author,
        author_email='richard.hartmann@tu-dresden.de',
        url='https://github.com/cimatosa/binfootprint',
        version=version,
        packages=[name],
        package_dir={name: name},
        license="BSD (3 clause)",
        description=description,
        install_requires=["NumPy >= 1.5.1"],
        keywords=["binary","footprint", "pickle", "key"],
        classifiers= [
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Intended Audience :: Developers'],
        platforms=['ALL']
        )