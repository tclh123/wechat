#!/usr/bin/env python

from io import open
from setuptools import setup, find_packages
from wechat import VERSION


setup(
    name='wechat3',
    version=VERSION,
    description='Wechat Python SDK',
    long_description=open("README.md", encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    author='jeff kit',
    author_email='bbmyth@gmail.com',
    maintainer='Harry Lee',
    maintainer_email='tclh123@gmail.com',
    url='https://github.com/tclh123/wechat',
    keywords=['wechat', 'SDK'],
    license="GPLv3",
    packages=find_packages(exclude=['demo*', 'tests*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=['requests', 'cryptography'],
)
