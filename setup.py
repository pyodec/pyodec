#!/usr/bin/env python

from distutils.core import setup

setup(name='pyodec',
      version='0.0',
      description='Python open file decoder',
      author='Joe Young & Others',
      author_email='joe.young@utah.edu',
      url='http://pyodec.github.io',
      packages=['pyodec',
                'pyodec.core',
                'pyodec.files',
                'pyodec.messages',
                ],
     )