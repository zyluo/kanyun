#!/usr/bin/env python
# encoding: utf-8
# TAB char: space

# Author: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-4-6
# Last update: Peng Yuwei<yuwei5@staff.sina.com.cn> 2012-4-6

import sys
from setuptools import setup, find_packages


requirements = ['pyzmq']#, 'python-novaclient', 'python-keystoneclient']

setup(
    name = "kanyun",
    version = "0.1",
#    package_dir = {'':'monitoring'},   # tell distutils packages are under src
    packages = ['kanyun',
              'kanyun.database',
              'kanyun.server',
              'kanyun.worker',
              'kanyun.client'],
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = requirements,

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        'worker': ['*.conf'],
        'server': ['*.conf'],
    },

    # metadata for upload to PyPI
    author = 'Sina Corp.',
    author_email = "pengyuwei@gmail.com",
    description = "OpenStack Monitoring System",
    long_description = "OpenStack Monitoring System",
    license = 'Apache',
    keywords = "vm openstack monitor",
    url = "https://git.sws.sina.com.cn/pyw_code/pyw_code",   # project home page, if any
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],

    # could also include long_description, download_url, classifiers, etc.
)


