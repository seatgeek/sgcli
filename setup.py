#!/usr/bin/env python

from distutils.core import setup

setup(name='sgcli',
      version='1.6',
      description='SeatGeek command line app',
      author='Mike Dirolf',
      author_email='mike@dirolf.com',
      url='http://github.com/mdirolf/sgcli',
      scripts=['sgcli'],
      install_requires=["pillow", "requests"],
      )
