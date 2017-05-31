#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from setuptools import setup


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='django-include',
    version=find_version('include/__init__.py'),
    author='Chris Seto',
    author_email='chriskseto@gmail.com',
    description='ORM extensions for performance-conscious perfectionists.',
    long_description=read('README.rst'),
    url='http://github.com/chrisseto/django-include',
    license='MIT',
    packages=[
        'include',
    ],
    keywords=('django', 'postgres', 'sql', 'optimization', 'performance'),
    install_requires=[
        'psycopg2',
    ],
    extras_require={
        'faster': ['ujson', 'ciso8601']
    },
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    zip_safe=False,
    include_package_data=True,
)
