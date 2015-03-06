#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
from setuptools import setup
setup(
	name = 'my_app',
	version='1.0',
	license='GNU General Public License v3',
	author='Cqshinn',
	author_email='Cqshinn92@gmail.com',
	description='Hello world Flask',
	packages=[
	'my_app',
	'my_app/product',
	'my_app/catalog',
	'my_app/auth',

	],
	platforms='any',
	install_requires=[
	'flask',
	],
	classifiers=[
	'Development Status :: 4 - Beta',
	'Environment :: Web Environment',
	'Intended Audience :: Developers',
	'License :: OSI Approved :: GNU General Public License v3',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
	'Topic :: Software Development :: Libraries :: Python Modules'
	],
	)
