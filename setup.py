#!/usr/bin/env python

from distutils.core import setup

setup(name='SG',
      version='1.0',
      description='SeatGeek command line app',
      author='Mike Dirolf',
      author_email='mike@dirolf.com',
      url='http://github.com/mdirolf/sgcli',
      scripts=['sg'],
      install_requires=["PIL", "requests"],
      )
