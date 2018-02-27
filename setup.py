#!/usr/bin/env python
# http://docs.python.org/distutils/setupscript.html
# http://docs.python.org/2/distutils/examples.html

from setuptools import setup
import re
import os
from codecs import open


name = 'gsuites'
with open("{name}.py".format(name=name), encoding='utf-8') as f:
  version = re.search("^__version__\s*=\s*[\'\"]([^\'\"]+)", f.read(), flags=re.I | re.M).group(1)

with open('README.rst', encoding='utf8') as f:
  long_description = f.read()

install_requires = [
    'google-api-python-client',
]

PY_VERSIONS = [
    '2.7',
    '3.4',
    '3.5',
    '3.6',
]

# https://pypi.python.org/pypi?:action=list_classifiers
classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
]

classifiers += [
    'Programming Language :: Python :: {v}'.format(v=v) for v in PY_VERSIONS]


## generate the req.txt
if __name__ == '__main__':
  with open('req.txt', 'wb') as f:
    for i in install_requires:
      f.write((i + '\n').encode('utf8'))

  setup(
    name=name,
    version=version,
    description='Gsuites - a set of Google Gsuites API wrapper',
    long_description=long_description,
    author='Tom Tang',
    author_email='tly1980@gmail.com',
    url='http://github.com/tly1980/{name}'.format(name=name),
    py_modules=[name],
    install_requires=install_requires,
    license="MIT",
    classifiers=classifiers,
  )
