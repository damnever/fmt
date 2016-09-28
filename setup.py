#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import codecs

from setuptools import setup, find_packages


version = ''
with open('fmt/__init__.py', 'r') as f:
    version = re.search(r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.M).group(1)

with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='fmt',
    version=version,
    description='f-strings(Python 3.6) style literal string interpolation.',
    long_description=long_description,
    url='https://github.com/damnever/fmt',
    author='damnever',
    author_email='dxc.wolf@gmail.com',
    license='The BSD 3-Clause License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='f-strings, format, literal string interpolation',
    packages=find_packages()
)
