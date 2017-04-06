#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
from setuptools import setup, find_packages


# Remove build status and move Gitter link under title for PyPi
# README = open('README.md').read()    \
#     .replace('|Build Status|', '', 1) \
#     .replace('|Gitter|', '', 1)       \
#     .replace('===\n', '===\n\n|Gitter|\n')


setup(
    name='django-include',
    version='0.0.0',
    author='Chris Seto',
    author_email='chriskseto@gmail.com',
    description='ORM extensions for performance conscious perfectionists.',
    # long_description=README,
    long_description='',
    url='http://github.com/chrisseto/django-include',
    license='MIT',
    packages=[
        'include',
    ],
    install_requires=[
        'ujson',
        'psycopg2',
        'ciso8601',
        'django>=1.9',
    ],
    classifiers=[
        # 'Development Status :: 5 - Production/Stable',
        # 'Operating System :: OS Independent',
        # 'Programming Language :: Python',
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
        # 'Framework :: Django',
        # 'Framework :: Django :: 1.7',
        # 'Framework :: Django :: 1.8',
        # 'Framework :: Django :: 1.9',
        # 'Framework :: Django :: 1.10',

        # 'Environment :: Web Environment',
        # 'Intended Audience :: Developers',
        # 'Topic :: Internet :: WWW/HTTP',
        # 'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    zip_safe=False,
    include_package_data=True,
)
